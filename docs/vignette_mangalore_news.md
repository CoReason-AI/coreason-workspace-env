# Vignette: Building a Mangalore News Agent

This vignette demonstrates how a single user can start the `coreason-workspace-env` and collaborate with the **Factory CEO** (`factory_ceo`) to design, build, validate, and publish a simple agentic application. Our goal is to create an agent that discusses the current local news in Mangalore, India.

## 1. Starting the Workspace

First, ensure your `.env` file is configured with the necessary LLM and infrastructure credentials. Then, start the workspace backing services (Postgres, etc.) and launch the MCP server:

```bash
# Start infrastructure and observability (Langfuse)
docker compose up -d

# Start the CoReason MCP Server to expose the factory to upstream orchestrators
uv run fastmcp run src/mcp/server.py --transport sse
```

This spins up the complete headless agent development platform and exposes it natively to IDEs and orchestration platforms like Dify.

## 2. Engaging the Factory CEO via Dify

Our platform strictly adheres to a **Headless-First Design**. Instead of using a custom CLI for chat, we rely on **Dify** for the interactive frontend.

1. In your Dify workspace, connect a new MCP Server pointing to the running `coreason-workspace-env` MCP endpoint.
2. Create a new Agent in Dify and give it access to the `execute_agent` and `run_native_deepagent` MCP tools.
3. In the Dify Chat UI, send your prompt:
   > "I want to create a simple agentic application that discusses the current local news in Mangalore, India."

## 3. The Orchestrator Interrogation Loop

Because the `factory_ceo` operates as a **State Machine Orchestrator** (adhering to the Context Engineering Harness philosophy), it realizes the context is underspecified. The CEO agent returns execution control, allowing the Dify UI to prompt you interactively:

> **[Dify / CEO]** I can help you build this agent. To ensure we build exactly what you need, please clarify:
> 1. Should this agent actively scrape specific local news sources (e.g., Daijiworld, Udayavani), or rely on general web search?
> 2. What is the intended output format? (e.g., a daily markdown summary, an interactive Q&A bot)
> **You:** It should use general web search via Tavily. The output should be an interactive Q&A bot.

## 4. Delegation and the Builder-Validator-Approver Workflow

With a fully saturated context, the `factory_ceo` delegates the raw context payload to its deterministic sub-agents executing natively via LangGraph:

1. **Planning (`agent_pm`):** Creates the project structure and tracking checklist.
2. **Building (`prompt_engineer` & `yaml_compiler`):** 
   - The `prompt_engineer` writes the system prompt detailing how to summarize and discuss Mangalore news.
   - The `yaml_compiler` writes the deterministic `agent.yaml` definition (in `src/agents/mangalore_news/agent.yaml`), wiring up the Tavily search tool and the LangGraph routing logic.
3. **Validation (`agent_validator`):** The validator checks the generated artifacts against the `src/core/skills/validation/` standards to ensure the schema is pure, the ID matches the folder namespace (`mangalore_news`), and the workflow is decoupled.

*You can observe this entire execution pipeline in real-time by viewing the Langfuse dashboard, which captures unified traces from both Dify and the DeepAgents runtime.*

## 5. Publishing the Agent

Once the validation is complete and the `mangalore_news` agent manifest is saved to disk, it is instantly available to the platform. 

Instead of dealing with custom CLI deployment commands, you can now natively expose this new agent directly in Dify:
1. In Dify, the new `mangalore_news` agent is automatically available through the CoReason MCP Server.
2. You can immediately embed it into a Dify Workflow, publish it as a standalone Dify WebApp, or expose it via Dify's REST API.

Your Mangalore News agent is now live, observable, and ready to discuss the latest updates from the coastal city!
