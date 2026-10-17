"""
Project Atlas - End-to-End Agent Workflow Orchestrator
Coordinates query routing, entitlement-bounded retrieval, safe SQL operations,
financial projections, conflict detection, Gemini LLM generation, critic evaluation,
and escalation ticketing.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from app.agent.router import QueryRouter
from app.agent.critic import FactCheckerCritic
from app.core.config import settings
from app.core.logging_config import logger
from app.db.connection import DatabaseManager
from app.security.prompt_defense import PromptDefense
from app.services.entitlements import EntitlementService
from app.services.llm_service import LLMService
from app.services.retrieval import RetrievalEngine
from app.tools.calculator import MarketCalculator
from app.tools.conflict_detector import ConflictDetector
from app.tools.sql_tool import SafeSQLTool


class AgentWorkflow:
    """End-to-end agentic workflow executing deterministic tools and generative reasoning."""

    @classmethod
    def process_chat(
        cls,
        client_id: str,
        question: str,
        conversation_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the Project Atlas copilot pipeline orchestrated via LangGraph StateGraph.
        Returns the structured API response contract.
        """
        start_time = time.time()
        req_id = request_id or f"req-{uuid.uuid4().hex[:12]}"
        conv_id = conversation_id or f"conv-{uuid.uuid4().hex[:12]}"

        logger.info(
            f"Processing chat request via LangGraph: Client={client_id}, Question='{question}'",
            extra={"request_id": req_id, "client_id": client_id}
        )

        # Ensure conversation exists in DB
        cls._ensure_conversation(conv_id, client_id)

        from app.agent.langgraph_workflow import atlas_langgraph

        initial_state = {
            "client_id": client_id,
            "question": question,
            "req_id": req_id,
            "conv_id": conv_id,
            "start_time": start_time,
            "citations": [],
            "conflicts": [],
            "derived_values": [],
            "quality_flags": []
        }

        final_state = atlas_langgraph.invoke(initial_state)

        # Record audit event if query was unsafe
        if final_state.get("route") == "unsafe":
            cls._record_audit_event(
                client_id,
                "UNSAFE_QUERY_REJECTED",
                {"question": question, "reason": final_state.get("refusal_reason")}
            )

        response_data = {
            "answer": final_state.get("answer", ""),
            "citations": final_state.get("citations", []),
            "confidence": final_state.get("confidence", 0.0),
            "conflicts": final_state.get("conflicts", []),
            "derived_values": final_state.get("derived_values", []),
            "escalated": final_state.get("escalated", False),
            "request_id": req_id,
            "escalation_id": final_state.get("escalation_id"),
            "refusal_reason": final_state.get("refusal_reason"),
            "llm_mode": final_state.get("llm_mode", "fallback"),
            "fallback_reason": final_state.get("fallback_reason"),
            "latency_ms": final_state.get("latency_ms", int((time.time() - start_time) * 1000))
        }

        return response_data

    @classmethod
    def _ensure_conversation(cls, conv_id: str, client_id: str):
        """Ensures conversation record exists in DB."""
        try:
            sql = "INSERT INTO conversations (id, client_id, title) VALUES (?, ?, ?) ON CONFLICT DO NOTHING"
            conn = DatabaseManager.get_connection()
            if not hasattr(conn, "row_factory"):
                # MySQL syntax
                sql = "INSERT INTO conversations (id, client_id, title) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE updated_at = NOW()"
                DatabaseManager.execute_commit(sql, (conv_id, client_id, "Market Research Chat"))
            else:
                DatabaseManager.execute_commit(sql, (conv_id, client_id, "Market Research Chat"))
        except Exception as e:
            logger.warning(f"Could not persist conversation header: {e}")

    @classmethod
    def _persist_message(cls, conv_id: str, role: str, content: str, response_data: Optional[Dict] = None):
        """Saves message to conversation_messages table."""
        try:
            msg_id = f"msg-{uuid.uuid4().hex[:12]}"
            citations_json = str(response_data.get("citations")) if response_data else None
            conflicts_json = str(response_data.get("conflicts")) if response_data else None
            derived_json = str(response_data.get("derived_values")) if response_data else None
            confidence = response_data.get("confidence") if response_data else None
            escalated = 1 if (response_data and response_data.get("escalated")) else 0
            latency_ms = response_data.get("latency_ms") if response_data else None

            sql = """
            INSERT INTO conversation_messages 
            (id, conversation_id, role, content, citations_json, confidence, conflicts_json, derived_values_json, escalated, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            conn = DatabaseManager.get_connection()
            if not hasattr(conn, "row_factory"):
                sql = sql.replace("?", "%s")
            DatabaseManager.execute_commit(sql, (
                msg_id, conv_id, role, content, citations_json, confidence, conflicts_json, derived_json, escalated, latency_ms
            ))
        except Exception as e:
            logger.warning(f"Could not persist message: {e}")

    @classmethod
    def _create_escalation_ticket(cls, client_id: str, conv_id: str, question: str, reason: str, confidence: float) -> str:
        """Creates an escalation ticket in MySQL."""
        ticket_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        try:
            sql = """
            INSERT INTO escalation_tickets 
            (id, client_id, conversation_id, question, reason, confidence_score, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """
            conn = DatabaseManager.get_connection()
            if not hasattr(conn, "row_factory"):
                sql = sql.replace("?", "%s")
            DatabaseManager.execute_commit(sql, (
                ticket_id, client_id, conv_id, question, reason, confidence
            ))
            logger.info(f"Escalation ticket {ticket_id} created for Client {client_id}")
        except Exception as e:
            logger.error(f"Failed to record escalation ticket: {e}")
        return ticket_id

    @classmethod
    def _record_audit_event(cls, client_id: str, event_type: str, details: Dict):
        """Records a security audit event in MySQL."""
        try:
            import json
            sql = "INSERT INTO audit_events (client_id, event_type, details) VALUES (?, ?, ?)"
            conn = DatabaseManager.get_connection()
            if not hasattr(conn, "row_factory"):
                sql = sql.replace("?", "%s")
            DatabaseManager.execute_commit(sql, (client_id, event_type, json.dumps(details)))
        except Exception as e:
            logger.warning(f"Failed to record audit event: {e}")
