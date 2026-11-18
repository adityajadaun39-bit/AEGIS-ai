"""Concurrent Stress & Load Testing Benchmark for AEGIS.

Simulates 50+ concurrent autonomous agent requests to profile P95/P99 latency
and verify zero database locking under SQLite concurrent write access.
"""

from __future__ import annotations

import concurrent.futures
import math
import statistics
import time
from pathlib import Path

from unittest.mock import patch
from backend.schemas.actions import ActionRequest
from backend.security.gateway import execute_action
from backend.security import policy_engine


def make_load_request(i: int) -> ActionRequest:
    return ActionRequest(
        action="read_document",
        agent_id="research_agent",
        resource="public_report.pdf",
    )


def execute_single_worker(request_id: int) -> dict:
    req = make_load_request(request_id)
    start = time.perf_counter_ns()
    if not policy_engine.find_opa():
        with patch(
            "backend.security.gateway.evaluate_policy",
            side_effect=policy_engine.evaluate_in_process_policy,
        ):
            res = execute_action(req)
    else:
        res = execute_action(req)
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    return {
        "id": request_id,
        "success": res.get("success", False),
        "decision": res.get("decision"),
        "latency_ms": elapsed_ms,
    }


def run_load_benchmark(concurrency: int = 50) -> dict:
    print(f"\n========== AEGIS CONCURRENCY LOAD BENCHMARK ==========")
    print(f"Simulating {concurrency} concurrent agent action proposals...\n")

    start_total = time.perf_counter()
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(execute_single_worker, i) for i in range(concurrency)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    total_time = time.perf_counter() - start_total
    latencies = [r["latency_ms"] for r in results]
    successes = sum(1 for r in results if r["success"])

    latencies.sort()
    p95_idx = max(0, math.ceil(0.95 * len(latencies)) - 1)
    p99_idx = max(0, math.ceil(0.99 * len(latencies)) - 1)

    print(f"--------------- RESULTS ---------------")
    print(f"Total Requests : {concurrency}")
    print(f"Successful     : {successes} ({successes / concurrency * 100:.1f}%)")
    print(f"Total Duration : {total_time:.3f} s")
    print(f"Throughput     : {concurrency / total_time:.1f} req/s")
    print(f"Mean Latency   : {statistics.mean(latencies):.2f} ms")
    print(f"Median Latency : {statistics.median(latencies):.2f} ms")
    print(f"P95 Latency    : {latencies[p95_idx]:.2f} ms")
    print(f"P99 Latency    : {latencies[p99_idx]:.2f} ms")
    print(f"Min Latency    : {min(latencies):.2f} ms")
    print(f"Max Latency    : {max(latencies):.2f} ms")
    print(f"=======================================================\n")

    return {
        "concurrency": concurrency,
        "success_rate": successes / concurrency,
        "mean_ms": statistics.mean(latencies),
        "p95_ms": latencies[p95_idx],
        "p99_ms": latencies[p99_idx],
    }


if __name__ == "__main__":
    run_load_benchmark(50)
