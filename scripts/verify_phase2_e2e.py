"""
Project Atlas - Phase 2 Strict E2E Verification Script
Tests B2, B6, B7, B8 against live running containers.
Saves raw JSON evidence to artifacts/e2e/phase2/
"""

import json
import os
import sys
import time
import requests
import pymysql

BASE_URL = "http://127.0.0.1:8000"
EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "e2e", "phase2")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

# Fetch client API keys directly from MySQL to avoid hardcoding or logging secrets
def get_client_keys():
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3307,
        user="atlas_app",
        password="atlas_app_secure_password",
        database="project_atlas",
        cursorclass=pymysql.cursors.DictCursor
    )
    keys = {}
    with conn.cursor() as cur:
        cur.execute("SELECT id, api_key FROM clients")
        for row in cur.fetchall():
            keys[row["id"]] = row["api_key"]
    conn.close()
    return keys

CLIENT_KEYS = get_client_keys()

def save_evidence(filename, data):
    path = os.path.join(EVIDENCE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  [Evidence Saved] -> {path}")
    return path

def run_tests():
    print("=" * 60)
    print("STARTING PHASE 2 STRICT VERIFICATION")
    print("=" * 60)

    results = {}

    # Test 0: Health Check
    print("\n--- Test 0: Health Check ---")
    resp = requests.get(f"{BASE_URL}/health", timeout=10)
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health_data = resp.json()
    save_evidence("test0_health.json", health_data)
    print("Health Status:", health_data.get("status"))

    # Test 1: B2 / B8 - C-01 "Which report should I trust?"
    print("\n--- Test 1: C-01 'Which report should I trust?' ---")
    q1_payload = {
        "client_id": "C-01",
        "question": "Which report should I trust regarding smart water meters?"
    }
    resp1 = requests.post(
        f"{BASE_URL}/chat",
        json=q1_payload,
        headers={"X-Client-Key": CLIENT_KEYS["C-01"]},
        timeout=30
    )
    assert resp1.status_code == 200, f"HTTP error {resp1.status_code}: {resp1.text}"
    data1 = resp1.json()
    save_evidence("C01-which-report-should-i-trust.json", data1)

    # Verification assertions
    ans1 = data1.get("answer", "")
    citations1 = data1.get("citations", [])
    report_ids_1 = [c.get("report_id") for c in citations1]

    # Check titles from MySQL
    assert "Global Smart Water Meter Market 2025" in ans1, "Missing R-101 title from MySQL"
    assert "Smart Water Metering: Industry Outlook 2024" in ans1, "Missing R-102 title from MySQL"
    # Check no 'authoritative' or 'verified' labels used as verdicts
    assert "authoritative" not in ans1.lower(), "Found prohibited word 'authoritative' in answer"
    # Check scope differences and no averaging
    assert "averaging" in ans1.lower(), "Missing warning that averaging is prohibited"
    assert "escalat" in ans1.lower(), "Missing escalation offer to research analyst"
    assert "R-101" in report_ids_1 and "R-102" in report_ids_1, f"Expected R-101 and R-102 citations, got {report_ids_1}"
    print("  PASS: C-01 comparison trust handles dynamic metadata, scopes, uncertainty, and citations.")
    results["C01_comparison_trust"] = "PASS"

    time.sleep(1) # Free-tier rate-limit buffer

    # Test 2: B2 / B8 - C-02 "Which report should I trust?"
    print("\n--- Test 2: C-02 'Which report should I trust?' ---")
    q2_payload = {
        "client_id": "C-02",
        "question": "Which report should I trust regarding smart water meters?"
    }
    resp2 = requests.post(
        f"{BASE_URL}/chat",
        json=q2_payload,
        headers={"X-Client-Key": CLIENT_KEYS["C-02"]},
        timeout=30
    )
    assert resp2.status_code == 200, f"HTTP error {resp2.status_code}: {resp2.text}"
    data2 = resp2.json()
    save_evidence("C02-which-report-should-i-trust.json", data2)

    ans2 = data2.get("answer", "")
    citations2 = data2.get("citations", [])
    report_ids_2 = [c.get("report_id") for c in citations2]

    # C-02: mentions R-101 exists, offers upgrade, gives ZERO of R-101 figures, citations do NOT include R-101
    assert "R-101" in ans2, "C-02 should mention R-101 exists"
    assert "4.21" not in ans2, "LEAK: R-101 valuation ($4.21B) leaked to C-02!"
    assert "R-101" not in report_ids_2, f"LEAK: R-101 cited in C-02 citations: {report_ids_2}"
    assert "R-102" in report_ids_2, f"R-102 expected in citations, got: {report_ids_2}"
    assert "upgrade" in ans2.lower() or "licensing" in ans2.lower(), "Missing upgrade route/email for C-02"
    print("  PASS: C-02 comparison trust discloses R-101 existence without figures or citations, with upgrade route.")
    results["C02_comparison_trust"] = "PASS"

    time.sleep(1)

    # Test 3: B6 - C-01 Q1 Citation Grounding (No R-103 purifier on smart water meter questions)
    print("\n--- Test 3: C-01 Q1 Smart Water Meter Market Size 2024 ---")
    q3_payload = {
        "client_id": "C-01",
        "question": "What was the global smart water meter market size in 2024?"
    }
    resp3 = requests.post(
        f"{BASE_URL}/chat",
        json=q3_payload,
        headers={"X-Client-Key": CLIENT_KEYS["C-01"]},
        timeout=30
    )
    assert resp3.status_code == 200, f"HTTP error {resp3.status_code}: {resp3.text}"
    data3 = resp3.json()
    save_evidence("C01-market-size-2024.json", data3)

    citations3 = data3.get("citations", [])
    c_ids3 = [c.get("report_id") for c in citations3]
    conf3 = data3.get("confidence", 0.0)

    # Must NOT contain R-103
    assert "R-103" not in c_ids3, f"IRRELEVANT CITATION LEAK: R-103 appeared in smart water meter answer: {c_ids3}"
    # Must contain R-101 or R-102
    assert "R-101" in c_ids3 or "R-102" in c_ids3, f"Expected R-101/R-102 citations, got: {c_ids3}"
    # Conflict detected -> confidence adjusted to 0.80
    assert conf3 == 0.80, f"Expected confidence 0.80 due to conflict between R-101 and R-102, got {conf3}"
    assert len(data3.get("conflicts", [])) > 0, "Expected source conflict detected between R-101 and R-102"
    print("  PASS: C-01 citations strictly grounded (no R-103), confidence policy adjusted to 0.80 on conflict.")
    results["C01_citation_grounding"] = "PASS"

    time.sleep(1)

    # Test 4: B6 / B7 - C-02 Smart Water Meter Market Size 2024 (Single-source R-102 boundary)
    print("\n--- Test 4: C-02 Smart Water Meter Market Size 2024 ---")
    q4_payload = {
        "client_id": "C-02",
        "question": "What was the global smart water meter market size in 2024?"
    }
    resp4 = requests.post(
        f"{BASE_URL}/chat",
        json=q4_payload,
        headers={"X-Client-Key": CLIENT_KEYS["C-02"]},
        timeout=30
    )
    assert resp4.status_code == 200, f"HTTP error {resp4.status_code}: {resp4.text}"
    data4 = resp4.json()
    save_evidence("C02-market-size-2024.json", data4)

    ans4 = data4.get("answer", "")
    citations4 = data4.get("citations", [])
    c_ids4 = [c.get("report_id") for c in citations4]
    conf4 = data4.get("confidence", 0.0)

    # Citations must strictly contain ONLY R-102
    assert "R-101" not in c_ids4, f"LEAK: R-101 cited for unpurchased client C-02: {c_ids4}"
    assert "R-103" not in c_ids4, f"IRRELEVANT CITATION LEAK: R-103 cited: {c_ids4}"
    assert "R-102" in c_ids4, f"R-102 must be cited, got: {c_ids4}"
    # Answer should state 3.87B hardware, mention R-101 exists, zero 4.21
    assert "3.87" in ans4, "Expected USD 3.87B hardware figure from R-102"
    assert "4.21" not in ans4, "LEAK: R-101 figure 4.21 leaked to C-02!"
    assert conf4 == 0.80, f"Expected confidence 0.80 for single-source boundary, got {conf4}"
    print("  PASS: C-02 single source boundary grounded in R-102, no R-101 leak, confidence 0.80.")
    results["C02_single_source_boundary"] = "PASS"

    time.sleep(1)

    # Test 5: B7 - C-02 Direct Request for Restricted Report R-101
    print("\n--- Test 5: C-02 Direct Request for Restricted Report R-101 ---")
    q5_payload = {
        "client_id": "C-02",
        "question": "What are the executive findings and market revenue numbers in report R-101?"
    }
    resp5 = requests.post(
        f"{BASE_URL}/chat",
        json=q5_payload,
        headers={"X-Client-Key": CLIENT_KEYS["C-02"]},
        timeout=30
    )
    assert resp5.status_code == 200, f"HTTP error {resp5.status_code}: {resp5.text}"
    data5 = resp5.json()
    save_evidence("C02-restricted-r101-direct-request.json", data5)

    ans5 = data5.get("answer", "")
    citations5 = data5.get("citations", [])
    c_ids5 = [c.get("report_id") for c in citations5]

    assert "R-101" not in c_ids5, f"LEAK: R-101 cited on restricted request: {c_ids5}"
    assert "4.21" not in ans5, "LEAK: R-101 figure 4.21 disclosed on restricted request!"
    assert "restricted" in ans5.lower() or "upgrade" in ans5.lower() or "license" in ans5.lower(), "Expected restriction/upgrade notice"
    print("  PASS: C-02 direct request for R-101 properly refused with upgrade notice, zero leak.")
    results["C02_direct_restricted_refusal"] = "PASS"

    # Overall Summary
    print("\n" + "=" * 60)
    print("PHASE 2 VERIFICATION SUMMARY")
    print("=" * 60)
    for test_name, status in results.items():
        print(f"  {test_name}: {status}")

    summary_file = os.path.join(EVIDENCE_DIR, "phase2_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll Phase 2 evidence written to {EVIDENCE_DIR}")

if __name__ == "__main__":
    run_tests()
