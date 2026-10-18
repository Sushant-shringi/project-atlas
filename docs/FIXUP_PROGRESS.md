# Project Atlas — Fixup Progress Tracker

This document tracks progress on the final strict fix-and-verify pass in priority order.

---

## Progress Overview

| Phase | Description | Status | Evidence / Notes |
| :--- | :--- | :---: | :--- |
| **Phase 0** | **Baseline Inspection** | **DONE** | Docker containers healthy, branch clean, background pytest cleared, Playwright Chromium verified on host. |
| **Phase 1** | **Portal UI & Tenant Switching (A1-A7)** | **DONE** | Real Playwright Chromium verification: bidirectional switching (C-01<->C-02 repeated), scoped message history, feedback saved to MySQL (id: 4), confidence N/A on refusals, and graceful offline error recovery. Evidence: `artifacts/e2e/phase1/phase1_evidence.json` + 8 screenshots. |
| **Phase 2** | **Entitlement & Answer Correctness (B2, B6, B7, B8)** | **IN PROGRESS** | No hardcoded template answers, real titles/publishers from MySQL, confidence policy, Qdrant server verification. |
| **Phase 3** | **Derived Value, Security Refusal, SQL Query Display, Redirect (B1, B3, B4, B5)** | PENDING | Calculation disclosure, security refusal event logging, parameterized SQL text display, election redirect. |
| **Phase 4** | **SQL Timeout & DB Write Denial (D1), Gemini & Fallback Eval (C1, C5)** | PENDING | MySQL timeouts, DB permissions test, live Gemini & fallback eval passes with evidence. |
| **Phase 5** | **Documentation Updates (C2, C3, C4, D2, D3)** | PENDING | Failure analyses (real observed), limitations, cost/token notes, reviewer docs. |
| **Phase 6** | **Final Verification & Full Regression Matrix** | PENDING | Complete regression matrix with Playwright evidence, single pytest background run, secrets hygiene check, git push. |

---

## Phase 0 Baseline Summary
- **Containers:** `atlas_api`, `atlas_ci3_portal`, `atlas_mysql`, `atlas_qdrant` all UP and healthy.
- **Git Branch:** `main`, clean working tree at commit `c949734`.
- **Background Processes:** No lingering pytest or python background processes.
- **Playwright Chromium:** Verified installed and operational on host.
- **Evidence Directory:** `artifacts/e2e/` configured and git-ignored in `.gitignore`.

---

## Phase 1 Verification Summary (All Real Browser Outputs)
- **A1 (Buttons & AJAX):** Fixed relative HTTP 302 redirection issue (`header('Location: /chat'); exit;`), ensuring all quick prompts and feedback buttons trigger real requests from host.
- **A2 (Tenant Switching):** Added dedicated C-01 and C-02 buttons in `.tenant-switcher`; verified repeated bidirectional switching in Chromium (`C-01 -> C-02 -> C-01 -> C-02 -> C-01`).
- **A3 (Server-Side Secrets):** Verified `client_id` and API key are strictly derived from server-side CI3 session (`atlas_client_id`), never from browser request inputs.
- **A4 (Scoped Message History):** Updated `Conversation_model` to scope sessions per client (`atlas_messages_C-01` vs `atlas_messages_C-02`); verified in browser that C-01 queries do not leak to C-02 and vice versa.
- **A5 (Entitlement Panel):** Verified live MySQL reflection: C-01 displays R-101 Full, R-103 Full, R-102 Excerpt; C-02 displays R-101 Restricted, R-103 Full, R-102 Excerpt.
- **A6 (Refusal Confidence Badge):** Refusal responses now show `Confidence: N/A` instead of `Confidence: 0%`.
- **A7 (Feedback & Offline Recovery):** Verified `user_feedback` MySQL row insertion; verified stopped API displays friendly notice without PHP traces, and recovers immediately upon restart.

