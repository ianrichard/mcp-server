from mcp.server.fastmcp import FastMCP
from pathlib import Path

def register_file_tools(mcp: FastMCP) -> None:
    """Register file-related tools with the MCP server."""
    
    @mcp.tool()
    def list_files(folder: str) -> list[str]:
        """
        List files from Desktop or Downloads folder.
        
        Args:
            folder: Either 'desktop' or 'downloads'
            
        Returns:
            List of filenames in the specified folder
        """
        home_dir = Path.home()
        
        # Only allow access to Desktop and Downloads folders
        if folder.lower() == 'desktop':
            target_dir = home_dir / 'Desktop'
        elif folder.lower() == 'downloads':
            target_dir = home_dir / 'Downloads'
        else:
            return ["Error: Only 'desktop' or 'downloads' folders are accessible"]
        
        # List files
        return [item.name for item in target_dir.iterdir() if item.is_file()]
    
    @mcp.tool()
    def read_file(folder: str, filename: str, max_chars: int = 10000) -> str:
        """
        Read the contents of a file from Desktop or Downloads folder.
        
        Args:
            folder: Either 'desktop' or 'downloads'
            filename: Name of the file to read
            max_chars: Maximum number of characters to read (default: 10000)
            
        Returns:
            Contents of the file or error message
        """
        home_dir = Path.home()
        
        # Only allow access to Desktop and Downloads folders
        if folder.lower() == 'desktop':
            target_dir = home_dir / 'Desktop'
        elif folder.lower() == 'downloads':
            target_dir = home_dir / 'Downloads'
        else:
            return "Error: Only 'desktop' or 'downloads' folders are accessible"
        
        file_path = target_dir / filename
        
        # Prevent path traversal attacks
        if not file_path.is_relative_to(target_dir):
            return "Error: Invalid filename"
        
        # Check if file exists
        if not file_path.is_file():
            return f"Error: File '{filename}' not found in {folder}"
        
        # Check file size to avoid loading huge files
        if file_path.stat().st_size > 1024 * 1024 * 10:  # 10MB limit
            return f"Error: File '{filename}' is too large (max 10MB)"
        
        try:
            # Try to read the file as text
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(max_chars)
                
            if len(content) == max_chars:
                content += f"\n... (file truncated, showing first {max_chars} characters)"
                
            return content
        except UnicodeDecodeError:
            return f"Error: File '{filename}' appears to be a binary file, not text"
        except Exception as e:
            return f"Error reading file: {str(e)}"