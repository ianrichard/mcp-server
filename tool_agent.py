import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

class MCPToolAgent:
    def __init__(self, server_path: str):
        """Initialize MCP Tool Agent with path to server script."""
        self.server_path = server_path
        self.session = None
        self.tools_cache = {}  # Cache tool schemas after fetching them
        self.exit_stack = AsyncExitStack()
        self.read_stream = None
        self.write_stream = None

    async def connect(self):
        """Connect to the MCP server."""
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "--with", "mcp[cli]", "mcp", "run", self.server_path],
            env=None,
        )
        
        try:
            # Use the exit_stack to properly manage async context managers
            self.read_stream, self.write_stream = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.read_stream, self.write_stream))
            await self.session.initialize()
            print("Connected to MCP server successfully!")
        except Exception as e:
            # Make sure to clean up on error
            await self.close()
            raise RuntimeError(f"Failed to connect to MCP server: {e}") from e

    async def get_tool_names(self) -> List[str]:
        """Get a list of available tool names."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        tools_result = await self.session.list_tools()
        return [tool.name for tool in tools_result.tools]

    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed schema for a specific tool."""
        if tool_name in self.tools_cache:
            return self.tools_cache[tool_name]
            
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        tools_result = await self.session.list_tools()
        
        # Find the requested tool
        for tool in tools_result.tools:
            if tool.name == tool_name:
                schema = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
                self.tools_cache[tool_name] = schema
                return schema
                
        raise ValueError(f"Tool '{tool_name}' not found")

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with the given arguments."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        result = await self.session.call_tool(tool_name, arguments)
        
        # Handle different return types
        if hasattr(result, 'content'):
            if all(hasattr(item, 'text') for item in result.content):
                return [item.text for item in result.content]
            return result.content
        
        return result

    async def close(self):
        """Close the connection to the MCP server."""
        if self.exit_stack:
            await self.exit_stack.aclose()
            self.session = None
            self.read_stream = None
            self.write_stream = None