from typing import Any, Generic, TypeVar, Optional, TypedDict, Annotated
from enum import StrEnum
from pydantic import BaseModel, Field
from langchain.agents import AgentState
from deepagents.graph import DeepAgentState

T = TypeVar('T')

class EpistemicQuarantineSnapshot(BaseModel):
    snapshot_id: str
    raw_payload: Any

class EpistemicProxyState(BaseModel):
    proxy_cid: str
    structural_type: str

class CoreasonBaseState(AgentState, total=False):
    pass

class UserIdentity(BaseModel):
    user_id: str
    tenant_id: str
    roles: list[str]

class OrchestratorCeoState(DeepAgentState, total=False):
    raw_transcript: Optional[str]
    epistemic_proxy: Optional[EpistemicProxyState]
    is_saturated: bool

class SemanticNodeState(BaseModel):
    node_id: str
    label: str

class CausalDirectedEdgeState(BaseModel):
    source_id: str
    target_id: str
    relation: str

class DocumentKnowledgeGraphManifest(BaseModel):
    nodes: list[SemanticNodeState]
    edges: list[CausalDirectedEdgeState]

class ActionSpaceCategoryProfile(StrEnum):
    """
    Taxonomy for CQRS-compliant skill isolation:
    - oracle: Pure read-only information retrieval.
    - solver: Pure isolated compute/synthesis without external side-effects.
    - effector: State-mutating writes (e.g., file edits, DB commits, API POSTs).
    - substrate: Broad environment-level interactions.
    - sensory: User-facing projection or UI rendering.
    - node: Meta-orchestration or inter-agent delegation.
    """
    ORACLE = "oracle"
    SOLVER = "solver"
    EFFECTOR = "effector"
    SUBSTRATE = "substrate"
    SENSORY = "sensory"
    NODE = "node"

class TargetTopologyProfile(StrEnum):
    LINEAR = "linear"
    DAG = "dag"
    SWARM = "swarm"
    COUNCIL = "council"

class EpistemicSecurityProfile(BaseModel):
    network_isolation: bool = Field(default=False, description="If True, blocks internet egress.")
    allow_file_system: bool = Field(default=False, description="If True, allows local disk RW.")
    clearance_tier: int = Field(default=0, description="The clearance level of the agent.")

class AgentManifest(BaseModel):
    name: str = Field(description="The snake_case name of the agent, matching the folder.")
    description: str = Field(description="The declarative rationale for this agent.")
    system_prompt: str = Field(description="The core instructional prompt.")
    skills: list[str] = Field(default_factory=list, description="List of authorized skill names.")
    security: EpistemicSecurityProfile = Field(default_factory=EpistemicSecurityProfile)

class ProjectManifest(BaseModel):
    project_id: str = Field(description="UUIDv7 identifier.")
    project_name: str
    entrypoint: str = Field(description="The orchestrator agent folder name.")
    topology: TargetTopologyProfile = Field(default=TargetTopologyProfile.LINEAR)
    agents: list[str] = Field(default_factory=list, description="List of generated agent folders.")

class SkillManifest(BaseModel):
    name: str
    description: str
    category: ActionSpaceCategoryProfile

class ManifestViolationReceipt(BaseModel):
    failing_pointer: str = Field(description="The exact JSON pointer to the failing field.")
    violation_category: str = Field(description="e.g., missing_field, type_error, constraint_breach.")
    diagnostic_message: str = Field(description="Actionable instruction on how to fix the error.")

class ToolInvocationEvent(BaseModel):
    tool_name: str
    parameters: dict[str, Any]

class DeploymentRecord(BaseModel):
    deployment_id: str = Field(description="UUIDv7 identifier for the deployment.")
    project_id: str
    environment: str = Field(description="'test' or 'production'")
    bundle_hash: str
    user_id: str
    tenant_id: str
    status: str = Field(default="deployed")
    deployed_at: str


class SandboxRecord(BaseModel):
    sandbox_id: str = Field(description="UUIDv7 identifier for the sandbox environment.")
    project_id: str
    user_id: str
    tenant_id: str
    environment: str = Field(default="test")
    status: str = Field(default="running", description="running, terminated, error")
    provisioned_secrets: dict[str, str] = Field(default_factory=dict)
    connections: dict[str, str] = Field(default_factory=dict)
    mcp_servers: list[str] = Field(default_factory=list)
    workspace_path: str = Field(description="Path to isolated sandbox workspace.")
    created_at: str
