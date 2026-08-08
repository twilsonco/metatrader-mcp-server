#!/usr/bin/env python3
"""
Test script to fetch 1 month of latest 1H candles for EURUSD
using the MCP server's get_candles_latest tool.

This helps verify that the _fetch_with_sync function is working correctly.

Usage:
    1. Make sure the MCP server is running (uv run metatrader-mcp-server)
    2. Run this script: python test_candles_mcp_client.py
"""

import asyncio
import sys
from io import StringIO

import pandas as pd


async def test_via_sse():
    """Try to connect via SSE transport."""
    try:
        from mcp.client.sse import sse_client
        from mcp.client.session import ClientSession
        
        print("Attempting to connect via SSE transport...")
        url = "http://localhost:8080/sse"
        
        async with sse_client(url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("[OK] Connected to MCP server via SSE\n")
                
                return await _call_tool(session)
    
    except Exception as e:
        print(f"[ERROR] SSE transport failed: {type(e).__name__}: {e}\n")
        return None


async def test_via_stdio():
    """Connect via stdio transport using subprocess."""
    try:
        from mcp.client.stdio import stdio_client, StdioServerParameters
        from mcp.client.session import ClientSession
        
        print("Attempting to connect via stdio transport...")
        
        # Start the MCP server in stdio mode as a subprocess
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "metatrader_mcp.cli", "--transport", "stdio"],
        )
        
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("[OK] Connected to MCP server via stdio\n")
                
                return await _call_tool(session)
    
    except Exception as e:
        print(f"[ERROR] Stdio transport failed: {type(e).__name__}: {e}\n")
        import traceback
        traceback.print_exc()
        return None


async def _call_tool(session):
    """Call the get_candles_latest tool via the session."""
    try:
        print("Calling get_candles_latest(symbol_name='EURUSD', timeframe='H1', count=720)...\n")
        result = await session.call_tool(
            "get_candles_latest",
            {
                "symbol_name": "EURUSD",
                "timeframe": "H1",
                "count": 720,
            }
        )
        
        if result.isError:
            print(f"[ERROR] Tool returned error: {result.content}")
            return None
        
        # The result should be CSV text
        csv_content = result.content[0].text
        df = pd.read_csv(StringIO(csv_content))
        return df
    
    except Exception as e:
        print(f"[ERROR] Failed to call tool: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main entry point."""
    SYMBOL = "EURUSD"
    TIMEFRAME = "H1"
    COUNT = 720
    
    print(f"Test: Fetch {COUNT} {TIMEFRAME} candles for {SYMBOL}\n")
    print("=" * 70)
    
    # Try SSE first
    df = await test_via_sse()
    
    # If SSE fails, try stdio
    if df is None:
        df = await test_via_stdio()
    
    if df is None:
        print("\n[ERROR] Failed to connect to MCP server via both SSE and stdio transports")
        print("[INFO] Make sure the server is running: uv run metatrader-mcp-server")
        return False
    
    print(f"\n[OK] Successfully fetched {len(df)} candles\n")
    
    # Display summary statistics
    print("=" * 70)
    print("CANDLE DATA SUMMARY")
    print("=" * 70)
    print(f"Total candles: {len(df)}")
    
    # Handle different column names
    close_col = None
    for col in ['close', 'c']:
        if col in df.columns:
            close_col = col
            break
    
    if close_col:
        print(f"\nFirst 5 candles (oldest):")
        print(df.head(5).to_string(index=False))
        print(f"\nLast 5 candles (most recent):")
        print(df.tail(5).to_string(index=False))
        
        # Statistics
        print(f"\n" + "=" * 70)
        print("PRICE STATISTICS")
        print("=" * 70)
        print(f"Highest close: {df[close_col].max()}")
        print(f"Lowest close:  {df[close_col].min()}")
        print(f"Average close: {df[close_col].mean():.5f}")
        
        try:
            print(f"Std deviation: {df[close_col].std():.5f}")
        except:
            pass
    
    # Volume info if available
    for vol_col in ['tick_volume', 'volume', 'v']:
        if vol_col in df.columns:
            print(f"\nTotal {vol_col}: {df[vol_col].sum():.0f}")
            print(f"Average {vol_col}: {df[vol_col].mean():.0f}")
            break
    
    # Time range
    time_col = None
    for col in ['time', 't']:
        if col in df.columns:
            time_col = col
            break
    
    if time_col:
        print(f"\nTime range: {df[time_col].iloc[-1]} to {df[time_col].iloc[0]}")
    
    print("=" * 70)
    print("\n[OK] Test completed successfully!")
    print("[INFO] The _fetch_with_sync function appears to be working correctly.")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


