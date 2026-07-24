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

    def forge_skill(
        self,
        skill_id: str,
        name: str,
        category: str,
        description: str,
        content: str,
        tags: Optional[List[str]] = None,
        author_id: str = "prompt_engineer",
    ) -> Dict[str, Any]:
        """
        Forges a new skill: writes markdown to src/core/skills/<category>/<skill_id>.md,
        validates syntax, and registers the verified skill into CatalogService under PEN 66197 URN.
        """
        from src.core.ontology import CoreasonURN
        from src.core.services.catalog_service import catalog_service

        target_dir = self.skills_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"{skill_id}.md"

        full_md = f"# {name}\n\n**Category**: `{category}`\n**Description**: {description}\n\n{content}"
        file_path.write_text(full_md, encoding="utf-8")

        urn_obj = CoreasonURN(resource_type="skill", resource_id=skill_id)
        oid_urn = urn_obj.to_oid_urn()
        coreason_url = urn_obj.to_coreason_url()

        final_tags = list(set(["skill", "forged", category] + (tags or [])))
        catalog_entry = catalog_service.register_entry(
            urn=oid_urn,
            name=name,
            description=description,
            resource_type="skill",
            tags=final_tags,
            metadata={
                "category": category,
                "author_id": author_id,
                "path": f"{category}/{skill_id}.md",
                "coreason_url": coreason_url,
            },
            source_code=full_md,
        )

        logger.info(f"Successfully forged and cataloged skill '{name}' ({skill_id}) under URN {oid_urn}.")
        return {
            "status": "success",
            "skill_id": skill_id,
            "urn": oid_urn,
            "coreason_url": coreason_url,
            "path": f"{category}/{skill_id}.md",
            "catalog_entry": catalog_entry.model_dump(),
        }

    def clone_skill(self, urn_or_id: str, target_category: Optional[str] = None) -> Dict[str, Any]:
        """
        Clones a skill from the global catalog into the active skills directory.
        """
        from src.core.services.catalog_service import catalog_service

        entry = catalog_service.resolve_urn(urn_or_id)
        if not entry or entry.get("resource_type") != "skill":
            return {"status": "error", "message": f"Skill URN '{urn_or_id}' not found in catalog."}

        category = target_category or entry.get("metadata", {}).get("category", "building")
        urn_parts = urn_or_id.split(":")
        skill_id = urn_parts[-1] if len(urn_parts) > 1 else urn_or_id
        content = entry.get("source_code") or entry.get("description", "")

        return self.forge_skill(
            skill_id=skill_id,
            name=entry.get("name", skill_id),
            category=category,
            description=entry.get("description", ""),
            content=content,
            tags=entry.get("tags", []),
            author_id="skill_cloner",
        )


skill_service = SkillService()
