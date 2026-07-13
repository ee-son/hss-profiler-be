import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import asyncio
from services.scraper import TwitterScraper

async def main():
    scraper = TwitterScraper()

    await scraper.initialize()

    tweets = await scraper.scrape_user(
        username="dukeofmalang",
        language="id",      # <-- tambahkan
        max_tweets=50
    )

    print(f"\nTotal: {len(tweets)}\n")

    for i, tweet in enumerate(tweets, start=1):
        print(f"Tweet #{i}")
        print(tweet)
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(main())
    