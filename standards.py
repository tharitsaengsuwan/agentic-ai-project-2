"""Where to draw the line: the materiality standards the agent applies, and a calculator for them.

The model never does this arithmetic. It extracts an amount and a relationship from a filing,
and assess() says, for each standard, whether the line is crossed, not crossed, or can't be
decided from the data (usually because the other party's revenue isn't public).

Sources, checked 2026-11-10:
- SEC Item 404: 17 CFR 229.404, read from Cornell LII's copy of the eCFR.
- ISS: United States Proxy Voting Guidelines, Benchmark Policy, effective for meetings on or after
  February 1, 2026 (published December 9, 2025), "ISS Classification of Directors - U.S."
  ISS footnote 8 restates the NYSE and Nasdaq payment tests; the exchanges' own rulebooks
  (NYSE 303A.02(b)(v), Nasdaq 5605(a)(2)(D)) blocked automated reading, so we cite ISS for them.
"""

SEC_404_URL = "https://www.law.cornell.edu/cfr/text/17/229.404"
ISS_URL = "https://www.iss-stoxx.com/file/policy/current/americas/us-voting-guidelines.pdf"

STANDARDS = {
    "sec_item_404a": {
        "name": "SEC Regulation S-K Item 404(a): related person transactions",
        "what_it_decides": "Whether a transaction must be disclosed in the proxy / 10-K.",
        "line": "Amount involved exceeds $120,000 and a related person has a direct or indirect material interest. "
        "Smaller reporting companies: the lesser of $120,000 or 1% of average year-end total assets for the last two years.",
        "quote": "Describe any transaction, since the beginning of the registrant's last fiscal year, or any currently "
        "proposed transaction, in which the registrant was or is to be a participant and the amount involved exceeds "
        "$120,000, and in which any related person had or will have a direct or indirect material interest.",
        "related_person": "Directors, executive officers, director nominees, their immediate family members (child, stepchild, "
        "parent, stepparent, spouse, sibling, in-laws, anyone sharing the household other than a tenant or employee), and "
        ">5% security holders and their immediate family.",
        "exclusions": "Instruction 5.a: compensation already reported under Item 402 (the executive compensation "
        "tables) need not be disclosed as a related person transaction.",
        "url": SEC_404_URL,
    },
    "iss_professional_services": {
        "name": "ISS Classification of Directors 2.12: professional services",
        "what_it_decides": "Whether ISS classifies a director as non-independent.",
        "line": "Professional services (advisory: legal, consulting, investment banking, audit, insurance, marketing, etc.) "
        "in excess of $10,000 per year.",
        "quote": "Director who (or whose immediate family member) currently provides professional services in excess of "
        "$10,000 per year to: the company, an affiliate, or an individual officer of the company or an affiliate; or who is "
        "(or whose immediate family member is) a partner, employee, or controlling shareholder of an organization which "
        "provides the services.",
        "url": ISS_URL,
    },
    "iss_transactional": {
        "name": "ISS Classification of Directors 2.13 / 2.14 and footnote 8: material transactional relationship "
        "(restating the NYSE and Nasdaq payment tests)",
        "what_it_decides": "Whether ISS (and, by the same numbers, the exchange's bright-line test) treats a director as non-independent.",
        "line": "Annual payments to or from another entity exceeding the greater of $1,000,000 or 2% of the recipient's gross "
        "revenues (NYSE companies), or the greater of $200,000 or 5% of the recipient's gross revenues (Nasdaq companies, and "
        "companies on neither exchange). Includes grants to non-profits.",
        "quote": "A material transactional relationship, including grants to non-profit organizations, exists if the company "
        "makes annual payments to, or receives annual payments from, another entity, exceeding the greater of: $200,000 or 5 "
        "percent of the recipient's gross revenues, for a company that follows NASDAQ listing standards; or the greater of "
        "$1,000,000 or 2 percent of the recipient's gross revenues, for a company that follows NYSE listing standards. For a "
        "company that follows neither of the preceding standards, ISS will apply the NASDAQ-based materiality test. (The "
        "recipient is the party receiving the financial proceeds from the transaction).",
        "url": ISS_URL,
    },
    "iss_family_of_officer": {
        "name": "ISS Classification of Directors 2.10: family members",
        "what_it_decides": "Whether a director is non-independent because of family ties to management.",
        "line": "A director who is an immediate family member of a current or former officer (last five years) is non-independent. "
        "No dollar amount.",
        "quote": "Immediate family member of a current or former officer of the company or its affiliates within the last five years.",
        "url": ISS_URL,
    },
}

RELATIONSHIPS = ("transactional", "professional_services", "charitable_grant", "family_employment", "executive_compensation", "other")


def _pct(x: float) -> str:
    return f"{x:.2%}" if x >= 0.0001 else "less than 0.01%"


def _usd(x: float) -> str:
    return f"${x:,.0f}"


def assess(
    amount_usd: float | None,
    relationship: str,
    exchange: str,
    direction: str,
    recipient_revenue_usd: float | None = None,
    smaller_reporting_company: bool = False,
    recipient_label: str | None = None,
    revenue_is_floor: bool = False,
    avg_total_assets_usd: float | None = None,
) -> dict:
    """Apply every standard that fits this relationship. Each result is crossed / not_crossed / cannot_determine."""
    relationship = relationship if relationship in RELATIONSHIPS else "other"
    results = []

    if relationship == "executive_compensation":
        # An insider's own pay is not a related-party transaction: Item 404 Instruction 5.a.i
        results.append({"standard": "sec_item_404a", "threshold_usd": None, "status": "excluded",
                        "why": "This is the executive's own compensation, reported in the compensation tables under Item 402. "
                               "Item 404 Instruction 5.a.i says such compensation need not be disclosed as a related person transaction."})
        results.append({"standard": "iss_executive", "threshold_usd": None, "status": "not_applicable_to_amount",
                        "why": "Independence tests don't apply: ISS already classifies a current officer as an Executive Director "
                               "(category 1.1), and pay is judged under ISS's compensation policies, not its related-party tests."})
        return {"amount_usd": amount_usd, "relationship": relationship, "exchange": exchange, "direction": direction, "results": results}

    if amount_usd is None:
        # The filing describes the deal but gives no dollar figure: say what the line is, not a verdict
        results.append({"standard": "sec_item_404a", "threshold_usd": 120_000.0, "status": "cannot_determine",
                        "why": "The filing gives no dollar amount for this relationship."})
        if relationship == "professional_services":
            results.append({"standard": "iss_professional_services", "threshold_usd": 10_000.0, "status": "cannot_determine",
                            "why": "ISS's line for professional services is only $10,000 a year, but the filing does not say how much "
                                   "was paid, so the test needs the actual fees, which only the company and the firm know."})
        elif relationship in ("transactional", "charitable_grant"):
            results.append({"standard": "iss_transactional", "threshold_usd": None, "status": "cannot_determine",
                            "why": "The filing does not give the payments in dollars, so the test needs figures that are not public."})
        elif relationship == "family_employment":
            results.append({"standard": "iss_family_of_officer", "threshold_usd": None, "status": "not_applicable_to_amount",
                            "why": "Employing an insider's relative is a disclosure matter; no dollar test applies."})
        return {"amount_usd": None, "relationship": relationship, "exchange": exchange, "direction": direction, "results": results}

    # SEC Item 404(a): every kind of transaction
    line = 120_000.0
    if smaller_reporting_company and avg_total_assets_usd:
        line = min(line, 0.01 * avg_total_assets_usd)
    results.append(
        {
            "standard": "sec_item_404a",
            "threshold_usd": line,
            "status": "crossed" if amount_usd > line else "not_crossed",
            "why": f"{_usd(amount_usd)} {'>' if amount_usd > line else '<='} {_usd(line)} disclosure line "
            "(disclosure also requires the related person to have a material interest).",
        }
    )

    if relationship == "professional_services":
        results.append(
            {
                "standard": "iss_professional_services",
                "threshold_usd": 10_000.0,
                "status": "crossed" if amount_usd > 10_000 else "not_crossed",
                "why": f"{_usd(amount_usd)} {'>' if amount_usd > 10_000 else '<='} $10,000 per year.",
            }
        )

    if relationship in ("transactional", "charitable_grant"):
        nyse = exchange.upper() == "NYSE"
        floor, pct = (1_000_000.0, 0.02) if nyse else (200_000.0, 0.05)
        test = f"{'NYSE' if nyse else 'Nasdaq'} test: greater of {_usd(floor)} or {pct:.0%} of the recipient's revenue"
        recipient = recipient_label or ("the other entity" if direction == "company_pays" else "the company")
        if recipient_revenue_usd and revenue_is_floor:
            # Partial-year revenue is a floor on annual revenue, so the line is at least this high
            line = max(floor, pct * recipient_revenue_usd)
            if amount_usd <= line:
                status = "not_crossed"
                why = (f"{test}. {recipient} has no full fiscal year in SEC data yet, but its year-to-date revenue alone is "
                       f"{_usd(recipient_revenue_usd)}, so the line is at least {_usd(line)} and {_usd(amount_usd)} is under it.")
            else:
                status = "cannot_determine"
                why = (f"{test}. {recipient} has no full fiscal year in SEC data yet (year-to-date revenue {_usd(recipient_revenue_usd)}, "
                       f"line at least {_usd(line)}). {_usd(amount_usd)} is above that floor, so the answer needs its full-year revenue, "
                       f"which its first 10-K will disclose.")
        elif recipient_revenue_usd:
            line = max(floor, pct * recipient_revenue_usd)
            status = "crossed" if amount_usd > line else "not_crossed"
            why = (
                f"{test} = {_usd(line)} (recipient: {recipient}, revenue {_usd(recipient_revenue_usd)}). "
                f"{_usd(amount_usd)} is {_pct(amount_usd / recipient_revenue_usd)} of the recipient's revenue."
            )
            # The same deal under the other exchange's test: the lines differ, and sometimes the verdict does
            o_floor, o_pct, o_name = (200_000.0, 0.05, "Nasdaq") if nyse else (1_000_000.0, 0.02, "NYSE")
            o_line = max(o_floor, o_pct * recipient_revenue_usd)
            o_status = "crossed" if amount_usd > o_line else "not_crossed"
            if o_status != status:
                why += (
                    f" Under the {o_name} test (greater of {_usd(o_floor)} or {o_pct:.0%}) the line would be {_usd(o_line)}, "
                    f"and this deal would {'cross' if o_status == 'crossed' else 'not cross'} it."
                )
        elif amount_usd <= floor:
            line, status = floor, "not_crossed"
            why = f"{_usd(amount_usd)} <= the {_usd(floor)} floor, so it is under the line whatever the recipient's revenue. ({test})"
        else:
            line, status = floor, "cannot_determine"
            why = (
                f"{_usd(amount_usd)} is above the {_usd(floor)} floor, so the test turns on the annual revenue of {recipient} "
                f"(the recipient). It is not a listed SEC filer and does not publish its revenue, so the test needs "
                f"private information that the board has and outside investors don't. ({test})"
            )
        results.append({"standard": "iss_transactional", "threshold_usd": line, "status": status, "why": why})

    if relationship == "family_employment":
        results.append(
            {
                "standard": "iss_family_of_officer",
                "threshold_usd": None,
                "status": "not_applicable_to_amount",
                "why": "Employing an insider's relative is a disclosure matter under Item 404. It affects a director's ISS "
                "classification only if that director is the relative of an officer (no dollar test).",
            }
        )

    return {"amount_usd": amount_usd, "relationship": relationship, "exchange": exchange, "direction": direction, "results": results}


if __name__ == "__main__":
    # Self-check: uv run standards.py
    r = assess(150_000, "family_employment", "Nasdaq", "company_pays")
    assert r["results"][0]["status"] == "crossed"
    r = assess(900_000, "transactional", "NYSE", "company_pays")
    assert r["results"][1]["status"] == "not_crossed"  # under the $1M floor
    r = assess(5_000_000, "transactional", "NYSE", "company_pays")
    assert r["results"][1]["status"] == "cannot_determine"  # depends on the private recipient's revenue
    r = assess(5_000_000, "transactional", "NYSE", "company_pays", recipient_revenue_usd=100_000_000)
    assert r["results"][1]["status"] == "crossed"  # 5% > 2%
    r = assess(5_000_000, "transactional", "Nasdaq", "company_receives", recipient_revenue_usd=400_000_000_000)
    assert r["results"][1]["status"] == "not_crossed"
    r = assess(11_400_000, "transactional", "Nasdaq", "company_pays", 27_083_000_000, recipient_label="SpaceX", revenue_is_floor=True)
    assert r["results"][1]["status"] == "not_crossed"  # under 5% of even the year-to-date revenue
    r = assess(2_000_000_000, "transactional", "Nasdaq", "company_pays", 27_083_000_000, recipient_label="SpaceX", revenue_is_floor=True)
    assert r["results"][1]["status"] == "cannot_determine"  # above the floor's line: needs the full year
    r = assess(1_150_000, "executive_compensation", "Nasdaq", "company_pays")
    assert r["results"][0]["status"] == "excluded"  # own pay: Item 402, not Item 404
    r = assess(None, "professional_services", "Nasdaq", "company_pays")
    assert r["results"][1]["status"] == "cannot_determine"  # no amount disclosed: never a verdict
    r = assess(25_000, "professional_services", "NYSE", "company_pays")
    assert r["results"][1]["status"] == "crossed"
    print("ok")
