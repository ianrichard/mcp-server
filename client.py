import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from tool_agent import MCPToolAgent
from chat_session import ChatSession

load_dotenv()

async def main():
    # Initialize MCP agent
    mcp_agent = None
    try:
        mcp_agent = MCPToolAgent("server.py")
        await mcp_agent.connect()
        
        # Get available tool names
        tool_names = await mcp_agent.get_tool_names()
        print(f"Available tools: {', '.join(tool_names)}")
        
        # Initialize LangChain OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            openai_api_key=api_key
        )
        
        # Create and initialize chat session
        chat_session = ChatSession(mcp_agent, llm, tool_names)
        await chat_session.initialize()
        
        # Chat loop
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ("exit", "quit"):
                break
                
            await chat_session.process_message(user_input)
    
    finally:
        # Ensure we always close the MCP connection
        if mcp_agent:
            await mcp_agent.close()


if __name__ == "__main__":
    asyncio.run(main())