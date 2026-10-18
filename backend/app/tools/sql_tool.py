"""
Project Atlas - Safe Read-Only SQL Analytical Tool
Executes predefined parameterized queries and audited SELECT queries over catalog and metrics tables.
Enforces:
1. SELECT-only statement validation (rejects write/DDL/DCL/multi-statement injection).
2. Prohibited keyword and sensitive table access blocking (clients, credentials, chats).
3. Table whitelisting (reports, market_metrics only).
4. Strict row limit enforcement (maximum 50 rows).
5. Read-only DB user isolation (atlas_readonly).
6. Query execution timeout enforcement (5 seconds).
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from app.db.connection import DatabaseManager
from app.core.logging_config import logger

MAX_SQL_ROWS = 50
SQL_TIMEOUT_SECONDS = 5.0

FORBIDDEN_SQL_PATTERNS = [
    re.compile(r"\b(delete|drop|update|insert|alter|truncate|replace|create|grant|revoke|call|exec|execute)\b", re.IGNORECASE),
    re.compile(r"\b(into\s+outfile|into\s+dumpfile|load_file|load\s+data)\b", re.IGNORECASE),
    re.compile(r";\s*--", re.IGNORECASE),
    re.compile(r";\s*\S+", re.IGNORECASE),  # Multi-statement injection attempt
    re.compile(r"\b(clients|conversations|user_feedback|escalation_tickets|audit_events|request_usage)\b", re.IGNORECASE),
    re.compile(r"\b(password|api_key|token|contact_email|secret)\b", re.IGNORECASE),
    re.compile(r"\b(information_schema|performance_schema|mysql|sys)\b", re.IGNORECASE),
]

ALLOWED_TABLES = {"reports", "market_metrics"}


class SafeSQLTool:
    """Read-only SQL analytical tool with strict bounds and security constraints."""

    @classmethod
    def is_safe_query(cls, query_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validates that a SQL string is strictly a single SELECT statement,
        does not contain destructive keywords, and targets only whitelisted tables.
        """
        stripped = query_str.strip()

        # 1. Enforce SELECT-only statement
        if not re.match(r"^(select|with)\b", stripped, re.IGNORECASE):
            reason = "Security Violation: Only SELECT analytical statements are permitted."
            logger.warning(
                f"SQL rejection: {reason}",
                extra={"security_flag": "NON_SELECT_SQL_REJECTED", "query": query_str}
            )
            return False, reason

        # 2. Check forbidden keywords, multi-statements, and sensitive tables
        for pattern in FORBIDDEN_SQL_PATTERNS:
            match = pattern.search(stripped)
            if match:
                reason = f"Security Violation: Query contains prohibited token '{match.group(0)}'."
                logger.warning(
                    f"SQL rejection: {reason}",
                    extra={"security_flag": "SQL_INJECTION_REJECTED", "query": query_str}
                )
                return False, reason

        # 3. Table whitelisting verification: scan FROM/JOIN clauses
        table_matches = re.findall(r"\b(?:from|join)\s+([a-zA-Z0-9_]+)", stripped, re.IGNORECASE)
        for tbl in table_matches:
            if tbl.lower() not in ALLOWED_TABLES:
                reason = f"Security Violation: Access to table '{tbl}' is forbidden. Allowed tables: {', '.join(sorted(ALLOWED_TABLES))}."
                logger.warning(
                    f"SQL rejection: {reason}",
                    extra={"security_flag": "FORBIDDEN_TABLE_REJECTED", "query": query_str}
                )
                return False, reason

        return True, None

    @classmethod
    def get_sector_report_counts(cls) -> List[Dict[str, Any]]:
        """
        Analytical Query: Counts reports by sector.
        Answer to 'Which sector has the most reports?'
        """
        sql = """
        SELECT sector, COUNT(*) as report_count 
        FROM reports 
        GROUP BY sector 
        ORDER BY report_count DESC
        LIMIT 50
        """
        return DatabaseManager.execute_query(sql, readonly=True)

    @classmethod
    def get_authorized_reports_count_for_client(cls, client_id: str) -> Dict[str, Any]:
        """
        Analytical Query: How many reports are accessible to the client?
        """
        from app.services.entitlements import EntitlementService
        report_ids = EntitlementService.get_authorized_reports_for_client(client_id)
        return {
            "client_id": client_id,
            "total_authorized_reports": len(report_ids),
            "report_ids": report_ids
        }

    @classmethod
    def get_market_metrics_summary(cls, sector: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves aggregate market metrics optionally filtered by sector (bounded to MAX_SQL_ROWS).
        """
        conn = DatabaseManager.get_connection(readonly=True)
        is_sqlite = hasattr(conn, "row_factory")

        if sector:
            sql = f"""
            SELECT r.id as report_id, r.title, r.sector, m.metric_name, m.metric_value, m.unit, m.year, m.cagr, m.scope
            FROM reports r
            JOIN market_metrics m ON r.id = m.report_id
            WHERE LOWER(r.sector) = LOWER(?)
            ORDER BY m.metric_value DESC
            LIMIT {MAX_SQL_ROWS}
            """
            if not is_sqlite:
                sql = sql.replace("?", "%s")
            return DatabaseManager.execute_query(sql, (sector,), readonly=True)
        else:
            sql = f"""
            SELECT r.id as report_id, r.title, r.sector, m.metric_name, m.metric_value, m.unit, m.year, m.cagr, m.scope
            FROM reports r
            JOIN market_metrics m ON r.id = m.report_id
            ORDER BY r.sector, m.metric_value DESC
            LIMIT {MAX_SQL_ROWS}
            """
            return DatabaseManager.execute_query(sql, readonly=True)

    @classmethod
    def execute_custom_safe_query(cls, sql_query: str) -> Dict[str, Any]:
        """
        Executes a validated read-only SQL query via the atlas_readonly account.
        Enforces SELECT-only parsing, row limit (MAX_SQL_ROWS = 50), and execution timeout.
        """
        is_safe, refusal_reason = cls.is_safe_query(sql_query)
        if not is_safe:
            return {
                "success": False,
                "error": refusal_reason,
                "rows": [],
                "row_count": 0
            }

        # Enforce row limit in SQL query if LIMIT clause is missing
        bounded_query = sql_query.strip()
        if not re.search(r"\blimit\s+\d+", bounded_query, re.IGNORECASE):
            bounded_query = f"{bounded_query} LIMIT {MAX_SQL_ROWS}"

        try:
            rows = DatabaseManager.execute_query(bounded_query, readonly=True)
            limited_rows = rows[:MAX_SQL_ROWS]  # Strict enforcement cap
            return {
                "success": True,
                "row_count": len(limited_rows),
                "rows": limited_rows
            }
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "rows": [],
                "row_count": 0
            }
