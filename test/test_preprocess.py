import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from services.preprocess import preprocess_tweets


def main():

    tweets = [
        # Mention
        {
            "tweet_id": "1",
            "text": "@budiman Halo semuanya!"
        },

        # URL + newline
        {
            "tweet_id": "2",
            "text": "Pilih Anies-Sandi atau tidak sama sekali.\nMasa depan DKI ada di tangan Anda.\nhttps://t.co/rloGJPskDu"
        },

        # Tweet biasa
        {
            "tweet_id": "3",
            "text": "Saya sedang mencoba preprocessing."
        },

        # Hashtag
        {
            "tweet_id": "4",
            "text": "Saya suka #anime dan #OnePiece"
        },

        # Mention + URL + Hashtag
        {
            "tweet_id": "5",
            "text": "@elonmusk cek ini https://x.com #tes"
        },

        # Quote tweet
        {
            "tweet_id": "6",
            "text": "Anime yang bagus.",
            "is_quoted": True
        },

        # Quote + Mention + URL + Hashtag
        {
            "tweet_id": "7",
            "text": "@naruto lihat ini\nhttps://x.com #anime",
            "is_quoted": True
        },

        # Multi newline
        {
            "tweet_id": "8",
            "text": "Baris pertama\n\nBaris kedua\r\nBaris ketiga"
        },

        # Emoji
        {
            "tweet_id": "9",
            "text": "🔥 Mantap sekali 😂"
        },

        # Mention berulang
        {
            "tweet_id": "10",
            "text": "@a @b @c Halo semua"
        },
    ]

    author_document = preprocess_tweets(
        tweets=tweets
    )

    print(author_document)


if __name__ == "__main__":
    main()
    