import json
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from app.agent.base_llm import LLMClient
from app.profiles.user_profile import UserProfile, DEFAULT_USER_PROFILE

class ArticleScore(BaseModel):
    digest_id: str
    score: int = Field(description="Relevance score from 1 (irrelevant/hype) to 10 (must-read high-impact story)")
    reason: str = Field(description="1 concise sentence explaining why this article is relevant or deprioritized.")

class CuratorOutput(BaseModel):
    ranked_articles: List[ArticleScore]

class CuratorAgent:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def rank_digests(
        self,
        digests: List[Dict[str, Any]],
        profile: UserProfile = DEFAULT_USER_PROFILE,
        topic_weights: Optional[Dict[str, float]] = None
    ) -> List[Tuple[Dict[str, Any], float, str]]:
        """
        Ranks a list of MongoDB digests against the user profile and applies topic weights.
        Returns a sorted list of (digest_dict, weighted_score, reason) tuples.
        """
        if not digests:
            return []

        # Map by stringified ID
        digest_map = {str(d["_id"]): d for d in digests}
        candidates_text = ""

        for d in digests:
            d_id = str(d["_id"])
            article = d.get("article", {})
            title = article.get("title", "Untitled")
            source = article.get("source", "unknown")
            category = d.get("category", "general")
            topic_name = d.get("topic_name", "General News")
            summary = d.get("summary", "")

            candidates_text += f"""
ID: {d_id}
Topic: {topic_name} [{category}]
Title: {title}
Source: {source}
Summary: {summary}
---"""

        system_prompt = f"""You are an elite intelligence briefing editor and curator.
Your objective is to evaluate candidate news summaries spanning Local, National, International, Technology, Business, Sports, and Weather, and rank them based on the user's profile.

User Profile:
- Name: {profile.name}
- Primary Interests: {', '.join(profile.primary_interests)}
- Avoid / Deprioritize: {', '.join(profile.disliked_topics)}

Output MUST be valid JSON matching this schema:
{{
  "ranked_articles": [
    {{
      "digest_id": "string_id",
      "score": 9,
      "reason": "High-impact verified policy decision."
    }}
  ]
}}

Scoring Guide:
- 9-10: Critical breakthrough, major national/global policy, essential localized alert/weather.
- 7-8: High-relevance news with verified facts and strong user alignment.
- 4-6: Routine update or moderate interest.
- 1-3: Low substance, sensational clickbait, or matches disliked topics."""

        user_prompt = f"""Evaluate and score each of the following candidate articles:
{candidates_text}

Provide JSON ranking for all article IDs:"""

        raw_response = self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt, json_mode=True)

        try:
            curator_output = CuratorOutput.model_validate_json(raw_response)
            scored_results = []
            weights = topic_weights or {}

            for item in curator_output.ranked_articles:
                if item.digest_id in digest_map:
                    target_digest = digest_map[item.digest_id]
                    topic = target_digest.get("topic_name", "")
                    category = target_digest.get("category", "")
                    
                    # Apply topic weight multiplier if configured
                    weight = weights.get(topic, weights.get(category, 1.0))
                    weighted_score = round(item.score * weight, 1)

                    scored_results.append((target_digest, weighted_score, item.reason))

            # Sort by weighted score descending
            scored_results.sort(key=lambda x: x[1], reverse=True)
            return scored_results
        except Exception as e:
            print(f"   [WARN] Curator LLM parsing failed: {e}. Using default ordering.")
            return [(d, 7.0, "Default ordering due to fallback") for d in digests]
