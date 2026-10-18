"""
Project Atlas - SQL Execution Timeout Verification (D1)
Tests that long-running/runaway queries are terminated by execution read timeout limits.
"""

import json
import os
import time
import pymysql

EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "e2e", "phase4")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def test_sql_timeout():
    print("Testing SQL connection read timeout enforcement (2.0s limit)...")
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3307,
        user="atlas_readonly",
        password="atlas_readonly_secure_password",
        database="project_atlas",
        read_timeout=2
    )

    results = {}

    with conn.cursor() as cur:
        # Test 1: Fast query (should complete in < 50ms)
        start = time.time()
        cur.execute("SELECT COUNT(*) FROM reports")
        fast_count = cur.fetchone()[0]
        fast_duration = round(time.time() - start, 3)
        results["fast_query"] = {
            "query": "SELECT COUNT(*) FROM reports",
            "duration_seconds": fast_duration,
            "status": "COMPLETED",
            "count": fast_count
        }

        # Test 2: Slow query (SLEEP 5) with 2s limit (should be aborted by read_timeout)
        start = time.time()
        timeout_triggered = False
        timeout_error = None
        try:
            cur.execute("SELECT SLEEP(5)")
            results["slow_query"] = {
                "status": "FAIL_UNEXPECTED_COMPLETION",
                "duration_seconds": round(time.time() - start, 3)
            }
        except Exception as e:
            timeout_triggered = True
            timeout_error = str(e)
            results["slow_query"] = {
                "query": "SELECT SLEEP(5)",
                "duration_seconds": round(time.time() - start, 3),
                "status": "INTERRUPTED_BY_TIMEOUT",
                "error": f"{type(e).__name__} - {timeout_error}"
            }

    conn.close()

    evidence_path = os.path.join(EVIDENCE_DIR, "d1_sql_timeout.json")
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Evidence saved to {evidence_path}")
    print(json.dumps(results, indent=2))

    assert timeout_triggered, "Expected query to be interrupted by read timeout"
    assert "timeout" in timeout_error.lower() or "lost connection" in timeout_error.lower() or "timed out" in timeout_error.lower(), f"Unexpected error: {timeout_error}"
    print("\nALL D1 SQL TIMEOUT CHECKS PASSED!")

if __name__ == "__main__":
    test_sql_timeout()
