# By using transport="streamable-http" and mount_path="/mcp", your MCP server becomes a standard HTTP API that can be accessed from anywhere. 
# The server runs on http://localhost:8000/mcp and exposes your tools through the MCP protocol over HTTP.

from typing import Any, Dict
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(
    name="test-server",
    instructions="this is a sample test server",
    host="0.0.0.0",
    port=8000,
)

# Define a tool with structured output
@mcp.tool(
    name="add_numbers",
    description="Add two numbers together and return the sum",
    structured_output=True,
)
def add(a: float, b: float) -> Dict[str, Any]:
    """Return the sum of two numbers in structured format"""
    return {
        "operation": "addition",
        "operands": {"a": a, "b": b},
        "result": a + b,
        "success": True,
    }

if __name__ == "__main__":
    # The magic happens here - HTTP streamable transport!
    mcp.run(transport="streamable-http", mount_path="/mcp")