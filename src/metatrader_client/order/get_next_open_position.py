"""
Round-robin selection of the next open position for AI review.

This module implements a position picker that returns the open position whose
market is currently active (based on tick staleness) and which has the oldest
(or missing) review timestamp in a persistent JSON cache. The cache is updated
with the current UTC timestamp for the selected ticket so subsequent calls
rotate through positions.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import MetaTrader5 as mt5

from ..types import OrderType


def _resolve_cache_path(cache_path: Optional[str]) -> Path:
    """Resolve the cache file path from argument, env var, or default.

    Args:
        cache_path: Optional explicit override.

    Returns:
        Path: Absolute path to the cache file. Parent directory is created if missing.
    """
    raw = cache_path or os.getenv("POSITION_REVIEW_CACHE_PATH")
    if raw:
        path = Path(raw).expanduser()
    else:
        path = Path.home() / ".metatrader-mcp" / "position_review_cache.json"

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_cache(path: Path) -> Dict[str, float]:
    """Load the review cache from disk.

    Args:
        path: Path to the JSON cache file.

    Returns:
        dict: Mapping of ticket (str) -> last reviewed UTC timestamp (float).
              Returns an empty dict if the file is missing or malformed.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k): float(v) for k, v in data.items()}
            return {}
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        return {}


def _save_cache(path: Path, cache: Dict[str, float]) -> None:
    """Persist the review cache to disk.

    Args:
        path: Path to the JSON cache file.
        cache: Mapping of ticket (str) -> last reviewed UTC timestamp (float).
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, sort_keys=True)


def _is_market_open(symbol: str, staleness_seconds: int) -> bool:
    """Check whether a symbol's market is currently active.

    Uses the staleness of the last tick as a proxy for market state. If the last
    tick is older than ``staleness_seconds``, the market is assumed closed.

    Args:
        symbol: The symbol name to check.
        staleness_seconds: Maximum age (in seconds) of the last tick before the
            market is considered closed.

    Returns:
        bool: True if the market appears open, False otherwise.
    """
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return False

    current_utc = datetime.now(timezone.utc).timestamp()
    if (current_utc - tick.time) > staleness_seconds:
        return False
    return True


def _format_position(pos: Any) -> Dict[str, Any]:
    """Format an MT5 position named tuple into a structured dictionary.

    Args:
        pos: MetaTrader 5 position named tuple.

    Returns:
        dict: Position payload suitable for AI agent consumption.
    """
    return {
        "ticket": pos.ticket,
        "symbol": pos.symbol,
        "type": OrderType.to_string(pos.type),
        "volume": pos.volume,
        "price_open": pos.price_open,
        "sl": pos.sl,
        "tp": pos.tp,
        "price_current": pos.price_current,
        "profit": pos.profit,
        "time_setup": datetime.fromtimestamp(pos.time, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        ),
    }


def get_next_open_position(
    connection,
    *,
    staleness_seconds: int = 600,
    cache_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Select the open position reviewed least recently for AI review.

    Fetches all open positions, filters out positions whose underlying market
    appears closed (based on tick staleness), then picks the position with the
    oldest (or missing) review timestamp from the persistent cache. The cache
    is updated with the current UTC timestamp for the selected ticket so
    subsequent calls rotate through positions.

    Args:
        connection: MetaTrader 5 connection object.
        staleness_seconds: Maximum age (in seconds) of the last tick before a
            market is considered closed (default: 600).
        cache_path: Optional override for the cache file path. Defaults to the
            ``POSITION_REVIEW_CACHE_PATH`` environment variable, falling back to
            ``~/.metatrader-mcp/position_review_cache.json``.

    Returns:
        dict: ``{"error": bool, "message": str, "data": Optional[Dict[str, Any]]}``
        where ``data`` is either a formatted position payload or ``None`` when
        no positions are available.
    """
    # Resolve and load cache
    cache_file = _resolve_cache_path(cache_path)
    cache = _load_cache(cache_file)

    # Fetch all open positions
    positions = mt5.positions_get()
    if positions is None or len(positions) == 0:
        return {
            "error": False,
            "message": "No open positions",
            "data": None,
        }

    # Filter to positions whose market appears open
    valid_positions = []
    for pos in positions:
        if _is_market_open(pos.symbol, staleness_seconds):
            last_checked = cache.get(str(pos.ticket), 0)
            valid_positions.append((last_checked, pos))

    if not valid_positions:
        return {
            "error": False,
            "message": "No positions on currently open markets",
            "data": None,
        }

    # Sort ascending by last-reviewed timestamp (oldest first)
    valid_positions.sort(key=lambda item: item[0])
    selected_pos = valid_positions[0][1]

    # Update cache and persist
    cache[str(selected_pos.ticket)] = datetime.now(timezone.utc).timestamp()
    _save_cache(cache_file, cache)

    return {
        "error": False,
        "message": "Selected position for review",
        "data": _format_position(selected_pos),
    }