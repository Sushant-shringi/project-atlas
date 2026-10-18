# Project Atlas — AI Assistance & Engineering Disclosure

**Candidate:** Sushant Shringi  
**Position:** AI Software Developer — Generative & Agentic AI  
**Company:** Cognitive Market Research & Consulting (CMR)  
**Date:** 18 October 2026

---

## 1. Transparency Statement

In strict adherence to the Project Atlas assignment requirements, professional ethics, and academic integrity, this document provides an honest, comprehensive breakdown of how Artificial Intelligence development tools were utilized throughout the project lifecycle.

Neither "zero AI used" nor "100% human written" is claimed. Generative AI was used extensively as a pair-programmer, accelerating development across architecture scaffolding, boilerplate generation, refactoring, test synthesis, and debugging, while all system invariants, security guarantees, architectural decisions, and verification steps were directed and validated by human engineering.

---

## 2. Tools & Models Employed

- **AI Development Assistant:** Google Antigravity AI pair-programming agent powered by Google DeepMind Gemini reasoning models.
- **Application LLM Services:** Google Gemini API (`gemini-1.5-flash` / `gemini-pro`) with deterministic structured fallback.
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (PyTorch dense embeddings running locally).

---

## 3. Engineering Breakdown by Phase

### A. Design Brainstorming & Architecture
- **AI Contribution:** Explored architectural trade-offs between custom directed acyclic graph (DAG) execution vs. LangGraph `StateGraph`, assisted in sketching initial Mermaid diagrams, and proposed regex patterns for multi-stage prompt injection detection.
- **Human Decision & Verification:**
  - Designed the strict pre-retrieval entitlement filtering model in Qdrant (`report_id in authorized_reports`) to achieve a provable 0.0% data leakage guarantee.
  - Mandated the dual-user MySQL security architecture (`atlas_app` for CRUD vs `atlas_readonly` for SELECT only) to ensure least-privilege database isolation.
  - Established the non-averaging conflict resolution strategy for contradictory multi-publisher research data (R-101 vs. R-102).

### B. Boilerplate & Scaffolding Generation
- **AI Contribution:** Generated initial FastAPI route handlers, Pydantic request/response schemas (`ChatRequest`, `ChatResponse`, `CitationItem`, `ConflictItem`, `DerivedValueItem`), Dockerfile / Docker Compose scaffolding, and basic CodeIgniter 3 controller/view layout.
- **Human Decision & Verification:**
  - Enforced strict Pydantic model validation rules and defense-in-depth header parsing.
  - Implemented server-side session protection and CSRF cookie validation in CodeIgniter 3 to prevent client impersonation.

### C. Refactoring & Orchestration
- **AI Contribution:** Refactored the procedural workflow into a compiled LangGraph `StateGraph(AgentState)` with clearly segregated functional nodes (`router`, `retriever`, `sql_tool`, `calculator`, `writer`, `critic`, `escalation`) and conditional routing edges.
- **Human Decision & Verification:**
  - Maintained all security-critical logic (entitlement resolution, SQL rejection, boundary checking) as deterministic Python functions rather than delegating security checks to LLM prompts.
  - Re-architected the Gemini Writer to include bounded context (4,000 characters), request timeouts (30s), exponential backoff retry (3 attempts on 429/5xx), and visible `llm_mode` ("gemini" vs "fallback") with zero token fabrication on fallback.
  - Integrated `FactCheckerCritic.validate_and_sanitize_response` to reject hallucinated figures or citations not grounded in authorized evidence.

### D. Test Synthesis & Evaluation Design
- **AI Contribution:** Generated pytest scenarios covering all 10 Appendix B requirements (`AB-Q01` through `AB-Q10`) with clients C-01 and C-02, plus 16 security and edge cases (`TC-11` through `TC-26`).
- **Human Decision & Verification:**
  - Designed automated prompt leak tests verifying that restricted report content (e.g., R-101 for C-02) and client credentials never appear in LLM prompt contexts.
  - Designed cryptographic cache isolation tests verifying distinct SHA-256 keys for different tenant-entitlement combinations.
  - Formulated the controlled fault injection experiments for Failures #4 and #5 in Section 19 of the Evaluation Report.

### E. Debugging & Issue Resolution
- **AI Contribution:** Identified breaking changes across library upgrades, including Qdrant Python client 1.19+ migration (`search` to `query_points`), and assisted in diagnosing API status codes.
- **Human Decision & Verification:**
  - Handled the Google API key leaked-key block (403 PermissionDenied) gracefully, activating verified deterministic fallback with full transparency in logs and API response fields.
  - Fixed LangGraph conditional routing edge states and resolved SQLite in-memory threading differences for local pytest runs.

---

## 4. Verification Standard & Integrity Guarantee

1. **No Simulated Passes:** Every test report, benchmark metric, and evaluation score was generated by executing live Python and pytest commands against genuine codebase implementations.
2. **Zero Fabricated Metrics:** Evaluation latency, token counts ($0.00$ cost on fallback, genuine counts on API), and accuracy numbers were recorded from actual tool output logs.
3. **Reproducibility:** All implementations, test scripts, and seed datasets are preserved in the repository with verified instructions for clean reproduction.
