import json
import re
import time
from typing import Optional, List
from groq import Groq
from app.config import settings

class LLMClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        # Active Groq models in order of capability & availability
        self.models: List[str] = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
            "qwen/qwen3.6-27b"
        ]

    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Calls Groq LLMs with automatic model fallback, token conservation, and robust JSON extraction."""
        if not self.client:
            raise ValueError(
                "GROQ_API_KEY is not set or invalid in your .env file! "
                "Get a free key from https://console.groq.com/keys"
            )

        if json_mode:
            system_prompt += "\nIMPORTANT: You must respond ONLY with valid, parseable JSON matching the requested schema. Do NOT include markdown fences, thoughts, or extra commentary."

        last_error = None

        for model_name in self.models:
            try:
                # Use conservative max_tokens (350) to stay well under Groq free-tier rate limits (1000 OTPM)
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=350
                )
                raw_text = response.choices[0].message.content.strip()

                if json_mode:
                    # Robust JSON extraction via regex
                    match = re.search(r'\{[\s\S]*\}', raw_text)
                    if match:
                        extracted = match.group(0)
                        # Validate JSON parseability
                        json.loads(extracted)
                        return extracted
                    else:
                        raise ValueError(f"No valid JSON object found in response from {model_name}")

                return raw_text

            except Exception as e:
                last_error = e
                err_str = str(e)
                print(f"      [INFO] Model {model_name} failed: {err_str[:120]}... Trying fallback model...")
                # Small pause on rate limits
                if "429" in err_str or "rate_limit" in err_str.lower():
                    time.sleep(1.0)

        raise RuntimeError(f"All LLM models failed. Last error: {last_error}")
