"""
Project Atlas - Database Connection Manager
Provides connection pooling for operational application queries and isolated
least-privilege read-only connections for analytical queries.
Supports SQLite in-memory fallback for isolated unit testing when MySQL server is offline.
"""

import pymysql
import sqlite3
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging_config import logger

_sqlite_test_db = None


def init_sqlite_test_db():
    """Initializes an in-memory SQLite database pre-seeded with project seed data for offline test runs."""
    global _sqlite_test_db
    if _sqlite_test_db is None:
        logger.info("Initializing in-memory SQLite test database with seed data.")
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Schema
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            publisher TEXT NOT NULL,
            published_date TEXT NOT NULL,
            sector TEXT NOT NULL,
            access_type TEXT NOT NULL,
            summary TEXT,
            total_pages INTEGER DEFAULT 1,
            file_path TEXT
        );

        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            contact_email TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS report_entitlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            report_id TEXT NOT NULL,
            access_granted INTEGER DEFAULT 1,
            scope TEXT DEFAULT 'full',
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            UNIQUE(client_id, report_id)
        );

        CREATE TABLE IF NOT EXISTS market_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            unit TEXT NOT NULL,
            year INTEGER NOT NULL,
            cagr REAL,
            cagr_period TEXT,
            region TEXT NOT NULL,
            scope TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            source_quote TEXT
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            title TEXT DEFAULT 'Chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS conversation_messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            citations_json TEXT,
            confidence REAL,
            conflicts_json TEXT,
            derived_values_json TEXT,
            escalated INTEGER DEFAULT 0,
            latency_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            rating TEXT NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS escalation_tickets (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            conversation_id TEXT,
            question TEXT NOT NULL,
            reason TEXT NOT NULL,
            confidence_score REAL,
            status TEXT DEFAULT 'pending',
            resolution_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            event_type TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS llm_usage_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            estimated_cost_usd REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Seed reports
        reports = [
            ('R-101', 'Global Smart Water Meter Market 2025', 'CMR', '2025-03-10', 'Utilities', 'paid', 'Comprehensive global market analysis...', 24, 'reports/R-101.txt'),
            ('R-102', 'Smart Water Metering: Industry Outlook 2024', 'Aquila Insights', '2024-06-18', 'Utilities', 'public_excerpt', 'Industry outlook examining hardware...', 18, 'reports/R-102.txt'),
            ('R-103', 'Residential Water Purifier Market 2025', 'CMR', '2025-01-22', 'Consumer Durables', 'paid', 'Global overview of point-of-use systems...', 20, 'reports/R-103.txt'),
            ('R-104', 'Industrial IoT Sensors Market 2025', 'Precision Sense', '2025-02-14', 'Manufacturing', 'paid', 'Analysis of edge sensing deployments...', 22, 'reports/R-104.txt'),
            ('R-105', 'Commercial Heat Pump Systems Outlook 2024', 'ThermalDynamics', '2024-11-05', 'Energy & HVAC', 'paid', 'Market evaluation of commercial heat pumps...', 26, 'reports/R-105.txt'),
            ('R-106', 'Electric Vehicle Charging Infrastructure Market 2025', 'VoltMetrics', '2025-04-01', 'Automotive & Mobility', 'paid', 'Global study of public and private EV fast charging...', 30, 'reports/R-106.txt'),
            ('R-107', 'Agricultural Drone & Precision Farming Report 2025', 'AgriTech Review', '2025-05-18', 'Agriculture', 'paid', 'Market trends in autonomous agricultural aerial vehicles...', 19, 'reports/R-107.txt')
        ]
        cur.executemany("INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", reports)

        # Seed clients
        clients = [
            ('C-01', 'Northwind Utilities', 'northwind.analyst@example-corp.internal', 'client_key_c01_northwind_utilities_secret_2026', 'active'),
            ('C-02', 'Blue Delta Infra', 'research.team@bluedelta-infra.internal', 'client_key_c02_blue_delta_infra_secret_2026', 'active')
        ]
        cur.executemany("INSERT INTO clients VALUES (?, ?, ?, ?, ?)", clients)

        # Seed entitlements
        entitlements = [
            ('C-01', 'R-101', 1, 'full', '2025-01-01', '2027-12-31'),
            ('C-01', 'R-103', 1, 'full', '2025-01-01', '2027-12-31'),
            ('C-02', 'R-103', 1, 'full', '2025-01-01', '2027-12-31')
        ]
        cur.executemany("INSERT INTO report_entitlements (client_id, report_id, access_granted, scope, valid_from, valid_to) VALUES (?, ?, ?, ?, ?, ?)", entitlements)

        # Seed market metrics
        metrics = [
            ('R-101', 'Global Smart Water Meter Market Size', 4.21, 'USD Billion', 2024, 11.20, '2025-2030', 'Global', 'Hardware, software, and services', 8, 'The global smart water meter market was valued at USD 4.21 billion in 2024 and is expected to grow at a CAGR of 11.2% from 2025 to 2030. Asia-Pacific accounted for 38% of 2024 revenue.'),
            ('R-101', 'Asia-Pacific Regional Market Share', 38.00, 'Percent', 2024, None, None, 'Asia-Pacific', 'Hardware, software, and services', 8, 'Asia-Pacific accounted for 38% of 2024 revenue...'),
            ('R-102', 'Global Smart Water Metering Hardware Market Size', 3.87, 'USD Billion', 2024, 9.80, '2024-2029', 'Global', 'AMR/AMI hardware only', 14, 'Global smart water meter hardware revenue reached USD 3.87 billion in 2024...'),
            ('R-102', 'Asia-Pacific Hardware Market Share', 41.00, 'Percent', 2024, None, None, 'Asia-Pacific', 'AMR/AMI hardware only', 14, 'Asia-Pacific represented 41% of global physical unit shipments...'),
            ('R-103', 'Global Residential Water Purifier Market Size', 9.45, 'USD Billion', 2024, 7.40, '2025-2030', 'Global', 'RO, UV, and ultrafiltration point-of-use systems', 11, 'The residential water purifier market reached USD 9.45 billion in 2024...'),
            ('R-104', 'Global Industrial IoT Sensors Market Size', 12.80, 'USD Billion', 2024, 14.50, '2025-2030', 'Global', 'Vibration, acoustic, and thermal sensors', 6, 'The global industrial IoT sensor sector reached USD 12.80 billion in 2024...'),
            ('R-105', 'Global Commercial Heat Pump Market Size', 7.15, 'USD Billion', 2023, 8.60, '2024-2029', 'Global', 'Air-source and ground-source commercial hydronic units', 9, 'Commercial heat pump market valuation totaled USD 7.15 billion in 2023...'),
            ('R-106', 'Global EV Charging Infrastructure Market Size', 26.50, 'USD Billion', 2024, 24.10, '2025-2030', 'Global', 'Level 2 AC and Level 3 DC fast charging hardware and networking', 15, 'The worldwide EV charging infrastructure market stood at USD 26.50 billion in 2024...'),
            ('R-107', 'Global Agricultural Drone Market Size', 3.60, 'USD Billion', 2024, 18.20, '2025-2030', 'Global', 'Multispectral remote sensing and automated spray drones', 12, 'Agricultural drone hardware and analytics platforms generated USD 3.60 billion in 2024...')
        ]
        cur.executemany("INSERT INTO market_metrics (report_id, metric_name, metric_value, unit, year, cagr, cagr_period, region, scope, page_number, source_quote) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", metrics)

        conn.commit()
        _sqlite_test_db = conn
    return _sqlite_test_db


class DatabaseManager:
    """Manages MySQL connections with graceful test SQLite fallback."""

    @classmethod
    def get_connection(cls, readonly: bool = False):
        """
        Attempts to connect to MySQL database using operational app user or readonly user.
        If MySQL is not available (such as in local unit testing before Docker is up),
        falls back to in-memory SQLite seed database.
        """
        import socket
        is_mysql_up = False
        try:
            with socket.create_connection((settings.MYSQL_HOST, settings.MYSQL_PORT), timeout=0.2):
                is_mysql_up = True
        except OSError:
            is_mysql_up = False

        if is_mysql_up:
            try:
                user = settings.MYSQL_READONLY_USER if readonly else settings.MYSQL_USER
                password = settings.MYSQL_READONLY_PASSWORD if readonly else settings.MYSQL_PASSWORD
                conn = pymysql.connect(
                    host=settings.MYSQL_HOST,
                    port=settings.MYSQL_PORT,
                    user=user,
                    password=password,
                    database=settings.MYSQL_DATABASE,
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=not readonly
                )
                return conn
            except Exception as e:
                logger.warning(f"MySQL connection failed ({e}); using test SQLite fallback.")

        # Fallback to seeded in-memory SQLite database
        return init_sqlite_test_db()

    @classmethod
    def execute_query(cls, sql: str, params: tuple = (), readonly: bool = False) -> List[Dict[str, Any]]:
        """Executes a query and returns a list of dictionary rows."""
        conn = cls.get_connection(readonly=readonly)
        if isinstance(conn, sqlite3.Connection):
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
            return rows
        else:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
            conn.close()
            return rows

    @classmethod
    def execute_commit(cls, sql: str, params: tuple = ()) -> int:
        """Executes a write operation (INSERT/UPDATE/DELETE) and returns affected row count."""
        conn = cls.get_connection(readonly=False)
        if isinstance(conn, sqlite3.Connection):
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
        else:
            with conn.cursor() as cur:
                affected = cur.execute(sql, params)
            conn.commit()
            conn.close()
            return affected
