from typing import List, Optional
from pydantic import BaseModel, Field

class ProvenanceCitation(BaseModel):
    """A strict traceability receipt pointing to the exact origin of a claim."""
    citation_id: str = Field(..., description="Unique identifier for this citation (e.g., [1], [2])")
    source_uri: str = Field(..., description="Path, URL, or document ID of the source material")
    chunk_snippet: str = Field(..., description="The exact verbatim text chunk supporting the synthesis")
    temporal_context: str = Field(..., description="Timestamp or date of the source to resolve temporal conflicts")

class KnowledgeReceipt(BaseModel):
    """
    The strict output contract for the knowledge_consultant.
    Ensures no information is returned without cryptographic/verifiable provenance.
    """
    query: str = Field(..., description="The original question asked by the supervisor")
    synthesis: str = Field(..., description="The synthesized, high-signal answer to the query")
    confidence_score: float = Field(..., description="Agent's confidence in the synthesis (0.0 to 1.0)")
    provenance_receipts: List[ProvenanceCitation] = Field(
        ..., 
        min_length=1,
        description="List of all citations used to generate the synthesis"
    )
    missing_context: Optional[str] = Field(
        None, 
        description="Explicit declaration of what could NOT be answered due to lack of data"
    )
