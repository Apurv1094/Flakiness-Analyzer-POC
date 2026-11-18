"""AI-assisted test-history insights from existing execution and failure CSVs.

Examples:
  python ai_stability_insights.py --input internet_output/record_level_classification.csv --ai-failures internet_output/ai_failure_analysis.csv --outdir internet_output --limit 3
  python ai_stability_insights.py --input internet_output/record_level_classification.csv --ai-failures internet_output/ai_failure_analysis.csv --outdir internet_output --all

Requires: pip install openai. Makes paid API calls ONLY when executed.
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = ['test_name','total_runs','passed','failed','other','stability_pattern','failure_categories','ai_insight','recurring_failure','likely_causes','recommended_actions','priority','confidence','ai_error']


def load(path):
    if not path.is_file():
        raise FileNotFoundError(f'File not found: {path}')
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def val(row, *keys):
    for key in keys:
        v = row.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ''


def status_kind(status):
    s = status.lower().strip()
    if s in ('passed','pass','success','expected'):
        return 'passed'
    if s in ('failed','fail','timedout','timed_out','error','interrupted'):
        return 'failed'
    return 'other'


def build_groups(records, failures):
    groups = defaultdict(list)
    for r in records:
        name = val(r,'test_name','test_id')
        if not name:
            raise ValueError('Execution CSV needs a test_name or test_id column')
        groups[name].append(r)
    ai = defaultdict(list)
    for r in failures:
        ai[val(r,'test_name','test_id')].append(r)
    return groups, ai


def summarize(name, records, ai_records):
    ordered = sorted(records, key=lambda r: val(r,'execution_timestamp','timestamp','start_time','run_id'))
    sequence = [status_kind(val(r,'status','outcome','result')) for r in ordered]
    counts = Counter(sequence)
    if counts['passed'] and counts['failed']:
        pattern = 'Flaky candidate (mixed pass/fail)'
    elif counts['failed'] and not counts['passed'] and not counts['other']:
        pattern = 'Consistently failing'
    elif counts['passed'] and not counts['failed'] and not counts['other']:
        pattern = 'Consistently passing'
    else:
        pattern = 'Insufficient or mixed other statuses'
    failures_only = [r for r in ordered if status_kind(val(r,'status','outcome','result')) == 'failed']
    cats = Counter(val(r,'rule_category','failure_category','category') or 'Unclassified' for r in failures_only)
    ai_cats = Counter(val(r,'ai_category') for r in ai_records if val(r,'ai_category') and not val(r,'ai_error'))
    # Limit external payload to sanitized, bounded examples; user must inspect for secrets before calling.
    examples = []
    for r in failures_only[:3]:
        error = val(r,'error_message','error','message')
        if error:
            examples.append(error[:650])
    ai_causes = [val(r,'probable_root_cause')[:250] for r in ai_records if val(r,'probable_root_cause')][:3]
    return {
        'test_name': name,
        'total_runs': len(records),
        'passed': counts['passed'], 'failed': counts['failed'], 'other': counts['other'],
        'stability_pattern': pattern,
        'status_sequence': sequence,
        'failure_categories': dict(cats),
        'prior_ai_categories': dict(ai_cats),
        'sample_errors': examples,
        'prior_ai_root_causes': ai_causes,
    }


def call_ai(client, model, summary):
    system = ('You are a senior QA reliability analyst. Interpret supplied test history only. '
              'Do not invent telemetry or assert unproven root causes. '
              'Mixed pass/fail means flaky candidate, not proven application flakiness. '
              'Return ONLY a JSON object with keys ai_insight, recurring_failure, likely_causes, '
              'recommended_actions, priority, confidence. '
              'ai_insight and recurring_failure are strings; likely_causes and recommended_actions '
              'are arrays of 1-3 short strings; priority is High, Medium, or Low; '
              'confidence is High, Medium, or Low. Prioritize recurring failures and mixed pass/fail.')
    response = client.chat.completions.create(
        model=model,
        messages=[{'role':'system','content':system},
                  {'role':'user','content':json.dumps(summary,ensure_ascii=False)}],
        response_format={'type':'json_object'},
        temperature=0,
    )
    content = response.choices[0].message.content
    result = json.loads(content)
    for key in ('ai_insight','recurring_failure','likely_causes','recommended_actions','priority','confidence'):
        if key not in result:
            raise ValueError(f'Missing AI response field: {key}')
    return result


def csv_text(value):
    if isinstance(value, (dict,list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value or '')


def main():
    parser=argparse.ArgumentParser(description='AI stability insights across repeated test executions')
    parser.add_argument('--input',type=Path,default=Path('internet_output/record_level_classification.csv'))
    parser.add_argument('--ai-failures',type=Path,default=Path('internet_output/ai_failure_analysis.csv'))
    parser.add_argument('--outdir',type=Path,default=Path('internet_output'))
    parser.add_argument('--model',default='gpt-4.1-mini')
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--limit',type=int,help='Analyze up to N tests (start with 3)')
    mode.add_argument('--all',action='store_true',help='Analyze all tests with at least one failure')
    parser.add_argument('--include-passing',action='store_true',help='Also analyze consistently passing tests')
    args=parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be at least 1')
    if not os.environ.get('OPENAI_API_KEY'):
        parser.error('OPENAI_API_KEY is not set; no API calls made')
    try:
        from openai import OpenAI
    except ImportError:
        parser.error('Install SDK: pip install openai')
    records=load(args.input)
    failures=load(args.ai_failures) if args.ai_failures.exists() else []
    groups, ai_groups=build_groups(records,failures)
    summaries=[summarize(name,items,ai_groups.get(name,[])) for name,items in groups.items()]
    if not args.include_passing:
        summaries=[s for s in summaries if s['failed'] > 0]
    # Focus first on flaky candidates and repeatedly failing tests.
    summaries.sort(key=lambda s: (0 if 'Flaky' in s['stability_pattern'] else 1, -s['failed'], s['test_name']))
    if args.limit:
        summaries=summaries[:args.limit]
    if not summaries:
        print('No eligible test histories found. No API calls made.')
        return
    print(f'Will send {len(summaries)} test histories to {args.model}; API charges apply.',flush=True)
    client=OpenAI()
    results=[]
    for i,s in enumerate(summaries,1):
        print(f'[{i}/{len(summaries)}] {s["test_name"]}',flush=True)
        row={key:csv_text(s.get(key,'')) for key in FIELDS}
        try:
            analysis=call_ai(client,args.model,s)
            for key in ('ai_insight','recurring_failure','likely_causes','recommended_actions','priority','confidence'):
                row[key]=csv_text(analysis[key])
        except Exception as exc:
            row['ai_error']=f'{type(exc).__name__}: {str(exc)[:350]}'
            print(f'  ERROR: {row["ai_error"]}',file=sys.stderr)
        results.append(row)
    args.outdir.mkdir(parents=True,exist_ok=True)
    # Avoid overwriting prior completed output: write to a new file if one exists.
    out=args.outdir/'ai_stability_insights.csv'
    if out.exists():
        out=args.outdir/f'ai_stability_insights_{int(time.time())}.csv'
    with out.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)
    md=out.with_suffix('.md')
    lines=['# AI Stability Insights','',f'Test histories analyzed: {len(results)}','',
           '**Caution:** AI-generated interpretations are hypotheses; manual review is required.','']
    for r in results:
        lines += [f'## {r["test_name"]}','',
                  f'- Runs: {r["total_runs"]}; Passed: {r["passed"]}; Failed: {r["failed"]}',
                  f'- Pattern: {r["stability_pattern"]}',
                  f'- Priority: {r["priority"] or "Not available"}',
                  f'- Insight: {r["ai_insight"] or "Not available"}',
                  f'- Recurring failure: {r["recurring_failure"] or "Not available"}',
                  f'- Likely causes: {r["likely_causes"] or "Not available"}',
                  f'- Recommended actions: {r["recommended_actions"] or "Not available"}',
                  f'- API error: {r["ai_error"] or "None"}','']
    md.write_text('\n'.join(lines),encoding='utf-8')
    print(f'CSV: {out.resolve()}\nReport: {md.resolve()}\nSuccess: {sum(not r["ai_error"] for r in results)}/{len(results)}')

if __name__=='__main__':
    main()
