import asyncio
import os
from dotenv import load_dotenv

from tool_agent import MCPToolAgent
from chat_session import ChatSession
from llm_factory import LLMFactory, Models

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
        
        # Use the factory to create an LLM - now with Llama 3.2
        llm = LLMFactory.create(
            # model=Models.LLAMA3_2,  # Use Llama 3.2 via Ollama
            model=Models.GPT4O,  # Use GPT-4 via OpenAI
            temperature=0.7,
            streaming=True
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