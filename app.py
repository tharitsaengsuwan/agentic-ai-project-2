"""Related Party Radar: deep research over SEC filings for insider deals and where they cross the line.

Four agents, each with one job:
  Clarifier   decides whether the question names a company and is about insider/related-party deals.
              If not, it asks the user one question and the run stops there.
  Lead        plans, fans out 2-4 Researchers in one turn (they run in parallel, each in a fresh
              context), reads their findings, and sends more for any gap, up to a cap.
  Researcher  reads one part of the filings: searches a proxy or 10-K, reads the passages, and runs
              each transaction it finds through the materiality calculator.
  Writer      sees only the question, the findings and the calculator's results, and writes a cited report.
Then code (not a model) checks every link in the report against what the researchers actually read.
"""

import asyncio
import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

import uvicorn
from agents import Agent, ModelSettings, RunContextWrapper, Runner, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from radar import edgar
from radar.context_panel import AgentContexts, PanelHooks, add_context_panel
from radar.standards import RELATIONSHIPS, STANDARDS, assess

HERE = Path(__file__).parent
STATIC = HERE / "static"
load_dotenv(HERE / ".env")
set_tracing_disabled(True)  # traces upload to OpenAI by default; we're on Gemini

# LiteLLM routes to Gemini on Vertex AI, using the gcloud / Cloud Run service account credentials.
MODEL = LitellmModel(model="vertex_ai/gemini-3.5-flash", api_key="unused")
RESEARCHER_MODEL = LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused")
# A stalled call gives up after 60 s and retries once. The run-level budgets below are the real cap.
SETTINGS = ModelSettings(extra_args={"vertex_location": "global", "timeout": 60, "num_retries": 1})

MAX_RESEARCHERS = 6  # in all, across every round. Prompts ask for restraint; code enforces it.
RESEARCH_BUDGET_S = 120  # graders wait 5 minutes: after this, the Writer works with what's in.
WRITER_BUDGET_S = 120  # after this, the report is assembled from the findings without the Writer.
TOOL_RESULT_CHARS = 6000  # how much of a tool result /chat returns


@dataclass
class Research:
    """One run's state, shared by every agent and tool. The models never see it."""

    hooks: PanelHooks
    researchers: int = 0
    findings: list[dict] = field(default_factory=list)  # {researcher, task, text}
    assessments: list[dict] = field(default_factory=list)  # the calculator's results, for the chart
    sources: dict[str, str] = field(default_factory=dict)  # url -> label, everything a tool read
    tool_calls: list[dict] = field(default_factory=list)  # {agent, name, args, result}
    # Citations: models write short ids like [S12]; code swaps in the real link after the Writer.
    # Long URLs copied by a model get mangled (a dropped word breaks a text-fragment link).
    cites: dict[str, dict] = field(default_factory=dict)  # "S12" -> {label, url}
    cite_ids: dict[tuple, str] = field(default_factory=dict)  # (url, paragraph) -> "S12"

    def cite(self, url: str, label: str, key=None) -> str:
        key = (url, key)
        if key not in self.cite_ids:
            cid = f"S{len(self.cites) + 1}"
            self.cite_ids[key] = cid
            self.cites[cid] = {"label": label, "url": url}
        return self.cite_ids[key]


# filing URL -> "DEF 14A 2026", filled by list_filings, for citation labels
_filing_labels: dict[str, str] = {}


# --- Tools ---------------------------------------------------------------------------------------


def _company(ticker: str) -> dict | None:
    matches = edgar.find_company(ticker)
    return matches[0] if matches else None


@function_tool
def find_company(query: str) -> str:
    """Find a company by ticker or name. Returns ticker, CIK, name, listing exchange and whether it
    is in the Russell 1000 ('yes', 'no', or 'unknown').

    Args:
        query: A ticker ('TSLA') or a company name ('Tesla').
    """
    matches = edgar.find_company(query)
    if not matches:
        return json.dumps({"matches": [], "note": f"No listed SEC filer matches '{query}'."})
    return json.dumps({"matches": matches})


@function_tool
async def list_filings(ctx: RunContextWrapper[Research], ticker: str, form: str) -> str:
    """List a company's most recent filings of one form, newest first, with their URLs.

    Args:
        ticker: The company's ticker.
        form: 'DEF 14A' (proxy statement: related person transactions, director independence) or
            '10-K' (annual report: related party note in the financial statements, Item 13).
    """
    company = _company(ticker)
    if not company:
        return json.dumps({"error": f"Unknown ticker {ticker}"})
    forms = {"DEF 14A": ["DEF 14A"], "10-K": ["10-K", "10-K/A"]}.get(form.strip().upper().replace("PROXY", "DEF 14A"), [form])
    try:
        filings = await edgar.list_filings(int(company["cik"]), forms, limit=3)
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})
    for f in filings:
        _filing_labels[f["url"]] = f"{company['ticker']} {f['form']} {f['filed'][:4]}"
    return json.dumps({"company": company["name"], "filings": filings})


def _passage(state: Research, url: str, p: dict, chars: int = 1200) -> str:
    text = p["text"] if len(p["text"]) <= chars else p["text"][:chars] + " [...]"
    label = f"{_filing_labels.get(url, 'filing')} ¶{p['i']}"
    cid = state.cite(edgar.cite_url(url, p["text"]), label, key=p["i"])
    return f"[para {p['i']}] Section: {p['heading'] or '(none)'}\n{text}\nCite as: [{cid}]"


@function_tool
async def search_filing(ctx: RunContextWrapper[Research], url: str, query: str) -> str:
    """Search one filing for the passages that best match a query. Returns up to 6 passages, each
    with its paragraph number, section heading, text, and a citation id like [S12] to cite it by. Put exact phrases in double quotes.

    Args:
        url: The filing's URL, from list_filings.
        query: What to look for, e.g. '"related person transactions" son daughter employed compensation'.
    """
    try:
        paragraphs = await edgar.get_document(url)
    except Exception as e:
        return f"Could not read {url}: {type(e).__name__}: {e}"
    ctx.context.sources[url] = "filing"
    hits = edgar.search_paragraphs(paragraphs, query, k=6)
    if not hits:
        return f"No passages match '{query}' in this filing ({len(paragraphs)} paragraphs). Try other words."
    return f"{len(paragraphs)} paragraphs in the filing. Best matches:\n\n" + "\n\n".join(_passage(ctx.context, url, p) for p in hits)


@function_tool
async def read_paragraphs(ctx: RunContextWrapper[Research], url: str, start: int, count: int = 6) -> str:
    """Read consecutive paragraphs of a filing, to see the rest of a section or table that a search hit is in.

    Args:
        url: The filing's URL.
        start: The first paragraph number to read (from a search result's [para N]).
        count: How many paragraphs, at most 10.
    """
    try:
        paragraphs = await edgar.get_document(url)
    except Exception as e:
        return f"Could not read {url}: {type(e).__name__}: {e}"
    ctx.context.sources[url] = "filing"
    chunk = paragraphs[max(0, start) : max(0, start) + min(max(count, 1), 10)]
    return "\n\n".join(_passage(ctx.context, url, p, chars=2500) for p in chunk) or "No paragraphs there."


@function_tool
async def get_financials(ctx: RunContextWrapper[Research], ticker: str) -> str:
    """Annual revenue and total assets for a public company's last few fiscal years, from the XBRL
    data in its 10-K filings. Use it for the company itself and for a public counterparty, since
    materiality tests compare an amount with the recipient's revenue.

    Args:
        ticker: The company's ticker.
    """
    company = _company(ticker)
    if not company:
        return json.dumps({"error": f"No listed SEC filer with ticker {ticker}: its revenue is not in SEC data."})
    try:
        fin = await edgar.get_financials(int(company["cik"]))
    except Exception as e:
        return json.dumps({"error": f"No XBRL financials for {ticker}: {type(e).__name__}: {e}"})
    cik = int(company["cik"])
    for kind in ("revenue", "total_assets"):
        for row in fin[kind]:
            url = edgar.INDEX_URL.format(cik=cik, acc=row["accession"].replace("-", ""))
            ctx.context.sources[url] = "financials"
            label = f"{company['ticker']} {row['form']} FY{row['fiscal_year_end'][:4]} {kind.replace('_', ' ')}"
            row["cite_as"] = f"[{ctx.context.cite(url, label, key=(kind, row['fiscal_year_end']))}]"
    return json.dumps(fin)


@function_tool
def get_materiality_standards() -> str:
    """The standards that decide where the line is: SEC Item 404(a) disclosure, and ISS's director
    independence tests (which restate the NYSE and Nasdaq payment tests), with quotes and URLs."""
    return json.dumps(STANDARDS)


ADVISORY = re.compile(
    r"legal|law firm|counsel|attorney|consult|advis|investment bank|banking|financ|invest|insur|account|audit|"
    r"marketing|property manag|real estate|realtor|brokerage|lobby|executive search|recruit", re.I)


async def _revenue(company: dict | None) -> tuple[float | None, str | None, bool]:
    """(revenue, label, is_floor) from XBRL. Code looks it up: the model never types a revenue figure.
    is_floor: only year-to-date revenue exists (a recent listing with no 10-K yet)."""
    if not company:
        return None, None, False
    try:
        fin = await edgar.get_financials(int(company["cik"]))
    except Exception:
        return None, None, False
    if fin["revenue"]:
        row = fin["revenue"][0]
        return float(row["usd"]), f"{company['name']} ({company['ticker']}, FY ending {row['fiscal_year_end']})", False
    if fin.get("revenue_ytd"):
        row = fin["revenue_ytd"]
        return float(row["usd"]), f"{company['name']} ({company['ticker']}, {row['start']} to {row['end']})", True
    return None, None, False


@function_tool
async def assess_materiality(
    ctx: RunContextWrapper[Research],
    ticker: str,
    transaction: str,
    related_person: str,
    relationship: str,
    direction: str,
    source: str,
    insider_role: str,
    amount_usd: float | None = None,
    amount_note: str | None = None,
    recipient_name: str | None = None,
) -> str:
    """Test one transaction against every standard that fits it. Never do this arithmetic yourself.
    The recipient's revenue is looked up for you: the company's own when it receives the money, or
    the counterparty's (if it is a listed company) from recipient_name.

    Args:
        ticker: The company whose filing disclosed the transaction.
        transaction: A short label, e.g. 'Hartung son-in-law employment'.
        related_person: Who the insider is and how they are related, e.g. 'son-in-law of director Jack Hartung'.
        amount_usd: The annual amount in US dollars, as a number, ONLY if the filing states one. For
            'in excess of $120,000' use 120001. For 'approximately $2.3 billion' use 2300000000.
            If the filing gives no dollar figure, leave it out: never estimate or invent one.
        amount_note: The filing's own words about the amount when it gives no figure or only a bound,
            e.g. 'less than 4% of WilmerHale's total revenue'.
        relationship: One of:
            professional_services: ONLY advisory services, per ISS: investment banking or financial
              advice, commercial banking beyond deposits, investment services, insurance, accounting
              or audit, consulting, marketing, legal, property management, realtor, lobbying,
              executive search, IT consulting.
            transactional: everything else bought or sold: products, components, vehicles, leases,
              loans, aircraft, security, construction, IT support, deposits, advertising purchases.
            charitable_grant, family_employment (the company employs an insider's RELATIVE),
            executive_compensation (an executive's or director's OWN pay: salary, bonus, equity,
              or notes/awards given as pay and shown in the compensation tables), other.
        direction: 'company_pays' (the company pays the other party) or 'company_receives'.
        source: The citation id of the passage that states the amount, e.g. 'S12'.
        insider_role: Who the related person is to the company: 'outside_director' (a non-employee
            director, or that director's family member), 'executive' (an executive officer, including
            a CEO who also sits on the board, or their family), 'holder' (a 5% holder), or 'former'
            (no longer a director, officer or 5% holder, e.g. 'former director', or someone who was
            an insider only of a predecessor such as a SPAC before a merger).
        recipient_name: When the company pays the other party: that party's name exactly as the
            filing writes it, e.g. 'Broadcom Inc.', 'SpaceX', 'Redwood Materials'. Never a ticker.
    """
    company = _company(ticker)
    exchange = company["exchange"] if company else "Nasdaq"
    # ISS's professional-services line is $10,000, so a mislabel turns any purchase "material".
    # Only advisory work qualifies (ISS footnote 7): anything else is tested as transactional.
    relationship_note = None
    if relationship == "professional_services" and insider_role != "outside_director":
        relationship, relationship_note = "transactional", (
            "ISS's $10,000 professional-services line protects outside directors' independence; this insider is "
            f"{'an executive (already non-independent under ISS)' if insider_role == 'executive' else 'a major holder'}, "
            "so the deal is judged on its size as a transactional relationship.")
    elif relationship == "professional_services" and direction == "company_receives":
        relationship, relationship_note = "transactional", ("The company provides the service here; ISS footnote 7 treats a company "
                                                            "serving a director's affiliate as a transactional relationship.")
    elif relationship == "professional_services" and not ADVISORY.search(f"{transaction} {related_person} {recipient_name or ''}"):
        relationship, relationship_note = "transactional", "Not advisory work under ISS footnote 7, so tested as a transactional relationship."
    revenue, revenue_source, is_floor, label = None, None, False, None
    if direction == "company_receives":
        revenue, revenue_source, is_floor = await _revenue(company)
        label = company["name"] if company else None
    elif recipient_name:
        counterparty = edgar.resolve_counterparty(recipient_name)
        revenue, revenue_source, is_floor = await _revenue(counterparty)
        label = counterparty["name"] + f" ({counterparty['ticker']})" if counterparty else recipient_name
    result = assess(amount_usd, relationship, exchange, direction, revenue, recipient_label=label, revenue_is_floor=is_floor)
    if insider_role == "former" and relationship != "executive_compensation":
        # ISS 2.12 / 2.13 test what a director "currently" provides or has: a former insider's deal is
        # still disclosed under Item 404, but it no longer bears on anyone's independence.
        result["results"] = [r for r in result["results"] if r["standard"] == "sec_item_404a"] + [{
            "standard": "iss_current_only", "threshold_usd": None, "status": "not_applicable_to_amount",
            "why": "The related person is no longer an insider. ISS's tests ask whether a director currently provides "
                   "services or currently has a material relationship, so the deal is disclosed but not tested for anyone's "
                   "independence (it can still be ongoing: only the insider is former)."}]
    source_id = source.strip("[] ")
    source_url = ctx.context.cites.get(source_id, {}).get("url", "")
    result.update(ticker=ticker, transaction=transaction, related_person=related_person, source=source_id, amount_note=amount_note, relationship_note=relationship_note, insider_role=insider_role,
                  source_url=source_url, recipient_revenue_source=revenue_source)
    # Two agents may assess the same deal under different labels: same source and amount is the same deal
    # The same deal assessed twice (two researchers, two labels): same label, or the same exact amount
    # in the same direction. Keep the version that knows the recipient's revenue.
    def same(a):
        if a["transaction"].lower() == transaction.lower() or (a["source"] == source_id and a["amount_usd"] == amount_usd):
            return True
        return amount_usd is not None and a["amount_usd"] == amount_usd and a["direction"] == direction and (amount_usd - 1) % 1000 != 0
    dupes = [a for a in ctx.context.assessments if same(a)]
    if any(a.get("recipient_revenue_source") for a in dupes) and not revenue_source:
        return json.dumps({**result, "note": "Already assessed with the recipient's revenue; kept that result."})
    ctx.context.assessments = [a for a in ctx.context.assessments if not same(a)]
    ctx.context.assessments.append(result)
    return json.dumps(result)


# --- Researcher ------------------------------------------------------------------------------------

researcher = Agent(
    name="Researcher",
    instructions=f"""\
You research one task about one company's related-party (insider) transactions in its SEC filings.

1. Use the filing URLs you are given: the latest DEF 14A proxy, or the latest 10-K for the
   financial-statement note. Use the previous year's only if your task asks about last year.
2. Search it with search_filing. Useful words: "related person transactions", "certain relationships",
   "director independence", "immediate family", "son", "daughter", "brother", "spouse", "employed",
   "lease", "aircraft", "purchased", "ordinary course", "% of", "revenues", "charitable", "consulting".
   When a hit is the start of a section or a list, read on with read_paragraphs.
3. For every specific transaction with a named or described related person, call assess_materiality
   once. A general statement ("no director had a material interest in these relationships") is a
   finding to report, not a transaction: don't assess it. An insider's own pay (salary, bonus,
   equity, notes or awards given as compensation) is not a related-party transaction either: SEC
   Item 404 excludes it. Mention it only if your task asks, as executive_compensation. If the filing gives no dollar figure (only
   "less than 4% of the firm's revenue", say), leave amount_usd out and quote the words in amount_note. If the company pays a
   counterparty, pass its name as the filing writes it as recipient_name ('Broadcom Inc.',
   'SpaceX'). Code finds its revenue if it is listed. Never guess a ticker.
4. Reply with at most 10 bullets of facts that answer your task, and nothing else. Every bullet names
   the people, the relationship, the amount and the fiscal year where given, and ends with the
   citation id of the passage it came from, exactly as the tool gave it: [S12].
   Quote the filing's own words for amounts ("in excess of $120,000", "approximately $150,000").
   If the filings don't answer part of your task, say so in a last bullet that starts "Not found:".

Use at most 8 tool calls. Never write URLs and never invent a citation id: only ids a tool returned.
Relationship types for assess_materiality: {", ".join(RELATIONSHIPS)}.""",
    model=RESEARCHER_MODEL,
    model_settings=SETTINGS,
    tools=[list_filings, search_filing, read_paragraphs, get_financials, find_company, assess_materiality],
)


@function_tool
async def research(ctx: RunContextWrapper[Research], task: str, ticker: str) -> str:
    """Send a researcher, in a fresh context, to answer one task from a company's filings.
    Returns its findings, each with a link to the passage it came from.

    Args:
        task: One specific thing to find out, e.g. 'List every related person transaction disclosed
            in the latest proxy, with the people, relationship and amount'.
        ticker: The company's ticker.
    """
    if ctx.context.researchers >= MAX_RESEARCHERS:
        return "No researchers left. Reply DONE."
    ctx.context.researchers += 1
    n = ctx.context.researchers
    agent = researcher.clone(name=f"Researcher {n}")
    company = _company(ticker) or {"ticker": ticker}
    # Code picks the latest filings so a researcher can't wander into an old one by mistake
    latest = []
    if company.get("cik"):
        for forms in (["DEF 14A"], ["10-K", "10-K/A"]):
            try:
                found = await edgar.list_filings(int(company["cik"]), forms, limit=2)
            except Exception:
                found = []
            for f in found:
                _filing_labels[f["url"]] = f"{company['ticker']} {f['form']} {f['filed'][:4]}"
            if found:
                latest.append(f"- Latest {found[0]['form']} (filed {found[0]['filed']}): {found[0]['url']}")
            if len(found) > 1 and re.search(r"last year|previous|prior|trend|compare|change|202[0-9]", task, re.I):
                latest.append(f"- Previous {found[1]['form']} (filed {found[1]['filed']}), only if the task asks about last year: {found[1]['url']}")
    filings = "\n".join(latest) or "(use list_filings)"
    prompt = f"Task: {task}\nCompany: {json.dumps(company)}\nFilings to use (start with the latest):\n{filings}"
    try:
        result = await Runner.run(agent, prompt, context=ctx.context, hooks=ctx.context.hooks, max_turns=12)
        text = str(result.final_output)
    except Exception as e:  # a researcher that runs out of turns shouldn't sink the others
        text = f"- Not found: this researcher stopped early ({type(e).__name__})."
    ctx.context.findings.append({"researcher": agent.name, "task": task, "text": text})
    done = "; ".join(f"{a['transaction']} ({_amount(a)})" for a in ctx.context.assessments) or "none yet"
    return f"{text}\n\n[Calculator has assessed so far: {done}]"


# --- Lead -------------------------------------------------------------------------------------------

lead = Agent(
    name="Lead",
    instructions="""\
You lead a team researching a public company's related-party transactions: deals between the company
and its directors, executive officers, 5% holders or their families, and whether any cross the lines
in SEC Item 404 and ISS's director-independence tests.

1. Call find_company to confirm the company, its exchange and its Russell 1000 status.
2. In ONE turn, call research 3 times so the researchers work in parallel. Cover:
   a. Every related person transaction disclosed in the latest proxy (DEF 14A): who, relationship,
      what, amount, year.
   b. The proxy's director independence discussion: relationships the board considered (payments to
      or from directors' other companies, charities, law firms) and the amounts or percentages given.
   c. The latest 10-K: the related party note in the financial statements and Item 13 (it often
      refers back to the proxy: say so if it does).
   Don't send a researcher for revenue: the calculator looks up every revenue figure itself.
   Say "latest", never a year: your sense of the current year is out of date, and each researcher
   is handed the latest filings. Shape the tasks to the user's question: if it names a person or
   deal, target that.
3. Read the findings. Every transaction in them that has a dollar amount must go through
   assess_materiality: call it yourself for any the researchers stated but didn't assess (the list of
   assessed ones follows each researcher's findings). Don't re-assess one already on that list. Use
   the citation id the finding gives as source, and recipient_name for the counterparty.
   If there is a gap that matters, call research again for just that gap, at most twice. Typical gaps: a counterparty that may be a public company whose revenue would decide a
   test; a transaction mentioned without an amount; last year's proxy, if the user asked about a trend.
4. When the question is covered, reply DONE and nothing else. A writer writes the report.""",
    model=MODEL,
    model_settings=SETTINGS,
    tools=[find_company, get_materiality_standards, research, assess_materiality],
)


# --- Clarifier ----------------------------------------------------------------------------------------


class Decision(BaseModel):
    ready: bool
    question_to_user: str  # when not ready: one short question, with 2-3 concrete options
    ticker: str  # when ready
    research_question: str  # when ready: the question rewritten so it stands alone


clarifier = Agent(
    name="Clarifier",
    instructions="""\
You check a user's question before a research team spends five minutes on it. The team researches ONE
or TWO public US companies' related-party transactions (deals with directors, executives, big holders
and their families) in SEC filings, and tests them against SEC Item 404 and ISS independence lines.

You get the conversation so far. Use find_company to check any company named.
Set ready=true, with the ticker and a standalone research_question, when:
- a company is identifiable (a name or ticker that find_company matches clearly), and
- the question is about insider / related-party dealings, independence, conflicts of interest, or is a
  general "does X have material related-party transactions" question.
Set ready=false and ask ONE short question (offer 2-3 concrete options) when:
- no company is named ("which companies have shady deals?"): ask which company, and suggest examples;
- the name could really mean two well-known companies equally (not "Apple": that is Apple Inc., not
  Apple Hospitality REIT). Take the obvious, largest match without asking; ask only when you
  genuinely can't tell, listing the options with tickers;
- the company is marked russell1000 'no': say it is outside the Russell 1000 scope and ask for another;
- "material transaction" clearly means something else (an acquisition, a big customer contract): ask
  whether they mean related-party deals with insiders, which is what this tool checks.
Don't ask about the year or the standard: the team uses the latest filings and every standard.
If the user already answered a question of yours, combine their answer with the original question.""",
    model=MODEL,
    model_settings=SETTINGS,
    tools=[find_company],
    output_type=Decision,
)


# --- Writer ------------------------------------------------------------------------------------------

writer = Agent(
    name="Writer",
    instructions="""\
Write a report in markdown that answers the question using only the findings and the calculator
results you're given. The reader is an investor or governance analyst deciding how to vote.

Structure, exactly these headings:
## Bottom line
Two to four plain sentences a voter can act on: what kinds of related-party deals the company has,
whether any crosses an independence line, and which. Agree with the calculator's counts. If a
calculator line says the deal would cross under the other exchange's test, say so here: it is the
most useful fact for a voter. Cite at most
two ids per sentence here: the table below carries every source.
[[TRANSACTIONS_TABLE]]
(Write that placeholder line exactly as shown. Code puts the table of transactions there.)
## How each one was judged
One short paragraph per transaction, with the arithmetic from the calculator's "why". Amounts exactly
as the calculator writes them ($3,300,000, never $3,300,000.0).
## Limits of public data
Start with one sentence: these are limits of what companies must disclose, not gaps in the research.
Then bullets: tests that need a private counterparty's revenue (say which counterparties: the test
divides by the recipient's revenue, the recipient doesn't publish it, so only the board and the
counterparty can run it); amounts given only as "less than" or "in excess of"; deals of $120,000 or
less, which never have to be disclosed; things the filings don't say (from "Not found:" notes in
the findings). Label bullets by the limit itself, e.g. "Private counterparties' revenue".
## Standards applied
One line each, linked: SEC Item 404(a), ISS 2026 U.S. guidelines.

Rules:
- Every sentence that states a fact ends with the citation id(s) of its source, copied from the
  findings: [S4] or [S4][S9]. Never write a URL for a filing; code turns the ids into links.
- Never invent a citation id or a number. If the findings don't say, write that they don't.
- For a test that needs private data, never write "can't be determined" alone: say it needs the
  private counterparty's revenue, which isn't public.
- "Material" for SEC disclosure is not the same as "material" for independence: keep them apart.
- Write as the report's author, about the company. Never mention the calculator, the tally, the
  findings, the researchers, "our analysis" or these instructions.
- Plain, specific sentences. No "pivotal", "notably", "it is worth noting".""",
    model=MODEL,
    model_settings=SETTINGS,
)


# --- Citation check (code, not a model) -----------------------------------------------------------

LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
CITE_ID = re.compile(r"\[(S\d+(?:\s*[,;]\s*S\d+)*)\]")


def resolve_citations(report: str, state: Research) -> tuple[str, list[dict]]:
    """[S12] -> [TSLA DEF 14A 2026 ¶365](link). An id no tool handed out is marked, not linked."""
    rows = []

    def one(cid: str) -> str:
        c = state.cites.get(cid)
        if not c:
            rows.append({"label": cid, "url": None, "status": "unknown_id"})
            return f"(unknown source {cid})"
        rows.append({"label": c["label"], "url": c["url"], "status": "id"})
        return f"[{c['label']}]({c['url']})"

    out = CITE_ID.sub(lambda m: " ".join(one(cid) for cid in re.split(r"\s*[,;]\s*", m.group(1))), report)
    return out, rows
STANDARD_URLS = {s["url"] for s in STANDARDS.values()}


def check_citations(report: str, id_rows: list[dict] | None = None) -> dict:
    """Every link in the report: did a tool read that page, and does the quoted passage exist in it?"""
    rows = []
    unknown = [r for r in (id_rows or []) if r["status"] == "unknown_id"]
    for label, url in LINK.findall(report):
        base, _, fragment = url.partition("#:~:text=")
        base = base.split("#")[0]
        row = {"label": label, "url": url, "status": "unverified"}
        if base in STANDARD_URLS:
            row["status"] = "standard"
        elif base in edgar._doc_cache:
            row["status"] = "filing"
            if fragment:
                words = unquote(fragment)
                text = " ".join(" ".join(p["text"].split()) for p in edgar._doc_cache[base])
                row["status"] = "passage" if words in text else "filing_passage_not_found"
        elif base.startswith("https://www.sec.gov/Archives/edgar/data/") and base.endswith("/"):
            row["status"] = "filing_index"  # a 10-K's index page, cited for XBRL financials
        rows.append(row)
    ok = sum(r["status"] in ("passage", "filing", "standard", "filing_index") for r in rows)
    return {"total": len(rows) + len(unknown), "verified": ok, "links": rows + unknown}


def fallback_report(question: str, state: Research, why: str) -> str:
    """When the Writer fails: the calculator's table and the raw findings, still cited."""
    lines = [f"## Bottom line", "", f"_The writer step failed ({why}), so this is the research team's raw output._", "",
             "[[TRANSACTIONS_TABLE]]", "", "## Findings", ""]
    lines += [f"### {f['researcher']}: {f['task']}\n{f['text']}\n" for f in state.findings]
    return "\n".join(lines)


STATUS_WORDS = {
    "crossed": "crosses",
    "not_crossed": "does not cross",
    "cannot_determine": "needs private data (the recipient's revenue is not public)",
    "not_applicable_to_amount": "no dollar test",
    "excluded": "excluded: the executive's own pay, reported under Item 402 (Item 404 Instruction 5.a.i)",
}
TABLE_WORDS = {"crossed": "✕ Material", "not_crossed": "✓ Not material", "cannot_determine": "Needs private data", "not_applicable_to_amount": "– No dollar test"}
SEC_WORDS = {"crossed": "Required", "not_crossed": "Not required", "excluded": "Excluded: own pay (Item 402)"}


def _amount(a: dict) -> str:
    v = a.get("amount_usd")
    if v is None:
        return "Not disclosed" + (f" ({a['amount_note']})" if a.get("amount_note") else "")
    if v > 1000 and (v - 1) % 1000 == 0:  # the "in excess of $120,000" convention: 120001
        return f"More than ${v - 1:,.0f}"
    return f"${v:,.0f}"


def _independence(a: dict) -> dict | None:
    return next((r for r in a["results"] if r["standard"] != "sec_item_404a"), None)


def transactions_table(assessments: list[dict]) -> str:
    """Built from the calculator, not written by a model: every row matches the chart and the verdict."""
    if not assessments:
        return "## Transactions found\n\nNo related-party transaction with a dollar amount was found in the filings read."
    order = {"crossed": 0, "cannot_determine": 1, "not_crossed": 2, "not_applicable_to_amount": 3}
    rows = sorted(assessments, key=lambda a: (order[(_independence(a) or {"status": "not_applicable_to_amount"})["status"]], -(a["amount_usd"] or 0)))
    lines = ["## Transactions found", "",
             "| Related person | Transaction | Amount | SEC 404 disclosure | Independence test | Source |",
             "|---|---|---:|---|---|---|"]
    for a in rows:
        sec = next(r for r in a["results"] if r["standard"] == "sec_item_404a")
        ind = _independence(a)
        lines.append(
            f"| {a['related_person']} | {a['transaction']} | {_amount(a)} | "
            f"{SEC_WORDS.get(sec['status'], 'Amount not disclosed')} | "
            f"{'– Own pay, not a related-party deal' if ind and ind['standard'] == 'iss_executive' else '– Former insider, not tested' if ind and ind['standard'] == 'iss_current_only' else TABLE_WORDS[ind['status']] if ind else TABLE_WORDS['not_applicable_to_amount']} | "
            f"{'[' + a['source'] + ']' if a.get('source') else ''} |"
        )
    return "\n".join(lines)


def verdict(assessments: list[dict]) -> dict:
    """The company-level answer. Material = at least one deal crosses an independence line (ISS /
    NYSE / Nasdaq). Crossing SEC's $120,000 line only means the deal must be disclosed."""
    # An insider's own pay is not a related-party transaction (Item 404 Instruction 5), so it doesn't count
    assessments = [a for a in assessments if a.get("relationship") != "executive_compensation"]
    statuses = [(_independence(a) or {"status": "not_applicable_to_amount"})["status"] for a in assessments]
    n, crossed, private = len(statuses), statuses.count("crossed"), statuses.count("cannot_determine")
    if not n:
        return {"level": "none", "label": "No related-party transactions with amounts found",
                "detail": "The filings read disclose no related-party transaction with a dollar amount."}
    if crossed:
        return {"level": "material", "label": "Material",
                "detail": f"{crossed} of {n} transactions cross an independence materiality line."}
    if private:
        return {"level": "public_not_material", "label": "Not material on public data",
                "detail": f"None of {n} transactions crosses a line that public data can test; {private} can only be "
                "tested with a private counterparty's revenue."}
    return {"level": "not_material", "label": "Not material", "detail": f"None of {n} transactions crosses an independence materiality line."}


def calculator_digest(assessments: list[dict]) -> str:
    """The calculator's results as fixed lines and a tally, so the Writer copies verdicts instead of re-deriving them."""
    if not assessments:
        return "No transaction with a dollar amount was assessed."
    tally: dict[str, int] = {}
    rows = []
    for a in assessments:
        sec = next(r for r in a["results"] if r["standard"] == "sec_item_404a")
        ind = next((r for r in a["results"] if r["standard"] != "sec_item_404a"), None)
        ind_word = STATUS_WORDS[ind["status"]] if ind else "no independence test applies"
        tally[ind_word] = tally.get(ind_word, 0) + 1
        rows.append(
            f"- {a['transaction']} | {a['related_person']} | {_amount(a)} | {a['direction'].replace('_', ' ')} | "
            f"SEC 404: {STATUS_WORDS[sec['status']]} | Independence ({ind['standard'] if ind else '-'}): {ind_word} | "
            f"why: {ind['why'] if ind else sec['why']}{' ' + a['relationship_note'] if a.get('relationship_note') else ''} | source: [{a['source']}]"
        )
    summary = "; ".join(f"{word}: {n}" for word, n in tally.items())
    return f"Counts by independence result (for you only: state them in plain words, e.g. 'three are under the line and one needs private data'; never copy this line): {summary}.\n" + "\n".join(rows)


# --- The run -----------------------------------------------------------------------------------------


class ToolHooks(PanelHooks):
    """The context panel's hooks, plus a record of every tool call for /chat's tool_calls."""

    def __init__(self, contexts: AgentContexts, emit, calls: list[dict]):
        super().__init__(contexts, emit)
        self.calls = calls

    async def on_tool_end(self, context, agent, tool, result):
        try:
            args = json.loads(getattr(context, "tool_arguments", "") or "{}")
        except ValueError:
            args = {}
        text = str(result)
        self.calls.append({"agent": agent.name, "name": tool.name, "args": args, "result": text[:TOOL_RESULT_CHARS]})
        self.emit({"type": "tool", "agent": agent.name, "name": tool.name, "args": args, "result": text[:400]})


@dataclass
class Session:
    contexts: AgentContexts = field(default_factory=AgentContexts)
    history: list[dict] = field(default_factory=list)  # {role, content}: what the Clarifier sees
    # The latest run's outcome, so a page that lost its stream (laptop asleep, tab switched) can pick it up
    status: str = "idle"  # idle | running | done
    last: dict | None = None


sessions: dict[str, Session] = {}


def _transcript(history: list[dict]) -> str:
    return "\n\n".join(f"{m['role'].upper()}: {m['content'][:1500]}" for m in history)


async def answer(session: Session, message: str, emit) -> dict:
    calls: list[dict] = []
    hooks = ToolHooks(session.contexts, emit, calls)
    state = Research(hooks=hooks, tool_calls=calls)
    session.history.append({"role": "user", "content": message})

    # 1. Clarify: is there a company, and is this the kind of question we answer?
    decision = (await Runner.run(clarifier, _transcript(session.history), context=state, hooks=hooks, max_turns=5)).final_output
    if not decision.ready:
        session.history.append({"role": "assistant", "content": decision.question_to_user})
        return {"kind": "clarify", "markdown": decision.question_to_user, "tool_calls": calls}
    emit({"type": "plan", "ticker": decision.ticker, "question": decision.research_question})

    # 2. Research: plan, fan out, fill gaps. Past the time budget, the Writer gets what's in.
    prompt = f"Question: {decision.research_question}\nCompany: {decision.ticker}"
    try:
        await asyncio.wait_for(Runner.run(lead, prompt, context=state, hooks=hooks, max_turns=10), RESEARCH_BUDGET_S)
    except (asyncio.TimeoutError, Exception) as e:
        state.findings.append({"researcher": "Lead", "task": "(run note)", "text": f"- Not found: research stopped early ({type(e).__name__}); the report covers what was found."})

    # 3. Write: one call, outside the loop. The Writer sees only the question, findings and calculations.
    findings = "\n\n---\n\n".join(f"### {f['researcher']}: {f['task']}\n{f['text']}" for f in state.findings)
    calcs = calculator_digest(state.assessments)
    standards = "\n".join(f"- {s['name']}: {s['line']} ({s['url']})" for s in STANDARDS.values())
    writer_prompt = (
        f"Question: {decision.research_question}\nCompany: {decision.ticker}\n\nFindings:\n\n{findings}\n\n"
        f"Calculator results:\n{calcs}\n\nStandards:\n{standards}"
    )
    report = None
    # Vertex quotas are per model: if the main model is rate-limited or stalls, the lite model writes.
    for model, budget in ((MODEL, WRITER_BUDGET_S * 0.6), (RESEARCHER_MODEL, WRITER_BUDGET_S * 0.4)):
        try:
            agent = writer if model is MODEL else writer.clone(model=model)
            result = await asyncio.wait_for(Runner.run(agent, writer_prompt, context=state, hooks=hooks, max_turns=2), budget)
            report = str(result.final_output)
            break
        except (asyncio.TimeoutError, Exception) as e:
            error = type(e).__name__
    if report is None:
        report = fallback_report(decision.research_question, state, error)
    # Code-built pieces: the transactions table and the verdict next to "Bottom line"
    table = transactions_table(state.assessments)
    if "[[TRANSACTIONS_TABLE]]" in report:
        report = report.replace("[[TRANSACTIONS_TABLE]]", table)
    elif "## How each one was judged" in report:
        report = report.replace("## How each one was judged", table + "\n\n## How each one was judged", 1)
    else:
        report += "\n\n" + table
    final = verdict(state.assessments)
    report = re.sub(r"^## Bottom line.*$", f"## Bottom line · {final['label']}", report, count=1, flags=re.M)
    report, id_rows = resolve_citations(report, state)
    session.history.append({"role": "assistant", "content": report})

    return {
        "kind": "report",
        "markdown": report,
        "ticker": decision.ticker,
        "company": _company(decision.ticker),
        "assessments": state.assessments,
        "verdict": final,
        "citations": check_citations(report, id_rows),
        "tool_calls": calls,
    }


# --- FastAPI -------------------------------------------------------------------------------------------

app = FastAPI(title="Related Party Radar")


class _Contexts(dict):
    """The context panel reads sessions[session_id] -> AgentContexts."""

    def get(self, key, default=None):
        session = sessions.get(key)
        return session.contexts if session else default


add_context_panel(app, _Contexts())


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list[dict]


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Project 1's shape. tool_calls holds every agent's calls, each with an agent field."""
    session_id = request.session_id or str(uuid.uuid4())
    session = sessions.setdefault(session_id, Session())
    try:
        result = await answer(session, request.message, lambda event: None)
        response, calls = result["markdown"], result["tool_calls"]
    except Exception as e:
        response, calls = f"Research failed: {type(e).__name__}: {str(e)[:300]}", []
    return ChatResponse(response=response, session_id=session_id, tool_calls=calls)


@app.get("/run")
async def run(message: str, session_id: str | None = None):
    """The same research, streamed as Server-Sent Events for the page."""
    session_id = session_id or str(uuid.uuid4())
    session = sessions.setdefault(session_id, Session())
    queue: asyncio.Queue = asyncio.Queue()

    async def work():
        session.status, session.last = "running", None
        try:
            result = await answer(session, message, queue.put_nowait)
            event = {"type": "done", **result}
        except Exception as e:
            event = {"type": "error", "message": f"{type(e).__name__}: {str(e)[:500]}"}
        session.status, session.last = "done", json.loads(json.dumps(event, default=str))
        queue.put_nowait(event)

    # The run outlives the stream: it is capped at about 4.5 minutes, and a page that reconnects
    # gets the result from /result instead of losing two minutes of research.
    task = asyncio.create_task(work())
    _running.add(task)
    task.add_done_callback(_running.discard)

    async def events():
        try:
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"  # proxies drop idle streams
                    continue
                yield f"data: {json.dumps(event, default=str)}\n\n"
                if event["type"] in ("done", "error"):
                    break
        except asyncio.CancelledError:
            pass  # the page went away; the run keeps going and its result waits at /result

    return StreamingResponse(events(), media_type="text/event-stream")


_running: set[asyncio.Task] = set()  # keep references so runs aren't garbage-collected mid-flight


@app.get("/result")
def result(session_id: str):
    """The latest run's outcome for a session: {status: idle|running|done, event}."""
    session = sessions.get(session_id)
    if not session:
        return {"status": "unknown"}
    return {"status": session.status, "event": session.last if session.status == "done" else None}


@app.post("/clear")
def clear(session_id: str | None = None):
    sessions.pop(session_id, None)
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    return {"ok": True, "companies": len(edgar.universe())}


if __name__ == "__main__":
    import os

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", 8000)))
