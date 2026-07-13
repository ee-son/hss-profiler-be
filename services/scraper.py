import asyncio
import json
import re
import glob

from langdetect import detect_langs, LangDetectException
from twscrape import API

FOREIGN_LANG_THRESHOLD = 0.70
MIN_TWEETS = 50

class TwitterScraper:
    def __init__(self, cookies_pattern: str = "config/cookies*.json"):
        self.cookies_pattern = cookies_pattern
        self.cookies_file = None
        self.api = API()
        self.initialized = False

    async def initialize(self):
        if self.initialized:
            return

        await self._initialize()
        self.initialized = True

    async def _initialize(self):
        cookie_files = sorted(glob.glob(self.cookies_pattern))
        if not cookie_files:
            raise Exception("No cookies files found")

        for index, cookie_file in enumerate(cookie_files, start=1):

            print(f"[INIT] Loading {cookie_file}")

            with open(cookie_file, "r", encoding="utf-8") as f:
                cookies_list = json.load(f)

            auth_token = None
            ct0 = None

            for cookie in cookies_list:
                if cookie["name"] == "auth_token":
                    auth_token = cookie["value"]
                elif cookie["name"] == "ct0":
                    ct0 = cookie["value"]

            if not auth_token or not ct0:
                print(f"[INIT] Skip {cookie_file}: missing auth_token/ct0")
                continue

            cookies_string = f"auth_token={auth_token}; ct0={ct0}"

            try:
                await self.api.pool.add_account(
                    username=f"scraper{index}",
                    password="",
                    email="",
                    email_password="",
                    cookies=cookies_string,
                )

                print(f"[INIT] ✓ Added scraper{index}")

            except Exception as e:
                print(f"[INIT] scraper{index} already exists ({e})")

        print("[INIT] TwitterScraper initialized")

    def _has_meaningful_text(self, text: str) -> bool:
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"\bRT\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        return bool(re.search(r"[A-Za-z0-9]", text))

    def _should_keep_tweet(self, text: str, target_lang: str):
        if not self._has_meaningful_text(text):
            return False, "only_mentions_rt_images"

        try:
            langs = detect_langs(text)

            for lang in langs:
                if (
                    lang.lang != target_lang
                    and lang.prob >= FOREIGN_LANG_THRESHOLD
                ):
                    return False, ", ".join(str(x) for x in langs)

            return True, ", ".join(str(x) for x in langs)

        except LangDetectException:
            return False, "undetected"

    async def scrape_user(self, username: str, language: str, max_tweets: int = 100):
        query = f"from:{username}"
        tweets_data = []

        async for tweet in self.api.search(query):

            # Pastikan benar-benar tweet dari user
            if tweet.user.username.lower() != username.lower():
                continue

            is_retweet = tweet.retweetedTweet is not None
            is_quoted = tweet.quotedTweet is not None

            if is_retweet and not is_quoted:
                continue

            text = tweet.rawContent.strip()

            if not text:
                continue

            keep, detected_lang = self._should_keep_tweet(text, language)

            if not keep:
                continue

            tweets_data.append(
                {
                    "tweet_id": tweet.id,
                    "created_at": str(tweet.date),
                    "text": text,
                    "url": tweet.url,
                    "language_detected": detected_lang,
                    "is_quoted": is_quoted,
                }
            )

            if len(tweets_data) >= max_tweets:
                break
        if len(tweets_data) < MIN_TWEETS:
            return []

        return tweets_data
    