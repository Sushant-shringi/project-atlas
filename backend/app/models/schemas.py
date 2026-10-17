"""
Project Atlas - Typed Pydantic Request & Response Models
Strictly implements the required API contract and serialization schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Chat Request & Response Schemas ---

class ChatRequest(BaseModel):
    client_id: str = Field(..., description="Unique client identifier (e.g. C-01, C-02)", example="C-01")
    question: str = Field(..., description="Market research question", example="What was the global smart water meter market size in 2024?")
    conversation_id: Optional[str] = Field(None, description="Optional conversation UUID for thread continuity", example="conv-12345")


class CitationItem(BaseModel):
    report_id: str = Field(..., description="Published research report identifier", example="R-101")
    title: Optional[str] = Field(None, description="Report publication title", example="Global Smart Water Meter Market 2025")
    page: Optional[int] = Field(None, description="Page number of cited evidence", example=8)
    publisher: Optional[str] = Field(None, description="Research publisher organization", example="CMR")
    scope: Optional[str] = Field(None, description="Coverage scope definition", example="Hardware, software, and services")
    access_type: Optional[str] = Field(None, description="Entitlement access class", example="paid")
    evidence: Optional[str] = Field(None, description="Supporting passage or metric quote")


class ConflictSourceItem(BaseModel):
    report_id: str
    title: str
    publisher: str
    page: int
    value: float
    unit: str
    year: int
    scope: str
    cagr: Optional[str] = None


class ConflictItem(BaseModel):
    conflict_id: str
    metric: str
    has_conflict: bool
    resolution_method: str
    explanation: str
    sources: List[ConflictSourceItem]


class DerivedValueItem(BaseModel):
    metric: str
    derived_value: float
    unit: str
    base_value: float
    base_year: int
    target_year: int
    cagr_applied: float
    formula: str
    is_derived_estimate: bool
    assumptions: List[str]
    citations: List[Dict[str, Any]]


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded, citation-backed natural response")
    citations: List[CitationItem] = Field(default_factory=list, description="Explicit source citations with report IDs and pages")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence score between 0.0 and 1.0")
    conflicts: List[ConflictItem] = Field(default_factory=list, description="Contrasting market metrics without averaging")
    derived_values: List[DerivedValueItem] = Field(default_factory=list, description="Calculated projections with disclosed assumptions")
    escalated: bool = Field(..., description="True if question was escalated to a human CMR analyst")
    request_id: str = Field(..., description="Unique request tracking identifier")
    escalation_id: Optional[str] = Field(None, description="Escalation ticket ID if escalated")
    refusal_reason: Optional[str] = Field(None, description="Explanation if question was refused")
    llm_mode: str = Field("fallback", description="Generation mode: 'gemini' or 'fallback'")
    fallback_reason: Optional[str] = Field(None, description="Explanation if fallback mode was activated")
    latency_ms: int = Field(..., description="Total processing latency in milliseconds")


# --- Ingest Request & Response Schemas ---

class IngestRequest(BaseModel):
    reports_directory: Optional[str] = Field("reports", description="Path to reports directory")
    recreate_index: Optional[bool] = Field(False, description="Re-create vector index if true")


class IngestResponse(BaseModel):
    success: bool
    reports_ingested: int
    report_ids: List[str]
    chunks_indexed: int
    injections_detected: int
    message: str


# --- Escalations Schema ---

class EscalationTicketItem(BaseModel):
    id: str
    client_id: str
    conversation_id: Optional[str] = None
    question: str
    reason: str
    confidence_score: Optional[float] = None
    status: str
    created_at: Optional[str] = None


# --- Feedback Schema ---

class FeedbackRequest(BaseModel):
    message_id: str
    client_id: str
    rating: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    success: bool
    feedback_id: Optional[int] = None
    message: str


# --- Health Check Schema ---

class ComponentHealth(BaseModel):
    status: str
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    environment: str
    components: Dict[str, ComponentHealth]
    timestamp: str
