def disconnect(connection):
    """
    Disconnect from the MetaTrader 5 terminal.
    
    NOTE: This is the synchronous version. For graceful shutdown, prefer async_disconnect().
    
    Returns:
        bool: True if successful, False otherwise.
    Raises:
        DisconnectionError: If disconnection fails.
    """
    import logging
    logger = logging.getLogger("MT5Connection")
    from metatrader_client.exceptions import DisconnectionError
    import MetaTrader5 as mt5
    
    # Prevent multiple disconnect attempts
    if connection._disconnect_called:
        logger.debug("Disconnect already in progress or completed (sync)")
        return True
    
    if not connection._connected:
        logger.debug("Already disconnected (sync)")
        return True
    
    connection._disconnect_called = True
    logger.debug("Starting synchronous disconnect")
    try:
        result = mt5.shutdown()
        if result:
            connection._connected = False
            logger.info("Successfully disconnected from MetaTrader 5 terminal")
            return True
        else:
            from ._get_last_error import _get_last_error
            error_code, error_message = _get_last_error(connection)
            raise DisconnectionError(f"Failed to disconnect from MetaTrader 5 terminal: {error_message} (Error code: {error_code})")
    except Exception as e:
        if "not initialized" in str(e).lower():
            connection._connected = False
            logger.debug("Terminal already disconnected (sync)")
            return True
        raise DisconnectionError(f"Error disconnecting from MetaTrader 5 terminal: {str(e)}")

async def async_disconnect(connection):
    """
    Asynchronously disconnect from the MetaTrader 5 terminal.
    
    This function wraps the synchronous mt5.shutdown() call in asyncio.to_thread()
    to prevent blocking the event loop during graceful shutdown.
    
    Uses an async lock to ensure only one disconnect attempt proceeds at a time,
    preventing race conditions during concurrent shutdown scenarios.
    
    Returns:
        bool: True if successful, False otherwise.
    Raises:
        DisconnectionError: If disconnection fails.
    """
    import logging
    import asyncio
    logger = logging.getLogger("MT5Connection")
    from metatrader_client.exceptions import DisconnectionError
    import MetaTrader5 as mt5
    
    # Acquire async lock to ensure only one disconnect proceeds at a time
    async with connection._disconnect_lock:
        # Prevent multiple disconnect attempts
        if connection._disconnect_called:
            logger.debug("Disconnect already in progress or completed")
            return True
        
        if not connection._connected:
            logger.debug("Already disconnected")
            return True
        
        connection._disconnect_called = True
    
    # Proceed with disconnect outside the lock to avoid blocking other checks
    try:
        # Run blocking mt5.shutdown() in a thread pool to avoid blocking event loop
        result = await asyncio.to_thread(mt5.shutdown)
        if result:
            connection._connected = False
            logger.info("Successfully disconnected from MetaTrader 5 terminal")
            return True
        else:
            from ._get_last_error import _get_last_error
            error_code, error_message = _get_last_error(connection)
            raise DisconnectionError(f"Failed to disconnect from MetaTrader 5 terminal: {error_message} (Error code: {error_code})")
    except Exception as e:
        if "not initialized" in str(e).lower():
            connection._connected = False
            logger.debug("Terminal already disconnected")
            return True
        raise DisconnectionError(f"Error disconnecting from MetaTrader 5 terminal: {str(e)}")
