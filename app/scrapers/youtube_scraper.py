from datetime import datetime, timezone, timedelta
from typing import List, Dict
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from app.scrapers.base import BaseScraper, ScrapedArticle

# Popular AI YouTube Channels with their Channel IDs
DEFAULT_CHANNELS: Dict[str, str] = {
    "Two Minute Papers": "UCbfYPyITQ-7l4upoX8nvctg",
    "Matthew Berman": "UCv83tO5cePwHMt1952IVVHw",
    "Fireship": "UCsBjURrPoezykLs9EqgamOA",
    "Yannic Kilcher": "UCZHmQk67mSJgfCCTn7xBfew",
    "Wes Roth": "UCqcbQf6yw5KzRoDDcZ_wBSw"
}

class YouTubeScraper(BaseScraper):
    def __init__(self, channels: Dict[str, str] = DEFAULT_CHANNELS):
        self.channels = channels

    def _get_transcript(self, video_id: str, fallback_description: str) -> str:
        """Fetches English transcript or falls back to video description."""
        try:
            transcript_items = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
            full_text = " ".join([item["text"] for item in transcript_items])
            # Truncate overly long transcripts if necessary (e.g. 15,000 characters)
            return full_text[:15000] if full_text else fallback_description
        except (TranscriptsDisabled, NoTranscriptFound):
            print(f"      [INFO] Captions unavailable for video {video_id}. Using description.")
            return fallback_description
        except Exception as e:
            print(f"      [WARN] Could not retrieve transcript for {video_id}: {e}")
            return fallback_description

    def get_articles(self, hours: int = 48) -> List[ScrapedArticle]:
        articles: List[ScrapedArticle] = []
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours) if hours > 0 else None

        for channel_name, channel_id in self.channels.items():
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            try:
                feed = feedparser.parse(feed_url)
                if feed.bozo and not feed.entries:
                    print(f"   [WARN] Failed to parse YouTube feed for {channel_name}")
                    continue

                for entry in feed.entries:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if hasattr(entry, "published_parsed") and entry.published_parsed else now

                    # Filter by cutoff time if specified
                    if cutoff_time and published_at < cutoff_time:
                        continue

                    title = getattr(entry, "title", "Untitled Video")
                    url = getattr(entry, "link", "")
                    video_id = getattr(entry, "yt_videoid", "")

                    if not video_id and "v=" in url:
                        video_id = url.split("v=")[1].split("&")[0]

                    if not url or not video_id:
                        continue

                    # Extract description fallback
                    description = getattr(entry, "summary", title)

                    print(f"   Fetching transcript for: [{channel_name}] {title[:40]}...")
                    content = self._get_transcript(video_id, fallback_description=description)

                    articles.append(
                        ScrapedArticle(
                            title=title,
                            url=url,
                            source=f"youtube_{channel_name.lower().replace(' ', '_')}",
                            raw_content=content,
                            published_at=published_at
                        )
                    )
            except Exception as e:
                print(f"   [ERROR] Error scraping channel {channel_name}: {e}")

        return articles
