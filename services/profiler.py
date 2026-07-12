from services.scraper import TwitterScraper
from services.preprocess import preprocess_tweets
from services.predictor import predict_user

scraper = TwitterScraper()

async def profile_user(username: str, language: str):

    tweets = await scraper.scrape_user(username=username, language=language)

    result = predict_user(
        username=username,
        tweets=tweets,
        language=language
    )

    return result