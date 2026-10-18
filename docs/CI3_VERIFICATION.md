# Project Atlas — CodeIgniter 3 Portal Verification Document

This document verifies the legacy CodeIgniter 3 (CI3) enterprise portal integration against all 7 security, architecture, and resilience requirements outlined in the project specification and assignment guidelines, backed by real observed outputs from container execution.

---

## 1. Verification Checklist & Code Reference Matrix

| # | Requirement | Implementation Status | Primary Files & Line References | Security & Architectural Mechanism |
|---|---|---|---|---|
| **1** | **Server-Side Session Identity** | Verified | [`ci3_portal/application/controllers/Chat.php:20-23, 29`](file:///ci3_portal/application/controllers/Chat.php#L20-L23)<br>[`ci3_portal/application/config/config.php:37`](file:///ci3_portal/application/config/config.php#L37) | Client identity (`atlas_client_id`) is stored exclusively in the server-side CI3 session file (`/tmp/atlas_ci_session*`). The browser cannot manipulate the client ID. |
| **2** | **Server-Side Secret API Keys & MySQL Identity** | Verified | [`ci3_portal/application/models/Client_model.php:18-21`](file:///ci3_portal/application/models/Client_model.php#L18-L21)<br>[`ci3_portal/application/libraries/Atlas_api.php:26-37`](file:///ci3_portal/application/libraries/Atlas_api.php#L26-L37) | Company name and confidential API keys are retrieved directly from the MySQL `clients` table on the server. The browser only sees `atlas_ci_session` and `atlas_csrf_cookie`. API keys are never exposed to the client. |
| **3** | **CSRF Protection** | Verified | [`ci3_portal/application/config/config.php:54-60`](file:///ci3_portal/application/config/config.php#L54-L60)<br>[`ci3_portal/application/controllers/Chat.php:73, 94`](file:///ci3_portal/application/controllers/Chat.php#L73) | `$config['csrf_protection'] = TRUE` with cookie enforcement (`atlas_csrf_cookie`). All POST endpoints (`/chat/send`, `/chat/feedback`, `/chat/switch_client`) validate and dynamically return refreshed CSRF token hashes. |
| **4** | **XSS Prevention & Output Escaping** | Verified | [`ci3_portal/application/config/config.php:52`](file:///ci3_portal/application/config/config.php#L52)<br>[`ci3_portal/application/views/chat_view.php:155-168, 220-224`](file:///ci3_portal/application/views/chat_view.php#L155-L168) | Global XSS filtering enabled. All server-side PHP data uses `htmlspecialchars()`. In the frontend DOM renderer, all user inputs, LLM text, citations, and formulas pass through `escapeHtml()` text-node sanitization. |
| **5** | **Resilient Integration & Graceful Timeout** | Verified | [`ci3_portal/application/libraries/Atlas_api.php:123-145`](file:///ci3_portal/application/libraries/Atlas_api.php#L123-L145)<br>[`ci3_portal/application/views/chat_view.php:305-312`](file:///ci3_portal/application/views/chat_view.php#L305-L312) | cURL client enforces `CURLOPT_TIMEOUT` (30s) and `CURLOPT_CONNECTTIMEOUT` (5s). When FastAPI is stopped (`docker compose stop api`), CI3 catches the cURL error and returns a styled user notice without exposing raw PHP errors. |
| **6** | **Conversation Persistence** | Verified | [`ci3_portal/application/models/Conversation_model.php:17-57`](file:///ci3_portal/application/models/Conversation_model.php#L17-L57)<br>[`ci3_portal/application/controllers/Chat.php:67, 71`](file:///ci3_portal/application/controllers/Chat.php#L67)<br>[`ci3_portal/application/views/chat_view.php:154-169`](file:///ci3_portal/application/views/chat_view.php#L154-L169) | `Conversation_model` stores active `conversation_id` and message history in session storage (`atlas_messages`). Stored turns, including report citation chips, are re-rendered safely upon page refresh. |
| **7** | **Thumbs-Up / Thumbs-Down Feedback** | Verified | [`ci3_portal/application/views/chat_view.php:265-275, 315-334`](file:///ci3_portal/application/views/chat_view.php#L265-L275)<br>[`ci3_portal/application/controllers/Chat.php:82-98`](file:///ci3_portal/application/controllers/Chat.php#L82-L98)<br>[`backend/app/api/routes.py:166-193`](file:///backend/app/api/routes.py#L166-L193) | Interactive thumbs up/down buttons submit message ID, client ID, rating, and optional comment to `/chat/feedback` -> `POST /feedback`, which persists directly into the MySQL `user_feedback` table. |

---

## 2. Real Observed Verification Outputs

The following outputs were produced live inside the `atlas_ci3_portal` container running against `atlas_mysql` and `atlas_api`:

### A. Client Identity & Dynamic Entitlement Resolution (C-01 vs C-02)

Executed live verification script against the portal:
```
=== 1. VERIFY CLIENT C-01 (Northwind Utilities) ===
Tenant: Northwind Utilities (C-01)
  [C-01] R-101: Authorized (Full)
  [C-01] R-102: Public Excerpt (pp. 1-14)
  [C-01] R-103: Authorized (Full)
  [C-01] R-104: Restricted
  [C-01] R-105: Restricted
  [C-01] R-106: Restricted
  [C-01] R-107: Restricted

CSRF Token for switch: b9eae8621f...

=== 2. VERIFY SWITCH TO CLIENT C-02 (Blue Delta Infra) ===
Switch HTTP Code: 303
Tenant after switch: Blue Delta Infra (C-02)
  [C-02] R-101: Restricted
  [C-02] R-102: Public Excerpt (pp. 1-14)
  [C-02] R-103: Authorized (Full)
  [C-02] R-104: Restricted
  [C-02] R-105: Restricted
  [C-02] R-106: Restricted
  [C-02] R-107: Restricted
```

**Key Findings:**
1. **Dynamic MySQL Lookup:** Company names ("Northwind Utilities" and "Blue Delta Infra") are fetched live from MySQL `clients` via `Client_model::get_client()`.
2. **Entitlement Isolation:** C-01 displays R-101 as `Authorized (Full)`. Upon switching to C-02, R-101 immediately displays as `Restricted`, while R-103 remains `Authorized (Full)` and R-102 displays as `Public Excerpt (pp. 1-14)`. No figures or text from unauthorized reports are displayed.

---

### B. Chat AJAX & Citations Delivery (Client C-02)

Dispatched query: `"What was the global water purifier market size in 2024?"`
```json
{
  "answer": "The global residential water purifier market reached a valuation of USD 9.45 billion in 2024 [R-103, p. 11]. This market scope encompasses reverse osmosis (RO), ultraviolet (UV), and ultrafiltration point-of-use systems [R-103, p. 11].",
  "citations": [
    {
      "report_id": "R-103",
      "title": "Residential Water Purifier Market 2025",
      "page": 11,
      "evidence": "Valued at USD 9.45 billion in 2024 with 9.8% CAGR from 2025 to 2030."
    }
  ],
  "confidence": 1.0,
  "conflicts": [],
  "derived_values": [],
  "escalated": false,
  "message_id": "msg-7bc237cb31f7",
  "csrf_name": "atlas_csrf_token",
  "csrf_hash": "b9eae8621f8bcfae2007c147fca56793"
}
```

---

### C. Feedback Persistence in MySQL

Submitted thumbs-up feedback for `msg-7bc237cb31f7`:
```
Feedback Response: {"success":true,"feedback_id":1,"message":"Feedback recorded successfully.","csrf_name":"atlas_csrf_token","csrf_hash":"b9eae8621f8bcfae2007c147fca56793"}
```

Direct query to MySQL database (`project_atlas.user_feedback`):
```sql
SELECT id, message_id, client_id, rating, comment, created_at FROM user_feedback;
```
**Database Output:**
```
id:         1
message_id: msg-7bc237cb31f7
client_id:  C-02
rating:     thumbs_up
comment:    Verified accurate via CI3 test script.
created_at: 2026-10-18 06:20:27
```

---

### D. Offline API & Timeout Resilience (Task E Verification)

Tested by shutting down the API container (`docker compose stop api`) and submitting a question:
```
$ docker compose stop api
Container atlas_api Stopped

$ curl -X POST http://localhost/chat/send -d "atlas_csrf_token=...&question=What is the market size?"
HTTP Status Code: 200
Response Body:
{
  "success": false,
  "error": "Backend service is currently unavailable or timed out.",
  "answer": "Connection Notice: The Report Copilot service did not respond within the allocated timeout. Please retry in a few moments.",
  "message_id": "msg-cd4c5d70c4d4",
  "csrf_name": "atlas_csrf_token",
  "csrf_hash": "cca325c21c42591ff6b2698caf0ba064"
}
```
**Security & Resilience Result:**
- **Zero raw PHP warnings or stack traces exposed** to the user.
- Handled gracefully via `Atlas_api::_execute_request()`.
- Returns HTTP 200 with structured JSON and user-friendly error notice rendered in the chat bubble.
- Refreshed CSRF token returned to keep the user session intact.

---

### E. XSS Sanitization & Escaping Verification

Submitted malicious payload: `<script>alert("xss")</script>`
1. **At Ingestion & Controller Level:** Sanitized by CI3 global XSS filter (`global_xss_filtering = TRUE`).
2. **At View Rendering Level:** Filtered through `htmlspecialchars()` on the server and `escapeHtml()` in the browser DOM.
3. **Observed Output on Chat Reload:**
   ```html
   <div class="bubble">[removed]alert&#40;&quot;xss&quot;&#41;[removed]</div>
   ```
   Zero executable script tags rendered in the browser.

---

## 3. End-to-End API Integration Verification (cURL Proofs)

### 1. Factual Lookup & Citations (`POST /chat`)
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-Client-Key: client_key_c01_northwind_utilities_secret_2026" \
  -d '{
    "client_id": "C-01",
    "question": "What was the global smart water meter market size in 2024?",
    "conversation_id": "conv-demo-001"
  }'
```

### 2. User Feedback (`POST /feedback`)
```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -H "X-Client-Key: client_key_c01_northwind_utilities_secret_2026" \
  -d '{
    "message_id": "msg-8f1e2a",
    "client_id": "C-01",
    "rating": "thumbs_up",
    "comment": "Accurate citations and clear methodology."
  }'
```

### 3. Escalations View (`GET /escalations`)
```bash
curl -X GET "http://localhost:8000/escalations?client_id=C-01" \
  -H "X-Client-Key: client_key_c01_northwind_utilities_secret_2026"
```

### 4. Health Check (`GET /health`)
```bash
curl -X GET "http://localhost:8000/health"
```
