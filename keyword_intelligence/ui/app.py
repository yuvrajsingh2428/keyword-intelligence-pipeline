"""Simplified Streamlit App Entry Point for Keyword Intelligence Pipeline."""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from keyword_intelligence.core.bootstrap import bootstrap
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.reporting.models import ReportResult
from keyword_intelligence.ui.services.pipeline_runner import PipelineRunner
from keyword_intelligence.ui.themes.theme import inject_css

# Must be the first Streamlit command
st.set_page_config(
    page_title="Keyword Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _init_app() -> None:
    """Initialize application DI container exactly once."""
    from keyword_intelligence.core.container import container
    from keyword_intelligence.pipeline.registry import StageRegistry

    try:
        container.resolve(StageRegistry)
    except Exception:
        bootstrap()


def main() -> None:
    """Main application entry point."""
    _init_app()
    st.markdown(inject_css(), unsafe_allow_html=True)

    st.title("Keyword Intelligence Pipeline")
    st.markdown("Automated keyword analysis, classification, and clustering.")
    st.markdown("---")

    import pickle
    import os

    STATE_FILE = ".last_run.pkl"

    # Initialize state
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    
    # Attempt to load from disk on fresh session
    if "result_context" not in st.session_state:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "rb") as f:
                    saved_state = pickle.load(f)
                for k, v in saved_state.items():
                    st.session_state[k] = v
            except Exception:
                st.session_state.result_context = None
                st.session_state.result_report = None
        else:
            st.session_state.result_context = None
            st.session_state.result_report = None

    # 1. Setup Form
    st.subheader("1. Setup")

    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g., Lenovo",
            disabled=st.session_state.is_processing,
        )
    with col2:
        website = st.text_input(
            "Company Website",
            placeholder="e.g., https://www.lenovo.com",
            disabled=st.session_state.is_processing,
        )

    uploaded_file = st.file_uploader(
        "Upload Dataset (CSV/Excel)",
        type=["csv", "xlsx", "xls"],
        disabled=st.session_state.is_processing,
    )

    can_run = bool(company_name and website and uploaded_file)

    if st.button(
        "🚀 Run Pipeline",
        type="primary",
        disabled=not can_run or st.session_state.is_processing,
    ):
        if uploaded_file is not None:
            st.session_state.is_processing = True
            st.session_state.file_bytes = uploaded_file.getvalue()
            st.session_state.file_name = uploaded_file.name
            st.session_state.company_name = company_name
            st.session_state.website = website
            st.session_state.result_context = None
            st.session_state.result_report = None
            st.rerun()

    # 2. Processing State
    if st.session_state.is_processing:
        st.markdown("---")
        st.subheader("2. Processing")
        with st.status("Running Pipeline...", expanded=True) as status:
            status_container = st.empty()

            from typing import Any

            def st_sink(msg: Any) -> None:
                record_msg = msg.record["message"]
                if (
                    "Using Gemini" in record_msg
                    or "Switching to" in record_msg
                    or "exhausted" in record_msg
                    or "OpenRouter" in record_msg
                    or "quota" in record_msg
                ):
                    status_container.markdown(f"**Status**: {record_msg}")

            from loguru import logger

            logger_id = logger.add(
                st_sink,
                format="{message}",
                filter=lambda record: "keyword_intelligence" in str(record["name"]),
            )

            runner = PipelineRunner()
            try:
                runner.run(
                    file_bytes=st.session_state.file_bytes,
                    file_name=st.session_state.file_name,
                    company_name=st.session_state.company_name,
                    website=st.session_state.website,
                    industry="",
                )

                st.session_state.result_context = runner.context
                st.session_state.result_report = runner.report
                st.session_state.is_processing = False
                
                # Save state to disk for persistence across browser refreshes
                try:
                    with open(STATE_FILE, "wb") as f:
                        pickle.dump({
                            "result_context": runner.context,
                            "result_report": runner.report,
                            "file_bytes": st.session_state.file_bytes,
                            "file_name": st.session_state.file_name,
                            "company_name": st.session_state.company_name,
                            "website": st.session_state.website,
                        }, f)
                except Exception:
                    pass

                status.update(
                    label="Pipeline Complete", state="complete", expanded=False
                )
                st.rerun()
            except Exception as e:
                st.session_state.is_processing = False
                status.update(
                    label=f"Pipeline Failed: {e}", state="error", expanded=True
                )
                st.error("An error occurred during processing.")
                st.stop()
            finally:
                logger.remove(logger_id)

    # 3. Results Section
    if st.session_state.result_context and st.session_state.result_report:
        st.markdown("---")
        st.subheader("3. Results Summary")

        context: PipelineContext = st.session_state.result_context
        report: ReportResult = st.session_state.result_report

        stats = report.analytics.dataset
        rel = report.analytics.relevance

        # Pipeline Summary Card
        st.markdown("#### Pipeline Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Keywords", f"{stats.total_keywords:,}")
        m2.metric("Relevant Keywords", f"{rel.relevant:,}")
        m3.metric("Irrelevant Keywords", f"{rel.irrelevant:,}")

        df = context.data
        ai_classified = (
            df["ai_confidence"].notna().sum() if "ai_confidence" in df.columns else 0
        )
        det_matches = len(df) - ai_classified

        m4, m5, m6 = st.columns(3)
        m4.metric("AI Classified", f"{ai_classified:,}")
        m5.metric("Deterministic Matches", f"{det_matches:,}")
        m6.metric(
            "Total Processing Time",
            f"{report.pipeline.timing.total_execution_time_ms / 1000:.1f}s",
        )

        filtered_count = stats.duplicate_keywords + rel.irrelevant
        st.success(
            f"Pipeline Completed Successfully. Processed: {stats.total_keywords}, Relevant: {rel.relevant}, Filtered: {filtered_count}"
        )

        st.markdown("#### Keyword Classification Preview")
        st.dataframe(context.data.head(20), use_container_width=True)

        st.markdown("#### Downloads")
        dl_col1, dl_col2 = st.columns(2)

        # Create Excel Bytes in-memory for download
        buf_all = io.BytesIO()
        buf_rel = io.BytesIO()

        with pd.ExcelWriter(buf_all, engine="openpyxl") as w:
            df.to_excel(w, sheet_name="All Keywords", index=False)

        with pd.ExcelWriter(buf_rel, engine="openpyxl") as w:
            df_rel = df
            if "business_relevance" in df_rel.columns:
                df_rel = df_rel[
                    df_rel["business_relevance"].astype(str).str.lower() == "relevant"
                ]
            elif "relevance" in df_rel.columns:
                df_rel = df_rel[
                    df_rel["relevance"].astype(str).str.lower() == "relevant"
                ]
            df_rel.to_excel(w, sheet_name="Relevant Keywords", index=False)

        with dl_col1:
            st.download_button(
                "⬇️ Download Complete Report",
                data=buf_all.getvalue(),
                file_name="complete_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="secondary",
            )

        with dl_col2:
            st.download_button(
                "⬇️ Download Relevant Keywords Only",
                data=buf_rel.getvalue(),
                file_name="relevant_keywords.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )


if __name__ == "__main__":
    main()
