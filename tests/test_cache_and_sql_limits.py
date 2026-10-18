"""
Project Atlas - Automated Tests for Phase 5:
1. Derived Values: Multi-period base-year scenario disclosure (5-period vs. 6-period).
2. Cache Isolation: Cryptographic tenant and entitlement key isolation and fresh-evaluation integrity.
3. SQL Security & Limits: Read-only enforcement, SELECT-only validation, injection rejection, table whitelisting, and 50-row bounds.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.cache import TenantIsolatedCache, response_cache
from app.services.ingestion import IngestionService
from app.tools.sql_tool import SafeSQLTool, MAX_SQL_ROWS
from app.tools.calculator import MarketCalculator
from app.agent.workflow import AgentWorkflow


@pytest.fixture(scope="module", autouse=True)
def setup_index():
    """Seed vector database before running workflow tests."""
    reports_dir = str(Path(__file__).parent.parent / "reports")
    IngestionService.ingest_directory(reports_dir, collection_name="report_chunks")


# ==============================================================================
# 1. DERIVED VALUES & BASE-YEAR AMBIGUITY TESTS
# ==============================================================================

def test_derived_values_explicit_multi_period_disclosure():
    """Verify that calculation output explicitly discloses both 5- and 6-period interpretations."""
    calc = MarketCalculator.compute_apac_smart_water_meter_2030()

    # 1. Assert both 5-period and 6-period values exist
    assert calc["derived_value"] == 2.72, "Standard 5-period compounding must equal 2.72B"
    assert calc["alternative_6_period_value"] == 3.02, "Alternative 6-period compounding must equal 3.02B"

    # 2. Assert explicit disclosure of base-year ambiguity
    assert "base_year_ambiguity" in calc
    ambiguity_text = calc["base_year_ambiguity"].lower()
    assert "5 periods" in ambiguity_text or "5-period" in ambiguity_text or "5" in ambiguity_text
    assert "6" in ambiguity_text
    assert "2.72" in calc["base_year_ambiguity"]
    assert "3.02" in calc["base_year_ambiguity"]

    # 3. Assert assumptions list discloses both scenarios
    assumptions_joined = " ".join(calc["assumptions"])
    assert "5 annual periods" in assumptions_joined or "5" in assumptions_joined
    assert "3.02" in assumptions_joined


# ==============================================================================
# 2. CACHE ISOLATION & FRESH EVALUATION TESTS
# ==============================================================================

def test_cache_keys_are_tenant_and_entitlement_isolated():
    """Prove that identical questions for different tenants produce completely distinct cache keys."""
    cache = TenantIsolatedCache()
    question = "What is the 2024 market size for smart water meters?"

    # Client C-01 has access to R-101 and R-102
    key_c01 = cache.compute_cache_key("C-01", ["R-101", "R-102"], question)

    # Client C-02 has access only to R-102
    key_c02 = cache.compute_cache_key("C-02", ["R-102"], question)

    # Assert cache keys are strictly distinct
    assert key_c01 != key_c02, "Cache keys for C-01 and C-02 must never collide"

    # Prove that caching data for C-01 never returns to C-02
    mock_c01_data = {
        "answer": "R-101 is $4.21B, R-102 is $3.87B",
        "citations": [{"report_id": "R-101"}, {"report_id": "R-102"}]
    }
    cache.set("C-01", ["R-101", "R-102"], question, mock_c01_data)

    # C-01 gets a cache hit
    hit_c01 = cache.get("C-01", ["R-101", "R-102"], question)
    assert hit_c01 is not None
    assert hit_c01["answer"] == mock_c01_data["answer"]

    # C-02 gets a cache miss (zero leakage)
    hit_c02 = cache.get("C-02", ["R-102"], question)
    assert hit_c02 is None, "Client C-02 must NEVER receive Client C-01's cached response"


def test_entitlement_change_invalidates_cache_key():
    """Prove that if a client's entitlements change, the cache key automatically changes."""
    cache = TenantIsolatedCache()
    question = "What is the 2024 market size for smart water meters?"

    key_initial = cache.compute_cache_key("C-02", ["R-102"], question)
    key_upgraded = cache.compute_cache_key("C-02", ["R-101", "R-102"], question)

    assert key_initial != key_upgraded, "Upgrading or modifying entitlements must produce a distinct key"


def test_fresh_evaluation_prevents_cross_tenant_bleed_in_workflow():
    """
    Verify that back-to-back workflow execution for C-01 and C-02 on the same question
    evaluates fresh against live entitlements and leaves zero residual leakage.
    """
    question = "What is the 2024 market size for smart water meters according to R-101 and R-102?"

    # 1. Run for C-01 (Authorized for both R-101 and R-102)
    resp_c01 = AgentWorkflow.process_chat(
        client_id="C-01",
        question=question,
        conversation_id="test-conv-fresh-1",
        request_id="req-test-fresh-c01"
    )
    assert "4.21" in resp_c01["answer"]
    assert "3.87" in resp_c01["answer"]

    # 2. Run immediately for C-02 (Authorized ONLY for R-102)
    resp_c02 = AgentWorkflow.process_chat(
        client_id="C-02",
        question=question,
        conversation_id="test-conv-fresh-2",
        request_id="req-test-fresh-c02"
    )

    # Assert C-02 does NOT receive R-101 figure $4.21B
    assert "4.21" not in resp_c02["answer"], "Client C-02 must NOT receive R-101 data even if queried immediately after C-01"
    # Assert C-02's response properly references R-102 or refusal/upgrade
    c02_cited_reports = [c.get("report_id") for c in resp_c02.get("citations", [])]
    assert "R-101" not in c02_cited_reports, "C-02 citations must never include R-101"


# ==============================================================================
# 3. SQL SECURITY, ROW BOUNDS & INJECTION REJECTION TESTS
# ==============================================================================

def test_sql_tool_rejects_write_statements():
    """Verify that all write/modification operations are strictly rejected."""
    write_queries = [
        "DELETE FROM reports WHERE id = 'R-101'",
        "UPDATE reports SET title = 'Compromised' WHERE id = 'R-101'",
        "INSERT INTO reports (id, title) VALUES ('R-999', 'Fake Report')",
        "TRUNCATE TABLE reports",
        "REPLACE INTO reports (id, title) VALUES ('R-101', 'Replacement')"
    ]
    for q in write_queries:
        res = SafeSQLTool.execute_custom_safe_query(q)
        assert res["success"] is False, f"Query '{q}' should have been rejected"
        assert "Security Violation" in res["error"]


def test_sql_tool_rejects_ddl_and_dcl_statements():
    """Verify that schema modification and privilege escalation queries are rejected."""
    admin_queries = [
        "DROP TABLE reports",
        "ALTER TABLE reports ADD COLUMN backdoor VARCHAR(255)",
        "CREATE TABLE backdoor (id INT)",
        "GRANT ALL PRIVILEGES ON *.* TO 'hacker'@'%'",
        "REVOKE SELECT ON reports FROM 'atlas_readonly'@'%'"
    ]
    for q in admin_queries:
        res = SafeSQLTool.execute_custom_safe_query(q)
        assert res["success"] is False, f"Query '{q}' should have been rejected"
        assert "Security Violation" in res["error"]


def test_sql_tool_rejects_multi_statement_injection():
    """Verify that chained multi-statement queries (e.g., SELECT ...; DROP ...) are rejected."""
    chained_queries = [
        "SELECT * FROM reports; DROP TABLE reports;",
        "SELECT id FROM reports; DELETE FROM market_metrics WHERE 1=1;",
        "SELECT * FROM reports; -- comment"
    ]
    for q in chained_queries:
        res = SafeSQLTool.execute_custom_safe_query(q)
        assert res["success"] is False, f"Chained query '{q}' should have been rejected"
        assert "Security Violation" in res["error"]


def test_sql_tool_rejects_sensitive_table_access():
    """Verify that queries targeting clients, credentials, or audit logs are rejected."""
    sensitive_queries = [
        "SELECT * FROM clients",
        "SELECT api_key, contact_email FROM clients",
        "SELECT * FROM user_feedback",
        "SELECT * FROM escalation_tickets",
        "SELECT * FROM audit_events",
        "SELECT * FROM information_schema.tables"
    ]
    for q in sensitive_queries:
        res = SafeSQLTool.execute_custom_safe_query(q)
        assert res["success"] is False, f"Sensitive query '{q}' should have been rejected"
        assert "Security Violation" in res["error"]


def test_sql_tool_enforces_row_limit():
    """Verify that SafeSQLTool enforces maximum 50 rows on analytical queries."""
    assert MAX_SQL_ROWS == 50

    # Query with missing limit is auto-clamped
    res = SafeSQLTool.execute_custom_safe_query("SELECT id, title FROM reports")
    assert res["success"] is True
    assert res["row_count"] <= 50
    assert len(res["rows"]) <= 50
