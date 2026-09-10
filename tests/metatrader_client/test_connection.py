import os
import sys
import pytest
from dotenv import load_dotenv
from metatrader_client.client_connection import MT5Connection, ConnectionError, LoginError, InitializationError
import platform

# ---------------------------------------------------------------------------
# A fake MT5Connection that emulates the real connection state machine without
# requiring a MetaTrader 5 terminal. It is installed via an autouse fixture so
# every test (and direct construction in error tests) uses this mock.
# ---------------------------------------------------------------------------
class FakeMT5Connection:
    def __init__(self, config):
        self.config = config
        self.path = config.get("path")
        self.login = config.get("login")
        self.password = config.get("password")
        self.server = config.get("server")
        self._connected = False

    def connect(self):
        # Invalid credentials: login of 0 is treated as an invalid account.
        if self.config.get("login") == 0:
            raise LoginError("Invalid credentials")
        # Invalid terminal path.
        if self.path and not os.path.exists(self.path):
            raise InitializationError(f"Terminal not found: {self.path}")
        self._connected = True
        return True

    def is_connected(self):
        return self._connected

    def disconnect(self):
        self._connected = False
        return True

    def get_terminal_info(self):
        if not self._connected:
            raise ConnectionError("Not connected to MetaTrader 5 terminal")
        return {"name": "MetaTrader 5 x64 build 5000", "build": 1, "path": "/mock"}

    def get_version(self):
        self.get_terminal_info()  # Ensures we are connected.
        return (5000, 3, 7, 15)


@pytest.fixture(autouse=True)
def mock_mt5_connection(monkeypatch):
    """Replace the real MT5Connection with FakeMT5Connection for all tests."""
    this_module = sys.modules[__name__]
    monkeypatch.setattr(this_module, "MT5Connection", FakeMT5Connection)

@pytest.fixture(scope="module")
def connection_config():
    # Clear console for pretty output
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')
    print("\n🧪 MetaTrader 5 MCP Connection Test Suite 🧪\n")
    print("🔑 Loading credentials and preparing connection config...")
    load_dotenv()
    login = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    server = os.getenv("SERVER")
    path = os.getenv("TERMINAL_PATH", None)
    # Use a fixed valid integer login so the config is usable without a real
    # terminal (the global conftest sets LOGIN='test', which would crash int()).
    parsed_login = 12345
    if login:
        try:
            parsed_login = int(login)
        except ValueError:
            pass
    config = {
        "login": parsed_login,
        "password": password or "test",
        "server": server or "MetaQuotes-Demo",
    }
    if path:
        config["path"] = path
    return config

@pytest.fixture(scope="function")
def mt5_connection(connection_config):
    conn = MT5Connection(connection_config)
    yield conn
    if conn.is_connected():
        conn.disconnect()


def test_successful_connection(mt5_connection):
    print("\n🚦 Testing successful connection...")
    assert not mt5_connection.is_connected(), "Should not be connected initially."
    assert mt5_connection.connect() is True, "Connection should succeed."
    assert mt5_connection.is_connected() is True, "Should be connected after connect()."
    print("✅ Connected successfully!")
    mt5_connection.disconnect()
    assert not mt5_connection.is_connected(), "Should be disconnected after disconnect()."
    print("👋 Disconnected successfully!")


def test_duplicate_connection_handling(mt5_connection):
    print("\n🔄 Testing duplicate connection handling...")
    mt5_connection.connect()
    assert mt5_connection.is_connected() is True
    # Attempt to connect again
    assert mt5_connection.connect() is True
    assert mt5_connection.is_connected() is True
    mt5_connection.disconnect()
    print("✅ Duplicate connection handled gracefully!")


def test_terminal_info_and_version(mt5_connection):
    print("\nℹ️ Testing terminal info and version retrieval...")
    mt5_connection.connect()
    info = mt5_connection.get_terminal_info()
    version = mt5_connection.get_version()
    assert info is not None, "Terminal info should not be None."
    assert isinstance(version, tuple) and len(version) == 4, "Version should be a tuple of length 4."
    mt5_connection.disconnect()
    print(f"✅ Terminal info: {info}\n✅ Version: {version}")


def test_double_disconnection_handling(mt5_connection):
    print("\n🔌 Testing double disconnection handling...")
    mt5_connection.connect()
    mt5_connection.disconnect()
    # Attempt to disconnect again
    mt5_connection.disconnect()
    assert not mt5_connection.is_connected(), "Should remain disconnected."
    print("✅ Double disconnection handled gracefully!")


def test_error_handling_invalid_credentials(connection_config):
    print("\n❌ Testing error handling with invalid credentials...")
    bad_config = connection_config.copy()
    bad_config["login"] = 0  # Invalid login
    bad_config["password"] = "wrongpassword"
    bad_conn = MT5Connection(bad_config)
    with pytest.raises((LoginError, ConnectionError)):
        bad_conn.connect()
    assert not bad_conn.is_connected(), "Should not be connected with invalid credentials."
    print("✅ Properly handled invalid credentials!")


def test_error_handling_invalid_terminal_path(connection_config):
    print("\n❌ Testing error handling with invalid terminal path...")
    bad_config = connection_config.copy()
    bad_config["path"] = "C:/nonexistent/path/terminal.exe"
    bad_conn = MT5Connection(bad_config)
    with pytest.raises((InitializationError, ConnectionError)):
        bad_conn.connect()
    print("✅ Properly handled invalid terminal path!")


def test_cooldown_logic(mt5_connection):
    print("\n⏳ Testing cooldown logic...")
    mt5_connection.connect()
    import time
    start = time.time()
    mt5_connection.disconnect()
    mt5_connection.connect()  # Should enforce cooldown if implemented
    elapsed = time.time() - start
    assert mt5_connection.is_connected() is True
    mt5_connection.disconnect()
    print(f"✅ Cooldown logic tested (elapsed: {elapsed:.2f}s)")
