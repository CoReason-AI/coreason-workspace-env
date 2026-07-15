from typing import Any, Generic, TypeVar, Optional, TypedDict
from pydantic import BaseModel, Field

T = TypeVar('T')

class EpistemicQuarantineSnapshot(BaseModel):
    snapshot_id: str
    raw_payload: Any

class EpistemicProxyState(BaseModel):
    proxy_cid: str
    structural_type: str

class CognitiveDeliberativeEnvelopeState(BaseModel, Generic[T]):
    deliberation_trace: str = Field(..., max_length=100000)
    payload: Optional[T] = None

class CoreasonBaseState(TypedDict, total=False):
    pass

class MakerCheckerState(CoreasonBaseState, total=False):
    messages: list
    worker_result: str
    feedback: str
    attempts: int
    final_output: str

class OrchestratorCeoState(CoreasonBaseState, total=False):
    messages: list
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
