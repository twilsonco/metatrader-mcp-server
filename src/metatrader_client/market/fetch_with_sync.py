from typing import Optional
from datetime import datetime
import time
import MetaTrader5 as mt5

def _fetch_with_sync(
    fetch_func, 
    symbol_name: str, 
    timeframe: int, 
    kick_date: datetime, 
    expected_count: Optional[int] = None, 
    max_retries: int = 20, 
    sleep_time: float = 0.5
):
    last_len = -1
    stable_iterations = 0
    
    for _ in range(max_retries):
        rates = fetch_func()
        current_len = len(rates) if rates is not None else 0
        
        # Success if we hit the requested count
        if expected_count is not None and current_len >= expected_count:
            return rates
            
        # Success if date range data length stabilizes
        if expected_count is None and current_len > 0:
            if current_len == last_len:
                stable_iterations += 1
                if stable_iterations >= 3:
                    return rates
            else:
                stable_iterations = 0
                
        # Force broker sync
        mt5.copy_rates_from(symbol_name, timeframe, kick_date, 1)
        
        last_len = current_len
        time.sleep(sleep_time)
        
    return fetch_func()