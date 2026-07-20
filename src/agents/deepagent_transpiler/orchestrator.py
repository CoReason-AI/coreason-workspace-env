import os
import yaml
import logging
from typing import Any
from src.core.base_agent import DeepAgent
from deepagents.graph import DeepAgentState, create_deep_agent
from langchain_core.messages import HumanMessage
from src.core.config import settings

logger = logging.getLogger(__name__)

DEEPAGENT_SCHEMA = {
    "name": "DeepAgentManifest",
    "description": "Deterministic transpiled DeepAgent YAML",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "model": {"type": "string", "description": "e.g., openai:gpt-4o"},
            "sp_prefix": {"type": "string", "description": "The main role definition and core capabilities from the system prompt"},
            "sp_suffix": {"type": "string", "description": "The behavioral constraints and output formatting rules from the system prompt"},
            "tools": {
                "type": "array",
                "items": {"type": "string"}
            },
            "response_format": {
                "type": "object",
                "description": "The extracted JSON Schema if 'outputs' was defined in the Oracle Spec. Omit if none."
            }
        },
        "required": ["name", "description", "model", "sp_prefix", "sp_suffix", "tools"],
        "additionalProperties": False
    },
    "strict": True
}

class DeepagentTranspilerAgent(DeepAgent):
    """
    Worker Agent that transpiles Oracle YAML to DeepAgent YAML.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)

    def execute(self, context: dict, session_id: str = None, config: dict = None) -> Any:
        prompt = self.agent_spec.get("system_prompt", "You are a YAML transpiler.")
        prompt += "\n\nCRITICAL: You MUST strictly adhere to the provided JSON schema."
        
        oracle_yaml = context.get("oracle_yaml", "")
        if not oracle_yaml:
            return "Error: No Oracle YAML provided in context['oracle_yaml'] for transpilation."
            
        human_msg = f"Transpile this Oracle YAML to DeepAgent YAML:\n\n```yaml\n{oracle_yaml}\n```"

        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=settings.LLM_MODEL_NAME,
            api_key=settings.LLM_API_KEY,
            temperature=0.1,  # Low temperature for highly deterministic parsing
            base_url=settings.LLM_BASE_URL
        )
        
        response_format = {"type": "json_schema", "json_schema": DEEPAGENT_SCHEMA}
        
        graph = create_deep_agent(
            model=llm,
            system_prompt=prompt,
            state_schema=DeepAgentState,
            response_format=response_format
        )
        
        config = {"configurable": {"thread_id": session_id or "transpiler"}}
        
        try:
            try:
                from langfuse.langchain import CallbackHandler
            except ImportError:
                from langfuse.callback import CallbackHandler
            langfuse_handler = CallbackHandler()
            config["callbacks"] = [langfuse_handler]
        except Exception as e:
            pass

        result = graph.invoke({"messages": [HumanMessage(content=human_msg)]}, config=config)
        content = result["messages"][-1].content
        
        try:
            import json
            parsed_json = json.loads(content)
            # Remove response_format if it is empty to keep YAML clean
            if "response_format" in parsed_json and not parsed_json["response_format"]:
                del parsed_json["response_format"]
                
            yaml_output = yaml.dump(parsed_json, sort_keys=False)
            return yaml_output
        except Exception:
            return content
