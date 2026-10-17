"""
Project Atlas - Client Entitlements & Identity Service
Resolves caller identity, validates client API keys against caller-supplied client_id,
and queries the database for authorized reports.
"""

from typing import Any, Dict, List, Optional, Tuple
from app.db.connection import DatabaseManager
from app.core.logging_config import logger


class EntitlementService:
    """Manages client authentication, report permissions, and access policy enforcement."""

    @classmethod
    def get_client_by_api_key(cls, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Looks up an active client by their confidential API key.
        """
        if not api_key:
            return None
        sql = "SELECT id, company_name, contact_email, status FROM clients WHERE api_key = ? AND status = 'active'"
        # For MySQL vs SQLite compatibility, replace ? if using MySQL
        conn = DatabaseManager.get_connection()
        is_sqlite = hasattr(conn, "row_factory")
        if not is_sqlite:
            sql = sql.replace("?", "%s")
        rows = DatabaseManager.execute_query(sql, (api_key,))
        return rows[0] if rows else None

    @classmethod
    def validate_client_authorization(cls, api_key: str, requested_client_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Defense-in-depth: Verifies that the provided API key belongs to requested_client_id.
        Rejects requests where caller attempts to impersonate another client.
        """
        client = cls.get_client_by_api_key(api_key)
        if not client:
            return False, "Invalid or inactive API key.", None

        if client["id"] != requested_client_id:
            logger.warning(
                f"CLIENT SPOOFING ATTEMPT: Authenticated as {client['id']} but requested {requested_client_id}",
                extra={"security_flag": "CLIENT_SPOOFING_DETECTED", "client_id": client["id"]}
            )
            return False, f"Unauthorized: API key does not have permission to act for client {requested_client_id}.", None

        return True, "Authorized", client

    @classmethod
    def get_authorized_reports_for_client(cls, client_id: str) -> List[str]:
        """
        Returns the list of report IDs accessible to the client.
        Includes:
        1. Explicitly purchased reports in report_entitlements (full access)
        2. Public excerpt reports (e.g. R-102), which are available according to public excerpt scope.
        """
        sql = """
        SELECT report_id FROM report_entitlements 
        WHERE client_id = ? AND access_granted = 1
        """
        conn = DatabaseManager.get_connection()
        is_sqlite = hasattr(conn, "row_factory")
        if not is_sqlite:
            sql = sql.replace("?", "%s")

        rows = DatabaseManager.execute_query(sql, (client_id,))
        purchased_ids = [r["report_id"] for r in rows]

        # Fetch public excerpt reports
        sql_public = "SELECT id FROM reports WHERE access_type = 'public_excerpt'"
        public_rows = DatabaseManager.execute_query(sql_public)
        public_ids = [r["id"] for r in public_rows]

        # Combine uniquely
        authorized_ids = sorted(list(set(purchased_ids + public_ids)))
        return authorized_ids

    @classmethod
    def is_report_authorized(cls, client_id: str, report_id: str) -> bool:
        """Checks if a single report ID is accessible to the client."""
        authorized = cls.get_authorized_reports_for_client(client_id)
        return report_id in authorized

    @classmethod
    def get_report_metadata(cls, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves catalog metadata for a report."""
        sql = "SELECT id, title, publisher, published_date, sector, access_type, summary FROM reports WHERE id = ?"
        conn = DatabaseManager.get_connection()
        is_sqlite = hasattr(conn, "row_factory")
        if not is_sqlite:
            sql = sql.replace("?", "%s")
        rows = DatabaseManager.execute_query(sql, (report_id,))
        return rows[0] if rows else None

    @classmethod
    def get_upgrade_path(cls, report_id: str) -> Dict[str, str]:
        """Provides an access upgrade request route when a report is restricted."""
        meta = cls.get_report_metadata(report_id)
        title = meta["title"] if meta else f"Report {report_id}"
        return {
            "report_id": report_id,
            "title": title,
            "access_status": "Restricted (Paid Subscription Required)",
            "action": "Request Report License Upgrade",
            "contact_email": "subscriptions@cognitivemarketresearch.com",
            "upgrade_url": f"https://portal.cognitivemarketresearch.com/reports/{report_id}/upgrade"
        }

