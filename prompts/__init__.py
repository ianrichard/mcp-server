from mcp.server.fastmcp import FastMCP

def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts with the MCP server."""
    from .code_review import register_code_review_prompts
    
    register_code_review_prompts(mcp)