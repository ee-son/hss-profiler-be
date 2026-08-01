import tensorflow as tf


class TweetRanker:
    def __init__(self, model, preprocess_func, language="id"):
        """
        Args:
            model: Trained Keras model.
            preprocess_func: preprocess_tweets().
            language: "id", "en", atau "es".
        """
        self.model = model
        self.preprocess = preprocess_func
        self.language = language

    def _predict_probability(self, author_document):
        """
        Predict probability dari satu author document.
        """

        sample = tf.constant(
            [[author_document]],
            dtype=tf.string
        )

        logit = self.model.predict(
            sample,
            verbose=0
        )[0][0]

        return float(tf.sigmoid(logit).numpy())

    def rank_tweets(self, tweets, top_k=5):
        """
        Leave-One-Out Tweet Ranking.

        Args:
            tweets: list[str] atau list[dict]
            top_k: jumlah tweet yang dikembalikan

        Returns:
        {
            "baseline_probability": float,
            "top_tweets": [...]
        }
        """

        # ==========================
        # Bersihkan tweet kosong
        # ==========================

        cleaned_tweets = []

        for tweet in tweets:

            if isinstance(tweet, dict):
                text = tweet.get("text", "").strip()

                if text:
                    cleaned_tweets.append(tweet)

            else:
                text = str(tweet).strip()

                if text:
                    cleaned_tweets.append(text)

        if not cleaned_tweets:
            return {
                "baseline_probability": 0.0,
                "top_tweets": []
            }

        # ==========================
        # Baseline Prediction
        # ==========================

        baseline_document = self.preprocess(
            tweets=cleaned_tweets,
            language=self.language
        )

        baseline_probability = self._predict_probability(
            baseline_document
        )

        # ==========================
        # Build Leave-One-Out Documents
        # ==========================

        documents = []

        for i in range(len(cleaned_tweets)):

            remaining = (
                cleaned_tweets[:i] +
                cleaned_tweets[i + 1:]
            )

            author_document = self.preprocess(
                tweets=remaining,
                language=self.language
            )

            documents.append(author_document)

        # ==========================
        # Batch Prediction
        # ==========================

        inputs = tf.constant(
            [[doc] for doc in documents],
            dtype=tf.string
        )

        logits = self.model.predict(
            inputs,
            verbose=0
        )

        probabilities = tf.sigmoid(
            logits
        ).numpy().flatten()

        # ==========================
        # Calculate Contribution
        # ==========================

        results = []

        for tweet, prob in zip(cleaned_tweets, probabilities):

            if isinstance(tweet, dict):
                tweet_text = tweet.get("text", "")
            else:
                tweet_text = tweet

            contribution = baseline_probability - float(prob)

            results.append({
                "tweet": tweet_text,
                "probability_without": round(float(prob), 4),
                "contribution": round(contribution, 4)
            })

        # Urutkan berdasarkan kontribusi terbesar
        results.sort(
            key=lambda x: x["contribution"],
            reverse=True
        )

        return {
            "baseline_probability": round(
                baseline_probability,
                4
            ),
            "top_tweets": results[:top_k]
        }
    