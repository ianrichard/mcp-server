import asyncio
import json
import os
import time
import uuid
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Add the client directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "client"))

# Now you can import from the client directory directly
from tool_client import MCPToolClient
from chat_session import ChatSession
from llm_factory import LLMFactory
from console_formatter import ConsoleFormatter

# Disable console output for API server
ConsoleFormatter.enabled = False

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    await get_mcp_client()
    yield
    # Shutdown code
    global mcp_client
    if mcp_client:
        await mcp_client.close()

app = FastAPI(title="LLM API Server", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False
    max_tokens: Optional[int] = None

# Global MCP client
mcp_client = None
active_sessions = {}

async def get_mcp_client():
    global mcp_client
    if mcp_client is None:
        mcp_client = MCPToolClient("main.py")
        await mcp_client.connect()
    return mcp_client

def parse_model_string(model_string: str):
    """Parse provider/model format or just use model name."""
    parts = model_string.split("/", 1)
    if len(parts) == 2:
        provider, model_name = parts
    else:
        # Default to groq if no provider specified
        provider, model_name = "groq", parts[0]
    
    return provider, model_name

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # Parse the model string to get provider and model
    provider, model_name = parse_model_string(request.model)
    
    # Convert openai-style messages to our format
    messages = []
    for msg in request.messages:
        if msg.role == "system":
            # Skip system message - we'll use our own system prompt with tool definitions
            continue
        elif msg.role == "user":
            messages.append({"role": "user", "content": msg.content})
        elif msg.role == "assistant":
            messages.append({"role": "assistant", "content": msg.content})
    
    # Get the last user message
    last_user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), None)
    if not last_user_message:
        return {"error": "No user message found"}
    
    # Get MCP client and tool names
    client = await get_mcp_client()
    tool_names = await client.get_tool_names()
    
    # Create appropriate LLM based on provider
    temperature = request.temperature or 0.7
    if provider == "openai":
        llm = LLMFactory.openai(model_name, temperature=temperature)
    elif provider == "azure":
        llm = LLMFactory.azure(model_name, temperature=temperature)
    elif provider == "ollama":
        llm = LLMFactory.ollama(model_name, temperature=temperature)
    elif provider == "groq":
        llm = LLMFactory.groq(model_name, temperature=temperature)
    else:
        return {"error": f"Unsupported provider: {provider}"}
    
    # Create a chat session
    session = ChatSession(client, llm, tool_names)
    
    # Handle streaming response
    if request.stream:
        return StreamingResponse(
            stream_response(session, last_user_message, request.model),
            media_type="text/event-stream"
        )
    
    # Non-streaming response
    try:
        # Create a response handler
        class ResponseCollector:
            def __init__(self):
                self.content = ""
            
            def add_content(self, text):
                self.content += text
                return text
                
            def get_content(self):
                return self.content
        
        response_collector = ResponseCollector()
        
        # Process the message with the output handler
        final_response = await session.process_message(
            last_user_message, 
            response_handler=response_collector
        )
        
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": final_response or response_collector.get_content()
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(last_user_message) // 4,  # Rough estimate
                "completion_tokens": len(final_response or response_collector.get_content()) // 4,  # Rough estimate
                "total_tokens": (len(last_user_message) + len(final_response or response_collector.get_content())) // 4  # Rough estimate
            }
        }
    except Exception as e:
        return {
            "error": {
                "message": str(e),
                "type": "internal_error"
            }
        }

async def stream_response(session, user_message, model_name):
    """Stream the response in OpenAI format."""
    import time
    import json
    import uuid
    
    # Create a response collector
    class StreamingResponseCollector:
        def __init__(self):
            self.content = ""
        
        def add_content(self, text):
            self.content += text
            return text
            
        def get_content(self):
            return self.content
    
    collector = StreamingResponseCollector()
    
    # Initial chunk with role
    yield f"data: {json.dumps({'id': f'chatcmpl-{uuid.uuid4()}', 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': model_name, 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]})}\n\n"
    
    try:
        # Process the message
        async for chunk in session.astream_message(user_message, output_handler=collector):
            if chunk:
                yield f"data: {json.dumps({'id': f'chatcmpl-{uuid.uuid4()}', 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': model_name, 'choices': [{'index': 0, 'delta': {'content': chunk}, 'finish_reason': None}]})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'id': f'chatcmpl-{uuid.uuid4()}', 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': model_name, 'choices': [{'index': 0, 'delta': {'content': f'Error: {str(e)}'}, 'finish_reason': 'error'}]})}\n\n"
    
    # Final chunk
    yield f"data: {json.dumps({'id': f'chatcmpl-{uuid.uuid4()}', 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': model_name, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
    yield "data: [DONE]\n\n"

class ResponseCollector:
    """Collects response content instead of printing it."""
    def __init__(self):
        self.content = ""
    
    def add_content(self, text):
        self.content += text
    
    def get_content(self):
        return self.content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)