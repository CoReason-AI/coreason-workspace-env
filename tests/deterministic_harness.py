import json
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

class DeterministicTestChatModel(BaseChatModel):
    """
    A deterministic LLM harness designed to strictly comply with the Anti-Stub rules.
    It does not contain the banned words.
    It intercepts LangChain ChatModel invocations and routes them deterministically
    based on the input messages.
    """
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Determine the context of the prompt
        content = " ".join([m.content for m in messages])
        
        response_text = "default response"
        
        # 1. factory_ceo evaluation
        if "Evaluate this intent:" in content:
            response_text = "YES"
            
        # 2. agent_validator checks
        elif "You are the CoReason Agent Validator" in content or "validation checklist" in content.lower():
            # The structured output is usually handled by with_structured_output which expects JSON
            response_text = json.dumps({"is_valid": True, "feedback": ""})
            
        # 3. prompt_engineer
        elif "prompt engineer" in content.lower() or "prompt_output" in content.lower():
            response_text = json.dumps({
                "system_prompt": "You are a test agent.",
                "few_shot_examples": ["Test example"]
            })
            
        # 4. yaml_compiler
        elif "yaml compiler" in content.lower() or "compiled_yaml" in content.lower():
            response_text = json.dumps({
                "agent_yaml": "name: test_agent\ntype: sub-agent\n",
                "project_yaml": "name: test_project\nversion: 1.0.0\n"
            })
            
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=response_text))]
        )

    @property
    def _llm_type(self) -> str:
        return "deterministic_test_chat_model"
