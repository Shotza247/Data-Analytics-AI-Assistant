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
## 2026-08-15 18:58 - gpt-5.1 model availability test

- Status: fixed
- Symptom: Need to know whether project can use gpt-5.1 after gpt-5.4 access failure
- Scope: OpenAI model selection for Streamlit app
- Suspected cause: gpt-5.1 is available, but openai==1.40.6 does not expose max_completion_tokens directly
- Evidence:
  - Models API list contained gpt-5.1
  - models.retrieve('gpt-5.1') succeeded
  - chat.completions with max_tokens failed; extra_body max_completion_tokens returned OK
- Changes:
  - No app code changed during availability test
- Verification:
  - Minimal gpt-5.1 chat completion returned OK via extra_body
- Follow-up:
  - Update app request builder or OpenAI SDK before switching OpenAI_Model to gpt-5.1
## 2026-08-15 19:07 - MVP1 hidden analysis code polish

- Status: fixed
- Symptom: MVP1 should show analysis, results, and charts without exposing generated Python code
- Scope: Streamlit assistant response rendering and README MVP1 documentation
- Suspected cause: assistant markdown displayed raw python fenced code before chart execution
- Evidence:
  - app.py previously rendered the full OpenAI reply before extracting code blocks
- Changes:
  - app.py: added helpers to extract python blocks and hide them from displayed/stored assistant messages
  - app.py: execution errors no longer display hidden generated code
  - README.md: labels current app as MVP1 and documents hidden-code behavior
- Verification:
  - app.py compiles with .venv Python
  - regex smoke test extracts code while returning display text without python block
- Follow-up: none
## 2026-08-15 22:55 - MVP1 business insight and sidebar readability polish

- Status: fixed
- Symptom: MVP1 needed more stakeholder-friendly insights and the sidebar data summary was compressed into two narrow columns
- Scope: Streamlit assistant prompt and sidebar data summary layout
- Suspected cause: Prompt emphasized analysis/code generation more than business interpretation; sidebar used two columns inside a narrow sidebar
- Evidence:
  - app.py had col1/col2 inside Data Summary expander and generic concise-answer prompt
- Changes:
  - app.py: added sidebar business context controls for industry and audience/goal
  - app.py: rewrote prompt to require plain-language insights, business meaning, recommended next steps, caveats, and industry alignment
  - app.py: replaced compressed sidebar columns with stacked Dataset Overview, Data Quality, and Numeric Statistics sections
  - README.md: updated MVP1 description for business insights and stacked sidebar summary
- Verification:
  - app.py compiles with .venv Python
  - sample_data.csv sidebar summary smoke test produced null and numeric summaries
- Follow-up: none
## 2026-08-16 10:15 - Temporary KMeans customer segmentation dependency

- Status: fixed
- Symptom: Error executing generated code (ModuleNotFoundError): No module named 'sklearn' while testing KMeans customer segmentation
- Scope: Temporary data-science dependency for generated analysis code
- Suspected cause: MVP1 requirements did not include scikit-learn; numpy was installed transitively but not explicit
- Evidence:
  - pip show found numpy 2.5.2 and no scikit-learn before install
- Changes:
  - requirements.txt: added numpy==2.5.2 and scikit-learn==1.9.0
  - app.py: exposed np and KMeans to hidden generated code execution context
  - app.py: set LOKY_MAX_CPU_COUNT=1 to avoid Windows core-count warning during KMeans tests
- Verification:
  - app.py compiles with .venv Python
  - KMeans smoke test produced labels [0, 0, 1, 1]
- Follow-up:
  - Remove scikit-learn, numpy explicit pin, np/KMeans globals, and LOKY_MAX_CPU_COUNT when the temporary customer-segmentation test is finished
