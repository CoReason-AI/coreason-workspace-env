import os
import uuid
import yaml
import logging
from typing import Any
from src.core.base_agent import DeepAgent
from deepagents.graph import DeepAgentState

from langchain_core.runnables import RunnableLambda
from deepagents.graph import create_deep_agent

logger = logging.getLogger(__name__)

class AgentPmAgent(DeepAgent):
    """
    Project Manager orchestrating the agent generation pipeline via create_deep_agent.
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
You have two subagents exposed as tools: prompt_engineer, yaml_compiler.
Step 1: Delegate the user's context to prompt_engineer.
Step 2: Delegate the prompt_engineer's output to yaml_compiler.
Once complete, return the final Markdown response.
"""
        self.system_prompt = f"{base_prompt}\n{pm_prompt}"

    def execute(self, context: Any, session_id: str = None, config: dict = None) -> str:
        """
        Executes pipeline using a deterministic linear StateGraph.
        """
        logger.info(f"*** [{session_id}] AgentPM initiating deterministic StateGraph pipeline! ***")
        
        from src.agents.prompt_engineer.orchestrator import PromptEngineerAgent
        from src.agents.yaml_compiler.orchestrator import YamlCompilerAgent
        from langgraph.graph import StateGraph, START, END
        from langchain_core.messages import AIMessage
        
        # 1. Prepare initial state
        initial_state = {"messages": context} if isinstance(context, list) else {"messages": [("user", str(context))]}
        
        # 2. Define node execution logic
        def run_prompt_engineer(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] PM Step 1: Delegating to PromptEngineerAgent")
            messages = state.get("messages", [])
            last_msg = messages[-1].content if messages else str(state)
            pe_output = PromptEngineerAgent().execute(last_msg, session_id=session_id, config=config)
            return {"messages": [AIMessage(content=pe_output)]}
            
        def run_yaml_compiler(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] PM Step 2: Delegating to YamlCompilerAgent")
            messages = state.get("messages", [])
            ceo_context = messages[0].content if messages else ""
            pe_output = messages[-1].content if len(messages) > 1 else ""
            
            combined_context = f"Original Instructions:\n{ceo_context}\n\nGenerated System Prompt to Inject:\n{pe_output}"
            
            yc_output = YamlCompilerAgent().execute(combined_context, session_id=session_id, config=config)
            return {"messages": [AIMessage(content=yc_output)]}
            
        def run_transpiler(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] PM Step 2.5: Delegating to DeepagentTranspilerAgent")
            messages = state.get("messages", [])
            last_msg = messages[-1].content if messages else ""
            
            import re
            import ast
            import yaml
            
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
            
            from src.agents.deepagent_transpiler.orchestrator import DeepagentTranspilerAgent
            transpiled_agent_yaml = DeepagentTranspilerAgent().execute({"oracle_yaml": oracle_yaml}, session_id=session_id, config=config)
            
            # Repackage the project yaml, oracle yaml, and transpiled agent yaml so disk_writer can write all of them
            final_output = f"```yaml\n{proj_yaml}\n```\n\n```yaml\n{oracle_yaml}\n```\n\n{transpiled_agent_yaml}"
            
            return {"messages": [AIMessage(content=final_output)]}
            
        def run_disk_writer(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] PM Step 3: Saving compiled agent to disk")
            messages = state.get("messages", [])
            last_msg = messages[-1].content if messages else ""
            
            if "FAILURE" in last_msg or "```yaml" not in last_msg:
                return {"messages": [AIMessage(content=last_msg)]}
                
            try:
                import re, pathlib
                blocks = re.findall(r'```yaml\n(.*?)\n```', last_msg, re.DOTALL)
                if len(blocks) >= 2:
                    proj_yaml_str = blocks[0]
                    if len(blocks) >= 3:
                        oracle_yaml_str = blocks[1]
                        agent_yaml_str = blocks[2]
                    else:
                        oracle_yaml_str = ""
                        agent_yaml_str = blocks[1]
                    
                    agent_dict = yaml.safe_load(agent_yaml_str)
                    agent_name = agent_dict.get("name", f"unnamed_agent_{str(uuid.uuid4())[:8]}")
                    
                    agents_dir = pathlib.Path(__file__).resolve().parent.parent
                    new_agent_dir = agents_dir / agent_name
                    new_agent_dir.mkdir(parents=True, exist_ok=True)
                    
                    with open(new_agent_dir / "project.yaml", "w", encoding="utf-8") as f:
                        f.write(proj_yaml_str)
                        
                    if oracle_yaml_str:
                        with open(new_agent_dir / "oracle_agent.yaml", "w", encoding="utf-8") as f:
                            f.write(oracle_yaml_str)
                        
                    with open(new_agent_dir / "agent.yaml", "w", encoding="utf-8") as f:
                        f.write(agent_yaml_str)
                        
                    with open(new_agent_dir / "orchestrator.py", "w", encoding="utf-8") as f:
                        f.write(f"\"\"\"Orchestrator for {agent_name}\"\"\"\n")
                        
                    success_msg = f"{last_msg}\n\n**SUCCESS**: Agent '{agent_name}' written to `{new_agent_dir}`!"
                    return {"messages": [AIMessage(content=success_msg)]}
            except Exception as e:
                logger.error(f"Failed to write agent to disk: {e}")
                
            return {"messages": [AIMessage(content=last_msg)]}
            
        # 3. Build linear StateGraph
        builder = StateGraph(DeepAgentState)
        builder.add_node("prompt_engineer", run_prompt_engineer)
        builder.add_node("yaml_compiler", run_yaml_compiler)
        builder.add_node("transpiler", run_transpiler)
        builder.add_node("disk_writer", run_disk_writer)
        
        builder.add_edge(START, "prompt_engineer")
        builder.add_edge("prompt_engineer", "yaml_compiler")
        builder.add_edge("yaml_compiler", "transpiler")
        builder.add_edge("transpiler", "disk_writer")
        builder.add_edge("disk_writer", END)
        
        graph = builder.compile()
        
        # 4. Invoke graph execution
        try:
            result = graph.invoke(initial_state, config=config or {})
            logger.info(f"[{session_id}] PM deterministic pipeline executed successfully.")
        except Exception as e:
            logger.error(f"[{session_id}] PM deterministic pipeline failed: {e}")
            result = {}
            
        final_message = result.get("messages", [])[-1].content if result.get("messages") else "FAILURE: No output produced."
        return final_message
