"""Build offline HTML dashboard from ai_stability_insights.csv; no API calls."""
import argparse
import csv
import html
import json
from collections import Counter
from pathlib import Path

def e(v):
    return html.escape(str(v if v is not None else ''), quote=True)

def number(v):
    try: return int(float(v or 0))
    except (ValueError, TypeError): return 0

def items(v):
    try:
        x=json.loads(v or '[]')
        return x if isinstance(x,list) else [str(x)]
    except (ValueError,TypeError): return [v] if v else []

def ul(v):
    return '<ul>'+''.join('<li>'+e(x)+'</li>' for x in items(v))+'</ul>' if v else '<p>Not available</p>'

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=Path('internet_output/ai_stability_insights.csv'))
    p.add_argument('--output',type=Path,default=Path('internet_output/ai_stability_dashboard.html'))
    a=p.parse_args()
    if not a.input.is_file(): p.error(f'Input CSV not found: {a.input}')
    with a.input.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        needed={'test_name','total_runs','passed','failed','stability_pattern'}
        missing=needed-set(reader.fieldnames or [])
        if missing: p.error('Missing CSV columns: '+', '.join(sorted(missing)))
        rows=list(reader)
    priority_order={'High':0,'Medium':1,'Low':2}
    rows.sort(key=lambda r:(priority_order.get(r.get('priority','').title(),3),-number(r.get('failed')),r.get('test_name','')))
    priority=Counter((r.get('priority') or 'Unassigned').title() for r in rows)
    recurrence=Counter(r.get('recurrence_status') or 'Not available' for r in rows)
    flaky=sum('flaky' in r.get('stability_pattern','').lower() for r in rows)
    consistent=sum('consistently failing' in r.get('stability_pattern','').lower() for r in rows)
    total_runs=sum(number(r.get('total_runs')) for r in rows)
    failures=sum(number(r.get('failed')) for r in rows)
    errors=sum(bool(r.get('ai_error','').strip()) for r in rows)
    cards=[]
    for i,r in enumerate(rows,1):
        name=r.get('test_name','')
        pat=r.get('stability_pattern','')
        pri=(r.get('priority') or 'Unassigned').title()
        rec=r.get('recurrence_status') or 'Not available'
        runs,passed,failed=[number(r.get(k)) for k in ('total_runs','passed','failed')]
        pct=round(100*failed/runs) if runs else 0
        cards.append(f'''<article class="test" data-name="{e(name.lower())}" data-priority="{e(pri.lower())}" data-pattern="{e(pat.lower())}">
<div class="head"><h3>{i:02}. {e(name)}</h3><span class="pill {e(pri.lower())}">{e(pri)} priority</span></div>
<div class="pills"><span class="pill">{e(pat)}</span><span class="pill">{e(rec)}</span></div>
<div class="numbers"><span>{runs} runs</span><span>{passed} passed</span><span>{failed} failed</span><span>{pct}% failure rate</span></div>
<div class="bar"><span class="pass" style="width:{100*passed/runs if runs else 0:.2f}%"></span><span class="fail" style="width:{100*failed/runs if runs else 0:.2f}%"></span></div>
<details><summary>View insights, evidence and actions</summary><div class="details">
<section><h4>AI insight</h4><p>{e(r.get('ai_insight') or 'Not available')}</p></section>
<section><h4>AI recurring failure interpretation</h4><p>{e(r.get('recurring_failure') or 'Not available')}</p></section>
<section><h4>Python recurrence evidence</h4><p>{e(r.get('recurrence_evidence') or 'Not available')}</p></section>
<section><h4>Failure categories</h4><p>{e(r.get('failure_categories') or 'Not available')}</p></section>
<section><h4>Likely causes (AI hypotheses)</h4>{ul(r.get('likely_causes'))}</section>
<section><h4>Recommended actions (AI)</h4>{ul(r.get('recommended_actions'))}</section>
</div><p class="meta">AI confidence: {e(r.get('confidence') or 'Not available')} · API error: {e(r.get('ai_error') or 'None')}</p></details></article>''')
    def pills(counts): return ' '.join(f'<span class="pill">{e(k)}: {v}</span>' for k,v in counts.items())
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Stability Insights</title>
<style>
:root{font-family:Segoe UI,Arial,sans-serif;background:#0d1523;color:#edf3fa}*{box-sizing:border-box}body{margin:0}main{max-width:1200px;margin:auto;padding:32px 20px 65px}h1{margin:0 0 8px;font-size:30px}h2{font-size:19px;margin:29px 0 12px}h3{font-size:15px;line-height:1.5;margin:0;overflow-wrap:anywhere}h4{font-size:13px;color:#b8cbe3;margin:0 0 8px}p,li{line-height:1.55}.sub,.meta{color:#a8bad0}.meta{font-size:12px}.notice{padding:13px 16px;border:1px solid #405777;background:#18283e;border-radius:10px;margin:20px 0}.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:22px 0}.kpi,.test{background:#162235;border:1px solid #2e415d;border-radius:13px;padding:17px}.kpi strong{display:block;font-size:27px}.kpi small{color:#a8bad0}.pills,.numbers{display:flex;gap:9px;flex-wrap:wrap;margin:13px 0}.pill{display:inline-block;background:#283950;border:1px solid #405572;padding:5px 10px;border-radius:999px;font-size:12px}.pill.high{background:#5a2934;border-color:#975260;color:#ffd2da}.pill.medium{background:#594329;border-color:#947346;color:#ffe3ac}.pill.low{background:#23473f;border-color:#43826f;color:#c5f7e6}.head{display:flex;justify-content:space-between;gap:15px;align-items:start}.numbers{gap:18px;color:#c3d2e4;font-size:13px}.bar{display:flex;height:8px;background:#394b61;overflow:hidden;border-radius:8px}.bar .pass{background:#42bd97}.bar .fail{background:#ef7c8a}.test-list{display:grid;gap:13px}.controls{display:flex;gap:10px;flex-wrap:wrap;margin:15px 0}input,select{background:#1a2a40;border:1px solid #435c7a;border-radius:9px;color:#edf3fa;padding:11px;font:inherit}input{flex:1;min-width:230px}details{margin-top:16px;padding-top:12px;border-top:1px solid #354862}summary{cursor:pointer;color:#a3caff;font-weight:600;font-size:13px}.details{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:18px 0}.details p,.details li{font-size:13px;margin-top:0;overflow-wrap:anywhere}ul{padding-left:19px}li{margin-bottom:5px}.empty{padding:22px;text-align:center;color:#adbed2}footer{color:#92a9c2;font-size:12px;margin-top:25px}[hidden]{display:none!important}@media(max-width:800px){.kpis{grid-template-columns:repeat(2,1fr)}.details{grid-template-columns:1fr}.head{flex-direction:column}}
</style></head><body><main><h1>AI Stability Insights</h1><p class="sub">Cross-run stability patterns, recurrence evidence and prioritized investigations</p>
<div class="notice">Python calculates execution and recurrence metrics. AI-generated root causes and actions are hypotheses that require manual review. This dashboard reads saved CSV data and makes <strong>no API calls</strong>.</div>
<div class="kpis"><div class="kpi"><strong>__COUNT__</strong><small>Test histories analyzed</small></div><div class="kpi"><strong>__FLAKY__</strong><small>Flaky candidates</small></div><div class="kpi"><strong>__CONSISTENT__</strong><small>Consistently failing</small></div><div class="kpi"><strong>__RUNS__</strong><small>Executions represented</small></div><div class="kpi"><strong>__FAILURES__</strong><small>Failed executions</small></div></div>
<h2>Investigation priorities</h2><div class="pills">__PRIORITIES__</div><h2>Recurrence evidence</h2><div class="pills">__RECURRENCES__</div>
<h2>Test investigations <span class="meta" id="count"></span></h2><div class="controls"><input type="search" id="search" placeholder="Search test ID, name or file" aria-label="Search tests"><select id="priority"><option value="">All priorities</option><option>High</option><option>Medium</option><option>Low</option><option>Unassigned</option></select><select id="pattern"><option value="">All patterns</option><option value="flaky">Flaky candidates</option><option value="consistently failing">Consistently failing</option></select></div>
<div class="test-list" id="list">__CARDS__</div><p class="empty" id="empty" hidden>No matching tests.</p>
<footer>Source: __SOURCE__ · AI errors: __ERRORS__</footer></main><script>
const cards=[...document.querySelectorAll('.test')],search=document.getElementById('search'),priority=document.getElementById('priority'),pattern=document.getElementById('pattern');function apply(){let n=0;for(const c of cards){const ok=c.dataset.name.includes(search.value.trim().toLowerCase())&&(!priority.value||c.dataset.priority===priority.value.toLowerCase())&&(!pattern.value||c.dataset.pattern.includes(pattern.value));c.hidden=!ok;if(ok)n++}document.getElementById('count').textContent=`(${n} of ${cards.length})`;document.getElementById('empty').hidden=n!==0}for(const x of [search,priority,pattern])x.addEventListener('input',apply);apply();
</script></body></html>'''
    for k,v in {'__COUNT__':len(rows),'__FLAKY__':flaky,'__CONSISTENT__':consistent,'__RUNS__':total_runs,'__FAILURES__':failures,'__PRIORITIES__':pills(priority),'__RECURRENCES__':pills(recurrence),'__CARDS__':'\n'.join(cards),'__SOURCE__':e(a.input.name),'__ERRORS__':errors}.items(): page=page.replace(k,str(v))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(page,encoding='utf-8')
    print(f'Dashboard generated: {a.output.resolve()}')
    print(f'Test histories: {len(rows)} | Flaky: {flaky} | Consistently failing: {consistent} | AI errors: {errors}')
    print('No API calls made.')
if __name__=='__main__': main()
