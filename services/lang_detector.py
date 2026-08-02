from collections import Counter
from langdetect import detect, LangDetectException

LANGUAGE_NAME = {
    "id": "Indonesian",
    "en": "English",
    "es": "Spanish",
}


class WrongLanguageError(Exception):
    def __init__(self, detected_language: str):
        self.detected_language = detected_language

        language_name = LANGUAGE_NAME.get(
            detected_language,
            detected_language
        )

        super().__init__(
            f"The tweets appear to be predominantly "
            f"{language_name}. "
            f"Please select {language_name}."
        )


def detect_dominant_language(tweets):
    counter = Counter()

    for tweet in tweets:
        text = tweet["text"].strip()

        if not text:
            continue

        try:
            lang = detect(text)

            if lang in LANGUAGE_NAME:
                counter[lang] += 1

        except LangDetectException:
            continue

    if not counter:
        return None

    return counter.most_common(1)[0][0]