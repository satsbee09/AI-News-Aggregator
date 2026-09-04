import json
from typing import Optional, List
from groq import Groq
from app.config import settings

class LLMClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        # Active Groq models
        self.models: List[str] = [
            "qwen/qwen3.8-27b",
            "qwen/qwen3.6-27b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b"
        ]

    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Calls Groq LLaMA with automatic model fallback and optional JSON enforcement."""
        if not self.client:
            raise ValueError(
                "GROQ_API_KEY is not set or invalid in your .env file! "
                "Get a free key from https://console.groq.com/keys"
            )

        response_format = {"type": "json_object"} if json_mode else None
        last_error = None

        for model_name in self.models:
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=response_format,
                    temperature=0.2,
                    max_tokens=800
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                print(f"      [INFO] Model {model_name} failed: {e}. Trying fallback model...")

        raise RuntimeError(f"All LLM models failed. Last error: {last_error}")
