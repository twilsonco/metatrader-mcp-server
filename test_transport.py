from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client, StdioServerParameters
import sys

print("SSE Client:")
transport = sse_client("http://localhost:8080/sse")
print(f"Type: {type(transport)}")
print(f"Has read_stream: {hasattr(transport, 'read_stream')}")
print(f"Has write_stream: {hasattr(transport, 'write_stream')}")
print(f"Methods: {[m for m in dir(transport) if not m.startswith('_')]}")

print("\nStdio Client:")
params = StdioServerParameters(
    command=sys.executable,
    args=["-m", "metatrader_mcp.cli", "--transport", "stdio"],
)
stdio_transport = stdio_client(params)
print(f"Type: {type(stdio_transport)}")
print(f"Has read_stream: {hasattr(stdio_transport, 'read_stream')}")
print(f"Has write_stream: {hasattr(stdio_transport, 'write_stream')}")
print(f"Methods: {[m for m in dir(stdio_transport) if not m.startswith('_')]}")
