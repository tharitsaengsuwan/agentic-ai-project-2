"""Offline build step: data/universe.csv, the companies the agent can research.

    uv run scripts/build_universe.py [path/to/IWB_holdings.csv]

1. SEC's company_tickers_exchange.json gives every listed filer's ticker, CIK, name and exchange.
   The exchange decides which listing standard (NYSE or Nasdaq) the materiality tests use.
2. The iShares Russell 1000 ETF (IWB) holdings file marks which ones are in the Russell 1000.
   Download it by hand from https://www.ishares.com/us/products/239707/ishares-russell-1000-etf
   ("Detailed Holdings and Analytics" -> Download) and save it as data/IWB_holdings.csv.
   Without it, russell1000 is "unknown" for everyone and the agent researches any SEC filer.
"""

import csv
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent  # the repo root
sys.path.insert(0, str(ROOT))

from radar.edgar import TICKERS_URL, UNIVERSE_CSV, user_agent  # noqa: E402

load_dotenv(ROOT / ".env")


def _key(ticker: str) -> str:
    # iShares writes BRKB, SEC writes BRK-B
    return re.sub(r"[^A-Z0-9]", "", ticker.upper())


def read_iwb(path: Path) -> tuple[set[str], str]:
    """Equity tickers in the IWB holdings file, and its 'as of' date."""
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    lines = text.splitlines()
    as_of = next((l.split(",", 1)[1].strip('" ') for l in lines[:10] if l.lower().startswith("fund holdings as of")), "")
    start = next(i for i, l in enumerate(lines) if l.startswith("Ticker,"))
    rows = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    tickers = {_key(r["Ticker"]) for r in rows if r.get("Asset Class") == "Equity" and r.get("Ticker") not in (None, "", "-")}
    return tickers, as_of


def main():
    sec = httpx.get(TICKERS_URL, headers={"User-Agent": user_agent()}, timeout=60).json()
    fields = sec["fields"]  # cik, name, ticker, exchange
    rows = [dict(zip(fields, r)) for r in sec["data"]]

    iwb_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "IWB_holdings.csv"
    members, as_of = (read_iwb(iwb_path) if iwb_path.exists() else (None, ""))

    out = []
    for r in rows:
        if not r["ticker"] or r["exchange"] not in ("NYSE", "Nasdaq", "CBOE"):
            continue
        flag = "unknown" if members is None else ("yes" if _key(r["ticker"]) in members else "no")
        out.append({"ticker": r["ticker"], "cik": r["cik"], "name": r["name"], "exchange": r["exchange"], "russell1000": flag})

    UNIVERSE_CSV.parent.mkdir(exist_ok=True)
    with open(UNIVERSE_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ticker", "cik", "name", "exchange", "russell1000"])
        w.writeheader()
        w.writerows(out)

    meta = {
        "built": date.today().isoformat(),
        "sec_source": TICKERS_URL,
        "russell1000_source": "iShares Russell 1000 ETF (IWB) holdings" if members else None,
        "russell1000_as_of": as_of or None,
        "companies": len(out),
        "russell1000_members_matched": sum(r["russell1000"] == "yes" for r in out),
        "russell1000_tickers_in_file": len(members) if members else None,
    }
    (UNIVERSE_CSV.parent / "universe_meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
