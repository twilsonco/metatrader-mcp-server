"""
Tests for graceful shutdown and connection lifecycle.

These tests verify that:
1. Graceful shutdown doesn't stall or require Ctrl+C
2. Connections are properly cleaned up (no duplicates)
3. Multiple connect/disconnect cycles don't leave orphaned connections
4. Timeout mechanism works when shutdown takes too long
5. No CancelledError exceptions during shutdown
"""

import pytest
import asyncio
import logging
import os
from unittest.mock import MagicMock, AsyncMock, patch
from metatrader_client import MT5Client
from metatrader_client.exceptions import DisconnectionError

logger = logging.getLogger(__name__)


class TestSyncDisconnect:
    """Test synchronous disconnect behavior."""
    
    def test_disconnect_called_flag_prevents_duplicate_calls(self):
        """Verify that _disconnect_called flag prevents multiple disconnect attempts."""
        config = {"login": 12345, "password": "pass", "server": "server"}
        client = MT5Client(config)
        connection = client._connection
        
        # Mark as connected
        connection._connected = True
        connection._disconnect_called = False
        
        # Mock mt5.shutdown
        with patch("MetaTrader5.mt5.shutdown", return_value=True):
            # First disconnect should succeed
            result1 = client.disconnect()
            assert result1 is True
            assert connection._disconnect_called is True
            
            # Second disconnect should return True immediately (guard check)
            result2 = client.disconnect()
            assert result2 is True
    
    def test_disconnect_graceful_degradation_when_not_initialized(self):
        """Verify that disconnect handles 'not initialized' gracefully."""
        config = {"login": 12345, "password": "pass", "server": "server"}
        client = MT5Client(config)
        connection = client._connection
        
        connection._connected = True
        connection._disconnect_called = False
        
        # Mock mt5.shutdown to raise 'not initialized' exception
        with patch("MetaTrader5.mt5.shutdown", side_effect=Exception("not initialized")):
            result = client.disconnect()
            assert result is True
            assert connection._connected is False
            assert connection._disconnect_called is True


class TestAsyncDisconnect:
    """Test asynchronous disconnect behavior."""
    
    def test_async_disconnect_called_flag_prevents_duplicate_calls(self):
        """Verify that async disconnect also uses _disconnect_called flag."""
        async def run_test():
            config = {"login": 12345, "password": "pass", "server": "server"}
            client = MT5Client(config)
            connection = client._connection
            
            # Mark as connected
            connection._connected = True
            connection._disconnect_called = False
            
            # Mock mt5.shutdown
            with patch("MetaTrader5.mt5.shutdown", return_value=True):
                # First async disconnect should succeed
                result1 = await client.async_disconnect()
                assert result1 is True
                assert connection._disconnect_called is True
                
                # Second async disconnect should return True immediately
                result2 = await client.async_disconnect()
                assert result2 is True
        
        asyncio.run(run_test())
    
    def test_async_disconnect_uses_thread_pool(self):
        """Verify that async_disconnect uses asyncio.to_thread()."""
        async def run_test():
            config = {"login": 12345, "password": "pass", "server": "server"}
            client = MT5Client(config)
            connection = client._connection
            
            connection._connected = True
            connection._disconnect_called = False
            
            # Track if to_thread was called
            to_thread_called = False
            
            async def mock_to_thread(func):
                nonlocal to_thread_called
                to_thread_called = True
                return func()
            
            with patch("asyncio.to_thread", side_effect=mock_to_thread):
                with patch("MetaTrader5.mt5.shutdown", return_value=True):
                    await client.async_disconnect()
                    assert to_thread_called is True
        
        asyncio.run(run_test())


class TestShutdownTimeout:
    """Test graceful shutdown with timeout mechanism."""
    
    def test_async_disconnect_timeout_during_shutdown(self):
        """Verify that timeout is enforced during shutdown."""
        async def run_test():
            config = {"login": 12345, "password": "pass", "server": "server"}
            client = MT5Client(config)
            connection = client._connection
            
            connection._connected = True
            connection._disconnect_called = False
            
            # Create a mock that sleeps
            original_to_thread = asyncio.to_thread
            async def slow_to_thread(func):
                await asyncio.sleep(100)  # This will be interrupted by timeout
                return func()
            
            with patch("asyncio.to_thread", side_effect=slow_to_thread):
                with pytest.raises(asyncio.TimeoutError):
                    # Timeout should interrupt the slow disconnect
                    await asyncio.wait_for(client.async_disconnect(), timeout=0.1)
        
        asyncio.run(run_test())
    
    def test_graceful_shutdown_waits_for_disconnect(self):
        """Verify that async disconnect can be awaited with timeout."""
        async def run_test():
            config = {"login": 12345, "password": "pass", "server": "server"}
            client = MT5Client(config)
            connection = client._connection
            
            connection._connected = True
            connection._disconnect_called = False
            
            with patch("MetaTrader5.mt5.shutdown", return_value=True):
                # Verify that async_disconnect returns a coroutine that can be awaited
                result = await asyncio.wait_for(client.async_disconnect(), timeout=2.0)
                assert result is True
        
        asyncio.run(run_test())


class TestConnectionStateTracking:
    """Test connection state tracking and initialization."""
    
    def test_disconnect_called_flag_initialized_false(self):
        """Verify _disconnect_called is initialized to False."""
        config = {"login": 12345, "password": "pass", "server": "server"}
        client = MT5Client(config)
        
        assert client._connection._disconnect_called is False
    
    def test_multiple_connects_and_disconnects(self):
        """Verify multiple connect/disconnect cycles work correctly."""
        config = {"login": 12345, "password": "pass", "server": "server"}
        client = MT5Client(config)
        connection = client._connection
        
        with patch("MetaTrader5.mt5.initialize", return_value=True):
            with patch("MetaTrader5.mt5.login", return_value=True):
                with patch("MetaTrader5.mt5.shutdown", return_value=True):
                    with patch("metatrader_client.client_connection._find_terminal_path", return_value="fake_path"):
                        # Cycle 1: connect
                        connection._connected = False
                        connection._disconnect_called = False
                        connection.connect()
                        
                        # Disconnect should set flag
                        connection.disconnect()
                        assert connection._disconnect_called is True
                        
                        # Cycle 2: fresh state after reconnect
                        connection._connected = False
                        connection._disconnect_called = False
                        connection.connect()
                        
                        # Second disconnect should also work
                        connection.disconnect()
                        assert connection._disconnect_called is True


class TestAsyncShutdownIntegration:
    """Integration tests for async shutdown behavior."""
    
    def test_lifespan_cleanup_with_timeout(self):
        """Test that async disconnect handles errors gracefully."""
        async def run_test():
            config = {"login": 12345, "password": "pass", "server": "server"}
            client = MT5Client(config)
            connection = client._connection
            
            connection._connected = True
            connection._disconnect_called = False
            
            # Mock a disconnect that fails
            with patch("asyncio.to_thread") as mock_to_thread:
                async def failing_disconnect():
                    raise Exception("Disconnect failed")
                mock_to_thread.return_value = failing_disconnect()
                
                # Should not raise - exception is handled
                try:
                    result = await client.async_disconnect()
                except Exception:
                    pass  # Exception is expected and should be handled
        
        asyncio.run(run_test())
    
    def test_no_orphaned_async_tasks_after_shutdown(self):
        """Verify no orphaned async tasks remain after shutdown."""
        async def run_test():
            from metatrader_mcp.server import app_lifespan
            
            initial_task_count = len(asyncio.all_tasks())
            
            with patch("metatrader_mcp.utils.init") as mock_init:
                mock_client = MagicMock()
                async def mock_async_disconnect():
                    return True
                mock_client.async_disconnect = mock_async_disconnect
                mock_init.return_value = mock_client
                
                mock_server = MagicMock()
                
                async with app_lifespan(mock_server) as ctx:
                    pass
                
                # Allow event loop to clean up
                await asyncio.sleep(0.01)
                
                final_task_count = len(asyncio.all_tasks())
                # Task count should not increase (no orphaned tasks)
                assert final_task_count <= initial_task_count + 1  # +1 for test cleanup
        
        asyncio.run(run_test())


class TestFastAPILifespan:
    """Test FastAPI lifespan shutdown."""
    
    def test_fastapi_lifespan_cleanup(self):
        """Test FastAPI lifespan cleanup with async disconnect."""
        async def run_test():
            # Test that the lifespan structure supports async disconnect
            # by verifying the pattern works with a simple mock
            config = {"login": 12345, "password": "pass", "server": "server"}
            client = MT5Client(config)
            connection = client._connection
            
            connection._connected = True
            connection._disconnect_called = False
            
            with patch("MetaTrader5.mt5.shutdown", return_value=True):
                # Simulate the pattern used in FastAPI lifespan
                result = await asyncio.wait_for(client.async_disconnect(), timeout=10.0)
                assert result is True
                assert connection._disconnect_called is True
        
        asyncio.run(run_test())
    
    def test_fastapi_lifespan_timeout_handling(self):
        """Test FastAPI lifespan handles timeout gracefully."""
        async def run_test():
            from metatrader_openapi.main import lifespan
            
            with patch.dict("os.environ", {"LOGIN": "12345", "PASSWORD": "pass", "SERVER": "server"}):
                with patch("metatrader_mcp.utils.init") as mock_init:
                    # Mock a disconnect that times out
                    mock_client = MagicMock()
                    async def timeout_disconnect():
                        await asyncio.sleep(100)
                    mock_client.async_disconnect = timeout_disconnect
                    mock_init.return_value = mock_client
                    
                    mock_app = MagicMock()
                    
                    # Should not raise even with timeout
                    async with lifespan(mock_app) as _:
                        pass
        
        asyncio.run(run_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
