"""Simplified Streamlit App Entry Point for Keyword Intelligence Pipeline."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from keyword_intelligence.core.bootstrap import bootstrap
from keyword_intelligence.interfaces.streamlit_runner import StreamlitRunner
from keyword_intelligence.pipeline.context import PipelineContext
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

    import os
    import pickle

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

    selected_sheet = None
    keyword_column = None
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        from keyword_intelligence.input_loader.loader import InputLoader

        loader = InputLoader()

        if file_ext in ["xlsx", "xls"]:
            try:
                sheets = loader.get_sheet_names(uploaded_file.getvalue())
                if len(sheets) > 1:
                    selected_sheet = st.selectbox(
                        "Select Sheet",
                        options=sheets,
                        disabled=st.session_state.is_processing,
                    )
                elif sheets:
                    selected_sheet = sheets[0]
            except Exception as e:
                st.error(f"Failed to read Excel sheets: {e}")

        # Extract columns and resolve keyword column
        try:
            from keyword_intelligence.column_resolver.resolver import ColumnResolver

            columns = loader.get_columns(
                uploaded_file.getvalue(),
                file_name=uploaded_file.name,
                sheet_name=selected_sheet,
            )
            resolver = ColumnResolver()
            candidates = resolver.resolve(columns)

            # Use top candidate by default
            top_col = candidates[0].original_column

            # If multiple candidates, allow user to choose
            if len(candidates) > 1:
                # Build option labels including confidence
                options = [c.original_column for c in candidates]
                format_func = lambda col: next(
                    f"{c.original_column} (Confidence: {c.confidence_score}%, Method: {c.method.value})"
                    for c in candidates
                    if c.original_column == col
                )
                keyword_column = st.selectbox(
                    "Select Keyword Column",
                    options=options,
                    index=0,
                    format_func=format_func,
                    disabled=st.session_state.is_processing,
                )
            else:
                keyword_column = top_col

        except Exception as e:
            st.error(f"Failed to resolve keyword column: {e}")
            keyword_column = None

    can_run = bool(company_name and website and uploaded_file and keyword_column)

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
            st.session_state.sheet_name = selected_sheet
            st.session_state.keyword_column = keyword_column
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

            runner = StreamlitRunner()
            try:
                runner.run(
                    file_bytes=st.session_state.file_bytes,
                    file_name=st.session_state.file_name,
                    company_name=st.session_state.company_name,
                    website=st.session_state.website,
                    industry="",
                    sheet_name=st.session_state.get("sheet_name"),
                    keyword_column=st.session_state.get("keyword_column"),
                )

                st.session_state.result_context = runner.context
                st.session_state.result_report = runner.report
                st.session_state.is_processing = False

                # Save state to disk for persistence across browser refreshes
                try:
                    with open(STATE_FILE, "wb") as f:
                        pickle.dump(
                            {
                                "result_context": runner.context,
                                "result_report": runner.report,
                                "file_bytes": st.session_state.file_bytes,
                                "file_name": st.session_state.file_name,
                                "company_name": st.session_state.company_name,
                                "website": st.session_state.website,
                                "sheet_name": st.session_state.get("sheet_name"),
                                "keyword_column": st.session_state.get(
                                    "keyword_column"
                                ),
                            },
                            f,
                        )
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
    if st.session_state.result_context and hasattr(
        st.session_state.result_context, "execution_id"
    ):
        st.markdown("---")
        st.subheader("3. Execution Summary")

        context: PipelineContext = st.session_state.result_context
        # Use PipelineContext and PipelineResult since we bypass old ReportingStage
        result_file = None
        for file in getattr(context, "output_file_locations", []):
            if file.endswith("filtered_keywords.csv"):
                result_file = file

        df = context.data

        decisions = (
            df["decision"].value_counts().to_dict() if "decision" in df.columns else {}
        )
        keep_count = decisions.get("KEEP", 0)
        drop_count = decisions.get("DROP", 0)
        review_count = decisions.get("REVIEW", 0)
        send_to_ai_count = decisions.get("SEND_TO_AI", 0)

        # Pipeline Summary Card
        st.markdown("#### Pipeline Observability")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Processed", f"{len(df):,}")
        m2.metric("KEEP", f"{keep_count:,}")
        m3.metric("DROP", f"{drop_count:,}")
        m4.metric("REVIEW", f"{review_count:,}")
        m5.metric("SEND_TO_AI", f"{send_to_ai_count:,}")

        relevant_count = df["relevant"].sum() if "relevant" in df.columns else 0
        irrelevant_count = len(df) - relevant_count

        duplicates = (
            df["duplicate_group"].nunique() if "duplicate_group" in df.columns else 0
        )

        m6, m7, m8, m9 = st.columns(4)
        m6.metric("Relevant", f"{relevant_count:,}")
        m7.metric("Irrelevant", f"{irrelevant_count:,}")
        m8.metric("Duplicates Grouped", f"{duplicates:,}")
        m9.metric(
            "Total Execution Time",
            f"{context.pipeline_metrics.total_time_ms / 1000:.2f}s",
        )

        st.success(
            f"Pipeline Execution Complete. {len(context.errors)} errors, {len(context.warnings)} warnings."
        )

        st.markdown("#### Stage Timings")
        stage_data = []
        for stage_metric in context.stage_metrics:
            stage_data.append(
                {
                    "Stage": stage_metric.stage_name,
                    "Duration (ms)": round(stage_metric.processing_time_ms, 2),
                    "Input Rows": stage_metric.rows_loaded,
                    "Output Rows": stage_metric.rows_output,
                    "Success": stage_metric.success,
                }
            )
        st.dataframe(pd.DataFrame(stage_data), use_container_width=True)

        st.markdown("#### Keyword Classification Preview")
        st.dataframe(df.head(20), use_container_width=True)

        import io

        st.markdown("#### Downloads")
        dl_col1, dl_col2 = st.columns(2)

        df_relevant = df[df["relevant"] == True] if "relevant" in df.columns else df

        # Create Excel for all data
        buffer_all = io.BytesIO()
        # openpyxl is typical engine but xlsxwriter is fine if installed. Fallback to openpyxl
        try:
            with pd.ExcelWriter(buffer_all, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Complete Report")
        except ImportError:
            with pd.ExcelWriter(buffer_all, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Complete Report")
        excel_all = buffer_all.getvalue()

        # Create Excel for relevant data
        buffer_relevant = io.BytesIO()
        try:
            with pd.ExcelWriter(buffer_relevant, engine="xlsxwriter") as writer:
                df_relevant.to_excel(writer, index=False, sheet_name="Relevant Keywords")
        except ImportError:
            with pd.ExcelWriter(buffer_relevant, engine="openpyxl") as writer:
                df_relevant.to_excel(writer, index=False, sheet_name="Relevant Keywords")
        excel_relevant = buffer_relevant.getvalue()

        with dl_col1:
            st.download_button(
                "⬇️ Download Complete Report (Excel)",
                data=excel_all,
                file_name="complete_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="secondary",
            )

        with dl_col2:
            st.download_button(
                "⬇️ Download Relevant Keywords Only (Excel)",
                data=excel_relevant,
                file_name="relevant_keywords.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )


if __name__ == "__main__":
    main()
