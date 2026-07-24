"""Pytest configuration and fixtures for mocking MetaTrader5."""
import sys
from unittest.mock import MagicMock
import pytest
import os

# Create a mock MetaTrader5 module before any imports that depend on it
mock_mt5 = MagicMock()
sys.modules['MetaTrader5'] = mock_mt5

# Set up environment variables for mocking
os.environ['LOGIN'] = 'test'
os.environ['PASSWORD'] = 'test'
os.environ['SERVER'] = 'test'

# Store the mock client globally so tests can access it
_test_mock_client = None


def pytest_configure(config):
    """Create and store mock client at pytest startup."""
    global _test_mock_client
    _test_mock_client = MagicMock()
    _test_mock_client.market = MagicMock()
    _test_mock_client.disconnect = MagicMock()


@pytest.fixture(autouse=True)
def mock_init_function(monkeypatch):
    """Auto-use fixture that mocks the init function."""
    def fake_init(*args, **kwargs):
        return _test_mock_client
    
    # Patch in both locations since main.py does "from metatrader_mcp.utils import init"
    monkeypatch.setattr("metatrader_mcp.utils.init", fake_init)
    # Import main after patching utils
    import metatrader_openapi.main
    monkeypatch.setattr("metatrader_openapi.main.init", fake_init)
    
    yield
    # Reset the mock client methods after each test
    _test_mock_client.reset_mock()
    _test_mock_client.market.reset_mock()


@pytest.fixture
def mock_client():
    """Provide access to the mock client for tests."""
    return _test_mock_client
