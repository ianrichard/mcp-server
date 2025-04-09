import asyncio
import os
from dotenv import load_dotenv

from tool_client import MCPToolClient
from chat_session import ChatSession
from llm_factory import LLMFactory
from console_formatter import ConsoleFormatter

load_dotenv()

async def main():
    mcp_agent = None
    try:
        mcp_agent = MCPToolClient("main.py")
        await mcp_agent.connect()

        tool_names = await mcp_agent.get_tool_names()

        # llm = LLMFactory.ollama()
        # llm = LLMFactory.openai()
        # llm = LLMFactory.azure() 
        llm = LLMFactory.groq()  

        # llm = LLMFactory.openai("gpt-4o")
        # llm = LLMFactory.groq("llama-3.3-70b")
        
        chat_session = ChatSession(mcp_agent, llm, tool_names)

        while True:
            # Get input without the horizontal rule
            print("\nYou: ", end="", flush=True)
            user_input = input()

            # Check for exit command
            if user_input.lower() in ("exit", "quit"):
                break

            # Clear the "You: [input]" line
            print("\033[1A\033[2K", end="")  # Move up 1 line and clear it

            await chat_session.process_message(user_input)

    except Exception as e:
        ConsoleFormatter.format_error(f"An error occurred: {e}")

    finally:
        if mcp_agent:
            await mcp_agent.close()


if __name__ == "__main__":
    asyncio.run(main())