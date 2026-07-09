from services.scraper import scrape_user
from services.preprocess import preprocess_tweets
from services.predictor import predict_user

def profile_user(username):
    tweets = scrape_user(username)
    cleaned = preprocess_tweets(tweets)
    result = predict_user(cleaned)

    return result