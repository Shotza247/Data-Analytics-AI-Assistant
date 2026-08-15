# CSV Data Analytics AI Assistant

A Streamlit app for exploring CSV files with natural-language questions, automatic data summaries, and AI-generated analysis or visualizations.

## What It Does

- Upload a CSV file from the sidebar.
- Preview the first rows of the dataset.
- Review dataset dimensions, memory usage, null counts, and numeric summary statistics.
- Ask questions about the data in a chat interface.
- Generate pandas, Matplotlib, and Seaborn analysis code from the AI response.
- Display generated charts directly in the Streamlit app.
- Retain assistant replies, notes, and generated chart images in the session chat history.

## Tech Stack

- [Streamlit](https://streamlit.io/) for the web app
- [pandas](https://pandas.pydata.org/) for data loading and analysis
- [OpenAI Python SDK](https://github.com/openai/openai-python) for AI responses
- [Matplotlib](https://matplotlib.org/) and [Seaborn](https://seaborn.pydata.org/) for visualizations

## Project Structure

```text
.
+-- app.py
+-- sample_data.csv
+-- .streamlit/
|   +-- secrets.toml
+-- .gitignore
+-- README.md
```

`sample_data.csv` contains 60 example e-commerce orders across customer regions, product categories, payment methods, quantities, unit prices, and total order amounts.

## Getting Started

### Prerequisites

- Python 3.10 or newer
- An OpenAI API key
- pip

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd Streamlit-Data-Analytics-AI-Assistant-1
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

   On macOS or Linux:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install streamlit pandas openai matplotlib seaborn
   ```

4. Add your OpenAI API key to `.streamlit/secrets.toml`:

   ```toml
   OpenAI_API_Key = "your-api-key-here"
   OpenAI_Model = "gpt-4o"
   ```

5. Run the app:

   ```bash
   streamlit run app.py
   ```

6. Open the local Streamlit URL shown in your terminal, usually:

   ```text
   http://localhost:8501
   ```

## Usage

1. Upload a CSV file in the sidebar.
2. Expand **Preview Data** to inspect the first 10 rows.
3. Expand **Data Summary** in the sidebar to review dataset metadata and numeric statistics.
4. Ask questions in the chat box.

Example questions:

- What is the average total amount?
- Which product category has the highest revenue?
- Show sales by customer region.
- Create a bar chart of the top 10 products by total amount.
- What are the null values in each column?
- What is the correlation between quantity, unit price, and total amount?

## How The App Works

When a CSV is uploaded, `app.py` stores the dataframe and a compact data summary in Streamlit session state. For smaller datasets, the full dataframe is included in the prompt context. For datasets with more than 100 rows, the app sends a summarized context instead to reduce token usage.

The assistant response can include Python code blocks. When code is returned, the app extracts the generated code, executes it with access to `df`, `pd`, `plt`, `sns`, and `st`, then renders and saves any generated Matplotlib figures as chat images.

Assistant text, warning notes, and generated chart images are saved in Streamlit session state so they remain visible when the app reruns during the same session.

## Configuration

The OpenAI call is configured in `app.py`:

```python
response = client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ],
    temperature=0.1,
    max_completion_tokens=500
)
```

If your OpenAI project does not have access to the configured model, update `OpenAI_Model` in `.streamlit/secrets.toml` to a model available for your project.

## Security Notes

- Do not commit `.streamlit/secrets.toml`.
- Keep your OpenAI API key private.
- Review API usage to avoid unexpected costs.
- Be careful with untrusted prompts or files. The app executes Python code returned by the model, so only run it in an environment where you are comfortable testing generated code.

## Troubleshooting

- **Missing API key**: Confirm `.streamlit/secrets.toml` exists and contains `OpenAI_API_Key`.
- **CSV upload fails**: Check that the file is a valid CSV and uses a readable encoding.
- **OpenAI request fails**: Confirm your API key, model access, billing status, and network connection.
- **Generated chart fails**: Rephrase the question with exact column names from the uploaded CSV.
- **Large file responses are vague**: Ask more specific questions or filter the CSV before uploading.

## License

This project is available for personal and educational use.
