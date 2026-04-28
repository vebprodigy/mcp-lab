import asyncio
import os
import re
import json
from openai import OpenAI
from typing import Optional
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()  # Load ANTHROPIC_API_KEY from .env
class MCPClient:
    def __init__(self, server_url: str, llm_url: str):
        self.server_url = server_url
        self.llm_url = llm_url
        self.token = os.getenv("LLM_TOKEN")
        # Initialize OpenAI client for vLLM (OpenAI-compatible)
        self.openai_client = OpenAI(
            base_url=llm_url,
            api_key=self.token,
        )
        self.session: Optional[ClientSession] = None
        self.tools = []
        self.client_context = None
        self.session_context = None

    async def connect(self):
        # Connect to the streamable HTTP server
        self.client_context = streamable_http_client(self.server_url)
        read_stream, write_stream, _ = await self.client_context.__aenter__()
        # Create a session using the client streams
        self.session_context = ClientSession(read_stream, write_stream)
        self.session = await self.session_context.__aenter__()
        await self.session.initialize()
        resp = await self.session.list_tools()
        self.tools = self._convert_mcp_to_openai_tools(resp.tools)
        print("✅ Connected: Tools available =", [t["function"]["name"] for t in self.tools])

    def _convert_mcp_to_openai_tools(self, mcp_tools):
        """Convert MCP tool format to OpenAI-compatible tool format"""
        openai_tools = []
        for t in mcp_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema,
                }
            })
        return openai_tools

    async def process_query(self, query: str) -> str:
        # Check if query mentions numbers/math operations
        needs_tool = bool(re.search(r'\d+.*\d+|add|sum|plus|calculate', query.lower()))

        # Send message to vLLM using OpenAI client
        create_kwargs = {
            "model": "llama4-maverick",
            "messages": [{"role": "user", "content": query}],
            "max_tokens": 5000,
        }
        if needs_tool:
            create_kwargs["tools"] = self.tools
        llm_resp = self.openai_client.chat.completions.create(**create_kwargs)

        # Convert OpenAI response to JSON for pretty printing
        llm_resp_dict = llm_resp.model_dump()
        print("LLM Response:", json.dumps(llm_resp_dict, indent=2))

        output = []
        message = llm_resp.choices[0].message
        
        # Handle text content
        if message.content:
            output.append(message.content)
        
        # Handle tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = tool_call.function.arguments
                # Parse arguments (OpenAI client returns JSON string)
                args = json.loads(args)
                result = await self.session.call_tool(name, args)
                output.append(f"[Tool Call] {name}({args}) → {result.content!r}")
        
        return "\n".join(output)

    async def chat_loop(self):
        print("💬 Ask questions (type 'exit' to quit):")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            response = await self.process_query(user_input)
            print("Assistant:", response)

    async def close(self):
        if self.session_context:
            await self.session_context.__aexit__(None, None, None)
        if self.client_context:
            await self.client_context.__aexit__(None, None, None)

async def main():
    client = MCPClient("http://localhost:8000/mcp", "http://10.239.41.81:8001/v1")
    try:
        await client.connect()
        # Direct test
        #print(await client.process_query("Add 23 and 56.67"))
        # Optionally enable chat
        await client.chat_loop()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())