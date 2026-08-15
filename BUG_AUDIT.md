# Bug Audit

## 2026-08-15 16:01 - OpenAI model access failure

- Status: fixed
- Symptom: 403 model_not_found because project does not have access to gpt-5.4
- Scope: Streamlit OpenAI chat request
- Suspected cause: app.py hard-coded unavailable model gpt-5.4; Models API showed gpt-4o is available
- Evidence:
  - OpenAI Models API preferred candidates returned gpt-4o
- Changes:
  - app.py: model argument now uses OPENAI_MODEL with gpt-4o default
  - README.md: secrets example documents OpenAI_Model = gpt-4o
- Verification:
  - openai.OpenAI client initialized successfully after dependency fixes
  - app.py compiles with .venv Python
  - Minimal chat completion using configured model returned OK
- Follow-up: none

## 2026-08-15 16:06 - Generated code warning variable NameError

- Status: fixed
- Symptom: Error executing generated code (NameError): name 'w' is not defined
- Scope: Streamlit generated Python code execution path
- Suspected cause: app.py checked if w after exec without defining or collecting warnings
- Evidence:
  - rg found if w after exec(code.strip(), {}, exec_globals) with no w assignment
- Changes:
  - app.py: imported warnings and wrapped exec in warnings.catch_warnings(record=True) as w
- Verification:
  - app.py compiles with .venv Python
  - warnings.catch_warnings smoke test captured one generated-code warning
- Follow-up: none
## 2026-08-15 17:57 - Session memory for generated visualizations

- Status: fixed
- Symptom: Assistant-generated visualization output disappeared from chat after Streamlit reruns and prior turns were not sent back to the model
- Scope: Streamlit chat history and generated-code visualization path
- Suspected cause: messages only stored role/content markdown; figures and warning notes were displayed but not persisted; OpenAI request only included the current user turn
- Evidence:
  - app.py replay loop rendered only msg content; generated figures were shown from plt.gcf without storing image bytes
- Changes:
  - app.py: added render_saved_message for content, notes, and stored chart images
  - app.py: sends text chat_history into OpenAI requests
  - app.py: saves each generated Matplotlib figure as PNG bytes in assistant_message images
  - app.py: sets Matplotlib backend to Agg so chart PNG capture does not require Tcl/Tk
- Verification:
  - app.py compiles with .venv Python
  - Matplotlib BytesIO smoke test produced non-empty PNG bytes
- Follow-up: none
