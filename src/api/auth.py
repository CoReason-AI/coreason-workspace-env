from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Validates the bearer token.
    For demonstration/testing, it expects 'coreason-dev-token'.
    In production, this would decode a JWT and validate against an identity provider.
    """
    expected_token = os.getenv("API_SECRET_TOKEN", "coreason-dev-token")
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user": "authenticated"}
