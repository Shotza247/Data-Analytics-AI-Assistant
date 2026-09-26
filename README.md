# 📊 AI Data Analytics Assistant | Streamlit + OpenAI


<img width="2164" height="727" alt="ChatGPT Image Sep 26, 2026, 11_46_20 AM" src="https://github.com/user-attachments/assets/ce14b073-6c0e-4c1c-8849-a4463da729e3" />


Developed an end-to-end AI-powered analytics solution that transforms raw CSV data into actionable business insights through natural-language interaction. The application leverages OpenAI models to generate stakeholder-ready analyses, dynamic visualizations, filtered datasets, and data quality assessments, making advanced analytics accessible without requiring SQL or Python expertise.

- [GitHub Repository](https://github.com/Shotza247/Data-Analytics-AI-Assistant)
- [Shared Mermaid Workspace](https://mermaid.ai/app/projects/8db0f199-c162-4402-91a8-260688637404/diagrams/9dac37a4-7600-4f7d-adb9-30b525224fe9/share/invite/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkb2N1bWVudElEIjoiOWRhYzM3YTQtNzYwMC00ZjdkLWFkYjktMzBiNTI1MjI0ZmU5IiwiYWNjZXNzIjoiVmlldyIsInB1cnBvc2UiOiJzaGFyZS1pbnZpdGUiLCJpYXQiOjE3OTAyNjg2MDAsImV4cCI6MTc5Mjg2MDYwMH0.Av27ixyr3Mc4fYug-xJz65GzdOVnEofPeb7nS4evt9A?entryPoint=share-modal)
- [Versioned MVP2 Architecture Diagrams](docs/mvp2-architecture.md)

## MVP1 Status

This repository currently represents **MVP1** of the CSV Data Analytics AI Assistant. MVP1 focuses on a single-user Streamlit workflow for uploading one CSV, asking natural-language questions, receiving stakeholder-friendly business insights/results, viewing requested rows/tables, and viewing generated charts without exposing the Python code used behind the scenes.

## MVP2 Closeout

MVP2 includes business-context guidance, usage controls, two-pass grounded interpretation, and approval-gated PDF reports for non-technical stakeholders. Conversation outputs remain only in Streamlit session state; persistent memory and external caching are not required. Hugging Face and Claude remain planned provider adapters. PPTX export is the remaining additional acceptance criterion.

## MVP3 Foundation

Data masking is the first implemented MVP3 privacy enhancement. The app detects likely personally identifiable information (PII) and sensitive personal information (SPI/PSI), masks values before AI access, alerts the user about protected columns, and hides those columns from the preview. Masked identifiers remain available only for privacy-preserving operations such as anonymous counts, grouping, and duplicate-pattern analysis. Future MVP3 work can add configurable policies, role-based access, audit events, and organization-specific detection rules.

## What It Does

- Upload a CSV file from the sidebar.
- Receive a short-lived toast when a newly selected CSV loads successfully.
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
- Detect likely PII and sensitive personal information in uploaded CSV columns, mask it before AI analysis, and show a persistent red sidebar alert naming the protected columns.
- Ask for explicit approval before sending sanitized session outputs to the PDF report service.
- Download a stakeholder-ready PDF containing questions, grounded interpretations, charts, capped result tables, caveats, and a session-usage summary.

## Development Workflow

Upcoming enhancements will be planned, prioritized, and tracked in the repository's GitHub Project before implementation. Project items should identify the target milestone, expected user outcome, acceptance criteria, and relevant issue so product decisions and code changes remain synchronized.

The versioned Mermaid source for the current MVP2 workflow is maintained in [docs/mvp2-architecture.md](docs/mvp2-architecture.md). The shared Mermaid workspace remains available for collaborative editing, while the repository copy preserves the reviewed architecture alongside the code.

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
- [fpdf2](https://py-pdf.github.io/fpdf2/) for PDF generation
- [Model Context Protocol](https://modelcontextprotocol.io/) Streamable HTTP for the deployable report tool

## Project Structure

```text
.
+-- app.py
+-- pdf_builder.py
+-- pdf_mcp_server.py
+-- pdf_tool_client.py
+-- privacy.py
+-- sample_data.csv
+-- tests/
|   +-- test_mvp2_controls.py
|   +-- test_pdf_builder.py
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
   PDF_MCP_URL = "http://localhost:8000/mcp"
   ```

5. Start the PDF tool service in a separate terminal:

   ```bash
   python pdf_mcp_server.py
   ```

   Local development uses `http://localhost:8000/mcp`. For online processing, deploy the service behind HTTPS and set `PDF_MCP_URL` to its `https://.../mcp` endpoint.

6. Run the app:

   ```bash
   streamlit run app.py
   ```

7. Open the local Streamlit URL shown in your terminal, usually:

   ```text
   http://localhost:8501
   ```

## Usage

1. Upload a CSV file in the sidebar.
2. Open the main **Data Summary** tab to inspect the first 10 rows of non-sensitive columns and review privacy findings, data quality, and numeric statistics.
3. Open the main **Insights** tab and expand **Business Context** when you need to set an industry, audience, or goal.
4. Review responses in the conversation area and continue with the chat input anchored beneath them.
5. Ask for a PDF report, review the disclosure, and approve the export before the report service is called.

## Interface Layout

### Sidebar

The sidebar is reserved for global controls. After an upload it shows the privacy alert above the file uploader, followed by the uploader, provider selection, API-key mode, response-token control, and session usage. The alert lists only protected column names and categories; it never displays original sensitive values.

### Data Summary

The **Data Summary** tab contains the first 10 preview rows, excluding detected PII/SPI columns. It also provides the privacy-protection breakdown, dataset dimensions, memory usage, missing-value analysis, and numeric statistics.

### Insights

The **Insights** tab contains a collapsed **Business Context** section for industry and audience or goal settings. Conversation history, generated tables, charts, and stakeholder-ready interpretations appear below it. The solid chat composer stays fixed at the bottom, centers within the available workspace when the sidebar opens or closes, and leaves enough page padding to avoid covering results.

Example questions:

- What is the average total amount?
- Which product category has the highest revenue?
- Show sales by customer region.
- Create a bar chart of the top 10 products by total amount.
- What are the null values in each column?
- Show the top 20 records where total amount is above 500.
- What is the correlation between quantity, unit price, and total amount?

## How The App Works

When a CSV is uploaded, the app scans column names and sampled values for likely personally identifiable information (PII) and sensitive personal information (SPI/PSI). Detected values are replaced with deterministic, session-scoped tokens before the dataframe is stored, summarized, or sent to the AI. A short-lived toast confirms a successful new upload. The persistent red sidebar alert names the protected columns without displaying their original values and confirms that the remaining non-sensitive columns retain their analytical values. Protected columns are hidden from the data preview to reduce clutter but can still be used for anonymous counts and grouping.

`app.py` stores only the privacy-protected dataframe and a compact data summary in Streamlit session state. For datasets with 100 rows or fewer, the full protected dataframe is included in the prompt context. Larger datasets use a compact structural sample and summaries to reduce token usage. Uploaded data is capped at 50,000 rows for the MVP2 workflow.

The assistant can return hidden Python code blocks for chart and table generation. The app extracts and executes those hidden blocks with access to `df`, `pd`, `np`, `plt`, `sns`, and `st`. For visual requests, it renders and saves generated Matplotlib figures as chat images. For list-style, row, record, or filtered-result requests, it renders pandas DataFrames with `st.dataframe(...)` and stores them in the chat history. Generated tables are capped to the requested top/last rows, with a maximum of 10 rows displayed, so large datasets do not flood the interface. The user-facing chat shows business-oriented analysis, results, notes, tables, and charts, not the Python code.

The main view separates dataset inspection from analysis. **Data Summary** contains the privacy-safe preview and dataset diagnostics. **Insights** places optional business context in a collapsible section, keeps responses in the central scrollable conversation area, and pins the chat input to the lower edge of the interface on a solid, high-contrast surface. The composer centers itself within the available workspace as the sidebar opens or closes, keeping it visible regardless of response, chart, or viewport size while still allowing chart explanations to be framed for the relevant industry, audience, and business goal.

Assistant text, warning notes, generated tables, and generated chart images are saved in Streamlit session state so they remain visible when the app reruns during the same session. MVP2 does not persist chat memory or analysis data outside that session.

### Grounded Interpretation And PDF Export

After hidden analysis code runs, the app performs a second interpretation pass using only executed tables, scalar results, and chart metadata. It produces a concise explanation that answers the question, connects the evidence to the selected industry and business goal, and recommends a practical optimization direction without exposing code.

When a user asks for a PDF, the model calls a typed `request_pdf_report` function with a title and business focus. The app displays an approval prompt before contacting the PDF MCP service. Approval sends only session questions, grounded interpretations, generated chart images, capped result tables, caveats, business context, aggregate session usage, and privacy-scan metadata. The report opens with structured **Report Overview**, **Privacy Protection**, and **Session Usage** sections. Privacy metadata includes dataset dimensions, protected and analytical column counts, detected PII/SPI column names, categories, and detection methods, but never original sensitive values. The usage section reports requests used and remaining, input and output tokens, total tokens, and an estimated cumulative token cost for the configured model. The uploaded CSV is never sent to the PDF service, and protected columns are removed from analysis result tables. The service returns the PDF over MCP Streamable HTTP for download in Streamlit.

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

The sidebar exposes the active MVP2 usage controls: requests used and remaining from a maximum of 10 successful requests per session, separate input and output token totals, combined tokens, cumulative estimated cost, a response-token cap of 500, a 50,000-row upload cap, a 100-row full-context cap, and a pre-request token/cost estimate. Displayed costs are estimates based on the configured model and may differ from provider billing.

The exported PDF takes a session usage snapshot at approval time. Request usage reflects user-triggered analysis requests. Input and output token totals include every OpenAI response recorded by the app, including the grounded interpretation pass. The cumulative cost remains an estimate and is shown only when pricing is configured for the selected model.

Users can choose **Use app key** or **Use my own key**. A user-owned key is held only in Streamlit session state for the active browser session. OpenAI is the first implemented provider; the provider class keeps Hugging Face and Claude integrations as future adapters without requiring LangChain.

If your OpenAI project does not have access to the configured model, update `OpenAI_Model` in `.streamlit/secrets.toml` to a model available for your project.

## Security Notes

- Do not commit `.streamlit/secrets.toml`.
- Keep your OpenAI API key private.
- Review the privacy alert after every upload. PII/SPI detection is heuristic and should support, not replace, an organization's privacy and compliance review.
- Original values from detected sensitive columns are discarded after masking and are not sent to the AI. Non-sensitive columns remain available for normal analysis.
- PDF export is opt-in. Review the approval disclosure before sending sanitized outputs to the configured report endpoint.
- Protect a deployed MCP endpoint with HTTPS, authentication, request-size limits, and service monitoring. Do not expose the local development endpoint publicly.
- Review API usage to avoid unexpected costs.
- Treat the in-app token and cost figures as estimates, and enforce account-level budgets in the provider dashboard as the final spending control.
- Be careful with untrusted prompts or files. The app executes hidden Python code returned by the model for analysis and visualizations, so only run it in an environment where you are comfortable testing generated code.

## Troubleshooting

- **Missing API key**: Confirm `.streamlit/secrets.toml` exists and contains `OpenAI_API_Key`.
- **CSV upload fails**: Check that the file is a valid CSV and uses a readable encoding.
- **OpenAI connection fails before reaching OpenAI**: The Streamlit host cannot open outbound HTTPS connections. Stop that server and launch `streamlit run app.py` from a normal network-enabled terminal. An unauthenticated request to `https://api.openai.com/v1/models` should return HTTP `401`; that response confirms DNS, TLS, and routing work without exposing an API key.
- **OpenAI authentication, permission, or rate-limit error**: Confirm the selected API key, project model access, billing status, credits, and provider limits. These checks apply only after a request reaches OpenAI.
- **Generated chart fails**: Rephrase the question with exact column names from the uploaded CSV.
- **Requested rows or lists do not appear**: Ask for a table, rows, records, or a filtered dataframe and include the relevant column names. The app displays at most 10 rows for generated result tables.
- **Large file responses are vague**: Ask more specific questions or filter the CSV before uploading.
- **PDF report service fails**: Start `pdf_mcp_server.py`, confirm `PDF_MCP_URL` ends with `/mcp`, and verify that a deployed HTTPS endpoint is reachable from the Streamlit host.

## License

This project is available for personal and educational use.
