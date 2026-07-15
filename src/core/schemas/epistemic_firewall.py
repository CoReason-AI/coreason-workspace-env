from typing import Optional
from pydantic import BaseModel
from coreason_manifest.spec.ontology import (
    EpistemicProxyState,
    EpistemicQuarantineSnapshot,
    NeurosymbolicIngestionTopologyManifest,
    DocumentKnowledgeGraphManifest
)

class LibrarianRoutingState(BaseModel):
    """LangGraph State passed from factory_ceo to librarian_pm"""
    proxy: EpistemicProxyState
    directives: Optional[str] = None
