import asyncio
import sys
import json
from typing import List, Dict, Any, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

from tool_client import MCPToolClient
from tool_handler import ToolHandler
from mcp_adapter_prompt import create_system_prompt
from console_formatter import ConsoleFormatter

class ChatSession:
    def __init__(
        self, 
        mcp_agent: MCPToolClient, 
        llm: ChatOpenAI,
        tool_names: List[str]
    ):
        """Initialize a chat session."""
        self.mcp_agent = mcp_agent
        self.llm = llm.with_config({"streaming": True})
        self.tool_names = tool_names
        self.tool_handler = ToolHandler(mcp_agent)
        self.system_prompt = create_system_prompt(tool_names)
        self.messages = [SystemMessage(content=self.system_prompt)]
        
        # Format and print system prompt
        ConsoleFormatter.format_system_prompt(self.system_prompt)
        
    async def process_message(self, user_input: str) -> None:
        """Process a user message and handle any tool requests."""
        # Format and print user message
        ConsoleFormatter.format_user_message(user_input)
        
        self.messages.append(HumanMessage(content=user_input))
        
        tool_processing = True
        while tool_processing:
            ConsoleFormatter.format_assistant_prefix()
            response_content = ""
            
            try:
                async for chunk in self.llm.astream(self.messages):
                    if hasattr(chunk, "content") and chunk.content:
                        ConsoleFormatter.format_assistant_chunk(chunk.content)
                        response_content += chunk.content
                ConsoleFormatter.format_assistant_complete()
                
                self.messages.append(AIMessage(content=response_content))
                
                should_continue = await self.tool_handler.extract_and_process_tool_request(
                    response_content, 
                    self.messages
                )
                
                # If we didn't find a tool request that needs continued processing, exit the tool loop
                if not should_continue:
                    tool_processing = False
                    
            except Exception as e:
                ConsoleFormatter.format_error(f"Error during streaming: {e}")
                tool_processing = False