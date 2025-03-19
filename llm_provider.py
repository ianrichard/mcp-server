class LLMProvider:
    """Base provider class with nested provider-specific model classes."""
    
    class OPENAI:
        """OpenAI models."""
        GPT4O = "gpt-4o"
        
        DEFAULT = GPT4O
    
    class OLLAMA:
        """Ollama models."""
        GEMMA3 = "gemma3"
        PHI = "phi4-mini"
        MISTRAL = "mistral:7b-instruct-v0.3-q4_0"
        LLAMA = "llama3.2"
        DEEPSEEK = "deepseek-r1:1.5b"
        
        DEFAULT = GEMMA3
    
    DEFAULT = OPENAI.DEFAULT
    
    @staticmethod
    def is_openai(model: str) -> bool:
        """Check if a model is from OpenAI."""
        return model in [
            LLMProvider.OPENAI.GPT4O,
        ]    