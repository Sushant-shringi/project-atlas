# Project Atlas — Fixup Progress Tracker

This document tracks progress on the final strict fix-and-verify pass in priority order.

---

## Progress Overview

| Phase | Description | Status | Evidence / Notes |
| :--- | :--- | :---: | :--- |
| **Phase 0** | **Baseline Inspection** | **DONE** | Docker containers healthy, branch clean, background pytest cleared, Playwright Chromium verified on host. |
| **Phase 1** | **Portal UI & Tenant Switching (A1-A7)** | **DONE** | Real Playwright Chromium verification: bidirectional switching (C-01<->C-02 repeated), scoped message history, feedback saved to MySQL (id: 4), confidence N/A on refusals, and graceful offline error recovery. Evidence: `artifacts/e2e/phase1/phase1_evidence.json` + 8 screenshots. |
| **Phase 2** | **Entitlement & Answer Correctness (B2, B6, B7, B8)** | **DONE** | No hardcoded template answers; dynamic metadata (titles/publishers from MySQL); stated scope uncertainty; zero R-101 figure/citation leaks for C-02; strict citation grounding (no R-103 purifier on smart water meter queries); confidence policy calibrated to 0.80 on source conflict and single-source boundary; live Qdrant container connected. Evidence: `artifacts/e2e/phase2/` (6 JSON files). |
| **Phase 3** | **Derived Value, Security Refusal, SQL Query Display, Redirect (B1, B3, B4, B5)** | **DONE** | APAC 2030 projection shows both 5/6 period values (2.72B/3.02B), inputs, CAGR, formula, and base-year ambiguity; C-02 properly refused with zero leak; prompt injection refused with security violation and logged to MySQL `audit_events` (Row ID 6); parameterized SQL query displayed in markdown; out-of-scope election queries redirected with concrete research suggestions. Evidence: `artifacts/e2e/phase3/` (5 JSON files + 5 screenshots). |
| **Phase 4** | **SQL Timeout & DB Write Denial (D1), Gemini & Fallback Eval (C1, C5)** | **DONE** | Least-privilege DB write denial (MySQL 1142 on INSERT/UPDATE/DELETE/DROP and sensitive SELECT), 2s SQL read timeout, 26/26 (100%) eval pass on live Gemini (932ms avg) and 26/26 on Fallback (846ms avg). Evidence: `artifacts/e2e/phase4/` (4 files). |
| **Phase 5** | **Documentation Updates (C2, C3, C4, D2, D3)** | **DONE** | Updated EVALUATION_REPORT.md (side-by-side Gemini vs Fallback table, 5 real observed failure analyses, token costs & latency profiles), updated README.md with IPv6 troubleshooting & live vs fallback modes. |
| **Phase 6** | **Final Verification & Full Regression Matrix** | **DONE** | Full regression matrix executed, 42 pytest unit/integration tests passed, clean git tree verified, secrets audit passed (zero .env in history), all 32 evidence files saved in artifacts/e2e/. |

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

---

## Phase 3 Verification Summary (Derived Value, Security Refusals, SQL & Browser UI)
- **B1 (APAC 2030 Derived Projection & Ambiguity Disclosure):**
  - Fully articulated both 5-period compounding (USD 2.72 Billion) and 6-period compounding (USD 3.02 Billion).
  - Explicitly disclosed inputs ($4.21B global 2024 base, 38% APAC share -> $1.60B regional base, 11.2% CAGR), formula $FV = PV \times (1 + \text{CAGR})^n$, and base-year reporting ambiguity.
  - Verified entitlement boundary: C-02 request for calculation is refused with license upgrade contact and ZERO figure leakage.
- **B3 (Security Refusal & Real-Time Audit Event Logging):**
  - Expanded `PromptDefense.SUSPICIOUS_PATTERNS` to catch instruction-ignoring and email extraction directives.
  - Returns explicit security policy violation notice with 0.0 confidence.
  - Recorded security audit event row in MySQL table `audit_events` (verified row inserted with `event_type="PROMPT_INJECTION_DETECTED"`, client_id, and matched patterns JSON).
- **B4 (Parameterized SQL Query Display):**
  - For catalog questions ("Which sector has the most reports?"), formats and displays the exact parameterized SQL query executed (`SELECT sector, COUNT(*) as report_count FROM reports GROUP BY sector ORDER BY report_count DESC LIMIT 50;`) in a markdown code block alongside the aggregated breakdown.
- **B5 (Out-of-Scope Political Election Redirect):**
  - Clarified boundaries: returns polite refusal for election queries and provides bulleted clickable/copyable examples of valid market research inquiries (market sizing, catalog analytics, methodology comparison, derived projections).
- **Playwright Browser UI Evidence (Chromium):**
  - Verified all 5 scenarios directly inside the CI3 Portal UI and captured real host screenshots:
    - `artifacts/e2e/phase3/browser_c01_apac_2030.png`
    - `artifacts/e2e/phase3/browser_c02_apac_2030_refusal.png`
    - `artifacts/e2e/phase3/browser_c01_sql_display.png`
    - `artifacts/e2e/phase3/browser_c01_security_refusal.png`
    - `artifacts/e2e/phase3/browser_c01_election_redirect.png`
- **Evidence Files Generated:**
  - `artifacts/e2e/phase3/C01-apac-2030-projection.json`
  - `artifacts/e2e/phase3/C02-apac-2030-projection-refusal.json`
  - `artifacts/e2e/phase3/C01-security-injection-refusal.json`
  - `artifacts/e2e/phase3/mysql-latest-audit-event.json`
  - `artifacts/e2e/phase3/C01-sql-query-display.json`
  - `artifacts/e2e/phase3/C01-election-redirect.json`
  - `artifacts/e2e/phase3/phase3_summary.json`

---

## Phase 4 Verification Summary (DB Least-Privilege, SQL Timeout, and Dual Eval Harness)
- **D1 (Least-Privilege DB Permissions):**
  - Tested `atlas_readonly` user against prohibited write operations: `INSERT`, `UPDATE`, `DELETE`, `DROP`. All denied with MySQL Error 1142 (`INSERT command denied to user 'atlas_readonly'@'%' for table 'reports'`).
  - Tested `atlas_readonly` against sensitive operational tables (`clients`, `audit_events`). All denied with MySQL Error 1142 (`SELECT command denied to user 'atlas_readonly'@'%' for table 'clients'`).
  - Allowed operations verified: `SELECT` on analytical tables (`reports`, `report_sections`, `report_tables`) executes successfully.
  - Evidence: `artifacts/e2e/phase4/d1_db_permissions.json`.
- **D1 (SQL Query Execution Timeout):**
  - Tested query execution with runaway query `SELECT SLEEP(5);` against `get_readonly_engine()` with `read_timeout=2`.
  - Terminated after 2.00s with `OperationalError: (2013, 'Lost connection to MySQL server during query (timed out)')`.
  - Evidence: `artifacts/e2e/phase4/d1_sql_timeout.json`.
- **C1 & C5 (Live Gemini Benchmark Evaluation):**
  - Ran benchmark suite against live API container (`atlas_api`): **26/26 (100.0%) PASSED**.
  - Average Latency: 932.3 ms.
  - Metrics:
    - Answer Correctness: 100.0% (26/26)
    - Citation Accuracy: 100.0% (26/26)
    - Refusal Accuracy: 100.0% (26/26)
    - Conflict Detection: 100.0% (26/26)
    - Entitlement Leakage Rate: 0.0% (0/26)
    - Escalation Correctness: 100.0% (26/26)
  - Evidence: `artifacts/e2e/phase4/eval_results_live_gemini.json`.
- **C1 & C5 (Deterministic Fallback Benchmark Evaluation):**
  - Ran benchmark suite in fallback mode (`--mode fallback --use-api`): **26/26 (100.0%) PASSED**.
  - Average Latency: 846.5 ms.
  - All 6 benchmark metrics met.
  - Evidence: `artifacts/e2e/phase4/eval_results_fallback.json`.
- **Cost & Token Tracking (Live MySQL `llm_usage_records`):**
  - Tracked across 33 live Gemini calls: 51,110 tokens, total estimated cost of $0.005295.

---

## Phase 5 Verification Summary (Comprehensive Documentation & Failure Analyses)
- **C2 (5 Real Observed Failure Analyses):** Documented in `docs/EVALUATION_REPORT.md` Section 5 with exact prompts, system errors, root causes, engineering fixes, and added regression tests:
  1. CI3 Portal relative redirect loop & host cross-port navigation (`header('Location: /chat'); exit;`).
  2. Cross-topic vector semantic bleed & citation hallucination (`FactCheckerCritic.filter_citations_to_answer()`).
  3. LLM associative hallucination of unprovided report IDs (`SYSTEM_INSTRUCTION` negative constraints & critic whitelist).
  4. Obscure query topic overlap false confidence (`FactCheckerCritic` generic domain word stop-list).
  5. MySQL PyMySQL snapshot isolation masking newly committed audit rows in tests (`autocommit=True` resolution).
- **D2 & C1 (Dual Benchmark Comparison Table):** Embedded side-by-side comparison in `docs/EVALUATION_REPORT.md` Section 2 comparing Live Gemini (932.3ms, $0.0053 cost) vs Deterministic Fallback (846.5ms, $0.00 cost) with 100% pass rates across all 6 PDF benchmark criteria.
- **C3 & C4 (Pricing, Latency & Limitations):** Documented subsystem latency breakdowns, MySQL `llm_usage_records` accounting, 15 RPM free-tier rate limit mitigation, and Windows IPv6 `127.0.0.1` binding.

---

## Phase 6 Verification Summary (Final Regression & Clean Submission State)
- **Pytest Automated Test Suite:**
  - Ran full unit and integration test suite across all 7 test modules: **42 passed, 0 failed** (in 462s).
  - Modules passed: `test_agent_tools.py` (6), `test_cache_and_sql_limits.py` (9), `test_entitlements.py` (4), `test_ingestion.py` (4), `test_api.py` (7), `test_workflow.py` (8), `test_gemini_writer.py` (4).
- **Evaluation Harness Matrix:**
  - Live Gemini API Suite: **26/26 (100.0%) PASSED**, avg latency 932.3ms, zero entitlement leakage (`artifacts/e2e/phase4/eval_results_live_gemini.json`).
  - Fallback Suite: **26/26 (100.0%) PASSED**, avg latency 846.5ms, zero token fabrication (`artifacts/e2e/phase4/eval_results_fallback.json`).
- **Secrets & Git Tree Audit:**
  - Git working tree verified completely clean (`git status`).
  - Git history verified with `git log --all --full-history -- "**.env"`: zero `.env` commits across entire repository history.
  - `.gitignore` verified: `.env`, `artifacts/`, and `*.log` strictly ignored.
- **Evidence Files:** 32 raw artifacts preserved in `artifacts/e2e/` spanning HTTP JSON responses, SQL rows, MySQL audit events, and Chromium browser UI screenshots.





