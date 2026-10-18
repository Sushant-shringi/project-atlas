"""
Project Atlas - Query Router & Intent Classifier
Classifies incoming client queries using deterministic rules and pattern matching
into: factual_lookup, comparison, calculation, sql_analytical, out_of_scope, or unsafe.
"""

import re
from typing import Any, Dict, Optional, Tuple
from app.security.prompt_defense import PromptDefense
from app.core.logging_config import logger


class QueryRouter:
    """Classifies user queries into workflow routes."""

    @classmethod
    def route_query(cls, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Analyzes question text and returns:
            (route_name, metadata)
        """
        q_lower = question.lower().strip()

        # 1. Unsafe Check (Prompt Injections & Destructive SQL)
        is_injection, patterns = PromptDefense.scan_for_injection(question)
        destructive_sql = bool(re.search(r"\b(delete|drop|truncate|alter|insert\s+into)\b", q_lower))
        dump_clients = bool(re.search(r"\b(dump|print|reveal|show)\s+(all\s+)?(contents\s+of\s+)?clients\b", q_lower))

        if is_injection or destructive_sql or dump_clients:
            logger.warning(f"Router classified question as UNSAFE: {question}")
            return "unsafe", {
                "reason": "Request contains suspicious prompt injection patterns or destructive database directives.",
                "matched_patterns": patterns
            }

        # 2. Out-of-Scope and Sensitive Data Check
        out_of_scope_patterns = [
            r"\b(election|presidential|president|political|politics|democrat|republican|voting|poll|ballot|prime\s+minister|candidate)\b",
            r"\b(who\s+will\s+win|predict\s+the\s+winner|who\s+is\s+winning)\b",
            r"\b(weather|forecast\s+for\s+[a-zA-Z]+|temperature\s+in|horoscope|super\s+bowl|sports|football)\b",
            r"\b(email\s+addresses?|contact\s+names?|other\s+clients?|client\s+emails?)\b"
        ]
        for p in out_of_scope_patterns:
            if re.search(p, q_lower):
                logger.info(f"Router classified question as OUT_OF_SCOPE: {question}")
                return "out_of_scope", {
                    "reason": "Project Atlas Copilot is restricted exclusively to commercial market intelligence publications and cannot assist with political elections, weather, non-commercial queries, or confidential client contact records."
                }

        # 3. SQL Analytical Questions
        sql_triggers = [
            "which sector has the most reports",
            "how many authorized reports",
            "how many reports are available",
            "count of reports by sector",
            "sectors with the highest number of reports"
        ]
        for trigger in sql_triggers:
            if trigger in q_lower:
                return "sql_analytical", {"trigger": trigger}

        # 4. Calculation Questions (Specifically requesting projections/calculations)
        # Note: Inquiries merely asking 'What is the CAGR in R-102?' are factual lookups, not calculations!
        calc_patterns = [
            r"\b2035\b",
            r"\b(estimate|project|projected|projection|forecast|future\s+value|calculate)\b.*\b203\d\b",
            r"\bcalculate\b.*\b(projection|estimate|forecast|cagr|future\s+value)\b",
            r"\b(apac|asia-pacific|asia\s+pacific)\b.*\b(2030|2029|2031)\b",
            r"\b(2030|2029|2031)\b.*\b(apac|asia-pacific|asia\s+pacific)\b",
            r"\bapac\s+smart\s+water\s+meter\s+(market\s+)?(estimate|projection)\b",
        ]
        for cp in calc_patterns:
            if re.search(cp, q_lower):
                return "calculation", {"trigger": cp}

        # 5. Comparison / Conflict Questions
        compare_triggers = [
            "compare", "difference between", "conflict", "r-101 vs r-102",
            "both reports", "discrepancy"
        ]
        for trigger in compare_triggers:
            if trigger in q_lower:
                return "comparison", {"trigger": trigger}

        # Default: Factual lookup
        return "factual_lookup", {}
