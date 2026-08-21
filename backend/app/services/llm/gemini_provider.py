import json
import re
import time
from google import genai
from google.genai import types
from app.config import settings
from app.services.llm.base import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment or .env file.")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    def generate_json(self, system_prompt: str, user_content: str) -> dict:
        combined_prompt = (
            f"{system_prompt}\n\n"
            f"Strictly return ONLY a valid JSON object matching the requested schema. "
            f"Do not add conversational markdown wrapping or preamble.\n\n"
            f"Input:\n{user_content}"
        )
        
        # Valid production Gemini models in order of preference
        candidate_models = [self.model_name, "gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]
        # Deduplicate while preserving order
        unique_models = list(dict.fromkeys(candidate_models))
        
        response = None
        last_error = None

        for model in unique_models:
            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=combined_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            response_mime_type="application/json",
                        ),
                    )
                    break
                except Exception as e:
                    last_error = e
                    print(f"[GeminiProvider] Model '{model}' attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(1.5 * (attempt + 1))
            
            if response is not None:
                break

        if response is None:
            raise ValueError(f"All Gemini fallback models failed. Last error: {last_error}")

        text = response.text.strip()
        
        # Strip markdown codeblocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Failed to parse JSON from Gemini output: {text}")