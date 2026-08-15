import streamlit as st
import pandas as pd
import openai
import io
import matplotlib

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


st.title("📊Ask about your CSV 🚀")
st.markdown('Upload your CSV file and ask questions about its content.')

with st.sidebar: #the 'with' creates a context where everything inside appears inside the side bar
    st.header("Upload your CSV file")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
    
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
            with st.expander("Data Summary"):
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Memory Usage")
                    st.metric("memory Usage (MB): ", f"{df.memory_usage().sum()/1024:.2f} MB")
                    st.subheader("Data Dimensions Info")
                    st.metric("Count Columns: ", len(df.columns))
                    st.metric("Count Rows: ", len(df))
                    st.subheader("Null Values Info")
                    st.markdown("**Null Values per Column:**")
                    st.write(df.isnull().sum())
                with col2:
                    st.subheader("Statistical Summary")
                    st.markdown("**Max Values:**")
                    st.write(df.max(numeric_only=True))
                    st.markdown("**Min Values:**")
                    st.write(df.min(numeric_only=True))
                    st.markdown("**Mean Values:**")
                    st.write(df.mean(numeric_only=True))
                    st.markdown("**Median Values:**")
                    st.write(df.median(numeric_only=True))
                    
                
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
            
        system_prompt = f"""You are a helpful expert data analyst AI assistant. Use the provided dataset information to answer user questions accurately and concisely.
        The user will ask questions about their CSV data. Use this dataset context {data_context} to provide precise answers.
        
        The data is loaded in a pandas dataframe called df. You can refer to columns by their names.
        
        Guidelines:
        1. Always refer to the dataset context when answering questions.
        2. Answer the users questions accurately and concisely.
        If the question requires analysis, describe the steps you would take to analyze the data.
        3. Write python code using pandas, matplotlib, or seaborn libraries to perform the analysis.
        4. For visualizations, describe the type of chart/graph to use and the columns involved.
        When generating more than one chart, always use subplots within a single figure rather than separate figures, ensuring clarity, alignment, and consistent styling with clear titles, labels, and consistent formatting.
        Always use matplotlib "plt.figure()" or seaborn but before plotting and include plt.tight_layout() before plt.show() to ensure proper layout.
        5. Always validate data before operations (e.g., check for nulls, data types etc.).
        6. If you cannot answer due to data limitations, politely inform the user why.
        7. Keep the response primarily focused on the data and questions asked, do not deviate from this.
        8. In the background, treat each column name as a business concept/term. 
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
                    message_placeholder.markdown(reply)
                    assistant_message = {"role": "assistant", "content": reply, "images": [], "notes": []}
                    
                    #We need to execute any code blocks in the reply for visualizations
                    if "```python" in reply:
                        code_blocks = [
                            reply_block.split("```")[0]
                            for reply_block in reply.split("```python")[1:]
                        ]
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
                                    
                                st.code(code, language='python')
                                st.info("There was an error executing the above code block.")
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
        
