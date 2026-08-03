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
from metatrader_client.market.get_symbols import get_symbols

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

# Connect and get symbols
client = MT5Client(config)
try:
    client.connect()
    print("✓ Connected to MetaTrader 5")
    print()
    
    symbols = get_symbols(client._connection, fields=["path"])
    print(f"Found {len(symbols)} symbols:")
    print()
    for i, symbol in enumerate(symbols, 1):
        print(f"  {i}. {symbol}")
    
    print(set(symbol.split("\\")[0] for symbol in symbols))  # Print the last part of each symbol's path
    
    
finally:
    client.disconnect()
    print()
    print("✓ Disconnected")
