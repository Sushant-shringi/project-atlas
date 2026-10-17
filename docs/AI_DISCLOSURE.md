# Project Atlas — AI Assistance & Engineering Disclosure

**Candidate:** Sushant Shringi  
**Position:** AI Software Developer — Generative & Agentic AI  
**Company:** Cognitive Market Research & Consulting (CMR)  
**Date:** 18 October 2026

---

## 1. Transparency Statement

In full alignment with professional integrity, academic honesty, and the assignment instructions for Project Atlas, this document discloses the use of generative AI development tools during the design, implementation, and testing of this submission.

---

## 2. Tools & Models Used

- **Primary Assistant:** Google Antigravity AI Pair-Programming Assistant (powered by Google DeepMind Gemini models).
- **Embedded LLM in Application:** Google Gemini API (`gemini-1.5-flash` / `gemini-pro`) with deterministic structured fallbacks.
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (local Hugging Face PyTorch weights, zero external API dependency).

---

## 3. Division of Engineering Labor

| Engineering Domain | AI Assistant Contribution | Human Engineering & Verification |
| :--- | :--- | :--- |
| **System Architecture** | Scaffolding initial directory layouts and Docker Compose configuration templates. | Designed the pre-retrieval entitlement security architecture, MySQL least-privilege user segregation (`atlas_app` vs `atlas_readonly`), and non-averaging conflict resolution strategy. |
| **Relational Schema** | Generating DDL syntax for 9 relational tables and foreign keys. | Structured data normalization, indexing strategy, audit logging schema, and escalation ticket tracking workflow. |
| **Vector Ingestion & RAG** | Providing initial chunking and text segmentation snippets. | Configured dense vector dimensionality (384-dim), implemented Qdrant payload filters, resolved Qdrant 1.19+ `query_points` client compatibility, and enforced defense-in-depth post-retrieval validation. |
| **Financial Math & Logic** | Drafting initial CAGR mathematical formulas. | Disambiguated the 5-period compounding window ($2025 \rightarrow 2030$), enforced boundary checks ($> 2030$), and designed structured assumptions tracking. |
| **Prompt Injection Defense** | Generating regular expression patterns for prompt injection detection. | Designed the XML tag sandboxing strategy (`<untrusted_publication_excerpt>`), multi-layered scanning at ingestion vs runtime, and document isolation protocol. |
| **CodeIgniter 3 Portal** | Generating HTML/CSS markup and responsive Bootstrap styling. | Integrated CSRF verification, dynamic session management, server-side API key protection, and custom AJAX error handling. |
| **Testing & Evaluation** | Expanding test scenario fixtures across 26 test cases. | Executed 100% of tests locally on Windows host, verified zero-leakage entitlement guarantees, analyzed 5 genuine failure modes, and calibrated confidence thresholds. |

---

## 4. Verification & Validation Standard

Every line of code, test case, database query, and documentation artifact in this repository was:
1. Executed and verified locally on Windows 11 with Docker Desktop.
2. Subjected to automated Pytest suites (`test_ingestion.py`, `test_entitlements.py`, `test_agent_tools.py`, `test_workflow.py`, `test_api.py`, `test_evaluation_suite.py`).
3. Evaluated without mocked AI responses, fake retrieval lists, or simulated database states.
