from mcp.server.fastmcp import FastMCP


from tools import register_tools
from prompts import register_prompts
from resources import register_resources

mcp = FastMCP("Demo")

register_tools(mcp)
register_prompts(mcp)
register_resources(mcp)
