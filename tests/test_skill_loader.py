"""
Tests for the JIT Skill Loader (src.core.skill_loader).
Verifies artifact-type routing, fallback behavior, and context prompt building.
"""
import unittest
from pathlib import Path


class TestSkillLoader(unittest.TestCase):
    """Test the JIT skill resolution engine."""

    def setUp(self):
        """Set up a realistic skill_registry matching yaml_compiler."""
        self.registry = [
            {
                "name": "agent_building_standards",
                "artifact_types": ["agent_yaml"],
                "abstract": "How to construct DeepAgent YAML manifests",
                "path": "core/skills/building/agent_building_standards",
            },
            {
                "name": "mcp_building_standards",
                "artifact_types": ["mcp_spec"],
                "abstract": "How to construct MCP server specifications",
                "path": "core/skills/building/mcp_building_standards",
            },
            {
                "name": "skill_building_standards",
                "artifact_types": ["skill"],
                "abstract": "How to construct agentic skills/SOPs",
                "path": "core/skills/building/skill_building_standards",
            },
        ]

    def test_resolve_agent_yaml_loads_only_agent_standard(self):
        """Resolving for 'agent_yaml' should load only agent_building_standards."""
        from src.core.skill_loader import resolve_skills
        results = resolve_skills(self.registry, artifact_type="agent_yaml")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "agent_building_standards")

    def test_resolve_mcp_spec_loads_only_mcp_standard(self):
        """Resolving for 'mcp_spec' should load only mcp_building_standards."""
        from src.core.skill_loader import resolve_skills
        results = resolve_skills(self.registry, artifact_type="mcp_spec")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "mcp_building_standards")

    def test_resolve_skill_loads_only_skill_standard(self):
        """Resolving for 'skill' should load only skill_building_standards."""
        from src.core.skill_loader import resolve_skills
        results = resolve_skills(self.registry, artifact_type="skill")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "skill_building_standards")

    def test_resolve_none_loads_all_skills(self):
        """Resolving with no artifact_type should load ALL skills."""
        from src.core.skill_loader import resolve_skills
        results = resolve_skills(self.registry, artifact_type=None)
        self.assertEqual(len(results), 3)

    def test_resolve_unknown_type_falls_back_to_all(self):
        """Resolving with an unknown type should fall back to loading all skills."""
        from src.core.skill_loader import resolve_skills
        results = resolve_skills(self.registry, artifact_type="unknown_type_xyz")
        # Should fall back to all
        self.assertEqual(len(results), 3)

    def test_resolved_skill_has_content(self):
        """Resolved skills should include non-empty markdown content."""
        from src.core.skill_loader import resolve_skills
        results = resolve_skills(self.registry, artifact_type="agent_yaml")
        self.assertEqual(len(results), 1)
        self.assertTrue(len(results[0]["content"]) > 100, "Content should be substantial markdown")

    def test_build_context_prompt(self):
        """build_context_prompt should wrap skill content in delimiters."""
        from src.core.skill_loader import build_context_prompt
        prompt = build_context_prompt(self.registry, artifact_type="agent_yaml")
        self.assertIn("BEGIN SKILL: agent_building_standards", prompt)
        self.assertIn("END SKILL: agent_building_standards", prompt)

    def test_build_context_prompt_empty_for_no_skills(self):
        """build_context_prompt should return empty string when no skills exist."""
        from src.core.skill_loader import build_context_prompt
        prompt = build_context_prompt([], artifact_type="agent_yaml")
        self.assertEqual(prompt, "")

    def test_get_registry_abstracts(self):
        """get_registry_abstracts should return compact listing."""
        from src.core.skill_loader import get_registry_abstracts
        abstracts = get_registry_abstracts(self.registry)
        self.assertIn("agent_building_standards", abstracts)
        self.assertIn("mcp_building_standards", abstracts)
        self.assertIn("[agent_yaml]", abstracts)
        self.assertIn("[mcp_spec]", abstracts)


class TestSkillRegistrySchema(unittest.TestCase):
    """Test the Pydantic schema for skill_registry validation."""

    def test_valid_entry(self):
        from src.core.skill_registry_schema import SkillRegistryEntry
        entry = SkillRegistryEntry(
            name="test_skill",
            artifact_types=["agent_yaml"],
            abstract="Test skill",
            path="core/skills/building/test",
        )
        self.assertEqual(entry.name, "test_skill")

    def test_registry_resolve(self):
        from src.core.skill_registry_schema import SkillRegistry, SkillRegistryEntry
        registry = SkillRegistry(entries=[
            SkillRegistryEntry(
                name="a", artifact_types=["agent_yaml"], abstract="A", path="path/a"
            ),
            SkillRegistryEntry(
                name="b", artifact_types=["mcp_spec"], abstract="B", path="path/b"
            ),
        ])
        matches = registry.resolve("agent_yaml")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].name, "a")

    def test_registry_to_abstracts_prompt(self):
        from src.core.skill_registry_schema import SkillRegistry, SkillRegistryEntry
        registry = SkillRegistry(entries=[
            SkillRegistryEntry(
                name="test", artifact_types=["skill"], abstract="A test", path="path/test"
            ),
        ])
        prompt = registry.to_abstracts_prompt()
        self.assertIn("[skill] test: A test", prompt)


class TestSkillRegistryInAgentYAML(unittest.TestCase):
    """Verify that all migrated agent YAMLs have valid skill_registry entries."""

    def _load_yaml(self, agent_name):
        import yaml
        path = Path(__file__).resolve().parent.parent / "src" / "agents" / agent_name / "agent.yaml"
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_yaml_compiler_has_skill_registry(self):
        data = self._load_yaml("yaml_compiler")
        self.assertIn("skill_registry", data)
        self.assertNotIn("skills", data)
        types = [t for e in data["skill_registry"] for t in e["artifact_types"]]
        self.assertIn("agent_yaml", types)
        self.assertIn("mcp_spec", types)
        self.assertIn("skill", types)

    def test_agent_validator_has_skill_registry(self):
        data = self._load_yaml("agent_validator")
        self.assertIn("skill_registry", data)
        self.assertNotIn("skills", data)
        types = [t for e in data["skill_registry"] for t in e["artifact_types"]]
        self.assertIn("agent_yaml", types)
        self.assertIn("mcp_spec", types)
        self.assertIn("skill", types)
        self.assertIn("workflow", types)
        self.assertIn("diagram", types)

    def test_factory_ceo_has_skill_registry(self):
        data = self._load_yaml("factory_ceo")
        self.assertIn("skill_registry", data)
        self.assertNotIn("skills", data)

    def test_agent_pm_has_skill_registry(self):
        data = self._load_yaml("agent_pm")
        self.assertIn("skill_registry", data)
        self.assertNotIn("skills", data)

    def test_all_registry_entries_have_required_fields(self):
        """Every skill_registry entry in every agent must have name, artifact_types, abstract, path."""
        agents_with_registry = [
            "yaml_compiler", "prompt_engineer", "agent_validator",
            "agent_pm", "factory_ceo", "backend_pm", "frontend_pm", "fastapi_coder",
        ]
        for agent_name in agents_with_registry:
            data = self._load_yaml(agent_name)
            self.assertIn("skill_registry", data, f"{agent_name} missing skill_registry")
            for entry in data["skill_registry"]:
                self.assertIn("name", entry, f"{agent_name}: entry missing 'name'")
                self.assertIn("artifact_types", entry, f"{agent_name}: entry missing 'artifact_types'")
                self.assertIn("abstract", entry, f"{agent_name}: entry missing 'abstract'")
                self.assertIn("path", entry, f"{agent_name}: entry missing 'path'")
                self.assertIsInstance(entry["artifact_types"], list, f"{agent_name}: artifact_types must be list")


if __name__ == "__main__":
    unittest.main()
