import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

_API_KEY_HEADER = APIKeyHeader(name="GDEV_API_TOKEN", auto_error=False)

_EXPECTED_TOKEN: str = os.getenv("GDEV_API_TOKEN", "dev-token-changeme")


def verify_token(api_key: str = Security(_API_KEY_HEADER)) -> str:
    if not api_key or api_key != _EXPECTED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing GDEV_API_TOKEN header",
        )
    return api_key
