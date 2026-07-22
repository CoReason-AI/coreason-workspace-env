import os
import uuid
import yaml
import logging
from typing import Any
from src.core.base_agent import DeepAgent
from deepagents.graph import DeepAgentState

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)


class AgentPmAgent(DeepAgent):
    """
    Project Manager orchestrating the agent generation pipeline via a strict Builder-Validator-Approver loop.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
                
        base_prompt = self.agent_spec.get("system_prompt", "You are an autonomous PM.")
        pm_prompt = """
You are an autonomous PM.
Follow the Builder-Validator-Approver workflow:
1. PromptEngineer builds prompt.
2. YamlCompiler compiles agent manifest.
3. AgentValidator validates manifest against standards.
4. If valid, approve & save to disk.
"""
        self.system_prompt = f"{base_prompt}\n{pm_prompt}"

    def execute(self, context: Any, session_id: str = None, config: dict = None) -> str:
        """
        Executes pipeline using a deterministic StateGraph (Builder -> Validator -> Approver).
        """
        logger.info(f"*** [{session_id}] AgentPM initiating Builder-Validator-Approver pipeline! ***")
        
        from src.agents.prompt_engineer.orchestrator import PromptEngineerAgent
        from src.agents.yaml_compiler.orchestrator import YamlCompilerAgent
        from src.agents.agent_validator.orchestrator import AgentValidatorAgent
        from src.agents.deepagent_transpiler.orchestrator import DeepagentTranspilerAgent
        
        initial_state = {"messages": context} if isinstance(context, list) else {"messages": [("user", str(context))]}
        
        # 1. Prompt Engineer Node
        def run_prompt_engineer(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] Builder Step 1: PromptEngineerAgent")
            messages = state.get("messages", [])
            last_msg = messages[-1].content if messages else str(state)
            pe_output = PromptEngineerAgent().execute(last_msg, session_id=session_id, config=config)
            return {"messages": [AIMessage(content=pe_output)]}

        # 2. YAML Compiler Node
        def run_yaml_compiler(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] Builder Step 2: YamlCompilerAgent")
            messages = state.get("messages", [])
            ceo_context = messages[0].content if messages else ""
            pe_output = messages[-1].content if len(messages) > 1 else ""
            
            combined = f"Original Instructions:\n{ceo_context}\n\nGenerated System Prompt:\n{pe_output}"
            yc_output = YamlCompilerAgent().execute(combined, session_id=session_id, config=config)
            return {"messages": [AIMessage(content=yc_output)]}

        # 3. Validator Node
        def run_validator(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] Validator Step 3: AgentValidatorAgent")
            messages = state.get("messages", [])
            last_msg = messages[-1].content if messages else ""
            val_output = AgentValidatorAgent().execute(last_msg, session_id=session_id, config=config)
            return {"messages": [AIMessage(content=f"VALIDATION_RESULT:\n{val_output}\n---\nMANIFEST:\n{last_msg}")]}

        # 4. Transpiler Node
        def run_transpiler(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] Approver Step 4: Transpiler & Packaging")
            messages = state.get("messages", [])
            last_msg = messages[-1].content if messages else ""
            
            import re, ast
            blocks = re.findall(r'```yaml\n(.*?)\n```', last_msg, re.DOTALL)
            oracle_yaml = ""
            proj_yaml = ""
            
            if "Returning structured response:" in last_msg:
                try:
                    dict_str = last_msg.split("Returning structured response:", 1)[1].strip()
                    parsed_dict = ast.literal_eval(dict_str)
                    if isinstance(parsed_dict, dict):
                        if "orchestrator_agent" in parsed_dict:
                            oracle_yaml = yaml.dump(parsed_dict["orchestrator_agent"], sort_keys=False)
                        if "project_yaml" in parsed_dict:
                            proj_yaml = parsed_dict["project_yaml"]
                except Exception as e:
                    logger.error(f"Failed to parse structured response: {e}")
            
            if not oracle_yaml:
                oracle_yaml = blocks[1] if len(blocks) >= 2 else (blocks[0] if blocks else last_msg)
            if not proj_yaml:
                proj_yaml = blocks[0] if len(blocks) >= 2 else "name: default_project\n"
            
            transpiled_agent_yaml = DeepagentTranspilerAgent().execute({"oracle_yaml": oracle_yaml}, session_id=session_id, config=config)
            final_output = f"```yaml\n{proj_yaml}\n```\n\n```yaml\n{oracle_yaml}\n```\n\n{transpiled_agent_yaml}"
            return {"messages": [AIMessage(content=final_output)]}

        # 5. Disk Writer Node
        def run_disk_writer(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] Approver Step 5: Writing Agent to Disk")
            messages = state.get("messages", [])
            last_msg = messages[-1].content if messages else ""
            
            if "FAILURE" in last_msg or "```yaml" not in last_msg:
                return {"messages": [AIMessage(content=last_msg)]}
                
            try:
                import re, pathlib
                blocks = re.findall(r'```yaml\n(.*?)\n```', last_msg, re.DOTALL)
                if len(blocks) >= 2:
                    proj_yaml_str = blocks[0]
                    agent_yaml_str = blocks[1]
                    
                    agent_dict = yaml.safe_load(agent_yaml_str) or {}
                    raw_agent_name = agent_dict.get("name", f"unnamed_agent_{str(uuid.uuid4())[:8]}")
                    agent_name = re.sub(r'[^a-zA-Z0-9_]', '_', raw_agent_name).strip('_').lower()
                    
                    agents_dir = pathlib.Path(__file__).resolve().parent.parent
                    new_agent_dir = agents_dir / agent_name
                    new_agent_dir.mkdir(parents=True, exist_ok=True)
                    
                    with open(new_agent_dir / "project.yaml", "w", encoding="utf-8") as f:
                        f.write(proj_yaml_str)
                    with open(new_agent_dir / "agent.yaml", "w", encoding="utf-8") as f:
                        f.write(agent_yaml_str)
                        
                    success_msg = f"{last_msg}\n\n**SUCCESS**: Agent '{agent_name}' validated and written to `{new_agent_dir}`!"
                    return {"messages": [AIMessage(content=success_msg)]}
            except Exception as e:
                logger.error(f"Failed to write agent to disk: {e}")
                
            return {"messages": [AIMessage(content=last_msg)]}

        # Build Graph
        builder = StateGraph(DeepAgentState)
        builder.add_node("prompt_engineer", run_prompt_engineer)
        builder.add_node("yaml_compiler", run_yaml_compiler)
        builder.add_node("validator", run_validator)
        builder.add_node("transpiler", run_transpiler)
        builder.add_node("disk_writer", run_disk_writer)
        
        builder.add_edge(START, "prompt_engineer")
        builder.add_edge("prompt_engineer", "yaml_compiler")
        builder.add_edge("yaml_compiler", "validator")
        builder.add_edge("validator", "transpiler")
        builder.add_edge("transpiler", "disk_writer")
        builder.add_edge("disk_writer", END)
        
        graph = builder.compile()
        
        try:
            result = graph.invoke(initial_state, config=config or {})
            logger.info(f"[{session_id}] PM Builder-Validator-Approver pipeline completed.")
        except Exception as e:
            logger.error(f"[{session_id}] PM pipeline failed: {e}")
            result = {}
            
        return result.get("messages", [])[-1].content if result.get("messages") else "FAILURE: No output produced."
