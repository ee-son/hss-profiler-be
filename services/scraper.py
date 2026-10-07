import os
import re
from typing import Optional
import requests
from langdetect import detect_langs, LangDetectException
from services.lang_detector import detect_dominant_language, WrongLanguageError

FOREIGN_LANG_THRESHOLD = 0.70
MIN_TWEETS = 50
TWITTER_API_BASE = "https://api.twitterapi.io"

class TwitterAPIError(Exception):
    pass

class TwitterScraper:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key or os.getenv("TWITTERAPI_IO_KEY")
        print(f"[INIT] API key loaded: {bool(self.api_key)} | length={len(self.api_key) if self.api_key else 0}")
        if not self.api_key:
            raise ValueError("TWITTERAPI_IO_KEY environment variable is not set")
        self.timeout = timeout
        self.initialized = False
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": self.api_key, "Accept": "application/json"})

    async def initialize(self):
        if self.initialized:
            return
        await self._initialize()
        self.initialized = True

    async def _initialize(self):
        # Configure twitterapi.io client.
        print("[INIT] Using twitterapi.io")
        print("[INIT] ✓ API key configured")
        self.initialized = True

    def _get(self, endpoint: str, params: dict) -> dict:
        # Send GET request to twitterapi.io.
        url = f"{TWITTER_API_BASE}{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        if response.status_code == 429:
            raise TwitterAPIError("twitterapi.io rate limit exceeded")
        if not response.ok:
            raise TwitterAPIError(f"twitterapi.io error {response.status_code}: {response.text}")
        try:
            return response.json()
        except ValueError:
            raise TwitterAPIError(f"Invalid JSON response from twitterapi.io: {response.text[:500]}")

    def _has_meaningful_text(self, text: str) -> bool:
        # Check whether tweet contains meaningful text.
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"\bRT\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return bool(re.search(r"[A-Za-z0-9]", text))

    def _should_keep_tweet(self, text: str, target_lang: str):
        # Validate tweet language and content.
        if not self._has_meaningful_text(text):
            return False, "only_mentions_rt_images"
        try:
            langs = detect_langs(text)
            for lang in langs:
                if lang.lang != target_lang and lang.prob >= FOREIGN_LANG_THRESHOLD:
                    return False, ", ".join(str(x) for x in langs)
            return True, ", ".join(str(x) for x in langs)
        except LangDetectException:
            return False, "undetected"

    def _get_user(self, username: str) -> dict:
        data = self._get("/twitter/user/info", {"userName": username})
        if isinstance(data, dict) and isinstance(data.get("data"), dict):
            return data["data"]
        raise TwitterAPIError(f"Unexpected user response for @{username}: {data}")

    def _get_tweet_id(self, tweet: dict):
        return tweet.get("id")

    def _get_tweet_text(self, tweet: dict) -> str:
        return (tweet.get("text") or "").strip()

    def _get_tweet_url(self, tweet: dict, username: str) -> Optional[str]:
        return tweet.get("url") or f"https://x.com/{username}/status/{tweet['id']}"

    def _is_retweet(self, tweet: dict) -> bool:
        return tweet.get("retweeted_tweet") is not None

    def _is_quoted(self, tweet: dict) -> bool:
        return tweet.get("quoted_tweet") is not None

    def _get_author_id(self, tweet: dict):
        author = tweet.get("author")
        return author.get("id") if isinstance(author, dict) else None

    def _get_created_at(self, tweet: dict):
        return tweet.get("createdAt")

    def _search_tweets(self, query: str, max_pages: int = 100):
        cursor = None
        seen_ids = set()
        for _ in range(max_pages):
            params = {"query": query, "queryType": "Latest"}
            if cursor:
                params["cursor"] = cursor
            data = self._get("/twitter/tweet/advanced_search", params)
            tweets = data.get("tweets", [])
            if not tweets:
                break
            for tweet in tweets:
                tweet_id = tweet.get("id")
                if not tweet_id or tweet_id in seen_ids:
                    continue
                seen_ids.add(tweet_id)
                yield tweet
            if not data.get("has_next_page"):
                break
            cursor = data.get("next_cursor")
            if not cursor:
                break

    async def scrape_user(self, username, language, max_tweets=100):
        tweets_data = []
        validation_tweets = []
        language_validated = False
        total_api = 0
        skipped_retweet = 0
        skipped_empty = 0
        skipped_not_meaningful = 0
        skipped_language = 0
        skipped_other_user = 0
        accepted = 0
        waiting_validation = 0

        print(f"[SCRAPE] Query: from:{username}")

        # Get target user ID.
        user = self._get_user(username)
        user_id = user.get("id") or user.get("userId")

        if not user_id:
            raise TwitterAPIError(f"Cannot determine user ID for @{username}")
        print(f"[SCRAPE] User: @{username} (id={user_id})")
        query = f"from:{username}"

        try:
            # Fetch tweets from target user.
            for tweet in self._search_tweets(query):
                total_api += 1

                # Verify tweet author.
                tweet_author_id = self._get_author_id(tweet)
                if tweet_author_id is not None and str(tweet_author_id) != str(user_id):
                    skipped_other_user += 1
                    continue
                is_retweet = self._is_retweet(tweet)
                is_quoted = self._is_quoted(tweet)

                if is_retweet:
                    skipped_retweet += 1
                    continue
                text = self._get_tweet_text(tweet)

                if not text:
                    skipped_empty += 1
                    continue

                if not self._has_meaningful_text(text):
                    skipped_not_meaningful += 1
                    continue

                tweet_info = {
                    "tweet_id": self._get_tweet_id(tweet),
                    "created_at": str(self._get_created_at(tweet)),
                    "text": text,
                    "url": self._get_tweet_url(tweet, username),
                    "is_quoted": is_quoted,
                }

                # Collect tweets for initial language validation.
                if not language_validated:
                    validation_tweets.append(tweet_info)
                    if len(validation_tweets) < 30:
                        waiting_validation += 1
                        continue
                    detected_language = detect_dominant_language(validation_tweets)
                    print(f"[LANGUAGE] Dominant: {detected_language} | Expected: {language}")
                    if detected_language != language:
                        raise WrongLanguageError(detected_language)
                    language_validated = True

                    # Process buffered validation tweets.
                    for buffered in validation_tweets:
                        keep, detected_lang = self._should_keep_tweet(buffered["text"], language)
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

                # Validate language for subsequent tweets.
                keep, detected_lang = self._should_keep_tweet(text, language)
                if not keep:
                    skipped_language += 1
                    continue
                tweet_info["language_detected"] = detected_lang
                tweets_data.append(tweet_info)
                accepted += 1
                print(text[:80])
                if len(tweets_data) >= max_tweets:
                    break
        except TwitterAPIError:
            raise

        print("\n" + "=" * 50)
        print("SCRAPE SUMMARY")
        print("=" * 50)
        print(f"Total from API         : {total_api}")
        print(f"Skipped other user     : {skipped_other_user}")
        print(f"Skipped retweet        : {skipped_retweet}")
        print(f"Skipped empty          : {skipped_empty}")
        print(f"Skipped not meaningful : {skipped_not_meaningful}")
        print(f"Skipped language       : {skipped_language}")
        print(f"Waiting validation     : {waiting_validation}")
        print(f"Accepted               : {accepted}")
        print("=" * 50 + "\n")

        return tweets_data
    