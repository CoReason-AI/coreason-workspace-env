import typer
import asyncio
import sys
from typing import Optional
from dotenv import load_dotenv
import uuid
import logging
import re
import yaml
from pathlib import Path
import httpx
import os
import json

load_dotenv()

from src.core.services import agent_service
from src.core.services.rbac_service import rbac_service

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = typer.Typer()
import langchain
os.environ["LANGCHAIN_TRACING_V2"] = "false"
agents_app = typer.Typer()
app.add_typer(agents_app, name="agents")

@app.callback()
def main(pretty: bool = False):
    pass

@app.command()
def health():
    """Check system health."""
    typer.echo(json.dumps({"status": "healthy"}))



@app.command()
def test(coverage: bool = False, e2e: bool = False, verbose: bool = False):
    """
    Run the strict test suite.
    """
    import subprocess
    import sys
    
    cmd = [sys.executable, "-m", "pytest"]
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
        
    if e2e:
        cmd.extend(["tests/test_agents_e2e.py"])
    
    try:
        result = subprocess.run(cmd, cwd=".")
        if result.returncode == 0:
            typer.secho("All Tests Passed! Zero Mock architecture verified.", fg=typer.colors.GREEN, bold=True)
        else:
            typer.secho("Test Suite Failed.", fg=typer.colors.RED, bold=True)
            raise typer.Exit(code=result.returncode)
    except KeyboardInterrupt:
        typer.secho("\nTest suite interrupted by user.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=130)

@agents_app.command("list")
def list_agents():
    res = {"agents": agent_service.list_agents()}
    typer.echo(json.dumps(res, default=str))

@agents_app.command("get")
def get_agent(name: str = typer.Option(..., '--name')):
    res = agent_service.get_agent(name)
    if not res:
        typer.echo("Not found")
        sys.exit(1)
    typer.echo(json.dumps({"agent": res}, default=str))

@agents_app.command("execute")
def execute_agent(
    name: str = typer.Option(..., '--name'), 
    payload: str = typer.Option('{}', '--payload'),
    user_id: str = typer.Option('cli-user', '--user-id'),
    tenant_id: str = typer.Option('cli-tenant', '--tenant-id')
):
    """
    Execute a native deepagent synchronously and return the structured JSON output.
    """
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=["admin", "developer", "viewer"])
    rbac_service.require_role(identity, "developer")
    
    try:
        payload_dict = json.loads(payload)
    except json.JSONDecodeError:
        typer.secho("Error: --payload must be a valid JSON string.", fg=typer.colors.RED)
        sys.exit(1)
        
    async def run():
        return await agent_service.execute_agent(
            agent_name=name,
            payload=payload_dict,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
    res = asyncio.run(run())
    typer.echo(json.dumps(res, default=str))

@agents_app.command("status")
def agent_status(job_id: str = typer.Option(..., '--job-id')):
    """Check the status of an enqueued job."""
    async def run():
        return await agent_service.get_execution_status(job_id)
        
    res = asyncio.run(run())
    typer.echo(json.dumps(res, default=str))

@agents_app.command("rewind")
def agent_rewind(checkpoint_id: str = typer.Option(..., '--checkpoint-id')):
    """Rewind a session to a specific UUIDv7 checkpoint ID."""
    res = agent_service.rewind_checkpoint(checkpoint_id)
    typer.echo(json.dumps(res, default=str))

@agents_app.command("override")
def submit_override(
    job_id: str = typer.Option(..., '--job-id'),
    agent_name: str = typer.Option(..., '--agent-name'),
    payload: str = typer.Option(..., '--payload'),
    user_id: str = typer.Option(os.environ.get("COREASON_USER_ID", "cli-user"), '--user-id'),
    tenant_id: str = typer.Option(os.environ.get("COREASON_TENANT_ID", "cli-tenant"), '--tenant-id')
):
    """HOTL Override: Intervene in a paused LangGraph thread by injecting a state payload."""
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=["admin", "developer", "viewer"])
    rbac_service.require_role(identity, "developer")
    
    try:
        payload_dict = json.loads(payload)
    except json.JSONDecodeError:
        typer.secho("Error: --payload must be a valid JSON string.", fg=typer.colors.RED)
        sys.exit(1)
        
    async def run():
        return await agent_service.submit_override(job_id, agent_name, payload_dict)
        
    res = asyncio.run(run())
    typer.echo(json.dumps(res, default=str))

deploy_app = typer.Typer()
app.add_typer(deploy_app, name="deploy")

@deploy_app.command("test")
def deploy_to_test(
    project_id: str = typer.Option(..., '--project-id'),
    user_id: str = typer.Option(os.environ.get("COREASON_USER_ID", "cli-user"), '--user-id'),
    tenant_id: str = typer.Option(os.environ.get("COREASON_TENANT_ID", "cli-tenant"), '--tenant-id')
):
    """Deploy the generated agent project to the Test Environment."""
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=["admin", "developer", "viewer"])
    rbac_service.require_role(identity, "developer")
    
    async def run():
        return await agent_service.deploy_to_test(project_id, identity.user_id, identity.tenant_id)
        
    res = asyncio.run(run())
    typer.echo(json.dumps(res, default=str))

@deploy_app.command("production")
def deploy_to_production(
    project_id: str = typer.Option(..., '--project-id'),
    user_id: str = typer.Option(os.environ.get("COREASON_USER_ID", "cli-user"), '--user-id'),
    tenant_id: str = typer.Option(os.environ.get("COREASON_TENANT_ID", "cli-tenant"), '--tenant-id')
):
    """Deploy the generated agent project to the Production Environment."""
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=["admin", "developer", "viewer"])
    rbac_service.require_role(identity, "admin")
    
    async def run():
        return await agent_service.deploy_to_production(project_id, identity.user_id, identity.tenant_id)
        
    res = asyncio.run(run())
    typer.echo(json.dumps(res, default=str))

mcp_app = typer.Typer()
app.add_typer(mcp_app, name="mcp")

@mcp_app.command("bundle")
def bundle_mcp_agents(source: str = "src/agents", output: str = "dist/coreason_mcp_bundle.enc"):
    """Bundle and encrypt MCP agents for air-gapped deployment."""
    from src.core.services.bundler_service import bundler_service
    
    key_b64 = os.environ.get("MCP_BUNDLE_KEY")
    if not key_b64:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import base64
        test_key = AESGCM.generate_key(bit_length=256)
        key_b64 = base64.b64encode(test_key).decode('utf-8')
        typer.secho(f"WARNING: MCP_BUNDLE_KEY not set. Generated a random test key: {key_b64}", fg=typer.colors.YELLOW)
        
    try:
        bundler_service.bundle_agents(source, output, key_b64)
        typer.secho("MCP agents bundled successfully.", fg=typer.colors.GREEN, bold=True)
    except Exception as e:
        typer.secho(f"Failed to bundle MCP agents: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)

skills_app = typer.Typer()
app.add_typer(skills_app, name="skills")

@skills_app.command("list")
def list_skills(category: Optional[str] = typer.Option(None, '--category')):
    """List all available skills in the registry."""
    from src.core.services import skill_service
    res = {"skills": skill_service.list_skills(category=category)}
    typer.echo(json.dumps(res, default=str))

@skills_app.command("get")
def get_skill(name: str = typer.Option(..., '--name')):
    """Get a specific skill's Markdown content and metadata."""
    from src.core.services import skill_service
    res = skill_service.get_skill(name)
    if not res:
        typer.echo("Not found")
        sys.exit(1)
    typer.echo(json.dumps({"skill": res}, default=str))

if __name__ == "__main__":
    app()
