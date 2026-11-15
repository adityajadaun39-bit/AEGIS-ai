"""Repeated reliability benchmark for the AEGIS MVP.

Runs each existing security evaluation scenario 30 times by default.
Reuses the isolated-database scenario runner from run_evaluation.py.
All tool operations remain simulated.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from evaluation.run_evaluation import DOCUMENTS, SCENARIOS, run_scenario

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "evaluation" / "results"
JSON_PATH = RESULTS_DIR / "benchmark_report.json"
CSV_PATH = RESULTS_DIR / "benchmark_results.csv"
DEFAULT_REPETITIONS = 30


def percentile_nearest_rank(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("Cannot calculate percentile for an empty list")
    ordered = sorted(values)
    rank = max(1, math.ceil((percentile / 100) * len(ordered)))
    return ordered[rank - 1]


def latency_summary(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "mean_ms": None, "median_ms": None, "p95_ms": None,
                "min_ms": None, "max_ms": None, "stdev_ms": None}
    return {
        "count": len(values),
        "mean_ms": round(statistics.mean(values), 3),
        "median_ms": round(statistics.median(values), 3),
        "p95_ms": round(percentile_nearest_rank(values, 95), 3),
        "min_ms": round(min(values), 3),
        "max_ms": round(max(values), 3),
        "stdev_ms": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0,
    }


def build_summary(results: list[dict], repetitions: int) -> dict:
    total = len(results)
    passed = sum(item["status"] == "PASS" for item in results)
    failed = sum(item["status"] == "FAIL" for item in results)
    errors = sum(item["status"] == "ERROR" for item in results)
    decision_matches = sum(bool(item.get("checks", {}).get("decision_matches")) for item in results)
    broker_matches = sum(bool(item.get("checks", {}).get("broker_actions_match")) for item in results)
    denied_checks = sum(bool(item.get("checks", {}).get("denied_action_not_executed")) for item in results)
    latencies = [item["latency_ms"] for item in results]
    return {
        "scenario_count": len(SCENARIOS),
        "repetitions_per_scenario": repetitions,
        "total_executions": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate_percent": round(passed / total * 100, 2) if total else 0,
        "decision_match_rate_percent": round(decision_matches / total * 100, 2) if total else 0,
        "broker_action_match_rate_percent": round(broker_matches / total * 100, 2) if total else 0,
        "denied_action_enforcement_check_rate_percent": round(denied_checks / total * 100, 2) if total else 0,
        "decision_counts": dict(Counter(item["actual_decision"] for item in results)),
        "latency": latency_summary(latencies),
    }


def write_csv(results: list[dict]) -> None:
    fields = [
        "id", "name", "run_number", "status", "expected_decision",
        "actual_decision", "latency_ms", "broker_actions",
        "decision_matches", "broker_actions_match",
        "denied_action_not_executed", "reason", "trace_id", "attack_id",
    ]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in results:
            checks = item.get("checks", {})
            writer.writerow({
                "id": item.get("id"),
                "name": item.get("name"),
                "run_number": item.get("run_number"),
                "status": item.get("status"),
                "expected_decision": item.get("expected_decision"),
                "actual_decision": item.get("actual_decision"),
                "latency_ms": item.get("latency_ms"),
                "broker_actions": "|".join(item.get("broker_actions", [])),
                "decision_matches": checks.get("decision_matches"),
                "broker_actions_match": checks.get("broker_actions_match"),
                "denied_action_not_executed": checks.get("denied_action_not_executed"),
                "reason": item.get("reason"),
                "trace_id": item.get("trace_id"),
                "attack_id": item.get("attack_id"),
            })


def main() -> None:
    repetitions = DEFAULT_REPETITIONS
    if len(sys.argv) > 1:
        try:
            repetitions = int(sys.argv[1])
        except ValueError:
            raise SystemExit("Usage: python -m evaluation.run_benchmark [repetitions]")
    if not 1 <= repetitions <= 1000:
        raise SystemExit("Repetitions must be between 1 and 1000.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    print("========== AEGIS REPEATED SECURITY BENCHMARK ==========")
    print(f"Scenarios: {len(SCENARIOS)} | Repetitions each: {repetitions}")
    print(f"Planned executions: {len(SCENARIOS) * repetitions}")

    try:
        for scenario in SCENARIOS:
            print(f"\n{scenario['id']} - {scenario['name']}")
            scenario_results = []
            for run_number in range(1, repetitions + 1):
                result = run_scenario(scenario)
                result["run_number"] = run_number
                results.append(result)
                scenario_results.append(result)
                if result["status"] != "PASS":
                    print(f"  Run {run_number}: {result['status']} - {result.get('reason') or result.get('checks')}")
            passed_count = sum(item["status"] == "PASS" for item in scenario_results)
            print(f"  {passed_count}/{repetitions} passed")
    finally:
        DOCUMENTS.pop("evaluation_safe_document.txt", None)

    summary = build_summary(results, repetitions)
    scenario_summaries = []
    for scenario in SCENARIOS:
        items = [item for item in results if item["id"] == scenario["id"]]
        pass_count = sum(item["status"] == "PASS" for item in items)
        scenario_summaries.append({
            "id": scenario["id"],
            "name": scenario["name"],
            "expected_decision": scenario["expected_decision"],
            "passed": pass_count,
            "failed": sum(item["status"] == "FAIL" for item in items),
            "errors": sum(item["status"] == "ERROR" for item in items),
            "pass_rate_percent": round(pass_count / len(items) * 100, 2) if items else 0,
            "latency": latency_summary([item["latency_ms"] for item in items]),
        })

    report = {
        "project": "AEGIS",
        "evaluation": "Repeated MVP Security Reliability Benchmark",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology": {
            "scenario_source": "evaluation.run_evaluation.SCENARIOS",
            "repetitions_per_scenario": repetitions,
            "database": "Isolated temporary SQLite database per execution",
            "policy_engine": "Actual configured OPA policy evaluator",
            "tool_execution": "Simulated only",
            "latency_scope": "Scenario timing from run_scenario; temporary database setup is excluded.",
            "percentile_method": "Nearest-rank",
        },
        "summary": summary,
        "scenario_summaries": scenario_summaries,
        "results": results,
        "limitations": [
            "This deterministic MVP benchmark is not a formal security proof.",
            "The trusted provenance document is a test-only fixture.",
            "All tool operations are simulated; no real email is sent.",
            "Results are local to this machine and software configuration.",
            "Thirty repetitions per scenario are a small repeatability sample, not production-scale evidence.",
            "Latency is scenario-level gateway latency, not throughput or concurrent-load performance.",
        ],
    }
    JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_csv(results)

    latency = summary["latency"]
    print("\n--------------- OVERALL SUMMARY ---------------")
    print(f"Executions : {summary['total_executions']}")
    print(f"Passed     : {summary['passed']}")
    print(f"Failed     : {summary['failed']}")
    print(f"Errors     : {summary['errors']}")
    print(f"Pass rate  : {summary['pass_rate_percent']}%")
    print(f"Decision match rate : {summary['decision_match_rate_percent']}%")
    print(f"Broker action match rate : {summary['broker_action_match_rate_percent']}%")
    print(f"Denied-action enforcement check rate : {summary['denied_action_enforcement_check_rate_percent']}%")
    print("\n--------------- LATENCY (ms) ---------------")
    print(f"Mean   : {latency['mean_ms']}")
    print(f"Median : {latency['median_ms']}")
    print(f"P95    : {latency['p95_ms']}")
    print(f"Min    : {latency['min_ms']}")
    print(f"Max    : {latency['max_ms']}")
    print(f"StdDev : {latency['stdev_ms']}")
    print(f"\nJSON report : {JSON_PATH}")
    print(f"CSV report  : {CSV_PATH}")

    if summary["failed"] or summary["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
