import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.database.models import Digest
from app.database.repository import Repository
from app.profiles.user_profile import UserProfile, DEFAULT_USER_PROFILE

def build_email_html(ranked_items: List[Tuple[Digest, int, str]], profile: UserProfile = DEFAULT_USER_PROFILE) -> str:
    """Renders a modern, responsive HTML email template for the daily digest."""
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    
    # Build HTML cards for each article
    cards_html = ""
    for rank, (digest, score, reason) in enumerate(ranked_items, start=1):
        # Format takeaways into HTML list items
        takeaways_list = "".join([f"<li style='margin-bottom: 6px;'>{line.lstrip('-• ')}</li>" for line in digest.key_takeaways.split("\n") if line.strip()])
        
        cards_html += f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="background: #eff6ff; color: #2563eb; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; padding: 4px 10px; border-radius: 6px;">
                    {digest.category}
                </span>
                <span style="background: #f0fdf4; color: #16a34a; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 6px;">
                    Score: {score}/10
                </span>
            </div>
            
            <h2 style="font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 8px 0; line-height: 1.4;">
                <a href="{digest.article.url}" style="color: #0f172a; text-decoration: none;" target="_blank">
                    #{rank}. {digest.article.title}
                </a>
            </h2>
            
            <div style="font-size: 12px; color: #64748b; margin-bottom: 14px;">
                Source: <strong>{digest.article.source.upper()}</strong>
            </div>

            <p style="font-size: 14px; line-height: 1.6; color: #334155; margin: 0 0 16px 0;">
                {digest.summary}
            </p>

            <div style="background: #f8fafc; border-left: 3px solid #3b82f6; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 16px;">
                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 8px;">Key Takeaways</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #334155; line-height: 1.5;">
                    {takeaways_list}
                </ul>
            </div>

            <div style="font-size: 12px; color: #64748b; font-style: italic;">
                💡 <strong>Curator Note:</strong> {reason}
            </div>
            
            <div style="margin-top: 14px; text-align: right;">
                <a href="{digest.article.url}" style="display: inline-block; font-size: 12px; font-weight: 600; color: #2563eb; text-decoration: none;" target="_blank">
                    Read full source &rarr;
                </a>
            </div>
        </div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily AI Intelligence Digest</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <div style="max-width: 680px; margin: 30px auto; background-color: transparent; padding: 0 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 16px; padding: 32px; color: #ffffff; text-align: center; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
                <div style="font-size: 12px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #38bdf8; margin-bottom: 6px;">
                    AI News Intelligence
                </div>
                <h1 style="font-size: 26px; font-weight: 800; margin: 0 0 8px 0; letter-spacing: -0.5px;">
                    Daily Curated Digest
                </h1>
                <div style="font-size: 13px; color: #94a3b8;">
                    {date_str} • Curated for <strong>{profile.name}</strong>
                </div>
            </div>

            <!-- Articles Container -->
            {cards_html}

            <!-- Footer -->
            <div style="text-align: center; padding: 24px; font-size: 12px; color: #94a3b8;">
                <p style="margin: 0 0 6px 0;">Automated AI News Aggregator • Built with Groq & SQLite</p>
                <p style="margin: 0;">Zero tracking, zero clickbait, 100% technical insights.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return full_html


def send_digest_email(
    session: Session,
    ranked_items: List[Tuple[Digest, int, str]],
    recipient: str = "",
    dry_run: bool = False
) -> bool:
    """Builds and delivers the email digest via Gmail SMTP, logging sent IDs to DB."""
    if not ranked_items:
        print("   [INFO] No articles to send in email.")
        return False

    repo = Repository(session)
    recipient = recipient or settings.RECIPIENT_EMAIL or settings.EMAIL_USER
    html_content = build_email_html(ranked_items)

    # 1. Always save a local preview HTML file for visual inspection
    preview_dir = "data"
    os.makedirs(preview_dir, exist_ok=True)
    preview_path = os.path.join(preview_dir, "latest_digest_preview.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   [SUCCESS] Saved local email preview to: {preview_path}")

    # Check if credentials are configured
    can_send = bool(settings.EMAIL_USER and settings.EMAIL_APP_PASSWORD and recipient)
    if dry_run or not can_send:
        if not can_send:
            print("   [INFO] EMAIL_USER / EMAIL_APP_PASSWORD not set in .env. Skipping SMTP dispatch.")
        else:
            print("   [INFO] Dry-run enabled. Skipping SMTP dispatch.")
        
        # Log sent status
        for digest, _, _ in ranked_items:
            repo.log_sent_digest(digest.id, recipient=recipient or "dry_run_user@local")
        return True

    # 2. Dispatch via Gmail SMTP
    date_str = datetime.now(timezone.utc).strftime("%b %d, %Y")
    subject = f"Daily AI Intelligence Digest — {date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AI News Digest <{settings.EMAIL_USER}>"
    msg["To"] = recipient

    # Attach HTML
    part = MIMEText(html_content, "html")
    msg.attach(part)

    try:
        print(f"   Connecting to SMTP server ({settings.EMAIL_HOST}:{settings.EMAIL_PORT})...")
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_APP_PASSWORD)
            server.send_message(msg)

        print(f"   [SUCCESS] Email successfully delivered to {recipient}!")

        # 3. Log sent digests to prevent re-sending
        for digest, _, _ in ranked_items:
            repo.log_sent_digest(digest.id, recipient=recipient)

        return True
    except Exception as e:
        print(f"   [ERROR] Failed to send email via SMTP: {e}")
        return False
