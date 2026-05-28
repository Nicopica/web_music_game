import json
import os

import streamlit as st
import pandas as pd
import random
import re
import glob
import streamlit.components.v1 as components

from utils import make_name_pretty

# run locally:
# python -m streamlit run app.py
# python -m streamlit run app.py --server.headless true

# link for spotify:
# "https://open.spotify.com/track/" +

LANGUAGE = "es"
POSSIBILITIES = 5

categoryPath = os.path.join(LANGUAGE, f"{LANGUAGE}_categories.json")
with open(categoryPath, "r", encoding="utf-8") as file:
    categories = json.load(file)

st.set_page_config(page_title="Guess the Spanish Word", page_icon="🎵", layout="centered")

csv_files = sorted(glob.glob(LANGUAGE + "/game/*.csv"))

if not csv_files:
    st.error("No CSV files found. Please ensure your playlist CSVs are in the same folder as this script.")
    st.stop()


@st.cache_data
def load_data(filepath):
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        return None

if 'current_song' not in st.session_state:
    st.session_state.current_song = None
# if 'show_hint' not in st.session_state:
#     st.session_state.show_hint = False
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'current_options' not in st.session_state:
    st.session_state.current_options = []
if 'played_songs' not in st.session_state:
    st.session_state.played_songs = []

def reset_game():
    st.session_state.current_song = None
    st.session_state.show_hint = False
    st.session_state.show_answer = False
    st.session_state.current_options = []
    st.session_state.played_songs = []

def turn_on_hint():
    st.session_state.show_hint = True


def turn_on_answer():
    st.session_state.show_answer = True


st.header("Guess the Hidden Word in Spanish!")
st.markdown("""
    <style>
           .block-container {
                padding-top: 3rem;
            }
    </style>
    """, unsafe_allow_html=True)

selected_file = st.selectbox(
    "Choose a Category:",
    options=csv_files,
    format_func=make_name_pretty,
    on_change=reset_game
)

df_playlist = load_data(selected_file)

if df_playlist is None:
    st.error(f"Could not load data from '{selected_file}'.")
else:
    filename = os.path.basename(selected_file)
    cat_key = filename.replace("playlist_", "").replace(".csv", "")
    full_category_words = [w.lower() for w in categories.get(cat_key, [])]

    st.markdown("""
        <style>
            /* Reducir margen superior */
            .block-container {
                padding-top: 2rem;
            }

            /* Ocultar la barra superior de menú de Streamlit */
            header {
                visibility: hidden;
            }

            /* FORZAR la eliminación de la barra de desplazamiento en toda la web */
            *::-webkit-scrollbar {
                display: none !important;
                width: 0px !important;
            }
            * {
                scrollbar-width: none !important; /* Firefox */
                -ms-overflow-style: none !important; /* IE y Edge */
            }
        </style>
        """, unsafe_allow_html=True)

    def new_song():
        # use new songs
        available_songs = df_playlist.drop(st.session_state.played_songs, errors='ignore')
        if available_songs.empty:
            st.toast("All songs played, using played ones!")
            st.session_state.played_songs = []
            available_songs = df_playlist

        sampled = available_songs.sample(n=1)
        st.session_state.current_song = sampled.iloc[0]

        st.session_state.played_songs.append(sampled.index[0])

        possible_options = str(st.session_state.current_song['foundWords']).split(',')
        target_lower = random.choice(possible_options).strip().lower()

        # get words that appear (not options)
        unplayable_raw = str(st.session_state.current_song.get('unplayableWords', ''))
        forbidden_words = [w.strip().lower() for w in unplayable_raw.split(',') if w.strip()]

        # get words from the category that are not in the song and are not the answer
        wrong_words = [w for w in full_category_words if w != target_lower and w not in forbidden_words]
        num_wrong = min(POSSIBILITIES - 1, len(wrong_words))

        #
        options = random.sample(wrong_words, num_wrong) + [target_lower]
        options.sort()
        st.session_state.current_options = options

        # st.session_state.show_hint = False
        st.session_state.show_answer = False

    # press new song
    if st.button("Draw New Song", use_container_width=True, type="primary"):
        new_song()

    if st.session_state.current_song is None:
        new_song()

    if st.session_state.current_options:
        st.write("**Options:** " + " - ".join([opt.title() for opt in st.session_state.current_options]))

    # game flow
    if st.session_state.current_song is not None:
        c = st.session_state.current_song
        target_word = str(c['foundWords']).split(',')[0].strip()
        track_id = str(c['track_id'])

        # if not track_id.startswith('http'):
        #     track_id = "https://" + track_id
        # st.subheader("Listen to the track")
        # st.track_id_button("▶️ OPEN IN SPOTIFY", track_id, use_container_width=True)
        # st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("Listen to the track")

        # Spotify mini reproducer
        iframe_html = f"""
                <iframe style="border-radius:12px" 
                    src="https://open.spotify.com/embed/track/{track_id}?utm_source=generator" 
                    width="100%" 
                    height="152" 
                    frameBorder="0" 
                    allowfullscreen="" 
                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
                    loading="lazy">
                </iframe>
                """

        components.html(iframe_html, height=152)
        st.markdown("<br>", unsafe_allow_html=True)

        # col1, col2 = st.columns(2)

        # with col1:
            # st.button("Context Hint", on_click=turn_on_hint, use_container_width=True)
        # with col2:
        st.button("Reveal Answer", on_click=turn_on_answer, use_container_width=True)

        # if st.session_state.show_hint:
        #     st.subheader("Context Hint")
        #     sentences = str(c['matchedLines'])
        #     first_verse = sentences.split('|')[0].strip()
        #     censored_verse = re.sub(rf'\b{target_word}\b', '***', first_verse, flags=re.IGNORECASE)
        #     censored_verse = re.sub(rf'\[{target_word}\]', '', censored_verse, flags=re.IGNORECASE).strip()
        #     st.warning(f"\"... {censored_verse} ...\"")
        #     st.markdown("---")

        if st.session_state.show_answer:
            sentences = str(c['matchedLines'])
            first_verse = sentences.split('|')[0].strip()

            highlighted_verse = re.sub(
                rf'\b({target_word})\b',
                r'<span style="color: #1DB954; font-weight: bold; font-size: 1.2rem;">\1</span>',
                first_verse,
                flags=re.IGNORECASE
            )

            html_reveal = f"""
                <p style="text-align: center; font-size: 1.5rem; font-style: italic; color: #E0E0E0; margin-top: 20px;">
                    "{highlighted_verse}"
                </p>
            """

            st.markdown(html_reveal, unsafe_allow_html=True)