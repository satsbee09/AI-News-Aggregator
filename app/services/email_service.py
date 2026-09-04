import os
import smtplib
from collections import defaultdict
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Tuple, Dict, Any, Optional
from app.config import settings
from app.database.repository import MongoRepository
from app.profiles.user_profile import UserProfile, DEFAULT_USER_PROFILE

CATEGORY_ICONS = {
    "ai": ("🤖", "Frontier AI & Technology", "#eff6ff", "#2563eb"),
    "local": ("📍", "Local News & Community", "#fef3c7", "#d97706"),
    "national": ("🇮🇳", "National News & Politics", "#ecfdf5", "#059669"),
    "international": ("🌍", "International Geopolitics", "#f3e8ff", "#7c3aed"),
    "sports": ("🏏", "Sports & Cricket", "#fff1f2", "#e11d48"),
    "weather": ("🌦️", "Weather & Forecast", "#e0f2fe", "#0284c7"),
    "general": ("📰", "General Intelligence", "#f1f5f9", "#475569")
}

def build_email_html(ranked_items: List[Tuple[Dict[str, Any], float, str]], profile: UserProfile = DEFAULT_USER_PROFILE) -> str:
    """Renders a modern, categorized HTML email newsletter grouped by topic/category."""
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    
    # 1. Group ranked items by category
    grouped_articles = defaultdict(list)
    for digest, score, reason in ranked_items:
        cat = digest.get("category", "general").lower()
        grouped_articles[cat].append((digest, score, reason))

    sections_html = ""

    for cat, items in grouped_articles.items():
        emoji, cat_title, bg_color, text_color = CATEGORY_ICONS.get(cat, ("📌", cat.capitalize(), "#f1f5f9", "#334155"))
        
        cards_html = ""
        for digest, score, reason in items:
            article = digest.get("article", {})
            title = article.get("title", "Untitled")
            url = article.get("url", "#")
            source = article.get("source", "unknown")
            topic_name = digest.get("topic_name", cat_title)
            summary = digest.get("summary", "")
            takeaways = digest.get("key_takeaways", "")

            takeaways_list = "".join([f"<li style='margin-bottom: 6px;'>{line.lstrip('-• ')}</li>" for line in takeaways.split("\n") if line.strip()])

            cards_html += f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="background: {bg_color}; color: {text_color}; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 8px; border-radius: 6px;">
                        {topic_name}
                    </span>
                    <span style="background: #f0fdf4; color: #16a34a; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 6px;">
                        Relevance: {score}/10
                    </span>
                </div>
                
                <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 0 0 6px 0; line-height: 1.4;">
                    <a href="{url}" style="color: #0f172a; text-decoration: none;" target="_blank">
                        {title}
                    </a>
                </h3>
                
                <div style="font-size: 11px; color: #64748b; margin-bottom: 12px;">
                    Source: <strong>{source.upper()}</strong>
                </div>

                <p style="font-size: 13.5px; line-height: 1.6; color: #334155; margin: 0 0 14px 0;">
                    {summary}
                </p>

                <div style="background: #f8fafc; border-left: 3px solid {text_color}; padding: 10px 14px; border-radius: 0 6px 6px 0; margin-bottom: 12px;">
                    <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 6px;">Key Highlights</div>
                    <ul style="margin: 0; padding-left: 16px; font-size: 12.5px; color: #334155; line-height: 1.45;">
                        {takeaways_list}
                    </ul>
                </div>

                <div style="font-size: 11.5px; color: #64748b; font-style: italic;">
                    💡 <strong>Analysis:</strong> {reason}
                </div>
                
                <div style="margin-top: 12px; text-align: right;">
                    <a href="{url}" style="display: inline-block; font-size: 12px; font-weight: 600; color: #2563eb; text-decoration: none;" target="_blank">
                        Read full story &rarr;
                    </a>
                </div>
            </div>
            """

        sections_html += f"""
        <div style="margin-bottom: 28px;">
            <div style="display: flex; align-items: center; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0;">
                <span style="font-size: 20px; margin-right: 8px;">{emoji}</span>
                <h2 style="font-size: 18px; font-weight: 800; color: #0f172a; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">
                    {cat_title}
                </h2>
            </div>
            {cards_html}
        </div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Multi-Topic Intelligence Digest</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <div style="max-width: 680px; margin: 24px auto; background-color: transparent; padding: 0 16px;">
            <!-- Header Banner -->
            <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 16px; padding: 28px; color: #ffffff; text-align: center; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.06);">
                <div style="font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #38bdf8; margin-bottom: 6px;">
                    Universal Intelligence Briefing
                </div>
                <h1 style="font-size: 24px; font-weight: 800; margin: 0 0 8px 0; letter-spacing: -0.5px;">
                    Daily Curated News Digest
                </h1>
                <div style="font-size: 12.5px; color: #94a3b8;">
                    {date_str} • Curated for <strong>{profile.name}</strong>
                </div>
            </div>

            <!-- Grouped Sections -->
            {sections_html}

            <!-- Footer -->
            <div style="text-align: center; padding: 20px; font-size: 11.5px; color: #94a3b8;">
                <p style="margin: 0 0 4px 0;">Universal News Intelligence Pipeline • Powered by MongoDB & Groq LLM</p>
                <p style="margin: 0;">Multi-topic curation across Local, National, Global, Tech & Weather.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return full_html


def send_digest_email(
    ranked_items: List[Tuple[Dict[str, Any], float, str]],
    repo: Optional[MongoRepository] = None,
    recipient: str = "",
    dry_run: bool = False
) -> bool:
    """Builds and delivers the categorized email digest via Gmail SMTP, logging sent IDs to MongoDB."""
    if not ranked_items:
        print("   [INFO] No articles to send in email.")
        return False

    repo = repo or MongoRepository()
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
        
        for digest, _, _ in ranked_items:
            repo.log_sent_digest(digest["_id"], recipient=recipient or "dry_run_user@local")
        return True

    # 2. Dispatch via Gmail SMTP
    date_str = datetime.now(timezone.utc).strftime("%b %d, %Y")
    subject = f"Daily Intelligence Digest — {date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"News Digest <{settings.EMAIL_USER}>"
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

        # 3. Log sent digests in MongoDB to prevent re-sending
        for digest, _, _ in ranked_items:
            repo.log_sent_digest(digest["_id"], recipient=recipient)

        return True
    except Exception as e:
        print(f"   [ERROR] Failed to send email via SMTP: {e}")
        return False
