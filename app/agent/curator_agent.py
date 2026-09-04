import json
from typing import List, Optional
from pydantic import BaseModel, Field
from app.agent.base_llm import LLMClient
from app.database.models import Digest
from app.profiles.user_profile import UserProfile, DEFAULT_USER_PROFILE

class ArticleScore(BaseModel):
    digest_id: int
    score: int = Field(description="Relevance score from 1 (irrelevant/hype) to 10 (must-read technical news)")
    reason: str = Field(description="1 concise sentence explaining why this article is relevant or deprioritized.")

class CuratorOutput(BaseModel):
    ranked_articles: List[ArticleScore]

class CuratorAgent:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def rank_digests(
        self,
        digests: List[Digest],
        profile: UserProfile = DEFAULT_USER_PROFILE
    ) -> List[tuple[Digest, int, str]]:
        """
        Ranks a list of digests against the user profile.
        Returns a sorted list of (Digest, score, reason) tuples in descending score order.
        """
        if not digests:
            return []

        # Prepare digest candidates summary for the LLM
        candidates_text = ""
        digest_map = {d.id: d for d in digests}
        
        for d in digests:
            candidates_text += f"""
ID: {d.id}
Title: {d.article.title}
Source: {d.article.source}
Category: {d.category}
Summary: {d.summary}
---"""

        system_prompt = f"""You are an elite AI newsletter editor and curation agent.
Your objective is to evaluate a candidate list of AI news summaries and rank them strictly based on the user's professional profile.

User Profile:
- Role: {profile.name}
- Interests: {', '.join(profile.primary_interests)}
- Avoid / Deprioritize: {', '.join(profile.disliked_topics)}

Output MUST be valid JSON matching this schema:
{{
  "ranked_articles": [
    {{
      "digest_id": 123,
      "score": 9,
      "reason": "Directly covers new reasoning model benchmark with open methodology."
    }}
  ]
}}

Scoring Guide:
- 9-10: Groundbreaking research, frontier model releases, major architecture upgrades.
- 7-8: Useful tooling, high-quality open-source releases, deep technical insights.
- 4-6: Interesting but minor industry update or standard incremental improvement.
- 1-3: Low substance, pure PR/marketing, or matches disliked topics."""

        user_prompt = f"""Evaluate and score each of the following candidate articles:
{candidates_text}

Provide JSON ranking for all article IDs:"""

        raw_response = self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt, json_mode=True)

        try:
            curator_output = CuratorOutput.model_validate_json(raw_response)
            scored_results = []
            for item in curator_output.ranked_articles:
                if item.digest_id in digest_map:
                    scored_results.append((digest_map[item.digest_id], item.score, item.reason))
            
            # Sort by score descending
            scored_results.sort(key=lambda x: x[1], reverse=True)
            return scored_results
        except Exception as e:
            print(f"   [WARN] Curator LLM parsing failed: {e}. Using default ordering.")
            return [(d, 7, "Default ordering due to fallback") for d in digests]
