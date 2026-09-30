import re


from datetime import datetime


def sort_by_date(documents):
    def date_key(document):
        date_text = document.get("report_date")

        if not date_text:
            return datetime.max

        try:
            return datetime.strptime(
                date_text,
                "%d/%m/%Y"
            )
        except ValueError:
            return datetime.max

    return sorted(
        documents,
        key=date_key
    )


def build_period_summary(documents):
    sorted_documents = sort_by_date(documents)

    summary = []

    for data in sorted_documents:
        summary.append({
            "report_date": data.get("report_date"),
            "aaum_crores": data.get("aaum_crores"),
            "aum_crores": data.get("aum_crores"),
            "standard_deviation": data.get("standard_deviation"),
            "beta": data.get("beta"),
            "sharpe_ratio": data.get("sharpe_ratio"),
            "equity_turnover": data.get("equity_turnover"),
            "total_turnover": data.get("total_turnover"),
            "holding_count": data.get("holding_count"),
            "industry_count": data.get("industry_count"),
        })

    return summary


def calculate_change(current, previous):
    if current is None or previous is None:
        return None

    return current - previous


def calculate_percent_change(current, previous):
    if current is None or previous in (None, 0):
        return None

    return ((current - previous) / previous) * 100


def build_period_changes(documents):
    sorted_documents = sort_by_date(documents)

    changes = []

    for index, current in enumerate(sorted_documents):

        if index == 0:
            continue

        previous = sorted_documents[index - 1]

        changes.append({
            "report_date": current.get("report_date"),
            "previous_date": previous.get("report_date"),

            "aaum_change": calculate_change(
                current.get("aaum_crores"),
                previous.get("aaum_crores")
            ),

            "aaum_percent_change": calculate_percent_change(
                current.get("aaum_crores"),
                previous.get("aaum_crores")
            ),

            "aum_change": calculate_change(
                current.get("aum_crores"),
                previous.get("aum_crores")
            ),

            "aum_percent_change": calculate_percent_change(
                current.get("aum_crores"),
                previous.get("aum_crores")
            ),

            "standard_deviation_change": calculate_change(
                current.get("standard_deviation"),
                previous.get("standard_deviation")
            ),

            "beta_change": calculate_change(
                current.get("beta"),
                previous.get("beta")
            ),

            "sharpe_ratio_change": calculate_change(
                current.get("sharpe_ratio"),
                previous.get("sharpe_ratio")
            ),

            "equity_turnover_change": calculate_change(
                current.get("equity_turnover"),
                previous.get("equity_turnover")
            ),

            "total_turnover_change": calculate_change(
                current.get("total_turnover"),
                previous.get("total_turnover")
            ),

            "holding_count_change": calculate_change(
                current.get("holding_count"),
                previous.get("holding_count")
            ),
        })

    return changes


def comparison_key(name):
    if not name:
        return None

    name = str(name).strip()

    # Normalize whitespace
    name = re.sub(r"\s+", " ", name)

    # Ignore trailing punctuation
    name = re.sub(r"\s*\.\s*$", "", name)

    # Ignore capitalization differences
    return name.upper()


def build_holding_changes(documents):
    sorted_documents = sort_by_date(documents)

    results = []

    for index in range(1, len(sorted_documents)):

        previous = sorted_documents[index - 1]
        current = sorted_documents[index]

        previous_holdings = {}
        current_holdings = {}

        # Build normalized comparison keys while preserving
        # the original display name and weight.
        for holding in previous.get("holdings", []):

            name = holding.get("name")
            key = comparison_key(name)

            if key:
                previous_holdings[key] = {
                    "name": name,
                    "weight_percent": holding.get("weight_percent")
                }

        for holding in current.get("holdings", []):

            name = holding.get("name")
            key = comparison_key(name)

            if key:
                current_holdings[key] = {
                    "name": name,
                    "weight_percent": holding.get("weight_percent")
                }

        previous_names = set(previous_holdings)
        current_names = set(current_holdings)

        new_names = current_names - previous_names
        removed_names = previous_names - current_names
        continuing_names = current_names & previous_names

        new_holdings = [
            {
                "name": current_holdings[key]["name"],
                "weight_percent": current_holdings[key]["weight_percent"]
            }
            for key in sorted(new_names)
        ]

        removed_holdings = [
            {
                "name": previous_holdings[key]["name"],
                "weight_percent": previous_holdings[key]["weight_percent"]
            }
            for key in sorted(removed_names)
        ]

        weight_increases = []
        weight_decreases = []
        unchanged_weights = []

        for key in continuing_names:

            previous_weight = previous_holdings[key]["weight_percent"]
            current_weight = current_holdings[key]["weight_percent"]

            if previous_weight is None or current_weight is None:
                continue

            change = current_weight - previous_weight

            record = {
                "name": current_holdings[key]["name"],
                "previous_weight_percent": previous_weight,
                "current_weight_percent": current_weight,
                "weight_change": change
            }

            if change > 0:
                weight_increases.append(record)

            elif change < 0:
                weight_decreases.append(record)

            else:
                unchanged_weights.append(record)

        weight_increases.sort(
            key=lambda x: x["weight_change"],
            reverse=True
        )

        weight_decreases.sort(
            key=lambda x: x["weight_change"]
        )

        results.append({
            "previous_date": previous.get("report_date"),
            "report_date": current.get("report_date"),

            "new_holdings": new_holdings,
            "removed_holdings": removed_holdings,

            "continuing_holdings": [
                current_holdings[key]["name"]
                for key in sorted(continuing_names)
            ],

            "weight_increases": weight_increases,
            "weight_decreases": weight_decreases,
            "unchanged_weights": unchanged_weights,

            "new_holding_count": len(new_holdings),
            "removed_holding_count": len(removed_holdings),
            "continuing_holding_count": len(continuing_names),
        })

    return results
