import os
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
# Fix the import to use the correct package
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

class LLMProviders:
    """Constants for supported LLM providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    # Add more providers as needed

class Models:
    """Constants for model names."""
    # OpenAI models
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"
    GPT4O = "gpt-4o"
    GPT35_TURBO = "gpt-3.5-turbo"
    
    # Ollama models
    LLAMA2 = "llama2"
    LLAMA3 = "llama3"
    LLAMA3_2 = "llama3.2"
    MISTRAL = "mistral"
    MIXTRAL = "mixtral"

class LLMFactory:
    """Factory for creating LLM instances with different providers."""
    
    @staticmethod
    def load_env() -> None:
        """Load environment variables."""
        load_dotenv()
    
    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        key_mapping = {
            LLMProviders.OPENAI: "OPENAI_API_KEY",
            # Ollama runs locally without API key
        }
        
        if provider in key_mapping:
            return os.getenv(key_mapping[provider])
        return None
    
    @classmethod
    def create(
        cls, 
        model: str = Models.GPT4O,
        temperature: float = 0.7,
        streaming: bool = True,
        **kwargs
    ) -> BaseChatModel:
        """Create an LLM instance based on the model name."""
        cls.load_env()
        
        # Determine provider from model name
        if model.startswith("gpt"):
            return cls._create_openai(model, temperature, streaming, **kwargs)
        elif model in [Models.LLAMA2, Models.LLAMA3, Models.LLAMA3_2, Models.MISTRAL, Models.MIXTRAL]:
            return cls._create_ollama(model, temperature, streaming, **kwargs)
        else:
            # Default to OpenAI
            return cls._create_openai(model, temperature, streaming, **kwargs)
    
    @classmethod
    def _create_openai(
        cls, 
        model: str,
        temperature: float,
        streaming: bool,
        **kwargs
    ) -> BaseChatModel:
        """Create an OpenAI LLM instance."""
        api_key = kwargs.pop("api_key", None) or cls.get_api_key(LLMProviders.OPENAI)
        if not api_key:
            raise ValueError(f"API key for {LLMProviders.OPENAI} not found")
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            streaming=streaming,
            openai_api_key=api_key,
            **kwargs
        )
    
    @classmethod
    def _create_ollama(
        cls, 
        model: str,
        temperature: float,
        streaming: bool,
        **kwargs
    ) -> BaseChatModel:
        """Create an Ollama LLM instance."""
        # Default to localhost, but allow override through kwargs
        base_url = kwargs.pop("base_url", "http://localhost:11434")
        
        return ChatOllama(
            model=model,
            temperature=temperature,
            streaming=streaming,
            base_url=base_url,
            **kwargs
        )