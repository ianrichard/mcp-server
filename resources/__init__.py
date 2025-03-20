from mcp.server.fastmcp import FastMCP

def register_resources(mcp: FastMCP) -> None:
    """Register all resources with the MCP server."""
    from .greetings import register_greeting_resources
    register_greeting_resources(mcp)