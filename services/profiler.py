from services.scraper import TwitterScraper
from services.preprocess import preprocess_tweets
from services.predictor import predict_user

scraper = TwitterScraper()

async def profile_user(username: str):

    tweets = await scraper.scrape_user(username)
    cleaned = [preprocess_tweets(tweet["text"])
               for tweet in tweets]
    result = predict_user(cleaned)

    return result