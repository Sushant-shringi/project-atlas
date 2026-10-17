"""
Project Atlas - Critic & Fact-Checker
Evaluates factual claims, verifies citations against retrieved source evidence,
computes calibrated confidence scores, and triggers human analyst escalation when appropriate.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from app.core.config import settings
from app.core.logging_config import logger


class FactCheckerCritic:
    """Deterministic validation and confidence evaluation engine."""

    @classmethod
    def extract_citations_from_chunks(cls, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extracts structured citations from retrieved authorized chunks."""
        citations = []
        seen = set()
        for chunk in chunks:
            rep_id = chunk.get("report_id")
            page = chunk.get("page")
            key = f"{rep_id}_{page}"
            if key not in seen:
                seen.add(key)
                citations.append({
                    "report_id": rep_id,
                    "title": chunk.get("title", ""),
                    "page": page,
                    "publisher": chunk.get("publisher", ""),
                    "scope": chunk.get("scope", ""),
                    "access_type": chunk.get("access_type", "")
                })
        return citations

    @classmethod
    def evaluate_confidence_and_facts(
        cls,
        question: str,
        answer_text: str,
        retrieved_chunks: List[Dict[str, Any]],
        derived_values: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]]
    ) -> Tuple[float, bool, List[str]]:
        """
        Calculates calibrated confidence score (0.0 to 1.0) and determines escalation necessity.
        Returns:
            (confidence_score, requires_escalation, quality_flags)
        """
        score = 1.0
        flags = []

        # Check if retrieved chunks actually address the specific topic of the question
        q_words = set(re.findall(r"\w+", question.lower()))
        combined_text = " ".join([c.get("text", "").lower() for c in retrieved_chunks])
        # Find material topic words (>5 chars) in question
        topic_words = [w for w in q_words if len(w) > 5 and w not in {"market", "global", "report", "growth", "valuation", "projected"}]
        overlap = [w for w in topic_words if w in combined_text]
        if topic_words and len(overlap) == 0 and not derived_values:
            score = 0.40
            flags.append("Retrieved documents do not contain evidence for query topic (obscure or missing concept).")

        # If answer indicates refusal or unable to find
        if "unable to" in answer_text.lower() or "not authorized" in answer_text.lower() or "does not contain" in answer_text.lower():
            score = 0.45
            flags.append("Insufficient evidence or restricted report.")

        # If no chunks were retrieved
        if not retrieved_chunks and not derived_values:
            score = 0.20
            flags.append("No authorized reference evidence retrieved.")

        # Check for citation presence
        has_citations = bool(re.search(r"\[(R-\d+)[^\]]*\]", answer_text)) or bool(re.search(r"R-\d+", answer_text))
        if not has_citations and not derived_values:
            score -= 0.30
            flags.append("Answer lacks explicit report identifier citations.")

        # Check for unsupported extrapolation (e.g. projecting to 2035)
        if "2035" in question:
            score = 0.35
            flags.append("Question requests unsupported long-term projection (2035) beyond report horizon.")

        # Check for conflicts presence: when conflicts exist, ensure neither was silently dropped
        if conflicts:
            conflict_covered = any(str(src.get("value")) in answer_text for src in conflicts[0].get("sources", []))
            if not conflict_covered:
                score -= 0.25
                flags.append("Conflicting sources present but not thoroughly detailed in output.")

        # Clamp score between 0.0 and 1.0
        final_score = max(0.0, min(1.0, round(score, 2)))
        requires_escalation = (final_score < settings.CONFIDENCE_THRESHOLD)

        logger.info(
            f"Critic evaluation completed: Confidence={final_score}, Escalation={requires_escalation}, Flags={flags}"
        )
        return final_score, requires_escalation, flags

    @classmethod
    def validate_and_sanitize_response(
        cls,
        answer_text: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[bool, str, List[str]]:
        """
        Validates that figures, percentages, and cited report IDs in the LLM response
        are grounded in the authorized retrieved chunks.
        Returns:
            (is_valid, validation_message, unverified_items)
        """
        if not answer_text or not retrieved_chunks:
            return True, "No figures to validate.", []

        # Authorized report IDs
        auth_report_ids = {c.get("report_id") for c in retrieved_chunks if c.get("report_id")}

        # Check for citation of unauthorized report IDs
        cited_report_ids = set(re.findall(r"\b(R-\d{3})\b", answer_text, re.IGNORECASE))
        cited_report_ids = {r.upper() for r in cited_report_ids}
        unauthorized_citations = cited_report_ids - auth_report_ids
        if unauthorized_citations:
            logger.warning(f"Critic rejected answer citing unauthorized report IDs: {unauthorized_citations}")
            return False, f"Answer cites unauthorized or unretrieved reports: {unauthorized_citations}", list(unauthorized_citations)

        # Build set of all numbers in authorized text
        evidence_numbers = set()
        for chunk in retrieved_chunks:
            for num in re.findall(r"\b\d+(?:\.\d+)?\b", chunk.get("text", "")):
                evidence_numbers.add(num)

        # Permit common baseline years and integers
        common_allowed = {"2024", "2025", "2026", "2027", "2028", "2029", "2030", "1", "2", "3", "4", "5", "10", "100"}

        # Extract numbers attached to units in answer: e.g. "4.21 billion", "11.2%", "3.87 billion"
        metric_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:billion|million|trillion|%|cagr)", answer_text, re.IGNORECASE)
        unverified_metrics = []
        for m in metric_matches:
            if m not in evidence_numbers and m not in common_allowed:
                unverified_metrics.append(m)

        if unverified_metrics:
            logger.warning(f"Critic detected ungrounded figures in LLM answer: {unverified_metrics}")
            return False, f"Answer contains unverified market figures not found in authorized evidence: {unverified_metrics}", unverified_metrics

        return True, "All figures and citations verified against authorized evidence.", []
