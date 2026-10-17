"""
Project Atlas - Entitlement-Aware Retrieval Engine
Enforces pre-retrieval Qdrant metadata filtering so unauthorized report chunks
are NEVER loaded into memory or transmitted to the LLM.
"""

from typing import Any, Dict, List, Optional, Tuple
from app.core.config import settings
from app.core.logging_config import logger
from app.services.embeddings import EmbeddingService
from app.services.entitlements import EntitlementService
from app.services.qdrant_service import QdrantService


class RetrievalEngine:
    """Entitlement-bounded semantic retrieval over Qdrant."""

    @classmethod
    def retrieve_for_client(
        cls,
        client_id: str,
        query: str,
        limit: int = 5,
        collection_name: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], List[str], Optional[Dict[str, Any]]]:
        """
        Executes entitlement-filtered retrieval for an authenticated client.
        Returns:
            (retrieved_chunks, authorized_report_ids, refusal_info)
        """
        # Step 1: Obtain authorized report IDs from MySQL
        authorized_report_ids = EntitlementService.get_authorized_reports_for_client(client_id)
        logger.info(f"Client {client_id} authorized reports: {authorized_report_ids}")

        if not authorized_report_ids:
            logger.warning(f"Client {client_id} has no report entitlements.")
            return [], [], {
                "refusal_reason": "No active report entitlements found for this account.",
                "upgrade_path": "Contact subscription services to purchase report access."
            }

        # Step 2: Compute embedding vector
        query_vector = EmbeddingService.embed_text(query)

        # Step 3: Apply metadata filter strictly at the vector database level
        raw_chunks = QdrantService.search_authorized(
            query_vector=query_vector,
            authorized_report_ids=authorized_report_ids,
            limit=limit,
            collection_name=collection_name
        )

        # Step 4: Defense-in-depth post-retrieval validation
        verified_chunks = []
        for chunk in raw_chunks:
            rep_id = chunk.get("report_id")
            if rep_id not in authorized_report_ids:
                logger.error(
                    f"CRITICAL ENTITLEMENT VIOLATION: Qdrant returned unauthorized chunk {rep_id} for client {client_id}! Discarded."
                )
                continue

            # Public excerpt enforcement
            if chunk.get("access_type") == "public_excerpt" and not chunk.get("is_excerpt", False):
                logger.warning(f"Excluding non-excerpt page {chunk.get('page')} of public report {rep_id}")
                continue

            verified_chunks.append(chunk)

        return verified_chunks, authorized_report_ids, None
