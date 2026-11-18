# Enhanced POC — Quick Start

This adds a Streamlit upload portal, persistent SQLite sprint history, and one consolidated HTML report. It does not alter the existing analyzer or make paid API calls.

## Windows CMD

```bat
cd C:\path\to\playwright-flakiness-poc
python -m pip install streamlit
python enhanced_poc.py
python -m streamlit run app.py
```

Open the URL printed by Streamlit. Upload Playwright JSON, Cucumber JSON or JUnit-compatible XML. Provide project, sprint and build metadata. Exact duplicate file uploads for the same project/sprint/build are skipped.

The consolidated dashboard is `internet_output\consolidated_dashboard.html`. The historical database is `data\execution_history.db`.

**Scope limitations:** The portal stores imported executions and shows sprint counts; it does not yet automatically run the existing analysis pipeline on uploaded reports. The AI and manual validation sections reuse previously generated CSVs and may refer to a different dataset from uploaded sprint history. Cucumber JSON and JUnit-style XML import are initial adapters; native TestNG XML is not yet supported. AI code-level fix suggestions and classifier retraining are not implemented. These need additional integration and validation. Existing `run_everything.py` still makes paid API calls.

Do not upload sensitive reports or code to an untrusted server. The portal is intended for local use only.

## Automatic rule-based analysis (new)

The updated `app.py` imports report data into SQLite and immediately recalculates test stability and failure patterns for the chosen project/sprint/build. Choose **All sprints** to analyze the full project history, or a specific sprint/build for a narrower scope. The consolidated HTML is regenerated from that selection and downloadable from the UI. No paid AI calls are made.

Start: `python -m streamlit run app.py`

**Important:** New imports update the SQLite history, not the older CSV files. AI and manual-validation results from the original POC are intentionally not presented as if they apply to new reports. A single run cannot establish intermittent/flaky behavior. Duplicate imports are skipped only for the same project/sprint/build and identical file bytes. The project database in this ZIP is a snapshot and will not contain any additional Sprint 2/3 uploads performed on your Windows machine; preserve your local `data/execution_history.db` when upgrading.
