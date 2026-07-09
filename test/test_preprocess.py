import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from services.preprocess import TweetPreprocessor


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

    preprocessor = TweetPreprocessor()

    author_document = preprocessor.preprocess(
        username="elonmusk",
        tweets=tweets,
    )

    print(author_document)


if __name__ == "__main__":
    main()