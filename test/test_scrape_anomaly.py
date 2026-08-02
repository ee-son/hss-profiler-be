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

    tweets = await scraper.scrape_user(
        username="",
        language="en",
        max_tweets=100
    )

    print("=" * 50)
    print(f"Jumlah tweet: {len(tweets)}")
    print("=" * 50)

    for i, tweet in enumerate(tweets[:10], start=1):
        print(f"{i}. {tweet['text'][:100]}")
        print()


if __name__ == "__main__":
    asyncio.run(main())