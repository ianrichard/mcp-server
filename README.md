# MCP Dev Server UI

`mcp dev main.py`

http://127.0.0.1:6274/#tools


# Chat Client
`python client/client.py`

# Client Usage Options

```python
llm = LLMFactory.ollama()
llm = LLMFactory.openai()
llm = LLMFactory.azure() 
llm = LLMFactory.groq()  

llm = LLMFactory.openai("gpt-4o")
llm = LLMFactory.groq("llama-3.3-70b")
```