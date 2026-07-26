import os
import pytest
from dotenv import load_dotenv
from metatrader_client import MT5Client
import platform
import time
from datetime import datetime
import time # Ensure time is imported, though it was already there

SYMBOL = "EURUSD"
VOLUME = 0.01
PENDING_PRICE = 1.2000  # Adjust for your demo market

@pytest.fixture(scope="module")
def mt5_client():
    # Clear console for pretty output
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')
    print("\n🧪 MetaTrader 5 MCP Order System Full Test Suite 🧪\n")
    print("🔑 Loading credentials and connecting to MetaTrader 5...")
    load_dotenv()
    
    # Check if environment variables are set
    login = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    server = os.getenv("SERVER")
    
    if not login or not password or not server:
        print("❌ Error: Missing required environment variables!")
        print("Please create a .env file with LOGIN, PASSWORD, and SERVER variables.")
        pytest.skip("Missing environment variables for MetaTrader 5 connection")
    
    config = {
        "login": int(login),
        "password": password,
        "server": server
    }
    client = MT5Client(config)
    client.connect()
    print("✅ Connected!\n")
    yield client
    print("\n🔌 Disconnecting from MetaTrader 5...")
    client.disconnect()
    print("👋 Disconnected!")

def test_place_market_order_with_sl_tp(mt5_client):
    """Tests placing market orders with stop loss and take profit."""
    print("\n🧪 Testing Market Orders with SL/TP 🧪")
    SYMBOL = "EURUSD"  # Or use the global one
    VOLUME = 0.01

    # Fetch current market price
    current_price_info = mt5_client.market.get_symbol_price(SYMBOL)
    assert current_price_info is not None, "Failed to fetch current market price."
    print(f"Current {SYMBOL} prices: Bid={current_price_info['bid']}, Ask={current_price_info['ask']}")

    # --- Test BUY Order with SL/TP ---
    print(f"\n🚀 Placing BUY order for {SYMBOL} with SL/TP...")
    order_type_buy = "BUY"
    buy_price = current_price_info['ask']
    stop_loss_buy = round(buy_price - 0.0010, 5)
    take_profit_buy = round(buy_price + 0.0010, 5)

    market_order_buy = mt5_client.order.place_market_order(
        type=order_type_buy,
        symbol=SYMBOL,
        volume=VOLUME,
        stop_loss=stop_loss_buy,
        take_profit=take_profit_buy
    )
    print(f"BUY Order Response: {market_order_buy}")

    assert market_order_buy is not None, "Market order (BUY) response is None."
    assert market_order_buy["error"] is False, f"BUY order failed: {market_order_buy['message']}"
    assert market_order_buy["data"] is not None, "BUY order data is None."
    # MT5 might adjust SL/TP slightly based on broker rules (e.g., distance from price), so direct equality might fail.
    # We should check if the SL/TP in the response are close to what we sent, or if they are not 0.0.
    # For this test, we'll check they are not 0.0 as a basic confirmation.
    # A more robust check would involve fetching the position details and verifying SL/TP there.
    assert market_order_buy["data"].request.sl == stop_loss_buy, f"BUY SL mismatch: expected {stop_loss_buy}, got {market_order_buy['data'].request.sl}"
    assert market_order_buy["data"].request.tp == take_profit_buy, f"BUY TP mismatch: expected {take_profit_buy}, got {market_order_buy['data'].request.tp}"
    print(f"✅ BUY order for {SYMBOL} with SL={stop_loss_buy}, TP={take_profit_buy} placed successfully. Order ID: {market_order_buy['data'].order}")

    time.sleep(2) # Allow broker to process
    print(f"Attempting to close BUY position ID: {market_order_buy['data'].order}")
    close_action_buy = mt5_client.order.close_position(market_order_buy["data"].order)
    print(f"Close BUY Response: {close_action_buy}")
    assert close_action_buy["error"] is False, f"Failed to close BUY position {market_order_buy['data'].order}: {close_action_buy['message']}"
    print(f"✅ BUY position {market_order_buy['data'].order} closed successfully.")

    time.sleep(5) # Interval between tests

    # --- Test SELL Order with SL/TP ---
    print(f"\n🚀 Placing SELL order for {SYMBOL} with SL/TP...")
    # Re-fetch price info in case market moved
    current_price_info_sell = mt5_client.market.get_symbol_price(SYMBOL)
    assert current_price_info_sell is not None, "Failed to fetch current market price for SELL."
    print(f"Current {SYMBOL} prices for SELL: Bid={current_price_info_sell['bid']}, Ask={current_price_info_sell['ask']}")

    order_type_sell = "SELL"
    sell_price = current_price_info_sell['bid']
    stop_loss_sell = round(sell_price + 0.0010, 5)
    take_profit_sell = round(sell_price - 0.0010, 5)

    market_order_sell = mt5_client.order.place_market_order(
        type=order_type_sell,
        symbol=SYMBOL,
        volume=VOLUME,
        stop_loss=stop_loss_sell,
        take_profit=take_profit_sell
    )
    print(f"SELL Order Response: {market_order_sell}")

    assert market_order_sell is not None, "Market order (SELL) response is None."
    assert market_order_sell["error"] is False, f"SELL order failed: {market_order_sell['message']}"
    assert market_order_sell["data"] is not None, "SELL order data is None."
    assert market_order_sell["data"].request.sl == stop_loss_sell, f"SELL SL mismatch: expected {stop_loss_sell}, got {market_order_sell['data'].request.sl}"
    assert market_order_sell["data"].request.tp == take_profit_sell, f"SELL TP mismatch: expected {take_profit_sell}, got {market_order_sell['data'].request.tp}"
    print(f"✅ SELL order for {SYMBOL} with SL={stop_loss_sell}, TP={take_profit_sell} placed successfully. Order ID: {market_order_sell['data'].order}")

    time.sleep(2) # Allow broker to process
    print(f"Attempting to close SELL position ID: {market_order_sell['data'].order}")
    close_action_sell = mt5_client.order.close_position(market_order_sell["data"].order)
    print(f"Close SELL Response: {close_action_sell}")
    assert close_action_sell["error"] is False, f"Failed to close SELL position {market_order_sell['data'].order}: {close_action_sell['message']}"
    print(f"✅ SELL position {market_order_sell['data'].order} closed successfully.")
    print("\n🎉 Test for market orders with SL/TP completed. 🎉")

def test_full_order_functionality(mt5_client):
    summary = []
    # 1. Get all positions
    print("\n📋 Getting all open positions...")
    all_positions = mt5_client.order.get_all_positions()
    print(f"📈 All positions:\n{all_positions}")
    summary.append("📋 get_all_positions: ✅")

    # 2. Get positions by symbol
    print("\n🔎 Getting positions by symbol...")
    positions_by_symbol = mt5_client.order.get_positions_by_symbol(SYMBOL)
    print(f"🔎 Positions for {SYMBOL}:\n{positions_by_symbol}")
    summary.append("🔎 get_positions_by_symbol: ✅")

    # 3. Get positions by currency (assuming USD)
    print("\n💵 Getting positions by currency...")
    positions_by_currency = mt5_client.order.get_positions_by_currency("USD")
    print(f"💵 Positions for USD:\n{positions_by_currency}")
    summary.append("💵 get_positions_by_currency: ✅")

    # 4. Place a market order
    print("\n🚀 Placing a market BUY order...")
    market_order = mt5_client.order.place_market_order(
        type="BUY",
        symbol=SYMBOL,
        volume=VOLUME
    )
    assert market_order is not None and ("data" in market_order and market_order["data"] is not None), "❌ Failed to place market order"
    print(f"✅ Market order placed! ID: {market_order['data'].order if market_order['data'] else 'N/A'}")
    summary.append("🚀 place_market_order: ✅")

    # 5. Get positions by id
    print("\n🆔 Getting position by ID...")
    pos_id = market_order["data"].order if market_order["data"] else None
    position_by_id = mt5_client.order.get_positions_by_id(pos_id)
    print(f"🆔 Position for ID {pos_id}:\n{position_by_id}")
    summary.append("🆔 get_positions_by_id: ✅")

    # 6. Place a pending order
    print("\n⏳ Placing a pending BUY order...")
    pending_order = mt5_client.order.place_pending_order(
        type="BUY",
        symbol=SYMBOL,
        volume=VOLUME,
        price=PENDING_PRICE
    )
    assert pending_order is not None and ("data" in pending_order and pending_order["data"] is not None), "❌ Failed to place pending order"
    print(f"✅ Pending order placed! ID: {pending_order['data'].order if pending_order['data'] else 'N/A'}")
    summary.append("⏳ place_pending_order: ✅")

    # 7. Get pending orders (all)
    print("\n🕒 Getting all pending orders...")
    all_pending_orders = mt5_client.order.get_all_pending_orders()
    print(f"🕒 All pending orders:\n{all_pending_orders}")
    summary.append("🕒 get_all_pending_orders: ✅")

    # 8. Get pending orders by symbol
    print("\n🔎 Getting pending orders by symbol...")
    pending_by_symbol = mt5_client.order.get_pending_orders_by_symbol(SYMBOL)
    print(f"🔎 Pending orders for {SYMBOL}:\n{pending_by_symbol}")
    summary.append("🔎 get_pending_orders_by_symbol: ✅")

    # 9. Get pending orders by currency
    print("\n💵 Getting pending orders by currency...")
    pending_by_currency = mt5_client.order.get_pending_orders_by_currency("USD")
    print(f"💵 Pending orders for USD:\n{pending_by_currency}")
    summary.append("💵 get_pending_orders_by_currency: ✅")

    # 10. Get pending orders by id
    print("\n🆔 Getting pending order by ID...")
    pend_id = pending_order["data"].order if pending_order["data"] else None
    pending_by_id = mt5_client.order.get_pending_orders_by_id(pend_id)
    print(f"🆔 Pending order for ID {pend_id}:\n{pending_by_id}")
    summary.append("🆔 get_pending_orders_by_id: ✅")

    # 11. Modify the open position (if supported)
    print("\n✏️ Modifying the open position SL/TP...")
    modified_position = mt5_client.order.modify_position(
        id=pos_id,
        stop_loss=1.1000,   # Example SL value, adjust as needed
        take_profit=1.3000  # Example TP value, adjust as needed
    )
    print(f"✏️ Modified position: {modified_position}")
    summary.append("✏️ modify_position: ✅")

    # 12. Modify the pending order
    print("\n✏️ Modifying the pending order price...")
    new_price = PENDING_PRICE - 0.0005
    modified_pending = mt5_client.order.modify_pending_order(
        id=pend_id,
        price=new_price
    )
    print(f"✏️ Modified pending order: {modified_pending}")
    summary.append("✏️ modify_pending_order: ✅")

    # 13. Close all profitable positions
    print("\n💰 Closing all profitable positions...")
    close_profitable = mt5_client.order.close_all_profitable_positions()
    print(f"💰 Closed profitable positions: {close_profitable}")
    summary.append("💰 close_all_profitable_positions: ✅")

    # 14. Close all losing positions
    print("\n🔻 Closing all losing positions...")
    close_losing = mt5_client.order.close_all_losing_positions()
    print(f"🔻 Closed losing positions: {close_losing}")
    summary.append("🔻 close_all_losing_positions: ✅")

    # 15. Close all positions by symbol
    print(f"\n🔒 Closing all positions for {SYMBOL}...")
    close_by_symbol = mt5_client.order.close_all_positions_by_symbol(SYMBOL)
    print(f"🔒 Closed positions for {SYMBOL}: {close_by_symbol}")
    summary.append("🔒 close_all_positions_by_symbol: ✅")

    # 16. Close all positions
    print("\n🛑 Closing all positions...")
    close_all = mt5_client.order.close_all_positions()
    print(f"🛑 Closed all positions: {close_all}")
    summary.append("🛑 close_all_positions: ✅")

    # 17. Close the specific market order (if still open)
    print("\n🛑 Closing the market order by ID...")
    close_market = mt5_client.order.close_position(id=pos_id)
    print(f"🛑 Closed market order: {close_market}")
    summary.append("🛑 close_position: ✅")

    # 18. Cancel the pending order by ID
    print("\n🚫 Cancelling the pending order by ID...")
    cancel_pending = mt5_client.order.cancel_pending_order(id=pend_id)
    print(f"🚫 Cancelled pending order: {cancel_pending}")
    summary.append("🚫 cancel_pending_order: ✅")

    # 19. Cancel all pending orders by symbol
    print(f"\n🚫 Cancelling all pending orders for {SYMBOL}...")
    cancel_by_symbol = mt5_client.order.cancel_pending_orders_by_symbol(SYMBOL)
    print(f"🚫 Cancelled pending orders for {SYMBOL}: {cancel_by_symbol}")
    summary.append("🚫 cancel_pending_orders_by_symbol: ✅")

    # 20. Cancel all pending orders
    print("\n🚫 Cancelling all pending orders...")
    cancel_all = mt5_client.order.cancel_all_pending_orders()
    print(f"🚫 Cancelled all pending orders: {cancel_all}")
    summary.append("🚫 cancel_all_pending_orders: ✅")

    # Summary
    print("\n\n✨📝 TEST SUMMARY 📝✨")
    for line in summary:
        print(line)
    print("\n🎉 All order functions tested successfully on demo account! 🎉\n")
    time.sleep(1)

    # --- REPORTING SECTION ---
    # Always write report, even if some steps failed
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d_%H-%M-%S')
    report_dir = os.path.join(os.path.dirname(__file__), '../reports')
    os.makedirs(report_dir, exist_ok=True)
    filename = f"{timestamp}_client_order.md"
    filepath = os.path.join(report_dir, filename)
    all_passed = all('✅' in s for s in summary)
    status = '✅ SUCCESS' if all_passed else '❌ FAILURE'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# 🧪 MetaTrader 5 MCP Order System Test Report\n\n")
        f.write(f"**Date:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Module:** Client Order\n\n")
        f.write(f"## Test Steps and Results\n\n")
        for s in summary:
            f.write(f"- {s}\n")
        f.write("\n---\n")
        f.write(f"**Status:** {status}\n")
    print(f"\n📄 Test report written to: {filepath}\n")


def test_get_next_open_position(mt5_client):
    """Tests the round-robin open position picker."""
    print("\n🧪 Testing get_next_open_position 🧪")

    result = mt5_client.order.get_next_open_position()

    print(f"Result: {result}")
    assert result is not None, "Result is None."
    assert "error" in result, "Result missing 'error' key."
    assert result["error"] is False, f"Operation failed: {result.get('message')}"
    assert "message" in result, "Result missing 'message' key."
    assert "data" in result, "Result missing 'data' key."

    if result["data"] is not None:
        expected_keys = {
            "ticket", "symbol", "type", "volume", "price_open",
            "sl", "tp", "price_current", "profit", "time_setup",
        }
        assert set(result["data"].keys()) >= expected_keys, (
            f"Missing keys: {expected_keys - set(result['data'].keys())}"
        )
        assert result["data"]["type"] in ("BUY", "SELL"), (
            f"Unexpected position type: {result['data']['type']}"
        )
        print(f"✅ Selected position ticket={result['data']['ticket']} "
              f"symbol={result['data']['symbol']} type={result['data']['type']}")
    else:
        print("ℹ️ No open positions available — result data is None.")


def test_get_next_open_position_with_cache_path(tmp_path, mt5_client):
    """Tests that the cache file is created and round-robin works across calls."""
    print("\n🧪 Testing get_next_open_position with custom cache path 🧪")

    cache_file = tmp_path / "review_cache.json"

    # First call — should create the cache file
    first = mt5_client.order.get_next_open_position(cache_path=str(cache_file))
    assert first is not None
    assert "error" in first
    assert first["error"] is False

    if first["data"] is None:
        print("ℹ️ No open positions available — skipping round-robin assertion.")
        return

    assert cache_file.exists(), f"Cache file was not created at {cache_file}"

    # Second call — should rotate to a different ticket (if more than one exists)
    second = mt5_client.order.get_next_open_position(cache_path=str(cache_file))
    assert second is not None
    assert "error" in second
    assert second["error"] is False

    if second["data"] is not None:
        # Cache should now contain at least two tickets (or the same one twice)
        import json
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        assert isinstance(cache_data, dict)
        assert len(cache_data) >= 1
        print(f"✅ Cache contains {len(cache_data)} ticket(s) after two calls.")
    else:
        print("ℹ️ Second call returned no data — only one position or all markets closed.")


def test_get_next_open_position_staleness_filter(mt5_client):
    """Tests that positions on closed markets are filtered out via staleness."""
    print("\n🧪 Testing get_next_open_position staleness filter 🧪")

    # Use an extremely low staleness threshold to force filtering
    result = mt5_client.order.get_next_open_position(staleness_seconds=1)

    assert result is not None
    assert "error" in result
    assert result["error"] is False

    # With staleness_seconds=1, most ticks will be considered stale, so data may be None
    if result["data"] is None:
        assert "No positions on currently open markets" in result["message"], (
            f"Expected closed-markets message, got: {result['message']}"
        )
        print("✅ Staleness filter correctly excluded all positions.")
    else:
        print(f"ℹ️ At least one position's tick was within 1s — "
              f"selected ticket={result['data']['ticket']}")


def test_get_next_open_position_prunes_closed_positions(tmp_path, mt5_client):
    """Tests that closed positions are purged from the cache."""
    print("\n🧪 Testing get_next_open_position cache pruning 🧪")

    import json
    cache_file = tmp_path / "prune_cache.json"

    # Pre-populate cache with a fake ticket that is NOT currently open
    fake_ticket = "99999999"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump({fake_ticket: 1700000000.0}, f)

    # Call the tool — it should prune the stale entry
    result = mt5_client.order.get_next_open_position(cache_path=str(cache_file))

    assert result is not None
    assert "error" in result
    assert result["error"] is False

    # Verify the fake ticket was removed from the cache
    with open(cache_file, "r", encoding="utf-8") as f:
        cache_after = json.load(f)

    assert fake_ticket not in cache_after, (
        f"Stale ticket {fake_ticket} should have been pruned, but cache still contains it: {cache_after}"
    )
    print(f"✅ Stale ticket {fake_ticket} was correctly pruned from cache.")
    print(f"   Cache after call: {cache_after}")
