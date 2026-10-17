"""
Project Atlas - Automated Tests for Real Gemini Writer & Verification (Phase 1)
Proves:
1. LLM Context Leakage Defense: exact prompt/context sent to LLM never contains unpurchased report figures (e.g., R-101 for C-02) or client contact emails.
2. Critic Output Validation: Rejects hallucinated market figures/citations and falls back to safe text.
3. Visible Fallback Mode: Responses clearly state llm_mode ("gemini" or "fallback") and reason.
4. Zero Fabricated Counts: Token and cost tracking are 0 when fallback is active.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.agent.workflow import AgentWorkflow
from app.agent.critic import FactCheckerCritic
from app.services.llm_service import LLMService
from app.services.ingestion import IngestionService


@pytest.fixture(scope="module", autouse=True)
def setup_vector_index():
    """Ensure vector database is populated."""
    reports_dir = str(Path(__file__).parent.parent / "reports")
    IngestionService.ingest_directory(reports_dir, collection_name="report_chunks")


def test_llm_prompt_leakage_defense():
    """
    Captures the exact prompt/context sent to the LLM during real workflow execution.
    Asserts:
    1. For Client C-02, R-101 text ($4.21 billion, R-101 title) never appears in context.
    2. Client emails (e.g. @northwind.com, @bluedelta.com) never appear in context.
    """
    captured_calls = []

    original_generate = LLMService.generate_response

    def spy_generate(prompt, context_str, request_id, client_id):
        captured_calls.append({
            "prompt": prompt,
            "context_str": context_str,
            "client_id": client_id
        })
        return original_generate(prompt, context_str, request_id, client_id)

    with patch.object(LLMService, "generate_response", side_effect=spy_generate):
        # Client C-02 queries about smart water meters (C-02 only has R-102 and R-103)
        res = AgentWorkflow.process_chat(
            client_id="C-02",
            question="What is the smart water meter market valuation and key trends?"
        )

        assert len(captured_calls) >= 1, "LLMService.generate_response was not invoked"
        captured = captured_calls[0]
        context_sent = captured["context_str"]

        # 1. Assert R-101 figures never leak into C-02 context
        assert "4.21" not in context_sent, "R-101 figure (4.21) leaked into C-02 context!"
        assert "Report ID: R-101" not in context_sent, "R-101 chunk included in C-02 context!"
        assert "Global Smart Water Meter Market 2025" not in context_sent

        # 2. Assert client contact emails never leak into LLM context
        assert "@northwind" not in context_sent
        assert "@bluedelta" not in context_sent
        assert "sara.chen@" not in context_sent
        assert "d.vance@" not in context_sent


def test_critic_rejects_hallucinated_figures():
    """
    Tests that FactCheckerCritic detects hallucinated figures and citations,
    and workflow falls back to verified extracted text.
    """
    retrieved_chunks = [
        {
            "report_id": "R-102",
            "title": "Smart Metering Technology Excerpt",
            "page": 3,
            "publisher": "CMR Public",
            "scope": "Hardware only",
            "text": "The global smart metering hardware market reached USD 3.87 billion in 2024."
        }
    ]

    # Valid grounded response
    valid_text = "According to R-102, the hardware market was USD 3.87 billion in 2024."
    is_valid, msg, unverified = FactCheckerCritic.validate_and_sanitize_response(valid_text, retrieved_chunks)
    assert is_valid is True
    assert len(unverified) == 0

    # Hallucinated figure (e.g. 99.8 billion)
    hallucinated_text = "According to R-102, the market reached USD 99.8 billion in 2024."
    is_valid, msg, unverified = FactCheckerCritic.validate_and_sanitize_response(hallucinated_text, retrieved_chunks)
    assert is_valid is False
    assert "99.8" in unverified

    # Hallucinated report citation (e.g. R-999)
    unauthorized_citation_text = "According to Report R-999, the market grew strongly."
    is_valid, msg, unverified = FactCheckerCritic.validate_and_sanitize_response(unauthorized_citation_text, retrieved_chunks)
    assert is_valid is False
    assert "R-999" in unverified


def test_workflow_falls_back_when_critic_rejects_llm_hallucination():
    """
    Simulates Gemini hallucinating an ungrounded figure.
    Workflow should reject the LLM answer, fall back to safe extraction,
    and tag llm_mode='fallback' with the rejection reason.
    """
    hallucinated_answer = "The global smart water meter market was valued at USD 142.5 billion in 2024 according to R-101."
    mock_metrics = {
        "latency_ms": 1200,
        "prompt_tokens": 500,
        "completion_tokens": 50,
        "total_tokens": 550,
        "estimated_cost_usd": 0.0001
    }

    with patch.object(LLMService, "generate_response", return_value=(hallucinated_answer, mock_metrics, "gemini", None)):
        res = AgentWorkflow.process_chat(
            client_id="C-01",
            question="What was the global smart water meter market size in 2024?"
        )

        # Output validator should have caught "142.5" which is not in R-101 evidence
        assert res["llm_mode"] == "fallback"
        assert res["fallback_reason"] is not None
        assert "Critic rejected" in res["fallback_reason"]
        assert "142.5" not in res["answer"]


def test_fallback_mode_has_zero_fabricated_counts():
    """
    Ensures that when deterministic fallback is used, token counts and cost are strictly 0.
    """
    ans, metrics = LLMService._fallback_response(
        prompt="What was the 2024 market size?",
        context_str="The market was valued at USD 4.21 billion in 2024.",
        reason="Deterministic fallback test"
    )

    assert metrics["prompt_tokens"] == 0
    assert metrics["completion_tokens"] == 0
    assert metrics["total_tokens"] == 0
    assert metrics["estimated_cost_usd"] == 0.0
    assert metrics["llm_mode"] == "fallback"
    assert metrics["fallback_reason"] == "Deterministic fallback test"
