import typer
import asyncio
from typing import Optional
import uuid

app = typer.Typer()
import json
agents_app = typer.Typer()
mcp_app = typer.Typer()
app.add_typer(agents_app, name="agents")
app.add_typer(mcp_app, name="mcp")

@app.callback()
def main(pretty: bool = False):
    pass

@agents_app.command("list")
def list_agents():
    from src.core.services import agent_service
    res = {"agents": agent_service.list_agents()}
    typer.echo(json.dumps(res))

@agents_app.command("get")
def get_agent(name: str = typer.Option(..., '--name')):
    from src.core.services import agent_service
    import sys
    res = agent_service.get_agent(name)
    if not res:
        typer.echo("Not found")
        sys.exit(1)
    typer.echo(json.dumps({"agent": res}))

@mcp_app.command("list-servers")
def mcp_list_servers():
    from src.core.services import mcp_tool_service
    res = {"servers": mcp_tool_service.list_servers()}
    typer.echo(json.dumps(res))


@app.command()
def build(intent: str, output_dir: str = "./dist"):
    """
    Headless CLI for building a new agent platform via the coreason factory.
    """
    typer.echo(f"Initializing build with intent: '{intent}'")
    
    from src.core.services.orchestration_service import OrchestrationService
    orch = OrchestrationService()
    
    session_id = str(uuid.uuid7())
    user_id = "cli-user"
    
    async def run():
        typer.echo(f"Session ID: {session_id}")
        result = await orch.run_factory_graph(user_id, session_id, intent)
        if result.get("status") == "success":
            typer.echo(f"[SUCCESS] Platform bundled at: {result.get('artifact')}")
        else:
            typer.echo(f"[ERROR] Build failed: {result.get('details')}")
            
    asyncio.run(run())

@app.command()
def export_project(project_id: str, output_path: str, skip_state: bool = False, skip_docker: bool = False):
    """
    Export a project for air-gapped transfer.
    """
    typer.echo(f"Exporting project '{project_id}' to '{output_path}'...")
    from src.core.services import project_service
    
    async def run():
        try:
            result = await project_service.export_project(project_id, output_path, skip_state=skip_state, skip_docker=skip_docker)
            if result.get("status") == "success":
                typer.echo(f"[SUCCESS] Project exported to: {result.get('export_path')}")
                typer.echo(f"Files written: {result.get('files_written')}")
            else:
                typer.echo(f"[ERROR] Export failed.")
        except Exception as e:
            typer.echo(f"[ERROR] {e}")
            
    asyncio.run(run())

@app.command()
def import_project(name: str, import_path: str, description: str = "", skip_state: bool = False, skip_docker: bool = False):
    """
    Import a project from an air-gapped export.
    """
    typer.echo(f"Importing project from '{import_path}' with name '{name}'...")
    from src.core.services import project_service
    
    project_id = str(uuid.uuid7())
    
    async def run():
        try:
            result = await project_service.import_project(project_id, import_path, name, description, skip_state=skip_state, skip_docker=skip_docker)
            if result.get("status") == "success":
                typer.echo(f"[SUCCESS] Project imported successfully! Project ID: {project_id}")
                typer.echo(f"Files read: {result.get('files_read')}")
            else:
                typer.echo(f"[ERROR] Import failed.")
        except Exception as e:
            typer.echo(f"[ERROR] {e}")
            
    asyncio.run(run())

@app.command()
def push_project(project_id: str, registry_url: str, skip_state: bool = False, skip_docker: bool = False):
    """
    Push a project to an OCI registry (Industry Standard).
    """
    from rich.console import Console
    from src.sdk.client import CoReasonClient
    console = Console()
    
    async def run():
        try:
            client = CoReasonClient()
            with console.status(f"Pushing project '{project_id}' to '{registry_url}'...", spinner="dots"):
                result = await client.projects.push_bundle(project_id, registry_url, skip_state=skip_state, skip_docker=skip_docker)
            
            if result.get("status") == "success":
                console.print(f"[green][SUCCESS][/green] Project pushed successfully! Job ID: {result.get('job_id')}")
            else:
                console.print(f"[red][ERROR][/red] Push failed.")
        except Exception as e:
            console.print(f"[red][ERROR][/red] {e}")
            
    asyncio.run(run())

@app.command()
def pull_project(name: str, oci_uri: str, description: str = "", skip_state: bool = False, skip_docker: bool = False):
    """
    Pull a project from an OCI registry (Industry Standard).
    """
    from rich.console import Console
    from src.sdk.client import CoReasonClient
    console = Console()
    
    async def run():
        try:
            client = CoReasonClient()
            with console.status(f"Pulling project from '{oci_uri}' with name '{name}'...", spinner="dots"):
                result = await client.projects.pull_bundle(oci_uri, name, description, skip_state=skip_state, skip_docker=skip_docker)
                
            if result.get("status") == "success":
                console.print(f"[green][SUCCESS][/green] Project pulled successfully! Job ID: {result.get('job_id')}")
            else:
                console.print(f"[red][ERROR][/red] Pull failed.")
        except Exception as e:
            console.print(f"[red][ERROR][/red] {e}")
            
    asyncio.run(run())

if __name__ == "__main__":
    app()
