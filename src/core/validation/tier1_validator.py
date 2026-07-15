# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>
import json
import logging
import yaml
from typing import Dict, Any, Callable

# Import the AST auditor directly as a pure Python validator
from src.core.skills.jinja2_ast_auditor import jinja2_ast_auditor

logger = logging.getLogger(__name__)

class CoreValidator:
    """
    Tier 1 Deterministic Fast-Fail Validation Registry.
    Bypasses the LLM entirely if the artifact fails structural checks.
    """
    def __init__(self):
        self._registry: Dict[str, Callable[[str], dict]] = {}
        
        # Register default validation handlers
        self.register_handler("agent_yaml", self._validate_yaml)
        self.register_handler("mcp_spec", self._validate_yaml)
        self.register_handler("workflow", self._validate_yaml)
        self.register_handler("skill", self._validate_yaml)
        self.register_handler("python", self._validate_python)
        
    def register_handler(self, artifact_type: str, handler: Callable[[str], dict]):
        self._registry[artifact_type] = handler

    def _validate_yaml(self, payload: str) -> dict:
        try:
            parsed = yaml.safe_load(payload)
            if not isinstance(parsed, dict) and not isinstance(parsed, list):
                return {
                    "status": "FAIL",
                    "reason": "GuardrailViolationEvent: Payload is not valid structured YAML (must be a dictionary or list)."
                }
        except yaml.YAMLError as e:
            return {
                "status": "FAIL",
                # The e exception usually contains the line number: e.g. "mapping values are not allowed here \n  in \"<unicode string>\", line 10, column 12"
                "reason": f"GuardrailViolationEvent: YAML Parsing Error: {e}"
            }
        return {"status": "PASS"}

    def _validate_python(self, payload: str) -> dict:
        try:
            # If it's still wrapped as a LangChain tool, invoke it
            if hasattr(jinja2_ast_auditor, "invoke"):
                result_str = jinja2_ast_auditor.invoke({"python_code": payload})
            else:
                # If it's a raw function now
                result_str = jinja2_ast_auditor(payload)
                
            result = json.loads(result_str)
            if result.get("status") == "FAIL":
                return result
        except Exception as e:
            logger.warning(f"AST Auditor failed to run (non-fatal): {e}")
            
        return {"status": "PASS"}

    def run_tier1_validation(self, payload: str, artifact_type: str = "unknown") -> dict:
        """
        Executes the registered Tier 1 validation logic based on artifact_type.
        If no handler is registered, attempts to guess based on payload content,
        then returns PASS if no specific rules are violated.
        """
        logger.info(f"Running Tier 1 Deterministic Validation for artifact type: {artifact_type}")

        handler = self._registry.get(artifact_type)
        if handler:
            return handler(payload)
            
        # Fallback heuristics for unknown types
        if "def " in payload or "class " in payload:
            return self._validate_python(payload)
            
        return {
            "status": "PASS",
            "reason": "No Tier 1 deterministic violations found."
        }

# Global singleton instance for easy import
tier1_engine = CoreValidator()
