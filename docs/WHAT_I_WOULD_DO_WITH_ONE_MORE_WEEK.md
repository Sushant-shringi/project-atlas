# Project Atlas — What I Would Do With One More Week

**Author:** Sushant Shringi  
**Target Role:** AI Software Developer — Generative & Agentic AI, Cognitive Market Research & Consulting (CMR)  
**Scope:** 1-Page Architectural Evolution Roadmap

---

Given an additional week of dedicated engineering time, I would advance Project Atlas from its current production-ready MVP into an enterprise-scale, autonomous intelligence platform along five strategic dimensions:

---

### 1. Hybrid Sparse-Dense Retrieval with Reciprocal Rank Fusion (RRF)
- **Current State:** Dense vector embeddings using SentenceTransformers `all-MiniLM-L6-v2` with cosine distance in Qdrant.
- **Limitation:** Dense embeddings capture high-level semantic intent well but occasionally suffer recall degradation on exact domain-specific acronyms, regulatory standards, and niche equipment codes (e.g., *AMR vs. AMI*, *LoRaWAN*, *EN 1434*, *DN15/DN20 meters*).
- **Roadmap:** Implement hybrid retrieval combining lexical BM25 (or Qdrant's sparse vector indexing) with dense embeddings, merged using Reciprocal Rank Fusion (RRF):
  $$RRF(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
  This guarantees exact keyword fidelity for industry jargon while retaining deep semantic matching for conversational queries.

---

### 2. Multi-Hop Query Decomposition with LangGraph Stateful Workflows
- **Current State:** Single-turn deterministic router and critic orchestrating retrieval, calculation, and conflict detection.
- **Roadmap:** Transition the orchestration pipeline to a stateful LangGraph agent graph featuring:
  - **Query Decomposition:** Breaking complex client queries (e.g., *"Compare the 2030 market size of APAC smart water meters with EMEA residential purifiers and evaluate CAGR differences"*) into sub-queries.
  - **Self-Corrective RAG (CRAG):** Introducing an automated document grader node that evaluates retrieval quality before generation; if retrieved chunks score below relevance thresholds, the agent reformulates search terms autonomously.
  - **Human-in-the-Loop Analyst Dashboard:** An interactive review interface where CMR senior research analysts can claim, review, edit, and resolve pending `escalation_tickets` directly from MySQL.

---

### 3. Modernized Identity Architecture & Multi-Tenant Namespace Isolation
- **Current State:** API key authentication mapped to Client IDs with pre-retrieval Boolean payload filters.
- **Roadmap:**
  - Implement an OAuth2 / OpenID Connect authorization server issuing cryptographically signed JWTs with fine-grained claim scopes (`reports:read`, `calculations:run`, `escalations:write`).
  - Introduce physical tenant isolation in Qdrant through tenant-partitioned namespaces or dedicated client collection shards, ensuring cryptographic and physical partition boundaries for high-compliance enterprise clients.

---

### 4. Real-Time Streaming Citations & Server-Sent Events (SSE)
- **Current State:** Synchronous HTTP POST request from CodeIgniter 3 to FastAPI, returning complete JSON payloads.
- **Roadmap:**
  - Implement Server-Sent Events (SSE) streaming on `/chat/stream` in FastAPI.
  - Update CodeIgniter 3 portal frontend to render token-by-token streaming responses with inline citation footnote badges appearing dynamically as facts are validated by the critic.

---

### 5. Automated Multimodal PDF Ingestion Pipeline
- **Current State:** Structured Markdown and text document ingestion with regex page preservation and prompt injection sanitization.
- **Roadmap:**
  - Build an asynchronous document ingestion worker (Celery / Redis) supporting raw publisher PDFs.
  - Integrate layout-aware document parsers (Docling / Unstructured.io) to extract complex financial tables directly into structured Markdown and relational `market_metrics` rows, preserving footnoted methodology notes and multi-column layouts across report pages.
