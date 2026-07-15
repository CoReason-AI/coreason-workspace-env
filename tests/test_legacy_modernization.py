import pytest
from pydantic import ValidationError

from src.core.skill_registry_schema import ARTIFACT_TYPES, SkillRegistry, SkillRegistryEntry
from src.core.skill_loader import resolve_skills
from src.core.schemas.legacy_ir import LegacyIR

class TestLegacyModernization:
    def test_legacy_ir_in_artifact_types(self):
        assert "legacy_ir" in ARTIFACT_TYPES

    def test_legacy_ir_schema_valid(self):
        # Test valid payload
        valid_payload = {
            "source_repository": "/path/to/repo",
            "scan_timestamp": "2024-01-01T00:00:00Z",
            "agents": [{
                "name": "test_agent",
                "raw_prompt": "You are a test agent.",
                "type_guess": "supervisor",
                "tools_used": ["test_tool"],
                "source_file": "agent.py",
                "dependencies_guess": []
            }],
            "tool_side_effects": [{
                "function_name": "make_request",
                "egress_type": "http",
                "target": "example.com",
                "source_file": "utils.py",
                "line_number": 10,
                "risk_level": "medium"
            }],
            "state_graph": [{
                "source_agent": "a",
                "target_agent": "b",
                "handoff_type": "json",
                "description": "handoff"
            }],
            "security_flags": [{
                "flag_type": "hardcoded_credential",
                "severity": "critical",
                "location": "config.py:10",
                "description": "API key found",
                "remediation_hint": "Use env var"
            }],
            "raw_file_count": 10,
            "total_lines_scanned": 1000
        }
        ir = LegacyIR(**valid_payload)
        assert len(ir.agents) == 1
        assert ir.agents[0].name == "test_agent"

    def test_legacy_ir_schema_invalid(self):
        # Missing required fields
        with pytest.raises(ValidationError):
            LegacyIR(source_repository="test")

    def test_skill_loader_resolves_legacy_standards(self):
        registry = SkillRegistry(entries=[
            SkillRegistryEntry(
                name="legacy_modernization_standards",
                artifact_types=["legacy_ir"],
                abstract="Test abstract",
                path="core/skills/building/legacy_modernization_standards"
            ),
            SkillRegistryEntry(
                name="agent_building_standards",
                artifact_types=["agent_yaml"],
                abstract="Test abstract",
                path="core/skills/building/agent_building_standards"
            )
        ])
        
        # Resolve legacy_ir
        resolved = registry.resolve("legacy_ir")
        assert len(resolved) == 1
        assert resolved[0].name == "legacy_modernization_standards"
        
        # Resolve agent_yaml
        resolved_agent = registry.resolve("agent_yaml")
        assert len(resolved_agent) == 1
        assert resolved_agent[0].name == "agent_building_standards"
