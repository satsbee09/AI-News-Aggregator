from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.config import settings

INTERNAL_API_KEY_HEADER = APIKeyHeader(name="X-Internal-Secret", auto_error=False)

async def verify_internal_secret(api_key: str = Security(INTERNAL_API_KEY_HEADER)):
    """Enforces X-Internal-Secret header validation on internal FastAPI routes."""
    if not api_key or api_key != settings.INTERNAL_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing X-Internal-Secret header."
        )
    return api_key
