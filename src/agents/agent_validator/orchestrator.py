from deepagents import DeepAgent
from langchain_core.messages import SystemMessage
from src.core.validation.tier1_validator import tier1_engine


class AgentValidatorAgent(DeepAgent):
    """
    Unified deterministic Checker for the CoReason Agent Factory.
    Validates all factory artifacts against formal validation standards.
    Operates as a post-build gate in the Maker-Checker-Approver pipeline.
    """
    def __init__(self, **kwargs):
        # We explicitly do NOT append jinja2_ast_auditor to the tools list
        # to prevent the LLM from hallucinating calls. It is handled in Tier 1.
        super().__init__(**kwargs)

    def invoke(self, inputs: dict, config: dict = None, **kwargs):
        # Extract the artifact from the incoming messages (Maker's output)
        messages = inputs.get("messages", [])
        if not messages:
            return super().invoke(inputs, config, **kwargs)

        last_msg = messages[-1]
        payload = getattr(last_msg, "content", str(last_msg))
        
        # Determine artifact type (could be passed in config or derived)
        artifact_type = "unknown"
        if config and "configurable" in config:
            artifact_type = config["configurable"].get("artifact_type", "unknown")

        # Run Tier 1 Deterministic Fast-Fail
        tier1_result = tier1_engine.run_tier1_validation(payload, artifact_type=artifact_type)
        
        if tier1_result.get("status") == "FAIL":
            # Circuit Breaker: Return the GuardrailViolationEvent directly as a system message
            # This bypasses the LLM-as-a-judge entirely, failing fast.
            reason = tier1_result.get("reason", "Unknown Tier 1 Failure")
            return {
                "messages": [SystemMessage(content=reason)]
            }

        # If Tier 1 passes, proceed to LLM Tier 2/3 validation
        return super().invoke(inputs, config, **kwargs)

    async def ainvoke(self, inputs: dict, config: dict = None, **kwargs):
        messages = inputs.get("messages", [])
        if not messages:
            return await super().ainvoke(inputs, config, **kwargs)

        last_msg = messages[-1]
        payload = getattr(last_msg, "content", str(last_msg))
        
        artifact_type = "unknown"
        if config and "configurable" in config:
            artifact_type = config["configurable"].get("artifact_type", "unknown")

        tier1_result = tier1_engine.run_tier1_validation(payload, artifact_type=artifact_type)
        
        if tier1_result.get("status") == "FAIL":
            reason = tier1_result.get("reason", "Unknown Tier 1 Failure")
            return {
                "messages": [SystemMessage(content=reason)]
            }

        return await super().ainvoke(inputs, config, **kwargs)
