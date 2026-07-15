# Epistemic Firewall

The **Epistemic Firewall** is a crucial security and architectural component designed for **Zero-Trust Knowledge**. 

Generative agents are prone to hallucination when ingesting massive, unstructured human transcripts directly. The Epistemic Firewall prevents this by physically blocking LLMs from reading raw text payloads.

## The Ingestion Pipeline

1. **Quarantine**: Raw text (transcripts, docs) is intercepted and stored in `epistemic_quarantine_snapshots`.
2. **Extraction**: The `knowledge_archivist` agent reads the quarantined text and uses a deterministic LLM output (`CognitiveDeliberativeEnvelopeState[DocumentKnowledgeGraphManifest]`) to extract discrete, structured facts.
3. **Storage**: These facts are embedded and stored in a `pgvector` database. The raw text is never passed further down the pipeline.

## The Retrieval Pipeline

When a downstream agent needs information, it must consult the `knowledge_consultant` agent.
1. The consultant queries the `pgvector` database.
2. It returns a `KnowledgeReceipt` that contains strictly the fetched facts alongside their cryptographic citations (provenance hashes).

By forcing all knowledge to pass through this structural extraction and citation process, we guarantee zero-trust, hallucination-free knowledge retrieval.
