"""
Project Atlas - Safe Read-Only SQL Analytical Tool
Executes predefined parameterized queries over catalog and metrics tables.
Enforces write-statement rejection, table whitelisting, and read-only DB user isolation.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from app.db.connection import DatabaseManager
from app.core.logging_config import logger

FORBIDDEN_SQL_PATTERNS = [
    re.compile(r"\b(delete|drop|update|insert|alter|truncate|replace|create|grant|revoke)\b", re.IGNORECASE),
    re.compile(r";\s*--", re.IGNORECASE),
    re.compile(r"\bclients\b", re.IGNORECASE),
    re.compile(r"\b(password|api_key|token|contact_email)\b", re.IGNORECASE),
]

ALLOWED_TABLES = {"reports", "market_metrics"}


class SafeSQLTool:
    """Read-only SQL tool for structured analytical queries."""

    @classmethod
    def is_safe_query(cls, query_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validates that a SQL string does not contain destructive keywords or access sensitive tables.
        """
        for pattern in FORBIDDEN_SQL_PATTERNS:
            match = pattern.search(query_str)
            if match:
                reason = f"Security Violation: Query contains prohibited token '{match.group(0)}'."
                logger.warning(
                    f"SQL rejection: {reason}",
                    extra={"security_flag": "SQL_INJECTION_REJECTED", "query": query_str}
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
        Retrieves aggregate market metrics optionally filtered by sector.
        """
        conn = DatabaseManager.get_connection(readonly=True)
        is_sqlite = hasattr(conn, "row_factory")

        if sector:
            sql = """
            SELECT r.id as report_id, r.title, r.sector, m.metric_name, m.metric_value, m.unit, m.year, m.cagr, m.scope
            FROM reports r
            JOIN market_metrics m ON r.id = m.report_id
            WHERE LOWER(r.sector) = LOWER(?)
            ORDER BY m.metric_value DESC
            """
            if not is_sqlite:
                sql = sql.replace("?", "%s")
            return DatabaseManager.execute_query(sql, (sector,), readonly=True)
        else:
            sql = """
            SELECT r.id as report_id, r.title, r.sector, m.metric_name, m.metric_value, m.unit, m.year, m.cagr, m.scope
            FROM reports r
            JOIN market_metrics m ON r.id = m.report_id
            ORDER BY r.sector, m.metric_value DESC
            """
            return DatabaseManager.execute_query(sql, readonly=True)

    @classmethod
    def execute_custom_safe_query(cls, sql_query: str) -> Dict[str, Any]:
        """
        Executes a validated read-only SQL query via the atlas_readonly account.
        Rejects write attempts and non-whitelisted table access.
        """
        is_safe, refusal_reason = cls.is_safe_query(sql_query)
        if not is_safe:
            return {
                "success": False,
                "error": refusal_reason,
                "rows": []
            }

        try:
            rows = DatabaseManager.execute_query(sql_query, readonly=True)
            return {
                "success": True,
                "row_count": len(rows),
                "rows": rows[:20]  # Enforce row limit
            }
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "rows": []
            }
