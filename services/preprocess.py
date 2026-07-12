def preprocess_tweets(tweets, language="en"):
    documents = []

    for tweet in tweets:
        if isinstance(tweet, dict):
            text = tweet.get("text", "")
        else:
            text = str(tweet)

        text = text.strip()

        documents.append(
            f"<document><{text}</document>"
        )

    return (
        f'<author_lang="{language}">\n'
        + "\n".join(documents)
        + "\n</author>"
    )