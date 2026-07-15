import asyncio
import json
import logging
import re
import sys

try:
    import websockets
except ImportError:
    websockets = None

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.patch_stdout import patch_stdout
except ImportError:
    PromptSession = None
    patch_stdout = None

logger = logging.getLogger(__name__)

def is_valid_uuid7(val: str) -> bool:
    """Validate that the given string is a valid UUIDv7."""
    pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-7[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    return bool(re.match(pattern, val))

async def handle_user_input(websocket, session):
    """Handle user input asynchronously using prompt_toolkit."""
    while True:
        try:
            with patch_stdout():
                # session.prompt_async is an awaitable that prompts the user
                cmd = await session.prompt_async("coreason> ")
            
            cmd = cmd.strip()
            if not cmd:
                continue

            if cmd.startswith("rewind"):
                parts = cmd.split(" ")
                if len(parts) == 2:
                    checkpoint_id = parts[1]
                    if not is_valid_uuid7(checkpoint_id):
                        print(f"[Error] '{checkpoint_id}' is not a valid UUIDv7.")
                        continue
                    
                    payload = {"action": "rewind", "checkpoint_id": checkpoint_id}
                    await websocket.send(json.dumps(payload))
                    print(f"\n[CLI] Sent rewind command for checkpoint: {checkpoint_id}")
                else:
                    print("[CLI] Error: rewind requires a checkpoint_id (e.g., 'rewind <uuid7>')")
            elif cmd in ("exit", "quit"):
                print("Exiting...")
                sys.exit(0)
            else:
                print(f"[CLI] Unknown command: {cmd}. Available commands: rewind <checkpoint_id>, exit")

        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            sys.exit(0)

async def watch_state_stream(session_id: str, host: str, pretty: bool = True):
    if websockets is None or patch_stdout is None:
        print("Missing required dependencies for state streaming.")
        print("Please ensure websockets and prompt_toolkit are installed.")
        sys.exit(1)

    uri = f"{host}/ws/state/{session_id}"
    print(f"Connecting to {uri} ...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Listening for live state sync updates.")
            print("Type 'rewind <checkpoint_id>' at any time to travel back in time.\n")
            
            prompt_session = PromptSession()
            # Start the background task to listen for user input
            input_task = asyncio.create_task(handle_user_input(websocket, prompt_session))
            
            while True:
                message = await websocket.recv()
                try:
                    data = json.loads(message)
                    with patch_stdout():
                        print("\n\033[94m--- State Update ---\033[0m")
                        if pretty:
                            print(json.dumps(data, indent=2))
                        else:
                            print(json.dumps(data))
                        print("\033[94m--------------------\033[0m")
                except json.JSONDecodeError:
                    with patch_stdout():
                        print(f"\n\033[93mRaw message:\033[0m {message}")
                    
    except websockets.exceptions.ConnectionClosed:
        print("\nConnection closed by the server.")
    except Exception as e:
        print(f"\nConnection error: {e}")
        print("Ensure the API server is running.")
