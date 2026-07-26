# 🎯 get_next_open_position

**Signature:**
```python
def get_next_open_position(connection, *, staleness_seconds: int = 600, cache_path: Optional[str] = None) -> Dict[str, Any]
```

## What does it do? 🧐
Selects the open position reviewed least recently for AI agent review. Fetches all open positions, filters out positions whose underlying market appears closed (based on tick staleness), then picks the position with the oldest (or missing) review timestamp from a persistent JSON cache. The cache is updated with the current UTC timestamp for the selected ticket so subsequent calls rotate through positions.

This is designed for AI agents that periodically review open trades (e.g. via cron jobs) and need to ensure each position gets attention without reviewing the same one twice in a row.

## Parameters
- **connection**: MetaTrader 5 connection object
- **staleness_seconds**: (Keyword-only, optional) Maximum age in seconds of the last tick before a market is considered closed (default: 600 = 10 minutes)
- **cache_path**: (Keyword-only, optional) Override for the cache file path. Defaults to the `POSITION_REVIEW_CACHE_PATH` environment variable, falling back to `~/.metatrader-mcp/position_review_cache.json`

## Returns
A dictionary with the standard `{"error": bool, "message": str, "data": ...}` envelope:
- **error**: `False` on success
- **message**: Human-readable status (`"Selected position for review"`, `"No open positions"`, or `"No positions on currently open markets"`)
- **data**: Either `None` (when no positions are available) or a formatted position payload with:
  - `ticket` (int): Position ticket ID
  - `symbol` (str): Asset symbol
  - `type` (str): `"BUY"` or `"SELL"`
  - `volume` (float): Lot size
  - `price_open` (float): Entry price
  - `sl` (float): Current stop-loss level
  - `tp` (float): Current take-profit level
  - `price_current` (float): Current market price
  - `profit` (float): Floating profit in account currency
  - `time_setup` (str): Entry time formatted as `"YYYY-MM-DD HH:MM:SS UTC"`

## Cache Behavior 📦
The cache file maps position tickets (as strings) to UTC Unix timestamps of their last review. Tickets not present in the cache are treated as having a timestamp of `0` (highest priority). The cache is loaded at the start of each call and written back after a position is selected.

The cache survives server restarts, so an AI agent running on a cron schedule won't re-review the same position after a process restart.

**Self-maintaining pruning**: On every call, entries for positions that are no longer open are purged from the cache. This is safe because MetaTrader 5 ticket IDs are never reused — a closed position's ticket is permanently retired. The cache therefore stays bounded by the number of currently open positions and never accumulates stale entries.

## Market Filtering 🕐
A position is excluded when its symbol's last tick is older than `staleness_seconds`. This avoids reviewing positions on closed markets (weekends, holidays, overnight gaps) where the floating P&L is meaningless.

## Fun Fact 🤖
Pair this with a cron-driven AI agent and you've got a tireless trading copilot that never forgets which positions it has already reviewed!