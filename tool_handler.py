import json
from typing import Any, Dict, List, Tuple
from langchain_core.messages import SystemMessage, BaseMessage

from tool_agent import MCPToolAgent

class ToolHandler:
    def __init__(self, mcp_agent: MCPToolAgent):
        """Initialize a tool handler with an MCP agent."""
        self.mcp_agent = mcp_agent
        
    async def extract_and_process_tool_request(
        self, 
        assistant_message: str, 
        messages: List[BaseMessage]
    ) -> Tuple[bool, bool]:
        """Extract and process a tool request from an assistant message.
        
        Args:
            assistant_message: The message from the assistant
            messages: The current message history
            
        Returns:
            Tuple of (is_tool_request, should_continue)
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
                                system_message = f"Tool schema for {tool_name}: {json.dumps(schema)}"
                                messages.append(SystemMessage(content=system_message))
                                print(f"\nSystem: {system_message}")
                                # Continue the loop to process the schema
                                return True, True
                            except Exception as e:
                                error_message = f"Error getting schema: {str(e)}"
                                messages.append(SystemMessage(content=error_message))
                                print(f"\nSystem: {error_message}")
                                # Continue to get a new response
                                return True, True
                                
                        elif tool_request["tool_request"] == "execute":
                            # Execute tool
                            tool_name = tool_request["tool_name"]
                            arguments = tool_request["arguments"]
                            
                            try:
                                result = await self.mcp_agent.execute_tool(tool_name, arguments)
                                system_message = f"Tool execution result: {json.dumps(result)}"
                                messages.append(SystemMessage(content=system_message))
                                print(f"\nSystem: {system_message}")
                                # Continue the loop to process the result
                                return True, True
                            except Exception as e:
                                error_message = f"Error executing tool: {str(e)}"
                                messages.append(SystemMessage(content=error_message))
                                print(f"\nSystem: {error_message}")
                                # Continue to get a new response
                                return True, True
                except json.JSONDecodeError:
                    # Not a valid JSON
                    pass
            
            # If we got here, it's not a tool request
            return False, False
                
        except Exception as e:
            print(f"Error in tool request extraction: {e}")
            return False, False