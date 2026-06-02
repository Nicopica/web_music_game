import glob
import os
import sys
import importlib
import pandas as pd
import lyricsgenius
from dotenv import load_dotenv
import re

from scripts.read_playlist import get_playlist_tracks
from utils.utils import SPACY_MODELS, clean_text, normalize_text, clean_title, sanitize_filename, EXPECTED_SYNTAX

MIN_REPETITIONS = 4
MIN_SONGS = 5
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_CSV_PATH = os.path.join(ROOT_DIR, "data", "master_categories.csv")


class ProcessorPlaylist:
    def __init__(self, language_code):
        self.language = language_code
        self.nlp = None
        self.categories = {}
        self.seen_base_songs = set()
        self.generated_playlists = {}
        self.seen_lines_per_cat = {}
        self.notProcessed = []
        self.lyrics_folder = None
        self.game_folder = None

        load_dotenv()
        genius_token = os.getenv('GENIUS_ACCESS_TOKEN')
        self.genius = lyricsgenius.Genius(genius_token)
        self.genius.verbose = False
        self.genius.remove_dict = True

    def load_lang_model(self):
        """Load model for Spacy"""
        model_name = SPACY_MODELS.get(self.language, "en_core_web_sm")
        try:
            print(f"Loading linguistic model ({model_name})...")
            model_module = importlib.import_module(model_name)
            self.nlp = model_module.load()
        except ImportError:
            print(f"\nERROR: {model_name} is not installed.")
            print(f"Please run: python -m spacy download {model_name} --user")
            sys.exit()

    def prepare_folders(self):
        """create necessary folders for csv"""
        self.game_folder = os.path.join(ROOT_DIR, "data", self.language, "game")
        self.lyrics_folder = os.path.join(ROOT_DIR, "data", self.language, "lyrics")
        os.makedirs(self.lyrics_folder, exist_ok=True)
        os.makedirs(self.game_folder, exist_ok=True)

        df_master = pd.read_csv(MASTER_CSV_PATH)

        for cat in df_master['category'].dropna().unique():
            words = df_master[df_master['category'] == cat][self.language].dropna().astype(str).str.lower().tolist()
            if words:
                self.categories[cat] = words

        self.generated_playlists = {cat: [] for cat in self.categories}
        self.seen_lines_per_cat = {cat: [] for cat in self.categories}
        self.seen_base_songs = set()

    # ---------------------------------------------------------
    # FUNCIONES AUXILIARES (Lógica extraída para evitar anidamiento)
    # ---------------------------------------------------------

    def _fetch_lyrics_with_retry(self, name, artist, filepath):
        """Intenta obtener la letra original, si falla, reintenta con el título limpio"""
        lyrics_text = self.get_lyric(name, artist, filepath)
        if lyrics_text:
            return lyrics_text

        clean_name = clean_title(name)
        lyrics_text = self.get_lyric(clean_name, artist, filepath)

        if lyrics_text:
            print("Found lyrics by changing title!!")
            return lyrics_text

        return None

    def _extract_tokens_and_lines(self, lyrics_text):
        """Procesa el texto con NLP y prepara las líneas para análisis"""
        doc = self.nlp(lyrics_text)
        analyzed_tokens = [
            (token.text.lower(), token.pos_)
            for token in doc
            if not token.is_punct and not token.is_space
        ]
        processed_lines = [
            (line.strip(), clean_text(line).split())
            for line in lyrics_text.split('\n') if line.strip()
        ]
        return analyzed_tokens, processed_lines

    def _evaluate_keyword(self, keyword, category, valid_type_tags, analyzed_tokens, processed_lines, forbidden_string,
                          assigned_categories, words_per_category, unplayable_per_category, lines_per_category):
        """Evalúa una sola palabra clave y la clasifica donde corresponda"""
        norm_keyword = normalize_text(keyword)

        # avoid word if it's on the title
        if re.search(rf'\b{norm_keyword}\b', forbidden_string):
            unplayable_per_category[category].append(keyword)
            return

        # count only if it's the right grammar
        valid_count = sum(
            1 for text, pos in analyzed_tokens
            if text == keyword and pos in valid_type_tags
        )

        # min of repetitions
        if valid_count < MIN_REPETITIONS:
            if valid_count > 0:
                unplayable_per_category[category].append(keyword)
            return

        assigned_categories.add(category)
        words_per_category[category].extend([keyword])

        matching_lines = [
            orig_line for orig_line, line_words in processed_lines
            if keyword in line_words
        ]

        for line in matching_lines:
            if line not in lines_per_category[category]:
                lines_per_category[category].append(line)

    def _save_to_playlists(self, name, artist, track_id, assigned, words_cat, unplayable_cat, lines_cat):
        """Guarda la canción válida en sus categorías correspondientes"""
        for cat in assigned:
            new_matched_lines = " | ".join(lines_cat[cat])

            if not new_matched_lines:
                continue

            self.seen_lines_per_cat[cat].append(new_matched_lines)

            self.generated_playlists[cat].append({
                "name": name,
                "artist": artist,
                "totalMatches": len(words_cat[cat]),
                "foundWords": ", ".join(words_cat[cat]),
                "unplayableWords": ", ".join(unplayable_cat[cat]),
                "matchedLines": new_matched_lines,
                "track_id": track_id
            })

    # ---------------------------------------------------------
    # FUNCIONES PRINCIPALES (Ahora mucho más limpias y legibles)
    # ---------------------------------------------------------

    def get_lyric(self, name, artist, filepath):
        """get lyrics from Genius"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()

        song_data = self.genius.search_song(name, artist)
        if not song_data:
            return ""

        lyrics_text = song_data.lyrics
        if '\n' in lyrics_text:
            lyrics_text = lyrics_text.split('\n', 1)[1]

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(lyrics_text)

        return lyrics_text

    def analyze_lyric(self, lyrics_text, song_name, artist_name):
        """analyze lyrics grammatically"""
        words_per_category = {cat: [] for cat in self.categories}
        unplayable_per_category = {cat: [] for cat in self.categories}
        lines_per_category = {cat: [] for cat in self.categories}
        assigned_categories = set()

        analyzed_tokens, processed_lines = self._extract_tokens_and_lines(lyrics_text)
        forbidden_string = normalize_text(f"{song_name} {artist_name}")

        for category, keywords in self.categories.items():
            valid_type_tags = EXPECTED_SYNTAX.get(category, [])

            for keyword in keywords:
                self._evaluate_keyword(
                    keyword, category, valid_type_tags, analyzed_tokens, processed_lines,
                    forbidden_string, assigned_categories, words_per_category,
                    unplayable_per_category, lines_per_category
                )

        return assigned_categories, words_per_category, unplayable_per_category, lines_per_category

    def process_song(self, song):
        """prepare download and lyrics processing"""
        name = str(song['name'])
        raw_artist = song['artist']
        artist = ", ".join(raw_artist) if isinstance(raw_artist, list) else str(raw_artist)
        track_id = str(song["id"])

        # look for duplicate songs by lines to not add more than once
        base_name = clean_title(name).lower()
        artist_lower = artist.lower()

        if (base_name, artist_lower) in self.seen_base_songs:
            print(f"-> [DUPLICATE] Skipping '{name}'. Base version already processed.")
            return

        filename = sanitize_filename(f"{artist}_{name}.txt")
        filepath = os.path.join(self.lyrics_folder, filename)

        try:
            lyrics_text = self._fetch_lyrics_with_retry(name, artist, filepath)

            if not lyrics_text:
                self.notProcessed.append(name)
                return

            assigned, words_cat, unplayable_cat, lines_cat = self.analyze_lyric(lyrics_text, name, artist)

            if not assigned:
                return

            self.seen_base_songs.add((base_name, artist_lower))
            self._save_to_playlists(name, artist, track_id, assigned, words_cat, unplayable_cat, lines_cat)

        except Exception as e:
            print(f"Error processing {name}: {e}")

    def execute(self):
        """principal method to call everything for one language"""
        print(f"\nStarting analysis for: {self.language.upper()}")
        self.load_lang_model()
        self.prepare_folders()

        # get list of songs
        path_csv = os.path.join(ROOT_DIR, "data", self.language, "playlist.csv")
        try:
            songs_playlist = get_playlist_tracks(path_csv)
        except Exception as e:
            print(f"cant load data for {self.language}: {e}")
            return

        # process all songs
        for count, song in enumerate(songs_playlist):
            if count % 100 == 0:
                print(f"{count}/{len(songs_playlist)}")
            self.process_song(song)

        print(f"\nGenerating files for {self.language}...")

        # delete old files
        for old_file in glob.glob(os.path.join(self.game_folder, "*.csv")):
            os.remove(old_file)

        # generate new files
        for category, songs in self.generated_playlists.items():
            if len(songs) >= MIN_SONGS:
                df_playlist = pd.DataFrame(songs)
                file_name = f"playlist_{category}.csv"
                df_playlist.to_csv(os.path.join(self.game_folder, file_name), index=False, encoding='utf-8-sig')
                print(f"Saved: {file_name} ({len(songs)} songs)")

        if self.notProcessed:
            print(f"Not processed songs for {self.language}: {len(self.notProcessed)}")