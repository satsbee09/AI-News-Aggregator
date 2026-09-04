from app.database.connection import init_db, SessionLocal
from app.database.repository import Repository
from app.agent.curator_agent import CuratorAgent
from app.services.email_service import send_digest_email
from app.profiles.user_profile import DEFAULT_USER_PROFILE

def run_test():
    print("1. Initializing Database...")
    init_db()
    session = SessionLocal()
    repo = Repository(session)

    unsent = repo.get_unsent_digests()
    print(f"   Found {len(unsent)} unsent digest(s) in DB.")
    assert len(unsent) > 0, "No unsent digests available. Run Phase 4/5 first!"

    print("\n2. Curating top stories for the email...")
    curator = CuratorAgent()
    ranked = curator.rank_digests(unsent, profile=DEFAULT_USER_PROFILE)
    top_stories = ranked[:DEFAULT_USER_PROFILE.max_daily_articles]

    print(f"   Selected top {len(top_stories)} stories.")

    print("\n3. Generating and dispatching email digest...")
    success = send_digest_email(session=session, ranked_items=top_stories)
    assert success, "Email generation failed."

    print("\n4. Checking updated unsent count in DB...")
    remaining_unsent = repo.get_unsent_digests()
    print(f"   Remaining unsent digests: {len(remaining_unsent)}")

    session.close()
    print("\n[SUCCESS] Phase 6 Email Delivery test passed completely!")
    print("Tip: Open 'data/latest_digest_preview.html' in your web browser to view your formatted newsletter!")

if __name__ == "__main__":
    run_test()
