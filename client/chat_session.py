import asyncio
import sys
import json
from typing import List, Dict, Any
# Updated imports using the newer package structure
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models.chat_models import BaseChatModel

# Keep these as relative imports
from tool_client import MCPToolClient
from tool_handler import ToolHandler
from mcp_adapter_prompt import create_system_prompt
from console_formatter import ConsoleFormatter

class ChatSession:
    def __init__(
        self, 
        mcp_agent: MCPToolClient, 
        llm: BaseChatModel,  # Changed type hint to BaseChatModel for flexibility
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
        
    async def process_message(self, user_input: str, response_handler=None) -> None:
        """
        Process a user message and handle any tool requests.
        
        Args:
            user_input: The user input to process
            response_handler: Optional handler to collect output instead of printing
        """
        # Format and print user message if no response handler provided
        if not response_handler:
            ConsoleFormatter.format_user_message(user_input)
        
        self.messages.append(HumanMessage(content=user_input))
        
        tool_processing = True
        while tool_processing:
            if not response_handler:
                ConsoleFormatter.format_assistant_prefix()
            response_content = ""
            
            try:
                async for chunk in self.llm.astream(self.messages):
                    if hasattr(chunk, "content") and chunk.content:
                        if response_handler:
                            response_handler.add_content(chunk.content)
                        else:
                            ConsoleFormatter.format_assistant_chunk(chunk.content)
                        response_content += chunk.content
                        
                if not response_handler:
                    ConsoleFormatter.format_assistant_complete()
                
                self.messages.append(AIMessage(content=response_content))
                
                should_continue = await self.tool_handler.extract_and_process_tool_request(
                    response_content, 
                    self.messages,
                    response_handler=response_handler
                )
                
                # If we didn't find a tool request that needs continued processing, exit the tool loop
                if not should_continue:
                    tool_processing = False
                    
            except Exception as e:
                if response_handler:
                    response_handler.add_content(f"Error during streaming: {e}")
                else:
                    ConsoleFormatter.format_error(f"Error during streaming: {e}")
                tool_processing = False
                
        # Return the final response content if there's a response handler
        if response_handler:
            return response_handler.get_content()

    async def process_message_api(self, user_input: str, stream=False):
        """API-friendly version of process_message that can return content or stream it."""
        handler = APIResponseHandler()
        
        self.messages.append(HumanMessage(content=user_input))
        
        if stream:
            async def content_generator():
                tool_processing = True
                while tool_processing:
                    response_content = ""
                    
                    try:
                        async for chunk in self.llm.astream(self.messages):
                            if hasattr(chunk, "content") and chunk.content:
                                text = handler.add_content(chunk.content)
                                response_content += chunk.content
                                yield text
                        
                        self.messages.append(AIMessage(content=response_content))
                        
                        should_continue = await self.tool_handler.extract_and_process_tool_request(
                            response_content, 
                            self.messages,
                            response_handler=handler
                        )
                        
                        if not should_continue:
                            tool_processing = False
                            
                    except Exception as e:
                        error_text = handler.format_error(str(e))
                        yield error_text
                        tool_processing = False
            
            return content_generator()
        
        else:
            # Non-streaming version
            tool_processing = True
            while tool_processing:
                response_content = ""
                
                try:
                    async for chunk in self.llm.astream(self.messages):
                        if hasattr(chunk, "content") and chunk.content:
                            handler.add_content(chunk.content)
                            response_content += chunk.content
                    
                    self.messages.append(AIMessage(content=response_content))
                    
                    should_continue = await self.tool_handler.extract_and_process_tool_request(
                        response_content, 
                        self.messages,
                        response_handler=handler
                    )
                    
                    if not should_continue:
                        tool_processing = False
                        
                except Exception as e:
                    handler.format_error(str(e))
                    tool_processing = False
            
            return handler.get_content()

    async def astream_message(self, user_input: str, output_handler=None):
        """
        Process a user message and stream the response chunks.
        
        Args:
            user_input: The user input to process
            output_handler: Optional handler to collect output
        
        Yields:
            Content chunks as they are generated
        """
        # Add user message to history
        self.messages.append(HumanMessage(content=user_input))
        
        tool_processing = True
        while tool_processing:
            response_content = ""
            
            try:
                # Stream the initial LLM response
                async for chunk in self.llm.astream(self.messages):
                    if hasattr(chunk, "content") and chunk.content:
                        chunk_text = chunk.content
                        if output_handler:
                            output_handler.add_content(chunk_text)
                        response_content += chunk_text
                        yield chunk_text
                
                # Add the assistant's message to history
                self.messages.append(AIMessage(content=response_content))
                
                # Process any tool requests
                should_continue = await self.tool_handler.extract_and_process_tool_request(
                    response_content, 
                    self.messages,
                    response_handler=output_handler
                )
                
                if not should_continue:
                    tool_processing = False
                    
            except Exception as e:
                error_msg = f"Error in streaming: {str(e)}"
                if output_handler:
                    output_handler.add_content(error_msg)
                yield error_msg
                tool_processing = False

class APIResponseHandler:
    """Handles collecting API responses instead of console output."""
    def __init__(self):
        self.content = ""
    
    def add_content(self, text):
        self.content += text
        return text  # Return for streaming
    
    def format_user_message(self, text):
        pass  # Do nothing, we don't need formatting
    
    def format_assistant_prefix(self):
        pass
    
    def format_assistant_chunk(self, text):
        return text
    
    def format_assistant_complete(self):
        pass
    
    def format_error(self, text):
        return f"Error: {text}"
    
    def get_content(self):
        return self.content