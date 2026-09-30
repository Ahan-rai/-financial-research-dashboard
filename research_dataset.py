from multi_period import sort_by_date


def build_research_dataset(
    documents,
    period_summary,
    period_changes,
    holding_changes
):

    documents = sort_by_date(documents)

    latest = documents[-1] if documents else None

    dataset = {
        "fund": {
            "name": latest.get("fund_name") if latest else None,
            "fund_manager": latest.get("fund_manager") if latest else None,
            "benchmark": latest.get("benchmark") if latest else None,
            "period_start": documents[0].get("report_date") if documents else None,
            "period_end": latest.get("report_date") if latest else None,
            "period_count": len(documents),
        },

        "period_summary": period_summary,

        "period_changes": period_changes,

        "holding_changes": holding_changes,

        "monthly_documents": documents,

        "latest_period": latest,
    }

    return dataset
