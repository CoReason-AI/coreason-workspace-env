import os
import jwt
from typing import Optional
from fastapi import Request, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

class UserIdentity(BaseModel):
    user_id: str
    email: str
    roles: list[str]
    session_id: str

# In a CISO-grade architecture, the actual OAuth2 flow (NextAuth.js) happens at the Edge Proxy (Next.js).
# This FastAPI server strictly validates the resulting JWT issued by that edge proxy or Azure AD.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_jwt_secret() -> str:
    # Strict SSOT: No default fallback
    return os.environ["JWT_SECRET_KEY"]

def verify_token(token: str) -> UserIdentity:
    """
    Verifies the JWT token and extracts the UserIdentity.
    """
    try:
        payload = jwt.decode(
            token, 
            get_jwt_secret(), 
            algorithms=["HS256"], 
            audience="coreason-platform"
        )
        return UserIdentity(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            roles=payload.get("roles", []),
            session_id=payload.get("sid", "default-session")
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def get_current_user(token: str = Security(oauth2_scheme)) -> UserIdentity:
    """
    FastAPI Dependency to inject the current authenticated user into endpoints.
    """
    return verify_token(token)

async def get_current_supervisor(user: UserIdentity = Security(get_current_user)) -> UserIdentity:
    """
    RBAC Enforcement: Ensures the user has the 'Supervisor' role required for JIT approval.
    """
    if "Supervisor" not in user.roles:
        raise HTTPException(status_code=403, detail="Supervisory privileges required.")
    return user
