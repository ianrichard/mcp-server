import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from llm_provider import LLMProvider


class LLMFactory:
    """Factory for creating LLM instances."""
    
    @staticmethod
    def load_env() -> None:
        """Load environment variables."""
        load_dotenv()
    
    @staticmethod
    def get_openai_key() -> Optional[str]:
        """Get OpenAI API key."""
        return os.getenv("OPENAI_API_KEY")
    
    @classmethod
    def create(
        cls, 
        model: str = LLMProvider.DEFAULT,
        temperature: float = 0.3,
        streaming: bool = True,
        **kwargs
    ) -> BaseChatModel:
        """Create an LLM instance based on the model name."""
        cls.load_env()
        
        if LLMProvider.is_openai(model):
            return cls._create_openai(model, temperature, streaming, **kwargs)
        else:
            return cls._create_ollama(model, temperature, streaming, **kwargs)
    
    @classmethod
    def _create_openai(
        cls, 
        model: str,
        temperature: float,
        streaming: bool,
        **kwargs
    ) -> BaseChatModel:
        """Create an OpenAI LLM instance."""
        api_key = kwargs.pop("api_key", None) or cls.get_openai_key()
        if not api_key:
            raise ValueError("OpenAI API key not found")
        
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
        base_url = kwargs.pop("base_url", "http://localhost:11434")
        
        return ChatOllama(
            model=model,
            temperature=temperature,
            streaming=streaming,
            base_url=base_url,
            **kwargs
        )