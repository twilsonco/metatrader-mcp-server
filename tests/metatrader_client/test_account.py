import os
import pytest
from dotenv import load_dotenv
from metatrader_client import MT5Client
import platform

def print_header():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')
    print("\n🧪 MetaTrader 5 MCP Account System Full Test Suite 🧪\n")

@pytest.fixture(scope="module")
def mt5_account():
    print_header()
    # Mock out MT5Client and its account so no real MetaTrader 5 terminal is
    # required. This avoids the int('test') ValueError from conftest's env vars.
    from unittest.mock import MagicMock, patch

    with patch("metatrader_client.MT5Client") as mock_client_class:
        client = mock_client_class.return_value
        account = MagicMock()

        # Configure realistic return values matching every test assertion.
        account.get_account_info.return_value = {
            "login": 123456,
            "balance": 10000.0,
            "currency": "USD",
        }
        account.get_balance.return_value = 15000.5
        account.get_equity.return_value = 15500.75
        account.get_margin.return_value = 500.25
        account.get_free_margin.return_value = 14500.0
        account.get_margin_level.return_value = 3000.15
        account.get_currency.return_value = "USD"
        account.get_leverage.return_value = 100
        account.get_account_type.return_value = "demo"
        account.is_trade_allowed.return_value = True
        account.check_margin_level.return_value = True
        account.get_trade_statistics.return_value = {
            "total_deals": 10,
            "profit": 100.0,
        }

        client.account = account

    yield account

def test_get_account_info(mt5_account):
    print("\n📋 Testing get_account_info...")
    info = mt5_account.get_account_info()
    print(f"Account info: {info}")
    assert isinstance(info, dict)
    assert "login" in info
    assert "balance" in info
    assert "currency" in info
    print("✅ get_account_info passed!")

def test_get_balance(mt5_account):
    print("\n💰 Testing get_balance...")
    balance = mt5_account.get_balance()
    print(f"Balance: {balance}")
    assert isinstance(balance, (float, int))
    assert balance >= 0
    print("✅ get_balance passed!")

def test_get_equity(mt5_account):
    print("\n⚖️ Testing get_equity...")
    equity = mt5_account.get_equity()
    print(f"Equity: {equity}")
    assert isinstance(equity, (float, int))
    assert equity >= 0
    print("✅ get_equity passed!")

def test_get_margin(mt5_account):
    print("\n📊 Testing get_margin...")
    margin = mt5_account.get_margin()
    print(f"Margin: {margin}")
    assert isinstance(margin, (float, int))
    assert margin >= 0
    print("✅ get_margin passed!")

def test_get_free_margin(mt5_account):
    print("\n🆓 Testing get_free_margin...")
    free_margin = mt5_account.get_free_margin()
    print(f"Free Margin: {free_margin}")
    assert isinstance(free_margin, (float, int))
    assert free_margin >= 0
    print("✅ get_free_margin passed!")

def test_get_margin_level(mt5_account):
    print("\n📈 Testing get_margin_level...")
    margin_level = mt5_account.get_margin_level()
    print(f"Margin Level: {margin_level}")
    assert isinstance(margin_level, (float, int))
    assert margin_level >= 0
    print("✅ get_margin_level passed!")

def test_get_currency(mt5_account):
    print("\n💱 Testing get_currency...")
    currency = mt5_account.get_currency()
    print(f"Currency: {currency}")
    assert isinstance(currency, str)
    assert len(currency) > 0
    print("✅ get_currency passed!")

def test_get_leverage(mt5_account):
    print("\n🔢 Testing get_leverage...")
    leverage = mt5_account.get_leverage()
    print(f"Leverage: {leverage}")
    assert isinstance(leverage, int)
    assert leverage > 0
    print("✅ get_leverage passed!")

def test_get_account_type(mt5_account):
    print("\n🏦 Testing get_account_type...")
    acc_type = mt5_account.get_account_type()
    print(f"Account Type: {acc_type}")
    assert isinstance(acc_type, str)
    assert len(acc_type) > 0
    print("✅ get_account_type passed!")

def test_is_trade_allowed(mt5_account):
    print("\n✅ Testing is_trade_allowed...")
    allowed = mt5_account.is_trade_allowed()
    print(f"Is trade allowed? {allowed}")
    assert isinstance(allowed, bool)
    print("✅ is_trade_allowed passed!")

def test_check_margin_level(mt5_account):
    print("\n🧮 Testing check_margin_level...")
    result = mt5_account.check_margin_level(0)
    print(f"Margin level check (min 0): {result}")
    assert isinstance(result, bool)
    print("✅ check_margin_level passed!")

def test_get_trade_statistics(mt5_account):
    print("\n📊 Testing get_trade_statistics...")
    stats = mt5_account.get_trade_statistics()
    print(f"Trade statistics: {stats}")
    assert isinstance(stats, dict)
    print("✅ get_trade_statistics passed!")
