"""SEC EDGAR access: find a company, list its filings, read and search a filing, get its financials.

Everything here is free and keyless, but SEC asks every automated client to say who it is in the
User-Agent header ("Name email@example.com") and to stay under 10 requests a second.
https://www.sec.gov/os/accessing-edgar-data

Filings are big (a proxy statement is 1-3 MB of HTML), so we turn each one into a list of
paragraphs, each tagged with the heading it sits under, and let the agents search those paragraphs
instead of reading the whole thing.
"""

import asyncio
import csv
import html
import math
import os
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import httpx

HERE = Path(__file__).parent
UNIVERSE_CSV = HERE / "data" / "universe.csv"

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
INDEX_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/"
TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"

# SEC allows 10 requests/second per client. Stay well under it, even with researchers in parallel.
_gate = asyncio.Semaphore(4)
_last_request = [0.0]
MIN_INTERVAL = 0.15  # seconds between requests

# Small in-memory caches: one process, a handful of companies per run.
_json_cache: dict[str, dict] = {}
_doc_cache: dict[str, list[dict]] = {}


def user_agent() -> str:
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua or "@" not in ua:
        raise RuntimeError("Set SEC_USER_AGENT to 'Your Name your@email' (SEC requires it).")
    return ua


async def _get(url: str) -> httpx.Response:
    async with _gate:
        wait = _last_request[0] + MIN_INTERVAL - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request[0] = time.monotonic()
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": user_agent(), "Accept-Encoding": "gzip, deflate"})
    response.raise_for_status()
    return response


async def _get_json(url: str) -> dict:
    if url not in _json_cache:
        _json_cache[url] = (await _get(url)).json()
    return _json_cache[url]


# --- Companies ---------------------------------------------------------------------------------

_universe: list[dict] | None = None


def universe() -> list[dict]:
    """Every company in data/universe.csv: ticker, cik, name, exchange, russell1000 (yes/no/unknown).
    Built offline by build_universe.py."""
    global _universe
    if _universe is None:
        with open(UNIVERSE_CSV, newline="") as f:
            _universe = list(csv.DictReader(f))
    return _universe


def _norm(name: str) -> str:
    name = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    name = re.sub(r"\b(inc|corp|corporation|co|company|ltd|plc|holdings?|group|the|class [a-z])\b", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def find_company(query: str, limit: int = 5) -> list[dict]:
    """Match a ticker or a company name against the universe. Exact ticker first, then names."""
    q = query.strip()
    rows = universe()
    exact = [r for r in rows if r["ticker"].upper() == q.upper()]
    if exact:
        return exact[:limit]
    nq = _norm(q)
    if not nq:
        return []
    scored = []
    for r in rows:
        nn = _norm(r["name"])
        if nn == nq:
            score = 3
        elif nn.startswith(nq) or f" {nq} " in f" {nn} ":
            score = 2
        elif all(w in nn.split() for w in nq.split()):
            score = 1
        else:
            continue
        # Prefer index members, then shorter names (the parent, not "X Capital Trust II")
        scored.append((score, r["russell1000"] == "yes", -len(nn), r))
    scored.sort(key=lambda s: s[:3], reverse=True)
    seen, out = set(), []
    for *_, r in scored:
        if r["cik"] not in seen:
            seen.add(r["cik"])
            out.append(r)
    return out[:limit]


# Counterparties that filings name by a short name no legal name matches. Only add certain ones.
ALIASES = {"spacex": "SPCX", "space x": "SPCX"}


def resolve_counterparty(name: str) -> dict | None:
    """A counterparty named in a filing -> the listed company, or None. Strict on purpose: a loose match
    (xAI -> some fund, X Corp -> XPO) would test a deal against the wrong company's revenue."""
    nq = _norm(name)
    if not nq:
        return None
    if nq in ALIASES:
        return next((r for r in universe() if r["ticker"] == ALIASES[nq]), None)
    exact = [r for r in universe() if _norm(r["name"]) == nq]
    exact.sort(key=lambda r: (r["russell1000"] != "yes", len(r["ticker"])))
    return exact[0] if exact else None


# --- Filings -----------------------------------------------------------------------------------


async def list_filings(cik: int, forms: list[str], limit: int = 6) -> list[dict]:
    """The company's most recent filings of the given forms, newest first."""
    data = await _get_json(SUBMISSIONS_URL.format(cik=int(cik)))
    recent = data["filings"]["recent"]
    out = []
    for i, form in enumerate(recent["form"]):
        if form in forms:
            acc = recent["accessionNumber"][i]
            doc = recent["primaryDocument"][i]
            out.append(
                {
                    "form": form,
                    "filed": recent["filingDate"][i],
                    "period": recent.get("reportDate", [""] * (i + 1))[i],
                    "accession": acc,
                    "url": ARCHIVE_URL.format(cik=int(cik), acc=acc.replace("-", ""), doc=doc),
                    "index_url": INDEX_URL.format(cik=int(cik), acc=acc.replace("-", "")),
                }
            )
            if len(out) >= limit:
                break
    return out


# --- Turning a filing into searchable paragraphs ------------------------------------------------

BLOCK_TAGS = r"p|div|tr|li|h[1-6]|table|section|br|center|font"
# Lines that repeat on every page of a proxy: page numbers, running headers, nav menus.
_BOILERPLATE = re.compile(r"^(\d{1,3}|table of contents|.{0,40}proxy statement|page \d+)$", re.I)


def html_to_paragraphs(raw: str) -> list[dict]:
    """HTML -> [{i, heading, text}]. A heading is a short line that isn't a sentence; every
    paragraph remembers the last heading above it so a search hit says which section it's in."""
    raw = re.sub(r"(?is)<(script|style|head|ix:header)\b.*?</\1>", " ", raw)
    raw = re.sub(r"\s+", " ", raw)  # newlines in HTML source are just spaces
    raw = re.sub(rf"(?i)</?({BLOCK_TAGS})\b[^>]*>", "\n", raw)
    raw = re.sub(r"(?i)</t[dh]>", " | ", raw)  # keep table cells apart
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    lines = [re.sub(r"[ \t ​|]+", " ", line).strip(" |") for line in text.split("\n")]
    lines = [line for line in lines if line and not _BOILERPLATE.match(line)]
    # Running headers and page nav bars repeat on every page: drop short lines seen 4+ times
    counts = Counter(line for line in lines if len(line) < 120)
    lines = [line for line in lines if counts.get(line, 0) < 4]

    paragraphs: list[dict] = []
    heading = ""
    buffer: list[str] = []

    def flush():
        if buffer:
            body = " ".join(buffer).strip()
            if len(body) > 25:
                paragraphs.append({"i": len(paragraphs), "heading": heading, "text": body})
            buffer.clear()

    for line in lines:
        words = line.split()
        looks_like_heading = (
            2 <= len(words) <= 12 and len(line) < 90 and not line.endswith((".", ",", ";", ":")) and line[0].isupper()
            and sum(w[0].isupper() for w in words if w[0].isalpha()) >= max(1, len(words) * 0.6)
        )
        if looks_like_heading:
            flush()
            heading = line
            continue
        buffer.append(line)
        # Paragraph breaks: a line that ends a sentence closes the paragraph
        if line.endswith((".", ":", ";")) and sum(len(b) for b in buffer) > 200:
            flush()
    flush()
    return paragraphs


async def get_document(url: str) -> list[dict]:
    if url not in _doc_cache:
        if not url.startswith("https://www.sec.gov/Archives/"):
            raise ValueError("Only SEC EDGAR archive URLs (https://www.sec.gov/Archives/...) can be read.")
        response = await _get(url)
        _doc_cache[url] = html_to_paragraphs(response.text)
    return _doc_cache[url]


_CLEAN = re.compile(r"^[A-Za-z0-9$%.,;:'’-]+$")


def fragment_words(text: str, n: int = 7) -> list[str]:
    """The first run of n plain words in text: what a #:~:text= link can match exactly."""
    tokens = text.split()
    run: list[str] = []
    for token in tokens:
        if _CLEAN.match(token):
            run.append(token)
            if len(run) == n:
                return run
        else:
            run = []
    return run if len(run) >= 4 else []


def cite_url(url: str, text: str) -> str:
    """A link that opens the filing scrolled to and highlighting this passage (a text fragment,
    #:~:text=, supported by Chrome, Edge and Safari). '-' and ',' are special in fragments."""
    words = fragment_words(text)
    if not words:
        return url
    return f"{url}#:~:text={quote(' '.join(words), safe='').replace('-', '%2D')}"


_WORD = re.compile(r"[a-z0-9$]+")


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def search_paragraphs(paragraphs: list[dict], query: str, k: int = 6) -> list[dict]:
    """BM25 over paragraphs, with the heading counted too, plus a bonus for exact phrases in quotes."""
    terms = [t for t in _tokens(query) if len(t) > 2 or t.startswith("$")]
    phrases = [p.lower() for p in re.findall(r'"([^"]+)"', query)]
    if not terms and not phrases:
        return []
    docs = [_tokens(p["heading"] + " " + p["heading"] + " " + p["text"]) for p in paragraphs]
    n = len(docs)
    avg = sum(len(d) for d in docs) / max(n, 1)
    df = Counter(t for d in docs for t in set(d))
    scores = []
    for p, d in zip(paragraphs, docs):
        tf = Counter(d)
        s = 0.0
        for t in set(terms):
            if tf[t]:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf[t] * 2.2 / (tf[t] + 1.2 * (0.25 + 0.75 * len(d) / avg))
        low = (p["heading"] + " " + p["text"]).lower()
        s += sum(4.0 for ph in phrases if ph in low)
        if s > 0:
            scores.append((s, p))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scores[:k]]


# --- Financials (XBRL) -------------------------------------------------------------------------

REVENUE_CONCEPTS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
    "RevenuesNetOfInterestExpense",
    "InterestAndDividendIncomeOperating",
]


def _annual(points: list[dict], instant: bool) -> dict[str, dict]:
    """10-K values per fiscal-year end date. Durations must be about a year; latest filing wins."""
    out: dict[str, dict] = {}
    for p in points:
        if p.get("form") not in ("10-K", "10-K/A", "20-F", "40-F"):
            continue
        if not instant:
            if "start" not in p:
                continue
            days = (time.mktime(time.strptime(p["end"], "%Y-%m-%d")) - time.mktime(time.strptime(p["start"], "%Y-%m-%d"))) / 86400
            if not 340 <= days <= 380:
                continue
        prev = out.get(p["end"])
        if prev is None or p["filed"] > prev["filed"]:
            out[p["end"]] = p
    return out


async def get_financials(cik: int) -> dict:
    """Annual revenue and total assets for the last few fiscal years, with the 10-K each came from."""
    data = await _get_json(FACTS_URL.format(cik=int(cik)))
    gaap = data.get("facts", {}).get("us-gaap", {})
    result = {"company": data.get("entityName"), "revenue": [], "total_assets": [], "revenue_concept": None}

    # Different companies tag revenue differently. Take the concept with the most recent data.
    best = None
    for concept in REVENUE_CONCEPTS:
        pts = gaap.get(concept, {}).get("units", {}).get("USD", [])
        annual = _annual(pts, instant=False)
        if annual:
            latest = max(annual)
            if best is None or latest > best[0]:
                best = (latest, concept, annual)
    if best:
        _, concept, annual = best
        result["revenue_concept"] = concept
        for end in sorted(annual, reverse=True)[:4]:
            p = annual[end]
            result["revenue"].append({"fiscal_year_end": end, "usd": p["val"], "form": p["form"], "accession": p["accn"]})
    assets = _annual(gaap.get("Assets", {}).get("units", {}).get("USD", []), instant=True)
    for end in sorted(assets, reverse=True)[:4]:
        p = assets[end]
        result["total_assets"].append({"fiscal_year_end": end, "usd": p["val"], "form": p["form"], "accession": p["accn"]})
    # A company that listed recently has no 10-K yet: its latest year-to-date revenue from a 10-Q is a
    # floor on its annual revenue, which still settles some tests.
    if not result["revenue"]:
        best_ytd = None
        for concept in REVENUE_CONCEPTS:
            for p in gaap.get(concept, {}).get("units", {}).get("USD", []):
                if p.get("form") != "10-Q" or "start" not in p:
                    continue
                key = (p["end"], p["end"] > p["start"] and (time.mktime(time.strptime(p["end"], "%Y-%m-%d")) - time.mktime(time.strptime(p["start"], "%Y-%m-%d"))))
                if best_ytd is None or key > best_ytd[0]:
                    best_ytd = (key, p)
        if best_ytd:
            p = best_ytd[1]
            result["revenue_ytd"] = {"start": p["start"], "end": p["end"], "usd": p["val"], "form": p["form"], "accession": p["accn"]}
    result["source_url"] = FACTS_URL.format(cik=int(cik))
    return result


if __name__ == "__main__":
    # Smoke test: uv run edgar.py AAPL
    import sys

    from dotenv import load_dotenv

    load_dotenv(HERE / ".env")

    async def main(ticker: str):
        company = find_company(ticker)[0]
        print(company)
        filings = await list_filings(int(company["cik"]), ["DEF 14A"], 2)
        print(filings)
        paragraphs = await get_document(filings[0]["url"])
        print(len(paragraphs), "paragraphs")
        for p in search_paragraphs(paragraphs, "related person transactions family member compensation $120,000", 3):
            print(f"\n[{p['i']}] ## {p['heading']}\n{p['text'][:500]}")
        fin = await get_financials(int(company["cik"]))
        print({k: v[:2] if isinstance(v, list) else v for k, v in fin.items()})

    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "AAPL"))
