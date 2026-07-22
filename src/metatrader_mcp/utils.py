import logging
import os
import sys
from typing import Any, Optional, Union
from metatrader_client import client

# Module-level flag so configure_logging() is idempotent across multiple init() calls
_LOGGING_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
	"""Configure logging for the MT5 client.

	Sets up a stream handler on the 'MT5Connection' logger so connection
	retries and success messages become visible. Idempotent — safe to call
	multiple times. Callers can re-invoke with a different level to adjust
	verbosity.
	"""
	global _LOGGING_CONFIGURED
	logger = logging.getLogger("MT5Connection")
	logger.setLevel(level)
	if _LOGGING_CONFIGURED:
		return
	handler = logging.StreamHandler()
	handler.setFormatter(
		logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
	)
	logger.addHandler(handler)
	_LOGGING_CONFIGURED = True


def resolve_transport_config(transport=None, host=None, port=None):
	"""Resolve transport config: CLI flag > env var > default."""
	transport = transport or os.getenv("MCP_TRANSPORT", "sse")
	host = host or os.getenv("MCP_HOST", "0.0.0.0")
	port = port if port is not None else int(os.getenv("MCP_PORT", "8080"))
	return transport, host, port


def run_mcp(mcp, transport, host, port):
	"""Run the MCP server with the resolved transport config."""
	if transport == "stdio":
		mcp.run(transport="stdio")
	else:
		mcp.settings.host = host
		mcp.settings.port = port
		# Disable DNS rebinding protection when binding to all interfaces,
		# since the server is intended to be accessed remotely.
		if host == "0.0.0.0":
			try:
				mcp.settings.transport_security.enable_dns_rebinding_protection = False
			except AttributeError:
				pass  # transport_security not available in this version
		mcp.run(transport=transport)

def _print_confirmation(mt5_client, login, server):
	"""Print a one-line connection confirmation to stderr.

	Includes whatever info is available — account stats if logged in,
	terminal version if the terminal is initialized. Failures are
	swallowed so a missing account doesn't prevent the confirmation.
	"""
	parts = [f"login={login}", f"server={server}"]
	try:
		stats = mt5_client.account.get_trade_statistics() or {}
		if stats.get("balance") is not None:
			parts.append(f"balance={stats['balance']}")
		if stats.get("equity") is not None:
			parts.append(f"equity={stats['equity']}")
		if stats.get("currency"):
			parts.append(f"currency={stats['currency']}")
	except Exception:
		pass
	try:
		version = mt5_client.get_version()
		if version:
			parts.append(f"terminal=v{version[0]}.{version[1]}.{version[2]}.{version[3]}")
	except Exception:
		pass
	print(f"[metatrader-mcp] Connected to MT5 — {' '.join(parts)}", file=sys.stderr, flush=True)


def init(
	login: Optional[Union[str, int]],
	password: Optional[str],
	server: Optional[str],
	path: Optional[str] = None,
) -> Optional[client.MT5Client]:
	"""
	Initialize MT5Client and print a connection confirmation.

	Args:
		login (Optional[Union[str, int]]): Login ID
		password (Optional[str]): Password
		server (Optional[str]): Server name
		path (Optional[str]): Path to MT5 terminal executable (default: None for auto-detect)

	Returns:
		Optional[client.MT5Client]: MT5Client instance on success, None if credentials are missing or connection fails.
	"""
	configure_logging()

	if not (login and password and server):
		return None

	config = {
		"login": int(login),
		"password": password,
		"server": server,
	}
	if path:
		config["path"] = path

	mt5_client = client.MT5Client(config=config)
	try:
		if not mt5_client.connect():
			print("[metatrader-mcp] Failed to connect to MT5 terminal", file=sys.stderr, flush=True)
			return None
	except Exception as e:
		print(f"[metatrader-mcp] Failed to connect to MT5 terminal: {e}", file=sys.stderr, flush=True)
		return None

	_print_confirmation(mt5_client, login, server)
	return mt5_client
	
def get_client(ctx: Any) -> Optional[client.MT5Client]:
	return ctx.request_context.lifespan_context.client