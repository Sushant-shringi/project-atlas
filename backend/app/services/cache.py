"""
Project Atlas - Tenant- and Entitlement-Isolated Cache
Implements cryptographic tenant isolation for query response caching.
Guarantees that cached answers for Client A (e.g., C-01) can never be returned to Client B (e.g., C-02),
even when asking identical questions.
"""

import hashlib
import time
from typing import Any, Dict, List, Optional
from app.core.logging_config import logger


class TenantIsolatedCache:
    """
    In-memory response cache with cryptographic tenant and entitlement isolation.
    
    Cache Key Construction:
        Key = SHA256(client_id + "::" + sorted_entitlements_hash + "::" + normalized_query)
    
    Security Proof:
        1. Tenant Separation: client_id is part of the hash preimage.
        2. Entitlement Isolation: The hash of the client's current authorized report list is included.
           If entitlements change or differ between clients (e.g., C-01 has R-101+R-102, C-02 has R-102),
           the cache keys are mathematically distinct.
        3. Fresh Evaluation Policy: In Project Atlas, fresh entitlement evaluation is performed by default
           on every request against MySQL to prevent stale authorization bypass upon subscription revocation.
    """

    def __init__(self, default_ttl_seconds: int = 300):
        self._store: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds

    @staticmethod
    def compute_cache_key(client_id: str, authorized_reports: List[str], question: str) -> str:
        """Computes a SHA-256 hash incorporating tenant ID, entitlement set, and normalized query."""
        sorted_reports = ",".join(sorted(authorized_reports))
        normalized_q = " ".join(question.strip().lower().split())
        preimage = f"{client_id}::{sorted_reports}::{normalized_q}"
        return hashlib.sha256(preimage.encode("utf-8")).hexdigest()

    def get(self, client_id: str, authorized_reports: List[str], question: str) -> Optional[Dict[str, Any]]:
        """Retrieves a cached response if valid, unexpired, and strictly owned by this tenant context."""
        key = self.compute_cache_key(client_id, authorized_reports, question)
        entry = self._store.get(key)
        if not entry:
            return None

        # Check expiration
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None

        logger.info(f"Tenant-isolated cache hit for {client_id} [key={key[:8]}...]")
        return entry["data"]

    def set(
        self,
        client_id: str,
        authorized_reports: List[str],
        question: str,
        response_data: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> str:
        """Stores a response isolated to the tenant and their current entitlement set."""
        key = self.compute_cache_key(client_id, authorized_reports, question)
        ttl = ttl_seconds or self.default_ttl
        self._store[key] = {
            "client_id": client_id,
            "authorized_reports": sorted(authorized_reports),
            "data": response_data,
            "created_at": time.time(),
            "expires_at": time.time() + ttl
        }
        return key

    def clear(self):
        """Clears the cache store."""
        self._store.clear()

    def size(self) -> int:
        """Returns the number of entries currently in cache."""
        return len(self._store)


# Global singleton instance
response_cache = TenantIsolatedCache()
