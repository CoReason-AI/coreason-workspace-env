import os
import yaml
import logging
from typing import Any, Dict, List
from src.core.base_agent import DeepAgent
from src.core.ontology import AgentManifest, ManifestViolationReceipt

logger = logging.getLogger(__name__)


class AgentValidatorAgent(DeepAgent):
    """
    Validation sub-agent for checking artifacts produced by factory Makers.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
        self.system_prompt = self.agent_spec.get("system_prompt", "You are the Agent Validator.")

    def validate_manifest(self, manifest_data: Dict[str, Any]) -> List[ManifestViolationReceipt]:
        """
        Validates an agent manifest dictionary against schema & business rules.
        """
        violations = []
        
        # Check required fields
        if not manifest_data.get("name"):
            violations.append(ManifestViolationReceipt(
                failing_pointer="/name",
                violation_category="missing_field",
                diagnostic_message="Agent manifest must include a non-empty 'name' field."
            ))

        if not manifest_data.get("system_prompt"):
            violations.append(ManifestViolationReceipt(
                failing_pointer="/system_prompt",
                violation_category="missing_field",
                diagnostic_message="Agent manifest must include a 'system_prompt' string."
            ))

        # Check skills existence via skill_service if provided
        skills = manifest_data.get("skills", [])
        if skills:
            from src.core.services import skill_service
            val_res = skill_service.validate_skill_references(skills)
            if not val_res["is_valid"]:
                for missing in val_res["missing"]:
                    violations.append(ManifestViolationReceipt(
                        failing_pointer="/skills",
                        violation_category="missing_skill",
                        diagnostic_message=f"Referenced skill '{missing}' does not exist in skill_service registry."
                    ))

        return violations

    def execute(self, context: Any, session_id: str = None, config: dict = None) -> str:
        """
        Parses YAML or dict context, runs validation checks, and returns PASS or FAIL string with violations.
        """
        logger.info(f"[{session_id}] AgentValidator executing artifact validation...")
        
        manifest_dict = {}
        if isinstance(context, dict):
            manifest_dict = context
        elif isinstance(context, str):
            try:
                manifest_dict = yaml.safe_load(context) or {}
            except Exception as e:
                return f"FAIL\nParsing error: {e}"

        violations = self.validate_manifest(manifest_dict)
        if not violations:
            return "PASS"

        violation_msgs = [f"- [{v.violation_category}] {v.failing_pointer}: {v.diagnostic_message}" for v in violations]
        return "FAIL\n" + "\n".join(violation_msgs)
