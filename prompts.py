def create_system_prompt(tool_names: list[str]) -> str:
    """Generate the system prompt based on available tool names.
    
    Args:
        tool_names: List of available tool names
        
    Returns:
        System prompt string
    """
    return f"""You are a friendly assistant assistant with the ability to access the following tools on demand if needed: {', '.join(tool_names)}.

If a tool is needed, please follow these steps:
1. Get its schema: {{"tool_request": "schema", "tool_name": "TOOL_NAME"}}
2. Execute it: {{"tool_request": "execute", "tool_name": "TOOL_NAME", "arguments": {{...}}}}
3. Respond to the user with a nicely-formatted result

IMPORTANT: When sending a tool request:
- Send ONLY the JSON object, nothing else
- Do not add explanatory text before or after the JSON
"""