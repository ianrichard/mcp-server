import json
from typing import Any, Dict, List, Tuple
from langchain_core.messages import SystemMessage, BaseMessage, ToolMessage

from tool_client import MCPToolClient

class ToolHandler:
    def __init__(self, mcp_agent: MCPToolClient):
        """Initialize a tool handler with an MCP agent."""
        self.mcp_agent = mcp_agent
        
    async def extract_and_process_tool_request(
        self, 
        assistant_message: str, 
        messages: List[BaseMessage]
    ) -> bool:  # Changed return type from Tuple[bool, bool] to just bool
        """Extract and process a tool request from an assistant message.
        
        Args:
            assistant_message: The message from the assistant
            messages: The current message history
            
        Returns:
            bool: should_continue (whether to continue processing the conversation)
        """
        try:
            # Try to parse JSON (might be embedded in text)
            json_start = assistant_message.find('{')
            json_end = assistant_message.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = assistant_message[json_start:json_end]
                try:
                    tool_request = json.loads(json_str)
                    
                    if "tool_request" in tool_request:
                        if tool_request["tool_request"] == "schema":
                            # Get and return tool schema
                            tool_name = tool_request["tool_name"]
                            try:
                                schema = await self.mcp_agent.get_tool_schema(tool_name)
                                print(f"\nMCP Schema sent to LLM: {json.dumps(schema, indent=2)}")
                                # Add clear instructions with the schema
                                schema_message = f"Use the following schema for tool '{tool_name}':\n{json.dumps(schema, indent=2)}"
                                # Use SystemMessage instead of ToolMessage
                                system_message = SystemMessage(
                                    content=schema_message
                                )
                                messages.append(system_message)
                                print(f"\nTool: Schema for {tool_name}")
                                # Continue the loop to process the schema
                                return True
                            except Exception as e:
                                error_message = f"Error getting schema: {str(e)}"
                                messages.append(SystemMessage(
                                    content=error_message
                                ))
                                print(f"\nTool Error: {error_message}")
                                # Continue to get a new response
                                return True
                                
                        elif tool_request["tool_request"] == "execute":
                            # Execute tool
                            tool_name = tool_request["tool_name"]
                            arguments = tool_request["arguments"]
                            
                            try:
                                result = await self.mcp_agent.execute_tool(tool_name, arguments)
                                # Add clear instructions with the result
                                result_message = f"This is the result of executing '{tool_name}':\n{json.dumps(result, indent=2)}"
                                # Use SystemMessage instead of ToolMessage
                                system_message = SystemMessage(
                                    content=result_message
                                )
                                messages.append(system_message)
                                print(f"\nTool: Execution of {tool_name}")
                                # Continue the loop to process the result
                                return True
                            except Exception as e:
                                error_message = f"Error executing tool: {str(e)}"
                                messages.append(SystemMessage(
                                    content=error_message
                                ))
                                print(f"\nTool Error: {error_message}")
                                # Continue to get a new response
                                return True
                except json.JSONDecodeError:
                    # Not a valid JSON
                    pass
            
            # If we got here, it's not a tool request, don't continue the tool loop
            return False
                
        except Exception as e:
            print(f"Error in tool request extraction: {e}")
            return False