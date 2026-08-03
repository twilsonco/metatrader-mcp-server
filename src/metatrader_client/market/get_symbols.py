from typing import Optional, List
import MetaTrader5 as mt5

def get_symbols(connection, group: Optional[str] = None, fields: list[str] = ["name"]) -> List[str]:
    """
    Get list of all available market symbols.
    Args:
        connection: MT5Connection instance (not used directly, but kept for API consistency)
        group: Filter symbols by group pattern (e.g., "*USD*" for USD pairs).
        fields: List of fields to retrieve for each symbol. If empty, returns full symbol objects.
        
    Full list of available fields:
    ask, askhigh, asklow, bank, basis, bid, bidhigh, bidlow, category, chart_mode, count, currency_base, currency_margin, currency_profit, custom, description, digits, exchange, expiration_mode, expiration_time, filling_mode, formula, index, isin, last, lasthigh, lastlow, margin_hedged, margin_hedged_use_leg, margin_initial, margin_maintenance, n_fields, n_sequence_fields, n_unnamed_fields, name, option_mode, option_right, option_strike, order_gtc_mode, order_mode, page, path, point, price_change, price_greeks_delta, price_greeks_gamma, price_greeks_omega, price_greeks_rho, price_greeks_theta, price_greeks_vega, price_sensitivity, price_theoretical, price_volatility, select, session_aw, session_buy_orders, session_buy_orders_volume, session_close, session_deals, session_interest, session_open, session_price_limit_max, session_price_limit_min, session_price_settlement, session_sell_orders, session_sell_orders_volume, session_turnover, session_volume, spread, spread_float, start_time, swap_long, swap_mode, swap_rollover3days, swap_short, ticks_bookdepth, time, trade_accrued_interest, trade_calc_mode, trade_contract_size, trade_exemode, trade_face_value, trade_freeze_level, trade_liquidity_rate, trade_mode, trade_stops_level, trade_tick_size, trade_tick_value, trade_tick_value_loss, trade_tick_value_profit, visible, volume, volume_limit, volume_max, volume_min, volume_real, volume_step, volumehigh, volumehigh_real, volumelow, volumelow_real
    
    Returns:
        List: List of symbol attributes matching the filter criteria if fields are specified, otherwise list of full symbol objects.
    """
    symbols = mt5.symbols_get() if group is None else mt5.symbols_get(group)
    if not symbols:
        return []
    result = []
    for symbol in symbols:
        item = {}
        if fields:
            # If only one field specified, return a flat list that field value for each symbol,
            # otherwise return a list of dicts with the specified fields for each symbol.
            for field in fields:
                item[field] = getattr(symbol, field)
            result.append(item if len(item) > 1 else item[fields[0]])
        else:
            result.append(symbol)
    return result
