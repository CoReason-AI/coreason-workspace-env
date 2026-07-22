"""
Full System E2E Tests — Comprehensive End-to-End Integration Suite.
Tests multi-agent orchestration, dynamic tool forging, URN cataloging, reasoning engines, and API surfaces.
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage

from src.core.services.catalog_service import catalog_service
from src.core.services.tool_forging_service import tool_forging_service
from src.core.services.skill_service import skill_service
from src.core.services.audit_service import audit_service
from src.core.services.testing_service import testing_service
from src.core.services.improvement_service import improvement_service
from src.core.services.reasoning_service import reasoning_service
from src.core.services.causal_proving_service import causal_proving_service
from src.core.services.thought_structuring_service import thought_structuring_service

from src.core.tools.reasoning_tools import analogical_mapping_tool, neurosymbolic_deduction_tool
from src.core.tools.causal_thought_tools import prove_causal_hypothesis_tool, organize_thoughts_tool, structure_complex_thoughts_tool


class TestFullSystemE2E:
    """
    Full System End-to-End Test Suite.
    """

    def test_e2e_tool_and_skill_forging_lifecycle(self, tmp_path):
        """E2E Test: Tool Forging -> URN Cataloging -> Skill Creation -> URN Resolution."""
        tool_code = """
def e2e_custom_calculator(a: int, b: int) -> int:
    '''Calculates the product of two numbers.'''
    return a * b
"""
        test_code = """
def test_calc():
    assert e2e_custom_calculator(3, 4) == 12
"""
        # 1. Forge tool
        forge_receipt = tool_forging_service.forge_tool(
            tool_id="e2e_custom_calculator",
            name="e2e_custom_calculator",
            description="E2E Calculator Tool",
            code=tool_code,
            unit_test_code=test_code
        )
        assert "urn:oid:1.3.6.1.4.1.66197" in forge_receipt["tool"]["urn"]
        assert forge_receipt["tool"]["validation_status"] == "passed"

        # 2. Query Catalog
        entries = catalog_service.search_catalog(query="e2e_custom_calculator")
        assert len(entries) >= 1
        found_urn = entries[0]["urn"]

        # 3. Resolve URN
        resolved = catalog_service.resolve_urn(found_urn)
        assert resolved is not None
        assert resolved["name"] == "e2e_custom_calculator"

        # 4. Forge Skill
        skill_receipt = skill_service.forge_skill(
            skill_id="e2e_calculation_skill",
            name="e2e_calculation_skill",
            category="building",
            description="Skill for multiplying metrics deterministically.",
            content="# E2E Skill\nUse e2e_custom_calculator tool for math."
        )
        assert "urn:oid:1.3.6.1.4.1.66197" in skill_receipt["urn"]

    def test_e2e_audit_testing_remediation_pipeline(self):
        """E2E Test: Artifact Audit -> Test Execution -> Autonomous Improvement Loop."""
        # 1. Audit artifact with probabilistic calculation anti-pattern
        probabilistic_artifact = "Based on LLM probability, 15 * 4 = 60. Calculate probabilities."
        audit_report = audit_service.audit_prompt_or_skill(
            content=probabilistic_artifact,
            target_name="test_prompt",
            target_type="prompt"
        )
        assert audit_report.target_name == "test_prompt"

        # 2. Run agent sandbox tests
        agent_code = "def run(x):\n    return x * 2"
        test_code = "def test_run():\n    assert run(3) == 6"
        test_report = testing_service.run_agent_test_suite(
            agent_name="yaml_compiler",
            test_code=test_code,
            agent_code=agent_code
        )
        assert test_report.status == "PASSED"

        # 3. Autonomously improve artifact
        improvement_receipt = improvement_service.improve_agent_artifact(
            target_name="test_prompt",
            content=probabilistic_artifact,
            audit_report=audit_report,
            test_receipt=test_report
        )
        assert improvement_receipt.status == "REMEDIATED"
        assert improvement_receipt.new_audit_score >= 80.0

    def test_e2e_full_cognitive_reasoning_pipeline(self):
        """E2E Test: Structure Mapping -> Z3 SMT Deduction -> DoWhy Causal Proving -> MECE Structuring."""
        # 1. Analogical Structure Mapping
        map_res = analogical_mapping_tool.invoke({
            "target_problem": "How to scale distributed cache invalidation?",
            "source_domain": "immune_system_memory",
            "target_domain": "distributed_cache"
        })
        assert map_res["source_domain"] == "immune_system_memory"
        assert "entity_mappings" in map_res

        # 2. Neuro-Symbolic Z3 Deduction
        z3_script = """
a = Int('a')
b = Int('b')
s = Solver()
s.add(a > 5, b == a * 2, b == 16)
if s.check() == sat:
    print('sat')
    print(s.model())
"""
        z3_res = neurosymbolic_deduction_tool.invoke({
            "problem_statement": "Find a > 5 such that b = a * 2 = 16",
            "z3_code": z3_script
        })
        assert z3_res["solver_status"] == "SAT"
        assert z3_res["is_mathematically_proven"] is True

        # 3. DoWhy Causal Proof
        causal_res = prove_causal_hypothesis_tool.invoke({
            "hypothesis": "Increasing cache memory allocation reduces DB query latency",
            "treatment": "cache_size_gb",
            "outcome": "db_latency_ms",
            "confounders": ["traffic_qps"]
        })
        assert causal_res["is_theory_proven"] is True
        assert causal_res["bradford_hill_score"] >= 0.70

        # 4. MECE Thought Structuring
        thought_res = organize_thoughts_tool.invoke({
            "raw_unorganized_text": "- Design distributed cache topology\n- Run benchmark load tests in sandbox\n- Enforce access security policies"
        })
        assert len(thought_res["structured_groups"]) == 3
        assert thought_res["mece_coverage_score"] == 100.0

    @pytest.mark.asyncio
    @patch("langchain_openai.chat_models.base.ChatOpenAI.invoke")
    async def test_e2e_yaml_compiler_orchestration(self, mock_invoke):
        """E2E Test: YamlCompilerAgent generating deterministic AgentSpec definitions."""
        from src.agents.yaml_compiler.orchestrator import YamlCompilerAgent

        expected_response = {
            "deliberation_trace": "Analyzing requirement context...",
            "project_yaml": "project: e2e_agent_system",
            "orchestrator_agent": {
                "agentspec_version": "26.1.2",
                "component_type": "Agent",
                "id": "e2e_agent",
                "name": "e2e_agent",
                "description": "E2E Test Agent Definition",
                "metadata": {"tags": ["e2e"]},
                "llm_config": {"$component_ref": "default_llm"},
                "system_prompt": "You are an E2E agent.",
                "inputs": {"query": {"type": "string"}},
                "outputs": {"result": {"type": "string"}},
                "$referenced_components": {
                    "default_llm": {
                        "component_type": "LlmConfig",
                        "id": "default_llm",
                        "name": "default_llm",
                        "description": "default",
                        "metadata": {},
                        "model_id": "gpt-4o",
                        "provider": "openai",
                        "api_type": "chat_completions",
                        "api_key": None
                    }
                }
            }
        }
        mock_invoke.return_value = AIMessage(content=json.dumps(expected_response))

        compiler = YamlCompilerAgent()
        output = compiler.execute(context="Create a data pipeline agent", session_id="e2e-session-1")
        assert "e2e_agent" in output
