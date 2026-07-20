import os
import yaml
import logging
from typing import Any
from src.core.base_agent import DeepAgent
from langchain_core.messages import HumanMessage
from deepagents.graph import DeepAgentState

logger = logging.getLogger(__name__)

# --- RAW JSON SCHEMA FOR CONSTRAINED DECODING ---
SCHEMA_DICT = {
    "name": "CognitiveDeliberativeEnvelopeState",
    "description": "Envelope for deterministic YAML generation",
    "parameters": {
        "type": "object",
        "properties": {
            "deliberation_trace": {
                "type": "string",
                "description": "Think out loud. Weigh architectural patterns and map context."
            },
            "project_yaml": {
                "type": "string",
                "description": "The raw string contents of project.yaml"
            },
            "orchestrator_agent": {
                "type": "object",
                "properties": {
                    "agentspec_version": { "type": "string", "enum": ["26.1.2"] },
                    "component_type": { "type": "string", "enum": ["Agent"] },
                    "id": { "type": "string" },
                    "name": { "type": "string" },
                    "description": { "type": "string" },
                    "metadata": { "type": "object" },
                    "llm_config": {
                        "type": "object",
                        "properties": { "$component_ref": { "type": "string", "enum": ["default_gpt4"] } },
                        "required": ["$component_ref"]
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "The core instructions, execution framework, and constraints. You MUST copy these sections verbatim from the context. DO NOT SUMMARIZE."
                    },
                    "inputs": {
                        "type": "object",
                        "description": "Extract the 'Required Inputs'. MUST be strict fully expanded JSON Schema objects."
                    },
                    "outputs": {
                        "type": "object",
                        "description": "Extract the 'Output Schema'. MUST be strict fully expanded JSON Schema objects."
                    },
                    "tools": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": { "$component_ref": { "type": "string" } },
                            "required": ["$component_ref"]
                        }
                    },
                    "toolboxes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": { "$component_ref": { "type": "string" } },
                            "required": ["$component_ref"]
                        }
                    },
                    "$referenced_components": {
                        "type": "object",
                        "properties": {
                            "default_gpt4": {
                                "type": "object",
                                "properties": {
                                    "component_type": { "type": "string", "enum": ["LlmConfig"] },
                                    "id": { "type": "string", "enum": ["default_gpt4"] },
                                    "name": { "type": "string" },
                                    "description": { "type": "string" },
                                    "metadata": { "type": "object" },
                                    "model_id": { "type": "string", "enum": ["gpt-4o"] },
                                    "provider": { "type": "string", "enum": ["openai"] },
                                    "api_type": { "type": "string", "enum": ["chat_completions"] },
                                    "api_key": { "type": "null" }
                                },
                                "required": ["component_type", "id", "name", "description", "metadata", "model_id", "provider", "api_type"]
                            }
                        },
                        "required": ["default_gpt4"]
                    }
                },
                "required": [
                    "agentspec_version", "component_type", "id", "name", "description",
                    "metadata", "llm_config", "system_prompt", "inputs", "outputs", 
                    "$referenced_components"
                ]
            }
        },
        "required": ["deliberation_trace", "project_yaml", "orchestrator_agent"]
    }
}

class YamlCompilerAgent(DeepAgent):
    """
    Deterministic worker for YAML compilation via DeepAgent using Constrained Decoding.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
        
        self.system_prompt = self.agent_spec.get("system_prompt", "You are an expert YAML compiler.")

    def execute(self, context: Any, session_id: str = None, config: dict = None) -> str:
        """
        Executes deterministic generation via DeepAgent loop.
        """
        logger.info(f"[{session_id}] YamlCompiler executing via DeepAgent with Strict JSON Dictionary Output.")
        
        graph = self.build_standard_deep_agent(
            system_prompt=self.system_prompt,
            state_schema=DeepAgentState
        )
        
        initial_state = {"messages": [HumanMessage(content=f"Requirements: {context}")]}
        result = graph.invoke(initial_state, config=config or {})
        
        final_message = "FAILURE: No output produced."
        
        if result.get("messages"):
            last_msg = result["messages"][-1]
            final_message = getattr(last_msg, "content", str(last_msg))
                
        return final_message
