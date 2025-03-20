from mcp.server.fastmcp import FastMCP

def register_code_review_prompts(mcp: FastMCP) -> None:
    """Register code review related prompts with the MCP server."""
    
    @mcp.prompt()
    def review_code(code: str) -> str:
        return f"Please review this code:\n\n{code}"