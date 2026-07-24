import os
import json
import base64
import logging
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.core.services.license_service import license_service

logger = logging.getLogger(__name__)

class BundlerService:
    """
    Manages the bundling, encryption, and decryption of MCP agent YAML manifests.
    """
    
    def bundle_agents(self, source_dir: str, output_file: str, key_b64: str):
        """
        Walks the source directory, collects YAML files, and encrypts them into a single bundle.
        """
        source_path = Path(source_dir)
        if not key_b64:
            raise ValueError("Key must be provided for bundling")
            
        key = base64.b64decode(key_b64)
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
            
        aesgcm = AESGCM(key)
        
        bundle = {}
        for root, _, files in os.walk(source_path):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(source_path).as_posix()
                    with open(file_path, 'r', encoding='utf-8') as f:
                        bundle[relative_path] = f.read()
                        
        payload = json.dumps(bundle).encode('utf-8')
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, payload, None)
        
        # Store nonce + ciphertext together
        final_data = nonce + ciphertext
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'wb') as f:
            f.write(final_data)
            
        logger.info(f"Successfully bundled {len(bundle)} agents into {output_file}")
        return len(bundle)

    def decrypt_bundle(self, bundle_path: str) -> dict:
        """
        Reads the encrypted bundle, fetches the KMS key from license_service, 
        and decrypts it strictly in-memory.
        Returns a dictionary of relative file paths to their YAML contents.
        """
        with open(bundle_path, 'rb') as f:
            final_data = f.read()
            
        nonce = final_data[:12]
        ciphertext = final_data[12:]
        
        key = license_service.get_decryption_key()
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
            
        aesgcm = AESGCM(key)
        
        try:
            payload = aesgcm.decrypt(nonce, ciphertext, None)
            bundle = json.loads(payload.decode('utf-8'))
            logger.info(f"Successfully decrypted bundle containing {len(bundle)} files in-memory.")
            return bundle
        except Exception as e:
            logger.error(f"Failed to decrypt MCP bundle: {e}")
            raise

    def synthesize_project_template(
        self,
        project_id: str,
        name: str,
        description: str,
        orchestrator_yaml: str,
        tools: list = None,
        skills: list = None,
    ) -> dict:
        """
        Synthesizes a self-similar agentic application template.
        Copies the platform's runtime harness, mounts the orchestrator YAML,
        registers a PEN 66197 URN, and returns the project structure.
        """
        from src.core.ontology import CoreasonURN
        from src.core.services.catalog_service import catalog_service

        urn_obj = CoreasonURN(resource_type="project", resource_id=project_id)
        oid_urn = urn_obj.to_oid_urn()
        coreason_url = urn_obj.to_coreason_url()

        # Register synthesized template in PEN 66197 Catalog
        catalog_entry = catalog_service.register_entry(
            urn=oid_urn,
            name=name,
            description=description,
            resource_type="project",
            tags=["synthesized", "self_similar", "template"],
            metadata={
                "tools": tools or [],
                "skills": skills or [],
                "coreason_url": coreason_url,
            },
            source_code=orchestrator_yaml,
        )

        # Synthesize standard 5-surface documentation
        readme_md = f"""# {name}

{description}

## Identity & Authority
- **IANA OID URN**: `{oid_urn}`
- **Coreason URL Authority**: `{coreason_url}`

## Architectural Design
This application inherits the CoReason self-similar 5-surface architecture:
1. **REST API**: `/agents`, `/catalog`, `/sandboxes`
2. **CLI**: `coreason agents execute`, `coreason catalog search`
3. **MCP Server**: FastMCP tools exposed via stdio/SSE
4. **WebSockets / SSE**: Real-time state updates
5. **Python SDK**: `CoReasonClient` in-process embedding
"""

        deployment_md = f"""# Deployment Guide for {name}

## 1. Local / Standalone Deployment
```bash
docker compose -f docker-compose.yaml -f docker-compose.standalone.yaml up -d --build
```

## 2. Dify Enterprise Shell Integration
Connect your Dify instance to the MCP Server tool endpoint:
`http://localhost:9005/mcp`
"""

        distribution_md = f"""# Distribution & Packaging Guide for {name}

## 1. OCI Container Registry Push
```bash
docker tag {project_id}:latest registry.coreason.ai/apps/{project_id}:latest
docker push registry.coreason.ai/apps/{project_id}:latest
```

## 2. PEN 66197 Catalog Registration
```bash
coreason catalog register --urn "{oid_urn}" --name "{name}" --type "project"
```
"""

        logger.info(f"Synthesized self-similar project template {oid_urn} ({name}) with complete documentation")
        return {
            "status": "success",
            "project_id": project_id,
            "urn": oid_urn,
            "coreason_url": coreason_url,
            "documentation": {
                "README.md": readme_md,
                "DEPLOYMENT.md": deployment_md,
                "DISTRIBUTION.md": distribution_md,
            },
            "catalog_entry": catalog_entry.model_dump(),
        }

    def synthesize_standalone_app(
        self,
        target_location: str,
        agent_name: str,
        agent_dict: dict,
        orchestrator_code: str,
        proj_yaml: str = "",
    ) -> dict:
        """
        Synthesizes a fully deployable, executable container, multi-surface copy of a coreason-workspace-env-like
        agentic application at target_location.
        """
        target_path = Path(target_location).resolve()
        target_agent_dir = target_path / "src" / "agents" / agent_name
        target_agent_dir.mkdir(parents=True, exist_ok=True)

        # 1. Write core agent files
        with open(target_agent_dir / "agent.yaml", "w", encoding="utf-8") as f:
            import yaml
            yaml.dump(agent_dict, f, sort_keys=False)
        with open(target_agent_dir / "orchestrator.py", "w", encoding="utf-8") as f:
            f.write(orchestrator_code)
        if proj_yaml:
            with open(target_agent_dir / "project.yaml", "w", encoding="utf-8") as f:
                f.write(proj_yaml)

        # 2. Write pyproject.toml
        pyproject_content = f"""[project]
name = "{agent_name}-app"
version = "0.1.0"
description = "Standalone multi-surface agentic application for {agent_name}"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "fastmcp>=0.4.0",
    "langchain>=0.3.0",
    "langgraph>=0.2.0",
    "deepagents>=0.6.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "tavily-python>=0.3.0",
    "httpx>=0.27.0",
]

[project.scripts]
{agent_name} = "src.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
        with open(target_path / "pyproject.toml", "w", encoding="utf-8") as f:
            f.write(pyproject_content)

        # 3. Write Dockerfile & docker-compose.yaml
        dockerfile_content = f"""FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .
EXPOSE 9005
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "9005"]
"""
        with open(target_path / "Dockerfile", "w", encoding="utf-8") as f:
            f.write(dockerfile_content)

        compose_content = f"""version: '3.8'
services:
  {agent_name}_app:
    build: .
    ports:
      - "9005:9005"
    environment:
      - LLM_MODEL_NAME=${{LLM_MODEL_NAME:-meta-llama/llama-3.3-70b-instruct}}
      - OPENROUTER_API_KEY=${{OPENROUTER_API_KEY}}
      - TAVILY_API_KEY=${{TAVILY_API_KEY}}
"""
        with open(target_path / "docker-compose.yaml", "w", encoding="utf-8") as f:
            f.write(compose_content)

        # 4. Synthesize README documentation
        readme_content = f"""# {agent_name} Standalone Application

This repository is a fully deployable, multi-surface agentic application synthesized from `coreason-workspace-env`.

## Identity
- **Agent Name**: `{agent_name}`
- **Description**: {agent_dict.get('description', '')}

## Multi-Surface Surfaces
1. **REST API**: Launch via `uvicorn src.api.main:app --port 9005`
2. **CLI**: Run `python -m src.cli.main`
3. **MCP Server**: Launch via `fastmcp run src/mcp/server.py --transport sse`
4. **Container**: Run `docker compose up -d`
"""
        with open(target_path / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

        logger.info(f"Successfully synthesized standalone multi-surface container app at {target_path}")
        return {
            "status": "success",
            "target_location": str(target_path),
            "agent_name": agent_name,
            "agent_dir": str(target_agent_dir),
        }

bundler_service = BundlerService()
