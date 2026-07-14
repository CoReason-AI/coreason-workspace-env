from deepagents import DeepAgent


class AgentValidatorAgent(DeepAgent):
    """
    Unified deterministic Checker for the CoReason Agent Factory.
    Validates all factory artifacts against formal validation standards.
    Operates as a post-build gate in the Maker-Checker-Approver pipeline.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
