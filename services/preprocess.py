from typing import List, Dict

class TweetPreprocessor:
    """
    Mengubah hasil scraping menjadi author document
    dengan format yang sama seperti dataset PAN.
    """

    def preprocess_tweet(self, text: str) -> str:
        return text.strip()

    def build_author_document(
        self,
        username: str,
        tweets: List[Dict],
    ) -> str:
        """
        Input:
            tweets = [
                {"text": "..."},
                {"text": "..."},
            ]

        Output:
            <author id="username">
                <documents>
                    <document><![CDATA[
                    tweet1
                    ]]></document>
                    ...
                </documents>
            </author>
        """

        documents = []

        for tweet in tweets:
            text = tweet.get("text", "")
            text = self.preprocess_tweet(text)

            if not text:
                continue

            documents.append(
                f"<document><![CDATA[\n{text}\n]]></document>"
            )

        xml = (
            f'<author id="{username}">\n'
            "<documents>\n"
            + "\n".join(documents)
            + "\n</documents>\n"
            "</author>"
        )

        return xml

    def preprocess(
        self,
        username: str,
        tweets: List[Dict],
    ) -> str:

        return self.build_author_document(
            username=username,
            tweets=tweets,
        )