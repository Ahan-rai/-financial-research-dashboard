import re
from datetime import datetime


def normalize_company_name(name):
    if not name:
        return None

    name = str(name).strip()

    # Remove PDF artifact/bullet characters
    name = name.replace("", "")

    # Normalize whitespace
    name = re.sub(r"\s+", " ", name).strip()

    # Normalize trailing punctuation differences
    name = re.sub(r"\s*\.\s*$", "", name).strip()

    known_names = {
        "PVR INOX LTD": "PVR Inox Ltd.",
        "PVR INOX LTD.": "PVR Inox Ltd.",
        "PVR INOX LIMITED": "PVR Inox Ltd.",
        "TTK PRESTIGE LTD": "TTK Prestige Ltd.",
        "TTK PRESTIGE LTD.": "TTK Prestige Ltd.",
        "GO FASHION (INDIA) LTD": "Go Fashion (India) Ltd.",
        "E.I.D-PARRY (INDIA) LTD": "E.I.D-Parry (India) Ltd.",
        "E.I.D-PARRY (INDIA) LTD.": "E.I.D-Parry (India) Ltd.",
    }

    return known_names.get(name.upper(), name)


def normalize_date(date_value):
    if not date_value:
        return None

    try:
        return datetime.strptime(
            str(date_value),
            "%d/%m/%Y"
        ).date().isoformat()

    except (ValueError, TypeError):
        return date_value


def normalize_number(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    try:
        cleaned = str(value).strip()
        cleaned = cleaned.replace(",", "")
        cleaned = cleaned.replace("%", "")
        return float(cleaned)

    except (ValueError, TypeError):
        return None


def normalize_holding(holding):
    normalized = {}

    normalized["name"] = normalize_company_name(
        holding.get("name")
    )

    normalized["weight_percent"] = normalize_number(
        holding.get("weight_percent")
    )

    sector = holding.get("sector")

    if sector:
        sector = re.sub(
            r"\s+",
            " ",
            str(sector).strip()
        )

    normalized["sector"] = sector

    return normalized


def normalize_financial_data(data):
    normalized = {}

    normalized["source_file"] = data.get("source_file")
    normalized["fund_name"] = data.get("fund_name")

    normalized["report_date"] = normalize_date(
        data.get("report_date")
    )

    normalized["fund_manager"] = data.get("fund_manager")
    normalized["benchmark"] = data.get("benchmark")

    normalized["aaum_crores"] = normalize_number(
        data.get("aaum_crores")
    )

    normalized["aum_crores"] = normalize_number(
        data.get("aum_crores")
    )

    normalized["standard_deviation"] = normalize_number(
        data.get("standard_deviation")
    )

    normalized["beta"] = normalize_number(
        data.get("beta")
    )

    normalized["sharpe_ratio"] = normalize_number(
        data.get("sharpe_ratio")
    )

    normalized["equity_turnover"] = normalize_number(
        data.get("equity_turnover")
    )

    normalized["total_turnover"] = normalize_number(
        data.get("total_turnover")
    )

    normalized["asset_allocation"] = {}

    for key, value in data.get(
        "asset_allocation",
        {}
    ).items():

        normalized["asset_allocation"][key] = (
            normalize_number(value)
        )

    normalized["industry_allocation"] = {}

    for key, value in data.get(
        "industry_allocation",
        {}
    ).items():

        normalized["industry_allocation"][key] = (
            normalize_number(value)
        )

    normalized_holdings = []

    for holding in data.get("holdings", []):

        normalized_holding = normalize_holding(
            holding
        )

        if normalized_holding["name"]:
            normalized_holdings.append(
                normalized_holding
            )

    normalized_holdings.sort(
        key=lambda x: (
            x["weight_percent"] is None,
            -(x["weight_percent"] or 0)
        )
    )

    normalized["holdings"] = normalized_holdings

    normalized["holding_count"] = len(
        normalized_holdings
    )

    normalized["industry_count"] = len(
        normalized["industry_allocation"]
    )

    return normalized
