"""Load test: 100 concurrent users against key endpoints.

Usage:
    python -m scripts.load_test [--base-url http://localhost:8000] [--users 100]
"""
import argparse
import asyncio
import statistics
import time

import httpx

ENDPOINTS = [
    ("GET", "/healthz"),
    ("GET", "/opportunities?q=beasiswa&limit=10"),
    ("GET", "/opportunities?category=beasiswa&limit=10"),
    ("GET", "/opportunities?location=Jakarta&limit=10"),
]

RESULTS: list[dict] = []


async def hit(client: httpx.AsyncClient, method: str, url: str, user_id: int):
    start = time.perf_counter()
    try:
        resp = await client.request(method, url)
        elapsed_ms = (time.perf_counter() - start) * 1000
        RESULTS.append({
            "user": user_id,
            "endpoint": url,
            "status": resp.status_code,
            "latency_ms": round(elapsed_ms, 1),
            "error": None,
        })
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        RESULTS.append({
            "user": user_id,
            "endpoint": url,
            "status": 0,
            "latency_ms": round(elapsed_ms, 1),
            "error": str(e),
        })


async def run_load_test(base_url: str, num_users: int):
    print(f"Load test: {num_users} concurrent users x {len(ENDPOINTS)} endpoints")
    print(f"Target: {base_url}")
    print("-" * 60)

    async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
        tasks = []
        for i in range(num_users):
            method, path = ENDPOINTS[i % len(ENDPOINTS)]
            tasks.append(hit(client, method, path, i))
        await asyncio.gather(*tasks)

    latencies = [r["latency_ms"] for r in RESULTS]
    errors = [r for r in RESULTS if r["error"] or r["status"] >= 400]
    latencies_sorted = sorted(latencies)

    p50 = latencies_sorted[len(latencies_sorted) // 2]
    p95_idx = int(len(latencies_sorted) * 0.95)
    p95 = latencies_sorted[min(p95_idx, len(latencies_sorted) - 1)]
    p99_idx = int(len(latencies_sorted) * 0.99)
    p99 = latencies_sorted[min(p99_idx, len(latencies_sorted) - 1)]

    print(f"Total requests:  {len(RESULTS)}")
    print(f"Errors:          {len(errors)}")
    print(f"Success rate:    {(len(RESULTS) - len(errors)) / len(RESULTS) * 100:.1f}%")
    print(f"Latency avg:     {statistics.mean(latencies):.1f} ms")
    print(f"Latency p50:     {p50:.1f} ms")
    print(f"Latency p95:     {p95:.1f} ms")
    print(f"Latency p99:     {p99:.1f} ms")
    print(f"Latency max:     {max(latencies):.1f} ms")
    print("-" * 60)

    if errors:
        print("Errors:")
        for e in errors[:10]:
            print(f"  [{e['status']}] {e['endpoint']}: {e['error']}")

    targets = {"p95": 5000, "success_rate": 95.0}
    success_rate = (len(RESULTS) - len(errors)) / len(RESULTS) * 100
    passed = p95 <= targets["p95"] and success_rate >= targets["success_rate"]
    print(f"\nTarget p95 < {targets['p95']}ms: {'PASS' if p95 <= targets['p95'] else 'FAIL'}")
    print(f"Target success >= {targets['success_rate']}%: {'PASS' if success_rate >= targets['success_rate'] else 'FAIL'}")
    print(f"Overall: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--users", type=int, default=100)
    args = parser.parse_args()
    asyncio.run(run_load_test(args.base_url, args.users))
