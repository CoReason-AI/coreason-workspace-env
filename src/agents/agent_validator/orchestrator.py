import os
import yaml
import logging
from typing import Any, Dict
from src.core.base_agent import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from langchain.agents import create_agent

logger = logging.getLogger(__name__)

@tool
def e2b_data_analysis_tool(code: str) -> str:
    """Executes Python code in a secure E2B sandbox and returns the result."""
    try:
        from e2b_code_interpreter import CodeInterpreter
        sandbox = CodeInterpreter()
        execution = sandbox.notebook.exec_cell(code)
        if execution.error:
            sandbox.close()
            return f"Error: {execution.error.name} - {execution.error.value}\n{execution.error.traceback}"
        
        results = []
        for result in execution.results:
            if result.is_main_result:
                results.append(str(result.text))
        
        logs = []
        if execution.logs.stdout:
            logs.append("\n".join(execution.logs.stdout))
        if execution.logs.stderr:
            logs.append("\n".join(execution.logs.stderr))
            
        sandbox.close()
        return "\n".join(results + logs) or "Code executed successfully."
    except ImportError:
        return "E2B Code Interpreter is not installed."
    except Exception as e:
        return f"Sandbox Error: {str(e)}"

class ValidatorOutput(BaseModel):
    is_valid: bool = Field(description="True if the output conforms to standards, False otherwise.")
    feedback: str = Field(description="Actionable feedback for remediation if invalid.")

class AgentValidatorAgent(DeepAgent):
    """
    Checker logic for evaluating generated artifacts.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
        
        from src.core.config import settings
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL_NAME,
            api_key=settings.LLM_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            base_url=settings.LLM_BASE_URL
        )
        self.structured_llm = self.llm.with_structured_output(ValidatorOutput)
        
        # Initialize E2B tool
        if settings.E2B_API_KEY:
            os.environ["E2B_API_KEY"] = settings.E2B_API_KEY
            self.e2b_tool = e2b_data_analysis_tool
        else:
            self.e2b_tool = None

    def execute(self, payload: dict, session_id: str = None, config: dict = None) -> ValidatorOutput:
        """
        Executes validation checking against standards.
        """
        prompt = self.agent_spec.get("system_prompt", "You are an expert agent validator.")
        
        # Load standards
        standards = "Ensure the output is well formed and deterministic. No mocks or stubs allowed."
        
        logger.info(f"[{session_id}] AgentValidator checking artifacts.")
        
        if config is None:
            config = {}
                
        # Setup tools
        tools = []
        if self.e2b_tool:
            tools.append(self.e2b_tool)
            
        # Run ReAct agent to allow code execution before final answer
        if tools:
            react_agent = create_agent(self.llm, tools, system_prompt=prompt + f" Standards: {standards}")
            messages = [HumanMessage(content=f"Please validate this output: {payload}")]
            result_state = react_agent.invoke({"messages": messages}, config=config)
            final_message = result_state["messages"][-1]
            
            # Parse the final output into ValidatorOutput
            result = self.structured_llm.invoke([final_message])
        else:
            messages = [
                SystemMessage(content=prompt + f" Standards: {standards}"),
                HumanMessage(content=f"Please validate this output: {payload}")
            ]
            result = self.structured_llm.invoke(messages, config=config)
            
        return result
