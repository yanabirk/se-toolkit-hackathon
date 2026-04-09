import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from lms_backend.settings import settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if not settings.api_key:
        return ""
    if credentials is None or credentials.credentials != settings.api_key:
        logger.warning("auth_failure", extra={"event": "auth_failure"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return credentials.credentials
