"""AI-assisted stability insights from repeated test executions.

Examples (paid API calls):
  python ai_stability_insights.py --limit 3
  python ai_stability_insights.py --all

Requires: pip install openai; OPENAI_API_KEY environment variable.
Existing outputs are never overwritten; new timestamped outputs are created.
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

FIELDS = [
    'test_name', 'total_runs', 'passed', 'failed', 'other', 'stability_pattern',
    'failure_categories', 'recurrence_status', 'recurrence_evidence',
    'ai_insight', 'recurring_failure', 'likely_causes', 'recommended_actions',
    'priority', 'confidence', 'ai_error'
]
AI_FIELDS = ('ai_insight', 'recurring_failure', 'likely_causes', 'recommended_actions', 'priority', 'confidence')


def load(path):
    if not path.is_file():
        raise FileNotFoundError(f'File not found: {path}')
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def val(row, *keys):
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ''


def status_kind(status):
    s = status.lower().strip()
    if s in ('passed', 'pass', 'success', 'expected'):
        return 'passed'
    if s in ('failed', 'fail', 'timedout', 'timed_out', 'error', 'interrupted'):
        return 'failed'
    return 'other'


def build_groups(records, failures):
    groups = defaultdict(list)
    for record in records:
        name = val(record, 'test_name', 'test_id')
        if not name:
            raise ValueError('Execution CSV needs a test_name or test_id column')
        groups[name].append(record)
    ai = defaultdict(list)
    for record in failures:
        name = val(record, 'test_name', 'test_id')
        if name:
            ai[name].append(record)
    return groups, ai


def recurrence(failed_records):
    """Classify observed repetition, not a proven root cause.

    Two or more failures sharing a *non-generic* rule category provide
    category-level recurrence evidence, not proof of identical causes.
    """
    n = len(failed_records)
    if n == 0:
        return 'No observed failures', 'No failed executions'
    if n == 1:
        return 'Isolated observed failure', 'Only 1 failed execution; recurrence not established'
    categories = Counter(
        val(r, 'rule_category', 'failure_category', 'category') or 'Unclassified'
        for r in failed_records
    )
    repeated = [(cat, count) for cat, count in categories.items()
                if count >= 2 and cat.lower() not in ('unclassified', 'unknown', 'other')]
    if repeated:
        repeated.sort(key=lambda item: (-item[1], item[0]))
        details = '; '.join(f'{cat}: {count} failures' for cat, count in repeated)
        return 'Repeated failure category observed', (
            f'{details}. Same category does not prove the same underlying cause.'
        )
    return 'Multiple failures; recurrence unconfirmed', (
        f'{n} failures, but no specific failure category repeats at least twice; '
        'inspect raw errors manually.'
    )


def summarize(name, records, ai_records):
    ordered = sorted(records, key=lambda r: val(r, 'execution_timestamp', 'timestamp', 'start_time', 'run_id'))
    sequence = [status_kind(val(r, 'status', 'outcome', 'result')) for r in ordered]
    counts = Counter(sequence)
    if counts['passed'] and counts['failed']:
        pattern = 'Flaky candidate (mixed pass/fail)'
    elif counts['failed'] and not counts['passed'] and not counts['other']:
        pattern = 'Consistently failing'
    elif counts['passed'] and not counts['failed'] and not counts['other']:
        pattern = 'Consistently passing'
    else:
        pattern = 'Insufficient or mixed other statuses'

    failures_only = [r for r in ordered if status_kind(val(r, 'status', 'outcome', 'result')) == 'failed']
    cats = Counter(val(r, 'rule_category', 'failure_category', 'category') or 'Unclassified'
                   for r in failures_only)
    ai_cats = Counter(val(r, 'ai_category') for r in ai_records
                      if val(r, 'ai_category') and not val(r, 'ai_error'))
    recurrence_status, recurrence_evidence = recurrence(failures_only)
    examples = []
    for r in failures_only[:3]:
        error = val(r, 'error_message', 'error', 'message')
        if error:
            examples.append(error[:650])
    ai_causes = [val(r, 'probable_root_cause')[:250] for r in ai_records
                 if val(r, 'probable_root_cause') and not val(r, 'ai_error')][:3]
    return {
        'test_name': name, 'total_runs': len(records),
        'passed': counts['passed'], 'failed': counts['failed'], 'other': counts['other'],
        'stability_pattern': pattern, 'status_sequence': sequence,
        'failure_categories': dict(cats), 'prior_ai_categories': dict(ai_cats),
        'sample_errors': examples, 'prior_ai_root_causes': ai_causes,
        'recurrence_status': recurrence_status,
        'recurrence_evidence': recurrence_evidence,
    }


def call_ai(client, model, summary):
    system = (
        'You are a senior QA reliability analyst. Interpret ONLY the supplied test history. '
        'Do not invent measurements, logs, reproduction steps, or proven root causes. '
        'Mixed pass/fail is a flaky candidate, not proof of an application defect. '
        'Treat recurrence_status and recurrence_evidence as authoritative observations '
        'calculated by Python; do not contradict them. A single failure is NOT recurring. '
        'Repeated broad categories are evidence of category repetition, not proof of the same cause. '
        'Distinguish locator-not-found from element-not-visible and navigation timeout where evidence allows. '
        'Recommend inspecting traces, timestamps, error messages, page readiness, and environment first. '
        'Do not recommend blind timeout increases or retries as a primary fix; retries may mask flakiness. '
        'Return ONLY a JSON object with keys ai_insight, recurring_failure, likely_causes, '
        'recommended_actions, priority, confidence. '
        'ai_insight and recurring_failure are strings; likely_causes and recommended_actions '
        'are arrays of 1-3 short strings; priority and confidence are High, Medium, or Low. '
        'Prioritize by failure frequency, severity of available evidence, and investigation value; '
        'do not assert business impact without evidence.'
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{'role': 'system', 'content': system},
                  {'role': 'user', 'content': json.dumps(summary, ensure_ascii=False)}],
        response_format={'type': 'json_object'},
        temperature=0,
    )
    result = json.loads(response.choices[0].message.content)
    for key in AI_FIELDS:
        if key not in result:
            raise ValueError(f'Missing AI response field: {key}')
    for key in ('likely_causes', 'recommended_actions'):
        if not isinstance(result[key], list) or not all(isinstance(x, str) for x in result[key]):
            raise ValueError(f'AI response {key} must be an array of strings')
    for key in ('priority', 'confidence'):
        if result[key] not in ('High', 'Medium', 'Low'):
            raise ValueError(f'AI response {key} must be High, Medium, or Low')
    for key in ('ai_insight', 'recurring_failure'):
        if not isinstance(result[key], str):
            raise ValueError(f'AI response {key} must be a string')
    return result


def csv_text(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return '' if value is None else str(value)


def unique_output(outdir):
    base = outdir / 'ai_stability_insights.csv'
    if not base.exists():
        return base
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    candidate = outdir / f'ai_stability_insights_{stamp}.csv'
    counter = 2
    while candidate.exists():
        candidate = outdir / f'ai_stability_insights_{stamp}_{counter}.csv'
        counter += 1
    return candidate


def main():
    parser = argparse.ArgumentParser(description='AI stability insights across repeated test executions')
    parser.add_argument('--input', type=Path, default=Path('internet_output/record_level_classification.csv'))
    parser.add_argument('--ai-failures', type=Path, default=Path('internet_output/ai_failure_analysis.csv'))
    parser.add_argument('--outdir', type=Path, default=Path('internet_output'))
    parser.add_argument('--model', default='gpt-4.1-mini')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--limit', type=int, help='Analyze up to N tests')
    mode.add_argument('--all', action='store_true', help='Analyze all eligible tests')
    parser.add_argument('--include-passing', action='store_true')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be at least 1')
    if not os.environ.get('OPENAI_API_KEY'):
        parser.error('OPENAI_API_KEY is not set; no API calls made')
    try:
        from openai import OpenAI
    except ImportError:
        parser.error('Install SDK: pip install openai')

    records = load(args.input)
    failures = load(args.ai_failures) if args.ai_failures.exists() else []
    groups, ai_groups = build_groups(records, failures)
    summaries = [summarize(name, items, ai_groups.get(name, [])) for name, items in groups.items()]
    if not args.include_passing:
        summaries = [s for s in summaries if s['failed'] > 0]
    summaries.sort(key=lambda s: (0 if 'Flaky' in s['stability_pattern'] else 1,
                                  -s['failed'], s['test_name']))
    if args.limit:
        summaries = summaries[:args.limit]
    if not summaries:
        print('No eligible test histories found. No API calls made.')
        return

    print(f'Will send {len(summaries)} test histories to {args.model}; API charges apply.', flush=True)
    client = OpenAI()
    results = []
    for i, summary in enumerate(summaries, 1):
        print(f'[{i}/{len(summaries)}] {summary["test_name"]}', flush=True)
        row = {key: csv_text(summary.get(key, '')) for key in FIELDS}
        try:
            analysis = call_ai(client, args.model, summary)
            for key in AI_FIELDS:
                row[key] = csv_text(analysis[key])
        except Exception as exc:
            row['ai_error'] = f'{type(exc).__name__}: {str(exc)[:350]}'
            print(f'  ERROR: {row["ai_error"]}', file=sys.stderr)
        results.append(row)

    args.outdir.mkdir(parents=True, exist_ok=True)
    output = unique_output(args.outdir)
    with output.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)

    report = output.with_suffix('.md')
    lines = [
        '# AI Stability Insights', '', f'Test histories analyzed: {len(results)}', '',
        '**Caution:** AI interpretations are hypotheses; manual review is required.', '',
    ]
    for row in results:
        lines.extend([
            f'## {row["test_name"]}', '',
            f'- Runs: {row["total_runs"]}; Passed: {row["passed"]}; Failed: {row["failed"]}',
            f'- Pattern: {row["stability_pattern"]}',
            f'- Recurrence status (Python): {row["recurrence_status"]}',
            f'- Recurrence evidence (Python): {row["recurrence_evidence"]}',
            f'- Priority (AI): {row["priority"] or "Not available"}',
            f'- Insight (AI): {row["ai_insight"] or "Not available"}',
            f'- Recurring failure interpretation (AI): {row["recurring_failure"] or "Not available"}',
            f'- Likely causes (AI): {row["likely_causes"] or "Not available"}',
            f'- Recommended actions (AI): {row["recommended_actions"] or "Not available"}',
            f'- API error: {row["ai_error"] or "None"}', '',
        ])
    report.write_text('\n'.join(lines), encoding='utf-8')
    successes = sum(not row['ai_error'] for row in results)
    print(f'CSV: {output.resolve()}\nReport: {report.resolve()}\nSuccess: {successes}/{len(results)}')


if __name__ == '__main__':
    main()
