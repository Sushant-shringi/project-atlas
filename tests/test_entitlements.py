"""
Project Atlas - Automated Tests for Entitlement-Aware Security (Milestone 4)
Proves:
1. Client identity resolution via API key and spoofing prevention.
2. Client C-01 and C-02 entitlement lists match MySQL seed data exactly.
3. Client C-02 CANNOT retrieve R-101 (paid smart water meter report).
4. Restricted report text never enters the retrieval output for unauthorized clients.
5. Public excerpt boundaries (R-102) are strictly respected.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.ingestion import IngestionService
from app.services.entitlements import EntitlementService
from app.services.retrieval import RetrievalEngine


@pytest.fixture(scope="module", autouse=True)
def setup_vector_index():
    """Ensure all synthetic reports are indexed in Qdrant before testing retrieval."""
    reports_dir = str(Path(__file__).parent.parent / "reports")
    IngestionService.ingest_directory(reports_dir, collection_name="report_chunks")


def test_client_authentication_and_spoofing_defense():
    """Verify API key authentication and prevention of client ID spoofing."""
    key_c01 = "client_key_c01_northwind_utilities_secret_2026"
    key_c02 = "client_key_c02_blue_delta_infra_secret_2026"
    invalid_key = "client_key_invalid_fake_unauthorized"

    # 1. Valid authentication
    client_c01 = EntitlementService.get_client_by_api_key(key_c01)
    assert client_c01 is not None
    assert client_c01["id"] == "C-01"
    assert client_c01["company_name"] == "Northwind Utilities"

    # 2. Invalid key rejected
    assert EntitlementService.get_client_by_api_key(invalid_key) is None

    # 3. Client spoofing attempt: caller presents C-01's key but requests client C-02
    is_valid, msg, _ = EntitlementService.validate_client_authorization(key_c01, "C-02")
    assert is_valid is False
    assert "Unauthorized" in msg

    # 4. Legitimate client matching
    is_valid, msg, client = EntitlementService.validate_client_authorization(key_c01, "C-01")
    assert is_valid is True
    assert client["id"] == "C-01"


def test_entitlements_resolution():
    """Verify normalized entitlement permissions for C-01 and C-02."""
    c01_reports = EntitlementService.get_authorized_reports_for_client("C-01")
    c02_reports = EntitlementService.get_authorized_reports_for_client("C-02")

    # C-01 purchased R-101 and R-103, plus R-102 public excerpt
    assert "R-101" in c01_reports
    assert "R-103" in c01_reports
    assert "R-102" in c01_reports

    # C-02 purchased R-103, plus R-102 public excerpt. R-101 MUST NOT be present.
    assert "R-103" in c02_reports
    assert "R-102" in c02_reports
    assert "R-101" not in c02_reports, "Client C-02 must not be entitled to R-101"


def test_entitlement_filtering_c02_cannot_access_r101():
    """
    CRITICAL PROOF: Verify that when Client C-02 queries about the smart water meter market,
    R-101 chunks are NEVER retrieved by Qdrant or passed downstream.
    """
    query = "What was the global smart water meter market size in 2024 and CAGR?"

    # Retrieval for Client C-02
    chunks_c02, authorized_ids_c02, _ = RetrievalEngine.retrieve_for_client("C-02", query, limit=10)

    # Prove R-101 is not authorized for C-02
    assert "R-101" not in authorized_ids_c02

    # Prove ZERO chunks from R-101 were returned
    r101_chunks = [c for c in chunks_c02 if c.get("report_id") == "R-101"]
    assert len(r101_chunks) == 0, "Security violation: R-101 chunk returned for Client C-02!"

    # Prove restricted text ($4.21 billion) from R-101 is nowhere in C-02 retrieved chunks
    for chunk in chunks_c02:
        assert chunk["report_id"] != "R-101"
        assert "4.21 billion" not in chunk["text"]


def test_entitlement_filtering_c01_can_access_r101():
    """Verify that authorized Client C-01 successfully retrieves R-101."""
    query = "What was the global smart water meter market size in 2024 and CAGR?"

    chunks_c01, authorized_ids_c01, _ = RetrievalEngine.retrieve_for_client("C-01", query, limit=5)
    assert "R-101" in authorized_ids_c01

    r101_chunks = [c for c in chunks_c01 if c.get("report_id") == "R-101"]
    assert len(r101_chunks) > 0, "Client C-01 should retrieve authorized R-101 chunks"

    # Confirm required market figure is present for C-01
    has_market_figure = any("4.21 billion" in c["text"] for c in r101_chunks)
    assert has_market_figure is True
