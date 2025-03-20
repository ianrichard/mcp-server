from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo")

from tools import register_tools
from prompts import register_prompts
from resources import register_resources

register_tools(mcp)
register_prompts(mcp)
register_resources(mcp)

if __name__ == "__main__":
    pass