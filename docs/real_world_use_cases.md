# Real-World Use Cases & Vignettes

This document presents real-world production vignettes demonstrating how the CoReason AI Agent Building Factory synthesizes enterprise-grade agentic applications across diverse industries.

---

## Vignette 1: Enterprise Regulatory & Financial Compliance Monitoring Agent

### Objective
A Tier-1 financial institution requires an autonomous agentic application to monitor transaction logs, cross-reference SEC EDGAR filings, and generate audit-ready compliance reports.

### Architecture Topology
- **Orchestrator**: `fin_compliance_supervisor`
- **Sub-Agents**: `sec_filing_analyzer`, `transaction_auditor`, `report_compiler`
- **IANA PEN 66197 Identity**: `urn:oid:1.3.6.1.4.1.66197:project:fin_compliance_v1`
- **OpenShell Boundary Policy**:
  - `allowed_egress_domains`: `["api.sec.gov", "urn.coreason.ai"]`
  - `allow_subprocess`: `false`

### Synthesis & Execution Trace
1. Human compliance officer interacts with `factory_ceo` via Dify UI shell.
2. `factory_ceo` searches `CatalogService` for past financial compliance exemplars under PEN 66197.
3. `agent_pm` and `yaml_compiler` generate PyAgentSpec `agent.yaml` manifests and StateGraph topology.
4. `BundlerService` packages the application, auto-generating `README.md`, `DEPLOYMENT.md`, and `DISTRIBUTION.md`.
5. `SandboxService` provisions an OpenShell sandbox (`sandboxes/<sandbox_id>`) with bound PostgreSQL connection strings and SEC API secrets.
6. The application is deployed to production with OpenTelemetry + Langfuse tracing enabled.

---

## Vignette 2: Autonomous Healthcare Diagnostic & Hypotheses Generation Pipeline

### Objective
A medical research organization needs a closed-loop scientific agent to generate literature hypotheses, extract PubMed citations, and execute formal causal inference models using `dowhy`.

### Architecture Topology
- **Orchestrator**: `healthcare_research_supervisor`
- **Sub-Agents**: `pubmed_extractor`, `causal_inference_engine`, `hypothesis_critic`
- **IANA PEN 66197 Identity**: `urn:oid:1.3.6.1.4.1.66197:project:med_causal_v2`
- **Epistemic Firewall**: Cryptographically signed `KnowledgeReceipt` verification to prevent hallucination in medical reasoning.

---

## Vignette 3: Mangalore Regional News & Weather Synthesis Agent

### Objective
A regional news publisher deploys an automated agent pipeline to scrape local RSS feeds, format multilingual news digests (Kannada & English), and stream real-time updates via WebSockets.

### Execution Surface
- **CLI**: Executed via cron jobs using `coreason agents execute --name "news_scraper"`.
- **REST API**: Serves JSON news feeds to mobile apps.
- **Dify Enterprise Shell**: Provides interactive news querying for journalists.
