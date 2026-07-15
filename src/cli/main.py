import typer
import asyncio
from typing import Optional
import uuid

app = typer.Typer()

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

if __name__ == "__main__":
    app()
