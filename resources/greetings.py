from mcp.server.fastmcp import FastMCP

def register_greeting_resources(mcp: FastMCP) -> None:
    """Register greeting related resources with the MCP server."""
    
    @mcp.resource("greeting://{name}")
    def get_greeting(name: str) -> str:
        """Get a personalized greeting"""
        return f"Hello, {name}!"