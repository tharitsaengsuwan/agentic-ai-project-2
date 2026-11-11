# Tesla: no tools vs. Paper Trail

**Question:** `Does Tesla have material related-party transactions with Elon Musk's other companies?`

Both answers were produced on 2026-11-10 by the same model, `vertex_ai/gemini-3.5-flash`.

- **No tools:** a single call with no system prompt and no tools.
- **Paper Trail:** `POST /chat` on the current code. It took 63s, with 33 tool calls from Clarifier, Lead, Researcher 1, Researcher 2, Researcher 3. Every source link opens the SEC filing at the quoted sentence.

---

## No tools, no system prompt

**Yes**, Tesla has multiple related-party transactions with Elon Musk’s other companies, including SpaceX, X (formerly Twitter), The Boring Company, and xAI. 

While these transactions are **legally material**—meaning they must be disclosed to the SEC under securities laws—they are generally **financially immaterial** relative to Tesla’s massive overall annual revenue (which was approximately $96.8 billion in 2023). However, they attract significant scrutiny from investors and corporate governance experts due to potential conflicts of interest.

Here is a breakdown of Tesla’s related-party transactions with Musk’s other ventures, based on Tesla's SEC filings (primarily its Form 10-K and annual Proxy Statements):

---

### 1. SpaceX (Space Exploration Technologies Corp.)
The relationship between Tesla and SpaceX is the most long-standing and active. The two companies share engineering expertise, materials, and equipment.
*   **Reciprocal Sales:** Tesla sells battery components, vehicle parts, and non-financial services (such as machining and engineering support) to SpaceX. In turn, SpaceX sells parts and services to Tesla.
*   **Starlink:** Tesla uses SpaceX’s Starlink satellite internet services at various Tesla facilities and Gigafactories.
*   **Corporate Travel:** Tesla and SpaceX share the costs of private aviation. Tesla pays SpaceX (or Musk's private jet LLC) for Tesla-related travel, and SpaceX reimburses Tesla when SpaceX uses Tesla assets.
*   **Financial Scale:** In 2023, Tesla reported that it sold about $5.9 million in parts and services to SpaceX and purchased about $4.9 million from SpaceX. 

### 2. X Corp. (formerly Twitter)
Since Elon Musk acquired Twitter in late 2022, Tesla has engaged in business transactions with the social media platform.
*   **Advertising and Marketing:** Historically, Tesla did not advertise. However, in late 2023 and 2024, Tesla began running paid advertisements on X.
*   **Shared Services:** Tesla employees have occasionally been brought in to assist at X (particularly during the transition in late 2022), and X has used certain Tesla resources. X also pays Tesla for security and facility sharing in certain locations.
*   **Financial Scale:** In 2023, Tesla’s transactions with X were relatively small (disclosed in the millions), but the relationship remains highly scrutinized, especially regarding the allocation of Musk’s time and the use of Tesla’s engineering talent at X.

### 3. The Boring Company (TBC)
The Boring Company, Musk’s tunnel-construction venture, has several commercial agreements with Tesla.
*   **The Las Vegas Loop:** TBC built the transport system under the Las Vegas Convention Center, which exclusively uses Tesla vehicles to transport passengers. Tesla sold vehicles and charging infrastructure to TBC for this project.
*   **Excavation and Construction:** Tesla has contracted with TBC for tunneling and utility work at Giga Texas.
*   **Financial Scale:** These contracts typically amount to a few million dollars annually. 

### 4. xAI (Artificial Intelligence)
Founded by Musk in 2023, xAI has become a major point of discussion regarding related-party transactions, talent sharing, and hardware allocation.
*   **GPU Allocation:** In early 2024, controversy arose when it was revealed that Musk redirected thousands of Nvidia H100 AI microchips—which had been reserved for Tesla—to xAI and X. Musk defended the move, stating Tesla did not yet have the infrastructure ready to house the chips, while xAI did.
*   **Talent Poaching/Sharing:** Several top AI and autopilot engineers have moved from Tesla to xAI. Musk has argued that if these engineers hadn't gone to xAI, they would have been hired by rival tech firms.
*   **Proposed Financial Investment:** In mid-2024, Musk publicly floated the idea of Tesla investing $5 billion into xAI. If this occurs, it would represent a highly material financial transaction.

---

### Why These Transactions are Controversial
While the dollar amounts of these transactions are usually small compared to Tesla's balance sheet, they raise several corporate governance concerns:

*   **Fiduciary Duty:** Critics and activist shareholders argue that Tesla’s Board of Directors (which contains several Musk close associates and his brother, Kimbal Musk) may not negotiate these deals at "arm's length," potentially benefiting Musk's private companies at the expense of Tesla’s public shareholders.
*   **Splitting Focus and Resources:** The transfer of key personnel (especially AI engineers) and hardware (like Nvidia GPUs) from Tesla to privately held companies like xAI has led to lawsuits and complaints that Musk is starving Tesla of resources to build his other ventures.
*   **Board Oversight:** Tesla’s Audit Committee is legally required to review and approve all related-party transactions to ensure they are fair to Tesla. However, critics argue the committee is too deferential to Musk.

---

## Paper Trail (`POST /chat`)

## Bottom line · Not material on public data
Tesla engaged in nine related-party transactions in 2025 and early 2026 involving entities affiliated with its CEO, Elon Musk [TSLA DEF 14A 2026 ¶361](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=Elon%20Musk%20is%20an%20executive%20officer%2C%20director)[TSLA 10-K 2026 ¶517](https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm#:~:text=Tesla%20periodically%20does%20business%20with%20certain%20entities). Under director independence standards, four of these transactions do not cross the material threshold [TSLA DEF 14A 2026 ¶364](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=Since%20April%202016%2C%20SpaceX%20has%20invoiced%20Tesla)[TSLA DEF 14A 2026 ¶363](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=SpaceX%20is%20party%20to%20certain%20commercial%2C%20licensing). The remaining five transactions require private counterparty revenue data to determine if they cross independence lines [TSLA DEF 14A 2026 ¶366](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=TBC%20is%20party%20to%20certain%20commercial%20agreements)[TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C).

## Transactions found

| Related person | Transaction | Amount | SEC 404 disclosure | Independence test | Source |
|---|---|---:|---|---|---|
| Elon Musk (CEO, director, and significant shareholder of SpaceX, xAI, X, and TBC) | Investment in xAI Holdings / SpaceX shares | $2,000,000,000 | Required | Needs private data | [TSLA DEF 14A 2026 ¶362](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20previously%20disclosed%2C%20on%20January%2016%2C%202026%2C) |
| Elon Musk, CEO | Elon Musk security services (expenses) | $4,800,000 | Required | Needs private data | [TSLA DEF 14A 2026 ¶366](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=TBC%20is%20party%20to%20certain%20commercial%20agreements) |
| Elon Musk, CEO | xAI commercial, consulting, and support agreements (expenses) | $4,000,000 | Required | Needs private data | [TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C) |
| Elon Musk, CEO | Advertising purchases on X | $3,300,000 | Required | Needs private data | [TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C) |
| Elon Musk, CEO | The Boring Company commercial agreements (expenses) | $900,000 | Required | Needs private data | [TSLA DEF 14A 2026 ¶366](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=TBC%20is%20party%20to%20certain%20commercial%20agreements) |
| Elon Musk, CEO | xAI commercial agreements (revenue) | $430,100,000 | Required | ✓ Not material | [TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C) |
| Elon Musk, CEO | SpaceX vehicle sales and commercial agreements (revenue) | $143,300,000 | Required | ✓ Not material | [TSLA DEF 14A 2026 ¶363](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=SpaceX%20is%20party%20to%20certain%20commercial%2C%20licensing) |
| Elon Musk, CEO | SpaceX commercial, licensing, and support agreements (expenses) | $11,400,000 | Required | ✓ Not material | [TSLA DEF 14A 2026 ¶363](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=SpaceX%20is%20party%20to%20certain%20commercial%2C%20licensing) |
| Elon Musk, CEO | SpaceX aircraft use (expenses) | $400,000 | Required | ✓ Not material | [TSLA DEF 14A 2026 ¶364](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=Since%20April%202016%2C%20SpaceX%20has%20invoiced%20Tesla) |

## How each one was judged
Tesla agreed to invest $2,000,000,000 to acquire Series E Preferred Stock of xAI, which crosses the SEC Item 404 disclosure threshold [TSLA DEF 14A 2026 ¶362](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20previously%20disclosed%2C%20on%20January%2016%2C%202026%2C)[TSLA 10-K 2026 ¶518](https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm#:~:text=In%20January%202026%2C%20the%20Company%20entered%20into). Under the Nasdaq independence test, the threshold is the greater of $200,000 or 5% of the recipient's revenue [TSLA DEF 14A 2026 ¶362](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20previously%20disclosed%2C%20on%20January%2016%2C%202026%2C). Because SpaceX has no full fiscal year in SEC data yet, its year-to-date revenue of $27,083,000,000 sets a floor of at least $1,354,150,000 [TSLA DEF 14A 2026 ¶361](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=Elon%20Musk%20is%20an%20executive%20officer%2C%20director)[TSLA DEF 14A 2026 ¶362](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20previously%20disclosed%2C%20on%20January%2016%2C%202026%2C). Since the $2,000,000,000 investment exceeds this floor, determining if it crosses the independence threshold requires SpaceX's full-year revenue, which is not yet public [TSLA DEF 14A 2026 ¶362](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20previously%20disclosed%2C%20on%20January%2016%2C%202026%2C).

Tesla incurred $11,400,000 in expenses under commercial, licensing, and support agreements with SpaceX, crossing the SEC disclosure threshold [TSLA DEF 14A 2026 ¶363](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=SpaceX%20is%20party%20to%20certain%20commercial%2C%20licensing). Under the Nasdaq independence test, the threshold is at least $1,354,150,000 based on SpaceX's year-to-date revenue of $27,083,000,000 [TSLA DEF 14A 2026 ¶363](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=SpaceX%20is%20party%20to%20certain%20commercial%2C%20licensing). Because the $11,400,000 expense is below this floor, it does not cross the independence line [TSLA DEF 14A 2026 ¶363](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=SpaceX%20is%20party%20to%20certain%20commercial%2C%20licensing).

Tesla recognized $143,300,000 in revenue from vehicle sales and commercial agreements with SpaceX, crossing the SEC disclosure threshold [TSLA DEF 14A 2026 ¶363](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=SpaceX%20is%20party%20to%20certain%20commercial%2C%20licensing). Under the Nasdaq independence test, the threshold for Tesla as the recipient is $4,741,350,000, which is 5% of Tesla's $94,827,000,000 revenue [TSLA DEF 14A 2026 ¶363](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=SpaceX%20is%20party%20to%20certain%20commercial%2C%20licensing). Because the $143,300,000 revenue represents 0.15% of Tesla's revenue, it does not cross the independence line [TSLA DEF 14A 2026 ¶363](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=SpaceX%20is%20party%20to%20certain%20commercial%2C%20licensing).

Tesla incurred $400,000 in expenses for the use of an aircraft owned and operated by SpaceX, crossing the SEC disclosure threshold [TSLA DEF 14A 2026 ¶364](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=Since%20April%202016%2C%20SpaceX%20has%20invoiced%20Tesla). Under the Nasdaq independence test, the threshold is at least $1,354,150,000 based on SpaceX's year-to-date revenue of $27,083,000,000 [TSLA DEF 14A 2026 ¶364](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=Since%20April%202016%2C%20SpaceX%20has%20invoiced%20Tesla). Because the $400,000 expense is below this floor, it does not cross the independence line [TSLA DEF 14A 2026 ¶364](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=Since%20April%202016%2C%20SpaceX%20has%20invoiced%20Tesla).

Tesla purchased advertising on X incurring $3,300,000 in expenses, which crosses the SEC disclosure threshold [TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C). Because X is not a listed SEC filer and does not publish its revenue, the Nasdaq independence test (the greater of $200,000 or 5% of the recipient's revenue) requires private counterparty revenue data [TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C).

Tesla incurred $4,000,000 in expenses under commercial, consulting, and support agreements with xAI, crossing the SEC disclosure threshold [TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C). Because xAI is not a listed SEC filer and does not publish its revenue, the Nasdaq independence test (the greater of $200,000 or 5% of the recipient's revenue) requires private counterparty revenue data [TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C).

Tesla recognized $430,100,000 in revenue from commercial agreements with xAI, crossing the SEC disclosure threshold [TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C). Under the Nasdaq independence test, the threshold for Tesla as the recipient is $4,741,350,000, which is 5% of Tesla's $94,827,000,000 revenue [TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C). Because the $430,100,000 revenue is 0.45% of Tesla's revenue, it does not cross the independence line [TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C).

Tesla incurred $900,000 in expenses under commercial agreements with The Boring Company, crossing the SEC disclosure threshold [TSLA DEF 14A 2026 ¶366](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=TBC%20is%20party%20to%20certain%20commercial%20agreements). Because The Boring Company is not a listed SEC filer and does not publish its revenue, the Nasdaq independence test (the greater of $200,000 or 5% of the recipient's revenue) requires private counterparty revenue data [TSLA DEF 14A 2026 ¶366](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=TBC%20is%20party%20to%20certain%20commercial%20agreements).

Tesla incurred $4,800,000 in expenses for security services concerning Elon Musk provided by a security company owned by him, crossing the SEC disclosure threshold [TSLA DEF 14A 2026 ¶366](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=TBC%20is%20party%20to%20certain%20commercial%20agreements). Because the security company is not a listed SEC filer and does not publish its revenue, the Nasdaq independence test (the greater of $200,000 or 5% of the recipient's revenue) requires private counterparty revenue data [TSLA DEF 14A 2026 ¶366](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=TBC%20is%20party%20to%20certain%20commercial%20agreements).

## Limits of public data
These are limits of what companies must disclose, not gaps in the research.
* **Private counterparties' revenue:** The Nasdaq independence test divides by the recipient's revenue to see if the transaction exceeds 5% of its annual gross revenue [TSLA DEF 14A 2026 ¶366](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=TBC%20is%20party%20to%20certain%20commercial%20agreements)[TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C). Because X Corp., xAI, The Boring Company, and Elon Musk's security company are private entities that do not publish their revenues, only the board and the counterparties can run this test [TSLA DEF 14A 2026 ¶366](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=TBC%20is%20party%20to%20certain%20commercial%20agreements)[TSLA DEF 14A 2026 ¶365](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20part%20of%20a%20multi%2Dplatform%20advertising%20campaign%2C).
* **Unpublished full-year revenue:** SpaceX has no full fiscal year in SEC data yet, meaning its final full-year revenue is not public and cannot be used to calculate a precise Nasdaq independence threshold [TSLA DEF 14A 2026 ¶362](https://www.sec.gov/Archives/edgar/data/1318605/000110465926116700/tm267596-1_def14a.htm#:~:text=As%20previously%20disclosed%2C%20on%20January%2016%2C%202026%2C).
* **Deals of $120,000 or less:** Under SEC rules, transactions of $120,000 or less do not require disclosure, which means smaller transactions between Tesla and these entities are omitted from the filings [TSLA 10-K 2026 ¶517](https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm#:~:text=Tesla%20periodically%20does%20business%20with%20certain%20entities).

## Standards applied
* [SEC Item 404(a)](https://www.law.cornell.edu/cfr/text/17/229.404)
* [ISS 2026 U.S. guidelines](https://www.iss-stoxx.com/file/policy/current/americas/us-voting-guidelines.pdf)
