import tensorflow as tf
import re

def preprocess_tweets(tweets, language="en"):
    documents = []

    for tweet in tweets:

        if isinstance(tweet, dict):
            text = tweet.get("text", "")
            is_quoted = tweet.get("is_quoted", False)
        else:
            text = str(tweet)
            is_quoted = False

        text = text.strip()

        # Replace hashtag
        text = re.sub(r"#\w+", "#HASHTAG#", text)

        # Replace mention
        text = re.sub(r"@\w+", "#USER#", text)

        # Replace URL
        text = re.sub(r"https?://\S+", "#URL#", text)

        # Quoted tweet
        if is_quoted:
            text = f'RT #USER#: "{text}"'

        # Replace newline dengan ";"
        text = re.sub(r"\r?\n+", "; ", text)

        documents.append(
            f"<document>{text}</document>"
        )

    return (
        f'<author lang="{language}">\n'
        "<documents>\n"
        + "\n".join(documents)
        + "\n</documents>\n"
        "</author>"
    )

# Prepocessing untuk di model
def custom_standardization(input_data):
  formatting_removed_es_1 = tf.strings.regex_replace(input_data, '<author lang="es" class="1">\n\t', '<author_lang="es">')
  formatting_removed_es_0 = tf.strings.regex_replace(formatting_removed_es_1, '<author lang="es" class="0">\n\t', '<author_lang="es">')

  formatting_removed_en_1 = tf.strings.regex_replace(formatting_removed_es_0, '<author lang="en" class="1">\n\t', '<author_lang="en">')
  formatting_removed_en_0 = tf.strings.regex_replace(formatting_removed_en_1, '<author lang="en" class="0">\n\t', '<author_lang="en">')

  formatting_removed_id_1 = tf.strings.regex_replace(formatting_removed_en_0, '<author lang="id" class="1">\n\t', '<author_lang="id">')
  formatting_removed_id_0 = tf.strings.regex_replace(formatting_removed_id_1, '<author lang="id" class="0">\n\t', '<author_lang="id">')

  tag_open_CDATA_removed = tf.strings.regex_replace(formatting_removed_id_0, '<\!\[CDATA\[', ' <')
  tag_closed_CDATA_removed = tf.strings.regex_replace(tag_open_CDATA_removed,'\]{1,}>', '')

  tag_open_documents_removed  = tf.strings.regex_replace(tag_closed_CDATA_removed, '<documents>\n(\t){0,2}', '')
  tag_closed_documents_removed = tf.strings.regex_replace(tag_open_documents_removed, '</documents>\n(\t){0,2}', '')

  tag_open_document_whitespace_removed = tf.strings.regex_replace(tag_closed_documents_removed, '<document> ', '<document>')
  tag_closed_document_add_whitespace = tf.strings.regex_replace(tag_open_document_whitespace_removed, '</document>\n(\t){0,2}', '</document> ')

  return  tag_closed_document_add_whitespace