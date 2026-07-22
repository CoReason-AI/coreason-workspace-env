import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.core.ontology import SkillManifest, ActionSpaceCategoryProfile

logger = logging.getLogger(__name__)

_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


class SkillService:
    """
    Service layer for dynamic discovery, parsing, validation, and injection of skills.
    Serves as the single source of truth across all 5 interaction surfaces.
    """

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or _SKILLS_DIR

    def list_skills(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discovers all Markdown skills under src/core/skills/ recursively.
        """
        skills = []
        if not self.skills_dir.is_dir():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return skills

        for md_file in sorted(self.skills_dir.rglob("*.md")):
            rel_path = md_file.relative_to(self.skills_dir)
            category_name = rel_path.parts[0] if len(rel_path.parts) > 1 else "general"
            
            if category and category.lower() != category_name.lower():
                continue

            skill_name = md_file.stem
            skills.append({
                "name": skill_name,
                "category": category_name,
                "path": str(rel_path).replace("\\", "/"),
                "full_path": str(md_file),
            })

        return skills

    def get_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        Reads a specific skill's Markdown content and metadata.
        """
        all_skills = self.list_skills()
        for s in all_skills:
            if s["name"] == skill_name or s["path"] == skill_name or s["path"].replace(".md", "") == skill_name:
                p = Path(s["full_path"])
                if p.is_file():
                    content = p.read_text(encoding="utf-8")
                    return {
                        "name": s["name"],
                        "category": s["category"],
                        "path": s["path"],
                        "content": content,
                    }
        return None

    def validate_skill_references(self, skill_names: List[str]) -> Dict[str, Any]:
        """
        Validates whether a list of requested skill names exist in the registry.
        """
        available = {s["name"]: s for s in self.list_skills()}
        valid = []
        missing = []

        for name in skill_names:
            clean_name = name.split("/")[-1].replace(".md", "")
            if clean_name in available:
                valid.append(available[clean_name])
            else:
                missing.append(name)

        return {
            "valid": valid,
            "missing": missing,
            "is_valid": len(missing) == 0,
        }


skill_service = SkillService()
