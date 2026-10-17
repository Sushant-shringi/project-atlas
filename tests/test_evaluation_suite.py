"""
Project Atlas - Pytest Wrapper for Evaluation Scenarios
Enables running the evaluation matrix under standard pytest commands.
"""

import sys
from pathlib import Path

# Add backend and project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.agent.workflow import AgentWorkflow
from app.services.ingestion import IngestionService
from eval.scenarios import EVALUATION_SCENARIOS


@pytest.fixture(scope="module", autouse=True)
def ensure_indexed():
    reports_dir = str(Path(__file__).parent.parent / "reports")
    IngestionService.ingest_directory(reports_dir, collection_name="report_chunks")


def test_evaluation_baseline_pass_rate():
    """Verify evaluation benchmark completes and achieves > 75% pass rate."""
    from eval.run_eval import run_evaluation
    results = run_evaluation()
    assert results["total_tests"] >= 25
    assert results["pass_rate_percent"] >= 75.0
    assert results["entitlement_leakage_rate"] == 0.0, "Zero tolerance for entitlement data leakage"
