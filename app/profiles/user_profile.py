from dataclasses import dataclass, field
from typing import List

@dataclass
class UserProfile:
    name: str = "AI Engineer / Researcher"
    primary_interests: List[str] = field(default_factory=lambda: [
        "LLM architecture, reasoning models, and frontier capabilities (GPT, Claude, Gemini, Qwen)",
        "Open-source model releases, weights, and fine-tuning techniques (Hugging Face, vLLM)",
        "Autonomous AI agents, tool-use, and coding workflows",
        "Hardware, inference optimization, and systems engineering",
        "High-impact AI research papers and technical breakthroughs"
    ])
    disliked_topics: List[str] = field(default_factory=lambda: [
        "Non-technical corporate PR and generic funding rounds",
        "Crypto, NFT, or Web3 AI buzzwords",
        "Elementary beginner tutorials or listicles",
        "Superficial marketing hype without benchmark data or code"
    ])
    max_daily_articles: int = 5

# Default active profile
DEFAULT_USER_PROFILE = UserProfile()
