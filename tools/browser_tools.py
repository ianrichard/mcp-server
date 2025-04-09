import asyncio
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse

import markdownify
import readabilipy.simple_json
from mcp.server.fastmcp import FastMCP

DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; MCPClient/1.0; +https://github.com/yourusername/mcp-server)"

def extract_content_from_html(html: str) -> str:
    """Extract and convert HTML content to Markdown format.

    Args:
        html: Raw HTML content to process

    Returns:
        Simplified markdown version of the content
    """
    try:
        ret = readabilipy.simple_json.simple_json_from_html_string(
            html, use_readability=True
        )
        if not ret or not ret.get("content"):
            return "<error>Page failed to be simplified from HTML</error>"
        
        content = markdownify.markdownify(
            ret["content"],
            heading_style=markdownify.ATX,
        )
        return content
    except Exception as e:
        return f"<error>Error extracting content: {str(e)}</error>"


def get_robots_txt_url(url: str) -> str:
    """Get the robots.txt URL for a given website URL."""
    parsed = urlparse(url)
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    return robots_url


async def check_robots_txt(url: str, user_agent: str) -> bool:
    """Check if the URL can be fetched by the user agent according to robots.txt."""
    import httpx
    from protego import Protego

    robot_txt_url = get_robots_txt_url(url)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                robot_txt_url,
                follow_redirects=True,
                headers={"User-Agent": user_agent},
                timeout=10.0
            )
            
            if response.status_code in (401, 403):
                return False
            elif 400 <= response.status_code < 500:
                return True  # No robots.txt or can't retrieve it, assume allowed
                
            robot_txt = response.text
            processed_robot_txt = "\n".join(
                line for line in robot_txt.splitlines() if not line.strip().startswith("#")
            )
            robot_parser = Protego.parse(processed_robot_txt)
            return robot_parser.can_fetch(url, user_agent)
    except Exception:
        return True  # If there's any error checking robots.txt, assume it's allowed


async def fetch_url(url: str, user_agent: str, force_raw: bool = False) -> Tuple[str, str]:
    """Fetch URL content and return as markdown or raw HTML."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            follow_redirects=True,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            timeout=30.0
        )
        
        if response.status_code >= 400:
            return f"Error: Failed to fetch {url} - status code {response.status_code}", ""

        page_raw = response.text
        content_type = response.headers.get("content-type", "")
        
        is_page_html = (
            "<html" in page_raw[:100] or "text/html" in content_type or not content_type
        )

        if is_page_html and not force_raw:
            return extract_content_from_html(page_raw), ""
            
        return (
            page_raw,
            f"Content type {content_type} cannot be simplified to markdown, here is the raw content:\n"
        )


def register_browser_tools(mcp: FastMCP) -> None:
    """Register browser-related tools with the MCP server."""
    
    @mcp.tool()
    async def fetch_page(url: str, raw_html: bool = False, max_chars: int = 10000, check_robots: bool = True) -> str:
        """
        Fetch a webpage and convert it to markdown (or get raw HTML).
        
        Args:
            url: The URL to fetch
            raw_html: If True, return raw HTML instead of markdown
            max_chars: Maximum number of characters to return (default: 10000)
            check_robots: Whether to respect robots.txt restrictions (default: True)
            
        Returns:
            Web page content as markdown (or HTML if raw_html=True)
        """
        import httpx
        
        # Basic URL validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return "Error: Invalid URL. Must include scheme (e.g., http://, https://)"
        
        try:
            # Check robots.txt if requested
            if check_robots:
                allowed = await check_robots_txt(url, DEFAULT_USER_AGENT)
                if not allowed:
                    return (
                        f"Error: The site's robots.txt at {get_robots_txt_url(url)} does not allow fetching this page.\n"
                        f"You can try setting check_robots=False if you believe this is a public page."
                    )
            
            # Fetch the content
            content, prefix = await fetch_url(url, DEFAULT_USER_AGENT, force_raw=raw_html)
            
            # Limit content size
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n\n... (content truncated at {max_chars} characters)"
            
            return f"{prefix}Contents of {url}:\n\n{content}"
                
        except httpx.HTTPStatusError as e:
            return f"Error: HTTP status code {e.response.status_code} when fetching {url}"
        except httpx.RequestError as e:
            return f"Error: Failed to fetch {url} - {str(e)}"
        except Exception as e:
            return f"Error: An unexpected error occurred: {str(e)}"
    
    @mcp.tool()
    async def search_web(query: str, max_results: int = 5) -> str:
        """
        Search the web for information (placeholder - requires API key setup).
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Search results as text
        """
        # This is a placeholder that would need to be implemented with a search API
        return (
            "Note: Web search functionality requires setup with a search API provider.\n"
            "To implement this feature, you would need to integrate with services like:\n"
            "- Google Custom Search API\n"
            "- Bing Search API\n"
            "- DuckDuckGo API\n\n"
            f"Your search query was: '{query}'"
        )