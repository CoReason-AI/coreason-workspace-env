#!/usr/bin/env python3
import asyncio
import json
import sys

# DeepSeek Configuration
DEEPSEEK_API_KEY = "sk-42488d05b84d4055a8402511227de54a"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Inline import check to use standard library or openai SDK
try:
    from openai import OpenAI
except ImportError:
    print("Error: The 'openai' library is required to run this script.")
    print("Please install it using: pip install openai")
    sys.exit(1)

# Initialize DeepSeek client
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


async def send_rpc_request(writer, reader, method, params, req_id):
    """Sends JSON-RPC request to the MCP server and returns the response."""
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    writer.write(json.dumps(payload).encode("utf-8") + b"\n")
    await writer.drain()

    response_line = await reader.readline()
    if not response_line:
        raise ConnectionError("MCP server disconnected unexpectedly.")
    return json.loads(response_line.decode("utf-8"))


async def execute_mcp_pipeline(user_query: str):
    # 1. Start the MCP server only using the GitHub repository via uvx
    # We use a direct ZIP archive URL so that the playground container does not require a local 'git' executable to run.
    print("[System] Launching MCP Server via uvx (GitHub ZIP archive)...", file=sys.stderr)
    try:
        proc = await asyncio.create_subprocess_exec(
            "uvx",
            "--from",
            "sequential-thinking@https://github.com/arben-adm/mcp-sequential-thinking/archive/2fad3ee8ab1d0868b6c1afb5895bc336a10e5267.zip",
            "mcp-sequential-thinking",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=sys.stderr,  # Pipe stderr directly so we can diagnose connection issues
        )
        # Short sleep to check if it crashed immediately
        await asyncio.sleep(0.5)
        if proc.returncode is not None:
            raise RuntimeError(f"Process exited immediately with code {proc.returncode}")
    except Exception as e:
        print(f"Error: Failed to launch MCP server via uvx: {e}", file=sys.stderr)
        sys.exit(1)

    req_id = 1

    try:
        # 2. Perform MCP Handshake
        init_params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "deepseek-bridge", "version": "1.0"},
        }
        await send_rpc_request(proc.stdin, proc.stdout, "initialize", init_params, req_id)
        req_id += 1

        # Send initialized notification
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode("utf-8") + b"\n")
        await proc.stdin.drain()

        # Clear old session history
        await send_rpc_request(
            proc.stdin, proc.stdout, "tools/call", {"name": "clear_history", "arguments": {}}, req_id
        )
        req_id += 1

        # 3. Define the Tool declaration for DeepSeek
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "process_thought",
                    "description": "Add a sequential thought containing metadata for the current step.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "thought": {
                                "type": "string",
                                "description": "Detailed explanation of the current step's thinking",
                            },
                            "thought_number": {"type": "integer", "description": "The current step index"},
                            "total_thoughts": {"type": "integer", "description": "Total steps in this plan (always 6)"},
                            "next_thought_needed": {
                                "type": "boolean",
                                "description": "True if there are more steps remaining",
                            },
                            "stage": {
                                "type": "string",
                                "description": "The stage category: 'Problem Definition', 'Research', 'Analysis', 'Synthesis', or 'Conclusion'",
                            },
                            "tags": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["thought", "thought_number", "total_thoughts", "next_thought_needed", "stage"],
                    },
                },
            }
        ]

        # 4. Construct System Instruction
        system_instruction = (
            "You are a clinical NLP processing system. You must resolve the user query using exactly 6 steps:\n"
            "1. Read and Parse: Ingest the raw_unstructured_text.\n"
            "2. Orthographic Correction: Fix obvious spelling and typographical errors (e.g., 'mycardial infarcshun' -> 'myocardial infarction').\n"
            "3. Token-Level Domain Preservation: Identify all domain-specific biopharma vocabulary (drug names, symptom names, medical acronyms). Explicitly mark these tokens as immutable.\n"
            "4. Syntactic Restructuring: Fix run-on sentences, missing punctuation, and grammatical syntax errors to create clear, discrete sentences, working strictly around the immutable tokens.\n"
            "5. Semantic Preservation Check: Verify that no clinical facts, temporal relationships (e.g., 'prior to', 'after'), or negations (e.g., 'no evidence of') were altered or removed.\n"
            "6. Compile JSON: Output the cleaned string.\n\n"
            "Constraints:\n"
            "- Idempotency & Reversibility: Purely analytical and idempotent.\n"
            "- Transactional Safety: Does not mutate external state.\n\n"
            "🛑 Negative Constraints (Anti-Patterns & Epistemic Boundaries):\n"
            "- Refusal Predicate: If the input text is entirely unreadable, missing, or entirely outside the clinical domain, you MUST NOT hallucinate corrections. You MUST halt and return a 'NOT_FOUND' / 'INSUFFICIENT_DATA' failure state.\n"
            "- Anti-Citation Rule: Explicitly forbid casually citing human-facing textbooks, consulting literature, or non-peer-reviewed sources. Enforce native mathematical execution instead.\n"
            "- Provenance Rule: DO NOT return external or retrieved factual data without attaching strict provenance metadata (e.g., citation IDs, source JSON blocks) to allow downstream cryptographic verification.\n"
            "- Domain Vocabulary Collapse: Do not over-normalize medical jargon into layman's terms (e.g., do NOT change 'dyspnea' to 'shortness of breath'). The original clinical fidelity must be mathematically preserved at the token level.\n"
            "- Semantic Drift: You are strictly forbidden from changing the meaning of the text. If a sentence is ambiguous, preserve the ambiguity.\n"
            "- Abbreviation Expansion Risk: DO NOT guess medical abbreviations. If 'MI' could mean Myocardial Infarction or Mitral Incompetence, leave it as 'MI'.\n\n"
            "You must invoke the 'process_thought' tool for each of the 6 steps sequentially to log your progress.\n\n"
            "Your final output MUST be a JSON object conforming exactly to the following NormalizedTextData schema:\n"
            "{\n"
            '  "normalized_text": "string",\n'
            '  "changes_made": ["string (brief descriptions of syntax/spelling changes)"]\n'
            "}"
        )

        messages = [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_query}]

        print("[DeepSeek Interface] Sending query to DeepSeek...")

        # 5. Handle LLM Tool Calling loop
        while True:
            response = client.chat.completions.create(
                model="deepseek-chat", messages=messages, tools=tools, tool_choice="auto"
            )

            response_message = response.choices[0].message
            messages.append(response_message)

            # Check if DeepSeek wants to call a tool
            tool_calls = response_message.tool_calls
            if not tool_calls:
                # No more tool calls, we're done
                break

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                print(f" -> DeepSeek invoked Step {args.get('thought_number')}/6: [{args.get('stage')}]")

                # Execute tool call on the local MCP server
                mcp_resp = await send_rpc_request(
                    proc.stdin, proc.stdout, "tools/call", {"name": tool_name, "arguments": args}, req_id
                )
                req_id += 1

                # Extract the result payload from the MCP tool output
                content_list = mcp_resp.get("result", {}).get("content", [])
                mcp_output_text = content_list[0].get("text", "Success") if content_list else "Success"

                # Print proof of MCP Server validation
                try:
                    parsed_res = json.loads(mcp_output_text)
                    progress = parsed_res.get("thoughtAnalysis", {}).get("analysis", {}).get("progress", 0.0)
                    history_len = (
                        parsed_res.get("thoughtAnalysis", {}).get("context", {}).get("thoughtHistoryLength", 0)
                    )
                    print(
                        f"    [MCP Server Verification] Success! Thought logged. Progress: {progress}%, History Length: {history_len}"
                    )
                except Exception:
                    pass

                # Feed the tool output back to the conversation history
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "name": tool_name, "content": mcp_output_text}
                )

        # 6. # Parse and print only the text string to stdout
        try:
            res_json = json.loads(response_message.content)
            print(res_json.get("normalized_text", response_message.content))
        except Exception:
            print(response_message.content)

    finally:
        # Gracefully shut down the local MCP server
        if proc.returncode is None:
            proc.terminate()
            await proc.wait()


if __name__ == "__main__":
    query = None

    # 1. Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if arg.startswith("{"):
            try:
                data = json.loads(arg)
                query = data.get("text") or data.get("query") or arg
            except Exception:
                query = arg
        else:
            query = " ".join(sys.argv[1:])

    # 2. Parse stdin if CLI arguments were not provided
    elif not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                if stdin_data.startswith("{"):
                    try:
                        data = json.loads(stdin_data)
                        query = data.get("text") or data.get("query") or stdin_data
                    except Exception:
                        query = stdin_data
                else:
                    query = stdin_data
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to read from stdin: {e}\n")


    asyncio.run(execute_mcp_pipeline(query))
