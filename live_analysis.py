"""Fresh, scoped, cost-free analysis of imported execution history."""
from pathlib import Path
import html
from analyzer import analyze_stability, analyze_failure_patterns
from enhanced_poc import connection, history, tabulate, OUTPUT

def scopes(db):
    return [dict(project=p,sprint=s,build=b) for p,s,b in db.execute('SELECT DISTINCT project,sprint,build FROM runs ORDER BY project,sprint,build')]

def analyze(db, project, sprint=None, build=None):
    sql='''SELECT results.test_name,results.status,results.execution_timestamp,results.error_message,results.failure_category FROM results JOIN runs ON results.run_id=runs.id WHERE runs.project=?'''
    params=[project]
    if sprint is not None:
        sql+=' AND runs.sprint=?';params.append(sprint)
    if build is not None:
        sql+=' AND runs.build=?';params.append(build)
    records=[dict(zip(('test_name','status','execution_timestamp','error_message','failure_category'),r)) for r in db.execute(sql,params)]
    return records,analyze_stability(records),analyze_failure_patterns(records)

def render(db,project,sprint=None,build=None):
    from portal_ai import existing_reviews, scoped_failures, code_history
    records,stability,patterns=analyze(db,project,sprint,build)
    failed=[r for r in records if r['status'] in ('failed','timedout','timed_out','error','interrupted')]
    cards=[('Execution records',len(records)),('Tests',len(stability)),('Failed executions',len(failed)),('Consistently failing',sum(r['classification']=='Consistently Failing' for r in stability)),('Flaky candidates',sum(r['classification']=='Flaky Candidate' for r in stability)),('AI reviewed failures',len(existing_reviews(db,project,sprint,build)))]
    reviews=existing_reviews(db,project,sprint,build)
    review_map={r['result_id']:r for r in reviews}
    ai_rows=[{**r,**review_map[r['result_id']]} for r in scoped_failures(db,project,sprint,build) if r['result_id'] in review_map]
    code_rows=code_history(db,project,sprint,build)
    sections=[('history','Sprint history',tabulate(history(db,project),[('Project','project'),('Sprint','sprint'),('Executions','executions'),('Passed','passed'),('Failed','failed'),('Runs','runs')])),('stability','Test stability',tabulate(stability,[('Test','test_name'),('Executions','total_executions'),('Passed','passed'),('Failed','failed'),('Pass rate','pass_rate_percent'),('Classification','classification')])),('patterns','Failure patterns',tabulate(patterns,[('Category','failure_category'),('Count','failure_count'),('Affected tests','affected_tests')])),('failures','Failure details',tabulate(failed,[('Test','test_name'),('Status','status'),('Rule category','failure_category'),('Error','error_message')])),('ai','AI failure analysis',tabulate(ai_rows,[('Test','test_name'),('Rule','failure_category'),('AI','ai_category'),('Confidence','confidence'),('Probable cause','probable_root_cause'),('Action','recommended_action'),('Review','review_required'),('API error','ai_error')]) if ai_rows else '<p>No AI analysis saved for this scope. Use Run AI Analysis in the portal (paid API).</p>'),('code','Code-level suggestions',tabulate(code_rows,[('Test','test_name'),('Source','source_path'),('Suggestion','suggestion'),('Generated','created_at')]) if code_rows else '<p>No code suggestions generated for this scope.</p>'),('manual','Manual validation','<p>Manual validation requires human-reviewed labels matching this selected execution history.</p>')]
    css='''body{font:14px system-ui,Arial;background:#f5f7fb;color:#172235;margin:0}header{background:#152c4b;color:white;padding:24px 5%}main{max-width:1350px;margin:auto;padding:20px}nav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}button{border:1px solid #cbd5e1;border-radius:7px;padding:9px 12px;background:white;cursor:pointer}button.active{background:#1d4ed8;color:white}section{display:none;background:white;border:1px solid #e2e8f0;border-radius:10px;padding:18px;margin:12px 0}section.active{display:block}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}.card{background:#fff;padding:14px;border-radius:9px;border:1px solid #ddd}.card strong{display:block;font-size:25px}.scroll{overflow:auto;max-height:570px}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:9px;text-align:left;border-bottom:1px solid #e5e7eb;vertical-align:top}th{position:sticky;top:0;background:#eaf0f8}input{padding:10px;border:1px solid #bbb;border-radius:6px;min-width:250px}'''
    nav=''.join('<button id="btn-{0}" onclick="show(\'{0}\')">{1}</button>'.format(key,html.escape(title)) for key,title,_ in sections)
    content=''.join('<section id="{0}"><h2>{1}</h2>{2}</section>'.format(key,html.escape(title),table) for key,title,table in sections)
    metrics=''.join('<div class="card">{0}<strong>{1}</strong></div>'.format(html.escape(k),v) for k,v in cards)
    js="function show(id){document.querySelectorAll('section').forEach(e=>e.classList.toggle('active',e.id===id));document.querySelectorAll('nav button').forEach(e=>e.classList.toggle('active',e.id==='btn-'+id))}function filter(){let s=document.querySelector('section.active');if(!s)return;let q=document.getElementById('search').value.toLowerCase();s.querySelectorAll('tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(q)?'':'none')}show('history');"
    scope=' / '.join(x for x in (project,sprint,build) if x)
    page=f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>QE Analyzer</title><style>{css}</style><header><h1>Test Stability & Flakiness Analyzer</h1><p>{html.escape(scope)} · Fresh rule-based analysis · No paid API calls</p></header><main><div class="cards">{metrics}</div><p>Stability is based on the selected execution history; a single run cannot establish flakiness.</p><input id="search" oninput="filter()" placeholder="Filter active table"><nav>{nav}</nav>{content}</main><script>{js}</script></html>'
    OUTPUT.mkdir(exist_ok=True)
    path=OUTPUT/'consolidated_dashboard.html'
    path.write_text(page,encoding='utf-8')
    return path
