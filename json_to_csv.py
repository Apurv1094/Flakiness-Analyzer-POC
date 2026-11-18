
import argparse
import csv
import json
import re
from pathlib import Path

COLUMNS = [
    "test_name",
    "status",
    "execution_timestamp",
    "error_message",
]

ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def extract_error(result):
    errors = result.get("errors") or []

    messages = []
    for error in errors:
        message = error.get("message") or error.get("value") or ""
        if message:
            messages.append(ANSI_PATTERN.sub("", str(message)))

    if not messages and result.get("error"):
        message = result["error"].get("message", "")
        if message:
            messages.append(ANSI_PATTERN.sub("", str(message)))

    return "\n".join(messages)


def extract_records(suites):
    records = []

    def traverse(suite):
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                for result in test.get("results", []):
                    records.append({
                        "test_name": (
                            f"{spec.get('file', '')}::"
                            f"{spec.get('title', '')}"
                            f" [{test.get('projectName', '')}]"
                        ),
                        "status": result.get("status", "unknown"),
                        "execution_timestamp": result.get(
                            "startTime", ""
                        ),
                        "error_message": extract_error(result),
                    })

        for child in suite.get("suites", []):
            traverse(child)

    for suite in suites:
        traverse(suite)

    return records


def convert(input_dir, output_file):
    input_dir = Path(input_dir)
    output_file = Path(output_file)

    if not input_dir.is_dir():
        raise ValueError(
            f"Input directory does not exist: {input_dir}"
        )

    json_files = sorted(
        input_dir.glob("execution_run_*.json")
    )

    if not json_files:
        raise ValueError(
            f"No execution_run_*.json files found in {input_dir}"
        )

    all_records = []

    for json_file in json_files:
        with json_file.open(
            "r", encoding="utf-8-sig"
        ) as file:
            report = json.load(file)

        records = extract_records(report.get("suites", []))

        if not records:
            raise ValueError(
                f"No test records found in {json_file}"
            )

        all_records.extend(records)

        print(
            f"{json_file.name}: "
            f"{len(records)} execution records"
        )

    output_file.parent.mkdir(
        parents=True, exist_ok=True
    )

    with output_file.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=COLUMNS
        )
        writer.writeheader()
        writer.writerows(all_records)

    print(f"\nTotal records: {len(all_records)}")
    print(f"CSV generated: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Playwright JSON reports to CSV"
    )

    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing execution_run_*.json",
    )

    parser.add_argument(
        "--output",
        default="playwright_execution_records.csv",
        help="Output CSV path",
    )

    args = parser.parse_args()

    convert(args.input_dir, args.output)
