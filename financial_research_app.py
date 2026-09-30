
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AI Financial Research",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AI Financial Research")
st.caption(
    "Multi-period financial document analysis and portfolio research"
)

st.divider()

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.header("Research Settings")

uploaded_files = st.sidebar.file_uploader(
    "Upload financial reports",
    type=["pdf", "csv", "xlsx", "xls", "txt", "md", "docx"],
    accept_multiple_files=True
)

analyze_button = st.sidebar.button(
    "Run Analysis",
    type="primary",
    use_container_width=True
)

st.sidebar.divider()

st.sidebar.info(
    "Upload two or more financial reports to compare "
    "metrics, holdings and portfolio movements."
)

# ---------------------------------------------------------
# MAIN PAGE
# ---------------------------------------------------------

if not uploaded_files:

    st.info(
        "Upload financial reports from the sidebar to begin the analysis."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Document Analysis",
            "Ready"
        )

    with col2:
        st.metric(
            "Portfolio Comparison",
            "Ready"
        )

    with col3:
        st.metric(
            "Research Report",
            "Ready"
        )

    st.divider()

    st.subheader("Supported Analysis")

    st.markdown("""
    - 📄 Financial document extraction
    - 📅 Multi-period comparison
    - 💰 AUM / AAUM analysis
    - 📊 Risk and turnover metrics
    - 🏢 Portfolio holdings comparison
    - ➕ Added holdings
    - ➖ Exited holdings
    - 📈 Increased / reduced weights
    - 🏭 Sector allocation changes
    - 📝 Automated research report
    """)

else:

    st.success(
        f"{len(uploaded_files)} file(s) uploaded successfully."
    )

    st.subheader("Uploaded Documents")

    file_data = []

    for file in uploaded_files:
        file_data.append({
            "File Name": file.name,
            "File Type": file.type,
            "Size (KB)": round(file.size / 1024, 2)
        })

    files_df = pd.DataFrame(file_data)

    st.dataframe(
        files_df,
        use_container_width=True,
        hide_index=True
    )

    if analyze_button:

        st.divider()

        st.subheader("Analysis")

        st.warning(
            "The Streamlit interface is connected successfully. "
            "The next step is to connect the validated research engine."
        )

        st.info(
            "No analysis has been run yet. The extraction and comparison "
            "functions from the Jupyter research engine will be connected "
            "in the next stage."
        )
