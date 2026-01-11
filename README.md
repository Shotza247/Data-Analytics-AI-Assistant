# 📊 CSV Data Analytics AI Assistant

A Streamlit-powered web application that leverages OpenAI's GPT-4 to provide intelligent data analysis and visualization capabilities for CSV files.

## Overview

This application allows users to:
- Upload CSV files and explore their data
- Ask natural language questions about their datasets
- Get AI-powered insights and analysis
- Generate visualizations automatically
- View comprehensive data summaries

## 🛠️ Technology Stack

- **Streamlit**: Interactive web framework for data apps
- **Pandas**: Data manipulation and analysis
- **OpenAI API**: GPT-4 for intelligent responses
- **Matplotlib & Seaborn**: Data visualization
- **Python 3.8+**: Core programming language

## 📁 Project Structure

```
.
├── app.py                 # Main Streamlit application
├── sample_data.csv        # Sample dataset for testing
├── .streamlit/
│   └── secrets.toml       # API keys and credentials (git-ignored)
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Build a Data Analytics AI Assistant"
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install streamlit pandas openai matplotlib seaborn
   ```

4. **Set up API credentials**
   - Create `.streamlit/secrets.toml` if it doesn't exist
   - Add your OpenAI API key:
     ```toml
     OpenAI_API_Key = "your-api-key-here"
     ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

The app will open in your default browser at `http://localhost:8501`

## 📖 Features & Usage

### 1. **File Upload** 🗂️
- Located in the left sidebar
- Supports CSV files
- Displays success message with row/column count
- Shows memory usage and data dimensions

### 2. **Data Preview** 
[**INSERT IMAGE HERE**: Screenshot showing the data preview section with the first 10 rows of the CSV displayed in a table format]

- Expandable section showing first 10 rows
- Helps verify data loaded correctly

### 3. **Data Summary Dashboard** 📊
[**INSERT IMAGE HERE**: Screenshot of the Data Summary sidebar showing memory usage, statistical summary (Max, Min, Mean, Median), and null values info]

Located in the left sidebar, includes:
- **Memory Usage**: Total RAM consumed by the dataset
- **Data Dimensions**: Number of columns and rows
- **Null Values**: Missing data per column
- **Statistical Summary**: 
  - Maximum values
  - Minimum values
  - Mean values
  - Median values

### 4. **Interactive Chat Interface** 
[**INSERT IMAGE HERE**: Screenshot of the main chat interface showing example user questions and AI responses with generated visualizations]

- Natural language question input
- Real-time AI-powered responses
- Chat history maintained in session state
- Automatic code execution for visualizations

### 5. **Intelligent Visualizations** 
[**INSERT IMAGE HERE**: Examples of generated charts (bar chart, distribution plot, correlation heatmap, etc.)]

The AI can generate:
- Bar charts
- Distribution plots
- Correlation heatmaps
- Line charts
- Box plots
- And more based on your questions

## 🔧 How It Works

### Data Processing Pipeline

```
User Input (CSV)
    ↓
Pandas reads CSV
    ↓
Data Summary Created
    ↓
User asks questions
    ↓
System Prompt + Data Context → GPT-4
    ↓
AI generates response + code
    ↓
Python code extracted and executed
    ↓
Visualizations displayed
    ↓
Response added to chat history
```

### Key Components

#### Session State Management
```python
st.session_state['messages']  # Chat history
st.session_state['df']        # Loaded dataframe
st.session_state['data_summary']  # Data statistics
```

#### System Prompt
The AI operates under a carefully crafted system prompt that:
- Focuses on accurate data analysis
- Enforces proper code generation practices
- Requires data validation
- Ensures visualizations have titles and labels
- Uses appropriate libraries (pandas, matplotlib, seaborn)

#### Code Execution
- Extracts Python code blocks from AI responses
- Executes code in a controlled environment
- Displays generated matplotlib figures
- Handles errors gracefully with user-friendly messages

## Example Questions

Try asking:
- "What is the average value of [column_name]?"
- "How many rows are in the dataset?"
- "Which column has the highest maximum value?"
- "Show me the distribution of values in [column_name]"
- "Create a bar chart of the top 10 values in [column_name]"
- "What is the correlation between [column1] and [column2]?"
- "What are the null values in each column?"
- "What are the top selling products by revenue?"

## ⚙️ Configuration

### Page Settings
Located at the top of `app.py`:
```python
st.set_page_config(
    page_title="My CSV Assistant",
    page_icon="📊",
    layout="wide",           # Wide layout for more space
    initial_sidebar_state="expanded"
)
```

### AI Model Parameters
In the chat response generation:
- **Model**: `gpt-4.1` (High accuracy)
- **Temperature**: `0.1` (Focused, consistent responses)
- **Max Tokens**: `500` (Concise answers)

Adjust these in app.py for different behavior.

## Security Notes

 **Important**: 
- Never commit `.streamlit/secrets.toml` to version control
- Keep API keys confidential
- Monitor your OpenAI API usage to control costs
- The `.gitignore` file already protects secrets.toml

## Error Handling

The application handles:
- Invalid CSV formats
- Missing or malformed data
- OpenAI API errors
- Code execution errors
- Network connectivity issues

Errors are displayed in red boxes with helpful guidance.

##  UI/UX Layout

```
┌─────────────────────────────────────────────┐
│             Ask about your CSV              │
├──────────────┬──────────────────────────────┤
│   SIDEBAR    │         MAIN AREA            │
│              │                              │
│    Upload    │  Preview Data (expandable)   │
│    CSV       │  [INSERT IMAGE SECTION 2]    │
│              │                              │
│    Data      │  Chat History                │
│    Summary   │  [INSERT IMAGE SECTION 4]    │
│  [INSERT IMG │                              │
│   SECTION 3] │     Chat Input Box           │
│              │                              │
│              │  Generated Visualizations    │
│              │  [INSERT IMAGE SECTION 5]    │
└──────────────┴──────────────────────────────┘
```

## Sample Data

The project includes `sample_data.csv` with e-commerce data:
- **Records**: 60 orders
- **Columns**: Order ID, Date, Region, Product Category, Product Name, Quantity, Unit Price, Total Amount, Payment Method
- **Categories**: Electronics, Fitness, Home Essentials
- **Regions**: Northeast, West, Midwest, South

Perfect for testing visualizations and analysis features!

## Performance Tips

1. **For large datasets (>100 rows)**:
   - App creates a summarized context instead of full data
   - Reduces token usage and API costs
   - Faster response times

2. **Optimize API costs**:
   - Adjust temperature to 0 for focused responses
   - Reduce max_tokens if responses are too long
   - Batch similar questions together

3. **Better visualizations**:
   - Ask specific questions about subsets of data
   - Request explicit chart types (bar, scatter, heatmap, etc.)
   - Always provide column names in your questions

## Future Enhancements

Potential features to add:
- [ ] Data export/download functionality
- [ ] Custom chart styling options
- [ ] Caching for repeated queries
- [ ] Support for multiple file formats (Excel, JSON, etc.)
- [ ] Advanced filtering and data cleaning tools
- [ ] Model selection (GPT-3.5, GPT-4, etc.)
- [ ] Cost tracking dashboard
- [ ] User authentication and usage analytics

## License

This project is open source and available for personal and educational use.

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the example questions
3. Verify your OpenAI API key is valid
4. Check internet connectivity
5. Be careful with the file size uploaded-> to avoid a data_summary 'shape' dtype error

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [OpenAI's GPT-4](https://openai.com/gpt-4)
- Data visualization with [Matplotlib](https://matplotlib.org/) and [Seaborn](https://seaborn.pydata.org/)

---

**Happy analyzing! 🚀📊**
