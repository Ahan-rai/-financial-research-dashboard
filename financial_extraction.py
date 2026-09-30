
import re


def extract_text(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def extract_number(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    try:
        return float(match.group(1).replace(",", ""))
    except (ValueError, AttributeError):
        return None


def clean_name(name):
    name = str(name).replace("", " ").strip()
    name = re.sub(r"\s+", " ", name)

    # Remove a trailing holding weight accidentally included
    # in the company name.
    name = re.sub(
        r"\s+\d+(?:\.\d+)?$",
        "",
        name
    )

    return name.strip()


def is_number(value):
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", value.strip()))


def extract_financial_data(text, filename=""):

    data = {
        "source_file": filename,
        "fund_name": None,
        "report_date": None,
        "aaum_crores": None,
        "aum_crores": None,
        "fund_manager": None,
        "benchmark": None,
        "standard_deviation": None,
        "beta": None,
        "sharpe_ratio": None,
        "equity_turnover": None,
        "total_turnover": None,
        "asset_allocation": {},
        "industry_allocation": {},
        "holdings": []
    }

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    data["fund_name"] = extract_text(
        r"(SBI\s+SMALL\s+CAP\s+FUND)",
        text
    )

    data["report_date"] = extract_text(
        r"Report\s+As\s+On\s*:\s*(\d{2}/\d{2}/\d{4})",
        text
    )

    # Newer June/July layout: date appears in the RBI exchange-rate sentence.
    if not data["report_date"]:
        date_match = re.search(
            r"as\s+on\s+"
            r"(January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+(\d{1,2}),\s+(\d{4})",
            text,
            re.IGNORECASE
        )

        if date_match:
            month = date_match.group(1)
            day = int(date_match.group(2))
            year = int(date_match.group(3))

            month_number = {
                "january": 1,
                "february": 2,
                "march": 3,
                "april": 4,
                "may": 5,
                "june": 6,
                "july": 7,
                "august": 8,
                "september": 9,
                "october": 10,
                "november": 11,
                "december": 12,
            }[month.lower()]

            data["report_date"] = f"{day:02d}/{month_number:02d}/{year}"

    data["aaum_crores"] = extract_number(
        r"AAUM\s+for\s+the\s+Month.*?₹?\s*([\d,]+\.\d+)\s*Crores",
        text
    )

    # Newer layout: "Monthly Avg. AUM" followed by the INR-crore value.
    if data["aaum_crores"] is None:
        match = re.search(
            r"Monthly\s+Avg\.\s+AUM\s+(?:`\s*)?([\d,]+\.\d+)",
            text,
            re.IGNORECASE
        )
        if match:
            data["aaum_crores"] = float(match.group(1).replace(",", ""))

    data["aum_crores"] = extract_number(
        r"AUM\s+as\s+on.*?₹?\s*([\d,]+\.\d+)\s*Crores",
        text
    )

    # Newer layout: "Month end AUM" followed by the INR-crore value.
    if data["aum_crores"] is None:
        match = re.search(
            r"Month\s+end\s+AUM\s+(?:`\s*)?([\d,]+\.\d+)",
            text,
            re.IGNORECASE
        )
        if match:
            data["aum_crores"] = float(match.group(1).replace(",", ""))

    data["fund_manager"] = extract_text(
        r"Fund\s+Manager:\s*(?:Mr\.\s*)?([A-Za-z.\s]+?)(?:\n|Managing\s+Since)",
        text
    )

    data["benchmark"] = extract_text(
        r"First\s+Tier\s+Benchmark:\s*(.*?)(?:\n|Exit\s+Load)",
        text
    )

    data["standard_deviation"] = extract_number(
        r"Standard\s+Deviation\s*:\s*([\d.]+)%",
        text
    )

    data["beta"] = extract_number(
        r"Beta\s*:\s*([\d.]+)",
        text
    )

    # Sharpe Ratio
    # Supports both:
    #   Sharpe Ratio: 0.54
    # and the June/July layout:
    #   Sharpe Ratio
    #   0.50
    data["sharpe_ratio"] = extract_number(
        r"Sharpe\s+Ratio\s*(?::\s*)?([+-]?\d+(?:\.\d+)?)",
        text
    )

    data["equity_turnover"] = extract_number(
        r"Equity\s+Turnover\s*:\s*([\d.]+)",
        text
    )

    data["total_turnover"] = extract_number(
        r"Total\s+Turnover\s*:\s*([\d.]+)",
        text
    )

    # =====================================================
    # INDUSTRY ALLOCATION
    # =====================================================

    industry_names = [
        "Financial Services",
        "Automobile And Auto Components",
        "Capital Goods",
        "Chemicals",
        "Consumer Durables",
        "Consumer Services",
        "Fast Moving Consumer Goods",
        "Construction",
        "Information Technology",
        "Healthcare",
        "Sovereign",
        "Textiles",
        "Services",
        "Realty",
        "Media, Entertainment & Publication",
        "Derivatives",
        "Cash, Cash Equivalents And Others"
    ]

    for industry in industry_names:

        match = re.search(
            re.escape(industry) + r"\s+([\d.]+)",
            text,
            re.IGNORECASE
        )

        if match:
            data["industry_allocation"][industry] = float(
                match.group(1)
            )

    # =====================================================
    # FIND EQUITY SECTION
    # =====================================================

    equity_start = None

    for index, line in enumerate(lines):

        if line.upper() == "EQUITY SHARES":
            equity_start = index + 1
            break

    if equity_start is None:
        return data

    # =====================================================
    # LAYOUT DETECTION
    # =====================================================

    new_layout = any(
        line.upper() == "COMPANY/ ISSUER"
        for line in lines[equity_start:]
    )

    # =====================================================
    # NEW LAYOUT — JUNE / JULY
    # =====================================================

    if new_layout:

        current_sector = None
        name_buffer = []

        stop_words = {
            "DEBT",
            "DEBT",
            "TREASURY BILLS",
            "CASH, CASH EQUIVALENTS AND OTHERS",
            "GRAND TOTAL",
            "TOTAL NET ASSETS"
        }

        ignored_headers = {
            "COMPANY/ ISSUER",
            "RATING",
            "NET% TO AUM",
            "NET % TO AUM"
        }

        for line in lines[equity_start:]:

            upper = line.upper()

            if upper in stop_words:
                break

            if upper in ignored_headers:
                continue

            # Sector heading
            if upper in {x.upper() for x in industry_names}:
                current_sector = line.title()
                name_buffer = []
                continue

            # Weight line
            if is_number(line):

                if name_buffer:

                    company_name = clean_name(
                        " ".join(name_buffer)
                    )

                    if company_name.upper() not in {
                        "TOTAL",
                        "GRAND TOTAL"
                    }:

                        data["holdings"].append({
                            "name": company_name,
                            "weight_percent": float(line),
                            "sector": current_sector
                        })

                name_buffer = []
                continue

            # Otherwise this is part of company name
            name_buffer.append(line)

    # =====================================================
    # =====================================================
    # OLD LAYOUT — FEB / MAR / APR / MAY
    # =====================================================

    else:

        stop_words = {
            "DEBT",
            "TREASURY BILLS",
            "CASH, CASH EQUIVALENTS AND OTHERS",
            "GRAND TOTAL",
            "TOTAL NET ASSETS"
        }

        ignored_headers = {
            "COMPANY/ ISSUER",
            "RATING",
            "NET% TO AUM",
            "NET % TO AUM",
            "EQUITY SHARES"
        }

        i = equity_start

        while i < len(lines):

            line = lines[i]
            upper = line.upper()

            # Stop at end of equity holdings
            if upper in stop_words:
                break

            # Stop before derivatives / T-Bills
            if re.match(r"^NIFTY\s+INDEX\b", upper):
                break

            if re.match(r"^\d+\s*DAY\s*T[- ]?BILL\b", upper):
                break

            # Ignore table headers
            if upper in ignored_headers:
                i += 1
                continue

            # Numeric-only lines cannot start a company
            if is_number(line):
                i += 1
                continue

            # -------------------------------------------------
            # CASE 1:
            # Company name + weight are on the SAME line
            # -------------------------------------------------

            same_line_match = re.match(
                r"^(.*?)\s+(\d+(?:\.\d+)?)$",
                line
            )

            if same_line_match:

                company_name = clean_name(
                    same_line_match.group(1)
                )

                weight_value = float(
                    same_line_match.group(2)
                )

                if company_name.upper() not in {
                    "TOTAL",
                    "GRAND TOTAL"
                }:

                    data["holdings"].append({
                        "name": company_name,
                        "weight_percent": weight_value,
                        "sector": None
                    })

                i += 1

                # Skip duplicate weight if it appears
                # immediately after the same-line row.
                if (
                    i < len(lines)
                    and is_number(lines[i])
                ):
                    i += 1

                continue

            # -------------------------------------------------
            # CASE 2:
            # Company name and weight are on separate lines
            # -------------------------------------------------

            name_buffer = [line]
            j = i + 1

            while j < len(lines):

                candidate = lines[j]
                candidate_upper = candidate.upper()

                if candidate_upper in stop_words:
                    break

                if re.match(
                    r"^NIFTY\s+INDEX\b",
                    candidate_upper
                ):
                    break

                if re.match(
                    r"^\d+\s*DAY\s*T[- ]?BILL\b",
                    candidate_upper
                ):
                    break

                if candidate_upper in ignored_headers:
                    j += 1
                    continue

                # A standalone number means holding weight
                if is_number(candidate):
                    break

                # Also handle company + weight on a continuation line
                same_line_match = re.match(
                    r"^(.*?)\s+(\d+(?:\.\d+)?)$",
                    candidate
                )

                if same_line_match:

                    name_buffer.append(
                        same_line_match.group(1).strip()
                    )

                    weight_value = float(
                        same_line_match.group(2)
                    )

                    company_name = clean_name(
                        " ".join(name_buffer)
                    )

                    if company_name.upper() not in {
                        "TOTAL",
                        "GRAND TOTAL"
                    }:

                        data["holdings"].append({
                            "name": company_name,
                            "weight_percent": weight_value,
                            "sector": None
                        })

                    j += 1

                    if (
                        j < len(lines)
                        and is_number(lines[j])
                    ):
                        j += 1

                    i = j
                    break

                name_buffer.append(candidate)
                j += 1

            else:
                j = len(lines)

            # If a standalone number follows the company name,
            # use it as the holding weight.
            if (
                j < len(lines)
                and is_number(lines[j])
            ):

                company_name = clean_name(
                    " ".join(name_buffer)
                )

                if company_name.upper() not in {
                    "TOTAL",
                    "GRAND TOTAL"
                }:

                    data["holdings"].append({
                        "name": company_name,
                        "weight_percent": float(lines[j]),
                        "sector": None
                    })

                # Skip weight
                i = j + 1

                # Skip duplicate weight if present
                if (
                    i < len(lines)
                    and is_number(lines[i])
                ):
                    i += 1

                continue

            # Move forward if nothing was extracted
            if i < j:
                i = j
            else:
                i += 1

    # Final holding count
    data["holding_count"] = len(data.get("holdings", []))

    return data


def is_derivative_or_tbill_section(name):
    if not name:
        return False

    text = re.sub(r"\s+", " ", str(name).strip()).upper()

    if re.match(r"^NIFTY\s+INDEX\b", text):
        return True

    if re.match(r"^\d+\s*DAY\s*T[- ]?BILL\b", text):
        return True

    return False





# ============================================================
# JUNE / JULY 2026 FACTSHEET EXTRACTION
# ============================================================

_original_extract_financial_data = extract_financial_data


def extract_financial_data(text, filename=''):

    data = _original_extract_financial_data(
        text,
        filename
    )

    import re

    # --------------------------------------------------------
    # Quantitative Indicators
    # --------------------------------------------------------

    match = re.search(
        r"Standard\s+Deviation\s*\(%\)\s*\n?\s*([0-9.]+)\s*%",
        text,
        re.IGNORECASE
    )

    if match:
        data["standard_deviation"] = float(match.group(1))


    match = re.search(
        r"Beta\s*\n?\s*([0-9.]+)",
        text,
        re.IGNORECASE
    )

    if match:
        data["beta"] = float(match.group(1))


    match = re.search(
        r"Sharpe\s+Ratio\s*\n?\s*([0-9.-]+)",
        text,
        re.IGNORECASE
    )

    if match:
        data["sharpe_ratio"] = float(match.group(1))


    match = re.search(
        r"Portfolio\s+Turnover\s*\(1\s*Year\)\s*Equity\s*\n?\s*([0-9.]+)",
        text,
        re.IGNORECASE
    )

    if match:
        data["equity_turnover"] = float(match.group(1))


    match = re.search(
        r"Portfolio\s+Turnover\s+Total\s*\n?\s*([0-9.]+)",
        text,
        re.IGNORECASE
    )

    if match:
        data["total_turnover"] = float(match.group(1))


    # --------------------------------------------------------
    # Fund Manager
    # --------------------------------------------------------

    match = re.search(
        r"Fund\s+Manager\s+"
        r"Total\s+Experience\s+"
        r"Managing\s+Since\s+"
        r"Mr\.\s*([A-Za-z.\s]+?)\s+"
        r"\d+\s+years",
        text,
        re.IGNORECASE
    )

    if match:
        data["fund_manager"] = (
            "Mr. " + match.group(1).strip()
        )


    # --------------------------------------------------------
    # Benchmark
    # --------------------------------------------------------

    match = re.search(
        r"Benchmark\s+"
        r"(BSE\s+250\s+Small\s+Cap\s+Index\s+TRI)",
        text,
        re.IGNORECASE
    )

    if match:
        data["benchmark"] = (
            match.group(1)
            .replace("\n", " ")
            .strip()
        )


    # --------------------------------------------------------
    # Industry / Sector headings
    # --------------------------------------------------------

    sector_names = [
        "FINANCIAL SERVICES",
        "AUTOMOBILE AND AUTO COMPONENTS",
        "CAPITAL GOODS",
        "CHEMICALS",
        "CONSUMER DURABLES",
        "CONSUMER SERVICES",
        "FAST MOVING CONSUMER GOODS",
        "CONSTRUCTION",
        "HEALTHCARE",
        "POWER",
        "TEXTILES",
        "INFORMATION TECHNOLOGY",
        "SERVICES",
        "REALTY",
        "MEDIA, ENTERTAINMENT & PUBLICATION"
    ]

    # Only inspect the portfolio section.
    portfolio_start = text.find("EQUITY SHARES")
    portfolio_end = text.find("TOTAL", portfolio_start)

    if portfolio_start != -1 and portfolio_end != -1:

        portfolio_text = text[
            portfolio_start:portfolio_end
        ].upper()

        found = []

        for sector in sector_names:

            if sector in portfolio_text:
                found.append(sector)

        data["industry_count"] = len(found)


    # --------------------------------------------------------
    # Clean holding names contaminated by PDF table header
    # --------------------------------------------------------

    for holding in data.get("holdings", []):

        name = holding.get("name", "")

        if name:

            name = name.replace(
                "Company/ Issuer Rating Net% To AUM",
                ""
            )

            name = name.replace(
                "Company/ Issuer Rating Net% To AUM ",
                ""
            )

            name = name.replace(
                "Net% To AUM",
                ""
            )

            holding["name"] = name.strip()


    # --------------------------------------------------------
    # Clean floating-point display values
    # --------------------------------------------------------

    for holding in data.get("holdings", []):

        if isinstance(holding.get("weight"), float):
            holding["weight"] = round(
                holding["weight"],
                4
            )


    return data
