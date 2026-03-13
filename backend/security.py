from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
import logging

from config import WHISPER_API_KEY

logger = logging.getLogger(__name__)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == WHISPER_API_KEY:
        return api_key
    logger.warning(f"Invalid API key attempt")
    raise HTTPException(status_code=403, detail="Could not validate credentials")
