import json
from typing import List, Optional
from pydantic import BaseModel, Field
from app.agent.base_llm import LLMClient

class DigestOutput(BaseModel):
    summary: str = Field(description="2-3 sentence factual, hype-free summary of the content.")
    key_takeaways: List[str] = Field(description="Exactly 3 bullet points highlighting technical takeaways or metrics.")
    category: str = Field(description="One of: 'Model Release', 'Research Paper', 'Tooling & Infrastructure', 'Industry News', 'Agentic AI'")

class DigestAgent:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def summarize(self, title: str, source: str, raw_content: str) -> DigestOutput:
        system_prompt = """You are an expert AI research scientist and technical editor.
Your job is to read raw articles and video transcripts, cut through sensationalism and clickbait, and produce a concise, highly informative technical summary.

Output MUST be valid JSON matching this schema:
{
  "summary": "2-3 concise sentences explaining what happened, the technical mechanism, and why it matters.",
  "key_takeaways": [
    "Key technical fact / metric 1",
    "Key technical fact / metric 2",
    "Key technical fact / metric 3"
  ],
  "category": "Model Release | Research Paper | Tooling & Infrastructure | Industry News | Agentic AI"
}

Guidelines:
- Strip all hype words (e.g. 'game-changing', 'mind-blowing', 'unbelievable').
- Highlight concrete models, architectures, benchmarks, code repos, or business milestones.
- Keep takeaways concise and punchy."""

        # Truncate content to avoid exceeding context window
        user_prompt = f"""Title: {title}
Source: {source}

Content:
{raw_content[:7000]}

Generate the JSON summary now:"""

        raw_response = self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt, json_mode=True)
        
        try:
            data = json.loads(raw_response)
            return DigestOutput(**data)
        except Exception as e:
            # Fallback if parsing fails
            return DigestOutput(
                summary=raw_response[:300],
                key_takeaways=["Key insight extracted", "Review full source for details", "Parsed with fallback"],
                category="General AI"
            )
