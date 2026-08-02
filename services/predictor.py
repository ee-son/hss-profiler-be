import tensorflow as tf

from services.preprocess import (
    preprocess_tweets,
    custom_standardization,
)

from services.ranker import TweetRanker

GENERAL_MODEL = tf.keras.models.load_model(
    "models/best_general_model.keras",
    custom_objects={
        "custom_standardization": custom_standardization
    }
)

ID_MODEL = tf.keras.models.load_model(
    "models/best_general_model_id.keras",
    custom_objects={
        "custom_standardization": custom_standardization
    }
)

GENERAL_RANKER = TweetRanker(
    model=GENERAL_MODEL,
    preprocess_func=preprocess_tweets,
    language="en"
)

ID_RANKER = TweetRanker(
    model=ID_MODEL,
    preprocess_func=preprocess_tweets,
    language="id"
)

def predict_user(
    username: str,
    tweets: list,
    language: str = "id",
    explain: bool = False
):

    if language == "id":
        model = ID_MODEL
        ranker = ID_RANKER
    else:
        model = GENERAL_MODEL
        ranker = GENERAL_RANKER

    print("=" * 50)
    print("Jumlah tweet:", len(tweets))

    if tweets:
        print(type(tweets[0]))
        print(tweets[0])

    print("=" * 50)

    author_text = preprocess_tweets(
        tweets=tweets,
        language=language
    )

    sample = tf.constant(
        [[author_text]],
        dtype=tf.string
    )

    output = model.predict(
        sample,
        verbose=0
    )

    logit = float(output[0][0])

    probability = float(
        tf.sigmoid(logit).numpy()
    )

    label = int(logit > 0)

    confidence = (
        probability
        if label == 1
        else 1 - probability
    )

    response = {
        "username": username,
        "total_tweets": len(tweets),
        "label": label,
        "class": (
            "hate_speech_spreader"
            if label
            else "non_hate_speech_spreader"
        ),
        "confidence": round(confidence, 4)
    }

    if explain:
        explanation = ranker.rank_tweets(
        tweets=tweets,
        predicted_label=label,
        top_k=5
    )

        explanation["method"] = "Leave-One-Out"
        response["explanation"] = explanation

    return response