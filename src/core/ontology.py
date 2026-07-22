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


class CoreasonURN(BaseModel):
    """
    URN Authority using Coreason AI's IANA Private Enterprise Number (66197).
    Supports OID URN: urn:oid:1.3.6.1.4.1.66197:<resource_type>:<resource_id>
    and Coreason URL: https://urn.coreason.ai/1.3.6.1.4.1.66197/<resource_type>/<resource_id>
    """
    pen: int = 66197
    resource_type: str = Field(description="project, agent, skill, workflow, component")
    resource_id: str
    tenant_id: Optional[str] = None

    @classmethod
    def parse(cls, urn_str: str) -> "CoreasonURN":
        clean = urn_str.strip()
        if clean.startswith("urn:oid:1.3.6.1.4.1.66197:"):
            parts = clean.replace("urn:oid:1.3.6.1.4.1.66197:", "").split(":")
            return cls(resource_type=parts[0], resource_id=":".join(parts[1:]))
        elif "urn.coreason.ai/1.3.6.1.4.1.66197/" in clean:
            path = clean.split("urn.coreason.ai/1.3.6.1.4.1.66197/", 1)[1]
            parts = path.strip("/").split("/")
            return cls(resource_type=parts[0], resource_id="/".join(parts[1:]))
        elif clean.startswith("urn:coreason:"):
            parts = clean.replace("urn:coreason:", "").split(":")
            return cls(resource_type=parts[0], resource_id=":".join(parts[1:]))
        else:
            raise ValueError(f"Invalid Coreason URN/URL format: {urn_str}")

    def to_oid_urn(self) -> str:
        return f"urn:oid:1.3.6.1.4.1.66197:{self.resource_type}:{self.resource_id}"

    def to_coreason_url(self) -> str:
        return f"https://urn.coreason.ai/1.3.6.1.4.1.66197/{self.resource_type}/{self.resource_id}"


class CatalogEntry(BaseModel):
    urn: str = Field(description="Canonical Coreason URN (PEN 66197)")
    name: str
    description: str
    resource_type: str = Field(description="project, agent, skill, workflow, component")
    version: str = "1.0.0"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_code: Optional[str] = None
    created_at: str
