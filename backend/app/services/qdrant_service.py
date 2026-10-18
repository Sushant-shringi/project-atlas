"""
Project Atlas - Qdrant Vector Store Service
Handles collection initialization, payload indexing, vector upsert,
and strict metadata-filtered semantic retrieval.
"""

from typing import Any, Dict, List, Optional
import uuid
from app.core.config import settings
from app.core.logging_config import logger

_qdrant_client = None


def get_qdrant_client():
    """Lazily connects to Qdrant or falls back to in-memory store if network is unavailable."""
    global _qdrant_client
    if _qdrant_client is None:
        import socket
        from qdrant_client import QdrantClient

        target_host = settings.QDRANT_HOST
        target_port = settings.QDRANT_PORT
        try:
            socket.gethostbyname(target_host)
        except OSError:
            if target_host == "qdrant":
                target_host = "127.0.0.1"

        # Fast socket check to avoid long connection timeout if daemon isn't running on host
        is_port_open = False
        try:
            with socket.create_connection((target_host, target_port), timeout=1.0):
                is_port_open = True
        except OSError:
            is_port_open = False

        if is_port_open:
            try:
                logger.info(f"Connecting to live Qdrant at {target_host}:{target_port}")
                client = QdrantClient(host=target_host, port=target_port, timeout=2.0)
                client.get_collections()
                _qdrant_client = client
                logger.info("Successfully connected to live Qdrant instance.")
            except Exception as e:
                logger.warning(f"Could not connect to live Qdrant ({e}). Falling back to in-memory store.")
                _qdrant_client = QdrantClient(":memory:")
        else:
            logger.info("Qdrant port not reachable on host; initializing local in-memory Qdrant client.")
            _qdrant_client = QdrantClient(":memory:")

    return _qdrant_client


class QdrantService:
    """Service wrapping Qdrant operations with strict entitlement filtering."""

    @classmethod
    def ensure_collection(cls, collection_name: Optional[str] = None) -> bool:
        """Ensures the vector collection exists with appropriate index configurations."""
        from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

        col_name = collection_name or settings.QDRANT_COLLECTION
        client = get_qdrant_client()

        collections = [c.name for c in client.get_collections().collections]
        if col_name not in collections:
            logger.info(f"Creating Qdrant collection: {col_name}")
            client.create_collection(
                collection_name=col_name,
                vectors_config=VectorParams(size=settings.VECTOR_DIMENSION, distance=Distance.COSINE),
            )
            # Create payload indexes for fast filtered lookups
            for field in ["report_id", "access_type", "sector"]:
                client.create_payload_index(
                    collection_name=col_name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD
                )
            logger.info(f"Collection {col_name} created with keyword indexes.")
        return True

    @classmethod
    def upsert_chunks(cls, chunks: List[Dict[str, Any]], embeddings: List[List[float]], collection_name: Optional[str] = None) -> int:
        """Upserts embedded document chunks into Qdrant."""
        from qdrant_client.models import PointStruct

        cls.ensure_collection(collection_name)
        client = get_qdrant_client()
        col_name = collection_name or settings.QDRANT_COLLECTION

        points = []
        for chunk, vector in zip(chunks, embeddings):
            # Create a deterministic point id based on report_id and chunk_id
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk['report_id']}_{chunk['chunk_id']}"))
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=chunk
                )
            )

        client.upsert(collection_name=col_name, points=points)
        logger.info(f"Upserted {len(points)} chunks into collection {col_name}")
        return len(points)

    @classmethod
    def search_authorized(
        cls,
        query_vector: List[float],
        authorized_report_ids: List[str],
        limit: int = 5,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves document chunks matching query vector, strictly bounded by authorized report IDs.
        Under NO circumstances does this query return chunks from unpurchased/unauthorized reports.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchAny

        if not authorized_report_ids:
            logger.warning("Search called with empty authorized_report_ids. Returning zero chunks.")
            return []

        cls.ensure_collection(collection_name)
        client = get_qdrant_client()
        col_name = collection_name or settings.QDRANT_COLLECTION

        # Build Qdrant metadata filter
        retrieval_filter = Filter(
            must=[
                FieldCondition(
                    key="report_id",
                    match=MatchAny(any=authorized_report_ids)
                )
            ]
        )

        if hasattr(client, "query_points"):
            response = client.query_points(
                collection_name=col_name,
                query=query_vector,
                query_filter=retrieval_filter,
                limit=limit,
                with_payload=True
            )
            search_results = response.points
        else:
            search_results = client.search(
                collection_name=col_name,
                query_vector=query_vector,
                query_filter=retrieval_filter,
                limit=limit,
                with_payload=True
            )

        retrieved_chunks = []
        for hit in search_results:
            chunk = dict(hit.payload)
            chunk["score"] = float(hit.score)
            
            # Additional defense-in-depth check: confirm report_id is strictly in authorized list
            if chunk.get("report_id") not in authorized_report_ids:
                logger.error(f"SECURITY ANOMALY: Chunk {chunk.get('report_id')} bypassed Qdrant filter! Discarding immediately.")
                continue

            # Additional check: If this is an excerpt-scoped report, ensure it's marked as excerpt
            if chunk.get("access_type") == "public_excerpt" and not chunk.get("is_excerpt", False):
                logger.warning(f"Excluding non-excerpt chunk from public excerpt report {chunk.get('report_id')}")
                continue

            retrieved_chunks.append(chunk)

        logger.info(f"Retrieved {len(retrieved_chunks)} authorized chunks for reports: {authorized_report_ids}")
        return retrieved_chunks
