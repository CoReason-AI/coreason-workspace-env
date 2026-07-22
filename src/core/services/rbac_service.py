import logging
from typing import List, Optional, Dict
from pydantic import BaseModel
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class UserIdentity(BaseModel):
    user_id: str
    tenant_id: str
    roles: List[str]

class RbacService:
    """
    Role-Based Access Control (RBAC) Service.
    Authenticates and authorizes humans interacting with the platform.
    """
    
    def __init__(self):
        # In a real system, this would query Postgres. 
        # For this prototype, we'll maintain an in-memory mock or rely on JWT claims passed from Dify.
        self._mock_users = {
            "admin-user-123": ["viewer", "developer", "admin"],
            "dev-user-456": ["viewer", "developer"],
            "viewer-user-789": ["viewer"]
        }

    def authenticate_human(self, user_id: str, tenant_id: str, provided_roles: Optional[List[str]] = None) -> UserIdentity:
        """
        Identifies the human user and constructs their RBAC identity.
        """
        # Fallback to mock lookup if roles are not provided via JWT
        roles = provided_roles or self._mock_users.get(user_id, ["viewer"])
        logger.debug(f"Authenticated human: {user_id} with roles {roles}")
        return UserIdentity(user_id=user_id, tenant_id=tenant_id, roles=roles)

    def require_role(self, identity: UserIdentity, required_role: str):
        """
        Enforces that the user has the required role. Raises an exception if unauthorized.
        """
        if required_role not in identity.roles:
            logger.warning(f"RBAC Deny: User {identity.user_id} attempted action requiring {required_role}")
            raise HTTPException(
                status_code=403, 
                detail=f"RBAC Authorization failed. Required role: {required_role}. Your roles: {identity.roles}"
            )
        return True

rbac_service = RbacService()
