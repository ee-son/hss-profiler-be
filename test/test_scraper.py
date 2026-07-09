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
        username="elonmusk",
        max_tweets=5
    )
    
    print(f"Total : {len(tweets)}\n")

    for tweet in tweets:
        print(tweet)
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(main())
    