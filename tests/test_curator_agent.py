from app.database.connection import init_db, SessionLocal
from app.database.repository import Repository
from app.services.process_digest import process_unprocessed_digests
from app.agent.curator_agent import CuratorAgent
from app.profiles.user_profile import DEFAULT_USER_PROFILE

def run_test():
    print("1. Initializing Database...")
    init_db()
    session = SessionLocal()
    repo = Repository(session)

    # Ensure we have at least 5 digests to rank
    unsent = repo.get_unsent_digests()
    if len(unsent) < 5:
        print(f"   Currently {len(unsent)} digests available. Generating more from raw articles...")
        process_unprocessed_digests(session, limit=5)
        unsent = repo.get_unsent_digests()

    print(f"\n2. Evaluating {len(unsent)} candidate digests against User Profile:")
    print(f"   Target User Role: {DEFAULT_USER_PROFILE.name}")

    curator = CuratorAgent()
    ranked_results = curator.rank_digests(unsent, profile=DEFAULT_USER_PROFILE)

    print("\n3. Top Ranked Articles Leaderboard:")
    print("="*75)
    for rank, (digest, score, reason) in enumerate(ranked_results[:5], start=1):
        print(f"#{rank} [Score: {score}/10] [{digest.category}]")
        print(f"   Title  : {digest.article.title}")
        print(f"   Source : {digest.article.source}")
        print(f"   Reason : {reason}")
        print("-"*75)

    assert len(ranked_results) > 0, "Curator should produce scored articles."
    top_5 = ranked_results[:DEFAULT_USER_PROFILE.max_daily_articles]
    print(f"\n[SUCCESS] Successfully curated top {len(top_5)} daily stories!")

    session.close()
    print("\n[SUCCESS] Phase 5 Curation Agent test passed completely!")

if __name__ == "__main__":
    run_test()
