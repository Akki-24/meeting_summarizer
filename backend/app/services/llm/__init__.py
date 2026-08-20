from app.config import settings
from app.services.llm.base import BaseLLMProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.ollama_provider import OllamaProvider

def get_llm_provider() -> BaseLLMProvider:
    if settings.LLM_PROVIDER.lower() == "ollama":
        return OllamaProvider()
    return GeminiProvider()