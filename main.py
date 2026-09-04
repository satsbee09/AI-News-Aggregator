import sys
import argparse
from app.config import settings
from app.services.pipeline_service import run_daily_pipeline

# Ensure UTF-8 output encoding across Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def main():
    parser = argparse.ArgumentParser(description="AI News Aggregator & Daily Digest Pipeline")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate local HTML preview and log to DB without sending actual email."
    )
    parser.add_argument(
        "--scrape-only",
        action="store_true",
        help="Only run scrapers to fetch and persist raw articles, skipping LLM and email."
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=48,
        help="Lookback window in hours for scraping articles (default: 48)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of new articles to summarize with LLM per run (default: 10)."
    )

    args = parser.parse_args()

    run_daily_pipeline(
        hours=args.hours,
        limit=args.limit,
        dry_run=args.dry_run,
        scrape_only=args.scrape_only
    )

if __name__ == "__main__":
    main()
