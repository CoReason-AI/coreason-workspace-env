from typing import List, Literal, Optional
from pydantic import BaseModel

class LegacyAgent(BaseModel):
    """A single agent extracted from the legacy codebase."""
    name: str
    raw_prompt: str
    type_guess: Literal["supervisor", "sub-agent", "ambiguous"]
    tools_used: List[str]
    source_file: str
    dependencies_guess: List[str]

class ToolSideEffect(BaseModel):
    """An unprotected side-effect found in legacy code."""
    function_name: str
    egress_type: Literal["http", "filesystem", "database", "subprocess", "unknown"]
    target: str
    source_file: str
    line_number: Optional[int]
    risk_level: Literal["critical", "high", "medium", "low"]

class StateGraphEdge(BaseModel):
    """An implicit state transition between legacy agents."""
    source_agent: str
    target_agent: str
    handoff_type: Literal["free_text", "json", "function_call", "unknown"]
    description: str

class SecurityFlag(BaseModel):
    """A security concern found during deconstruction."""
    flag_type: Literal["hardcoded_credential", "unprotected_egress", "missing_auth",
                       "raw_eval", "prompt_injection_surface", "unvalidated_input"]
    severity: Literal["critical", "high", "medium", "low"]
    location: str
    description: str
    remediation_hint: str

class LegacyIR(BaseModel):
    """
    The complete Intermediate Representation of a deconstructed legacy codebase.
    """
    source_repository: str
    scan_timestamp: str
    agents: List[LegacyAgent]
    tool_side_effects: List[ToolSideEffect]
    state_graph: List[StateGraphEdge]
    security_flags: List[SecurityFlag]
    raw_file_count: int
    total_lines_scanned: int
