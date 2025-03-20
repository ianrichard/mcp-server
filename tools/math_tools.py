from mcp.server.fastmcp import FastMCP

def register_math_tools(mcp: FastMCP) -> None:
    """Register math-related tools with the MCP server."""
    
    @mcp.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b