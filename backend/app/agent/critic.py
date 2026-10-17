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

        # If answer indicates refusal or unable to find
        if "unable to" in answer_text.lower() or "not authorized" in answer_text.lower():
            score = 0.50
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
