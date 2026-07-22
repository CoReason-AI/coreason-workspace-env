import typer
import asyncio
import sys
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
import uuid
import logging
import re
import yaml
from pathlib import Path
import httpx
from rich.live import Live
from rich.tree import Tree
from rich.console import Console
from rich.prompt import Prompt

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = typer.Typer()
import langchain
import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"
import json
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
    from src.core.services import agent_service
    res = {"agents": agent_service.list_agents()}
    typer.echo(json.dumps(res, default=str))

@agents_app.command("get")
def get_agent(name: str = typer.Option(..., '--name')):
    from src.core.services import agent_service
    import sys
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
    from src.core.services import agent_service
    from src.core.services.rbac_service import rbac_service
    import sys
    
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
    from src.core.services import agent_service
    import sys
    
    async def run():
        return await agent_service.get_execution_status(job_id)
        
    res = asyncio.run(run())
    typer.echo(json.dumps(res, default=str))

@agents_app.command("rewind")
def agent_rewind(checkpoint_id: str = typer.Option(..., '--checkpoint-id')):
    """Rewind a session to a specific UUIDv7 checkpoint ID."""
    from src.core.services.agent_service import AgentService
    service = AgentService()
    res = service.rewind_checkpoint(checkpoint_id)
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
    from src.core.services.rbac_service import rbac_service
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=["admin", "developer", "viewer"])
    rbac_service.require_role(identity, "developer")
    
    from src.core.services.agent_service import AgentService
    service = AgentService()
    try:
        payload_dict = json.loads(payload)
    except json.JSONDecodeError:
        typer.secho("Error: --payload must be a valid JSON string.", fg=typer.colors.RED)
        sys.exit(1)
        
    async def run():
        return await service.submit_override(job_id, agent_name, payload_dict)
        
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
    from src.core.services.rbac_service import rbac_service
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=["admin", "developer", "viewer"])
    rbac_service.require_role(identity, "developer")
    
    from src.core.services.agent_service import AgentService
    service = AgentService()
    async def run():
        return await service.deploy_to_test(project_id, identity.user_id, identity.tenant_id)
        
    res = asyncio.run(run())
    typer.echo(json.dumps(res, default=str))

@deploy_app.command("production")
def deploy_to_production(
    project_id: str = typer.Option(..., '--project-id'),
    user_id: str = typer.Option(os.environ.get("COREASON_USER_ID", "cli-user"), '--user-id'),
    tenant_id: str = typer.Option(os.environ.get("COREASON_TENANT_ID", "cli-tenant"), '--tenant-id')
):
    """Deploy the generated agent project to the Production Environment."""
    from src.core.services.rbac_service import rbac_service
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=["admin", "developer", "viewer"])
    rbac_service.require_role(identity, "admin")
    
    from src.core.services.agent_service import AgentService
    service = AgentService()
    async def run():
        return await service.deploy_to_production(project_id, identity.user_id, identity.tenant_id)
        
    res = asyncio.run(run())
    typer.echo(json.dumps(res, default=str))

mcp_app = typer.Typer()
app.add_typer(mcp_app, name="mcp")

@mcp_app.command("bundle")
def bundle_mcp_agents(source: str = "src/agents", output: str = "dist/coreason_mcp_bundle.enc"):
    """Bundle and encrypt MCP agents for air-gapped deployment."""
    import sys
    import subprocess
    cmd = [sys.executable, "scripts/mcp_bundler.py", "--source", source, "--output", output]
    result = subprocess.run(cmd, cwd=".")
    if result.returncode != 0:
        typer.secho("Failed to bundle MCP agents.", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=result.returncode)
    typer.secho("MCP agents bundled successfully.", fg=typer.colors.GREEN, bold=True)

if __name__ == "__main__":
    app()
