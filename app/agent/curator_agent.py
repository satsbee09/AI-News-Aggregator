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

        # Cap candidate pool to top 15 most recent digests to strictly stay within Groq ITPM (7,000 tokens)
        candidate_pool = digests[:15]
        digest_map = {str(d["_id"]): d for d in candidate_pool}
        candidates_text = ""

        for d in candidate_pool:
            d_id = str(d["_id"])
            article = d.get("article", {})
            title = article.get("title", "Untitled")[:80]
            source = article.get("source", "unknown")
            category = d.get("category", "general")
            topic_name = d.get("topic_name", "General News")
            summary = d.get("summary", "")[:180]

            candidates_text += f"""
ID: {d_id}
Topic: {topic_name} [{category}]
Title: {title}
Source: {source}
Summary: {summary}
---"""

        system_prompt = f"""You are an elite intelligence briefing editor and curator.
Your objective is to evaluate candidate news summaries and rank them based on the user's profile.

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
}}"""

        user_prompt = f"""Evaluate and score each of the candidate articles below:
{candidates_text}

Provide JSON ranking for all article IDs:"""

        try:
            raw_response = self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt, json_mode=True)
            import json
            import re
            cleaned = raw_response.strip()
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                cleaned = match.group(0)
            data = json.loads(cleaned)
            ranked_list = data.get("ranked_articles", [])

            results: List[Tuple[Dict[str, Any], float, str]] = []
            for item in ranked_list:
                d_id = str(item.get("digest_id"))
                score = float(item.get("score", 5))
                reason = item.get("reason", "Curated item")

                if d_id in digest_map:
                    results.append((digest_map[d_id], score, reason))

            # Include any missing items with baseline score 5.0
            scored_ids = {str(item.get("digest_id")) for item in ranked_list}
            for d_id, d in digest_map.items():
                if d_id not in scored_ids:
                    results.append((d, 5.0, "Baseline relevance"))

            return sorted(results, key=lambda x: x[1], reverse=True)

        except Exception as e:
            print(f"      [WARN] Curator LLM ranking failed ({e}). Using deterministic fallback ranking.")
            fallback_ranked = []
            interests_lower = [i.lower() for i in profile.primary_interests if i]
            for d in candidate_pool:
                article = d.get("article", {})
                title = str(article.get("title", "")).lower()
                topic = str(d.get("topic_name", "")).lower()
                cat = str(d.get("category", "")).lower()
                
                score = 6.0
                if any(i in title or i in topic or i in cat for i in interests_lower):
                    score += 2.5
                fallback_ranked.append((d, min(10.0, score), "Topic relevance match"))
            return sorted(fallback_ranked, key=lambda x: x[1], reverse=True)
