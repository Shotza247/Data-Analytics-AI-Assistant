import streamlit as st
import pandas as pd
import openai
import io
import matplotlib
import re
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

st.set_page_config(
    page_title="My CSV Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

#We will inistialize the OpenAI client using the API key
client = openai.OpenAI(api_key=st.secrets["OpenAI_API_Key"])
OPENAI_MODEL = st.secrets.get("OpenAI_Model", "gpt-4o")
PYTHON_CODE_BLOCK_RE = re.compile(r"```(?:python|py)\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)
TABLE_DISPLAY_ROW_LIMIT = 10
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


def requested_table_limit(user_query):
    match = ROW_LIMIT_RE.search(user_query or "")
    if not match:
        return TABLE_DISPLAY_ROW_LIMIT

    raw_limit = match.group(1).lower()
    requested_limit = int(raw_limit) if raw_limit.isdigit() else NUMBER_WORDS.get(raw_limit, TABLE_DISPLAY_ROW_LIMIT)
    return max(1, min(requested_limit, TABLE_DISPLAY_ROW_LIMIT))


def should_show_last_rows(user_query):
    return bool(LAST_ROWS_RE.search(user_query or ""))


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
    st.header("Upload your CSV file")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
    st.divider()
    st.subheader("Business Context")
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
    )
    business_goal = st.text_area(
        "Business goal or audience",
        placeholder="Example: Explain revenue drivers for store managers",
        height=90,
    )
    
if uploaded_file is not None: # move entire code inside the with block up
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state["df"] = df
        st.session_state.data_summary = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "sample_data": df.head().to_dict(),
        "summary_stats": df.describe().to_dict()
        }
        st.success(f"{uploaded_file.name} uploaded and data loaded successfully! {df.shape[0]} Rows x {df.shape[1]} Columns")
        
        with st.expander("Preview Data"):
            st.subheader("Data Preview" + ":" + uploaded_file.name)
            st.dataframe(df.head(10))
        
        with st.sidebar:
            with st.expander("Data Summary", expanded=True):
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
    st.info("Awaiting CSV file to be uploaded.")

#Main chat state
if st.session_state["df"] is not None:
    for msg in st.session_state['messages']:
        render_saved_message(msg)
            
    #chat input box
    user_input = st.chat_input("Ask me anything about your CSV data...")
    
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
            
        df = st.session_state.df
        
        if len(df) > 100:
            data_context = f"""
            Dataset shape: {st.session_state.data_summary['shape']}
            Column names: {', '.join(st.session_state.data_summary['columns'])}
            Data types: {st.session_state.data_summary['dtypes']} 
            Sample data: {st.session_state.data_summary['sample_data']}
            Summary statistics: {st.session_state.data_summary['summary_stats']}
            """
        else:
            data_context = f"""
            Full dataset: {df.to_string()}
            """

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
            """
        
        #Generate response from OpenAI
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Analyzing data and generating response..."):
                try:
                    chat_history = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in st.session_state.messages
                        if msg.get("content")
                    ]
                    response = client.chat.completions.create(
                        model=OPENAI_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *chat_history
                        ],
                        temperature=0.1, #0 more focused answers, 1->2 more creative/random
                        max_tokens=500
                    )
                    reply = response.choices[0].message.content
                    display_reply = hide_python_code_blocks(reply)
                    message_placeholder.markdown(display_reply)
                    assistant_message = {"role": "assistant", "content": display_reply, "images": [], "notes": [], "tables": []}
                    
                    #We need to execute any code blocks in the reply for visualizations
                    code_blocks = extract_python_code_blocks(reply)
                    if code_blocks:
                        displayed_table_ids = set()
                        generated_st = GeneratedCodeStreamlitProxy(assistant_message, user_input, displayed_table_ids)
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
                                    display_generated_table(value, assistant_message, user_input, displayed_table_ids)
                                    
                                #display any generated plots
                                for fig_num in plt.get_fignums():
                                    fig = plt.figure(fig_num)
                                    if fig.get_axes():
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
                    
                    st.session_state.messages.append(assistant_message)
                except openai.OpenAIError as e:
                    st.error(f"OpenAI API Error: {e}")
                    st.info("Please check your OpenAI API key and usage limits, and try again.")
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
        
