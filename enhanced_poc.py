"""Local-only enhanced POC: normalized imports, SQLite history, consolidated HTML."""
import csv, hashlib, html, io, json, sqlite3, xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from json_to_csv import extract_records
from analyzer import classify_failure

ROOT=Path(__file__).resolve().parent
DB=ROOT/'data'/'execution_history.db'
OUTPUT=ROOT/'internet_output'
FIELDS=['test_name','status','execution_timestamp','error_message']

def read_csv(path):
    p=Path(path)
    if not p.exists(): return []
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def normalize(data,filename):
    name=filename.lower()
    if name.endswith('.json'):
        doc=json.loads(data.decode('utf-8-sig'))
        if isinstance(doc,dict) and 'suites' in doc: return extract_records(doc['suites'])
        if isinstance(doc,list):
            rows=[]
            def walk(steps,prefix):
                for x in steps:
                    label=' / '.join([*prefix,x.get('name','scenario')])
                    if x.get('type')=='scenario' or ('steps' in x and 'keyword' not in x):
                        results=[s.get('result',{}) for s in x.get('steps',[])]
                        bad=next((r for r in results if r.get('status') in ('failed','undefined','ambiguous')),None)
                        rows.append(dict(test_name=label,status='failed' if bad else 'passed',execution_timestamp=x.get('startTime',''),error_message=(bad or {}).get('error_message','')))
                    walk(x.get('elements',[]),[*prefix,x.get('name','feature')])
            walk(doc,[])
            if rows:return rows
        raise ValueError('Unsupported JSON schema; expected Playwright JSON or Cucumber JSON')
    if name.endswith('.xml'):
        root=ET.fromstring(data)
        cases=root.findall('.//testcase')
        if root.tag=='testcase':cases=[root]
        rows=[]
        for case in cases:
            problem=next((case.find(tag) for tag in ('failure','error') if case.find(tag) is not None),None)
            skipped=case.find('skipped') is not None
            rows.append(dict(test_name=f"{case.get('classname','suite')}::{case.get('name','test')}",status='failed' if problem is not None else 'skipped' if skipped else 'passed',execution_timestamp=case.get('timestamp') or root.get('timestamp',''),error_message=((problem.get('message','')+'\n'+(problem.text or '')) if problem is not None else '')))
        if not rows:raise ValueError('No JUnit-style testcase elements found. Native TestNG XML requires conversion to JUnit XML.')
        return rows
    raise ValueError('Supported extensions: .json, .xml')

def connection():
    DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB);c.execute('PRAGMA foreign_keys=ON')
    c.executescript('''CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY,project TEXT NOT NULL,sprint TEXT NOT NULL,build TEXT NOT NULL,source TEXT NOT NULL,sha256 TEXT NOT NULL,imported_at TEXT NOT NULL,UNIQUE(project,sprint,build,sha256));
    CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY,run_id INTEGER NOT NULL REFERENCES runs(id),test_name TEXT NOT NULL,status TEXT NOT NULL,execution_timestamp TEXT,error_message TEXT,failure_category TEXT);''')
    return c

def import_report(c,data,filename,project,sprint,build):
    if not all(v.strip() for v in (project,sprint,build)):raise ValueError('Project, sprint and build must be provided')
    records=normalize(data,filename)
    if not records:raise ValueError('No executions found')
    digest=hashlib.sha256(data).hexdigest()
    existing=c.execute('SELECT id FROM runs WHERE project=? AND sprint=? AND build=? AND sha256=?',(project,sprint,build,digest)).fetchone()
    if existing:return 0,True
    with c:
        cur=c.execute('INSERT INTO runs(project,sprint,build,source,sha256,imported_at) VALUES(?,?,?,?,?,?)',(project,sprint,build,filename,digest,datetime.now(timezone.utc).isoformat()))
        c.executemany('INSERT INTO results(run_id,test_name,status,execution_timestamp,error_message,failure_category) VALUES(?,?,?,?,?,?)',[(cur.lastrowid,r.get('test_name',''),r.get('status','unknown').lower(),r.get('execution_timestamp',''),r.get('error_message',''),classify_failure(r.get('status','unknown'),r.get('error_message',''))) for r in records])
    return len(records),False

def history(c,project=None):
    q='''SELECT runs.project,runs.sprint,COUNT(*) executions,SUM(CASE WHEN LOWER(results.status)='passed' THEN 1 ELSE 0 END) passed,SUM(CASE WHEN LOWER(results.status) IN ('failed','timedout','timed_out','error','interrupted') THEN 1 ELSE 0 END) failed,COUNT(DISTINCT runs.id) runs FROM results JOIN runs ON results.run_id=runs.id'''
    args=[]
    if project:q+=' WHERE runs.project=?';args.append(project)
    q+=' GROUP BY runs.project,runs.sprint ORDER BY runs.project,runs.sprint'
    return [dict(zip(['project','sprint','executions','passed','failed','runs'],r)) for r in c.execute(q,args)]

def esc(v):return html.escape(str(v if v is not None else ''))

def tabulate(rows,columns,limit=250):
    if not rows:return '<p class="muted">No data available.</p>'
    th=''.join(f'<th>{esc(title)}</th>' for title,key in columns)
    body=''.join('<tr>'+''.join(f'<td>{esc(r.get(key,""))[:1200]}</td>' for title,key in columns)+'</tr>' for r in rows[:limit])
    return f'<div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'

def dashboard(c=None):
    OUTPUT.mkdir(exist_ok=True)
    stability=read_csv(OUTPUT/'test_stability.csv'); failures=read_csv(OUTPUT/'ai_failure_analysis.csv'); insights=read_csv(OUTPUT/'ai_stability_insights.csv');manual=read_csv(OUTPUT/'manual_validation_comparison.csv'); classifications=read_csv(OUTPUT/'record_level_classification.csv')
    if c is None:c=connection()
    trends=history(c)
    totals=Counter(r.get('classification','') for r in stability)
    cards=[('Test cases',len(stability)),('Execution records',len(classifications)),('Consistently failing',totals['Consistently Failing']+totals['Consistently failing']),('Flaky candidates',sum('flaky' in k.lower() for k in totals for _ in range(totals[k]))),('AI failure records',len(failures)),('Manually reviewed',len(manual))]
    css='''body{font:14px system-ui,Arial;background:#f5f7fb;color:#172235;margin:0}header{background:#152c4b;color:white;padding:24px 5%}main{max-width:1350px;margin:auto;padding:20px}nav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}button{border:1px solid #cbd5e1;border-radius:7px;padding:9px 12px;background:white;cursor:pointer}button.active{background:#1d4ed8;color:white}section{display:none;background:white;border:1px solid #e2e8f0;border-radius:10px;padding:18px;margin:12px 0}section.active{display:block}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}.card{background:#fff;padding:14px;border-radius:9px;border:1px solid #ddd}.card strong{display:block;font-size:25px}.muted{color:#64748b}.scroll{overflow:auto;max-height:570px}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:9px;text-align:left;border-bottom:1px solid #e5e7eb;vertical-align:top}th{position:sticky;top:0;background:#eaf0f8}input{padding:10px;border:1px solid #bbb;border-radius:6px;min-width:250px}'''
    sections=[('history','Sprint history',tabulate(trends,[('Project','project'),('Sprint','sprint'),('Executions','executions'),('Passed','passed'),('Failed','failed'),('Runs','runs')])),('stability','Test stability',tabulate(stability,[('Test','test_name'),('Executions','total_executions'),('Pass','passed'),('Fail','failed'),('Pass rate','pass_rate_percent'),('Classification','classification')])),('failures','AI failure analysis',tabulate(failures,[('Test','test_name'),('Rule','rule_category'),('AI','ai_category'),('Confidence','confidence'),('Probable root cause','probable_root_cause'),('Suggested action','recommended_action'),('Review','review_required')])),('insights','AI stability insights',tabulate(insights,[('Test','test_name'),('Pattern','stability_pattern'),('AI insight','ai_insight'),('Likely causes','likely_causes'),('Recommended actions','recommended_actions'),('Priority','priority')])),('validation','Manual validation',tabulate(manual,[('Test','test_name'),('Manual','manual_category'),('Rule','rule_category'),('AI','ai_category'),('Rule match','rule_match'),('AI match','ai_match')]))]
    nav=''.join(f'<button onclick="show(\'{sid}\')" id="btn-{sid}">{esc(title)}</button>' for sid,title,_ in sections)
    content=''.join(f'<section id="{sid}"><h2>{esc(title)}</h2>{body}</section>' for sid,title,body in sections)
    metrics=''.join(f'<div class="card"><span class="muted">{esc(k)}</span><strong>{esc(v)}</strong></div>' for k,v in cards)
    js="function show(id){document.querySelectorAll('section').forEach(e=>e.classList.toggle('active',e.id===id));document.querySelectorAll('nav button').forEach(e=>e.classList.toggle('active',e.id==='btn-'+id))}function filter(){let s=document.querySelector('section.active');if(!s)return;let q=document.getElementById('search').value.toLowerCase();s.querySelectorAll('tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(q)?'':'none')}show('history');"
    page=f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>QE Consolidated Dashboard</title><style>{css}</style><header><h1>Test Stability & Flakiness Analyzer</h1><p>Consolidated POC dashboard · Existing saved AI outputs are reused; no API calls</p></header><main><div class="cards">{metrics}</div><p><input id="search" oninput="filter()" placeholder="Filter active table..."> <span class="muted">Historical data is based on imported reports; other tabs use existing analysis CSVs.</span></p><nav>{nav}</nav>{content}</main><script>{js}</script></html>'
    path=OUTPUT/'consolidated_dashboard.html';path.write_text(page,encoding='utf-8');return path

if __name__=='__main__':print(dashboard())
