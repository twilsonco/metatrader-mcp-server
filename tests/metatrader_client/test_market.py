import os
import pytest
from unittest.mock import MagicMock
import pandas as pd

def _make_candles(count):
    """Build a realistic candles DataFrame with `count` rows."""
    return pd.DataFrame({
        "time": [pd.Timestamp("2024-01-01") + pd.to_timedelta(i, unit="min")
                 for i in range(count)],
        "open": 1.1000,
        "high": 1.1050,
        "low": 1.0950,
        "close": 1.1025,
        "tick_volume": 10,
    })

@pytest.fixture(scope="module")
def mt5_market():
    """Mock the MT5Client.market object so tests run without a real terminal."""
    market = MagicMock()

    def fake_get_symbols(group=None):
        return ["EURUSD", "GBPUSD"]

    def fake_get_symbol_info(symbol_name):
        if symbol_name == "INVALID_SYMBOL":
            raise Exception(f"Symbol '{symbol_name}' not found")
        return {"name": symbol_name, "digits": 5}

    def fake_get_symbol_price(symbol_name):
        if symbol_name == "INVALID_SYMBOL":
            raise Exception("Could not get price data for 'INVALID_SYMBOL'")
        return {
            "bid": 1.1000,
            "ask": 1.1002,
            "last": 1.1001,
            "volume": 1200,
            "time": pd.Timestamp("2024-01-01", tz="UTC"),
        }

    def fake_get_candles_latest(symbol_name, timeframe, count=100):
        if symbol_name == "INVALID_SYMBOL" or timeframe == "INVALID_TF":
            raise Exception(f"Cannot retrieve candles for '{symbol_name}' / '{timeframe}'")
        return _make_candles(count)

    def fake_get_candles_by_date(symbol_name, timeframe, from_date=None, to_date=None):
        if symbol_name == "INVALID_SYMBOL" or timeframe == "INVALID_TF":
            raise Exception(f"Cannot retrieve candles for '{symbol_name}' / '{timeframe}'")
        return _make_candles(5)

    def fake_get_symbol_contract_size(symbol_name):
        if symbol_name == "INVALID_SYMBOL":
            raise Exception(f"Symbol '{symbol_name}' not found")
        return 100000.0

    market.get_symbols.side_effect = fake_get_symbols
    market.get_symbol_info.side_effect = fake_get_symbol_info
    market.get_symbol_price.side_effect = fake_get_symbol_price
    market.get_candles_latest.side_effect = fake_get_candles_latest
    market.get_candles_by_date.side_effect = fake_get_candles_by_date
    market.get_symbol_contract_size.side_effect = fake_get_symbol_contract_size

    yield market

# --- Test Data ---
TEST_SYMBOL = os.getenv("TEST_SYMBOL", "EURUSD")
TEST_TIMEFRAME = os.getenv("TEST_TIMEFRAME", "M1")

# --- Tests ---
def test_get_symbols(mt5_market):
    symbols = mt5_market.get_symbols()
    assert isinstance(symbols, list)
    assert TEST_SYMBOL in symbols

def test_get_symbols_group(mt5_market):
    group = "forex"
    symbols = mt5_market.get_symbols(group)
    assert isinstance(symbols, list)

def test_get_symbol_info(mt5_market):
    info = mt5_market.get_symbol_info(TEST_SYMBOL)
    assert isinstance(info, dict)
    assert "name" in info
    assert info["name"] == TEST_SYMBOL

def test_get_symbol_info_invalid(mt5_market):
    with pytest.raises(Exception):
        mt5_market.get_symbol_info("INVALID_SYMBOL")

def test_get_symbol_price(mt5_market):
    price = mt5_market.get_symbol_price(TEST_SYMBOL)
    assert isinstance(price, dict)
    assert "bid" in price and "ask" in price
    assert price["bid"] > 0 and price["ask"] > 0

def test_get_symbol_price_invalid(mt5_market):
    with pytest.raises(Exception):
        mt5_market.get_symbol_price("INVALID_SYMBOL")

def test_get_candles_latest(mt5_market):
    candles = mt5_market.get_candles_latest(TEST_SYMBOL, TEST_TIMEFRAME, count=10)
    assert isinstance(candles, pd.DataFrame)
    assert not candles.empty
    assert len(candles) == 10

def test_get_candles_by_date(mt5_market):
    # Use a recent date range (last 2 days)
    from datetime import datetime, timedelta
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    candles = mt5_market.get_candles_by_date(TEST_SYMBOL, TEST_TIMEFRAME, from_date, to_date)
    assert isinstance(candles, pd.DataFrame)
    assert not candles.empty

def test_get_candles_invalid_symbol(mt5_market):
    with pytest.raises(Exception):
        mt5_market.get_candles_latest("INVALID_SYMBOL", TEST_TIMEFRAME, count=5)

def test_get_candles_invalid_timeframe(mt5_market):
    with pytest.raises(Exception):
        mt5_market.get_candles_latest(TEST_SYMBOL, "INVALID_TF", count=5)

def test_get_symbol_contract_size(mt5_market):
    contract_size = mt5_market.get_symbol_contract_size(TEST_SYMBOL)
    assert isinstance(contract_size, float)
    assert contract_size > 0

def test_get_symbol_contract_size_invalid(mt5_market):
    with pytest.raises(Exception):
        mt5_market.get_symbol_contract_size("INVALID_SYMBOL")
