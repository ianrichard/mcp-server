import asyncio
import os
from dotenv import load_dotenv

from tool_agent import MCPToolAgent
from chat_session import ChatSession
from llm_factory import LLMFactory
from llm_provider import LLMProvider

load_dotenv()

async def main():
    mcp_agent = None
    try:
        mcp_agent = MCPToolAgent("server.py")
        await mcp_agent.connect()
        
        tool_names = await mcp_agent.get_tool_names()
        print(f"Available tools: {', '.join(tool_names)}")
        
        llm = LLMFactory.create(
            model=LLMProvider.OLLAMA.DEFAULT,
            temperature=0.7,
            streaming=True
        )
        
        chat_session = ChatSession(mcp_agent, llm, tool_names)
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ("exit", "quit"):
                break
                
            await chat_session.process_message(user_input)
    
    finally:
        if mcp_agent:
            await mcp_agent.close()


if __name__ == "__main__":
    asyncio.run(main())