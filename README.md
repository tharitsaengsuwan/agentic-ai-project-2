# Related Party Radar

**Does this company do business with its own insiders, and does any of it cross a line?**

Related Party Radar is a deep-research agent over SEC filings. You name a large US public company and
a team of agents reads its latest proxy statement (DEF 14A) and annual report (10-K) for
**related-party transactions**: deals between the company and its directors, executive officers,
5% holders or their families. Each deal is then tested against the published lines that decide when
such a deal *matters*:

| Line | What it decides | Threshold | Source |
|---|---|---|---|
| SEC Regulation S-K Item 404(a) | Must the company disclose it? | amount > **$120,000** and the related person has a material interest | [17 CFR 229.404](https://www.law.cornell.edu/cfr/text/17/229.404) |
| ISS 2.12, professional services | Is the director independent? | > **$10,000** a year | [ISS U.S. Guidelines 2026](https://www.iss-stoxx.com/file/policy/current/americas/us-voting-guidelines.pdf) |
| ISS 2.13 / fn 8, transactional (restates NYSE 303A.02(b)(v) and Nasdaq 5605(a)(2)(D)) | Is the director independent? | > greater of **$1M or 2%** of recipient's revenue (NYSE); > greater of **$200K or 5%** (Nasdaq) | same |

**Who it's for:** shareholders deciding how to vote on directors, stewardship and governance analysts,
and journalists. Today that work means reading 100+ page proxies by hand. The agent shows the deals,
the arithmetic and a link to the exact sentence in the filing for every fact.

The important distinction it draws: *"material" for SEC disclosure is not "material" for
independence*. A $430M deal can be disclosed under Item 404 and still be far under the line that
makes a director non-independent. And when the line depends on a private company's revenue, the
agent says it can't decide, instead of guessing.

## Deep research design

```
 user ─▶ Clarifier ──(vague? ask one question, stop)
            │
            ▼
          Lead ── fans out in ONE turn ──▶ Researcher 1  (proxy: related person transactions)
            │                         ├─▶ Researcher 2  (proxy: director independence review)
            │                         ├─▶ Researcher 3  (10-K: related-party note, Item 13)
            │                         └─▶ Researcher 4  (XBRL revenue / assets: denominators)
            │      reads findings, assesses any un-assessed deal, sends more for gaps (≤ 6 in all)
            ▼
          Writer (sees only question + findings + calculator lines) ──▶ cited report
            │
            ▼
   citation checker (code): every link was read by a tool, and its quoted passage exists in the filing
```

| Agent | Model | Job | Tools |
|---|---|---|---|
| **Clarifier** | gemini-3.5-flash, structured output | Decide whether the question names one identifiable company and is about insider deals. If not (no company, ambiguous name, "material transaction" meaning an acquisition, outside the Russell 1000), it asks **one** question and the run stops. The answer continues the same `session_id`. | `find_company` |
| **Lead** | gemini-3.5-flash | Plans 3 tasks (proxy transactions, proxy independence review, 10-K note) and calls `research` for all of them **in the same turn**, so Researchers run in parallel in fresh contexts. Reads findings, runs any stated-but-unassessed deal through the calculator, and sends more Researchers for gaps (for example a counterparty that might be public), up to a code-enforced cap of 6. | `find_company`, `get_materiality_standards`, `research`, `assess_materiality` |
| **Researcher ×N** | gemini-3.5-flash-lite | One task. Finds the filing, searches its paragraphs (BM25 over section-tagged paragraphs), reads on, calls the calculator for each deal with an amount, and returns ≤10 bullets that each end with a passage link. Ends with "Not found:" for what the filing doesn't say. | `list_filings`, `search_filing`, `read_paragraphs`, `get_financials`, `find_company`, `assess_materiality` |
| **Writer** | gemini-3.5-flash (falls back to flash-lite if rate-limited) | Writes the report from the findings and the calculator's fixed lines only: bottom line, how each deal was judged, **limits of public data**, and the standards applied. Code inserts the transactions table and the verdict. | none |

**Things done in code, not by the model:**
- **Materiality arithmetic** ([standards.py](standards.py)). The model extracts an amount, a relationship type and who receives the money. `assess()` returns *crossed / not crossed / can't determine* for each standard, with the arithmetic. When the amount is above the floor and the recipient doesn't publish revenue, the result is **needs private data**. The report presents this as a limit of what companies must disclose (the board can see the figure, investors can't), not as a gap in the research. When the filing gives no dollar figure at all ("less than 4% of the firm's revenue"), the model passes no amount and the result is "not disclosed". It may never invent a number.
- **Counterparty revenue, looked up by code.** The model names the counterparty as the filing does ("SpaceX", "Broadcom Inc."), and `resolve_counterparty()` matches it strictly: exact legal name or a short alias list. In testing, the model once guessed SpaceX's ticker as `SPCE` (Virgin Galactic, $1.5M revenue), which made an $11.4M payment look like 738% of the recipient's revenue. Loose matches like "X Corp" → XPO are rejected. A recently listed company with no 10-K yet (SpaceX) is tested against its year-to-date 10-Q revenue as a **floor**: that settles "under the line" for certain, never "over".
- **ISS's classification rules, enforced in code.** The professional-services line is only $10,000, so a mislabel makes any purchase "material". Code applies ISS footnote 7: only *advisory* work counts as professional services (legal, consulting, banking, insurance, audit, marketing, lobbying…), so security, aircraft, components and IT support are tested as transactional. A company providing a service to a director's affiliate is transactional too. The $10,000 test also applies only when the insider is an **outside director** or their family. For an executive like a CEO, whom ISS already treats as non-independent, a deal is judged on its size. Each reclassification is explained in the report. (Found in testing: Musk's $4.8M security services and xAI's $4M consulting to Tesla were both briefly flagged "Material".)
- **Who the tests apply to.** An insider's **own pay** (salary, equity, notes given as compensation) is not a related-party transaction: SEC Item 404 Instruction 5.a.i excludes compensation reported under Item 402, so it shows as "Own pay" and doesn't count toward the verdict. A **former** insider's deal is still disclosed but not tested, because ISS asks what a director *currently* provides or has. Loans and convertible notes from insiders get the ordinary size test (ISS's guidance doesn't treat financing separately), which is the conservative reading.
- **The verdict and the table.** The transactions table and the verdict next to *Bottom line* are built from the calculator results, not written by a model. **Material** = at least one deal crosses an ISS / NYSE / Nasdaq independence line. **Not material on public data** = none crosses, but some need private data to test. **Not material** = everything tested is under its line. Crossing SEC's $120,000 line only means the deal must be disclosed.
- **Passage-level citations by id.** Each passage a tool returns gets a short id (`[S12]`). The models cite only ids. After the Writer, code swaps each id for a [text-fragment](https://developer.mozilla.org/en-US/docs/Web/URI/Fragment/Text_fragments) link labeled with the filing and paragraph (`TSLA DEF 14A 2026 ¶365` → `…def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform…`), which opens sec.gov scrolled to and highlighting the sentence. An early version had models copy the long URLs themselves. They sometimes dropped a word, which broke the highlight. Ids made that impossible and cut run time by about 40%.
- **Citation check.** After the Writer, `check_citations()` verifies each link: was the page read by a tool, and does the fragment's text actually occur in it? The page shows "N/M citations verified" and marks any id no tool handed out, or any unmatched link.
- **The latest filings, chosen by code.** Each Researcher is handed the latest DEF 14A and 10-K URLs. The previous year's are offered only when the task is about a change or trend. Left to choose, the lite model sometimes read last year's proxy and missed the year's biggest deal.
- **Time budgets.** Research stops at 120 s, and the Writer has 120 s (main model, then lite). If both fail, the report is assembled from the calculator table and raw findings, so a grader never waits more than about 4.5 minutes or gets nothing.

**Show its work.** `POST /chat` keeps Project 1's shape. Every tool call from every agent is in
`tool_calls`, with an `agent` field (`"Clarifier"`, `"Lead"`, `"Researcher 3"`, …):

```json
{"response": "## Bottom line ...", "session_id": "…",
 "tool_calls": [{"agent": "Researcher 2", "name": "search_filing",
                 "args": {"url": "https://www.sec.gov/Archives/…def14a.htm", "query": "\"related person transactions\""},
                 "result": "469 paragraphs in the filing. Best matches: …"}]}
```

The page uses `GET /run` (Server-Sent Events) for the same run, to draw the research team live: a lane
per agent, with researchers appearing side by side as the Lead sends them. A chart places every
deal on a log dollar scale against its two lines. The **Agents' raw context** drawer shows the exact
message list each agent sent to the model.

## Data

| Source | What | How it's reached |
|---|---|---|
| [SEC EDGAR submissions API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | Each company's filing list (DEF 14A, 10-K) | `data.sec.gov/submissions/CIK##########.json`, live |
| SEC EDGAR archives | The filing documents (HTML), parsed into section-tagged paragraphs | `www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}`, live, cached in memory |
| [SEC XBRL company facts](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | Revenue and total assets per fiscal year: the denominators for the % tests | `data.sec.gov/api/xbrl/companyfacts/CIK##########.json`, live |
| SEC `company_tickers_exchange.json` + iShares IWB holdings | Ticker → CIK, exchange (decides NYSE vs Nasdaq test), Russell 1000 membership | built offline into `data/universe.csv` |
| SEC Item 404 (eCFR via Cornell LII) and ISS 2026 U.S. Proxy Voting Guidelines | The materiality lines, quoted verbatim | encoded in `standards.py` |

All SEC endpoints are free and keyless, but SEC requires a `User-Agent` naming you
(`SEC_USER_AGENT="Your Name you@example.com"`) and fewer than 10 requests a second. The client
throttles to about 6 a second.

**Why the model doesn't already know this:** proxies are filed every year and the agent reads the
latest at question time (Tesla's 2026 proxy was filed 2026-10-19). The specifics, like *which*
family member, *how much*, and *which year*, are buried in footnote-level prose that models only
remember vaguely or wrongly. The baseline answers below show this.

**Offline build step:** `uv run build_universe.py [data/IWB_holdings.csv]` writes `data/universe.csv`
and `data/universe_meta.json`. Download the IWB holdings CSV from the
[iShares IWB page](https://www.ishares.com/us/products/239707/ishares-russell-1000-etf)
("Detailed Holdings and Analytics" → Download). Without it, every listed SEC filer is in scope.

**What the data can't answer, and the agent says so:**
- Transactions of $120,000 or less: companies never have to disclose them.
- The revenue of private counterparties (SpaceX, xAI, a director's family firm). Any test that needs it comes back *can't determine*.
- Amounts given only as "in excess of $120,000" or "less than 1% of revenues". The agent uses the stated bound and says that's all it has.
- Whether the board *should* have found a director independent. The agent reports the tests, not a legal opinion.

## Sample queries

Each one is also a button on the page. Expected answers were checked by hand against the filing
text. The "no tools" column is `vertex_ai/gemini-3.5-flash` with no system prompt and no tools,
asked the same question (run 2026-11-10).

### 1. `Do any of Meta's directors have business relationships with Meta that could affect their independence?`

**Expected:** Director **Hock E. Tan** is CEO of **Broadcom**. Meta paid Broadcom **about $2.3 billion in
2025** for components and engineering services. The recipient is Broadcom (FY2025 revenue
$63,887,000,000), so the deal is **3.6%** of its revenue: **under** the Nasdaq/ISS line that applies to
Meta (greater of $200K or 5% = $3.19B), but it **would cross** the NYSE line (2% = $1.28B). The board
found Tan independent. Also disclosed: **John Hegeman**, an immediate family member of an executive
officer, was employed as Chief Revenue Officer, with about **$17.5M** in 2025 compensation (Item 404
disclosure; no ISS dollar test). Director **Robert Kimmitt** is senior international counsel at
**WilmerHale**, which does legal work for Meta. The filing gives no dollar figure, only *"less than 4%
of WilmerHale's total revenue"*, so ISS's $10,000 professional-services test can't be run from the filing.
**Verdict: Not material on public data.**
**Source:** Meta DEF 14A filed 2026-04-16, "Related Party Transactions" and "Director Independence"
(`https://www.sec.gov/Archives/edgar/data/1326801/000162828026025532/meta-20260416.htm`). Broadcom
revenue from XBRL company facts (`data.sec.gov/api/xbrl/companyfacts/CIK0001730168.json`, 10-K 0001730168-25-000121).

| No tools, no system prompt | Related Party Radar |
|---|---|
| Names Hock Tan and Broadcom, but gives no figure: *"Meta's multi-million or even multi-billion dollar purchases do not cross this 5% threshold."* It never checks the number. It adds Marc Andreessen and a16z portfolio companies (not in the filing's related-party section) and misses John Hegeman entirely. | **Not material on public data.** The bottom line leads with *"the $2,300,000,000 Broadcom purchase would cross the NYSE independence threshold"*. The table shows Broadcom at 3.60% of Broadcom's revenue (under Meta's Nasdaq line of $3,194,350,000), Hegeman at $17,500,000 (Item 404, no dollar test), Kimmitt/WilmerHale as *"Not disclosed (less than 4% of WilmerHale's total revenue)"*, and Zuckerberg's $2.2M charter arrangement as *needs private data*. 36/36 citations verified, ~80 s. |

### 2. `Is any Apple director or executive involved in a related-party transaction, and does it matter?`

**Expected:** Yes, one. A **family member of Apple's former Chief Operating Officer** is employed by Apple
and received **total compensation in excess of $120,000** from the start of fiscal 2025 through the
proxy date. It is disclosable under Item 404. It isn't a dollar-tested independence issue, because
it's an employee's relative, not a payment to a director's firm. Apple also says no director had a
direct or indirect material interest in its commercial or charitable relationships with directors'
other organizations. **Verdict: Not material.**
**Source:** Apple DEF 14A filed 2026-01-08, "Related Party Policy and Transactions"
(`https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm`).

| No tools, no system prompt | Related Party Radar |
|---|---|
| **Wrong:** *"no Apple director or executive officer is currently involved in a material related-party transaction that requires disclosure."* Then it discusses Bob Iger leaving the board in 2019. | **Not material.** Finds the former COO's family member: "More than $120,000", Item 404 disclosure required, no ISS dollar test. Reports the board's "no material interest" statement on directors' other organizations. 26/26 citations verified, ~70 s. |

### 3. `Does Tesla have material related-party transactions with Elon Musk's other companies?`

**Expected:** Yes, many, all disclosable under Item 404. From the 2026 proxy: Tesla recognized about
**$143.3M** of revenue from **SpaceX** in 2025 (mostly vehicle sales) and about **$430.1M** from **xAI**
(mostly Megapack). Where **Tesla is the recipient**, the denominator is Tesla's 2025 revenue of
$94,827,000,000: 0.15% and 0.45%, far **under** the Nasdaq 5% line. SpaceX listed in June 2026 (SPCX)
and has no 10-K yet, but its nine-month 2026 revenue ($27,083,000,000) is a floor on its annual revenue.
That proves Tesla's **$11.4M payment to SpaceX** is under the line, while the **$2B** xAI/SpaceX share
investment (January 2026) stays open until SpaceX's first 10-K. Tesla's payments to X (about $3.3M of
advertising), xAI, The Boring Company and Musk's security firm go to **private** companies, so those
tests need private data. **Verdict: Not material on public data.** Also: JB Straubel's Redwood Materials, and a son-in-law of director Jack
Hartung employed at about $150,000.
**Source:** Tesla DEF 14A filed 2026-10-19, "Related Person Transactions"
(`https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm`), and
Tesla 10-K for FY2025, related party note (`…/000162828026003952/tsla-20251231.htm`).

| No tools, no system prompt | Related Party Radar |
|---|---|
| Describes the relationships in general and gives stale numbers: *"In 2023, Tesla reported that it sold about $5.9 million in parts and services to SpaceX."* Nothing for 2025, no xAI Megapack revenue, no $2B xAI investment, and no test against any line. | **Not material on public data.** 10 transactions. SpaceX and xAI revenue to Tesla: ✓ not material (0.15% and 0.45%). SpaceX $11.4M expenses: ✓ not material, using SpaceX's year-to-date revenue as a floor. $2B investment and payments to X, xAI, Boring Co. and the security firm: *needs private data*, explained under "Limits of public data" as a disclosure limit. 32/32 citations verified, ~2.5 min. |

**A vague one, to see clarification:** `Which companies have shady insider deals?` gets *"Which
company would you like us to investigate … for example Tesla (TSLA), Meta (META), or Oracle (ORCL)?"*.
Answering `Tesla` in the same session runs the full research.

## Run it

```bash
cp .env.example .env            # set SEC_USER_AGENT="Your Name you@example.com"
gcloud auth application-default login
uv run build_universe.py        # optional: rebuild data/universe.csv
uv run app.py                   # http://localhost:8000  (PORT=8010 uv run app.py for another port)
uv run standards.py             # calculator self-check: prints ok
uv run edgar.py AAPL            # data smoke test
```

```bash
curl -s -X POST localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message": "Does Tesla have material related-party transactions?"}' | jq '.response, (.tool_calls | map(.agent) | unique)'
```

## Deploy (Cloud Run, continuous from GitHub)

The `Dockerfile` installs from `uv.lock` and ships `data/`. In Cloud Run → *Create service* →
*Continuously deploy from a repository* → this repo, Dockerfile build. Then set:
- env var `SEC_USER_AGENT`
- request timeout **600 s** (a run takes 2–3 minutes; the agent caps itself at about 4.5)
- memory 1 GiB, min instances 0, max 2
- a service account with **Vertex AI User**

Local container test (on Apple Silicon, build for Cloud Run's platform: the arm64 `cryptography`
wheel crashes in Docker Desktop's VM):
`docker build --platform linux/amd64 -t rpr . && docker run --platform linux/amd64 -p 8080:8080 -e SEC_USER_AGENT="Name you@example.com" rpr`

## Files

- `app.py`: the four agents, their tools, the run (clarify → research → write → check citations), `/chat`, `/run` (SSE), `/clear`.
- `edgar.py`: the SEC client: company lookup, filing lists, HTML → section-tagged paragraphs, BM25 search, text-fragment cite links, XBRL financials.
- `standards.py`: the materiality lines with verbatim quotes, and the `assess()` calculator.
- `build_universe.py`: the offline build of `data/universe.csv`.
- `index.html`: the page. `context_panel.py` and `context-panel.js`: the raw-context drawer (from the course's deep-research reference).
