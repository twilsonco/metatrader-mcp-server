import os
import pytest
from dotenv import load_dotenv
from metatrader_client import MT5Client
import pandas as pd

@pytest.fixture(scope="module")
def mt5_market():
    load_dotenv()
    login = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    server = os.getenv("SERVER")
    if not login or not password or not server:
        pytest.skip("Missing environment variables for MetaTrader 5 connection")
    config = {
        "login": int(login),
        "password": password,
        "server": server
    }
    client = MT5Client(config)
    client.connect()
    market = client.market
    yield market
    client.disconnect()

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
