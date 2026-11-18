"""Compare manually reviewed failure categories against rule and AI results.

Usage:
 python validate_manual_results.py --manual manual_validation.csv --rules internet_output/record_level_classification.csv --ai internet_output/ai_failure_analysis.csv --outdir internet_output
"""
import argparse
import csv
import html
import re
from collections import Counter
from pathlib import Path


def read_csv(path, required):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        missing = set(required) - set(fields)
        if missing:
            raise ValueError(f'{path}: missing columns: {sorted(missing)}; available: {fields}')
        return list(reader)


def key(row):
    return (row['test_name'].strip(), row['execution_timestamp'].strip())


def index_rows(rows, label):
    index = {}
    duplicates = set()
    for row in rows:
        k = key(row)
        if k in index:
            duplicates.add(k)
        else:
            index[k] = row
    if duplicates:
        raise ValueError(f'{label}: {len(duplicates)} duplicate test_name/timestamp pairs; cannot match safely')
    return index


def normalize(category):
    return re.sub(r'\s+', ' ', category.strip()).casefold()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manual', required=True, type=Path)
    parser.add_argument('--rules', type=Path, default=Path('internet_output/record_level_classification.csv'))
    parser.add_argument('--ai', type=Path, default=Path('internet_output/ai_failure_analysis.csv'))
    parser.add_argument('--outdir', type=Path, default=Path('internet_output'))
    args = parser.parse_args()
    manual = read_csv(args.manual, ['test_name', 'execution_timestamp', 'Remarks'])
    rules = index_rows(read_csv(args.rules, ['test_name', 'execution_timestamp', 'failure_category']), 'Rules')
    ai = index_rows(read_csv(args.ai, ['test_name', 'execution_timestamp', 'ai_category']), 'AI')
    index_rows(manual, 'Manual')
    output = []
    for row in manual:
        category = row['Remarks'].strip()
        if not category:
            continue
        k = key(row)
        rule = rules.get(k)
        prediction = ai.get(k)
        rule_category = rule['failure_category'].strip() if rule else ''
        ai_category = prediction['ai_category'].strip() if prediction else ''
        output.append({
            'test_name': k[0], 'execution_timestamp': k[1],
            'manual_category': category, 'rule_category': rule_category, 'ai_category': ai_category,
            'rule_match': ('Match' if normalize(category) == normalize(rule_category) else 'Mismatch') if rule and rule_category else 'Unmatched',
            'ai_match': ('Match' if normalize(category) == normalize(ai_category) else 'Mismatch') if prediction and ai_category else 'Unmatched',
            'probable_root_cause': prediction.get('probable_root_cause', '') if prediction else '',
            'recommended_action': prediction.get('recommended_action', '') if prediction else '',
        })
    if not output:
        raise ValueError('No rows with non-empty Remarks were found')
    args.outdir.mkdir(parents=True, exist_ok=True)
    comparison = args.outdir / 'manual_validation_comparison.csv'
    with comparison.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    def metrics(field):
        counts = Counter(r[field] for r in output)
        evaluated = counts['Match'] + counts['Mismatch']
        percent = 100 * counts['Match'] / evaluated if evaluated else 0
        return counts, evaluated, percent
    rc, rn, rp = metrics('rule_match')
    ac, an, ap = metrics('ai_match')
    unmatched = [r for r in output if r['rule_match'] == 'Unmatched' or r['ai_match'] == 'Unmatched']
    rule_display = f'{rp:.1f}%' if rn else 'N/A (no matched records)'
    ai_display = f'{ap:.1f}%' if an else 'N/A (no matched records)'
    summary = f'''# Manual Validation Summary

- Manually labeled rows: **{len(output)}**
- Rule vs manual: **{rc['Match']}/{rn} ({rule_display})** exact-category agreement; {rc['Mismatch']} mismatches; {rc['Unmatched']} unmatched
- AI vs manual: **{ac['Match']}/{an} ({ai_display})** exact-category agreement; {ac['Mismatch']} mismatches; {ac['Unmatched']} unmatched
- Records missing a rule or AI match: **{len(unmatched)}**

Agreement is measured only on matched rows with non-empty predictions, not all test executions. Manual labels are reference judgments, not necessarily proven root causes. Matching requires exact `test_name` and `execution_timestamp`.
'''
    (args.outdir / 'manual_validation_summary.md').write_text(summary, encoding='utf-8')
    rows_html = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(r[field]))}</td>' for field in ['test_name','execution_timestamp','manual_category','rule_category','ai_category','rule_match','ai_match']) + '</tr>' for r in output)
    dashboard = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Manual Validation Comparison</title><style>body{{font:16px system-ui,sans-serif;margin:2rem;background:#f7f9fc;color:#172033}}h1{{margin-bottom:.25rem}}.stats{{display:flex;flex-wrap:wrap;gap:1rem;margin:1.5rem 0}}.card{{background:white;padding:1.2rem;border-radius:12px;box-shadow:0 2px 12px #0001;min-width:180px}}.value{{font-size:2rem;font-weight:700}}.tablewrap{{overflow:auto;background:white;border-radius:12px}}table{{border-collapse:collapse;width:100%;font-size:.85rem}}td,th{{padding:.7rem;text-align:left;border-bottom:1px solid #e4e8ee}}th{{background:#eaf0f7;position:sticky;top:0}}.muted{{color:#536177}}</style></head><body><h1>Manual Validation Comparison</h1><p class="muted">Exact-category agreement against manually assigned Remarks</p><div class="stats"><div class="card">Reviewed<div class="value">{len(output)}</div></div><div class="card">Rule vs manual<div class="value">{rule_display}</div><small>{rc['Match']} / {rn} matched</small></div><div class="card">AI vs manual<div class="value">{ai_display}</div><small>{ac['Match']} / {an} matched</small></div><div class="card">Unmatched records<div class="value">{len(unmatched)}</div></div><p class="muted">Manual categories are review labels, not automatically verified root causes. Percentages exclude unmatched records.</p><div class="tablewrap"><table><thead><tr><th>Test</th><th>Timestamp</th><th>Manual</th><th>Rule</th><th>AI</th><th>Rule match</th><th>AI match</th></tr></thead><tbody>{rows_html}</tbody></table></div></body></html>'''
    (args.outdir / 'manual_validation_dashboard.html').write_text(dashboard, encoding='utf-8')
    print(summary)
    print('Created:', comparison, args.outdir / 'manual_validation_summary.md', args.outdir / 'manual_validation_dashboard.html', sep='\n - ')

if __name__ == '__main__':
    main()
