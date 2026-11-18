
import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

REQUIRED_COLUMNS = {
    "test_name",
    "status",
    "execution_timestamp",
    "error_message",
}

# Order matters: more specific patterns come first.
PATTERNS = [
    (
        "Authentication / Authorization",
        r"401|403|unauthorized|forbidden|invalid credentials|"
        r"access denied|authentication failed|permission denied",
    ),
    (
        "Stale Element / DOM Change",
        r"stale element|staleelementreference|detached from dom|"
        r"element is not attached",
    ),
    (
        "Locator / Element",
        r"strict mode violation|locator.*resolved to|"
        r"no element found|element not found|"
        r"unable to locate element|nosuchelementexception|"
        r"waiting for locator",
    ),
    (
        "Schema / Contract Validation",
        r"schema validation|schema mismatch|contract violation|"
        r"required property|additional properties|invalid schema",
    ),
    (
        "Browser / Driver",
        r"browser has been closed|target page.*closed|"
        r"browser disconnected|session not created|"
        r"webdriverexception|chromedriver",
    ),
    (
        "Synchronization / Race Condition",
        r"race condition|not stable|intercepted|"
        r"another element would receive|execution context destroyed",
    ),
    (
        "Timeout",
        r"timeout|timed out|timeoutexception|"
        r"exceeded.*ms|deadline exceeded",
    ),
    (
        "Environment / Connectivity",
        r"econnrefused|econnreset|enotfound|dns|"
        r"network error|connection refused|"
        r"connection reset|service unavailable|"
        r"502 bad gateway|503 service unavailable",
    ),
    (
        "Test Data",
        r"missing test data|invalid test data|"
        r"duplicate key|unique constraint|"
        r"test data not found|fixture data missing",
    ),
    (
        "Setup / Dependency",
        r"beforeall|beforeeach|fixture setup|"
        r"setup failed|dependency failed|"
        r"module not found|modulenotfounderror",
    ),
    (
        "Assertion / Functional",
        r"assertionerror|expect\(|expected:|received:|"
        r"toequal|tobevisible|tocontaintext|"
        r"assert\.|expected.*but.*found",
    ),
]

COMPILED_PATTERNS = [
    (name, re.compile(pattern, re.IGNORECASE | re.DOTALL))
    for name, pattern in PATTERNS
]

FAILED_STATUSES = {
    "failed",
    "timedout",
    "timed_out",
    "interrupted",
    "error",
}

PASSED_STATUSES = {"passed"}


def classify_failure(status, error_message):
    status = status.lower().strip()

    if status in PASSED_STATUSES:
        return "Passed"

    if status == "skipped":
        return "Skipped"

    message = error_message or ""

    for category, pattern in COMPILED_PATTERNS:
        if pattern.search(message):
            return category

    if status in FAILED_STATUSES:
        return "Unknown"

    return "Other"


def read_records(input_file):
    with open(
        input_file, "r", newline="", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("Input CSV is empty")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)

        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}"
            )

        records = []

        for row in reader:
            if not row["test_name"].strip():
                continue

            record = {
                key: (value or "").strip()
                for key, value in row.items()
                if key is not None
            }

            record["status"] = record["status"].lower()

            record["failure_category"] = classify_failure(
                record["status"],
                record["error_message"],
            )

            records.append(record)

    return records


def analyze_stability(records):
    grouped = defaultdict(list)

    for record in records:
        grouped[record["test_name"]].append(record)

    results = []

    for test_name, executions in sorted(grouped.items()):
        total = len(executions)

        passed = sum(
            r["status"] in PASSED_STATUSES
            for r in executions
        )

        failed = sum(
            r["status"] in FAILED_STATUSES
            for r in executions
        )

        skipped = total - passed - failed
        executed = passed + failed

        if passed > 0 and failed > 0:
            classification = "Flaky Candidate"
        elif failed > 0 and passed == 0:
            classification = "Consistently Failing"
        elif passed > 0 and failed == 0:
            classification = "Consistently Passing"
        else:
            classification = "No Completed Executions"

        pass_rate = (
            round(passed / executed * 100, 2)
            if executed
            else 0
        )

        results.append({
            "test_name": test_name,
            "total_executions": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate_percent": pass_rate,
            "classification": classification,
        })

    return results


def analyze_failure_patterns(records):
    grouped = defaultdict(lambda: {
        "failures": 0,
        "tests": set(),
    })

    for record in records:
        if record["status"] not in FAILED_STATUSES:
            continue

        category = record["failure_category"]

        grouped[category]["failures"] += 1
        grouped[category]["tests"].add(
            record["test_name"]
        )

    patterns = []

    for category, data in grouped.items():
        patterns.append({
            "failure_category": category,
            "failure_count": data["failures"],
            "affected_tests": len(data["tests"]),
        })

    return sorted(
        patterns,
        key=lambda x: x["failure_count"],
        reverse=True,
    )


def write_csv(path, records, columns):
    with open(
        path, "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=columns, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(records)


def generate_report(
    output_file, records, stability, patterns
):
    total = len(records)

    passed = sum(
        r["status"] in PASSED_STATUSES
        for r in records
    )

    failed = sum(
        r["status"] in FAILED_STATUSES
        for r in records
    )

    skipped = total - passed - failed

    flaky = [
        t for t in stability
        if t["classification"] == "Flaky Candidate"
    ]

    consistent_failures = [
        t for t in stability
        if t["classification"] == "Consistently Failing"
    ]

    lines = [
        "# Test Stability & Flakiness Analysis Report",
        "",
        "## Executive Summary",
        "",
        f"- Execution records analyzed: {total}",
        f"- Unique tests analyzed: {len(stability)}",
        f"- Passed executions: {passed}",
        f"- Failed/error executions: {failed}",
        f"- Skipped/other executions: {skipped}",
        f"- Flaky candidates: {len(flaky)}",
        f"- Consistently failing tests: {len(consistent_failures)}",
        "",
        "## Failure Pattern Analysis",
        "",
        "| Failure Category | Failures | Affected Tests |",
        "|---|---:|---:|",
    ]

    for item in patterns:
        lines.append(
            f"| {item['failure_category']} "
            f"| {item['failure_count']} "
            f"| {item['affected_tests']} |"
        )

    if not patterns:
        lines.append("| None | 0 | 0 |")

    lines.extend([
        "",
        "## Flaky Candidates",
        "",
    ])

    if flaky:
        for test in flaky:
            lines.append(
                f"- {test['test_name']} "
                f"({test['passed']} passed, "
                f"{test['failed']} failed)"
            )
    else:
        lines.append(
            "No flaky candidates observed in this dataset."
        )

    lines.extend([
        "",
        "## Consistently Failing Tests",
        "",
    ])

    if consistent_failures:
        for test in consistent_failures:
            lines.append(
                f"- {test['test_name']} "
                f"({test['failed']} failures)"
            )
    else:
        lines.append(
            "No consistently failing tests observed."
        )

    lines.extend([
        "",
        "## Actionable Insights",
        "",
    ])

    for item in patterns:
        category = item["failure_category"]

        if category == "Locator / Element":
            advice = (
                "Review locator uniqueness, selector stability, "
                "and DOM changes."
            )
        elif category == "Timeout":
            advice = (
                "Review wait conditions, response times, "
                "and execution load."
            )
        elif category == "Assertion / Functional":
            advice = (
                "Review expected results against application "
                "behavior and requirements."
            )
        elif category == "Environment / Connectivity":
            advice = (
                "Investigate environment health, networking, "
                "and dependent services."
            )
        else:
            advice = (
                "Review the associated error messages and "
                "investigate the recurring root cause."
            )

        lines.append(f"- **{category}:** {advice}")

    if not patterns:
        lines.append(
            "- No failures were observed. Continue monitoring "
            "across future executions."
        )

    lines.extend([
        "",
        "## Limitations",
        "",
        "- Failure classification uses regex rules, not an LLM.",
        "- Flaky Candidate means both passing and failing "
        "executions were observed for the same test.",
        "- A consistently failing test is not automatically flaky.",
        "- Classification should be validated against a manually "
        "reviewed sample.",
        "- A small execution history cannot prove that a test "
        "will never be flaky.",
    ])

    output_file.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Analyze test execution stability"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Input execution records CSV",
    )

    parser.add_argument(
        "--outdir",
        default="output",
        help="Output directory",
    )

    args = parser.parse_args()

    output_dir = Path(args.outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = read_records(args.input)

    if not records:
        raise ValueError(
            "No execution records found in input CSV"
        )

    stability = analyze_stability(records)
    patterns = analyze_failure_patterns(records)

    write_csv(
        output_dir / "record_level_classification.csv",
        records,
        [
            "test_name",
            "status",
            "execution_timestamp",
            "error_message",
            "failure_category",
        ],
    )

    write_csv(
        output_dir / "test_stability.csv",
        stability,
        [
            "test_name",
            "total_executions",
            "passed",
            "failed",
            "skipped",
            "pass_rate_percent",
            "classification",
        ],
    )

    write_csv(
        output_dir / "failure_patterns.csv",
        patterns,
        [
            "failure_category",
            "failure_count",
            "affected_tests",
        ],
    )

    generate_report(
        output_dir / "sample_report.md",
        records,
        stability,
        patterns,
    )

    print(f"Analyzed {len(records)} execution records")
    print(f"Unique tests: {len(stability)}")
    print(
        "Flaky candidates:",
        sum(
            t["classification"] == "Flaky Candidate"
            for t in stability
        ),
    )
    print(
        "Consistently failing tests:",
        sum(
            t["classification"] == "Consistently Failing"
            for t in stability
        ),
    )
    print(f"Reports generated in: {output_dir}")


if __name__ == "__main__":
    main()
