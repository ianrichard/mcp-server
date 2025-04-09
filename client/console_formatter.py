from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
import json
from typing import Any, Dict, List

class ConsoleFormatter:
    """Utility for formatting console output with chat-like styling using Rich."""
    
    # Create a console instance with a small right margin
    console = Console(width=Console().width - 4)  # Add 4 character margin
    
    # Define styles for different message types
    USER_STYLE = "bold blue"
    ASSISTANT_STYLE = "bold green"
    SYSTEM_STYLE = "bold cyan"
    TOOL_STYLE = "bold yellow"
    ERROR_STYLE = "bold red"
    
    # Buffer for collecting assistant message chunks
    _assistant_buffer = []
    _live_display = None
    
    @staticmethod
    def format_system_prompt(content: str) -> None:
        """Format and print system prompt with distinctive styling."""
        ConsoleFormatter.console.print()
        ConsoleFormatter.console.print("SYSTEM PROMPT", style=ConsoleFormatter.SYSTEM_STYLE)
        ConsoleFormatter.console.print(Panel(content, border_style="cyan"))
    
    @staticmethod
    def format_user_message(content: str) -> None:
        """Format and print user message as a chat bubble with Markdown support."""
        ConsoleFormatter.console.print()
        ConsoleFormatter.console.print("You:", style=ConsoleFormatter.USER_STYLE)
        ConsoleFormatter.console.print(Panel(Markdown(content), border_style="blue"))
    
    @staticmethod
    def format_assistant_prefix() -> None:
        """Print assistant prefix and prepare for streaming."""
        ConsoleFormatter.console.print()
        ConsoleFormatter.console.print("Assistant:", style=ConsoleFormatter.ASSISTANT_STYLE)
        
        # Clear the buffer for a new message
        ConsoleFormatter._assistant_buffer = []
        
        # Start with an empty Panel that will be updated
        ConsoleFormatter._live_display = Live(
            Panel("", border_style="green"),
            console=ConsoleFormatter.console,
            refresh_per_second=10,  # Update frequently
            auto_refresh=True
        )
        ConsoleFormatter._live_display.start()
    
    @staticmethod
    def format_assistant_chunk(chunk: str) -> None:
        """Collect a chunk from the assistant and update the live display."""
        # Add to the buffer
        ConsoleFormatter._assistant_buffer.append(chunk)
        
        # Get the complete message so far
        current_message = "".join(ConsoleFormatter._assistant_buffer)
        
        # Update the panel content
        if ConsoleFormatter._live_display:
            ConsoleFormatter._live_display.update(
                Panel(Text(current_message), border_style="green")
            )
    
    @staticmethod
    def format_assistant_complete() -> None:
        """Complete assistant output by finalizing the panel with markdown formatting."""
        # Get the complete message from the buffer
        complete_message = "".join(ConsoleFormatter._assistant_buffer)
        
        # Final update with markdown rendering
        if ConsoleFormatter._live_display:
            ConsoleFormatter._live_display.update(
                Panel(Markdown(complete_message), border_style="green")
            )
            
            # Stop the live display
            ConsoleFormatter._live_display.stop()
            ConsoleFormatter._live_display = None
        
        # Clear the buffer
        ConsoleFormatter._assistant_buffer = []
    
    @staticmethod
    def format_tool_request(tool_name: str, request_data: Any) -> None:
        """Format and print a tool request with distinctive styling."""
        ConsoleFormatter.console.print()
        ConsoleFormatter.console.print(f"🔧 Tool Request: {tool_name}", style=ConsoleFormatter.TOOL_STYLE)
        
        # Convert request data to formatted string
        if isinstance(request_data, dict):
            content = json.dumps(request_data, indent=2)
        else:
            content = str(request_data)
            
        ConsoleFormatter.console.print(Panel(content, border_style="yellow"))
    
    @staticmethod
    def format_tool_response(tool_name: str, response_data: Any) -> None:
        """Format and print a tool response with distinctive styling."""
        ConsoleFormatter.console.print()
        ConsoleFormatter.console.print(f"🔄 Tool Response: {tool_name}", style=ConsoleFormatter.TOOL_STYLE)
        
        # Convert response data to formatted string
        if isinstance(response_data, dict):
            content = json.dumps(response_data, indent=2)
        else:
            content = str(response_data)
            
        ConsoleFormatter.console.print(Panel(content, border_style="yellow"))
    
    @staticmethod
    def format_error(message: str) -> None:
        """Format and print an error message with distinctive styling."""
        ConsoleFormatter.console.print()
        ConsoleFormatter.console.print("❌ ERROR", style=ConsoleFormatter.ERROR_STYLE)
        ConsoleFormatter.console.print(Panel(message, border_style="red"))