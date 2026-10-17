"""
Project Atlas - API Security & Authentication Dependencies
Enforces header-based client authentication and administrative authorization.
"""

from typing import Any, Dict, Optional
from fastapi import Header, HTTPException, Security, status
from app.core.config import settings
from app.services.entitlements import EntitlementService
from app.core.logging_config import logger


def get_current_client(
    x_client_key: Optional[str] = Header(None, alias="X-Client-Key"),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI security dependency: Authenticates client by API key.
    Accepts either X-Client-Key header or Authorization: Bearer <key>.
    """
    api_key = x_client_key
    if not api_key and authorization and authorization.startswith("Bearer "):
        api_key = authorization.split("Bearer ", 1)[1].strip()

    if not api_key:
        logger.warning("Unauthenticated request: missing API key header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid client API key via X-Client-Key or Bearer token."
        )

    client = EntitlementService.get_client_by_api_key(api_key)
    if not client:
        logger.warning("Authentication failed: invalid client API key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired client API key."
        )

    return client


def get_admin_user(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")
) -> bool:
    """
    FastAPI dependency: Protects administrative endpoints (such as /ingest).
    """
    if not x_admin_key or x_admin_key != settings.ADMIN_API_KEY:
        logger.warning("Admin authorization failed: invalid X-Admin-Key.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrative privileges required."
        )
    return True
