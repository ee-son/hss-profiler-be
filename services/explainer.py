import re
import tensorflow as tf


class WordExplainer:
    def __init__(self, model, preprocess_func, language="id"):
        self.model = model
        self.preprocess = preprocess_func
        self.language = language

    def _predict(self, tweet):
        """
        Predict probability untuk SATU tweet.
        """

        author_doc = self.preprocess(
            tweets=[tweet],
            language=self.language
        )

        logit = self.model.predict(
            [author_doc],
            verbose=0
        )[0][0]

        return float(tf.sigmoid(logit))

    def explain(self, tweet, top_k=5):
        """
        Leave-One-Word-Out.

        Returns:
            [
                {
                    "word": "...",
                    "contribution": 0.123
                }
            ]
        """

        baseline = self._predict(tweet)

        words = tweet.split()

        if len(words) == 0:
            return []

        results = []

        for i, word in enumerate(words):

            # hapus satu kata
            new_words = words[:i] + words[i+1:]

            new_tweet = " ".join(new_words)

            prob = self._predict(new_tweet)

            contribution = baseline - prob

            results.append({
                "word": word,
                "contribution": round(contribution, 4)
            })

        results.sort(
            key=lambda x: x["contribution"],
            reverse=True
        )

        return results[:top_k]