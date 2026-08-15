import streamlit as st
import pandas as pd
import openai
import io
import matplotlib
import re

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


def render_saved_message(msg):
    with st.chat_message(msg["role"]):
        if msg.get("content"):
            st.markdown(msg["content"])
        for note in msg.get("notes", []):
            st.info(note)
        for image in msg.get("images", []):
            st.image(image, use_column_width=True)


def extract_python_code_blocks(text):
    return [block.strip() for block in PYTHON_CODE_BLOCK_RE.findall(text)]


def hide_python_code_blocks(text):
    cleaned = PYTHON_CODE_BLOCK_RE.sub("\n\n", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned or "Here are the results from the analysis."


st.title("📊Ask about your CSV 🚀")
st.markdown('Upload your CSV file and ask questions about its content.')

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
            
        system_prompt = f"""You are a helpful expert data analyst AI assistant. Use the provided dataset information to answer user questions accurately and concisely.
        The user will ask questions about their CSV data. Use this dataset context {data_context} to provide precise answers.
        Business context: Industry = {industry_context}. Business goal or audience = {business_context}
        
        The data is loaded in a pandas dataframe called df. You can refer to columns by their names.
        
        Guidelines:
        1. Always refer to the dataset context when answering questions.
        2. Answer in plain language for non-technical business stakeholders. Avoid jargon unless you briefly explain it.
        3. Provide insight, not just numbers or charts. Explain what changed, what stands out, why it matters, and what decision or action it may support.
        4. Align the interpretation with the stated or inferred industry and business goal. If the industry is inferred, mention the assumption briefly when it affects the interpretation.
        5. When useful, structure the answer with short sections such as Key findings, Business meaning, Recommended next step, and Caveats.
        6. If the question requires analysis, describe the result and business implication rather than the technical steps.
        7. Write python code using pandas, matplotlib, or seaborn libraries to perform the analysis.
        8. For visualizations, describe what the chart means and the key takeaway a non-technical stakeholder should notice.
        When generating more than one chart, always use subplots within a single figure rather than separate figures, ensuring clarity, alignment, and consistent styling with clear titles, labels, and consistent formatting.
        Always use matplotlib "plt.figure()" or seaborn but before plotting and include plt.tight_layout() before plt.show() to ensure proper layout.
        9. Always validate data before operations (e.g., check for nulls, data types etc.).
        10. If you cannot answer due to data limitations, politely inform the user why and suggest the next best question or data needed.
        11. Keep the response primarily focused on the data, user question, business context, and decision relevance.
        12. In the background, treat each column name as a business concept/term. 
        Infer and validate its definition, business purpose, data type, and unit. 
        Record uncertainties and assumptions internally. 
        Only present column definitions if the user explicitly asks.
        
        When generating code, follow this format:
        - import statements are already done (pandas as pd, matplotlib.pyplot as plt, seaborn as sns)
        - The dataframe is already loaded as df
        - Always use plt.show() to display plots
        - Ensure code is syntactically correct and can run without errors
        - For plots, use plt.figure(figsize=(6,4)) before plotting and plt.tight_layout() before plt.show() for a better display layout.
        - Always add titles and labels to plots for clarity.
        - Do not show Python code as part of the user-facing explanation. Present the analysis, results, and interpretation in plain language first.
        - If code is needed to create charts, place it only in fenced python code blocks. The app will hide those code blocks and show only the results and charts.
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
                    assistant_message = {"role": "assistant", "content": display_reply, "images": [], "notes": []}
                    
                    #We need to execute any code blocks in the reply for visualizations
                    code_blocks = extract_python_code_blocks(reply)
                    if code_blocks:
                        exec_globals = {
                            "df": df,
                            "pd": pd, 
                            "plt": plt,
                            "sns": sns,
                            "st": st
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
        
