"""API dependencies and shared utilities."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Security (optional, for future authentication)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Get current user from bearer token (placeholder for future auth).

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        User ID or None
    """
    if credentials is None:
        return None

    # TODO: Implement actual JWT validation
    token = credentials.credentials
    return "anonymous"


async def require_auth(
    user: Optional[str] = Depends(get_current_user)
) -> str:
    """
    Require authentication (placeholder for future).

    Args:
        user: User from get_current_user dependency

    Returns:
        User ID

    Raises:
        HTTPException: If not authenticated
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
