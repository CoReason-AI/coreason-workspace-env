"""
Skill Registry Schema — Pydantic models for the skill_registry YAML field.

Defines the schema that replaces the static `skills:` array in agent.yaml files.
Each entry in the registry is a lightweight abstract that can be JIT-resolved
at runtime based on the incoming task's artifact_type.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# Canonical artifact types recognized by the factory
ARTIFACT_TYPES = [
    "agent_yaml",   # DeepAgent YAML manifest
    "mcp_spec",     # MCP server specification
    "skill",        # Agentic skill / SOP definition
    "workflow",     # Workflow topology / LangGraph DAG
    "diagram",      # Architecture diagram / visual communication
    "legacy_ir",    # Legacy codebase intermediate representation
    "knowledge_receipt", # Epistemic Firewall strict provenance return
]


class SkillRegistryEntry(BaseModel):
    """A single entry in an agent's skill registry."""

    name: str = Field(
        ...,
        description="Short identifier for the skill (e.g. 'agent_building_standards')",
    )
    artifact_types: List[str] = Field(
        ...,
        description=(
            "Which artifact types this skill applies to. "
            f"Valid values: {ARTIFACT_TYPES}"
        ),
    )
    abstract: str = Field(
        ...,
        description="One-line summary of what this skill teaches (shown in the agent's system prompt as a registry listing)",
    )
    path: str = Field(
        ...,
        description="Relative path to the skill markdown file (e.g. 'core/skills/building/agent_building_standards')",
    )


class SkillRegistry(BaseModel):
    """The full skill_registry for an agent.yaml."""

    entries: List[SkillRegistryEntry] = Field(default_factory=list)

    def resolve(self, artifact_type: str) -> List[SkillRegistryEntry]:
        """Return only the entries that match the given artifact_type."""
        return [e for e in self.entries if artifact_type in e.artifact_types]

    def resolve_all(self) -> List[SkillRegistryEntry]:
        """Return all entries (fallback when no artifact_type specified)."""
        return list(self.entries)

    def to_abstracts_prompt(self) -> str:
        """
        Render the registry as a compact prompt fragment for the agent's system prompt.
        This replaces loading full skill content — agents see only abstracts until JIT resolution.
        """
        lines = ["Available Skills (loaded on demand by artifact type):"]
        for entry in self.entries:
            types_str = ", ".join(entry.artifact_types)
            lines.append(f"  - [{types_str}] {entry.name}: {entry.abstract}")
        return "\n".join(lines)
