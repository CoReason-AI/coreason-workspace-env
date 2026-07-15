import outlines
from pydantic import BaseModel
from typing import Type, TypeVar, Any
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class FSMDecoder:
    """
    Hybrid Deterministic Enforcement (FSM Decoding).
    For local Sovereign models (e.g., vLLM), we cannot rely entirely on prompt engineering
    to guarantee valid JSON outputs matching Pydantic schemas.
    This class uses `outlines` to compile a Finite State Machine (FSM) based on the 
    Pydantic schema and forces the local LLM to ONLY output tokens that conform to that FSM.
    """
    def __init__(self, model_name: str = "nvidia/nemotron-3-nano-30b-a3b:free"):
        # In a real environment, this connects to the local vLLM KServe endpoint
        # For remote API models, we fall back to standard LangChain StructuredOutputParsers
        # with retry logic.
        try:
            self.model = outlines.models.vllm(model_name)
            self.is_local = True
            logger.info(f"FSM Decoder initialized for local model: {model_name}")
        except Exception as e:
            logger.warning(f"Could not initialize outlines vLLM. Falling back to API mode: {e}")
            self.is_local = False

    def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        """
        Forces the LLM to output a valid JSON string matching the Pydantic schema.
        """
        if self.is_local:
            generator = outlines.generate.json(self.model, schema)
            result_json = generator(prompt)
            return schema.model_validate_json(result_json)
        else:
            logger.warning("FSM Decoding bypassed (using remote API). Falling back to LangChain structured outputs.")
            # Genuine fallback for Cloud API models using with_structured_output
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(schema)
            from langchain_core.messages import HumanMessage
            return llm.invoke([HumanMessage(content=prompt)])

# Singleton instance
fsm_decoder = FSMDecoder()
