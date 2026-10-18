"""
Project Atlas - Database Permissions & Least Privilege Verification (D1)
Tests atlas_readonly user write denial and table restrictions.
"""

import json
import os
import pymysql

EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "e2e", "phase4")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def test_permissions():
    print("Testing atlas_readonly database account permissions...")
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3307,
        user="atlas_readonly",
        password="atlas_readonly_secure_password",
        database="project_atlas"
    )

    results = {}

    with conn.cursor() as cur:
        # 1. Permitted SELECT on reports
        cur.execute("SELECT COUNT(*) FROM reports")
        results["select_reports_count"] = cur.fetchone()[0]
        results["select_reports_status"] = "PERMITTED"

        # 2. Denied INSERT on reports
        try:
            cur.execute("INSERT INTO reports (id, title, publisher, published_date, sector, access_type) VALUES ('R-999', 'Fake', 'Hacker', '2026-01-01', 'Test', 'paid')")
            results["insert_reports"] = "FAIL_UNEXPECTED_PASS"
        except Exception as e:
            results["insert_reports"] = f"DENIED: {type(e).__name__} - {e}"

        # 3. Denied UPDATE on reports
        try:
            cur.execute("UPDATE reports SET title = 'Hacked' WHERE id = 'R-101'")
            results["update_reports"] = "FAIL_UNEXPECTED_PASS"
        except Exception as e:
            results["update_reports"] = f"DENIED: {type(e).__name__} - {e}"

        # 4. Denied DELETE on reports
        try:
            cur.execute("DELETE FROM reports WHERE id = 'R-101'")
            results["delete_reports"] = "FAIL_UNEXPECTED_PASS"
        except Exception as e:
            results["delete_reports"] = f"DENIED: {type(e).__name__} - {e}"

        # 5. Denied DROP TABLE reports
        try:
            cur.execute("DROP TABLE reports")
            results["drop_reports"] = "FAIL_UNEXPECTED_PASS"
        except Exception as e:
            results["drop_reports"] = f"DENIED: {type(e).__name__} - {e}"

        # 6. Denied SELECT on clients table
        try:
            cur.execute("SELECT * FROM clients")
            results["select_clients"] = "FAIL_UNEXPECTED_PASS"
        except Exception as e:
            results["select_clients"] = f"DENIED: {type(e).__name__} - {e}"

        # 7. Denied SELECT on audit_events table
        try:
            cur.execute("SELECT * FROM audit_events")
            results["select_audit_events"] = "FAIL_UNEXPECTED_PASS"
        except Exception as e:
            results["select_audit_events"] = f"DENIED: {type(e).__name__} - {e}"

    conn.close()

    # Save evidence
    evidence_path = os.path.join(EVIDENCE_DIR, "d1_db_permissions.json")
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Evidence saved to {evidence_path}")
    for k, v in results.items():
        print(f"  {k}: {v}")

    # Assert all write operations and sensitive tables were denied
    assert results["select_reports_status"] == "PERMITTED"
    assert "DENIED" in results["insert_reports"]
    assert "DENIED" in results["update_reports"]
    assert "DENIED" in results["delete_reports"]
    assert "DENIED" in results["drop_reports"]
    assert "DENIED" in results["select_clients"]
    assert "DENIED" in results["select_audit_events"]
    print("\nALL D1 LEAST-PRIVILEGE PERMISSION CHECKS PASSED!")

if __name__ == "__main__":
    test_permissions()
