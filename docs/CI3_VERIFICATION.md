# Project Atlas — CodeIgniter 3 Portal Verification Document

This document verifies the legacy CodeIgniter 3 (CI3) enterprise portal integration against all 7 security, architecture, and resilience requirements outlined in the project specification and assignment guidelines.

---

## 1. Verification Checklist & Code Reference Matrix

| # | Requirement | Implementation Status | Primary Files & Line References | Security & Architectural Mechanism |
|---|---|---|---|---|
| **1** | **Server-Side Session Identity** | Verified | [`ci3_portal/application/controllers/Chat.php:23-26, 70`](file:///ci3_portal/application/controllers/Chat.php#L23-L26) | Client identity (`atlas_client_id`) is stored exclusively in the server-side CI3 session. Requests never trust or accept `client_id` from browser form bodies or query parameters. |
| **2** | **Server-Side Secret API Keys** | Verified | [`ci3_portal/application/config/atlas_api.php:9-22`](file:///ci3_portal/application/config/atlas_api.php#L9-L22)<br>[`ci3_portal/application/libraries/Atlas_api.php:27-32, 54-55`](file:///ci3_portal/application/libraries/Atlas_api.php#L27-L32) | FastAPI credentials (`X-Client-Key`) are mapped on the CI3 server. The browser only receives `atlas_ci_session` and `atlas_csrf_cookie`. API keys are never transmitted to the frontend. |
| **3** | **CSRF Protection** | Verified | [`ci3_portal/application/config/config.php:54-60`](file:///ci3_portal/application/config/config.php#L54-L60)<br>[`ci3_portal/application/controllers/Chat.php:59, 83-84, 110-111`](file:///ci3_portal/application/controllers/Chat.php#L59) | `$config['csrf_protection'] = TRUE` with cookie enforcement (`atlas_csrf_cookie`). All AJAX endpoints (`/chat/send`, `/chat/feedback`, `/chat/switch_client`) validate and dynamically refresh tokens. |
| **4** | **XSS Prevention & Output Escaping** | Verified | [`ci3_portal/application/config/config.php:52`](file:///ci3_portal/application/config/config.php#L52)<br>[`ci3_portal/application/views/chat_view.php:123-145, 155-168, 204-208`](file:///ci3_portal/application/views/chat_view.php#L123-L145) | Global XSS filtering enabled. All server-side PHP data uses `htmlspecialchars()`. In the frontend DOM renderer, all user inputs, LLM text, citations, and formulas pass through `escapeHtml()` text-node sanitization. |
| **5** | **Resilient Integration & Graceful Timeout** | Verified | [`ci3_portal/application/libraries/Atlas_api.php:12-14, 110-135`](file:///ci3_portal/application/libraries/Atlas_api.php#L110-L135)<br>[`ci3_portal/application/views/chat_view.php:294-297`](file:///ci3_portal/application/views/chat_view.php#L294-L297) | cURL client enforces `CURLOPT_TIMEOUT` (30s) and `CURLOPT_CONNECTTIMEOUT` (5s). Connection timeouts or backend 5xx errors return friendly, styled system notices without crashes or unstyled error screens. |
| **6** | **Conversation Persistence** | Verified | [`ci3_portal/application/models/Conversation_model.php:17-57`](file:///ci3_portal/application/models/Conversation_model.php#L17-L57)<br>[`ci3_portal/application/controllers/Chat.php:73, 79`](file:///ci3_portal/application/controllers/Chat.php#L73)<br>[`ci3_portal/application/views/chat_view.php:154-169`](file:///ci3_portal/application/views/chat_view.php#L154-L169) | `Conversation_model` stores active `conversation_id` and message history in session storage (`atlas_messages`). Stored turns, including report citation chips, are re-rendered safely upon page refresh. |
| **7** | **Thumbs-Up / Thumbs-Down Feedback** | Verified | [`ci3_portal/application/views/chat_view.php:258-268, 301-320`](file:///ci3_portal/application/views/chat_view.php#L258-L268)<br>[`ci3_portal/application/controllers/Chat.php:97-113`](file:///ci3_portal/application/controllers/Chat.php#L97-L113)<br>[`backend/app/api/routes.py:166-193`](file:///backend/app/api/routes.py#L166-L193) | Interactive thumbs up/down buttons on assistant bubbles submit message ID, client ID, and rating to `/chat/feedback` -> `POST /feedback`, which persists into MySQL `user_feedback` table. |

---

## 2. Detailed Technical Explanations

### Requirement 1: Server-Side Session Identity
- **Risk Avoided:** In multi-tenant enterprise applications, allowing the browser to supply `client_id` in request payloads allows trivial horizontal privilege escalation (client impersonation).
- **CI3 Implementation:**
  ```php
  // ci3_portal/application/controllers/Chat.php (Line 70)
  $client_id = $this->session->userdata('atlas_client_id');
  ```
  The client ID is retrieved directly from server-side PHP session storage.
- **FastAPI Defense-in-Depth:** Even if an attacker compromises the network boundary and manually crafts an API request to `POST /chat`, FastAPI validates that the authenticated API key matches the requested `client_id`:
  ```python
  # backend/app/api/routes.py (Lines 52-60)
  if current_client["id"] != payload.client_id:
      logger.warning(f"SPOOFING REJECTED: Key belongs to {current_client['id']}, but requested {payload.client_id}")
      raise HTTPException(status_code=403, detail="Forbidden: Client identity mismatch.")
  ```

### Requirement 2: Server-Side Secret Storage
- **Risk Avoided:** Leaking API credentials to single-page applications or browser code allows unauthorized API consumption and bypasses rate limits.
- **CI3 Implementation:**
  FastAPI secrets are configured exclusively in `ci3_portal/application/config/atlas_api.php`:
  ```php
  $config['atlas_client_keys'] = array(
      'C-01' => array(
          'company_name' => 'Northwind Utilities',
          'api_key' => 'client_key_c01_northwind_utilities_secret_2026', ...
      )
  );
  ```
  `Atlas_api.php` attaches this key as an HTTP header (`X-Client-Key: <key>`) during server-to-server cURL dispatch. The client browser only ever receives standard session cookies.

### Requirement 3: CSRF Protection
- **Configuration:**
  ```php
  // ci3_portal/application/config/config.php
  $config['csrf_protection'] = TRUE;
  $config['csrf_token_name'] = 'atlas_csrf_token';
  $config['csrf_cookie_name'] = 'atlas_csrf_cookie';
  $config['csrf_expire'] = 7200;
  ```
- **Dynamic Token Handling:**
  Because the chat interface sends asynchronous fetch requests, every AJAX controller method (`send_message`, `feedback`) queries CI3's security library and returns fresh CSRF tokens in the response JSON:
  ```php
  $api_result['csrf_name'] = $this->security->get_csrf_token_name();
  $api_result['csrf_hash'] = $this->security->get_csrf_hash();
  ```
  The JavaScript client dynamically updates `csrfName` and `csrfHash` to ensure subsequent requests remain valid without full page reloads.

### Requirement 4: XSS Prevention & Escaping
- **Multi-Layer Defense:**
  1. **Global Sanitization:** `$config['global_xss_filtering'] = TRUE` in `config.php`.
  2. **PHP View Escaping:** All dynamically injected server variables in `chat_view.php` use `htmlspecialchars()`:
     ```php
     <?php echo htmlspecialchars($client_info['company_name']); ?>
     <?php echo nl2br(htmlspecialchars($msg['content'])); ?>
     ```
  3. **JavaScript DOM Escaping:** Dynamic chat bubbles create elements via browser DOM APIs, setting inner HTML exclusively after passing untrusted strings through:
     ```javascript
     function escapeHtml(text) {
         const div = document.createElement('div');
         div.textContent = text;
         return div.innerHTML;
     }
     ```

### Requirement 5: Resilient Timeout & Failure Containment
- **Failure Modes Covered:**
  - FastAPI container is offline (`Connection refused`).
  - Network partition / DNS resolution error.
  - LLM takes longer than 30 seconds to respond (`Operation timed out`).
  - FastAPI returns 500 Internal Server Error.
- **Graceful Behavior:**
  Instead of an unhandled PHP Fatal Error or a blank white screen, `Atlas_api.php` catches the cURL error and packages a user-friendly response:
  ```php
  if ($curl_error) {
      log_message('error', 'Atlas_api cURL error: ' . $curl_error);
      return array(
          'success' => FALSE,
          'error' => 'Backend service is currently unavailable or timed out.',
          'answer' => 'Connection Notice: The Report Copilot service did not respond within the allocated timeout. Please retry in a few moments.'
      );
  }
  ```
  The UI renders this notification seamlessly in the chat timeline.

### Requirement 6: Conversation Persistence
- Every turn is recorded in `$_SESSION['atlas_messages']` via `Conversation_model->add_message()`.
- On browser reload, `Chat->index()` passes `$data['messages']` to `chat_view.php`, which renders the complete message history with properly escaped content and citation chips.

### Requirement 7: Thumbs-Up / Thumbs-Down Feedback
- Assistant message bubbles attach a persistent feedback widget containing the generated `message_id`.
- Clicking "Helpful" or "Unhelpful" triggers a POST request to `/chat/feedback` -> `Atlas_api->submit_feedback()` -> FastAPI `POST /feedback`.
- FastAPI writes the feedback record directly into the MySQL `user_feedback` table:
  ```sql
  INSERT INTO user_feedback (message_id, client_id, rating, comment) VALUES (?, ?, ?, ?)
  ```

---

## 3. End-to-End API Integration Verification (cURL Proofs)

The following `curl` commands demonstrate the exact FastAPI endpoints utilized by the CodeIgniter 3 portal.

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
**Expected Response:**
```json
{
  "answer": "According to Global Smart Water Meter Market 2025 (R-101, p.8), the global smart water meter market was valued at USD 4.21 billion in 2024...",
  "citations": [
    {
      "report_id": "R-101",
      "title": "Global Smart Water Meter Market 2025",
      "page": 8,
      "evidence": "Valued at USD 4.21 billion in 2024 with 11.2% CAGR from 2025 to 2030."
    }
  ],
  "confidence": 0.95,
  "conflicts": [],
  "derived_values": [],
  "escalated": false,
  "llm_mode": "fallback",
  "fallback_reason": null
}
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
**Expected Response:**
```json
{
  "success": true,
  "feedback_id": 1,
  "message": "Feedback recorded successfully."
}
```

### 3. Escalations View (`GET /escalations`)
```bash
curl -X GET "http://localhost:8000/escalations?client_id=C-01" \
  -H "X-Client-Key: client_key_c01_northwind_utilities_secret_2026"
```
**Expected Response:**
```json
[
  {
    "id": "ESC-75FBE385",
    "client_id": "C-01",
    "conversation_id": "conv-demo-001",
    "question": "What is the projected market size in 2035?",
    "reason": "Unsupported Extrapolation beyond 2030 forecast horizon.",
    "confidence_score": 0.0,
    "status": "pending",
    "created_at": "2026-10-18T03:00:04"
  }
]
```

### 4. Health Check (`GET /health`)
```bash
curl -X GET "http://localhost:8000/health"
```
**Expected Response:**
```json
{
  "status": "healthy",
  "environment": "development",
  "components": {
    "api": {"status": "ok", "details": "FastAPI service running"},
    "mysql": {"status": "ok", "details": "Database connection operational"},
    "qdrant": {"status": "ok", "details": "Vector store online"},
    "embeddings": {"status": "ok", "details": "Model all-MiniLM-L6-v2 active"}
  },
  "timestamp": "2026-10-18T08:35:00Z"
}
```
