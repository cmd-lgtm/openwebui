"""
AI Router - Routes requests to appropriate AI provider
"""
import logging
from typing import AsyncGenerator, Optional

from app.core.config import settings
from app.core.exceptions import ProviderNotFoundException, ModelNotFoundException
from app.services.ollama_service import OllamaService, get_ollama_service
from app.services.openai_service import OpenAIService, get_openai_service
from app.services.anthropic_service import AnthropicService, get_anthropic_service
from app.cache import cache_service

logger = logging.getLogger(__name__)

# Cache TTL for model lists (5 minutes)
MODELS_CACHE_TTL = 300

# Supported providers
AVAILABLE_PROVIDERS = {
    "ollama": {
        "name": "Ollama",
        "description": "Local AI models running on your machine",
        "enabled": True,  # Always try to connect
        "models_endpoint": "/api/tags",
        "supports_streaming": True,
        "supports_embeddings": True,
    },
    "openai": {
        "name": "OpenAI",
        "description": "GPT-4, GPT-4o, and more from OpenAI",
        "enabled": settings.OPENAI_ENABLED and bool(settings.OPENAI_API_KEY),
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini"],
        "supports_streaming": True,
        "supports_embeddings": True,
    },
    "anthropic": {
        "name": "Anthropic",
        "description": "Claude 3.5 and Claude 3 models",
        "enabled": settings.ANTHROPIC_ENABLED and bool(settings.ANTHROPIC_API_KEY),
        "models": ["claude-sonnet-4-20251111", "claude-opus-4-20251111", "claude-haiku-3-5-20241022"],
        "supports_streaming": True,
        "supports_embeddings": False,
    },
    "azure": {
        "name": "Azure OpenAI",
        "description": "OpenAI models via Azure",
        "enabled": settings.AZURE_OPENAI_ENABLED and bool(settings.AZURE_OPENAI_API_KEY),
        "supports_streaming": True,
        "supports_embeddings": True,
    },
    "groq": {
        "name": "Groq",
        "description": "Fast inference with Llama, Mixtral, and more",
        "enabled": settings.GROQ_ENABLED and bool(settings.GROQ_API_KEY),
        "models": ["llama-3.1-70b-versatile", "llama-3.1-405b-reasoning", "mixtral-8x7b-32768"],
        "supports_streaming": True,
        "supports_embeddings": False,
    },
    "huggingface": {
        "name": "HuggingFace",
        "description": "Open source models on HuggingFace",
        "enabled": settings.HUGGINGFACE_ENABLED and bool(settings.HUGGINGFACE_API_KEY),
        "supports_streaming": False,
        "supports_embeddings": True,
    },
    "google": {
        "name": "Google AI",
        "description": "Gemini models from Google",
        "enabled": settings.GOOGLE_ENABLED and bool(settings.GOOGLE_API_KEY),
        "models": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
        "supports_streaming": True,
        "supports_embeddings": False,
    },
    "mistral": {
        "name": "Mistral AI",
        "description": "Mistral models",
        "enabled": settings.MISTRAL_ENABLED and bool(settings.MISTRAL_API_KEY),
        "models": ["mistral-large-latest", "mistral-small-latest"],
        "supports_streaming": True,
        "supports_embeddings": False,
    },
    "xai": {
        "name": "xAI (Grok)",
        "description": "Grok models from xAI",
        "enabled": settings.XAI_ENABLED and bool(settings.XAI_API_KEY),
        "models": ["grok-2-1212", "grok-2-vision-1212", "grok-beta"],
        "supports_streaming": True,
        "supports_embeddings": False,
    },
    "blackbox": {
        "name": "Blackbox AI",
        "description": "Code generation with Blackbox AI",
        "enabled": settings.BLACKBOX_ENABLED and bool(settings.BLACKBOX_API_KEY),
        "models": ["blackboxai", "blackboxai-pro"],
        "supports_streaming": True,
        "supports_embeddings": False,
    },
    "vertex": {
        "name": "Vertex AI",
        "description": "Google Vertex AI models",
        "enabled": settings.VERTEX_AI_ENABLED and bool(settings.VERTEX_AI_KEY),
        "models": ["gemini-2.0-flash-exp", "gemini-1.5-pro"],
        "supports_streaming": True,
        "supports_embeddings": False,
    },
}


class AIRouter:
    """Routes AI requests to appropriate provider"""

    def __init__(self):
        self.ollama = get_ollama_service()
        self.openai = get_openai_service()
        self.anthropic = get_anthropic_service()

    async def check_provider_status(self, provider: str) -> dict:
        """Check if a provider is available"""
        if provider not in AVAILABLE_PROVIDERS:
            return {"status": "unavailable", "reason": "Unknown provider"}

        provider_info = AVAILABLE_PROVIDERS[provider]
        if not provider_info["enabled"]:
            return {"status": "disabled", "reason": "Provider not enabled"}

        # Check actual connection
        if provider == "ollama":
            connected = await self.ollama.check_connection()
            return {"status": "connected" if connected else "disconnected", "reason": None}

        if provider == "openai":
            connected = await self.openai.check_connection()
            return {"status": "connected" if connected else "disconnected", "reason": None}

        if provider == "anthropic":
            connected = await self.anthropic.check_connection()
            return {"status": "connected" if connected else "disconnected", "reason": None}

        return {"status": "enabled", "reason": None}

    async def list_all_models(self) -> dict:
        """List all available models from all providers (cached)"""
        # Try cache first
        cache_key = "ai:models:all"
        cached = await cache_service.get(cache_key)
        if cached is not None:
            logger.debug("Returning cached model list")
            return cached

        # Fetch from providers
        models = {"ollama": [], "openai": [], "anthropic": []}

        # Ollama models
        if await self.ollama.check_connection():
            try:
                models["ollama"] = await self.ollama.list_models()
            except Exception as e:
                logger.warning(f"Failed to get Ollama models: {e}")

        # OpenAI models
        if self.openai.enabled:
            try:
                models["openai"] = await self.openai.list_models()
            except Exception as e:
                logger.warning(f"Failed to get OpenAI models: {e}")

        # Anthropic models
        if self.anthropic.enabled:
            try:
                models["anthropic"] = await self.anthropic.list_models()
            except Exception as e:
                logger.warning(f"Failed to get Anthropic models: {e}")

        # Cache the result
        await cache_service.set(cache_key, models, MODELS_CACHE_TTL)

        return models

    async def chat(
        self,
        messages: list[dict],
        provider: str = "ollama",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ):
        """Route chat request to appropriate provider"""
        if provider == "ollama":
            return await self.ollama.chat_stream(messages, model, temperature, max_tokens) if stream \
                else await self.ollama.chat(messages, model, temperature, max_tokens, stream)

        elif provider == "openai":
            return await self.openai.chat_stream(messages, model, temperature, max_tokens) if stream \
                else await self.openai.chat(messages, model, temperature, max_tokens, stream)

        elif provider == "anthropic":
            return await self.anthropic.chat_stream(messages, model, None, temperature, max_tokens) if stream \
                else await self.anthropic.chat(messages, model, None, temperature, max_tokens, stream)

        else:
            raise ProviderNotFoundException(provider)

    async def generate(
        self,
        prompt: str,
        provider: str = "ollama",
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ):
        """Route generate request to appropriate provider"""
        if provider == "ollama":
            return await self.ollama.generate_stream(prompt, model, system, temperature, max_tokens) if stream \
                else await self.ollama.generate(prompt, model, system, temperature, max_tokens, stream)

        elif provider == "openai":
            return await self.openai.generate_stream(prompt, model, system, temperature, max_tokens) if stream \
                else await self.openai.generate(prompt, model, system, temperature, max_tokens, stream)

        elif provider == "anthropic":
            return await self.anthropic.generate_stream(prompt, model, system, temperature, max_tokens) if stream \
                else await self.anthropic.generate(prompt, model, system, temperature, max_tokens, stream)

        else:
            raise ProviderNotFoundException(provider)

    async def create_embedding(self, text: str, provider: str = "ollama", model: Optional[str] = None) -> list[float]:
        """Create embedding for text"""
        if provider == "ollama":
            return await self.ollama.create_embedding(text, model or "nomic-embed-text")

        elif provider == "openai":
            return await self.openai.create_embedding(text, model or "text-embedding-3-small")

        else:
            raise ProviderNotFoundException(f"Embeddings not supported for {provider}")


# Singleton
ai_router: Optional[AIRouter] = None


def get_ai_router() -> AIRouter:
    """Get AI router instance"""
    global ai_router
    if ai_router is None:
        ai_router = AIRouter()
    return ai_router
