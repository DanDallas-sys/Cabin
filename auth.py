from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import get_settings

settings = get_settings()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(api_key_header)):
    """
    Dependency — protect any endpoint by adding:
        db: Session = Depends(get_db), _: str = Depends(require_api_key)
    """
    if not settings.api_key:
        # If no key is configured, block all requests
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured on server"
        )
    if key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return key
