import MetaTrader5 as mt5
from ..exceptions import SymbolNotFoundError

def get_symbol_contract_size(connection, *, symbol_name: str) -> float:
    """Get the contract size for a specified symbol.

    Args:
        connection: MT5 connection object (required for API consistency;
                   currently routing through MetaTrader5 module directly)
        symbol_name: The name of the symbol (e.g. 'EURUSD')

    Returns:
        float: The trade contract size (number of units per lot)

    Raises:
        SymbolNotFoundError: If the symbol is not found
    """
    # Note: Currently uses MetaTrader5 module directly for market data access.
    # Future enhancement: Route through connection object for better testability
    # and consistency with other helper functions.
    symbols = mt5.symbols_get(symbol_name)
    if not symbols or len(symbols) == 0:
        raise SymbolNotFoundError(f"Symbol '{symbol_name}' not found")
    symbol_info = symbols[0]
    return float(symbol_info.trade_contract_size)
