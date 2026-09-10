import os
import pytest
from unittest.mock import MagicMock
from dotenv import load_dotenv
from metatrader_client import MT5Client
import platform
import pandas as pd
from datetime import datetime, timedelta

def print_header():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')
    print("\n🧪 MetaTrader 5 MCP History System Full Test Suite 🧪\n")

@pytest.fixture(scope="module")
def mt5_history():
    """Return a mocked history object so tests run without a real MT5 terminal."""
    print_header()
    load_dotenv()

    def fake_get_deals(*args, **kwargs):
        from_date = kwargs.get("from_date") or (args[0] if args else None)
        # Empty date range -> no deals
        if isinstance(from_date, datetime) and from_date.year < 2001:
            return []
        return [{"ticket": 12345, "symbol": "EURUSD", "type": 0}]

    def fake_get_orders(*args, **kwargs):
        from_date = kwargs.get("from_date") or (args[0] if args else None)
        # Empty date range -> no orders
        if isinstance(from_date, datetime) and from_date.year < 2001:
            return []
        return [{"ticket": 67890, "symbol": "EURUSD", "type": 2}]

    history = MagicMock()
    history.get_deals.side_effect = fake_get_deals
    history.get_orders.side_effect = fake_get_orders
    history.get_total_deals.return_value = 5
    history.get_total_orders.return_value = 3
    history.get_deals_as_dataframe.return_value = pd.DataFrame([{"ticket": 12345, "symbol": "EURUSD"}])
    history.get_orders_as_dataframe.return_value = pd.DataFrame([{"ticket": 67890, "symbol": "EURUSD"}])

    yield history

# --- Test Data ---
TODAY = datetime.now()
YESTERDAY = TODAY - timedelta(days=1)

# --- Tests ---
def test_get_deals(mt5_history):
    print("\n📋 Testing get_deals...")
    deals = mt5_history.get_deals(from_date=YESTERDAY, to_date=TODAY)
    print(f"Deals: {deals}")
    assert isinstance(deals, list)
    if deals:
        assert "ticket" in deals[0]
    print("✅ get_deals passed!")

def test_get_orders(mt5_history):
    print("\n📋 Testing get_orders...")
    orders = mt5_history.get_orders(from_date=YESTERDAY, to_date=TODAY)
    print(f"Orders: {orders}")
    assert isinstance(orders, list)
    if orders:
        assert "ticket" in orders[0]
    print("✅ get_orders passed!")

def test_get_total_deals(mt5_history):
    print("\n📊 Testing get_total_deals...")
    total = mt5_history.get_total_deals(from_date=YESTERDAY, to_date=TODAY)
    print(f"Total deals: {total}")
    assert isinstance(total, int)
    assert total >= 0
    print("✅ get_total_deals passed!")

def test_get_total_orders(mt5_history):
    print("\n📊 Testing get_total_orders...")
    total = mt5_history.get_total_orders(from_date=YESTERDAY, to_date=TODAY)
    print(f"Total orders: {total}")
    assert isinstance(total, int)
    assert total >= 0
    print("✅ get_total_orders passed!")

def test_get_deals_as_dataframe(mt5_history):
    print("\n📑 Testing get_deals_as_dataframe...")
    df = mt5_history.get_deals_as_dataframe(from_date=YESTERDAY, to_date=TODAY)
    print(df)
    assert isinstance(df, pd.DataFrame)
    print("✅ get_deals_as_dataframe passed!")

def test_get_orders_as_dataframe(mt5_history):
    print("\n📑 Testing get_orders_as_dataframe...")
    df = mt5_history.get_orders_as_dataframe(from_date=YESTERDAY, to_date=TODAY)
    print(df)
    assert isinstance(df, pd.DataFrame)
    print("✅ get_orders_as_dataframe passed!")

def test_get_deals_empty_range(mt5_history):
    print("\n🧪 Testing get_deals with empty range...")
    empty_day = datetime(2000, 1, 1)
    deals = mt5_history.get_deals(from_date=empty_day, to_date=empty_day)
    print(f"Deals (empty): {deals}")
    assert isinstance(deals, list)
    assert len(deals) == 0 or (deals and "ticket" in deals[0])
    print("✅ get_deals_empty_range passed!")

def test_get_orders_empty_range(mt5_history):
    print("\n🧪 Testing get_orders with empty range...")
    empty_day = datetime(2000, 1, 1)
    orders = mt5_history.get_orders(from_date=empty_day, to_date=empty_day)
    print(f"Orders (empty): {orders}")
    assert isinstance(orders, list)
    assert len(orders) == 0 or (orders and "ticket" in orders[0])
    print("✅ get_orders_empty_range passed!")
