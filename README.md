# Project Atlas: Enterprise Report Copilot

Project Atlas is an enterprise-grade AI Report Copilot integrated into a legacy CodeIgniter 3 market research portal. It provides deterministic, entitlement-aware Retrieval-Augmented Generation (RAG) over market intelligence publications with strict multi-tenant authorization, prompt-injection defense, conflict detection, financial calculations, read-only SQL querying, citation verification, and human analyst escalation.

---

## 🏛️ High-Level Architecture Overview

```
                      +-----------------------------+
                      |   Legacy CodeIgniter 3      |
                      |   Portal (PHP 8.1 / Apache) |
                      +--------------+--------------+
                                     |
                       REST / JSON   | Authenticated via Client Key
                                     v
                      +-----------------------------+
                      |     FastAPI Python API      |
                      |    (Port 8000 / async)      |
                      +--------------+--------------+
                                     |
          +--------------------------+--------------------------+
          |                          |                          |
          v                          v                          v
+-------------------+      +-------------------+      +-------------------+
|  Entitlement &    |      |  Agent Workflow   |      |  Audit & Metrics  |
|  Security Engine  |      |  (Deterministic)  |      |  Logger (MySQL)   |
+---------+---------+      +---------+---------+      +-------------------+
          |                          |
          v                          |
+-------------------+                |
| Qdrant Vector DB  | <--------------+
| Metadata-Filtered |
+-------------------+
          |
          v
+-------------------+
| Google Gemini LLM |
| (Untrusted Data)  |
+-------------------+
```

---

## 🚀 Quick Start (Docker Compose)

```bash
# 1. Copy sample environment file and configure GEMINI_API_KEY
cp .env.example .env

# 2. Build and launch all services
docker compose up --build -d

# 3. Access Services
# FastAPI Docs:       http://localhost:8000/docs
# CodeIgniter 3:      http://localhost:8080/
# Qdrant Dashboard:   http://localhost:6333/dashboard
```

Detailed documentation, evaluation benchmarks, failure analyses, and architectural decisions are located in the `docs/` and `eval/` directories.
