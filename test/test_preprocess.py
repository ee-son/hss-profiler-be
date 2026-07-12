import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from services.preprocess import preprocess_tweets


def main():

    tweets = [
        {
            "tweet_id": "1",
            "text": "Halo semuanya!"
        },
        {
            "tweet_id": "2",
            "text": "Ini tweet kedua."
        },
        {
            "tweet_id": "3",
            "text": "Saya sedang mencoba preprocessing."
        },
        {
            "tweet_id": "4",
            "text": "   "      # akan di-skip
        }
    ]

    author_document = preprocess_tweets(
        tweets=tweets
    )

    print(author_document)


if __name__ == "__main__":
    main()
    