# The Epistemic Firewall

As Agentic Retrieval-Augmented Generation (RAG) matures, the most severe architectural vulnerability facing enterprise deployments is **Data Provenance Poisoning**. Standard vector stores operate on a model of implicit trust; if an attacker or a faulty pipeline injects a malicious or hallucinated document into the database, the retrieving agent treats it as absolute ground truth.

The CoReason platform fundamentally rearchitects enterprise data retrieval through the implementation of an **Epistemic Firewall** based on strict Zero-Trust principles.

## Decoupling Probabilistic Reasoning

Generative language models within the platform are mathematically forbidden from executing direct queries against high-entropy raw data lakes or unverified external APIs. 

The Epistemic Firewall acts as a structural boundary that physically decouples the agent's probabilistic reasoning from deterministic computation and verified data retrieval. The LLM is a blind, mathematically bounded planner. It only ever receives declarative, strongly typed representations of data.

## Cryptographic Provenance

To enforce the Epistemic Firewall, the platform introduces a multi-stage cryptographic pipeline that redefines how agents consume non-parametric knowledge.

1. **Quarantine and Ingestion**: Raw data is initially quarantined. An isolated ingestion pipeline processes documents, mathematically extracting them into a highly structured `pgvector` database.
2. **Cryptographic Signing**: During extraction, the system generates a SHA-256 hash of the specific data chunk, which is then cryptographically signed using an enterprise private key, such as **Ed25519**.
3. **Verification**: When an agent requires information, it does not query the vector database directly. Instead, a deterministic sub-routine retrieves the data and verifies the cryptographic signature against a public key infrastructure.
4. **KnowledgeReceipt Injection**: If the signature is mathematically valid, the data is wrapped in a strongly typed `KnowledgeReceipt`. This receipt—containing the verified data, its Merkle-DAG derivation history, and its cryptographic provenance—is then securely injected into the agent's context.

## Zero-Trust Retrieval

If a retrieved chunk's signature is invalid or missing, the retrieval gateway automatically drops it, triggering an immediate security alert. 

This implementation of **proof-carrying data** entirely mitigates prompt injection via contaminated memory stores. Every quantitative output, regulatory reference, or factual claim processed by the language model is guaranteed to originate exclusively from a verified, tamper-evident source.
