from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from tunip.service_config import get_service_config


service_config = get_service_config()
api_key_header = APIKeyHeader(name=service_config.api_key_name, auto_error=True)

def verify_api_key(api_key_header: str=Depends(api_key_header)):
    if api_key_header == service_config.api_key_token:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )