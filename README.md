# 📊 AI Data Analytics Assistant | Streamlit + OpenAI

Developed an end-to-end AI-powered analytics solution that transforms raw CSV data into actionable business insights through natural-language interaction. The application leverages OpenAI models to generate stakeholder-ready analyses, dynamic visualizations, filtered datasets, and data quality assessments, making advanced analytics accessible without requiring SQL or Python expertise.

- [GitHub Repository](https://github.com/Shotza247/Data-Analytics-AI-Assistant)

## MVP1 Status

This repository currently represents **MVP1** of the CSV Data Analytics AI Assistant. MVP1 focuses on a single-user Streamlit workflow for uploading one CSV, asking natural-language questions, receiving stakeholder-friendly business insights/results, viewing requested rows/tables, and viewing generated charts without exposing the Python code used behind the scenes.

## MVP2 In Progress

MVP2 development includes business-context guidance and provider and usage controls. OpenAI is available through either the app-owned key or a session-only user key, with request, output-token, upload-row, and context-row limits. Hugging Face and Claude remain planned provider adapters.

## MVP3 Foundation

Data masking is the first implemented MVP3 privacy enhancement. The app detects likely personally identifiable information (PII) and sensitive personal information (SPI/PSI), masks values before AI access, alerts the user about protected columns, and hides those columns from the preview. Masked identifiers remain available only for privacy-preserving operations such as anonymous counts, grouping, and duplicate-pattern analysis. Future MVP3 work can add configurable policies, role-based access, audit events, and organization-specific detection rules.

## What It Does

- Upload a CSV file from the sidebar.
- Preview the first rows of the dataset without clutter from detected PII/PSI columns.
- Review dataset dimensions, memory usage, data quality, numeric statistics, and privacy findings in the main **Data Summary** tab.
- Add business context, such as industry and audience, to make insights more relevant.
- Use the main **Insights** tab to configure business context and chat with the assistant.
- Ask questions about the data in a chat interface.
- Receive data analysis, result summaries, chart interpretation, business meaning, and recommended next steps in plain language.
- Display requested rows, records, filtered results, and table-style answers as Streamlit dataframes instead of prose-only responses, capped to the requested top/last rows with a maximum of 10 displayed rows.
- Generate charts directly in the Streamlit app without showing the underlying Python code.
- Retain assistant replies, notes, generated tables, and generated chart images in the session chat history.
- Control API usage with per-session request limits, response-token caps, CSV/context row limits, and token/cost estimates.
- Use the app's OpenAI key or provide a personal OpenAI key that remains in Streamlit session state and is not written to disk.
- Detect likely PII and sensitive information in uploaded CSV columns, mask it before AI analysis, and alert the user about which columns were protected.

## Development Workflow

Upcoming enhancements will be planned, prioritized, and tracked in the repository's GitHub Project before implementation. Project items should identify the target milestone, expected user outcome, acceptance criteria, and relevant issue so product decisions and code changes remain synchronized.

## Showcase
- [Notion](https://app.notion.com/p/Data-Analysis-Assistant-3bedc859ce3d80b18e49ee2b80b6e99f?v=377dc859ce3d80c094c0000cfa1eba82&source=copy_link)
Add screenshots to `docs/showcase/` and replace the image filenames below with the final files.

| App UI | Graphs And Insights |
| --- | --- |
| <img src="./Sample_UI_Images/Insights_BackedBy_YourData.png" alt="Data Analysis Assistant interface showing CSV upload, sidebar summary, and chat workflow" width="100%"> | <img src="./Sample_UI_Images/DTI_Ratio_Vs_Mortgage_Approval.png" alt="Generated analysis output showing business insights, tables, and charts" width="100%"> |
| The assistant turns a natural-language mortgage-risk question into a stakeholder-ready response. It explains the key finding, why the result matters, recommended next steps, and caveats, while also showing a capped table of matching applicants so the user can inspect examples without being overwhelmed by the full dataset. | The scatter plot compares debt-to-income ratio against credit score by mortgage approval status. From an analysis perspective, it helps identify approved applicants above the high-DTI threshold and suggests that approval decisions may be influenced by compensating factors such as stronger credit scores, property value, or other borrower characteristics. |

## Tech Stack

- [Streamlit](https://streamlit.io/) for the web app
- [pandas](https://pandas.pydata.org/) for data loading and analysis
- [OpenAI Python SDK](https://github.com/openai/openai-python) for AI responses
- [Matplotlib](https://matplotlib.org/) and [Seaborn](https://seaborn.pydata.org/) for visualizations

## Project Structure

```text
.
+-- app.py
+-- privacy.py
+-- sample_data.csv
+-- tests/
|   +-- test_mvp2_controls.py
|   +-- test_privacy.py
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
   git clone https://github.com/Shotza247/Data-Analytics-AI-Assistant.git
   cd Data-Analytics-AI-Assistant
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
   pip install -r requirements.txt
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
2. Open the main **Data Summary** tab to inspect the first 10 rows of non-sensitive columns and review privacy findings, data quality, and numeric statistics.
3. Open the main **Insights** tab and expand **Business Context** when you need to set an industry, audience, or goal.
4. Review responses in the conversation area and continue with the chat input anchored beneath them.

Example questions:

- What is the average total amount?
- Which product category has the highest revenue?
- Show sales by customer region.
- Create a bar chart of the top 10 products by total amount.
- What are the null values in each column?
- Show the top 20 records where total amount is above 500.
- What is the correlation between quantity, unit price, and total amount?

## How The App Works

When a CSV is uploaded, the app scans column names and sampled values for likely personally identifiable information (PII) and sensitive personal information (PSI). Detected values are replaced with deterministic, session-scoped tokens before the dataframe is stored, summarized, or sent to the AI. The privacy alert names the protected columns without displaying their original values and confirms that the remaining non-sensitive columns retain their analytical values. Protected columns are hidden from the data preview to reduce clutter but can still be used for anonymous counts and grouping.

`app.py` stores only the privacy-protected dataframe and a compact data summary in Streamlit session state. For datasets with 100 rows or fewer, the full protected dataframe is included in the prompt context. Larger datasets use a compact structural sample and summaries to reduce token usage. Uploaded data is capped at 50,000 rows for the MVP2 workflow.

The assistant can return hidden Python code blocks for chart and table generation. The app extracts and executes those hidden blocks with access to `df`, `pd`, `np`, `plt`, `sns`, and `st`. For visual requests, it renders and saves generated Matplotlib figures as chat images. For list-style, row, record, or filtered-result requests, it renders pandas DataFrames with `st.dataframe(...)` and stores them in the chat history. Generated tables are capped to the requested top/last rows, with a maximum of 10 rows displayed, so large datasets do not flood the interface. The user-facing chat shows business-oriented analysis, results, notes, tables, and charts, not the Python code.

The main view separates dataset inspection from analysis. **Data Summary** contains the privacy-safe preview and dataset diagnostics. **Insights** places optional business context in a collapsible section, keeps responses in the central scrollable conversation area, and pins the chat input to the lower edge of the interface on a solid, high-contrast surface. The composer centers itself within the available workspace as the sidebar opens or closes, keeping it visible regardless of response, chart, or viewport size while still allowing chart explanations to be framed for the relevant industry, audience, and business goal.

Assistant text, warning notes, generated tables, and generated chart images are saved in Streamlit session state so they remain visible when the app reruns during the same session.

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
    max_tokens=selected_output_tokens
)
```

The sidebar exposes the active MVP2 usage controls: a maximum of 10 successful requests per session, a response-token cap of 500, a 50,000-row upload cap, a 100-row full-context cap, and a pre-request token/cost estimate. The displayed cost is an estimate based on the configured model and may differ from provider billing.

Users can choose **Use app key** or **Use my own key**. A user-owned key is held only in Streamlit session state for the active browser session. OpenAI is the first implemented provider; the provider class keeps Hugging Face and Claude integrations as future adapters without requiring LangChain.

If your OpenAI project does not have access to the configured model, update `OpenAI_Model` in `.streamlit/secrets.toml` to a model available for your project.

## Security Notes

- Do not commit `.streamlit/secrets.toml`.
- Keep your OpenAI API key private.
- Review the privacy alert after every upload. PII/PSI detection is heuristic and should support, not replace, an organization's privacy and compliance review.
- Original values from detected sensitive columns are discarded after masking and are not sent to the AI. Non-sensitive columns remain available for normal analysis.
- Review API usage to avoid unexpected costs.
- Treat the in-app token and cost figures as estimates, and enforce account-level budgets in the provider dashboard as the final spending control.
- Be careful with untrusted prompts or files. The app executes hidden Python code returned by the model for analysis and visualizations, so only run it in an environment where you are comfortable testing generated code.

## Troubleshooting

- **Missing API key**: Confirm `.streamlit/secrets.toml` exists and contains `OpenAI_API_Key`.
- **CSV upload fails**: Check that the file is a valid CSV and uses a readable encoding.
- **OpenAI request fails**: Confirm your API key, model access, billing status, and network connection.
- **Generated chart fails**: Rephrase the question with exact column names from the uploaded CSV.
- **Requested rows or lists do not appear**: Ask for a table, rows, records, or a filtered dataframe and include the relevant column names. The app displays at most 10 rows for generated result tables.
- **Large file responses are vague**: Ask more specific questions or filter the CSV before uploading.

## License

This project is available for personal and educational use.
