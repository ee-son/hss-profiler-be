import tensorflow as tf

from services.preprocess import (
    preprocess_tweets,
    custom_standardization,
)

MODEL_PATH = "models/best_general_model.keras"

model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={
        "custom_standardization": custom_standardization
    }
)


def predict_user(username: str, tweets: list, language: str = "id"):
    author_text = preprocess_tweets(
        tweets=tweets,
        language=language
    )

    sample = tf.constant([[author_text]])

    output = model.predict(sample, verbose=0)

    logit = float(output[0][0])
    probability = float(tf.sigmoid(logit).numpy())

    label = int(logit > 0)

    return {
        "username": username,
        "total_tweets": len(tweets),
        "label": label,
        "class": "hate_speech" if label else "non_hate_speech",
        "probability": round(probability, 4)
    }