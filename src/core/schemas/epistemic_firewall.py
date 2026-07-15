from typing import Optional, Any
from pydantic import BaseModel

class EpistemicProxyState(BaseModel):
    proxy_cid: str
    structural_type: str

class EpistemicQuarantineSnapshot(BaseModel):
    snapshot_id: str
    raw_payload: Any

class NeurosymbolicIngestionTopologyManifest(BaseModel):
    pass

class DocumentKnowledgeGraphManifest(BaseModel):
    pass

class LibrarianRoutingState(BaseModel):
    """LangGraph State passed from factory_ceo to librarian_pm"""
    proxy: EpistemicProxyState
    directives: Optional[str] = None
