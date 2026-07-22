import logging
import os
import sys
from typing import Any, Optional, Union
from metatrader_client import client

# Module-level flag so configure_logging() is idempotent across multiple init() calls
_LOGGING_CONFIGURED = False


_MT5_LOGGER_NAMES = ("MT5Connection", "MT5Account", "MT5History", "MT5Market", "MT5Order")


def _resolve_log_level(level: Optional[int]) -> int:
	"""Resolve the effective log level from an explicit arg or the LOG_LEVEL env var."""
	if level is not None:
		return level
	level_name = os.getenv("LOG_LEVEL", "INFO").upper()
	return getattr(logging, level_name, logging.INFO)


def configure_logging(level: Optional[int] = None) -> None:
	"""Configure logging for the MT5 client.

	Reads ``LOG_LEVEL`` from the environment when ``level`` is not provided
	(default: ``INFO``). Applies the level to every ``MT5*`` logger so that
	connection, account, history, market, and order modules all honor the
	same verbosity. Sets up a stream handler on the ``MT5Connection`` logger
	so connection retries and success messages become visible. Idempotent —
	safe to call multiple times. Callers can re-invoke with a different level
	to adjust verbosity.
	"""
	global _LOGGING_CONFIGURED
	level = _resolve_log_level(level)
	for name in _MT5_LOGGER_NAMES:
		logging.getLogger(name).setLevel(level)
	if _LOGGING_CONFIGURED:
		return
	handler = logging.StreamHandler()
	handler.setFormatter(
		logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
	)
	logging.getLogger("MT5Connection").addHandler(handler)
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
	"""Initialize MT5Client and log connection status."""
	configure_logging()
	logger = logging.getLogger()

	if not (login and password and server):
		return None

	config = {
		"login": int(login),
		"password": password,
		"server": server,
	}
	if path:
		config["path"] = path
	
	# Honor MT5_DEBUG env var
	if os.getenv("MT5_DEBUG", "").lower() in ("1", "true", "yes"):
		config["debug"] = True

	mt5_client = client.MT5Client(config=config)
	
	# Re-apply logging after MT5Client init
	configure_logging()
	
	try:
		if not mt5_client.connect():
			msg = "Failed to connect to MT5 terminal"
			print(f"[metatrader-mcp] {msg}", file=sys.stderr, flush=True)
			logger.error(msg)
			return None
	except Exception as e:
		msg = f"Failed to connect to MT5 terminal: {e}"
		print(f"[metatrader-mcp] {msg}", file=sys.stderr, flush=True)
		logger.error(msg)
		return None

	_print_confirmation(mt5_client, login, server)
	return mt5_client
	
def get_client(ctx: Any) -> Optional[client.MT5Client]:
	return ctx.request_context.lifespan_context.client