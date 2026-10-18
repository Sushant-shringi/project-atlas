"""
Project Atlas - Automated Test for Ingestion Pipeline (Milestone 3)
Verifies:
1. Parsing of all synthetic report documents (R-101 through R-107).
2. Preservation of exact metadata, sectors, and page numbers.
3. Accurate detection and flagging of the R-102 page 14 prompt-injection trap.
4. Dense embedding generation and vector upsert into Qdrant.
"""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.ingestion import IngestionService
from app.services.qdrant_service import QdrantService
from app.services.embeddings import EmbeddingService


def test_parse_r101_preserves_page_8():
    """Verify R-101 preserves page 8 with required market numbers."""
    reports_dir = Path(__file__).parent.parent / "reports"
    r101_file = reports_dir / "R-101_Global_Smart_Water_Meter_Market_2025.txt"
    assert r101_file.exists(), "R-101 file must exist"

    parsed = IngestionService.parse_report_file(str(r101_file))
    assert parsed["metadata"]["report_id"] == "R-101"
    assert parsed["metadata"]["sector"] == "Utilities"
    assert parsed["metadata"]["access_type"] == "paid"

    pages = {chunk["page"]: chunk for chunk in parsed["chunks"]}
    assert 8 in pages, "Page 8 must exist in R-101"
    p8_text = pages[8]["text"]
    assert "4.21 billion" in p8_text
    assert "11.2%" in p8_text
    assert "38%" in p8_text
    assert pages[8]["chunk_id"] == "R-101_P08"


def test_parse_r102_detects_prompt_injection():
    """Verify R-102 detects prompt injection on page 14 while preserving market data."""
    reports_dir = Path(__file__).parent.parent / "reports"
    r102_file = reports_dir / "R-102_Smart_Water_Metering_Industry_Outlook_2024.txt"
    assert r102_file.exists(), "R-102 file must exist"

    parsed = IngestionService.parse_report_file(str(r102_file))
    assert parsed["metadata"]["report_id"] == "R-102"
    assert parsed["metadata"]["access_type"] == "public_excerpt"

    pages = {chunk["page"]: chunk for chunk in parsed["chunks"]}
    assert 14 in pages, "Page 14 must exist in R-102"
    p14_chunk = pages[14]

    # Verify injection detection
    assert p14_chunk["has_injection_pattern"] is True
    # Verify legitimate market facts are still present
    assert "3.87 billion" in p14_chunk["text"]
    assert "9.8%" in p14_chunk["text"]
    assert "41%" in p14_chunk["text"]
    assert p14_chunk["is_excerpt"] is True


def test_ingest_all_reports_into_qdrant():
    """Verify full directory ingestion and Qdrant storage."""
    reports_dir = str(Path(__file__).parent.parent / "reports")
    collection_test = "test_report_chunks"

    result = IngestionService.ingest_directory(reports_dir, collection_name=collection_test)
    assert result["reports_ingested"] >= 6
    assert "R-101" in result["report_ids"]
    assert "R-102" in result["report_ids"]
    assert "R-103" in result["report_ids"]
    assert result["chunks_indexed"] > 0
    assert result["injections_detected"] >= 1


def test_embeddings_generation():
    """Verify 384-dimensional dense vectors."""
    text = "The global smart water meter market was valued at USD 4.21 billion in 2024."
    vec = EmbeddingService.embed_text(text)
    assert isinstance(vec, list)
    assert len(vec) == 384

def test_public_excerpt_boundary_excludes_page_15_and_beyond(tmp_path):
    """Only pages up to 14 should be marked as public excerpts."""

    report_file = tmp_path / "R-TEST_Public_Excerpt.txt"
    report_file.write_text(
        """=== REPORT METADATA ===
report_id: R-TEST
title: Public Excerpt Boundary Test
publisher: Test Publisher
published_date: 2026-01-01
sector: Utilities
access_type: public_excerpt
scope: Test scope

--- PAGE 14 ---
This content is within the public excerpt boundary.

--- PAGE 15 ---
This content is outside the public excerpt boundary.
""",
        encoding="utf-8",
    )

    parsed = IngestionService.parse_report_file(str(report_file))
    pages = {chunk["page"]: chunk for chunk in parsed["chunks"]}

    assert pages[14]["is_excerpt"] is True
    assert pages[15]["is_excerpt"] is False
