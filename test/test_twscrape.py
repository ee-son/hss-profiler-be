import asyncio
from twscrape import API

async def main():
    api = API()

    count = 0

    async for tweet in api.search("from:elonmusk"):
        print(tweet.id, tweet.rawContent[:80])
        count += 1

        if count == 5:
            break

asyncio.run(main())