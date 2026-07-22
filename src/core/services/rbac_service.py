import logging
from typing import List, Optional, Dict
from pydantic import BaseModel
from fastapi import HTTPException
from src.core.ontology import UserIdentity

logger = logging.getLogger(__name__)

class RbacService:
    """
    Role-Based Access Control (RBAC) Service.
    Authenticates and authorizes humans interacting with the platform.
    """
    
    def __init__(self):
        pass

    def authenticate_human(self, user_id: str, tenant_id: str, provided_roles: Optional[List[str]] = None) -> UserIdentity:
        """
        Identifies the human user and constructs their RBAC identity.
        Strictly requires provided_roles from the upstream caller (e.g., Dify JWT).
        """
        if not provided_roles:
            logger.error(f"Authentication failed: No roles provided for user {user_id}")
            raise HTTPException(
                status_code=401, 
                detail="Authentication failed. No roles provided in request context."
            )
            
        logger.debug(f"Authenticated human: {user_id} with roles {provided_roles}")
        return UserIdentity(user_id=user_id, tenant_id=tenant_id, roles=provided_roles)

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
