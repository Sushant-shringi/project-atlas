"""
Project Atlas - Document Ingestion & Chunking Service
Parses market research reports, extracts metadata and page numbers,
detects embedded prompt injections, generates embeddings, and indexes into Qdrant.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging_config import logger
from app.security.prompt_defense import PromptDefense
from app.services.embeddings import EmbeddingService
from app.services.qdrant_service import QdrantService


class IngestionService:
    """Orchestrates parsing, chunking, security scanning, embedding, and vector storage."""

    @classmethod
    def parse_report_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Parses a single report text file into metadata and page-level chunks.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract metadata block
        metadata: Dict[str, Any] = {
            "report_id": "UNKNOWN",
            "title": "Untitled Report",
            "publisher": "Unknown",
            "published_date": "2025-01-01",
            "sector": "General",
            "access_type": "paid",
            "scope": "General",
            "is_excerpt": False
        }

        # Parse key-value pairs in header
        header_match = re.search(r"=== REPORT METADATA ===\s*(.*?)(?=--- PAGE|\Z)", content, re.DOTALL)
        if header_match:
            header_text = header_match.group(1)
            for line in header_text.strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if key == "report_id":
                        metadata["report_id"] = val
                    elif key == "title":
                        metadata["title"] = val
                    elif key == "publisher":
                        metadata["publisher"] = val
                    elif key == "published_date":
                        metadata["published_date"] = val
                    elif key == "sector":
                        metadata["sector"] = val
                    elif key == "access_type":
                        metadata["access_type"] = val
                    elif key == "scope":
                        metadata["scope"] = val

        # Parse pages
        page_pattern = re.compile(r"---\s*PAGE\s+(\d+)\s*---\s*(.*?)(?=---\s*PAGE|\Z)", re.DOTALL)
        page_matches = page_pattern.findall(content)

        chunks: List[Dict[str, Any]] = []
        for page_num_str, page_text in page_matches:
            page_num = int(page_num_str)
            clean_text = page_text.strip()
            if not clean_text:
                continue

            # Determine excerpt status (R-102 public excerpt covers pages 1-14)
            is_excerpt = False
            if metadata["access_type"] == "public_excerpt":
                is_excerpt = (page_num <= 14)
            elif metadata["access_type"] == "free":
                is_excerpt = True

            # Scan for prompt-injection patterns in untrusted report content
            has_injection, matched_patterns = PromptDefense.scan_for_injection(clean_text)
            if has_injection:
                logger.warning(
                    f"Report {metadata['report_id']} Page {page_num} contains prompt injection: {matched_patterns}",
                    extra={
                        "report_id": metadata["report_id"],
                        "page": page_num,
                        "security_flag": "INGESTION_INJECTION_DETECTED"
                    }
                )

            chunk_id = f"{metadata['report_id']}_P{page_num:02d}"
            chunks.append({
                "chunk_id": chunk_id,
                "report_id": metadata["report_id"],
                "title": metadata["title"],
                "publisher": metadata["publisher"],
                "published_date": metadata["published_date"],
                "sector": metadata["sector"],
                "access_type": metadata["access_type"],
                "scope": metadata["scope"],
                "page": page_num,
                "is_excerpt": is_excerpt,
                "has_injection_pattern": has_injection,
                "text": clean_text
            })

        return {
            "metadata": metadata,
            "chunks": chunks
        }

    @classmethod
    def ingest_directory(cls, reports_dir: str, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans a directory for report text files, processes, embeds, and stores them in Qdrant.
        """
        dir_path = Path(reports_dir)
        if not dir_path.exists():
            raise FileNotFoundError(f"Reports directory not found: {reports_dir}")

        all_chunks: List[Dict[str, Any]] = []
        reports_processed = []
        injections_found = 0

        for file_path in sorted(dir_path.glob("*.txt")):
            logger.info(f"Ingesting report file: {file_path.name}")
            parsed = cls.parse_report_file(str(file_path))
            reports_processed.append(parsed["metadata"]["report_id"])
            for c in parsed["chunks"]:
                if c.get("has_injection_pattern"):
                    injections_found += 1
                all_chunks.append(c)

        if not all_chunks:
            logger.warning("No chunks extracted during ingestion.")
            return {
                "reports_ingested": 0,
                "chunks_indexed": 0,
                "injections_detected": 0
            }

        # Generate dense embeddings
        texts = [chunk["text"] for chunk in all_chunks]
        logger.info(f"Generating dense embeddings for {len(texts)} chunks...")
        embeddings = EmbeddingService.embed_batch(texts)

        # Upsert into Qdrant
        indexed_count = QdrantService.upsert_chunks(
            chunks=all_chunks,
            embeddings=embeddings,
            collection_name=collection_name
        )

        logger.info(
            f"Ingestion complete: {len(reports_processed)} reports, {indexed_count} chunks indexed, {injections_found} injections flagged."
        )

        return {
            "reports_ingested": len(reports_processed),
            "report_ids": reports_processed,
            "chunks_indexed": indexed_count,
            "injections_detected": injections_found
        }
