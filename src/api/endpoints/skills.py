from typing import Optional
from fastapi import APIRouter, HTTPException
from src.core.services import skill_service

router = APIRouter()

@router.get("/")
async def list_skills(category: Optional[str] = None):
    """List all available Markdown skills."""
    skills = skill_service.list_skills(category=category)
    return {"skills": skills}

@router.get("/{skill_name}")
async def get_skill(skill_name: str):
    """Get a specific skill's Markdown content and metadata."""
    skill = skill_service.get_skill(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    return {"skill": skill}
