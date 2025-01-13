from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import yaml
from dataclasses import dataclass
import requests

# Update imports to use Pydantic v2
from pydantic import BaseModel, Field

# LangChain imports
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import LLMResult

# Import specific model implementations
from langchain_ollama import OllamaLLM
from langchain_openai import OpenAI

# Define constants
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_LMSTUDIO_URL = "http://localhost:1234/v1"

@dataclass
class ModelConfig:
    """Configuration for a model."""
    provider: str
    model_name: str
    base_url: str
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    extra_params: Dict[str, Any] = None
    context_window: Optional[int] = 4096
    num_gpu: Optional[int] = None
    num_thread: Optional[int] = None
    repeat_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """Create ModelConfig from dictionary."""
        return cls(
            provider=data.get('provider'),
            model_name=data.get('model_name'),
            base_url=data.get('base_url'),
            temperature=data.get('temperature', 0.7),
            top_p=data.get('top_p', 0.9),
            max_tokens=data.get('max_tokens', 2048),
            context_window=data.get('context_window'),
            num_gpu=data.get('num_gpu'),
            num_thread=data.get('num_thread'),
            repeat_penalty=data.get('repeat_penalty'),
            frequency_penalty=data.get('frequency_penalty'),
            presence_penalty=data.get('presence_penalty'),
            stop=data.get('stop'),
            extra_params=data.get('extra_params', {})
        )

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def create_model(self, config: ModelConfig) -> BaseLanguageModel:
        """Create a language model instance based on configuration."""
        pass

    @abstractmethod
    def check_availability(self, config: ModelConfig) -> bool:
        """Check if the provider is available with given config."""
        pass

class OllamaProvider(BaseLLMProvider):
    """Ollama provider implementation using newer LangChain integration."""
    
    def create_model(self, config: ModelConfig) -> BaseLanguageModel:
        """Create an Ollama model instance."""
        model_params = {
            "model": config.model_name,
            "base_url": config.base_url or DEFAULT_OLLAMA_URL,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "num_predict": config.max_tokens,  # max_tokens in Ollama is num_predict
            "num_ctx": config.context_window,
            "num_gpu": config.num_gpu,
            "num_thread": config.num_thread,
            "repeat_penalty": config.repeat_penalty,
            "stop": config.stop,
        }
        
        # Remove None values
        model_params = {k: v for k, v in model_params.items() if v is not None}
        
        # Add any extra parameters
        if config.extra_params:
            model_params.update(config.extra_params)
            
        return OllamaLLM(**model_params)
    
    def check_availability(self, config: ModelConfig) -> bool:
        """Check if Ollama model is available."""
        try:
            url = f"{config.base_url or DEFAULT_OLLAMA_URL}/api/tags"
            response = requests.get(url, timeout=5)  # Add timeout
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any( config.model_name in model.get('name') for model in models)
            return False
        except Exception:
            return False

class LMStudioProvider(BaseLLMProvider):
    """LM Studio provider implementation using OpenAI-compatible API."""
    
    def create_model(self, config: ModelConfig) -> BaseLanguageModel:
        """Create an LM Studio model instance using OpenAI compatibility."""
        # Base parameters that are directly supported by OpenAI
        model_params = {
            "model_name": config.model_name,
            "base_url": config.base_url or DEFAULT_LMSTUDIO_URL,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_tokens": config.max_tokens,
            "openai_api_key": "not-needed"  # LM Studio doesn't require API key
        }
        
        # Handle special parameters that need to be at the top level
        if config.extra_params:
            # Extract frequency_penalty and presence_penalty if they exist
            if 'frequency_penalty' in config.extra_params:
                model_params['frequency_penalty'] = config.extra_params.pop('frequency_penalty')
            if 'presence_penalty' in config.extra_params:
                model_params['presence_penalty'] = config.extra_params.pop('presence_penalty')
        
        # Add remaining extra parameters to model_kwargs, excluding unsupported ones
        model_kwargs = {}
        if config.stop:
            model_kwargs["stop"] = config.stop
        
        # Add any remaining extra parameters
        if config.extra_params:
            # Filter out context_window as it's not supported
            extra_params = {k: v for k, v in config.extra_params.items() 
                          if k not in ['context_window']}
            model_kwargs.update(extra_params)
        
        if model_kwargs:
            model_params["model_kwargs"] = model_kwargs
        
        return OpenAI(**model_params)
    
    def check_availability(self, config: ModelConfig) -> bool:
        """Check if LM Studio server is available."""
        try:
            response = requests.get(
                f"{config.base_url or DEFAULT_LMSTUDIO_URL}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

class ModelFactory:
    """Factory for creating language model instances."""
    
    _providers = {
        'ollama': OllamaProvider(),
        'lmstudio': LMStudioProvider()
    }
    
    @classmethod
    def create_model(cls, config: ModelConfig) -> Optional[BaseLanguageModel]:
        """Create a language model instance based on configuration."""
        provider = cls._providers.get(config.provider.lower())
        if not provider:
            raise ValueError(f"Unsupported provider: {config.provider}")
        
        if not provider.check_availability(config):
            raise RuntimeError(
                f"Provider {config.provider} is not available. "
                f"Please check if the service is running at {config.base_url}"
            )
        
        return provider.create_model(config)

class ModelManager:
    """Manager class for handling model configurations and creation."""
    
    def __init__(self, config_path: str = "config/models.yml"):
        self.config_path = config_path
        self.configs: Dict[str, ModelConfig] = {}
        self._default_model = None
        self.load_configs()
    
    def load_configs(self):
        """Load model configurations from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                for name, config in data.get('models', {}).items():
                    self.configs[name] = ModelConfig.from_dict(config)
                    if config.get('default', False):
                        self._default_model = name
        except FileNotFoundError:
            self._create_default_config()
            self.load_configs()
    
    def _create_default_config(self):
        """Create default configuration file."""
        default_config = {
            'models': {
                'mistral-ollama': {
                    'provider': 'ollama',
                    'model_name': 'mistral',
                    'base_url': DEFAULT_OLLAMA_URL,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 2048,
                    'context_window': 4096,
                    'default': True,
                    'num_gpu': 1,
                    'repeat_penalty': 1.1,
                    'stop': ["Human:", "Assistant:"],
                    'extra_params': {
                        'num_predict': 2048
                    }
                },
                'mixtral-lmstudio': {
                    'provider': 'lmstudio',
                    'model_name': 'mixtral-8x7b-instruct',
                    'base_url': DEFAULT_LMSTUDIO_URL,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 2048,
                    # Removed context_window as it's not supported
                    'stop': ["Human:", "Assistant:"],
                    # Move frequency_penalty and presence_penalty to top level
                    'frequency_penalty': 0.1,
                    'presence_penalty': 0.1,
                    'extra_params': {
                        # Add any other LM Studio specific parameters here
                    }
                }
            }
        }
        
        import os
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f)
        
        import os
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f)
    
    def get_model(self, model_name: Optional[str] = None) -> BaseLanguageModel:
        """Get language model instance by name or default."""
        if model_name is None and self._default_model:
            model_name = self._default_model
        
        if not model_name:
            raise ValueError("No model name provided and no default model configured")
        
        config = self.configs.get(model_name)
        if not config:
            raise ValueError(f"Model configuration not found: {model_name}")
        
        return ModelFactory.create_model(config)
    
    def list_available_models(self) -> Dict[str, bool]:
        """List all configured models and their availability."""
        available_models = {}
        for name, config in self.configs.items():
            provider = ModelFactory._providers.get(config.provider.lower())
            if provider:
                available_models[name] = provider.check_availability(config)
        return available_models

if __name__ == "__main__":
    # Initialize model manager
    manager = ModelManager()
    
    # List available models
    available_models = manager.list_available_models()
    print("Available models:")
    for model, available in available_models.items():
        print(f"{model}: {'Available' if available else 'Not available'}")
    
    try:
        # Try default model
        model = manager.get_model()
        response = model.invoke("Hello! How are you?")
        print("\nDefault model response:", response)
        
        # Try specific models
        for model_name in ['mistral-ollama', 'mixtral-lmstudio']:
            try:
                print(f"\nTrying {model_name}...")
                model = manager.get_model(model_name)
                response = model.invoke("Hello! How are you?")
                print(f"{model_name} response:", response)
            except Exception as e:
                print(f"Error with {model_name}: {str(e)}")
                
    except Exception as e:
        print(f"Error: {str(e)}")
