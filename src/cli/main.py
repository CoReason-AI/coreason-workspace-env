"""
CoReason Platform CLI — full parity with the REST API.
All commands delegate to src.core.services (same shared business logic).

Usage:
    python -m src.cli.main <command> [options]
    python -m src.cli.main --help

Output:
    Structured JSON by default. Use --pretty for human-readable formatting.
"""
import argparse
import asyncio
import json
import sys
import logging

logger = logging.getLogger(__name__)


def _output(data: dict, pretty: bool = False):
    """Print structured JSON output."""
    if pretty:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(json.dumps(data, default=str))


# ──────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────
async def cmd_health(args):
    from src.core.services import health_service
    result = await health_service.check()
    _output(result, args.pretty)


# ──────────────────────────────────────────────
# Projects
# ──────────────────────────────────────────────
async def cmd_projects_list(args):
    from src.core.services import project_service
    projects = await project_service.list_projects()
    _output({"projects": projects}, args.pretty)


async def cmd_projects_create(args):
    import uuid
    from src.core.services import project_service
    config = json.loads(args.config) if args.config else None
    project = await project_service.create_project(
        project_id=str(uuid.uuid4()),
        name=args.name,
        description=args.description or "",
        config=config,
    )
    _output({"status": "created", "project": project}, args.pretty)


async def cmd_projects_get(args):
    from src.core.services import project_service
    project = await project_service.get_project(args.id)
    if not project:
        _output({"status": "error", "detail": f"Project '{args.id}' not found"}, args.pretty)
        sys.exit(1)
    _output({"project": project}, args.pretty)


async def cmd_projects_delete(args):
    from src.core.services import project_service
    deleted = await project_service.delete_project(args.id)
    if not deleted:
        _output({"status": "error", "detail": f"Project '{args.id}' not found"}, args.pretty)
        sys.exit(1)
    _output({"status": "deleted", "project_id": args.id}, args.pretty)


async def cmd_projects_export(args):
    from src.core.services import project_service
    result = await project_service.export_project(args.project, args.out)
    _output(result, args.pretty)


# ──────────────────────────────────────────────
# Agents
# ──────────────────────────────────────────────
async def cmd_agents_list(args):
    from src.core.services import agent_service
    agents = agent_service.list_agents()
    _output({"agents": agents}, args.pretty)


async def cmd_agents_get(args):
    from src.core.services import agent_service
    agent = agent_service.get_agent(args.name)
    if not agent:
        _output({"status": "error", "detail": f"Agent '{args.name}' not found"}, args.pretty)
        sys.exit(1)
    _output({"agent": agent}, args.pretty)


async def cmd_agents_execute(args):
    from src.core.services import agent_service
    payload = json.loads(args.payload) if args.payload else {}
    result = await agent_service.execute_agent(
        agent_name=args.name,
        payload=payload,
        user_id=args.user_id,
        tenant_id=args.tenant_id,
    )
    _output(result, args.pretty)


# ──────────────────────────────────────────────
# MCP
# ──────────────────────────────────────────────
async def cmd_mcp_list_servers(args):
    from src.core.services import mcp_tool_service
    servers = mcp_tool_service.list_servers()
    _output({"servers": servers}, args.pretty)


async def cmd_mcp_execute_tool(args):
    from src.core.services import mcp_tool_service
    arguments = json.loads(args.args) if args.args else {}
    result = await mcp_tool_service.execute_tool(
        server_name=args.server,
        tool_name=args.tool,
        arguments=arguments,
        session_id=args.session_id or "cli-session",
    )
    _output(result, args.pretty)


# ──────────────────────────────────────────────
# Docs
# ──────────────────────────────────────────────
async def cmd_docs_generate(args):
    from src.core.services import docs_service
    pages_data = json.loads(args.pages) if args.pages else []
    result = docs_service.generate_mkdocs(
        workspace_path=args.workspace,
        site_name=args.site_name,
        pages=pages_data,
    )
    _output(result, args.pretty)


# ──────────────────────────────────────────────
# Main parser
# ──────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coreason",
        description="CoReason Platform CLI — full parity with REST API",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    subparsers = parser.add_subparsers(dest="command")

    # health
    subparsers.add_parser("health", help="Check platform health (Postgres, Redis)")

    # projects
    projects_parser = subparsers.add_parser("projects", help="Manage projects")
    projects_sub = projects_parser.add_subparsers(dest="subcommand")

    projects_sub.add_parser("list", help="List all projects")

    create_p = projects_sub.add_parser("create", help="Create a new project")
    create_p.add_argument("--name", required=True, help="Project name")
    create_p.add_argument("--description", default="", help="Project description")
    create_p.add_argument("--config", default=None, help="JSON config string")

    get_p = projects_sub.add_parser("get", help="Get a project by ID")
    get_p.add_argument("--id", required=True, help="Project ID")

    del_p = projects_sub.add_parser("delete", help="Delete a project by ID")
    del_p.add_argument("--id", required=True, help="Project ID")

    export_p = projects_sub.add_parser("export", help="Export a project for air-gap transfer")
    export_p.add_argument("--project", required=True, help="Path to the project directory")
    export_p.add_argument("--out", required=True, help="Output directory for the export bundle")

    # agents
    agents_parser = subparsers.add_parser("agents", help="Manage agents")
    agents_sub = agents_parser.add_subparsers(dest="subcommand")

    agents_sub.add_parser("list", help="List all agents")

    get_a = agents_sub.add_parser("get", help="Get a specific agent")
    get_a.add_argument("--name", required=True, help="Agent name")

    exec_a = agents_sub.add_parser("execute", help="Execute an agent workflow")
    exec_a.add_argument("--name", required=True, help="Agent name")
    exec_a.add_argument("--user-id", required=True, help="User ID")
    exec_a.add_argument("--tenant-id", required=True, help="Tenant ID")
    exec_a.add_argument("--payload", default=None, help="JSON payload string")

    # mcp
    mcp_parser = subparsers.add_parser("mcp", help="Manage MCP servers and tools")
    mcp_sub = mcp_parser.add_subparsers(dest="subcommand")

    mcp_sub.add_parser("list-servers", help="List connected MCP servers")

    exec_m = mcp_sub.add_parser("execute-tool", help="Execute an MCP tool")
    exec_m.add_argument("--server", required=True, help="MCP server name")
    exec_m.add_argument("--tool", required=True, help="MCP tool name")
    exec_m.add_argument("--args", default=None, help="JSON arguments string")
    exec_m.add_argument("--session-id", default=None, help="Session ID")

    # docs
    docs_parser = subparsers.add_parser("docs", help="Documentation generation")
    docs_sub = docs_parser.add_subparsers(dest="subcommand")

    gen_d = docs_sub.add_parser("generate", help="Generate MkDocs scaffold")
    gen_d.add_argument("--workspace", required=True, help="Absolute workspace path")
    gen_d.add_argument("--site-name", required=True, help="MkDocs site name")
    gen_d.add_argument("--pages", required=True, help="JSON array of page objects")

    return parser


# Command dispatch table
_DISPATCH = {
    ("health", None): cmd_health,
    ("projects", "list"): cmd_projects_list,
    ("projects", "create"): cmd_projects_create,
    ("projects", "get"): cmd_projects_get,
    ("projects", "delete"): cmd_projects_delete,
    ("projects", "export"): cmd_projects_export,
    ("agents", "list"): cmd_agents_list,
    ("agents", "get"): cmd_agents_get,
    ("agents", "execute"): cmd_agents_execute,
    ("mcp", "list-servers"): cmd_mcp_list_servers,
    ("mcp", "execute-tool"): cmd_mcp_execute_tool,
    ("docs", "generate"): cmd_docs_generate,
}


def main():
    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(level=logging.WARNING)

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    key = (args.command, getattr(args, "subcommand", None))
    handler = _DISPATCH.get(key)

    if not handler:
        parser.print_help()
        sys.exit(1)

    asyncio.run(handler(args))


if __name__ == "__main__":
    main()
