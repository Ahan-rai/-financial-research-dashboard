
import streamlit as st
import pandas as pd
from pathlib import Path

# Project directory
project = Path(
    r"C:\Users\Ahan Rai\anaconda_projects\07360977-eec4-4e7f-ad68-6149f2681a12\AI_Financial_Research"
)

from document_reader import read_pdf
from financial_extraction import extract_financial_data
from normalization import normalize_financial_data
from multi_period import (
    build_period_summary,
    build_period_changes,
    build_holding_changes,
)
from research_dataset import build_research_dataset


st.set_page_config(
    page_title="Financial Research Dashboard",
    page_icon="📊",
    layout="wide",
)


st.title("📊 Financial Research Dashboard")
st.caption("Deterministic Python financial analysis — no AI or external APIs")


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Upload Financial Reports")

uploaded_files = st.sidebar.file_uploader(
    "Upload one or more financial reports",
    type=["pdf"],
    accept_multiple_files=True,
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Upload multiple period reports to compare financial metrics, "
    "portfolio holdings and weight changes."
)


# ============================================================
# PROCESS DOCUMENTS
# ============================================================

if uploaded_files:

    documents = []

    for uploaded_file in uploaded_files:

        temp_path = project / "processed" / uploaded_file.name
        temp_path.parent.mkdir(exist_ok=True)

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:

            text = read_pdf(str(temp_path))

            data = extract_financial_data(
                text,
                filename=uploaded_file.name
            )

            data = normalize_financial_data(data)

            documents.append(data)

        except Exception as e:

            st.error(
                f"Could not process {uploaded_file.name}: {e}"
            )


    # ========================================================
    # SORT DOCUMENTS
    # ========================================================

    documents = sorted(
        documents,
        key=lambda x: x.get("report_date") or ""
    )


    if len(documents) == 0:

        st.error("No valid financial reports were processed.")

        st.stop()


    # ========================================================
    # BUILD ANALYSIS
    # ========================================================

    period_summary = build_period_summary(documents)

    period_changes = build_period_changes(documents)

    holding_changes = build_holding_changes(documents)

    research_dataset = build_research_dataset(
        documents,
        period_summary,
        period_changes,
        holding_changes,
    )


    st.success(
        f"Analysis completed successfully — "
        f"{len(documents)} reports processed."
    )


    # ========================================================
    # RESEARCH OVERVIEW
    # ========================================================

    st.header("Research Overview")

    latest = documents[-1]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Fund",
            latest.get("fund_name") or "Not available"
        )

    with col2:
        st.metric(
            "Reports Analyzed",
            len(documents)
        )

    with col3:
        aum = latest.get("aum_crores")

        st.metric(
            "Latest AUM",
            f"₹{aum:,.2f} Cr" if aum is not None else "Not available"
        )

    with col4:
        st.metric(
            "Latest Holdings",
            latest.get("holding_count", "Not available")
        )


    # ========================================================
    # FUND INFORMATION
    # ========================================================

    st.header("Fund Information")

    info_col1, info_col2, info_col3 = st.columns(3)

    with info_col1:
        st.write("**Fund Manager**")
        st.write(
            latest.get("fund_manager") or "Not available"
        )

    with info_col2:
        st.write("**Benchmark**")
        st.write(
            latest.get("benchmark") or "Not available"
        )

    with info_col3:
        st.write("**Analysis Period**")

        start_date = documents[0].get("report_date")
        end_date = documents[-1].get("report_date")

        st.write(
            f"{start_date} → {end_date}"
        )


    # ========================================================
    # FINANCIAL METRICS
    # ========================================================

    st.header("Financial Metrics")

    metric_rows = []

    for doc in documents:

        metric_rows.append(
            {
                "Period": doc.get("report_date"),
                "AUM (₹ Cr)": doc.get("aum_crores"),
                "AAUM (₹ Cr)": doc.get("aaum_crores"),
                "Std Dev (%)": doc.get("standard_deviation"),
                "Beta": doc.get("beta"),
                "Sharpe": doc.get("sharpe_ratio"),
                "Equity Turnover": doc.get("equity_turnover"),
                "Total Turnover": doc.get("total_turnover"),
                "Holdings": doc.get("holding_count"),
            }
        )

    metrics_df = pd.DataFrame(metric_rows)

    st.dataframe(
        metrics_df,
        use_container_width=True,
        hide_index=True,
    )


    # ========================================================
    # PERIOD CHANGES
    # ========================================================

    if period_changes:

        st.header("Period-over-Period Changes")

        change_rows = []

        for change in period_changes:

            change_rows.append(
                {
                    "Previous Period": change.get("previous_date"),
                    "Current Period": change.get("report_date"),
                    "AUM Change (₹ Cr)": change.get("aum_change"),
                    "AAUM Change (₹ Cr)": change.get("aaum_change"),
                    "Std Dev Change": change.get("standard_deviation_change"),
                    "Beta Change": change.get("beta_change"),
                    "Sharpe Change": change.get("sharpe_ratio_change"),
                    "Equity Turnover Change": change.get("equity_turnover_change"),
                    "Total Turnover Change": change.get("total_turnover_change"),
                }
            )

        changes_df = pd.DataFrame(change_rows)

        st.dataframe(
            changes_df,
            use_container_width=True,
            hide_index=True,
        )


    # ========================================================
    # PORTFOLIO CHANGES
    # ========================================================

    if holding_changes:

        st.header("Portfolio Changes")

        summary_rows = []

        for change in holding_changes:

            # IMPORTANT:
            # Actual engine keys are:
            # weight_increases
            # weight_decreases

            increases = change.get(
                "weight_increases",
                []
            )

            decreases = change.get(
                "weight_decreases",
                []
            )

            summary_rows.append(
                {
                    "Previous Period": change.get("previous_date"),
                    "Current Period": change.get("report_date"),
                    "New Holdings": change.get(
                        "new_holding_count",
                        len(change.get("new_holdings", []))
                    ),
                    "Removed Holdings": change.get(
                        "removed_holding_count",
                        len(change.get("removed_holdings", []))
                    ),
                    "Increased Weight": len(increases),
                    "Reduced Weight": len(decreases),
                    "Unchanged Weight": len(
                        change.get("unchanged_weights", [])
                    ),
                }
            )

        portfolio_summary_df = pd.DataFrame(
            summary_rows
        )

        st.dataframe(
            portfolio_summary_df,
            use_container_width=True,
            hide_index=True,
        )


        # ====================================================
        # DETAILED PERIOD TABS
        # ====================================================

        for change in holding_changes:

            previous_date = change.get(
                "previous_date",
                "Previous"
            )

            current_date = change.get(
                "report_date",
                "Current"
            )

            st.subheader(
                f"{previous_date} → {current_date}"
            )

            added = change.get(
                "new_holdings",
                []
            )

            removed = change.get(
                "removed_holdings",
                []
            )

            increased = change.get(
                "weight_increases",
                []
            )

            decreased = change.get(
                "weight_decreases",
                []
            )

            unchanged = change.get(
                "unchanged_weights",
                []
            )


            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                [
                    "Added",
                    "Exited",
                    "Increased",
                    "Reduced",
                    "Unchanged",
                ]
            )


            # =================================================
            # ADDED
            # =================================================

            with tab1:

                if added:

                    added_df = pd.DataFrame(added)

                    st.dataframe(
                        added_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    st.info(
                        "No new holdings in this period."
                    )


            # =================================================
            # EXITED
            # =================================================

            with tab2:

                if removed:

                    removed_df = pd.DataFrame(removed)

                    st.dataframe(
                        removed_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    st.info(
                        "No holdings exited in this period."
                    )


            # =================================================
            # INCREASED
            # =================================================

            with tab3:

                if increased:

                    increased_rows = []

                    for item in increased:

                        increased_rows.append(
                            {
                                "Company": item.get("name"),
                                "Previous Weight (%)": item.get(
                                    "previous_weight_percent"
                                ),
                                "Current Weight (%)": item.get(
                                    "current_weight_percent"
                                ),
                                "Change (pp)": round(
                                    item.get(
                                        "weight_change",
                                        0
                                    ),
                                    2,
                                ),
                            }
                        )

                    increased_df = pd.DataFrame(
                        increased_rows
                    )

                    st.dataframe(
                        increased_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    st.info(
                        "No increased-weight holdings."
                    )


            # =================================================
            # REDUCED
            # =================================================

            with tab4:

                if decreased:

                    decreased_rows = []

                    for item in decreased:

                        decreased_rows.append(
                            {
                                "Company": item.get("name"),
                                "Previous Weight (%)": item.get(
                                    "previous_weight_percent"
                                ),
                                "Current Weight (%)": item.get(
                                    "current_weight_percent"
                                ),
                                "Change (pp)": round(
                                    item.get(
                                        "weight_change",
                                        0
                                    ),
                                    2,
                                ),
                            }
                        )

                    decreased_df = pd.DataFrame(
                        decreased_rows
                    )

                    st.dataframe(
                        decreased_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    st.info(
                        "No reduced-weight holdings."
                    )


            # =================================================
            # UNCHANGED
            # =================================================

            with tab5:

                if unchanged:

                    unchanged_rows = []

                    for item in unchanged:

                        unchanged_rows.append(
                            {
                                "Company": item.get("name"),
                                "Weight (%)": item.get(
                                    "current_weight_percent"
                                ),
                            }
                        )

                    unchanged_df = pd.DataFrame(
                        unchanged_rows
                    )

                    st.dataframe(
                        unchanged_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    st.info(
                        "No unchanged holdings."
                    )


    # ========================================================
    # LATEST PORTFOLIO
    # ========================================================

    st.header("Latest Portfolio")

    latest_holdings = latest.get(
        "holdings",
        []
    )

    if latest_holdings:

        portfolio_rows = []

        for holding in latest_holdings:

            portfolio_rows.append(
                {
                    "Company": holding.get("name"),
                    "Weight (%)": holding.get(
                        "weight_percent"
                    ),
                }
            )

        portfolio_df = pd.DataFrame(
            portfolio_rows
        )

        portfolio_df = portfolio_df.sort_values(
            "Weight (%)",
            ascending=False,
        )

        st.dataframe(
            portfolio_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Portfolio holdings are not available."
        )


    # ========================================================
    # TECHNICAL DATASET
    # ========================================================

    with st.expander("Technical Dataset"):

        st.json(
            research_dataset
        )


else:

    st.info(
        "Upload financial reports from the sidebar to begin."
    )
