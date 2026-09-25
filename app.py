import streamlit as st
import pandas as pd
import openai
import asyncio
import base64
import io
import json
import matplotlib
import re
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

from privacy import (
    create_masking_salt,
    detect_sensitive_columns,
    mask_sensitive_data,
    mask_sensitive_text,
)

st.set_page_config(
    page_title="My CSV Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
from pdf_tool_client import request_pdf_report

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-bottom: 7rem;
    }

    [data-testid="stAppViewContainer"] .main [data-testid="stChatInput"] {
        position: fixed;
        right: max(3rem, calc((100vw - 21rem - 76rem) / 2));
        bottom: 1rem;
        left: calc(21rem + max(3rem, calc((100vw - 21rem - 76rem) / 2)));
        z-index: 1000;
        padding: 0.75rem;
        background-color: #ffffff !important;
        border: 1px solid #c7cbd1;
        border-radius: 8px;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.18);
    }

    [data-testid="stAppViewContainer"]:has(
        [data-testid="stSidebar"][aria-expanded="false"]
    ) .main [data-testid="stChatInput"] {
        right: max(3rem, calc((100vw - 76rem) / 2));
        left: max(3rem, calc((100vw - 76rem) / 2));
    }

    [data-testid="stAppViewContainer"] .main [data-testid="stChatInput"] > div,
    [data-testid="stAppViewContainer"] .main [data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        color: #111827 !important;
    }

    [data-testid="stAppViewContainer"] .main [data-testid="stChatInput"] textarea::placeholder {
        color: #5f6773 !important;
        opacity: 1;
    }

    @media (max-width: 768px) {
        [data-testid="stAppViewContainer"] .main [data-testid="stChatInput"] {
            right: 1rem;
            left: 1rem;
            bottom: 0.75rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

OPENAI_MODEL = st.secrets.get("OpenAI_Model", "gpt-4o")
PDF_MCP_URL = st.secrets.get("PDF_MCP_URL", "http://localhost:8000/mcp")
PYTHON_CODE_BLOCK_RE = re.compile(r"```(?:python|py)\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)
TABLE_DISPLAY_ROW_LIMIT = 10
MAX_UPLOAD_ROWS = 50000
MAX_CONTEXT_ROWS = 100
MAX_RESPONSE_TOKENS = 500
MAX_REQUESTS_PER_SESSION = 10
MAX_CONTEXT_CATEGORICAL_COLUMNS = 8
MAX_CONTEXT_CATEGORY_VALUES = 5
MAX_CONTEXT_CORRELATION_PAIRS = 8
MODEL_PRICING_PER_MILLION_TOKENS = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
}
PDF_EXPORT_TOOL = {
    "type": "function",
    "function": {
        "name": "request_pdf_report",
        "description": (
            "Request a stakeholder-ready PDF export only when the user explicitly asks "
            "to create, export, or download a PDF report of the current analysis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Concise business report title.",
                },
                "focus": {
                    "type": "string",
                    "description": "The business decision or optimization focus for the report.",
                },
            },
            "required": ["title", "focus"],
            "additionalProperties": False,
        },
    },
}
LAST_ROWS_RE = re.compile(r"\b(last|bottom|tail|ending|end|most recent|latest)\b", re.IGNORECASE)
ROW_LIMIT_RE = re.compile(
    r"\b(?:top|first|head|last|bottom|tail|show)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b",
    re.IGNORECASE,
)
NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

#Session State Initialization
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if "df" not in st.session_state:
    st.session_state["df"] = None
    
if "data_summary" not in st.session_state:
    st.session_state.data_summary = {
        "shape": None,
        "columns": None,
        "dtypes": None,
        "sample_data": None,
        "summary_stats": None
    }

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

if "input_tokens_used" not in st.session_state:
    st.session_state.input_tokens_used = 0

if "output_tokens_used" not in st.session_state:
    st.session_state.output_tokens_used = 0

if "privacy_salt" not in st.session_state:
    st.session_state.privacy_salt = create_masking_salt()

if "privacy_findings" not in st.session_state:
    st.session_state.privacy_findings = {}

if "uploaded_file_signature" not in st.session_state:
    st.session_state.uploaded_file_signature = None

if "pending_pdf_export" not in st.session_state:
    st.session_state.pending_pdf_export = None

if "pdf_export" not in st.session_state:
    st.session_state.pdf_export = None


class OpenAIProvider:
    name = "OpenAI"

    def __init__(self, api_key, model):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def generate(self, messages, max_output_tokens, tools=None):
        request = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": max_output_tokens,
        }
        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"
        return self.client.chat.completions.create(
            **request,
        )


def estimate_tokens(text):
    """Return a deliberately simple pre-request estimate for warning purposes."""
    return max(1, (len(text or "") + 3) // 4)


def estimate_cost(model, input_tokens, output_tokens):
    pricing = MODEL_PRICING_PER_MILLION_TOKENS.get(model)
    if not pricing:
        return None
    return (
        input_tokens * pricing["input"]
        + output_tokens * pricing["output"]
    ) / 1_000_000


def record_response_usage(response):
    usage = getattr(response, "usage", None)
    if not usage:
        return
    st.session_state.input_tokens_used += getattr(usage, "prompt_tokens", 0) or 0
    st.session_state.output_tokens_used += getattr(usage, "completion_tokens", 0) or 0


def build_report_payload(
    messages,
    title,
    focus,
    industry,
    business_goal,
    privacy_findings,
    usage_summary,
    privacy_summary,
):
    protected_columns = set(privacy_findings)
    analyses = []
    pending_question = None
    for message in messages:
        if message.get("role") == "user":
            pending_question = message.get("content", "")
            continue
        if message.get("role") != "assistant" or not pending_question:
            continue

        tables = []
        for dataframe in message.get("tables", []):
            if not isinstance(dataframe, pd.DataFrame):
                continue
            report_df = dataframe.drop(
                columns=[column for column in dataframe.columns if str(column) in protected_columns],
                errors="ignore",
            ).head(TABLE_DISPLAY_ROW_LIMIT)
            if report_df.empty:
                continue
            tables.append(
                {
                    "columns": [str(column) for column in report_df.columns],
                    "rows": report_df.fillna("").astype(str).values.tolist(),
                }
            )

        analyses.append(
            {
                "question": pending_question,
                "interpretation": message.get("report_interpretation")
                or message.get("content", ""),
                "images": [
                    base64.b64encode(image).decode("ascii")
                    for image in message.get("images", [])
                ],
                "tables": tables,
                "notes": message.get("notes", []),
            }
        )
        pending_question = None

    return {
        "title": title or "Business Analysis Report",
        "focus": focus,
        "industry": industry,
        "business_goal": business_goal,
        "usage_summary": usage_summary,
        "privacy_summary": privacy_summary,
        "analyses": analyses,
    }


def build_execution_evidence(exec_globals, assistant_message, chart_metadata):
    sections = []
    for table in assistant_message.get("tables", []):
        if isinstance(table, pd.DataFrame) and not table.empty:
            sections.append(table.head(TABLE_DISPLAY_ROW_LIMIT).to_string(index=False))

    for name, value in exec_globals.items():
        if name in {"df", "pd", "np", "plt", "sns", "st"}:
            continue
        if isinstance(value, pd.Series):
            sections.append(f"{name}:\n{value.head(TABLE_DISPLAY_ROW_LIMIT).to_string()}")
        elif isinstance(value, (str, int, float, bool, np.number)):
            sections.append(f"{name}: {value}")

    sections.extend(chart_metadata)
    return "\n\n".join(sections)[:12000]


def requested_table_limit(user_query):
    match = ROW_LIMIT_RE.search(user_query or "")
    if not match:
        return TABLE_DISPLAY_ROW_LIMIT

    raw_limit = match.group(1).lower()
    requested_limit = int(raw_limit) if raw_limit.isdigit() else NUMBER_WORDS.get(raw_limit, TABLE_DISPLAY_ROW_LIMIT)
    return max(1, min(requested_limit, TABLE_DISPLAY_ROW_LIMIT))


def should_show_last_rows(user_query):
    return bool(LAST_ROWS_RE.search(user_query or ""))


def build_data_context(df):
    context_sections = [
        f"Dataset shape: {df.shape[0]} rows x {df.shape[1]} columns",
        f"Column names: {', '.join(df.columns.astype(str))}",
        f"Data types: {df.dtypes.astype(str).to_dict()}",
    ]

    if len(df) <= MAX_CONTEXT_ROWS:
        context_sections.append(f"Full dataset:\n{df.to_string(index=False)}")
    else:
        context_sections.append(
            f"First 10 rows for structure only:\n{df.head(10).to_string(index=False)}"
        )

    missing_summary = (
        df.isnull()
        .sum()
        .sort_values(ascending=False)
    )
    missing_summary = missing_summary[missing_summary > 0].head(10)
    if missing_summary.empty:
        context_sections.append("Missing values: none detected")
    else:
        context_sections.append(f"Columns with missing values:\n{missing_summary.to_string()}")

    numeric_df = df.select_dtypes(include="number")
    if not numeric_df.empty:
        numeric_summary = numeric_df.describe().T[["min", "max", "mean", "50%"]].rename(
            columns={"min": "Min", "max": "Max", "mean": "Mean", "50%": "Median"}
        )
        context_sections.append(
            f"Numeric summary:\n{numeric_summary.round(2).to_string()}"
        )

        if len(numeric_df.columns) >= 2:
            corr = numeric_df.corr(numeric_only=True).abs()
            corr_pairs = (
                corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
                .stack()
                .sort_values(ascending=False)
                .head(MAX_CONTEXT_CORRELATION_PAIRS)
            )
            if not corr_pairs.empty:
                pair_lines = [
                    f"{left} vs {right}: {value:.2f}"
                    for (left, right), value in corr_pairs.items()
                ]
                context_sections.append(
                    "Strongest numeric correlations:\n" + "\n".join(pair_lines)
                )

    categorical_df = df.select_dtypes(include=["object", "category", "bool"])
    categorical_sections = []
    for column in categorical_df.columns[:MAX_CONTEXT_CATEGORICAL_COLUMNS]:
        value_counts = (
            categorical_df[column]
            .astype("string")
            .fillna("<missing>")
            .value_counts()
            .head(MAX_CONTEXT_CATEGORY_VALUES)
        )
        categorical_sections.append(f"{column}: {value_counts.to_dict()}")
    if categorical_sections:
        context_sections.append(
            "Top categorical values:\n" + "\n".join(categorical_sections)
        )

    return "\n\n".join(context_sections)


def limit_table_for_display(table, user_query=None):
    if not isinstance(table, pd.DataFrame) or table.empty:
        return table, None

    row_limit = requested_table_limit(user_query)
    total_rows = len(table)
    if total_rows <= row_limit:
        return table, None

    if should_show_last_rows(user_query):
        limited_table = table.tail(row_limit)
        direction = "last"
    else:
        limited_table = table.head(row_limit)
        direction = "top"

    note = f"Showing the {direction} {row_limit} rows from {total_rows} matching rows to keep the output focused."
    return limited_table, note


def display_generated_table(value, assistant_message, user_query, displayed_table_ids=None):
    if isinstance(value, pd.DataFrame):
        table = value
    elif isinstance(value, list) and value and isinstance(value[0], dict):
        table = pd.DataFrame(value)
    else:
        return False

    if table.empty:
        return False

    limited_table, note = limit_table_for_display(table, user_query)
    st.dataframe(limited_table, use_container_width=True)
    assistant_message["tables"].append(limited_table)

    if displayed_table_ids is not None:
        displayed_table_ids.add(id(value))
        displayed_table_ids.add(id(table))

    if note and note not in assistant_message["notes"]:
        st.info(note)
        assistant_message["notes"].append(note)

    return True


class GeneratedCodeStreamlitProxy:
    def __init__(self, assistant_message, user_query, displayed_table_ids):
        self.assistant_message = assistant_message
        self.user_query = user_query
        self.displayed_table_ids = displayed_table_ids

    def dataframe(self, data=None, *args, **kwargs):
        if display_generated_table(data, self.assistant_message, self.user_query, self.displayed_table_ids):
            return None
        return st.dataframe(data, *args, **kwargs)

    def table(self, data=None, *args, **kwargs):
        if display_generated_table(data, self.assistant_message, self.user_query, self.displayed_table_ids):
            return None
        return st.table(data, *args, **kwargs)

    def write(self, *args, **kwargs):
        displayed_any_table = False
        for arg in args:
            displayed_any_table = display_generated_table(
                arg,
                self.assistant_message,
                self.user_query,
                self.displayed_table_ids,
            ) or displayed_any_table
        if not displayed_any_table:
            return st.write(*args, **kwargs)
        return None

    def __getattr__(self, name):
        return getattr(st, name)


def render_saved_message(msg):
    with st.chat_message(msg["role"]):
        if msg.get("content"):
            st.markdown(msg["content"])
        for note in msg.get("notes", []):
            st.info(note)
        for table in msg.get("tables", []):
            if isinstance(table, pd.DataFrame):
                limited_table, _ = limit_table_for_display(table)
                st.dataframe(limited_table, use_container_width=True)
        for image in msg.get("images", []):
            st.image(image, use_column_width=True)


def extract_python_code_blocks(text):
    return [block.strip() for block in PYTHON_CODE_BLOCK_RE.findall(text)]


def hide_python_code_blocks(text):
    cleaned = PYTHON_CODE_BLOCK_RE.sub("\n\n", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned or "Here are the results from the analysis."


st.title("📊Derive Insights about your private CSV data")
st.markdown('Upload your CSV file and gain insight into faster and accurate decision-making.')

with st.sidebar: #the 'with' creates a context where everything inside appears inside the side bar
    privacy_alert_placeholder = st.empty()
    st.header("Upload your CSV file")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
    st.divider()
    st.subheader("AI Provider")
    provider_name = st.selectbox("Provider", ["OpenAI"], key="provider_select")
    credential_source = st.radio(
        "API key",
        ["Use app key", "Use my own key"],
        help="Your own key is kept only in this browser session and is not written to disk.",
    )
    user_api_key = ""
    if credential_source == "Use my own key":
        user_api_key = st.text_input(
            "OpenAI API key",
            type="password",
            placeholder="sk-...",
        )

    selected_output_tokens = st.slider(
        "Maximum response tokens",
        min_value=100,
        max_value=MAX_RESPONSE_TOKENS,
        value=MAX_RESPONSE_TOKENS,
        step=50,
        help="This is a hard output cap for each request.",
    )
    remaining_requests = max(0, MAX_REQUESTS_PER_SESSION - st.session_state.request_count)
    total_tokens_used = st.session_state.input_tokens_used + st.session_state.output_tokens_used
    estimated_session_cost = estimate_cost(
        OPENAI_MODEL,
        st.session_state.input_tokens_used,
        st.session_state.output_tokens_used,
    )
    st.progress(st.session_state.request_count / MAX_REQUESTS_PER_SESSION)
    st.caption(
        f"{st.session_state.request_count} of {MAX_REQUESTS_PER_SESSION} requests used · "
        f"{remaining_requests} remaining"
    )
    st.caption(
        f"{st.session_state.input_tokens_used:,} input tokens · "
        f"{st.session_state.output_tokens_used:,} output tokens · "
        f"{total_tokens_used:,} total"
    )
    if estimated_session_cost is not None:
        st.caption(f"Estimated session token cost: ${estimated_session_cost:.6f}")


data_summary_tab, insights_tab = st.tabs(["Data Summary", "Insights"])

with insights_tab:
    with st.expander("Business Context", expanded=False):
        selected_industry = st.selectbox(
            "Industry",
            [
                "Auto-detect from data",
                "Retail / E-commerce",
                "Financial Services",
                "Healthcare",
                "Education",
                "Manufacturing",
                "SaaS / Technology",
                "Logistics / Supply Chain",
                "Marketing / Advertising",
                "Other",
            ],
            key="industry_select",
        )
        business_goal = st.text_area(
            "Business goal or audience",
            placeholder="Example: Explain revenue drivers for store managers",
            height=90,
        )
        st.caption(
            "This context guides the business interpretation shown below."
        )
    
if uploaded_file is not None: # move entire code inside the with block up
    try:
        raw_df = pd.read_csv(uploaded_file, nrows=MAX_UPLOAD_ROWS + 1)
        upload_was_limited = len(raw_df) > MAX_UPLOAD_ROWS
        if upload_was_limited:
            raw_df = raw_df.head(MAX_UPLOAD_ROWS).copy()
            st.warning(
                f"This file exceeds the {MAX_UPLOAD_ROWS:,}-row MVP2 limit. "
                f"Only the first {MAX_UPLOAD_ROWS:,} rows were loaded."
            )
        privacy_findings = detect_sensitive_columns(raw_df)
        df = mask_sensitive_data(
            raw_df,
            privacy_findings,
            st.session_state.privacy_salt,
        )
        del raw_df
        st.session_state.privacy_findings = privacy_findings
        st.session_state["df"] = df
        st.session_state.data_summary = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "sample_data": df.head().to_dict(),
        "summary_stats": df.describe().to_dict()
        }
        uploaded_file_signature = (uploaded_file.name, uploaded_file.size)
        if st.session_state.uploaded_file_signature != uploaded_file_signature:
            st.toast(
                f"{uploaded_file.name} loaded: {df.shape[0]} rows x {df.shape[1]} columns"
            )
            st.session_state.uploaded_file_signature = uploaded_file_signature
        if privacy_findings:
            pii_columns = [
                column
                for column, details in privacy_findings.items()
                if details["category"] == "PII"
            ]
            psi_columns = [
                column
                for column, details in privacy_findings.items()
                if details["category"] == "PSI"
            ]
            analysis_columns = [
                str(column) for column in df.columns if str(column) not in privacy_findings
            ]
            privacy_message = [
                "Personal or sensitive information was detected and masked before "
                "the data was made available to the AI."
            ]
            if pii_columns:
                privacy_message.append(
                    f"Personal information (PII): {', '.join(pii_columns)}."
                )
            if psi_columns:
                privacy_message.append(
                    f"Sensitive personal information (SPI): {', '.join(psi_columns)}."
                )
            privacy_message.append(
                f"The remaining {len(analysis_columns)} non-sensitive column(s) retain "
                "their original analytical values and can be used normally. Protected "
                "columns can still support anonymous counts and grouping."
            )
            privacy_alert_placeholder.error("\n\n".join(privacy_message))
        else:
            privacy_alert_placeholder.success(
                "Privacy scan complete: no likely PII or PSI columns were detected. "
                "All columns remain available for analysis."
            )

        with data_summary_tab:
            st.subheader("Data Preview")
            preview_df = df.drop(columns=list(privacy_findings), errors="ignore")
            if privacy_findings:
                st.caption(
                    f"{len(privacy_findings)} protected PII/PSI column(s) are hidden "
                    "from this preview to reduce clutter."
                )
            if preview_df.empty:
                st.info("All uploaded columns were classified as protected.")
            else:
                st.dataframe(preview_df.head(10), use_container_width=True)

            st.divider()
            with st.expander("Privacy Protection", expanded=bool(privacy_findings)):
                if privacy_findings:
                    privacy_rows = [
                        {
                            "Column": column,
                            "Type": details["category"],
                            "Detected by": details["reason"],
                        }
                        for column, details in privacy_findings.items()
                    ]
                    st.dataframe(pd.DataFrame(privacy_rows), use_container_width=True, hide_index=True)
                    st.caption(
                        "Masked tokens preserve repeated-value groupings but not the original values. "
                        "Analysis of protected columns is limited to anonymized counts and patterns."
                    )
                else:
                    st.caption("No likely PII or PSI columns were detected.")

            st.subheader("Dataset Overview")
            st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB")
            st.metric("Rows", len(df))
            st.metric("Columns", len(df.columns))

            st.divider()
            st.subheader("Data Quality")
            null_summary = (
                df.isnull()
                .sum()
                .reset_index()
                .rename(columns={"index": "Column", 0: "Missing Values"})
            )
            null_summary["Missing %"] = 0 if len(df) == 0 else (null_summary["Missing Values"] / len(df) * 100).round(2)
            st.dataframe(null_summary, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("Numeric Statistics")
            numeric_df = df.select_dtypes(include="number")
            if numeric_df.empty:
                st.caption("No numeric columns found.")
            else:
                numeric_summary = numeric_df.describe().T[["min", "max", "mean", "50%"]].rename(
                    columns={"min": "Min", "max": "Max", "mean": "Mean", "50%": "Median"}
                )
                st.dataframe(numeric_summary.round(2), use_container_width=True)
                    
                
            #st.markdown("Count Columns: " + str(len(df.columns)))
            #st.markdown("Count Rows: " + str(len(df)))
            
            #st.markdown("Show Max Values:" + str(df.max(numeric_only=True)))
            #st.markdown("Show Min Values:" + str(df.min(numeric_only=True)))
            #st.markdown("Show Mean Values:" + str(df.mean(numeric_only=True)))
            # #st.markdown("Show Null Values per Column:" + str(df.isnull().sum()) + "\n")
        
        
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        st.info("Please ensure the file is a valid CSV format.")
else:
    with data_summary_tab:
        st.info("Upload a CSV to view its preview, quality, statistics, and privacy summary.")

with insights_tab:
    # Main chat state
    if st.session_state["df"] is not None:
        for msg in st.session_state['messages']:
            render_saved_message(msg)

        if st.session_state.pending_pdf_export:
            pending_export = st.session_state.pending_pdf_export
            st.warning(
                "PDF export requires your approval. The report service will receive only "
                "the questions, stakeholder interpretations, generated charts, capped result "
                "tables, and business context from this session. It will not receive the uploaded CSV."
            )
            st.caption(
                f"Report: {pending_export['title']} | Focus: {pending_export['focus']} | "
                f"Service: {PDF_MCP_URL}"
            )
            approve_column, cancel_column = st.columns(2)
            if approve_column.button("Approve PDF export", type="primary"):
                report_payload = build_report_payload(
                    st.session_state.messages,
                    pending_export["title"],
                    pending_export["focus"],
                    selected_industry,
                    business_goal.strip(),
                    st.session_state.privacy_findings,
                    {
                        "model": OPENAI_MODEL,
                        "request_limit": MAX_REQUESTS_PER_SESSION,
                        "requests_used": st.session_state.request_count,
                        "requests_remaining": max(
                            0,
                            MAX_REQUESTS_PER_SESSION - st.session_state.request_count,
                        ),
                        "input_tokens": st.session_state.input_tokens_used,
                        "output_tokens": st.session_state.output_tokens_used,
                        "total_tokens": (
                            st.session_state.input_tokens_used
                            + st.session_state.output_tokens_used
                        ),
                        "estimated_cost_usd": estimate_cost(
                            OPENAI_MODEL,
                            st.session_state.input_tokens_used,
                            st.session_state.output_tokens_used,
                        ),
                    },
                    {
                        "rows": len(st.session_state.df),
                        "columns": len(st.session_state.df.columns),
                        "memory_mb": round(
                            st.session_state.df.memory_usage(deep=True).sum()
                            / (1024 * 1024),
                            2,
                        ),
                        "protected_columns": len(st.session_state.privacy_findings),
                        "analysis_columns": (
                            len(st.session_state.df.columns)
                            - len(st.session_state.privacy_findings)
                        ),
                        "findings": [
                            {
                                "column": str(column),
                                "type": (
                                    "SPI"
                                    if details["category"] == "PSI"
                                    else details["category"]
                                ),
                                "detected_by": details["reason"],
                            }
                            for column, details in st.session_state.privacy_findings.items()
                        ],
                    },
                )
                try:
                    with st.spinner("Building the stakeholder report..."):
                        st.session_state.pdf_export = asyncio.run(
                            request_pdf_report(PDF_MCP_URL, report_payload)
                        )
                    st.session_state.pending_pdf_export = None
                    st.rerun()
                except Exception as error:
                    st.error(f"PDF report service error: {error}")
                    st.info(
                        "Confirm the Streamable HTTP PDF service is running and PDF_MCP_URL "
                        "points to its /mcp endpoint."
                    )
            if cancel_column.button("Cancel export"):
                st.session_state.pending_pdf_export = None
                st.rerun()

        if st.session_state.pdf_export:
            pdf_export = st.session_state.pdf_export
            st.download_button(
                "Download PDF report",
                data=pdf_export["pdf_bytes"],
                file_name=pdf_export["filename"],
                mime=pdf_export["mime_type"],
                type="primary",
            )
            
        #chat input box
        request_limit_reached = st.session_state.request_count >= MAX_REQUESTS_PER_SESSION
        if request_limit_reached:
            st.warning("This session has reached its request limit.")
        user_input = st.chat_input(
            "Ask me anything about your CSV data...",
            disabled=request_limit_reached,
        )
    
    
        if user_input:
            protected_user_input = mask_sensitive_text(
                user_input,
                st.session_state.privacy_salt,
            )
            st.session_state.messages.append({"role": "user", "content": protected_user_input})
        
            with st.chat_message("user"):
                st.markdown(protected_user_input)
            
            df = st.session_state.df
        
            data_context = build_data_context(df)
            privacy_context = (
                ", ".join(
                    f"{column} ({details['category']})"
                    for column, details in st.session_state.privacy_findings.items()
                )
                or "No likely PII or PSI columns were detected."
            )

            industry_context = selected_industry
            if selected_industry == "Auto-detect from data":
                industry_context = "Auto-detect the most likely industry from the dataset columns, values, and user question."
            business_context = business_goal.strip() or "No explicit business goal or audience was provided. Infer the most useful stakeholder lens from the dataset and question."
            
            system_prompt = f"""
                You are a senior data analyst who turns raw data into clear, decision-ready
                insight for non-technical business stakeholders. You have access to a pandas
                dataframe called `df`.

                # CONTEXT
                Dataset: {data_context}
                Industry: {industry_context}
                Business goal / audience: {business_context}
                Privacy-protected columns: {privacy_context}

                Values in privacy-protected columns have already been replaced with
                irreversible, session-scoped tokens. Never attempt to identify, reconstruct,
                or request the original values. Treat tokenized values only as anonymous
                group labels and clearly state when masking limits an interpretation.

                If industry or goal were inferred rather than stated, mention the assumption
                briefly, but only when it changes how a result should be read.

                # WHAT THE USER SEES — this is the entire point, get this right
                Every answer is written for someone who will make a decision from it, not run
                the analysis themselves. Structure substantive answers as:

                1. Key Finding — the one or two numbers/trends that matter, in plain language.
                2. Chart — when a chart adds clarity beyond the numbers (see Chart Rules).
                3. What it means — interpret the chart/number: what changed, how much,
                compared to what, why it's likely happening, and why a stakeholder in this
                industry should care. Never show a chart without saying what to look at
                and what to conclude from it.
                4. Recommended next step — a concrete action or a specific follow-up
                question/analysis, tied to the stated business goal.
                5. Caveats — only if something limits confidence (small sample, nulls,
                outliers, seasonality, correlation vs. causation).

                Skip sections that don't apply. A simple factual question ("what's the
                average order value?") gets a direct answer, not the full template. Match
                depth to the question.

                No jargon without a one-line plain-English explanation. No code, library, or
                function names in the user-facing text — describe results and implications
                only.

                # CHART RULES
                Generate a chart whenever it reveals something a number alone can't (a trend,
                a comparison, a distribution, an outlier). Don't chart single values or
                trivial comparisons.
                - One figure per response. If multiple charts are needed, use subplots
                (plt.subplots) inside that single figure, sized and styled consistently —
                never separate figures.
                - Every chart needs a title that states the insight, not just the variable
                (e.g. "Revenue dipped 18% in March" beats "Revenue by Month"), axis labels
                with units (e.g. "Revenue ($ in thousands )", "Percentage (%)" ), and a legend
                if there's more than one series placed at a clean and clear section of the chart not in front of other chart elements.
                - Highlight what matters directly on the chart where practical: annotate the
                peak, the outlier, or the inflection point rather than leaving the reader
                to spot it.
                - Use color with intent — one accent color for the point of interest, muted
                tones elsewhere — instead of default palettes.
                - figsize sized for readability (e.g. (10,6) for multi-panel), and always
                plt.tight_layout() before plt.show().
                - Put chart code only in fenced ```python code blocks — the app hides these
                and shows only the rendered chart. Never describe or narrate the code
                itself in the response text.

                # TABLE / LIST RULES
                When a user asks for a list, table, rows, or records, do not answer only in
                prose. Produce a filtered pandas DataFrame and display it in an executable
                Python code block using `st.dataframe(result_df, use_container_width=True)`.
                - Keep only the relevant columns and sort by the most important metric.
                - Show only the rows requested. Use `.head(10)` for top/first rows and
                `.tail(10)` for last/bottom rows. Never display more than 10 rows.
                - If the user asks for more than 10 rows or asks for all rows, show the most
                relevant 10 rows and explain that the table is capped for readability.
                - If a request is basically a find-records question, the table is the answer.
                - Example pattern: `result_df = df[df["Income"] > 50000].sort_values("Income", ascending=False)[["ID", "Name", "Income", "Credit Score"]].head(10); st.dataframe(result_df, use_container_width=True)`

                # ANALYTICAL STANDARDS — do this silently, don't narrate the process
                - Before analyzing, check relevant columns for nulls, wrong dtypes, or other
                data issues. If an issue would materially affect the answer, say so briefly
                in Caveats and adjust the analysis (e.g. exclude nulls) rather than failing
                silently.
                - For exact comparisons, rankings, grouped totals, filtered rows, or charts,
                use pandas code against the full `df`. Do not rely only on the sample rows in
                the prompt for the final answer.
                - If the question can't be answered with the available data, say why in
                plain language and suggest the next-best question or what data would be
                needed — don't just error out.
                - Treat every column name as a business concept: infer its likely
                definition, purpose, data type, and unit, and track your confidence
                internally. Only surface these definitions if the user explicitly asks
                what a column means.
                - Ground every interpretation in the stated industry and business goal — the
                same trend can be good or bad news depending on context, so make the
                business meaning explicit rather than assuming it's obvious.

                # CODE ENVIRONMENT
                pandas as pd, numpy as np, matplotlib.pyplot as plt, and seaborn as sns are
                already imported. `df` is already loaded. Write correct, runnable code, and
                always end plots with plt.show().

                # PDF EXPORT TOOL
                If the user explicitly asks to create, export, or download a PDF report,
                call request_pdf_report with a concise title and business focus. Do not
                claim the report was generated. The application will ask the user for
                approval before sending sanitized session outputs to the report service.
                """
        
            #Generate response from OpenAI
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("Analyzing data and generating response..."):
                    try:
                        if provider_name != "OpenAI":
                            raise ValueError(f"Provider '{provider_name}' is not supported yet.")

                        if credential_source == "Use my own key":
                            api_key = user_api_key.strip()
                        else:
                            api_key = st.secrets.get("OpenAI_API_Key", "").strip()

                        if not api_key:
                            raise ValueError(
                                "No OpenAI API key is available. Add the app key to Streamlit secrets "
                                "or choose 'Use my own key'."
                            )

                        chat_history = [
                            {"role": msg["role"], "content": msg["content"]}
                            for msg in st.session_state.messages
                            if msg.get("content")
                        ]
                        request_messages = [
                            {"role": "system", "content": system_prompt},
                            *chat_history,
                        ]
                        estimated_input_tokens = estimate_tokens(
                            "\n".join(message["content"] for message in request_messages)
                        )
                        estimated_max_cost = estimate_cost(
                            OPENAI_MODEL,
                            estimated_input_tokens,
                            selected_output_tokens,
                        )
                        estimate_text = (
                            f"Estimated request size: about {estimated_input_tokens:,} input tokens "
                            f"and up to {selected_output_tokens:,} output tokens"
                        )
                        if estimated_max_cost is not None:
                            estimate_text += f" (up to approximately ${estimated_max_cost:.4f})"
                        st.caption(estimate_text + ". Actual usage may differ.")

                        provider = OpenAIProvider(api_key=api_key, model=OPENAI_MODEL)
                        response = provider.generate(
                            messages=request_messages,
                            max_output_tokens=selected_output_tokens,
                            tools=[PDF_EXPORT_TOOL],
                        )
                        st.session_state.request_count += 1
                        record_response_usage(response)
                        response_message = response.choices[0].message
                        tool_calls = getattr(response_message, "tool_calls", None) or []
                        if tool_calls:
                            pdf_call = next(
                                (
                                    tool_call
                                    for tool_call in tool_calls
                                    if tool_call.function.name == "request_pdf_report"
                                ),
                                None,
                            )
                            if pdf_call:
                                arguments = json.loads(pdf_call.function.arguments)
                                st.session_state.pending_pdf_export = {
                                    "title": arguments.get("title", "Business Analysis Report"),
                                    "focus": arguments.get(
                                        "focus",
                                        business_goal.strip() or "Business optimization and decision support",
                                    ),
                                }
                                st.session_state.messages.append(
                                    {
                                        "role": "assistant",
                                        "content": (
                                            "The PDF report is ready for your approval. Review the "
                                            "export details before the report service is called."
                                        ),
                                        "images": [],
                                        "notes": [],
                                        "tables": [],
                                    }
                                )
                                st.rerun()

                        reply = response_message.content or "I could not produce an analysis response."
                        display_reply = hide_python_code_blocks(reply)
                        message_placeholder.markdown(display_reply)
                        assistant_message = {"role": "assistant", "content": display_reply, "images": [], "notes": [], "tables": []}
                    
                        #We need to execute any code blocks in the reply for visualizations
                        code_blocks = extract_python_code_blocks(reply)
                        if code_blocks:
                            displayed_table_ids = set()
                            chart_metadata = []
                            generated_st = GeneratedCodeStreamlitProxy(assistant_message, protected_user_input, displayed_table_ids)
                            exec_globals = {
                                "df": df,
                                "pd": pd,
                                "np": np,
                                "plt": plt,
                                "sns": sns,
                                "st": generated_st
                                }
                        
                            for code in code_blocks:
                                try:
                                    with warnings.catch_warnings(record=True) as w:
                                        warnings.simplefilter("always")
                                        exec(code.strip(), {}, exec_globals)
                                
                                    if w:
                                        for warning in w:
                                            note = f"Note:{warning.message}"
                                            st.info(note)
                                            assistant_message["notes"].append(note)

                                    for key, value in exec_globals.items():
                                        if key in {"df", "pd", "np", "plt", "sns", "st"}:
                                            continue
                                        if id(value) in displayed_table_ids:
                                            continue
                                        display_generated_table(value, assistant_message, protected_user_input, displayed_table_ids)
                                    
                                    #display any generated plots
                                    for fig_num in plt.get_fignums():
                                        fig = plt.figure(fig_num)
                                        if fig.get_axes():
                                            for axis in fig.get_axes():
                                                chart_metadata.append(
                                                    "Chart metadata: "
                                                    f"title={axis.get_title()!r}, "
                                                    f"x_axis={axis.get_xlabel()!r}, "
                                                    f"y_axis={axis.get_ylabel()!r}"
                                                )
                                            image_buffer = io.BytesIO()
                                            fig.savefig(image_buffer, format="png", bbox_inches="tight")
                                            image_buffer.seek(0)
                                            image_bytes = image_buffer.getvalue()
                                            st.image(image_bytes, use_column_width=True)
                                            assistant_message["images"].append(image_bytes)
                                        plt.close(fig)  # Close the figure to free up memory
                                
                                except Exception as e:
                                    error_type = type(e).__name__
                                    error_note = f"Error executing generated code ({error_type}): {e}"
                                    st.error(error_note)
                                    assistant_message["notes"].append(error_note)
                                
                                    if "NameError" in str(e):
                                        hint = "This might mean a column name is misspelled or doesn't exist."
                                    elif "TypeError" in str(e):
                                        hint = "This often happens when trying to plot non-numeric data."
                                    elif "KeyError" in str(e):
                                        hint = "The specified column might not exist in the dataset."
                                    elif "palette dictionary is missing keys" in str(e):
                                        hint = "This usually happens when a chart uses a palette dict with category values like 0/1 while the data is stored as strings. Use a simple color palette or convert the hue values consistently before plotting."
                                    else:
                                        hint = "Try rephrasing your question or check your data format."
                                    st.info(hint)
                                    assistant_message["notes"].append(hint)
                                    
                                    st.info("There was an error executing the hidden analysis code.")
                                finally:
                                    plt.close("all")

                            execution_evidence = build_execution_evidence(
                                exec_globals,
                                assistant_message,
                                chart_metadata,
                            )
                            if execution_evidence:
                                interpretation_response = provider.generate(
                                    messages=[
                                        {
                                            "role": "system",
                                            "content": (
                                                "You are writing the final interpretation for a business "
                                                "analysis report. Use only the executed evidence supplied. "
                                                "Write two or three direct paragraphs for non-technical "
                                                "stakeholders: answer the question, explain the chart or "
                                                "result in industry context, then recommend a concrete "
                                                "business optimization or solution direction. State a short "
                                                "caveat when the evidence does not support causation or a "
                                                "confident conclusion. Do not mention code or libraries."
                                            ),
                                        },
                                        {
                                            "role": "user",
                                            "content": (
                                                f"Question: {protected_user_input}\n"
                                                f"Industry: {industry_context}\n"
                                                f"Business goal: {business_context}\n\n"
                                                f"Executed evidence:\n{execution_evidence}"
                                            ),
                                        },
                                    ],
                                    max_output_tokens=selected_output_tokens,
                                )
                                record_response_usage(interpretation_response)
                                grounded_interpretation = (
                                    interpretation_response.choices[0].message.content or display_reply
                                )
                                assistant_message["content"] = grounded_interpretation
                                assistant_message["report_interpretation"] = grounded_interpretation
                                message_placeholder.markdown(grounded_interpretation)
                            else:
                                assistant_message["report_interpretation"] = display_reply
                        else:
                            assistant_message["report_interpretation"] = display_reply
                    
                        st.session_state.messages.append(assistant_message)
                        st.rerun()
                    except openai.APIConnectionError as e:
                        st.error("OpenAI API connection failed before the request reached OpenAI.")
                        st.info(
                            "If this app is running locally, restart Streamlit from a normal terminal "
                            "with outbound HTTPS access. Otherwise, check the host's proxy, SSL "
                            "certificates, DNS, and firewall rules. Your API key and usage limits "
                            "were not validated by this failed request."
                        )
                    except openai.AuthenticationError as e:
                        st.error(f"OpenAI authentication failed: {e}")
                        st.info("Check that the selected API key is active and belongs to the intended OpenAI project.")
                    except openai.RateLimitError as e:
                        st.error(f"OpenAI usage or rate limit reached: {e}")
                        st.info("Wait before retrying, or review the project's rate limits, credits, and spend limits.")
                    except openai.PermissionDeniedError as e:
                        st.error(f"OpenAI permission error: {e}")
                        st.info("Confirm that this API key and project have access to the configured model.")
                    except openai.OpenAIError as e:
                        st.error(f"OpenAI API Error: {e}")
                        st.info("Review the error details and try again.")
                    except Exception as e:
                        st.error(f"Error generating response: {e}")
                        #st.info("Please check your OpenAI API key and usage limits.")
                        st.info("I'm sorry, I couldn't generate a response at this time.")
                        #response_content = "I'm sorry, I couldn't generate a response at this time."
    else:
    
        col1,col2,col3=st.columns([1,2,1])
        with col2:
            st.info("Please upload a CSV file to start asking questions...")
        
            st.markdown("""
            ### Example Questions:
            - What is the average value of a specific column?
            - How many rows are in the dataset?
            - Which column has the highest maximum value?
            - Show me the distribution of values in a specific column.
            - Show me the bar chart of the top 10 values in a specific column.
            - Show me the correlation between two columns.
            - What are the null values in each column?
            """)
        
