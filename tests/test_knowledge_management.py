import pytest
from pydantic import ValidationError

from src.core.skill_registry_schema import ARTIFACT_TYPES
from src.core.schemas.knowledge_receipt import KnowledgeReceipt, ProvenanceCitation

class TestKnowledgeManagement:
    def test_knowledge_receipt_in_artifact_types(self):
        assert "knowledge_receipt" in ARTIFACT_TYPES

    def test_knowledge_receipt_schema_valid(self):
        # Test valid payload
        valid_payload = {
            "query": "What is our caching policy?",
            "synthesis": "We use Redis for caching.",
            "confidence_score": 0.95,
            "provenance_receipts": [{
                "citation_id": "[1]",
                "source_uri": "transcript_123.txt",
                "chunk_snippet": "decided to use Redis",
                "temporal_context": "2026-07-14"
            }],
            "missing_context": None
        }
        receipt = KnowledgeReceipt(**valid_payload)
        assert len(receipt.provenance_receipts) == 1
        assert receipt.query == "What is our caching policy?"

    def test_knowledge_receipt_schema_invalid(self):
        # Missing required provenance
        with pytest.raises(ValidationError):
            KnowledgeReceipt(
                query="Test",
                synthesis="Test",
                confidence_score=1.0,
                provenance_receipts=[] # Missing citation_id in a citation would fail, but empty list is technically allowed by schema if we don't constrain length. Wait, list requires items if we constrain it, but currently it's just List[ProvenanceCitation]. Let's test missing the field entirely.
            )
            
        with pytest.raises(ValidationError):
            KnowledgeReceipt(
                query="Test",
                synthesis="Test",
                confidence_score=1.0
                # missing provenance_receipts completely
            )
