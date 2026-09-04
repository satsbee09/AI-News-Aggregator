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
{raw_content[:5000]}

Generate the JSON summary now:"""

        try:
            raw_response = self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt, json_mode=True)
            data = json.loads(raw_response)
            return DigestOutput(**data)
        except Exception as e:
            print(f"      [WARN] Digest LLM generation failed ({e}). Using deterministic content extractor fallback.")
            # Deterministic fallback: extract clean sentences from raw content
            clean_lines = [l.strip() for l in raw_content.split("\n") if len(l.strip()) > 30]
            summary_snippet = " ".join(clean_lines[:2]) if clean_lines else (raw_content[:250] + "...")
            return DigestOutput(
                summary=summary_snippet[:350],
                key_takeaways=[
                    f"Reported by {source.upper()}: {title[:80]}",
                    "Live coverage update from primary news source",
                    "Direct reference available via full article link"
                ],
                category="General"
            )
