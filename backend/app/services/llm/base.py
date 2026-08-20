from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_json(self, system_prompt: str, user_content: str) -> Dict[str, Any]:
        """Send prompt to LLM and guarantee parsed JSON output."""
        pass