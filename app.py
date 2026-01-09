import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="My CSV Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

#Session State Initialization
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if "df" not in st.session_state:
    st.session_state["df"] = None
    
if "data_summary" not in st.session_state:
    st.session_state["data_summary"] = None

st.title("📊Ask about your CSV 🚀")
st.markdown('Upload your CSV file and ask questions about its content.')

with st.sidebar: #the 'with' creates a context where everything inside appears inside the side bar
    st.header("Upload your CSV file")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
    
if uploaded_file is not None: # move entire code inside the with block up
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state["df"] = df
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
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
    #chat input box
    user_input = st.chat_input("Ask me anything about your CSV data...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
    
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
        