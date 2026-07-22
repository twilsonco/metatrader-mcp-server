import click
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env BEFORE click parses options, so env vars are available as defaults.
# Search order: cwd, then walk up from this file to find the project root
# (directory containing pyproject.toml), then fall back to src-relative paths.
_here = Path(__file__).resolve().parent


def _find_project_root(start: Path) -> Path:
    """Walk up from `start` until a pyproject.toml is found, else return start's parent."""
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return start.parent


_project_root = _find_project_root(_here)
_search_paths = [Path.cwd(), _project_root / ".env", _here.parent / ".env", _here / ".env"]
for _p in _search_paths:
    if _p.is_file():
        load_dotenv(_p)
        break

from metatrader_mcp.server import mcp
from metatrader_mcp.utils import resolve_transport_config, run_mcp, configure_logging

@click.command()
@click.option("--login", default=os.environ.get("LOGIN"), type=int, help="MT5 login ID")
@click.option("--password", default=os.environ.get("PASSWORD"), help="MT5 password")
@click.option("--server", default=os.environ.get("SERVER"), help="MT5 server name")
@click.option("--path", default=None, help="Path to MT5 terminal executable (optional, auto-detected if not provided)")
@click.option("--transport", default=None, type=click.Choice(["sse", "stdio", "streamable-http"], case_sensitive=False), help="MCP transport type (default: sse, env: MCP_TRANSPORT)")
@click.option("--host", default=None, help="Host to bind for SSE/HTTP transport (default: 0.0.0.0, env: MCP_HOST)")
@click.option("--port", default=None, type=int, help="Port to bind for SSE/HTTP transport (default: 8080, env: MCP_PORT)")
def main(login, password, server, path, transport, host, port):
    """Launch the MetaTrader MCP server."""
    # override env vars if provided via CLI (only set non-None values)
    if login is not None:
        os.environ["LOGIN"] = str(login)
    if password is not None:
        os.environ["PASSWORD"] = password
    if server is not None:
        os.environ["SERVER"] = server
    if path is not None:
        os.environ["MT5_PATH"] = path

    transport, host, port = resolve_transport_config(transport, host, port)
    configure_logging()
    run_mcp(mcp, transport, host, port)

if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
