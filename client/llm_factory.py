import os
import json
from typing import Optional, Dict, Any, Tuple
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from dotenv import load_dotenv


class LLMFactory:
    """Factory for creating LLM instances."""
    
    PROVIDER_OPENAI = "openai"
    PROVIDER_AZURE = "azure"
    PROVIDER_OLLAMA = "ollama"
    PROVIDER_GROQ = "groq"
    
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "llm_providers.json")
    
    _config = None
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Load the configuration from JSON file."""
        if cls._config is None:
            try:
                with open(cls.CONFIG_PATH, "r") as f:
                    cls._config = json.load(f)
            except FileNotFoundError:
                cls._config = {"providers": {}, "default_provider": "openai"}
        return cls._config
    
    @staticmethod
    def load_env() -> None:
        """Load environment variables."""
        load_dotenv()
    
    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> str:
        """Get provider name, falling back to default if not specified."""
        config = cls.load_config()
        if provider_name:
            return provider_name
        return config.get("default_provider", "openai")
    
    @classmethod
    def get_model(cls, provider: str, model_name: Optional[str] = None) -> str:
        """Get model name, falling back to provider's default if not specified."""
        config = cls.load_config()
        if provider not in config.get("providers", {}):
            raise ValueError(f"Provider '{provider}' not found in configuration")
        
        provider_config = config["providers"][provider]
        if model_name:
            if model_name not in provider_config.get("models", {}):
                raise ValueError(f"Model '{model_name}' not found for provider '{provider}'")
            return model_name
        
        return provider_config.get("default")
    
    @classmethod
    def get_model_id(cls, provider: str, model_name: str) -> str:
        """Get the actual model ID to use with the provider."""
        config = cls.load_config()
        if provider not in config.get("providers", {}):
            raise ValueError(f"Provider '{provider}' not found in configuration")
        
        provider_config = config["providers"][provider]
        if model_name not in provider_config.get("models", {}):
            raise ValueError(f"Model '{model_name}' not found for provider '{provider}'")
        
        return provider_config["models"][model_name]
    
    @classmethod
    def create(
        cls,
        model_info: Optional[Tuple[str, str]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        streaming: bool = True,
        **kwargs
    ) -> BaseChatModel:
        """Create an LLM instance based on the provider and model."""
        cls.load_env()
        
        if model_info:
            provider, model = model_info
        
        provider = cls.get_provider(provider)
        model = cls.get_model(provider, model)
        model_id = cls.get_model_id(provider, model)
        
        if provider == cls.PROVIDER_OPENAI:
            return cls._create_openai(model_id, temperature, streaming, **kwargs)
        elif provider == cls.PROVIDER_AZURE:
            return cls._create_azure(model, model_id, temperature, streaming, **kwargs)
        elif provider == cls.PROVIDER_OLLAMA:
            return cls._create_ollama(model_id, temperature, streaming, **kwargs)
        elif provider == cls.PROVIDER_GROQ:
            return cls._create_groq(model_id, temperature, streaming, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @classmethod
    def _create_openai(cls, model_id: str, temperature: float, streaming: bool, **kwargs) -> BaseChatModel:
        """Create an OpenAI LLM instance."""
        api_key = kwargs.pop("api_key", None) or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found")
        
        return ChatOpenAI(
            model=model_id,
            temperature=temperature,
            streaming=streaming,
            openai_api_key=api_key,
            **kwargs
        )
    
    @classmethod
    def _create_azure(cls, model_name: str, model_id: str, temperature: float, streaming: bool, **kwargs) -> BaseChatModel:
        """Create an Azure OpenAI LLM instance."""
        api_key = kwargs.pop("api_key", None) or os.getenv("AZURE_OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Azure OpenAI API key not found")
        
        endpoint = kwargs.pop("endpoint", None) or os.getenv("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            raise ValueError("Azure OpenAI endpoint not found")
        
        api_version = kwargs.pop("api_version", None) or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15")
        deployment_name = kwargs.pop("deployment_name", model_name)
        
        return AzureChatOpenAI(
            deployment_name=deployment_name,
            model=model_id,
            openai_api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
            temperature=temperature,
            streaming=streaming,
            **kwargs
        )
    
    @classmethod
    def _create_ollama(cls, model_id: str, temperature: float, streaming: bool, **kwargs) -> BaseChatModel:
        """Create an Ollama LLM instance."""
        base_url = kwargs.pop("base_url", "http://localhost:11434")
        
        return ChatOllama(
            model=model_id,
            temperature=temperature,
            streaming=streaming,
            base_url=base_url,
            **kwargs
        )
    
    @classmethod
    def _create_groq(cls, model_id: str, temperature: float, streaming: bool, **kwargs) -> BaseChatModel:
        """Create a Groq LLM instance."""
        api_key = kwargs.pop("api_key", None) or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Groq API key not found")
        
        return ChatGroq(
            model=model_id,
            temperature=temperature,
            streaming=streaming,
            groq_api_key=api_key,
            **kwargs
        )
    
    # Convenience methods for specific providers
    @classmethod
    def openai(cls, model: str = None, **kwargs) -> BaseChatModel:
        """Create an OpenAI LLM instance."""
        return cls.create(provider=cls.PROVIDER_OPENAI, model=model, **kwargs)
    
    @classmethod
    def azure(cls, model: str = None, **kwargs) -> BaseChatModel:
        """Create an Azure OpenAI LLM instance."""
        return cls.create(provider=cls.PROVIDER_AZURE, model=model, **kwargs)
    
    @classmethod
    def ollama(cls, model: str = None, **kwargs) -> BaseChatModel:
        """Create an Ollama LLM instance."""
        return cls.create(provider=cls.PROVIDER_OLLAMA, model=model, **kwargs)
    
    @classmethod
    def groq(cls, model: str = None, **kwargs) -> BaseChatModel:
        """Create a Groq LLM instance."""
        return cls.create(provider=cls.PROVIDER_GROQ, model=model, **kwargs)