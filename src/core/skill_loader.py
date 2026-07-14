"""
Skill Loader — JIT resolution engine for the skill_registry.

Reads skill_registry entries from an agent's YAML manifest and resolves
the full markdown content of matching skills based on artifact_type.

Usage:
    from src.core.skill_loader import resolve_skills

    # At LangGraph node build time:
    content = resolve_skills(skill_registry_entries, artifact_type="agent_yaml")
    # Returns the full markdown of only the relevant standards
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Root of the source tree (src/)
_SRC_ROOT = Path(__file__).resolve().parent.parent


def resolve_skills(
    skill_registry: List[Dict[str, Any]],
    artifact_type: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Resolve skill_registry entries to their full markdown content.

    Args:
        skill_registry: List of registry entry dicts from agent.yaml
            Each entry has: name, artifact_types, abstract, path
        artifact_type: If provided, only load skills matching this type.
            If None, load ALL skills (backward-compatible fallback).

    Returns:
        List of dicts with 'name', 'path', and 'content' keys.
    """
    results = []

    for entry in skill_registry:
        # Filter by artifact_type if specified
        if artifact_type is not None:
            entry_types = entry.get("artifact_types", [])
            if artifact_type not in entry_types:
                continue

        # Resolve the path to the actual markdown file
        skill_path = entry.get("path", "")
        content = _load_skill_content(skill_path)

        if content is not None:
            results.append({
                "name": entry.get("name", "unknown"),
                "path": skill_path,
                "content": content,
            })
        else:
            logger.warning(f"Skill not found: {skill_path}")

    if not results and artifact_type is not None:
        logger.info(
            f"No skills matched artifact_type='{artifact_type}', "
            f"falling back to loading all {len(skill_registry)} skills"
        )
        return resolve_skills(skill_registry, artifact_type=None)

    return results


def _load_skill_content(skill_path: str) -> Optional[str]:
    """
    Load the markdown content of a skill from its registry path.

    The path in the registry is relative like 'core/skills/building/agent_building_standards'.
    We resolve it against the src/ root and try both with and without .md extension.
    """
    # The path format in YAML is like 'core/skills/building/agent_building_standards'
    # Resolve relative to src/
    resolved = _SRC_ROOT / skill_path
    candidates = [
        resolved.with_suffix(".md"),
        resolved,
    ]

    for candidate in candidates:
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to read skill file {candidate}: {e}")
                return None

    return None


def build_context_prompt(
    skill_registry: List[Dict[str, Any]],
    artifact_type: Optional[str] = None,
) -> str:
    """
    Build a context prompt string from resolved skills.
    This is injected into the agent's execution context at LangGraph runtime.

    Args:
        skill_registry: The agent's skill_registry entries.
        artifact_type: The artifact type being worked on.

    Returns:
        A formatted string containing the full content of resolved skills,
        wrapped in clear delimiters.
    """
    resolved = resolve_skills(skill_registry, artifact_type)

    if not resolved:
        return ""

    parts = []
    for skill in resolved:
        parts.append(f"--- BEGIN SKILL: {skill['name']} ---")
        parts.append(skill["content"])
        parts.append(f"--- END SKILL: {skill['name']} ---")
        parts.append("")

    return "\n".join(parts)


def get_registry_abstracts(skill_registry: List[Dict[str, Any]]) -> str:
    """
    Render the skill registry as a compact abstracts listing.
    This is injected into the agent's system prompt instead of full skill content.

    Args:
        skill_registry: The agent's skill_registry entries.

    Returns:
        A compact string listing each skill's name, types, and abstract.
    """
    lines = ["Available Standards (loaded on demand by artifact type):"]
    for entry in skill_registry:
        types_str = ", ".join(entry.get("artifact_types", []))
        name = entry.get("name", "unknown")
        abstract = entry.get("abstract", "")
        lines.append(f"  - [{types_str}] {name}: {abstract}")
    return "\n".join(lines)
