# MCP Lab

A demonstration project showing how to integrate MCP (Model Context Protocol) tools with OpenAI-compatible LLMs using vLLM.

## Overview

This project demonstrates a complete tool calling workflow:
- **MCP Server**: Exposes tools via HTTP using FastMCP
- **MCP Client**: Connects to both MCP server and LLM
- **Tool Integration**: LLM can intelligently call MCP tools when needed

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   User      │────────▶│   MCP Client │────────▶│  vLLM/LLM   │
│  (Chat)     │         │              │◀───────▶│ (OpenAI API)│
└─────────────┘         └──────┬───────┘         └─────────────┘
                               │
                               │ MCP Protocol
                               ▼
                        ┌──────────────┐
                        │  MCP Server  │
                        │  (FastMCP)   │
                        │  - Tools     │
                        └──────────────┘
```

## Components

### server.py
FastMCP server that exposes tools via HTTP streamable transport:
- **Transport**: `streamable-http` on `/mcp` endpoint
- **Host**: `0.0.0.0:8000`
- **Tool**: `add_numbers` - Adds two numbers and returns structured JSON

### client.py
MCP client that bridges LLM and MCP tools:
- Connects to MCP server via streamable-http
- Connects to LLM via OpenAI-compatible API
- Converts MCP tools to OpenAI format
- Intelligently includes tools based on query analysis
- Handles tool execution and response aggregation

## Setup

### Prerequisites

```bash
# Install Python dependencies
pip install mcp openai python-dotenv

# Set environment variables
export LLM_TOKEN=your_llm_token_here
```

Or create a `.env` file:
```env
LLM_TOKEN=your_llm_token_here
```

### Configuration

Edit `client.py` to configure your endpoints:

```python
client = MCPClient(
    "http://localhost:8000/mcp",           # MCP server URL
    "http://your-llm-host:port/v1"        # LLM endpoint (OpenAI-compatible)
)
```

## Usage

### Start the MCP Server

```bash
python server.py
```

Server will start on `http://0.0.0.0:8000/mcp`

### Run the Client

```bash
python client.py
```

### Example Interactions

**Math query (uses tool):**
```
You: Add 5 and 3
Assistant: [Tool Call] add_numbers({'a': 5, 'b': 3}) → {"operation": "addition", "operands": {"a": 5.0, "b": 3.0}, "result": 8.0, "success": true}
```

**General query (no tool):**
```
You: What is the capital of Texas?
Assistant: The capital of Texas is Austin. It is the state capital and the fourth-most populous city in the state...
```

## How It Works

1. **Tool Detection**: Client uses regex to detect if query needs tools (numbers, math keywords)
2. **Tool Conversion**: MCP tools are converted to OpenAI format with proper JSON Schema
3. **LLM Request**: Query sent to LLM with tools conditionally included
4. **Tool Execution**: If LLM returns tool calls, they are executed via MCP server
5. **Response Aggregation**: Tool results and text responses are combined

## Tool Format

**MCP Tool Definition:**
```python
@mcp.tool(
    name="add_numbers",
    description="Add two numbers together and return the sum",
    structured_output=True,
)
def add(a: float, b: float) -> Dict[str, Any]:
    return {
        "operation": "addition",
        "operands": {"a": a, "b": b},
        "result": a + b,
        "success": True,
    }
```

**Converted to OpenAI Format:**
```json
{
  "type": "function",
  "function": {
    "name": "add_numbers",
    "description": "Add two numbers together and return the sum",
    "parameters": {
      "type": "object",
      "properties": {
        "a": {"type": "number"},
        "b": {"type": "number"}
      },
      "required": ["a", "b"]
    }
  }
}
```

## Adding New Tools

To add a new tool to `server.py`:

```python
@mcp.tool(
    name="your_tool_name",
    description="What your tool does",
    structured_output=True,
)
def your_function(param1: str, param2: int) -> Dict[str, Any]:
    """Tool implementation"""
    return {
        "result": "your result",
        "success": True,
    }
```

The tool will automatically be available to the LLM after restarting the server.

## Troubleshooting

**404 Error from LLM:**
- Ensure `base_url` is set to the base URL (e.g., `http://host:port/v1`)
- The OpenAI client automatically appends `/chat/completions`

**Tool not being called:**
- Check the regex pattern in `process_query()` for tool detection
- Ensure tool description is clear and descriptive
- Verify LLM has tool-calling enabled

**MCP connection failed:**
- Ensure server is running on correct port
- Check firewall settings
- Verify MCP server URL is correct

## License

This is a demonstration/educational project.
