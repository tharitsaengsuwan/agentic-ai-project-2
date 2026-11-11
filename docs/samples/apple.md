# Apple: no tools vs. Paper Trail

**Question:** `Is any Apple director or executive involved in a related-party transaction, and does it matter?`

Both answers were produced on 2026-11-10 by the same model, `vertex_ai/gemini-3.5-flash`.

- **No tools:** a single call with no system prompt and no tools.
- **Paper Trail:** `POST /chat` on the current code. It took 50s, with 30 tool calls from Clarifier, Lead, Researcher 1, Researcher 2, Researcher 3, Researcher 4, Researcher 5. Every source link opens the SEC filing at the quoted sentence.

---

## No tools, no system prompt

Based on Apple’s recent regulatory filings, **no Apple director or executive officer is currently involved in a material related-party transaction** that requires disclosure under U.S. securities laws. 

According to Apple’s annual Proxy Statement (Form DEF 14A) filed with the SEC, Apple has a strict policy regarding these transactions, and none met the threshold for disclosure in recent fiscal years.

Here is a breakdown of what this means, the details of Apple's policies, and why this matters to investors.

---

### Part 1: Apple’s Position on Related-Party Transactions

A **Related-Party Transaction (RPT)** is a business deal or arrangement between a company and its directors, executives, major shareholders, or their immediate family members. 

Under SEC rules, public companies must disclose any transaction since the beginning of the last fiscal year in which the company was a participant, the amount involved exceeds **$120,000**, and a "related person" had a direct or indirect material interest.

#### Apple’s Approval Process:
Apple has a formal, written policy for the review and approval of RPTs:
1. **Audit Committee Oversight:** Any transaction involving a related party must be reviewed and approved by Apple’s Audit Committee (which consists entirely of independent directors).
2. **Standard of Review:** The committee will only approve the transaction if it determines that it is in the best interests of Apple and its shareholders, and is conducted on an "arm's-length" basis (meaning the terms are no more favorable than those available to unrelated third parties).

#### Historical Context & Overlapping Interests:
While Apple does not have direct, personal RPTs (such as Tim Cook renting a building he owns to Apple), it does occasionally navigate potential conflicts due to **interlocking directorates** (where Apple directors serve as executives at other companies Apple does business with). 

* **The Bob Iger Case:** The most notable historical conflict involved Disney CEO Bob Iger, who served on Apple’s board. As Apple launched Apple TV+ and Disney launched Disney+, the two companies became direct competitors. While not a corrupt RPT, it created a structural conflict of interest. To maintain clean governance, Iger resigned from Apple's board in 2019.

---

### Part 2: Does It Matter?

**Yes, it matters significantly.** The absence of related-party transactions at Apple is a indicator of strong corporate governance. 

Here is why the presence or absence of RPTs matters to investors:

#### 1. Mitigation of "Self-Dealing" and Conflicts of Interest
When executives or directors do business with their own companies, there is an inherent conflict of interest. They may be tempted to prioritize their personal financial gain over the interests of shareholders. By avoiding these transactions, Apple ensures that its capital is spent solely on business operations that drive shareholder value, rather than enrichment of insiders.

#### 2. Investor Trust and Valuation Premium
Large institutional investors (like Vanguard, BlackRock, and Berkshire Hathaway) highly value clean corporate governance. Companies with history of heavy RPTs often trade at a discount because investors fear "tunneling" (where insiders slowly siphon off cash). Apple’s squeaky-clean record on this front supports its premium market valuation.

#### 3. Red Flags in Contrast
To understand why this matters, look at companies where RPTs *did* matter:
* **WeWork:** Prior to its failed 2019 IPO, it was revealed that co-founder Adam Neumann owned buildings that he leased back to WeWork, and even charged the company $5.9 million for the trademark to the word "We." This massive RPT contributed to the collapse of the IPO.
* **Enron:** The infamous energy giant used complex, off-the-books related-party transactions with partnerships run by its CFO to hide billions in debt, ultimately leading to bankruptcy.

### Summary
For a company of Apple’s massive scale, the fact that its directors and executives do not engage in related-party transactions is a sign of **institutional maturity and excellent governance.** It assures shareholders that Apple's leadership is focused entirely on the company's success, rather than personal side-deals.

---

## Paper Trail (`POST /chat`)

## Bottom line · Not material
Apple has an employment relationship with a family member of a former executive officer, and maintaining routine commercial and charitable relationships with organizations where its directors or executive officers serve [AAPL DEF 14A 2026 ¶112](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=Several%20of%20Apple%E2%80%99s%20Board%20members%20and%20executive)[AAPL DEF 14A 2026 ¶113](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=A%20family%20member%20of%20our%20former%20Chief). The employment transaction crosses the SEC Item 404 disclosure threshold, but it does not cross any ISS independence lines [AAPL DEF 14A 2026 ¶113](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=A%20family%20member%20of%20our%20former%20Chief). There is one transaction that has no dollar-based test under ISS guidelines [AAPL DEF 14A 2026 ¶113](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=A%20family%20member%20of%20our%20former%20Chief).

## Transactions found

| Related person | Transaction | Amount | SEC 404 disclosure | Independence test | Source |
|---|---|---:|---|---|---|
| family member of former Chief Operating Officer | family member employment | More than $120,000 | Required | – Former insider, not tested | [AAPL DEF 14A 2026 ¶113](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=A%20family%20member%20of%20our%20former%20Chief) |

## How each one was judged
Apple employed a family member of its former Chief Operating Officer, who received total compensation in excess of $120,000 [AAPL DEF 14A 2026 ¶113](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=A%20family%20member%20of%20our%20former%20Chief). Because the compensation exceeds $120,000, the transaction crosses the SEC Item 404 disclosure threshold [AAPL DEF 14A 2026 ¶113](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=A%20family%20member%20of%20our%20former%20Chief). Under ISS guidelines, this transaction has no dollar-based test because the related person is no longer an active insider [AAPL DEF 14A 2026 ¶113](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=A%20family%20member%20of%20our%20former%20Chief). ISS guidelines evaluate whether a director currently provides services or has an active material relationship, so this past transaction is disclosed but not tested for independence [AAPL DEF 14A 2026 ¶113](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=A%20family%20member%20of%20our%20former%20Chief).

## Limits of public data
These are limits of what companies must disclose, not gaps in the research.
* Private counterparties' revenue: ISS material transactional tests require dividing payments by the recipient's gross revenues to check if they exceed 2% or 5% thresholds, but because Apple's private commercial and charitable counterparties do not publish their revenues, only the board and the counterparties can run these tests [AAPL DEF 14A 2026 ¶112](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=Several%20of%20Apple%E2%80%99s%20Board%20members%20and%20executive).
* Vague amount disclosures: Apple reported the compensation of the former Chief Operating Officer's family member only as "in excess of $120,000" rather than disclosing the exact dollar amount [AAPL DEF 14A 2026 ¶113](https://www.sec.gov/Archives/edgar/data/320193/000130817926000008/aapl014016-def14a.htm#:~:text=A%20family%20member%20of%20our%20former%20Chief).
* Deals of $120,000 or less: Related-party transactions that do not exceed $120,000 are not required to be disclosed under SEC Item 404(a), keeping any such smaller arrangements hidden from public filings.

## Standards applied
- [SEC Item 404(a)](https://www.law.cornell.edu/cfr/text/17/229.404)
- [ISS 2026 U.S. guidelines](https://www.iss-stoxx.com/file/policy/current/americas/us-voting-guidelines.pdf)
