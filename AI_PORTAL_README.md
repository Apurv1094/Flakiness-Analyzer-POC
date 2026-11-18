# Enhanced AI integration — Streamlit portal

## Included
- Automatic rule-based analysis and sprint/build dashboard (existing behavior)
- Explicit **Run AI Analysis** button for scoped failures, with configurable request limit
- SQLite-backed AI review cache keyed by imported result ID and model; refresh is optional
- Scoped AI results in the consolidated HTML dashboard
- Explicit **Suggest Code Fix** button using a selected local Playwright TypeScript test file and observed failure messages; suggestions are never applied automatically
- Saved code suggestion history, scoped by project/sprint/build

## Windows setup
1. Back up `data\execution_history.db` and your project before copying updates.
2. Install: `python -m pip install streamlit openai pandas`
3. Set your OpenAI API key **in the CMD session where Streamlit starts**: `set OPENAI_API_KEY=your_key_here` (do not share or commit it).
4. Start: `python -m streamlit run app.py`
5. Choose a project, sprint and build. Rule-based results refresh without AI calls.
6. Click **Run AI Analysis** only when you want paid API requests. Default limit is 10 new failures. Saved reviews are reused for the same model unless refresh is checked.
7. Choose a failing test and a source file, then click **Suggest Code Fix** to get a reviewable recommendation. Confirm the selected source corresponds to the failure before sending.

## Important limitations
- AI analysis requires a separately billed OpenAI API key and network access. This package was tested without making live paid API requests.
- Best-effort secret masking is applied to error messages, but source files are sent to the API for code suggestions; inspect them for secrets, personal data, and confidential code first.
- AI classifications and suggested fixes are hypotheses, not validated root causes. No code is changed automatically.
- Manual validation is not automatically linked to new sprint uploads; previously reviewed manual labels must not be treated as ground truth for different executions.
- Imported reports must be in supported schemas; native TestNG XML may need conversion to JUnit XML.
- Reusing the same report under a different sprint/build creates another historical entry; avoid using copied reports as genuine sprint comparisons.
- The existing classifier taxonomy has not been retrained or proven more accurate. The manual agreement baseline should be re-measured on independent reviewed records after prompt changes.
