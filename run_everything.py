"""One-command orchestration for the existing Playwright flakiness POC.
Run after generating the five execution_run_*.json files.
Fresh AI calls incur charges; OPENAI_API_KEY must be configured.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'internet_output'
REPORTS = ROOT / 'execution_reports' / 'the-internet'


def run(script, *args):
    print(f'\n=== {script} ===', flush=True)
    subprocess.run([sys.executable, str(ROOT / script), *map(str, args)], cwd=ROOT, check=True)


def main():
    reports = sorted(REPORTS.glob('execution_run_*.json'))
    if not reports:
        sys.exit(f'No execution_run_*.json reports found in {REPORTS}')
    print(f'Found {len(reports)} Playwright JSON report(s).', flush=True)

    # Refreshes JSON conversion, rule analysis, AI failure analysis, and their dashboards.
    run('run_pipeline.py', '--refresh-ai')

    # Generate fresh test-level AI insights; the script preserves existing CSVs
    # by creating a timestamped filename when the default already exists.
    before = {p.resolve() for p in OUT.glob('ai_stability_insights*.csv')}
    run('ai_stability_insights.py',
        '--input', OUT / 'record_level_classification.csv',
        '--ai-failures', OUT / 'ai_failure_analysis.csv',
        '--outdir', OUT, '--all')
    new_files = [p for p in OUT.glob('ai_stability_insights*.csv') if p.resolve() not in before]
    if new_files:
        newest = max(new_files, key=lambda p: p.stat().st_mtime_ns)
    else:
        # If no file existed previously, default output is the new one.
        newest = OUT / 'ai_stability_insights.csv'
        if not newest.exists():
            sys.exit('AI stability insights CSV was not generated.')
    run('generate_stability_dashboard.py',
        '--input', newest,
        '--output', OUT / 'ai_stability_dashboard.html')
    print('\nCOMPLETE. Fresh stability insights:', newest, flush=True)
    print('Dashboards:', *(str(OUT / name) for name in
        ('dashboard.html', 'ai_dashboard.html', 'ai_stability_dashboard.html')),
        sep='\n - ', flush=True)
    print('Manual validation is separate and is not included.', flush=True)


if __name__ == '__main__':
    main()
