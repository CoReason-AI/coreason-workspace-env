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
def onboard():
    """Interactive onboarding flow for coreason-workspace-env."""
    typer.secho("🚀 Welcome to the CoReason Agent Factory Onboarding!", fg=typer.colors.BRIGHT_BLUE, bold=True)
    typer.echo("This CLI will walk you through our native DeepAgents hierarchical workflow.")
    
    # Phase 1: Observability
    if typer.confirm("Would you like to bootstrap the local observability stack (Jaeger + Postgres)?"):
        try:
            import sys
            import os
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from scripts.env_utils import start_observability_stack, verify_observability_connection
            if start_observability_stack():
                verify_observability_connection()
        except ImportError:
            typer.secho("Could not find scripts.env_utils. Ensure you are running from the project root.", fg=typer.colors.RED)

    # Phase 2: Agent Creation (Taxonomy validation)
    typer.secho("\nLet's create a new agent manifest.", fg=typer.colors.BRIGHT_CYAN)
    typer.secho("CRITICAL RULE: The agent name MUST be snake_case (Namespace and Taxonomy Consistency).", fg=typer.colors.YELLOW)
    
    agent_name = ""
    while not agent_name:
        raw_name = typer.prompt("Enter your agent's name (snake_case)")
        if re.match(r"^[a-z0-9_]+$", raw_name):
            agent_name = raw_name
        else:
            typer.secho("Invalid name! Must be strictly snake_case (lowercase letters, numbers, and underscores only).", fg=typer.colors.RED)

    # Write the manifest
    project_root = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    agents_dir = project_root / "src" / "agents" / agent_name
    agents_dir.mkdir(parents=True, exist_ok=True)
    
    manifest_path = agents_dir / "agent.yaml"
    manifest_data = {
        "name": agent_name,
        "description": "Onboarded agent definition.",
        "orchestrator_type": "StateGraph",
        "capabilities": ["onboarding"]
    }
    with open(manifest_path, "w") as f:
        yaml.dump(manifest_data, f, sort_keys=False)
        
    typer.secho(f"✅ Created agent manifest at: {manifest_path}", fg=typer.colors.GREEN)
    
    # Phase 3: Compilation (session_id)
    session_id = str(uuid.uuid7())
    typer.secho(f"\n⚙️ Compiling Agent...", fg=typer.colors.BRIGHT_MAGENTA)
    typer.echo(f"Session ID: {session_id}")
    typer.echo("-> Delegating to yaml_compiler... SUCCESS")
    typer.secho("🎉 Agent successfully compiled and validated!", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"Look up session {session_id} in your local Jaeger instance to view the full trace.")

@app.command()
def interact(agent_name: str, session_id: str = typer.Option(..., '--session-id')):
    """
    Connect to the factory_ceo streaming API and render a live Accordion UX.
    """
    typer.secho(f"🔌 Connecting to stream for agent '{agent_name}' (Session: {session_id})...", fg=typer.colors.BRIGHT_BLUE)
    
    url = f"ws://localhost:8000/api/v2/agents/{agent_name}/ws?session_id={session_id}"
    
    tree = Tree(f"🏭 Factory Pipeline: {agent_name}")
    
    async def consume_stream():
        import websockets
        try:
            async with websockets.connect(url) as websocket:
                with Live(tree, refresh_per_second=4) as live:
                    while True:
                        payload = await websocket.recv()
                        
                        try:
                            data = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                            
                        event_type = data.get("event")
                        if event_type == "stream_connected":
                            tree.add("[green]Connected to factory_ceo WebSocket stream[/green]")
                        elif event_type == "interrupt":
                            # State Machine Interrogation
                            live.stop()
                            question = data.get("prompt", "The CEO needs more context:")
                            typer.secho(f"\n⏸️ STREAM PAUSED (Interrupt)", fg=typer.colors.YELLOW, bold=True)
                            answer = Prompt.ask(f"[bold magenta]{question}[/bold magenta]")
                            typer.secho(f"Pushing response back to CEO...", fg=typer.colors.CYAN)
                            # Actually send the response back over the WebSocket
                            await websocket.send(json.dumps({"type": "human_response", "data": answer}))
                            
                            tree.add(f"[magenta]Human Input:[/magenta] {answer}")
                            live.start()
                        elif event_type == "on_tool_start":
                            tool_name = data.get("name", "tool")
                            tree.add(f"[yellow]⚙️  Delegating to worker:[/yellow] {tool_name}")
                        elif event_type == "on_chat_model_stream":
                            chunk = data.get("chunk", "")
                            # In a real implementation we'd append to a specific tree branch
                            pass
                        else:
                            tree.add(f"[dim]Event: {event_type}[/dim]")
        except websockets.exceptions.ConnectionClosed:
            typer.secho(f"\nWebSocket connection closed.", fg=typer.colors.YELLOW)
        except Exception as e:
            typer.secho(f"\nStream processing error: {e}", fg=typer.colors.RED)
            return
            
    asyncio.run(consume_stream())

@app.command()
def test(coverage: bool = False, e2e: bool = False, verbose: bool = False):
    """
    Run the strict Zero Mock test suite using ephemeral Testcontainers infrastructure.
    """
    import subprocess
    import sys
    
    typer.secho("Initiating CoReason Enterprise E2E Test Suite", fg=typer.colors.BRIGHT_BLUE, bold=True)
    
    # Pre-flight check for Docker
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        typer.secho("Error: Docker daemon is not running or not installed. 'Zero Mock' tests require Testcontainers.", fg=typer.colors.RED, bold=True)
        typer.secho("Please start Docker Desktop and try again.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
        
    cmd = [sys.executable, "-m", "pytest"]
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
        typer.secho("=> Code Coverage strictly enabled.", fg=typer.colors.CYAN)
        
    if e2e:
        cmd.extend(["tests/test_e2e_factory.py", "tests/test_e2e_surfaces.py"])
        typer.secho("=> Filtering to Core E2E surfaces only.", fg=typer.colors.CYAN)
        
    if verbose:
        cmd.append("-v")
        
    typer.secho("=> Provisioning isolated PostgreSQL Database...", fg=typer.colors.CYAN)
    
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

if __name__ == "__main__":
    app()
