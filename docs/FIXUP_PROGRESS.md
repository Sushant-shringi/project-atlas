# Project Atlas — Fixup Progress Tracker

This document tracks progress on the final strict fix-and-verify pass in priority order.

---

## Progress Overview

| Phase | Description | Status | Evidence / Notes |
| :--- | :--- | :---: | :--- |
| **Phase 0** | **Baseline Inspection** | **DONE** | Docker containers healthy, branch clean, background pytest cleared, Playwright Chromium verified on host. |
| **Phase 1** | **Portal UI & Tenant Switching (A1-A7)** | **DONE** | Real Playwright Chromium verification: bidirectional switching (C-01<->C-02 repeated), scoped message history, feedback saved to MySQL (id: 4), confidence N/A on refusals, and graceful offline error recovery. Evidence: `artifacts/e2e/phase1/phase1_evidence.json` + 8 screenshots. |
| **Phase 2** | **Entitlement & Answer Correctness (B2, B6, B7, B8)** | **DONE** | No hardcoded template answers; dynamic metadata (titles/publishers from MySQL); stated scope uncertainty; zero R-101 figure/citation leaks for C-02; strict citation grounding (no R-103 purifier on smart water meter queries); confidence policy calibrated to 0.80 on source conflict and single-source boundary; live Qdrant container connected. Evidence: `artifacts/e2e/phase2/` (6 JSON files). |
| **Phase 3** | **Derived Value, Security Refusal, SQL Query Display, Redirect (B1, B3, B4, B5)** | IN PROGRESS | Calculation disclosure, security refusal event logging, parameterized SQL text display, election redirect. |
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

---

## Phase 2 Verification Summary (Real Live Outputs & Strict Grounding)
- **B8 (Hardcoded Strings & Secrets Removed):**
  - Updated `EntitlementService.get_upgrade_path()` to dynamically source licensing contact email and portal URL from configuration settings/environment (`UPGRADE_CONTACT_EMAIL`, `UPGRADE_PORTAL_URL`) with defaults in `.env.example`.
  - Replaced hardcoded titles and publishers in tests with real MySQL catalog values (`Aquila Insights`, `Smart Water Metering: Industry Outlook 2024`).
- **B2 ("Which report should I trust?"):**
  - Replaced static response with dynamic catalog lookups from MySQL for both R-101 and R-102.
  - Eliminated "authoritative" and "verified" labels; explicitly articulated scope differences (R-101 full ecosystem USD 4.21B vs R-102 hardware USD 3.87B), forbade averaging, and offered human escalation to a senior CMR research analyst.
  - For unentitled client C-02: mentions R-101 exists, provides upgrade path, with ZERO R-101 figures and ZERO R-101 citations.
- **B6 (Citation Grounding & Documented Confidence Policy):**
  - Added `FactCheckerCritic.filter_citations_to_answer()`: strictly discards cross-topic chunks (e.g. R-103 water purifier on smart water meter questions).
  - Enforced confidence heuristic: lowers confidence to 0.80 on source conflict (R-101 vs R-102) and 0.80 on single-source boundary (C-02 on smart water meters). Documented that confidence is an evidence validation heuristic, not a calibrated Bayesian probability.
  - Strengthened `SYSTEM_INSTRUCTION` in `llm_service.py` to prevent hallucinating unprovided report IDs (e.g., R-104), and enhanced fallback synthesizer to format exact `[Report ID, p.Page]` citations.
- **B7 (Live Qdrant Server & Tenant Isolation):**
  - Resolved `qdrant` host resolution in `qdrant_service.py` for host environment.
  - Verified live Qdrant container connection: 25 chunks across 7 reports, indexed by `report_id`, `sector`, `access_type`.
- **Evidence Files Generated:**
  - `artifacts/e2e/phase2/test0_health.json`
  - `artifacts/e2e/phase2/C01-which-report-should-i-trust.json`
  - `artifacts/e2e/phase2/C02-which-report-should-i-trust.json`
  - `artifacts/e2e/phase2/C01-market-size-2024.json`
  - `artifacts/e2e/phase2/C02-market-size-2024.json`
  - `artifacts/e2e/phase2/C02-restricted-r101-direct-request.json`
  - `artifacts/e2e/phase2/phase2_summary.json`


