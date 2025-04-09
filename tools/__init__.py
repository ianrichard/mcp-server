from mcp.server.fastmcp import FastMCP

def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    from .file_tools import register_file_tools
    from .math_tools import register_math_tools
    from .browser_tools import register_browser_tools
    
    register_file_tools(mcp)
    register_math_tools(mcp)
    register_browser_tools(mcp)