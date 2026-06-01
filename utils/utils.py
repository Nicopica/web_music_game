import os
import re
import unicodedata

dictionary_languages = {"esp": "Español", "eng": "English", "sve": "Svenska", "deu": "Deutsch", "cat": "Català"}
prepositions_languages = {"esp": "eng", "eng": "in", "sve": "på", "deu": "auf", "cat": "eng"}

# python -m spacy download sv_core_news_sm
# python -m spacy download es_core_news_sm
# python -m spacy download en_core_web_sm
# python -m spacy download de_core_news_sm
# python -m spacy download ca_core_news_sm

SPACY_MODELS = {
    "esp": "es_core_news_sm",
    "eng": "en_core_web_sm",
    "deu": "de_core_news_sm",
    "sve": "sv_core_news_sm",
    "cat": "ca_core_news_sm"
}

# expected type
EXPECTED_SYNTAX = {
    "colors": ["ADJ", "NOUN"],
    "numbers": ["NUM", "NOUN", "PRON"],
    "animals": ["NOUN", "PROPN"],
    "food_drinks": ["NOUN", "PROPN"],
    "body_parts": ["NOUN"],
    "weather_nature": ["NOUN", "PROPN"],
    "humans_family": ["NOUN", "PROPN"],
    "emotions_feelings": ["NOUN", "ADJ", "VERB"],
    "places_locations": ["NOUN", "PROPN"],
    "transport": ["NOUN", "PROPN"],
    "time_seasons": ["NOUN", "ADV"],
    "clothes": ["NOUN"],
    "directions": ["ADV", "ADP", "NOUN"],
    "swear_words": ["INTJ", "NOUN", "VERB", "ADJ", "PROPN"]
}

def clean_text(text):
    return re.sub(r'[^\w\s]', '', text)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

def normalize_text(text):
    text = unicodedata.normalize('NFD', text)
    return text.encode('ascii', 'ignore').decode("utf-8").lower()

def clean_title(name):
    name = re.sub(r'\(.*?\)|\[.*?]', '', name)
    name = name.split(' - ')[0]
    name = re.split(
        r'(?i)\s+\b(?:feat\.?|with|con|remix|versión|version|akustik|ny|radio'
        r'|remasterizado|remastered|remaster|edited|eng vivo|live|original|mix|acoustic|20|19|from)\b', name)[0]
    return name.strip()

# def make_name_pretty(path):
#     filename = os.path.basename(path)
#     clean_name = filename.replace('playlist_', '').replace('.csv', '')
#     return clean_name.replace('_', ' ').title()

def extract_category_key(path):
    filename = os.path.basename(path)
    return filename.replace('playlist_', '').replace('.csv', '')

def make_name_pretty(path):
    raw_key = extract_category_key(path)
    return raw_key.replace('_', ' ').title()
