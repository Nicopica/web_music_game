import os
import re

import unicodedata


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
        r'(?i)\s+\b(?:feat\.?|with|con|remix|versión|remasterizado|remastered|edited|en vivo|live)\b', name)[0]

    return name.strip()

def make_name_pretty(name):
    name = os.path.basename(name)
    name = name.replace('playlist_', '')
    name = name.replace('.csv', '')
    return name.replace('_', ' ').title()
