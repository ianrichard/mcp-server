import asyncio
import sys
import json
from typing import List, Dict, Any, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

from tool_agent import MCPToolAgent
from tool_handler import ToolHandler
from prompts import create_system_prompt

class ChatSession:
    def __init__(
        self, 
        mcp_agent: MCPToolAgent, 
        llm: ChatOpenAI,
        tool_names: List[str]
    ):
        """Initialize a chat session."""
        self.mcp_agent = mcp_agent
        # Create streaming version - simple approach
        self.llm = llm.with_config({"streaming": True})
        self.tool_names = tool_names
        self.tool_handler = ToolHandler(mcp_agent)
        self.messages = [SystemMessage(content=create_system_prompt(tool_names))]
        
    async def initialize(self) -> None:
        """Initialize the chat session with a greeting."""
        # Add example user message and get initial response
        self.messages.append(HumanMessage(content="What tools do you have available?"))
        
        # Stream the initial response
        print("\nAssistant: ", end="", flush=True)
        response_content = ""
        async for chunk in self.llm.astream(self.messages):
            if hasattr(chunk, "content") and chunk.content:
                print(chunk.content, end="", flush=True)
                response_content += chunk.content
        
        # Add the full response to messages
        self.messages.append(AIMessage(content=response_content))
        print()  # Add newline
        
    async def process_message(self, user_input: str) -> None:
        """Process a user message and handle any tool requests."""
        self.messages.append(HumanMessage(content=user_input))
        
        # Continue processing until we get a non-tool-request response
        tool_processing = True
        while tool_processing:
            # Stream the response
            print("\nAssistant: ", end="", flush=True)
            response_content = ""
            
            try:
                # Use astream instead of ainvoke for streaming
                async for chunk in self.llm.astream(self.messages):
                    if hasattr(chunk, "content") and chunk.content:
                        print(chunk.content, end="", flush=True)
                        response_content += chunk.content
                print()  # Add newline
                
                # Add the full response to messages
                self.messages.append(AIMessage(content=response_content))
                
                # Check if the response is a tool request
                is_tool_request, should_continue = await self.tool_handler.extract_and_process_tool_request(
                    response_content, 
                    self.messages
                )
                
                if not should_continue:
                    tool_processing = False
                    
            except Exception as e:
                print(f"\nError during streaming: {e}", file=sys.stderr)
                tool_processing = False