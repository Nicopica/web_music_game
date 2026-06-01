import glob
import os
import sys
from difflib import SequenceMatcher
import pandas as pd
import lyricsgenius
from dotenv import load_dotenv
import re
import spacy

from read_playlist import get_playlist_tracks
from utils.utils import clean_text, sanitize_filename, clean_title, normalize_text, SPACY_MODELS, EXPECTED_SYNTAX, \
    dictionary_languages

MIN_REPETITIONS = 4 # min words for song
MIN_SONGS = 5 # min songs per category

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MASTER_CSV_PATH = os.path.join(ROOT_DIR, "data", "master_categories.csv")

df_master = pd.read_csv(MASTER_CSV_PATH)

load_dotenv()
GENIUS_ACCESS_TOKEN = os.getenv('GENIUS_ACCESS_TOKEN')
genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)
genius.verbose = False
genius.remove_dict = True

path_csv = os.path.join("data", language, "playlist.csv")
songs_playlist = get_playlist_tracks(path_csv)

generated_playlists = {category: [] for category in categories}
seen_lines_per_cat = {category: [] for category in categories}

os.makedirs(os.path.join(ROOT_DIR, "data", language, 'lyrics'), exist_ok=True)

model_name = SPACY_MODELS.get(language, "en_core_web_sm")
try:
    print(f"Loading linguistic model ({model_name})...")
    nlp = spacy.load(model_name)
except OSError:
    print(f"\nERROR: {model_name} is not installed.")
    sys.exit()

def get_lyric(name, artist, filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    song_data = genius.search_song(name, artist)
    if not song_data:
        return ""

    lyrics_text = song_data.lyrics
    if '\n' in lyrics_text:
        lyrics_text = lyrics_text.split('\n', 1)[1]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(lyrics_text)

    return lyrics_text


def analyze_lyric(lyrics_text, song_name, artist_name):
    words_per_category = {cat: [] for cat in categories}
    unplayable_per_category = {cat: [] for cat in categories}
    lines_per_category = {cat: [] for cat in categories}
    assigned_categories = set()

    doc = nlp(lyrics_text)

    analyzed_tokens = [
        (token.text.lower(), token.pos_)
        for token in doc
        if not token.is_punct and not token.is_space
    ]

    cleaned_lyrics = clean_text(lyrics_text)
    words_in_lyrics = cleaned_lyrics.split()

    forbidden_string = normalize_text(f"{song_name} {artist_name}")

    valid_lines = [line for line in lyrics_text.split('\n') if line.strip()]
    processed_lines = [(line.strip(), clean_text(line).split()) for line in valid_lines]

    for category, keywords in categories.items():
        valid_type_tags = EXPECTED_SYNTAX.get(category)

        for keyword in keywords:
            norm_keyword = normalize_text(keyword)

            # avoid word if it's in string
            if re.search(rf'\b{norm_keyword}\b', forbidden_string):
                unplayable_per_category[category].append(keyword)
                continue

            # only count if it's the right type of word
            valid_count = sum(
                1 for text, pos in analyzed_tokens
                if text == keyword and pos in valid_type_tags
            )

            if valid_count == 0:
                continue

            if valid_count < MIN_REPETITIONS:
                unplayable_per_category[category].append(keyword)
                continue

            assigned_categories.add(category)
            words_per_category[category].extend([keyword])

            matching_lines = [
                orig_line
                for orig_line, line_words in processed_lines
                if keyword in line_words
            ]
            lines_per_category[category].extend(matching_lines)

    return assigned_categories, words_per_category, unplayable_per_category, lines_per_category
notProcessed = []

def process_song(song):
    name = song['name']
    artist = song['artist']
    track_id = song["id"]

    print(f"Searching lyrics for: {name} - {artist}...")

    filename = sanitize_filename(f"{artist}_{name}.txt")
    filepath = os.path.join(ROOT_DIR, "data", language, 'lyrics', filename)

    try:
        lyrics_text = get_lyric(name, artist, filepath)

        if not lyrics_text:
            cleanName = clean_title(name)
            print(f"  -> Retrying with cleaner title: '{cleanName}'")
            lyrics_text = get_lyric(cleanName, artist, filepath)

        if not lyrics_text:
            print("  -> Couldn't find lyrics even with clean title. Skipping song.")
            notProcessed.append(name)
            return ""

        print("Lyrics found!")

        assigned_categories, words_per_cat, unplayable_per_cat, lines_per_cat = analyze_lyric(lyrics_text, name, artist)

        if not assigned_categories:
            print(f"  -> No word appeared at least 4 times '{name}'.")
            return

        for cat in assigned_categories:
            new_matched_lines = " | ".join(lines_per_cat[cat])

            is_duplicate = False
            for seen_lines in seen_lines_per_cat[cat]:
                # if lines are very close, then the song is probably the same and it's skipped
                similarity = SequenceMatcher(None, new_matched_lines, seen_lines).ratio()
                if similarity > 0.9:
                    is_duplicate = True
                    break

            if is_duplicate:
                print(f"  -> Skipping duplicate version based on lyrics: {name}")
                continue

            seen_lines_per_cat[cat].append(new_matched_lines)

            generated_playlists[cat].append({
                "name": name,
                "artist": artist,
                "totalMatches": len(words_per_cat[cat]),
                "foundWords": ", ".join(words_per_cat[cat]),
                "unplayableWords": ", ".join(unplayable_per_cat[cat]),
                "matchedLines": new_matched_lines,
                "track_id": track_id
            })

    except Exception as e:
        print(f"Error processing {name}: {e}")

def process_language(language="esp"):
    GAME_FOLDER = os.path.join(ROOT_DIR, "data", language, "game")
    LYRICS_FOLDER = os.path.join(ROOT_DIR, "data", language, "lyrics")
    os.makedirs(LYRICS_FOLDER, exist_ok=True)

    categories = {}
    for cat in df_master['category'].dropna().unique():
        words = df_master[df_master['category'] == cat][language].dropna().astype(str).str.lower().tolist()
        if words:
            categories[cat] = words

    for song in songs_playlist:
        process_song(song)
    print("\nGenerate CSV files")

    # delete old files
    os.makedirs(GAME_FOLDER, exist_ok=True)
    for old_file in glob.glob(os.path.join(ROOT_DIR, GAME_FOLDER, "*.csv")):
        os.remove(old_file)

    # generate new files
    for category, songs in generated_playlists.items():
        # only create category if there are at least 5 songs
        if len(songs) >= MIN_SONGS:
            df_playlist = pd.DataFrame(songs)
            file_name = f"playlist_{category}.csv"
            df_playlist.to_csv(os.path.join(GAME_FOLDER, file_name), index=False, encoding='utf-8-sig')
            print(f"Saved: {file_name} ({len(songs)} songs with stats and lines)")

    print("Finished!")
    print(notProcessed)
    print(len(notProcessed))

def main():
    languages = dictionary_languages.items()
    for l in languages:
        process_language(l)

if __name__ == '__main__':
    main()
