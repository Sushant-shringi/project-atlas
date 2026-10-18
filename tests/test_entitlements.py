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
from types import SimpleNamespace

import app.services.qdrant_service as qdrant_service
from app.services.qdrant_service import QdrantService
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


def test_upgrade_contact_details_and_zero_leakage_c02():
    """
    Regression Test: For C-02 asking about R-101:
    1. Any URL or email in the answer must equal a configured value or be absent.
    2. Prohibited valuation figure 4.21 must NEVER appear.
    3. When contact config is empty, the fallback text directs to CMR account executive or analyst.
    """
    import os
    import re
    from app.agent.workflow import AgentWorkflow

    # Case A: When contact details are empty
    orig_email = os.environ.get("UPGRADE_CONTACT_EMAIL")
    orig_url = os.environ.get("UPGRADE_PORTAL_URL")
    try:
        os.environ["UPGRADE_CONTACT_EMAIL"] = ""
        os.environ["UPGRADE_PORTAL_URL"] = ""

        res_empty = AgentWorkflow.process_chat(
            client_id="C-02",
            question="What was the global smart water meter market size in 2024 according to report R-101?"
        )
        ans_empty = res_empty.get("answer", "")

        # Assert no 4.21
        assert "4.21" not in ans_empty, "Prohibited value 4.21 leaked to C-02"

        # Assert expected fallback wording
        assert "CMR account executive or an analyst" in ans_empty

        # Assert no email or URL present
        emails_empty = [em.rstrip(".,;:)") for em in re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", ans_empty)]
        urls_empty = [u.rstrip(".,;:)") for u in re.findall(r"https?://\S+", ans_empty)]
        assert len(emails_empty) == 0, f"Unexpected email found in answer: {emails_empty}"
        assert len(urls_empty) == 0, f"Unexpected URL found in answer: {urls_empty}"

        # Case B: When contact details are configured
        os.environ["UPGRADE_CONTACT_EMAIL"] = "licensing@example.com"
        os.environ["UPGRADE_PORTAL_URL"] = "https://example.com/atlas/request-access"

        res_configured = AgentWorkflow.process_chat(
            client_id="C-02",
            question="What was the global smart water meter market size in 2024 according to report R-101?"
        )
        ans_configured = res_configured.get("answer", "")

        assert "4.21" not in ans_configured

        emails_conf = [em.rstrip(".,;:)") for em in re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", ans_configured)]
        urls_conf = [u.rstrip(".,;:)") for u in re.findall(r"https?://[^\s)\]]+", ans_configured)]

        for em in emails_conf:
            assert em == "licensing@example.com", f"Invented email found: {em}"
        for u in urls_conf:
            assert u.startswith("https://example.com/atlas/request-access"), f"Invented URL found: {u}"

    finally:
        # Restore environment
        if orig_email is not None:
            os.environ["UPGRADE_CONTACT_EMAIL"] = orig_email
        else:
            os.environ.pop("UPGRADE_CONTACT_EMAIL", None)

        if orig_url is not None:
            os.environ["UPGRADE_PORTAL_URL"] = orig_url
        else:
            os.environ.pop("UPGRADE_PORTAL_URL", None)

def test_qdrant_filter_enforces_public_excerpt_boundary(monkeypatch):
    """Verify excerpt restrictions are applied inside the Qdrant query filter."""

    class FakeQdrantClient:
        def __init__(self):
            self.query_arguments = None

        def query_points(self, **kwargs):
            self.query_arguments = kwargs
            return SimpleNamespace(points=[])

    fake_client = FakeQdrantClient()

    monkeypatch.setattr(
        qdrant_service,
        "get_qdrant_client",
        lambda: fake_client,
    )

    monkeypatch.setattr(
        QdrantService,
        "ensure_collection",
        classmethod(lambda cls, collection_name=None: None),
    )

    QdrantService.search_authorized(
        query_vector=[0.0] * 384,
        authorized_report_ids=["R-101", "R-102"],
        limit=5,
        collection_name="test_collection",
    )

    assert fake_client.query_arguments is not None

    query_filter = fake_client.query_arguments["query_filter"]

    # Only authorized report IDs may match.
    assert query_filter.must[0].key == "report_id"
    assert query_filter.must[0].match.any == ["R-101", "R-102"]

    # The filter must allow non-excerpt reports.
    allows_non_excerpt_reports = any(
        condition.must_not
        and any(
            field.key == "access_type"
            and field.match.value == "public_excerpt"
            for field in condition.must_not
        )
        for condition in query_filter.should
    )

    # Public-excerpt reports must match excerpt chunks only.
    requires_excerpt_flag = any(
        condition.must
        and any(
            field.key == "is_excerpt"
            and field.match.value is True
            for field in condition.must
        )
        for condition in query_filter.should
    )

    assert allows_non_excerpt_reports, (
        "Qdrant filter must allow authorized non-excerpt reports."
    )
    assert requires_excerpt_flag, (
        "Qdrant filter must require is_excerpt=True for public excerpts."
    )
def test_qdrant_runtime_excludes_non_excerpt_chunks(monkeypatch):
    """Verify Qdrant itself excludes non-excerpt public-report chunks."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, Distance, VectorParams
    from types import SimpleNamespace
    import app.services.qdrant_service as qdrant_service
    from app.services.qdrant_service import QdrantService

    dimension = 384
    collection = "runtime_excerpt_boundary_test"

    # A completely isolated, in-memory Qdrant instance.
    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(
            size=dimension,
            distance=Distance.COSINE,
        ),
    )

    vector = [1.0] + [0.0] * (dimension - 1)

    client.upsert(
        collection_name=collection,
        points=[
            PointStruct(
                id=1,
                vector=vector,
                payload={
                    "report_id": "R-TEST",
                    "chunk_id": "excerpt",
                    "access_type": "public_excerpt",
                    "is_excerpt": True,
                    "text": "Allowed public excerpt",
                },
            ),
            PointStruct(
                id=2,
                vector=vector,
                payload={
                    "report_id": "R-TEST",
                    "chunk_id": "outside_excerpt",
                    "access_type": "public_excerpt",
                    "is_excerpt": False,
                    "text": "Content outside public excerpt",
                },
            ),
        ],
        wait=True,
    )

    class RecordingClient:
        """Capture Qdrant's raw results before application-level checks."""

        def __init__(self, wrapped):
            self.wrapped = wrapped
            self.raw_points = None

        def __getattr__(self, name):
            return getattr(self.wrapped, name)

        def query_points(self, **kwargs):
            response = self.wrapped.query_points(**kwargs)
            self.raw_points = response.points
            return response

    recording_client = RecordingClient(client)

    monkeypatch.setattr(
        qdrant_service,
        "get_qdrant_client",
        lambda: recording_client,
    )

    results = QdrantService.search_authorized(
        query_vector=vector,
        authorized_report_ids=["R-TEST"],
        limit=10,
        collection_name=collection,
    )

    # Inspect Qdrant's raw output, before Python post-filtering.
    assert recording_client.raw_points is not None
    raw_chunk_ids = {
        point.payload["chunk_id"]
        for point in recording_client.raw_points
    }
    assert raw_chunk_ids == {"excerpt"}, (
        f"Qdrant returned unexpected raw chunks: {raw_chunk_ids}"
    )

    # Also verify the final application-level response.
    assert [chunk["chunk_id"] for chunk in results] == ["excerpt"]

    client.close()
