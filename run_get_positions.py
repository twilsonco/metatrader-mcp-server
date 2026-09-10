import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from metatrader_client import MT5Client
from metatrader_client.order.get_all_positions import get_all_positions

# Get credentials from environment
config = {
    "login": int(os.getenv("LOGIN")),
    "password": os.getenv("PASSWORD"),
    "server": os.getenv("SERVER"),
    "path": os.getenv("MT5_PATH"),
    "debug": os.getenv("MT5_DEBUG", "false").lower() in ("true", "1", "yes"),
}

print(f"Connecting to MT5 with config:")
print(f"  Login: {config['login']}")
print(f"  Server: {config['server']}")
print(f"  Path: {config['path']}")
print()

# Connect and get all positions
client = MT5Client(config)
try:
    client.connect()
    print("✓ Connected to MetaTrader 5")
    print()

    df = get_all_positions(client._connection)

    if df is None or len(df) == 0:
        print("No open positions found.")
    else:
        print(f"Found {len(df)} open position(s):")
        print()
        # Same output format as the MCP tool (CSV)
        print(df.to_csv() if hasattr(df, 'to_csv') else str(df))

        # Quick summary report
        if 'profit' in df.columns:
            total_profit = float(df['profit'].sum())
            print("Summary:")
            print(f"  Total positions: {len(df)}")
            print(f"  Total profit:    {total_profit:.2f}")
            if 'symbol' in df.columns:
                print(f"  Symbols:         {sorted(set(df['symbol']))}")

finally:
    client.disconnect()
    print()
    print("✓ Disconnected")
