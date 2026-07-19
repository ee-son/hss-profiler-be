import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import asyncio
from services.scraper import TwitterScraper
from services.rate_limit import RateLimitError

async def main():
    scraper = TwitterScraper()

    await scraper.initialize()

    try:
        tweets = await scraper.scrape_user(
            username="elonmusk",
            language="en",
            max_tweets=5
        )

        print(f"Total: {len(tweets)}")

    except RateLimitError as e:
        print()
        print("=== RATE LIMIT ===")
        print(e)
        print(f"Retry at : {e.retry_at}")

if __name__ == "__main__":
    asyncio.run(main())
