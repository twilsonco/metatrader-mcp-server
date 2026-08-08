from datetime import timedelta, timezone, datetime
from typing import Optional
import pandas as pd
import MetaTrader5 as mt5
from ..types import Timeframe
from ..exceptions import SymbolNotFoundError, InvalidTimeframeError, MarketDataError
from .get_symbols import get_symbols
from .fetch_with_sync import _fetch_with_sync

def get_candles_latest(connection, symbol_name: str, timeframe: str, count: int = 100) -> pd.DataFrame:
    if not get_symbols(connection, symbol_name):
        raise SymbolNotFoundError(f"Symbol '{symbol_name}' not found")
    tf = Timeframe.get(timeframe)
    if tf is None:
        raise InvalidTimeframeError(f"Invalid timeframe: '{timeframe}'")
    # Kick the terminal by requesting a date far enough in the past to trigger sync
    kick_date = datetime.now(timezone.utc) - timedelta(days=365)
    
    candles = _fetch_with_sync(
        fetch_func=lambda: mt5.copy_rates_from_pos(symbol_name, tf, 0, count),
        symbol_name=symbol_name,
        timeframe=tf,
        kick_date=kick_date,
        expected_count=count
    )
    if candles is None or len(candles) == 0:
        raise MarketDataError(f"Failed to retrieve candle data for symbol '{symbol_name}' with timeframe '{timeframe}'")
    df = pd.DataFrame(candles)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df = df.sort_values('time', ascending=False)
    return df
