import json
import re
import requests
from app.config import settings
from app.services.llm.base import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.model_name = settings.OLLAMA_MODEL

    def generate_json(self, system_prompt: str, user_content: str) -> dict:
        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "prompt": user_content,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }
        
        response = requests.post(endpoint, json=payload, timeout=120)
        response.raise_for_status()
        
        raw_json_str = response.json().get("response", "{}").strip()
        raw_json_str = re.sub(r"^```json\s*", "", raw_json_str)
        raw_json_str = re.sub(r"\s*```$", "", raw_json_str)
        
        return json.loads(raw_json_str)