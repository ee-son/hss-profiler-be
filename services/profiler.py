import asyncio
from services.scraper import TwitterScraper
from services.preprocess import preprocess_tweets
from services.predictor import predict_user

scraper = TwitterScraper()

async def profile_user(username: str, language: str):

    tweets = await scraper.scrape_user(username=username, language=language)

    try:
        tweets = await asyncio.wait_for(
            scraper.scrape_user(username, language),
            timeout=30
        )
    except asyncio.TimeoutError:
        raise RuntimeError(
            "Twitter is temporarily rate limited. Please try again in a few minutes."
        )

    result = predict_user(
        username=username,
        tweets=tweets,
        language=language
    )

    return result