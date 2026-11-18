"""Streamlit: import reports, automatically analyze selected history, show fresh dashboard."""
import streamlit as st
from enhanced_poc import connection, import_report, history
from live_analysis import scopes, analyze, render
import streamlit.components.v1 as components
from portal_ai import scoped_failures, existing_reviews, run_triage, source_files, suggest_code, code_history

st.set_page_config(page_title='QE Flakiness Analyzer',layout='wide')
st.title('Test Stability & Flakiness Analyzer')
st.caption('Upload reports, preserve history, and analyze test stability automatically. No OpenAI API calls.')
with st.form('upload'):
    a,b,c=st.columns(3)
    project=a.text_input('Project',value='the-internet')
    sprint=b.text_input('Sprint',value='Sprint 1')
    build=c.text_input('Build',value='local-001')
    files=st.file_uploader('Playwright/Cucumber JSON or JUnit-style XML',type=['json','xml'],accept_multiple_files=True)
    submitted=st.form_submit_button('Import and analyze reports')
if submitted:
    if not files:st.warning('Choose at least one report.')
    else:
        with connection() as db:
            for f in files:
                try:
                    n,duplicate=import_report(db,f.getvalue(),f.name,project,sprint,build)
                    st.info(f'{f.name}: '+('already imported for this project/sprint/build (skipped)' if duplicate else f'{n} records imported and ready for analysis'))
                except Exception as exc:st.error(f'{f.name}: {exc}')
st.subheader('Historical execution overview')
with connection() as db:
    st.dataframe(history(db),use_container_width=True,hide_index=True)
    available=scopes(db)
    if available:
        st.subheader('Analyze a project, sprint or build')
        projects=sorted({x['project'] for x in available})
        selected_project=st.selectbox('Project to analyze',projects,index=projects.index(project) if project in projects else 0)
        sprints=['All sprints']+sorted({x['sprint'] for x in available if x['project']==selected_project})
        selected_sprint=st.selectbox('Sprint to analyze',sprints)
        builds=['All builds']+sorted({x['build'] for x in available if x['project']==selected_project and (selected_sprint=='All sprints' or x['sprint']==selected_sprint)})
        selected_build=st.selectbox('Build to analyze',builds)
        sprint_filter=None if selected_sprint=='All sprints' else selected_sprint
        build_filter=None if selected_build=='All builds' else selected_build
        records,stability,patterns=analyze(db,selected_project,sprint_filter,build_filter)
        a,b,c=st.columns(3)
        a.metric('Execution records',len(records))
        b.metric('Consistently failing',sum(x['classification']=='Consistently Failing' for x in stability))
        c.metric('Flaky candidates',sum(x['classification']=='Flaky Candidate' for x in stability))
        with st.expander('Test stability details'):
            st.dataframe(stability,use_container_width=True,hide_index=True)
        with st.expander('Failure classification details'):
            st.dataframe(patterns,use_container_width=True,hide_index=True)
        st.subheader('Optional AI failure analysis')
        st.caption('Paid OpenAI API calls only when you click Run AI Analysis. Results are stored for this execution scope; previously reviewed records are reused.')
        failures=scoped_failures(db,selected_project,sprint_filter,build_filter)
        reviewed=existing_reviews(db,selected_project,sprint_filter,build_filter)
        st.write(f'Failed execution records: {len(failures)} · Saved AI reviews: {len(reviewed)}')
        model=st.text_input('AI model',value='gpt-4.1-mini')
        max_rows=st.number_input('Maximum new failure records to analyze',min_value=1,max_value=200,value=10)
        refresh=st.checkbox('Refresh existing AI reviews (additional API charges)',value=False)
        if st.button('Run AI Analysis',disabled=not failures):
            try:
                with st.spinner('Analyzing selected failures with OpenAI...'):
                    total,pending,completed=run_triage(db,selected_project,sprint_filter,build_filter,model=model,limit=int(max_rows),refresh=refresh)
                errors=sum(bool(error) for _,error in completed)
                st.success(f'AI requests attempted: {len(completed)} of {pending} pending. API errors: {errors}.')
            except Exception as exc:
                st.error(f'AI analysis could not run: {exc}')
        reviews=existing_reviews(db,selected_project,sprint_filter,build_filter)
        if reviews:
            st.dataframe(reviews,use_container_width=True,hide_index=True)
            st.caption('AI categories are hypotheses, not manually verified accuracy.')
        st.subheader('AI code-level fix suggestions')
        st.caption('Select a failing test and a local Playwright source file. AI only proposes changes; no source files are modified.')
        names=sorted({r['test_name'] for r in failures})
        sources=source_files()
        if names and sources:
            chosen=st.selectbox('Failing test',names)
            source=st.selectbox('Test source file',[str(p.relative_to(__import__('pathlib').Path(__file__).resolve().parent)) for p in sources])
            if st.button('Suggest Code Fix (paid API)'):
                try:
                    with st.spinner('Reviewing failure evidence and source code...'):
                        suggestion=suggest_code(db,selected_project,sprint_filter,build_filter,chosen,__import__('pathlib').Path(__file__).resolve().parent/source,model)
                    st.markdown(suggestion)
                except Exception as exc:
                    st.error(f'Could not generate suggestion: {exc}')
        else:
            st.info('Code suggestions require failed executions and local tests/*.spec.ts files.')
        suggestions=code_history(db,selected_project,sprint_filter,build_filter)
        if suggestions:
            with st.expander('Saved code suggestions'):
                for item in suggestions:
                    st.markdown(f"**{item['test_name']}** — `{item['source_path']}` ({item['created_at']})")
                    st.code(item['suggestion'],language='text')
        path=render(db,selected_project,sprint_filter,build_filter)
    else:
        path=None
        st.info('Upload a report to begin.')
if path:
    st.subheader('Consolidated HTML dashboard')
    st.caption('Refreshed for the selected scope using imported records. AI/manual results from earlier runs are not mixed into this analysis.')
    with path.open('rb') as f:
        st.download_button('Download consolidated HTML',f,file_name=path.name,mime='text/html')
    components.html(path.read_text(encoding='utf-8'),height=850,scrolling=True)
