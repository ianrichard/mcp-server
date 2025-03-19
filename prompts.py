def create_system_prompt(tool_names: list[str]) -> str:
    """Generate the system prompt based on available tool names.
    
    Args:
        tool_names: List of available tool names
        
    Returns:
        System prompt string
    """
    return f"""You are an assistant with access to these tools: {', '.join(tool_names)}.

To use a tool:
1. First get its schema: {{"tool_request": "schema", "tool_name": "TOOL_NAME"}}
2. Then execute it: {{"tool_request": "execute", "tool_name": "TOOL_NAME", "arguments": {{...}}}}

IMPORTANT: When sending a tool request:
- Send ONLY the JSON object, nothing else
- Do not add explanatory text before or after the JSON
- Keep moving through all steps automatically

Example:
User asks to add numbers
Your response (exactly): {{"tool_request": "schema", "tool_name": "add"}}
After getting schema
Your response (exactly): {{"tool_request": "execute", "tool_name": "add", "arguments": {{"a": 5, "b": 7}}}}
"""