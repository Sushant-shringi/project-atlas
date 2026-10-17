"""
Project Atlas - FastAPI API Routes
Exposes:
- POST /chat: Entitlement-aware report copilot endpoint.
- POST /ingest: Administrative document ingestion and vectorization.
- GET /escalations: Escalation ticket catalog.
- POST /feedback: User thumbs-up/down interaction feedback.
- GET /health: Component health and dependency monitoring.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from app.api.auth import get_admin_user, get_current_client
from app.agent.workflow import AgentWorkflow
from app.core.config import settings
from app.core.logging_config import logger
from app.db.connection import DatabaseManager
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    EscalationTicketItem,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
)
from app.services.ingestion import IngestionService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, summary="Submit a question to the Report Copilot")
async def chat_endpoint(
    payload: ChatRequest,
    request: Request,
    current_client: Dict[str, Any] = Depends(get_current_client)
):
    """
    Executes an entitlement-bounded question answering flow.
    Enforces that caller's authenticated identity matches the requested client_id.
    """
    req_id = request.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:12]}")

    # Defense-in-depth: Prevent client impersonation
    if current_client["id"] != payload.client_id:
        logger.warning(
            f"SPOOFING REJECTED: Key belongs to {current_client['id']}, but requested {payload.client_id}",
            extra={"security_flag": "CLIENT_SPOOFING_REJECTED", "request_id": req_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Authenticated key belongs to {current_client['id']}, cannot execute queries for {payload.client_id}."
        )

    response_dict = AgentWorkflow.process_chat(
        client_id=payload.client_id,
        question=payload.question,
        conversation_id=payload.conversation_id,
        request_id=req_id
    )
    return response_dict


@router.post("/ingest", response_model=IngestResponse, summary="Ingest reports into vector database")
async def ingest_endpoint(
    payload: IngestRequest = IngestRequest(),
    is_admin: bool = Depends(get_admin_user)
):
    """
    Administrative endpoint to parse reports, generate embeddings, and populate Qdrant.
    """
    try:
        reports_dir = payload.reports_directory or "reports"
        result = IngestionService.ingest_directory(reports_dir)
        return IngestResponse(
            success=True,
            reports_ingested=result["reports_ingested"],
            report_ids=result.get("report_ids", []),
            chunks_indexed=result["chunks_indexed"],
            injections_detected=result["injections_detected"],
            message="Reports parsed, scanned, and indexed successfully."
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion error: {str(e)}"
        )


@router.get("/escalations", response_model=List[Dict[str, Any]], summary="Retrieve escalation tickets")
async def escalations_endpoint(
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by ticket status"),
    current_client: Dict[str, Any] = Depends(get_current_client)
):
    """
    Retrieves human analyst escalation tickets stored in MySQL.
    """
    try:
        # Non-admin clients can only view their own escalations
        target_client = client_id or current_client["id"]
        if current_client["id"] != target_client:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Cannot view escalations belonging to another client."
            )

        sql = "SELECT id, client_id, conversation_id, question, reason, confidence_score, status, created_at FROM escalation_tickets WHERE client_id = ?"
        params = [target_client]

        if status_filter:
            sql += " AND status = ?"
            params.append(status_filter)

        sql += " ORDER BY created_at DESC LIMIT 50"

        conn = DatabaseManager.get_connection()
        if not hasattr(conn, "row_factory"):
            sql = sql.replace("?", "%s")
        rows = DatabaseManager.execute_query(sql, tuple(params))
        return rows
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching escalations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve escalations.")


@router.post("/feedback", response_model=FeedbackResponse, summary="Record user thumbs-up or down feedback")
async def feedback_endpoint(
    payload: FeedbackRequest,
    current_client: Dict[str, Any] = Depends(get_current_client)
):
    """
    Persists user feedback for a message into MySQL.
    """
    try:
        sql = """
        INSERT INTO user_feedback (message_id, client_id, rating, comment)
        VALUES (?, ?, ?, ?)
        """
        conn = DatabaseManager.get_connection()
        if not hasattr(conn, "row_factory"):
            sql = sql.replace("?", "%s")
        affected = DatabaseManager.execute_commit(sql, (
            payload.message_id, payload.client_id, payload.rating, payload.comment
        ))
        return FeedbackResponse(
            success=True,
            feedback_id=affected,
            message="Feedback recorded successfully."
        )
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback.")


@router.get("/health", response_model=HealthResponse, summary="Health status of API and backend services")
async def health_endpoint():
    """
    Returns application and dependency health status without exposing sensitive credentials.
    """
    components = {}

    # Check API itself
    components["api"] = {"status": "ok", "details": "FastAPI service running"}

    # Check MySQL
    try:
        db_conn = DatabaseManager.get_connection()
        components["mysql"] = {"status": "ok", "details": "Database connection operational"}
    except Exception as e:
        components["mysql"] = {"status": "degraded", "details": f"Database unavailable: {type(e).__name__}"}

    # Check Qdrant
    try:
        from app.services.qdrant_service import get_qdrant_client
        q_client = get_qdrant_client()
        cols = q_client.get_collections()
        components["qdrant"] = {"status": "ok", "details": f"Vector store online ({len(cols.collections)} collections)"}
    except Exception as e:
        components["qdrant"] = {"status": "degraded", "details": f"Vector store unavailable: {type(e).__name__}"}

    # Check Embedding model
    try:
        from app.services.embeddings import get_embedding_model
        model = get_embedding_model()
        components["embeddings"] = {"status": "ok", "details": f"Model {settings.EMBEDDING_MODEL_NAME} active"}
    except Exception as e:
        components["embeddings"] = {"status": "degraded", "details": f"Embedding engine error: {type(e).__name__}"}

    overall_status = "healthy" if all(c["status"] == "ok" for c in components.values()) else "degraded"

    return HealthResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        components=components,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
