import glob
import os
from difflib import SequenceMatcher

import pandas as pd
import lyricsgenius
from dotenv import load_dotenv
import re

from read_playlist import get_playlist_tracks
from utils import clean_text, sanitize_filename, clean_title, normalize_text
import json

LANGUAGE = "es"

categoryPath = os.path.join(LANGUAGE, f"{LANGUAGE}_categories.json")
with open(categoryPath, "r", encoding="utf-8") as file:
    categories = json.load(file)

load_dotenv()
GENIUS_ACCESS_TOKEN = os.getenv('GENIUS_ACCESS_TOKEN')
genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)
genius.verbose = False
genius.remove_dict = True

songs_playlist = get_playlist_tracks(LANGUAGE + "/playlist.csv")

generated_playlists = {category: [] for category in categories}
seen_lines_per_cat = {category: [] for category in categories}

os.makedirs(os.path.join(LANGUAGE, 'lyrics'), exist_ok=True)

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


def analyze_lyric(lyrics_text, song_name, artist_name, min_repetitions=4):
    words_per_category = {cat: [] for cat in categories}
    unplayable_per_category = {cat: [] for cat in categories}
    lines_per_category = {cat: [] for cat in categories}
    assigned_categories = set()

    cleaned_lyrics = clean_text(lyrics_text)
    words_in_lyrics = cleaned_lyrics.split()

    forbidden_string = normalize_text(f"{song_name} {artist_name}")

    valid_lines = [line for line in lyrics_text.split('\n') if line.strip()]
    processed_lines = [(line.strip(), clean_text(line).split()) for line in valid_lines]

    for category, keywords in categories.items():
        for keyword in keywords:
            norm_keyword = normalize_text(keyword)

            if re.search(rf'\b{norm_keyword}\b', forbidden_string):
                unplayable_per_category[category].append(keyword)
                continue

            total_count = words_in_lyrics.count(keyword)

            if total_count == 0:
                continue

            if total_count < min_repetitions:
                unplayable_per_category[category].append(keyword)
                continue

            assigned_categories.add(category)
            words_per_category[category].extend([keyword] * total_count)

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
    filepath = os.path.join(LANGUAGE, 'lyrics', filename)

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


for song in songs_playlist:
    process_song(song)
print("\nGenerate CSV files")

# delete old files
game_folder = os.path.join(LANGUAGE, "game")
os.makedirs(game_folder, exist_ok=True)
for old_file in glob.glob(os.path.join(game_folder, "*.csv")):
    os.remove(old_file)

# generate new files
for category, songs in generated_playlists.items():
    # only create category if there are at least 5 songs
    if len(songs) >= 5:
        df_playlist = pd.DataFrame(songs)
        file_name = f"playlist_{category}.csv"
        df_playlist.to_csv(os.path.join(game_folder, file_name), index=False, encoding='utf-8-sig')
        print(f"Saved: {file_name} ({len(songs)} songs with stats and lines)")

print("Finished!")
print(notProcessed)
print(len(notProcessed))