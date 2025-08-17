import os
import inspect
from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.settings_loader import settings
from app.config_loader import load_config


class ModelLoader:
    """
    A class to dynamically load different LLM, embedding, and safeguard models
    based on specified providers.
    """
    def __init__(self):
        """Initializes the loader with application settings and model config."""
        self.settings = settings
        self.app_config = load_config()
        # Set environment variables from settings for API key access
        os.environ['OPENAI_API_KEY'] = self.settings.OPENAI_API_KEY
        os.environ['GOOGLE_API_KEY'] = self.settings.GOOGLE_API_KEY
        os.environ['GROQ_API_KEY'] = self.settings.GROQ_API_KEY


    def load_llm(self, provider: Optional[str] = None):
        """
        Loads and returns an LLM instance based on the specified provider.
        Defaults to the provider in the config if none is given.
        """
        try:
            target_provider = provider or self.app_config["llm"]["default_provider"]
            model_name = self.app_config["llm"]["providers"][target_provider]["model_name"]
            
            if target_provider == "openai":
                return ChatOpenAI(model=model_name)
            elif target_provider == "google":
                return ChatGoogleGenerativeAI(model=model_name)
            elif target_provider == "groq":
                return ChatGroq(model_name=model_name)
            else:
                raise ValueError(f"Unknown LLM provider: {target_provider}")
        except Exception as e:
            print(f"❌ Failed to load LLM model for provider '{provider}': {e}")
            return None


    def load_embedding(self, provider: Optional[str] = None):
        """
        Loads and returns an embedding model instance based on the specified provider.
        Defaults to the provider in the config if none is given.
        """
        try:
            target_provider = provider or self.app_config["embedding_model"]["default_provider"]
            model_name = self.app_config["embedding_model"]["providers"][target_provider]["model_name"]

            if target_provider == "google":
                return GoogleGenerativeAIEmbeddings(model=model_name)
            elif target_provider == "openai":
                return OpenAIEmbeddings(model=model_name)
            else:
                raise ValueError(f"Unknown embedding provider: {target_provider}")
        except Exception as e:
            print(f"❌ Failed to load embedding model for provider '{provider}': {e}")
            return None
    
    
    def load_safeguard(self):
        """
        Loads the safeguard model, which is configured to use Groq by default.
        """
        try:
            model_name = self.app_config["safeguard"]["groq"]["model_name"]
            return ChatGroq(model_name=model_name)
        except Exception as e:
            print(f"❌ Failed to load safeguard model: {e}")
            return None








# Example Usage
# if __name__ == '__main__':
#     # We're using a dummy settings object and the hardcoded config for this example
#     class DummySettings:
#         OPENAI_API_KEY = "dummy-openai-key"
#         GOOGLE_API_KEY = "dummy-google-key"
#         GROQ_API_KEY = "dummy-groq-key"

#     loader = ModelLoader(DummySettings(), app_config)

#     print("Loading Google LLM...")
#     google_llm = loader.load_llm("google")
#     print(f"Loaded: {type(google_llm).__name__} with model name: {inspect.getattr_static(google_llm, 'model_name')}\n")

#     print("Loading Groq LLM...")
#     groq_llm = loader.load_llm("groq")
#     print(f"Loaded: {type(groq_llm).__name__} with model name: {inspect.getattr_static(groq_llm, 'model_name')}\n")

#     print("Loading default LLM (Google)...")
#     default_llm = loader.load_llm()
#     print(f"Loaded: {type(default_llm).__name__} with model name: {inspect.getattr_static(default_llm, 'model_name')}\n")
    
#     print("Loading Google embedding model...")
#     google_embeddings = loader.load_embedding("google")
#     print(f"Loaded: {type(google_embeddings).__name__} with model name: {google_embeddings.model}\n")

#     # print("Loading OpenAI embedding model...")
#     # openai_embeddings = loader.load_embedding("openai")
#     # print(f"Loaded: {type(openai_embeddings).__name__} with model name: {openai_embeddings.model}\n")

#     print("Loading default embedding model (Google)...")
#     default_embeddings = loader.load_embedding()
#     print(f"Loaded: {type(default_embeddings).__name__} with model name: {default_embeddings.model}\n")

#     print("Loading Safeguard model...")
#     safeguard_model = loader.load_safeguard()
#     print(f"Loaded: {type(safeguard_model).__name__} with model name: {inspect.getattr_static(safeguard_model, 'model_name')}\n")
