import tensorflow as tf

from services.preprocess import (
    preprocess_tweets,
    custom_standardization,
)

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


def predict_user(username: str, tweets: list, language: str = "id"):
    if language == "id":
        model = ID_MODEL
    else:
        model = GENERAL_MODEL
        
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
        "class": "hate_speech_spreader" if label else "non_hate_speech_spreader",
        "probability": round(probability, 4)
    }