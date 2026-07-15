from deepagents import DeepAgent
from src.core.skills import jinja2_ast_auditor


class AgentValidatorAgent(DeepAgent):
    """
    Unified deterministic Checker for the CoReason Agent Factory.
    Validates all factory artifacts against formal validation standards.
    Operates as a post-build gate in the Maker-Checker-Approver pipeline.
    """
    def __init__(self, **kwargs):
        tools = kwargs.pop("tools", [])
        tools.append(jinja2_ast_auditor)
        super().__init__(tools=tools, **kwargs)
