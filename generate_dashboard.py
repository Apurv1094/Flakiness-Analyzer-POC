"""Generate a self-contained Plotly HTML dashboard from flakiness analyzer CSVs."""
import argparse
from pathlib import Path
import html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--output', default=None)
    args = parser.parse_args()
    folder = Path(args.input_dir)
    records = pd.read_csv(folder / 'record_level_classification.csv').fillna('')
    stability = pd.read_csv(folder / 'test_stability.csv').fillna('')
    patterns = pd.read_csv(folder / 'failure_patterns.csv').fillna('')
    output = Path(args.output) if args.output else folder / 'dashboard.html'
    output.parent.mkdir(parents=True, exist_ok=True)

    statuses = records['status'].astype(str).str.lower()
    passed = int((statuses == 'passed').sum())
    failed = int(statuses.isin(['failed', 'error', 'timedout', 'timed_out']).sum())
    other = len(records) - passed - failed
    counts = stability['classification'].astype(str).value_counts()
    flaky = int(counts.get('Flaky Candidate', 0))
    consistent_fail = int(counts.get('Consistently Failing', 0))
    rate = (passed / len(records) * 100) if len(records) else 0
    cards = [('Executions',len(records)),('Unique Tests',len(stability)),('Pass Rate',f'{rate:.1f}%'),('Failed Executions',failed),('Flaky Candidates',flaky),('Consistent Failures',consistent_fail)]
    card_html = ''.join(f'<div class="kpi"><span>{html.escape(str(k))}</span><strong>{html.escape(str(v))}</strong></div>' for k,v in cards)

    def chart(fig, include_js=False):
        fig.update_layout(template='plotly_white', paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=25,r=25,t=55,b=40), font=dict(family='Arial'))
        return plot(fig, output_type='div', include_plotlyjs=True if include_js else False, config={'responsive':True, 'displaylogo':False})

    outcome = pd.DataFrame({'Outcome':['Passed','Failed','Other'], 'Count':[passed,failed,other]})
    outcome = outcome[outcome.Count > 0]
    pie = px.pie(outcome, names='Outcome', values='Count', title='Execution Outcomes', hole=.48, color='Outcome', color_discrete_map={'Passed':'#10b981','Failed':'#ef4444','Other':'#94a3b8'})
    pie.update_traces(textinfo='label+percent')

    failure_fig = px.bar(patterns.sort_values('failure_count'), x='failure_count', y='failure_category', orientation='h', title='Failure Categories', labels={'failure_count':'Failures','failure_category':''}, text='failure_count', color_discrete_sequence=['#6366f1'])
    failure_fig.update_layout(yaxis={'automargin':True})

    stability_data = pd.DataFrame({'Classification':counts.index,'Tests':counts.values})
    stability_fig = px.bar(stability_data, x='Classification', y='Tests', title='Test Stability Classification', text='Tests', color='Classification', color_discrete_sequence=['#10b981','#f59e0b','#ef4444'])
    stability_fig.update_layout(showlegend=False, xaxis={'automargin':True})

    stable_table = stability.sort_values(['classification','failed','test_name'], ascending=[True,False,True]).copy()
    stable_table['test_name'] = stable_table['test_name'].astype(str).map(lambda s: html.escape(s))
    table_html = stable_table.to_html(index=False, escape=False, classes='data-table', border=0)
    fail_rows = records[statuses.isin(['failed','error','timedout','timed_out'])][['test_name','failure_category','error_message']].copy()
    fail_rows['error_message'] = fail_rows['error_message'].astype(str).str.slice(0,400)
    failures_html = fail_rows.to_html(index=False, escape=True, classes='data-table', border=0)
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Test Stability & Flakiness Dashboard</title><style>
    body{{margin:0;background:#f3f6fb;color:#14213d;font:15px Arial,sans-serif}}main{{max-width:1250px;margin:auto;padding:32px 20px}}h1{{margin-bottom:5px}}.sub{{color:#64748b;margin-top:0}}.kpis{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:25px 0}}.kpi,.panel{{background:#fff;border:1px solid #e4eaf2;border-radius:14px;padding:20px;box-shadow:0 2px 8px #17255409}}.kpi span{{display:block;color:#64748b;font-size:13px}}.kpi strong{{display:block;font-size:29px;margin-top:8px}}.charts{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.wide{{grid-column:1/-1}}.scroll{{overflow-x:auto;max-height:520px;overflow-y:auto}}.data-table{{width:100%;border-collapse:collapse;font-size:12px}}.data-table td,.data-table th{{border-bottom:1px solid #e8edf4;padding:10px;text-align:left;vertical-align:top;max-width:420px;overflow-wrap:anywhere}}.data-table th{{background:#f8fafc;position:sticky;top:0}}.note{{color:#64748b;font-size:13px}}@media(max-width:760px){{.kpis{{grid-template-columns:repeat(2,1fr)}}.charts{{grid-template-columns:1fr}}.wide{{grid-column:auto}}}}
    </style></head><body><main><h1>Test Stability & Flakiness Dashboard</h1><p class="sub">Execution analysis • Generated from analyzer CSV outputs</p><section class="kpis">{card_html}</section><section class="charts"><div class="panel">{chart(pie,True)}</div><div class="panel">{chart(failure_fig)}</div><div class="panel wide">{chart(stability_fig)}</div></section><h2>Test Stability Details</h2><div class="panel scroll">{table_html}</div><h2>Failure Details</h2><div class="panel scroll">{failures_html}</div><p class="note">Flaky candidates passed and failed across observed runs. Failure categories are rule-based predictions and require manual validation; they are not confirmed root causes.</p></main></body></html>'''
    output.write_text(page, encoding='utf-8')
    print(f'Dashboard generated: {output.resolve()}')

if __name__ == '__main__':
    main()
