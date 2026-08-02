import os
import json
import re
import glob

from langdetect import detect_langs, LangDetectException
from services.rate_limit import RateLimitError
from services.lang_detector import detect_dominant_language, WrongLanguageError

os.environ["TWS_RAISE_WHEN_NO_ACCOUNT"] = "1"
from twscrape import API
from twscrape.accounts_pool import NoAccountError

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

    async def scrape_user(self, username, language, max_tweets=100):
        tweets_data = []
        validation_tweets = []
        language_validated = False

        # Debug counters
        total_api = 0
        skipped_retweet = 0
        skipped_empty = 0
        skipped_not_meaningful = 0
        skipped_language = 0
        accepted = 0
        skipped_other_user = 0
        waiting_validation = 0

        print(f"[SCRAPE] Query: {username}")

        user = await self.api.user_by_login(username)

        try:
            async for tweet in self.api.user_tweets(
                user.id,
                limit=max_tweets * 2
            ):

                total_api += 1

                is_retweet = tweet.retweetedTweet is not None
                is_quoted = tweet.quotedTweet is not None

                if is_retweet and not is_quoted:
                    skipped_retweet += 1
                    continue

                text = tweet.rawContent.strip()

                if not text:
                    skipped_empty += 1
                    continue

                if not self._has_meaningful_text(text):
                    skipped_not_meaningful += 1
                    continue

                tweet_info = {
                    "tweet_id": tweet.id,
                    "created_at": str(tweet.date),
                    "text": text,
                    "url": tweet.url,
                    "is_quoted": is_quoted,
                }

                # Language validation
                if not language_validated:

                    validation_tweets.append(tweet_info)

                    if len(validation_tweets) < 30:
                        waiting_validation += 1
                        continue

                    detected_language = detect_dominant_language(
                        validation_tweets
                    )

                    if detected_language != language:
                        raise WrongLanguageError(detected_language)

                    language_validated = True

                    for buffered in validation_tweets:

                        keep, detected_lang = self._should_keep_tweet(
                            buffered["text"],
                            language
                        )

                        if not keep:
                            skipped_language += 1
                            continue

                        buffered["language_detected"] = detected_lang
                        tweets_data.append(buffered)
                        accepted += 1

                    validation_tweets.clear()

                    if len(tweets_data) >= max_tweets:
                        break

                    continue

                # ==========================
                # Normal filtering
                # ==========================

                keep, detected_lang = self._should_keep_tweet(
                    text,
                    language
                )

                if not keep:
                    skipped_language += 1
                    continue

                tweet_info["language_detected"] = detected_lang
                tweets_data.append(tweet_info)
                accepted += 1

                print(text[:80])

                if len(tweets_data) >= max_tweets:
                    break

        except NoAccountError:
            retry_at = await self.api.pool.next_available_at(
                "UserTweets"
            )

            print("=" * 50)
            print("Retry at:", retry_at)
            print("=" * 50)

            raise RateLimitError(retry_at)

        print("\n" + "=" * 50)
        print("SCRAPE SUMMARY")
        print("=" * 50)
        print(f"Total from API         : {total_api}")
        print(f"Skipped retweet        : {skipped_retweet}")
        print(f"Skipped empty          : {skipped_empty}")
        print(f"Skipped not meaningful : {skipped_not_meaningful}")
        print(f"Skipped language       : {skipped_language}")
        print(f"Waiting validation     : {waiting_validation}")
        print(f"Accepted               : {accepted}")
        print("=" * 50 + "\n")

        if len(tweets_data) < MIN_TWEETS:
            return []

        return tweets_data
    