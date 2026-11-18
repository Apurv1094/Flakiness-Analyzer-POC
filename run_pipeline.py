"""Orchestrate Playwright report conversion, analysis, and three HTML dashboards.

Usage:
    python run_pipeline.py
    python run_pipeline.py --reports-only
    python run_pipeline.py --refresh-ai

Only --refresh-ai makes paid API calls (individual failure analysis only).
Stability insights are never refreshed automatically.
"""

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JSON_DIR = BASE_DIR / "execution_reports" / "the-internet"
CSV_FILE = BASE_DIR / "internet_execution_records.csv"
OUTPUT_DIR = BASE_DIR / "internet_output"
RECORD_CLASSIFICATIONS = OUTPUT_DIR / "record_level_classification.csv"
AI_CSV = OUTPUT_DIR / "ai_failure_analysis.csv"
AI_METADATA = OUTPUT_DIR / "ai_failure_analysis.source.json"
STABILITY_AI_CSV = OUTPUT_DIR / "ai_stability_insights.csv"
STABILITY_AI_METADATA = OUTPUT_DIR / "ai_stability_insights.source.json"


def execute(script, *arguments):
    path = BASE_DIR / script
    if not path.is_file():
        raise FileNotFoundError(f"Required script not found: {path}")
    print(f"\nExecuting {script}...", flush=True)
    subprocess.run([sys.executable, str(path), *map(str, arguments)], cwd=BASE_DIR, check=True)


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ai_dashboard_script():
    for filename in ("generator_ai_dashboard.py", "generate_ai_dashboard.py"):
        if (BASE_DIR / filename).is_file():
            return filename
    raise FileNotFoundError("Neither generator_ai_dashboard.py nor generate_ai_dashboard.py exists.")


def verify_ai_source():
    if not AI_CSV.is_file():
        print("AI failure CSV not found. Skipping AI failure dashboard.")
        return False
    if not RECORD_CLASSIFICATIONS.is_file():
        print("WARNING: Cannot verify AI failure results: classification CSV is missing.")
        return True
    if not AI_METADATA.is_file():
        print("WARNING: AI failure CSV has no source fingerprint (legacy results).")
        print("         Confirm it belongs to this execution dataset before presenting it.")
        return True
    try:
        metadata = json.loads(AI_METADATA.read_text(encoding="utf-8"))
        if metadata.get("classification_sha256") != file_hash(RECORD_CLASSIFICATIONS):
            print("WARNING: AI failure results belong to a different classification CSV.")
            print("         Skipping AI failure dashboard. --refresh-ai will make paid calls.")
            return False
    except (OSError, ValueError) as exc:
        print(f"WARNING: Cannot verify AI failure source metadata: {exc}")
        return False
    return True


def refresh_ai():
    if not RECORD_CLASSIFICATIONS.is_file():
        raise FileNotFoundError(f"Classification CSV not found: {RECORD_CLASSIFICATIONS}")
    if AI_CSV.exists():
        suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = OUTPUT_DIR / f"ai_failure_analysis.backup.{suffix}.csv"
        shutil.copy2(AI_CSV, backup)
        print(f"Backed up AI failure CSV: {backup}")
    if AI_METADATA.exists():
        AI_METADATA.unlink()
    execute("ai_failure_analyzer.py", "--input", RECORD_CLASSIFICATIONS,
            "--output", AI_CSV, "--all")
    if not AI_CSV.is_file():
        raise RuntimeError("AI failure analyzer did not produce the expected CSV.")
    AI_METADATA.write_text(json.dumps({
        "classification_sha256": file_hash(RECORD_CLASSIFICATIONS),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2), encoding="utf-8")


def verify_stability_source():
    """Check that saved AI stability insights appear to match current executions.

    Legacy CSVs without a source fingerprint remain usable, but unverified.
    """
    if not STABILITY_AI_CSV.is_file():
        print("AI stability insights CSV not found. Skipping stability dashboard.")
        return False
    if not RECORD_CLASSIFICATIONS.is_file():
        print("WARNING: Cannot verify stability insights: classification CSV is missing.")
        return False
    try:
        with STABILITY_AI_CSV.open(encoding="utf-8-sig", newline="") as handle:
            insights = list(csv.DictReader(handle))
        with RECORD_CLASSIFICATIONS.open(encoding="utf-8-sig", newline="") as handle:
            records = list(csv.DictReader(handle))
        if not insights:
            print("WARNING: Stability insights CSV is empty; skipping dashboard.")
            return False
        if not records:
            print("WARNING: Classification CSV is empty; skipping stability dashboard.")
            return False
        counts = {}
        for row in records:
            name = (row.get("test_name") or row.get("test_id") or "").strip()
            if name:
                counts[name] = counts.get(name, 0) + 1
        for row in insights:
            name = (row.get("test_name") or "").strip()
            if name not in counts or int(row.get("total_runs") or 0) != counts[name]:
                print("WARNING: Stability insights do not match current test names/run counts.")
                print("         Skipping stability dashboard to avoid mixing datasets.")
                print("         Re-run ai_stability_insights.py --all (paid API calls).")
                return False
    except (OSError, ValueError, csv.Error) as exc:
        print(f"WARNING: Cannot validate stability insights CSV: {exc}")
        return False

    if STABILITY_AI_METADATA.is_file():
        try:
            metadata = json.loads(STABILITY_AI_METADATA.read_text(encoding="utf-8"))
            if metadata.get("classification_sha256") != file_hash(RECORD_CLASSIFICATIONS):
                print("WARNING: Stability insights source fingerprint does not match.")
                print("         Skipping stability dashboard; refresh stability insights explicitly.")
                return False
        except (OSError, ValueError) as exc:
            print(f"WARNING: Cannot verify stability source metadata: {exc}")
            return False
    else:
        print("WARNING: Stability insights have no source fingerprint (legacy results).")
        print("         Test names/run counts match, but identical source data is not proven.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate rule-based and AI test-analysis dashboards")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--refresh-ai", action="store_true",
                       help="Refresh individual AI failure analysis (paid API calls); does NOT refresh stability insights")
    modes.add_argument("--reports-only", action="store_true",
                       help="Regenerate dashboards from existing CSVs without paid API calls")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not args.reports_only:
        if not JSON_DIR.is_dir():
            raise FileNotFoundError(f"JSON reports folder not found: {JSON_DIR}")
        execute("json_to_csv.py", "--input-dir", JSON_DIR, "--output", CSV_FILE)
        execute("analyzer.py", "--input", CSV_FILE, "--outdir", OUTPUT_DIR)

    if not (OUTPUT_DIR / "test_stability.csv").is_file():
        raise FileNotFoundError("Rule-based output missing. Run without --reports-only first.")
    execute("generate_dashboard.py", "--input-dir", OUTPUT_DIR)

    if args.refresh_ai:
        print("\nNOTICE: --refresh-ai makes paid API calls for failure analysis ONLY.", flush=True)
        refresh_ai()

    if verify_ai_source():
        execute(ai_dashboard_script(), "--input", AI_CSV,
                "--output", OUTPUT_DIR / "ai_dashboard.html")
        print(f"AI failure dashboard: {OUTPUT_DIR / 'ai_dashboard.html'}")
    else:
        print("AI failure dashboard not regenerated.")

    if verify_stability_source():
        execute("generate_stability_dashboard.py", "--input", STABILITY_AI_CSV,
                "--output", OUTPUT_DIR / "ai_stability_dashboard.html")
        print(f"AI stability dashboard: {OUTPUT_DIR / 'ai_stability_dashboard.html'}")
    else:
        print("AI stability dashboard not regenerated.")

    print("\nPipeline finished successfully.")
    print(f"Rule-based dashboard: {OUTPUT_DIR / 'dashboard.html'}")
    print("Stability AI analysis was not re-run; existing insights were reused if available.")


if __name__ == "__main__":
    main()
