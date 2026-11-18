# AI-Driven Test Stability & Flakiness Analyzer POC
## Current Capabilities and End-to-End Execution Guide

### 1. Overview

The AI-Driven Test Stability & Flakiness Analyzer is a Python-based Quality Engineering POC designed to analyze automation test execution reports, identify recurring failures, detect potentially flaky tests, and provide AI-assisted investigation and corrective recommendations.

The solution currently supports two workflows:

1. **Command-line pipeline:** Processes saved Playwright JSON reports and generates rule-based and AI analysis outputs.
2. **Streamlit web portal:** Allows QA engineers to upload reports, maintain sprint/build history, perform rule-based analysis, view a consolidated dashboard, and optionally request AI failure analysis and code-level suggestions.

The goal is to reduce repetitive execution-report investigation and help QA teams prioritize unstable tests.

---

## 2. Current POC Capabilities

| Capability | Description |
|---|---|
| Execution report ingestion | Supports Playwright JSON, basic Cucumber JSON and JUnit-style XML reports |
| Historical execution tracking | Stores execution records by project, sprint and build in SQLite |
| Rule-based failure classification | Categorizes failures based on error messages and predefined classification rules |
| Test stability analysis | Identifies consistently passing, consistently failing and flaky-candidate tests |
| Sprint/build analysis | Allows selection of specific projects, sprints and builds |
| AI failure analysis | Analyzes failed executions and provides probable root causes and recommended actions |
| AI code-level suggestions | Reviews selected Playwright TypeScript test files and suggests possible fixes |
| AI result reuse | Stores AI failure reviews to avoid repeated analysis of the same records with the same model |
| Consolidated dashboard | Displays execution history, stability results and saved AI findings in one HTML dashboard |
| Manual validation | Existing scripts compare manually reviewed categories against automated classifications |

**Important:** AI recommendations are hypotheses requiring QA review. Classification accuracy improvements have not yet been independently demonstrated.

---

## 3. Prerequisites

The following software is required:

- Python 3.x
- Node.js and npm
- Playwright Test
- Chromium browser for Playwright
- Streamlit
- OpenAI Python package
- OpenAI API key for AI functionality

The latest project uses `@playwright/test` version 1.64.1 in its dependency configuration.

### Initial setup

Open Windows CMD and navigate to the project:

```bat
cd /d D:\playwright-flakiness-poc-enhanced\playwright-flakiness-poc
```

Install Node.js dependencies:

```bat
npm install
```

Install Chromium:

```bat
npx playwright install chromium
```

Install Python dependencies:

```bat
python -m pip install streamlit openai pandas
```

These installation steps are generally required only during initial setup or after dependency changes.

---

# 4. Workflow A — Execute Tests and Generate Playwright Reports

### Step 1: Verify available test cases

```bat
npx playwright test tests/the-internet --list
```

This lists the Playwright test cases available for execution.

### Step 2: Execute tests and generate a JSON report

For example, to generate a report for Sprint 2, Build 2:

```bat
npx playwright test tests/the-internet --project=chromium --retries=0 --reporter=json > execution_reports\the-internet\sprint2_build2.json
```

The generated JSON report contains execution results such as test names, statuses, errors and execution details.

**Note:** Because output is redirected using `>`, test progress is not displayed normally in CMD. Wait until the command prompt returns.

Test failures are acceptable; they are part of the data we want to analyze.

### Step 3: Generate multiple execution reports

To identify flakiness, tests must be executed repeatedly.

For five runs in Windows CMD:

```bat
for /L %i in (1,1,5) do @(echo Running %i & npx playwright test tests/the-internet --project=chromium --retries=0 --reporter=json > "execution_reports\the-internet\execution_run_0%i.json")
```

This generates:

```text
execution_reports/
  the-internet/
    execution_run_01.json
    execution_run_02.json
    execution_run_03.json
    execution_run_04.json
    execution_run_05.json
```

The existing command-line pipeline uses reports matching `execution_run_*.json`. It does not automatically include an arbitrarily named file such as `sprint2_build2.json`.

For sprint-specific history, retain distinct reports rather than overwriting previous execution evidence.

---

# 5. Workflow B — Execute the Existing Analysis Pipeline

The command-line pipeline processes Playwright execution reports and generates analysis outputs.

### Option 1: Run rule-based analysis without fresh AI calls

```bat
python run_pipeline.py
```

This performs:

1. Playwright JSON-to-CSV conversion
2. Rule-based failure classification
3. Test stability calculation
4. Rule-based dashboard generation
5. Reuse of compatible existing AI analysis outputs, when available

It does not initiate new OpenAI API requests.

### Option 2: Run the complete AI pipeline

First, configure the OpenAI API key in the CMD session:

```bat
set OPENAI_API_KEY=your_actual_api_key
```

Then execute:

```bat
python run_everything.py
```

This performs:

1. JSON-to-CSV conversion
2. Rule-based failure classification
3. Test stability analysis
4. Fresh AI analysis of failed execution records
5. AI-based analysis of failing test histories
6. HTML dashboard generation

**Important:** `run_everything.py` makes fresh, separately billed OpenAI API calls. It does not execute Playwright tests or automatically import reports into the Streamlit database.

### Option 3: Refresh only individual AI failure analysis

```bat
python run_pipeline.py --refresh-ai
```

This refreshes AI failure classifications but does not refresh test-level AI stability insights.

### Option 4: Regenerate existing dashboards

```bat
python run_pipeline.py --reports-only
```

This regenerates the original pipeline dashboards from existing CSV files without making paid API calls.

---

## 6. Generated Pipeline Outputs

The existing pipeline produces files such as:

```text
internet_execution_records.csv

internet_output/
  record_level_classification.csv
  test_stability.csv
  failure_patterns.csv
  sample_report.md

  dashboard.html
  ai_failure_analysis.csv
  ai_dashboard.html

  ai_stability_insights.csv
  ai_stability_insights.md
  ai_stability_dashboard.html

  manual_validation_comparison.csv
  manual_validation_dashboard.html
```

### Purpose of the main outputs

| File | Purpose |
|---|---|
| `internet_execution_records.csv` | Normalized execution records |
| `record_level_classification.csv` | Rule-based failure classifications |
| `test_stability.csv` | Per-test stability calculations |
| `failure_patterns.csv` | Failure-category summary |
| `ai_failure_analysis.csv` | AI classifications and recommendations |
| `ai_stability_insights.csv` | AI insights based on failing test histories |
| `manual_validation_comparison.csv` | Comparison with manually reviewed categories |

The manual-validation files are generated separately; manual validation is not included automatically in `run_everything.py`.

---

# 7. Workflow C — Launch the Streamlit Web Portal

### Step 1: Navigate to the project

```bat
cd /d D:\playwright-flakiness-poc-enhanced\playwright-flakiness-poc
```

### Step 2: Configure the OpenAI API key (optional)

Only required when using AI functionality:

```bat
set OPENAI_API_KEY=your_actual_api_key
```

Do not store API keys in source files or commit them to Git.

### Step 3: Start Streamlit

```bat
python -m streamlit run app.py
```

Expected output:

```text
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
```

### Step 4: Open the UI

Open:

http://localhost:8501

Keep the CMD window running while using the portal.

---

# 8. Upload Execution Reports Through the UI

The portal contains three metadata fields:

| Field | Example |
|---|---|
| Project | the-internet |
| Sprint | Sprint 2 |
| Build | Build 2 |

### Steps

1. Enter the project name.
2. Enter the sprint name.
3. Enter the build identifier.
4. Click the report upload control.
5. Select one or multiple supported JSON/XML execution reports.
6. Click **Import and analyze reports**.

### What happens after import?

The application:

- Parses the uploaded execution reports.
- Normalizes execution records.
- Calculates rule-based failure categories.
- Saves results in SQLite.
- Updates the historical execution overview.
- Makes the imported records available for sprint/build analysis.

The history database is stored at:

```text
data/execution_history.db
```

The same file is skipped if it has already been imported under the same project, sprint and build with identical content.

Uploading the same report under another sprint/build is technically possible, but should not be presented as a genuine new execution.

---

# 9. Analyze Historical Execution Results

After importing reports, locate:

**Analyze a project, sprint or build**

Select:

- Project
- Sprint, or All sprints
- Build, or All builds

The portal automatically calculates the rule-based analysis for the selected scope.

### Available metrics

**Execution records:** Total execution records in the selected scope.

**Consistently failing:** Tests that fail in every observed execution.

**Flaky candidates:** Tests with a mixture of passing and failing executions.

**Failure classification:** Failure categories derived from error messages.

The UI also provides expandable tables showing detailed stability and failure classifications.

**Important:** Stability is calculated from the execution history available in the selected scope. A single execution cannot establish a meaningful flaky pattern.

---

# 10. Execute AI Failure Analysis from the UI

The latest version includes an optional AI failure analysis section.

### Steps

1. Select the project, sprint and build.
2. Locate **Optional AI failure analysis**.
3. Confirm that failed execution records are available.
4. Select the AI model. The default is `gpt-4.1-mini`.
5. Enter the maximum number of new failure records to analyze.
6. Click **Run AI Analysis**.

The default request limit is 10 records.

### AI analysis output

For each analyzed failure, the AI can provide:

- Failure category
- Probable root cause
- Explanation
- Recommended corrective action
- Confidence indication
- Manual-review requirement

AI reviews are saved in SQLite and reused for the same execution record and model.

Selecting **Refresh existing AI reviews** requests fresh analysis and may incur additional API charges.

**No paid AI requests are triggered simply by uploading reports or opening the dashboard.**

---

# 11. Generate AI Code-Level Fix Suggestions

The portal also provides:

**AI code-level fix suggestions**

This functionality examines failure evidence and a selected local Playwright TypeScript test file.

### Steps

1. Select a project/sprint/build containing failures.
2. Choose a failing test.
3. Select its corresponding `.spec.ts` source file.
4. Click **Suggest Code Fix (paid API)**.

The AI reviews the supplied source code and error details and may suggest:

- A probable code-level issue
- The relevant code snippet
- A recommended modification
- Before-and-after TypeScript examples
- A way to validate the suggested fix

For example, if a test has a dialog-handling synchronization issue, AI may recommend registering the dialog handler before clicking the button.

### Important limitations

- AI does not automatically modify the test file.
- Suggestions require QA review.
- The user must select the correct source file.
- Source code is sent to the OpenAI API, so confidential information and credentials must be removed before analysis.

Generated code suggestions are saved for later review.

---

# 12. Consolidated HTML Dashboard

The Streamlit portal generates a consolidated dashboard for the selected project, sprint and build.

The dashboard provides access to:

1. Sprint execution history
2. Test stability information
3. Rule-based failure classifications
4. Saved AI failure reviews for the selected execution scope
5. Available AI code-fix suggestions

The portal provides a **Download consolidated HTML** option.

Unlike the original command-line dashboards, the portal dashboard is generated from the imported SQLite execution history for the selected scope.

Previously generated AI CSV files are not automatically treated as AI results for newly imported sprint executions.

---

# 13. Recommended Daily QA Execution Workflow

For regular QA usage, the recommended process is:

**Step 1 — Execute tests**

Run the Playwright test suite and generate a JSON report.

**Step 2 — Open the portal**

```bat
python -m streamlit run app.py
```

**Step 3 — Upload the report**

Provide the project, sprint and build identifiers.

**Step 4 — Review automatic rule-based results**

Check consistently failing tests, flaky candidates and failure categories.

**Step 5 — Run AI analysis when required**

Analyze selected failures using the **Run AI Analysis** button.

**Step 6 — Review code-level recommendations**

Select the relevant test source file and request a suggested fix.

**Step 7 — Download the consolidated dashboard**

Use the HTML report for review or demonstration.

**Step 8 — Repeat for future builds and sprints**

The portal preserves historical execution records, enabling comparison across imported execution periods.

For normal portal usage, running `run_pipeline.py` or `run_everything.py` beforehand is not mandatory.

---

# 14. Current Limitations and Future Improvements

Although the POC now supports an integrated UI workflow, some areas require further improvement:

- AI classification accuracy needs further independent validation.
- Historical comparisons should use genuinely different execution runs.
- Code-level AI suggestions require manual verification.
- Multi-framework support currently uses basic report adapters and needs broader real-world validation.
- Native TestNG XML may require conversion to JUnit XML.
- The original command-line pipeline and Streamlit portal maintain separate analysis workflows.
- Manual validation of newly imported sprint results is not yet fully integrated into the portal.
- CI/CD-triggered automatic report ingestion is not yet implemented.

---

## 15. Summary

The current POC has evolved from a command-line failure analyzer into a web-based execution analysis solution.

A QA engineer can now upload automation execution reports, preserve historical results by sprint/build, automatically perform rule-based stability analysis, request AI failure investigation, obtain reviewable code-level suggestions, and generate a consolidated dashboard.

The solution provides a foundation for historical test stability monitoring and AI-assisted failure investigation, with classification validation, framework coverage and CI integration remaining important areas for further development.
