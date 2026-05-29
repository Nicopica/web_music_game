import json
import os
import random
import re
import glob
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from utils.utils import make_name_pretty

# run locally:
# python -m .streamlit run app.py
# python -m .streamlit run app.py --server.headless true

LANGUAGE = "es"
POSSIBILITIES = 5

categoryPath = os.path.join("data", LANGUAGE, f"{LANGUAGE}_categories.json")
with open(categoryPath, "r", encoding="utf-8") as file:
    categories = json.load(file)

category_options = {}

for file in glob.glob("data/es/game/playlist_*.csv"):
    df = pd.read_csv(file)
    cat_name = make_name_pretty(file)
    visual_name = f"{cat_name} ({len(df)})"
    category_options[visual_name] = file


@st.cache_data
def load_data(filepath):
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        return None

# session state variables
if 'current_song' not in st.session_state:
    st.session_state.current_song = None
if 'current_options' not in st.session_state:
    st.session_state.current_options = []
if 'played_songs' not in st.session_state:
    st.session_state.played_songs = []
if 'target_word' not in st.session_state:
    st.session_state.target_word = ""
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'selected_option' not in st.session_state:
    st.session_state.selected_option = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'current_category' not in st.session_state:
    st.session_state.current_category = None

# logic functions
def reset_game():
    st.session_state.answered = False
    st.session_state.current_song = None
    st.session_state.selected_option = None
    st.session_state.current_options = []
    st.session_state.played_songs = []
    st.session_state.target_word = ""

def turn_on_hint():
    st.session_state.show_hint = True

def turn_on_answer():
    st.session_state.answered = True

def new_song():
    # use new songs
    available_songs = selected_playlist.drop(st.session_state.played_songs, errors='ignore')
    if available_songs.empty:
        st.toast("All songs played, using played ones!")
        st.session_state.played_songs = []
        available_songs = selected_playlist

    sampled = available_songs.sample(n=1)
    st.session_state.current_song = sampled.iloc[0]
    st.session_state.played_songs.append(sampled.index[0])

    possible_options = str(st.session_state.current_song['foundWords']).split(',')
    target_lower = random.choice(possible_options).strip().lower()

    # get words that appear (not options)
    unplayable_raw = str(st.session_state.current_song.get('unplayableWords', ''))
    forbidden_words = [w.strip().lower() for w in unplayable_raw.split(',') if w.strip()]

    # correct words that didn't get selected are also not playable
    for w in possible_options:
        if w.lower() != target_lower:
            forbidden_words.append(w.lower())

    # get words from the category that are not in the song and are not the answer
    wrong_words = [w for w in full_category_words if w != target_lower and w not in forbidden_words]
    num_wrong = min(POSSIBILITIES - 1, len(wrong_words))

    # get options
    options_raw = random.sample(wrong_words, num_wrong) + [target_lower]
    options = [opt.title() for opt in options_raw]
    options.sort()

    # new states
    st.session_state.current_options = options
    st.session_state.target_word = target_lower
    st.session_state.selected_option = None
    st.session_state.answered = False

# visual functions
def put_options(options, target_word):
    # distribute options in columns like bubbles
    cols = st.columns(len(options))
    for i, option in enumerate(options):
        with cols[i]:
            # button for each option
            if st.button(option.title(), key=f"btn_{i}_{option}", use_container_width=True):
                if option.lower() == target_word.lower():
                    st.markdown(
                        "<p style='color: #1DB954; font-size: 1.2rem; font-weight: bold; text-align: center; margin-top: 15px;'>Respuesta correcta</p>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        "<p style='color: #FF4B4B; font-size: 1.2rem; font-weight: bold; text-align: center; margin-top: 15px;'>Respuesta incorrecta</p>",
                        unsafe_allow_html=True
                    )

def answered(matched_lines, target_word):
    sentences = str(matched_lines)
    raw_verse = ""
    for line in sentences.split('|'):
        if re.search(rf'\b{target_word}\b', line, re.IGNORECASE):
            raw_verse = line.strip()
            break

    highlighted_verse = re.sub(
        rf'\b({target_word})\b',
        r'<span style="color: #1DB954; font-weight: bold; font-size: 1.8rem;">\1</span>',
        raw_verse,
        flags=re.IGNORECASE
    )

    html_reveal = f"""
        <p style="text-align: center; font-size: 1.5rem; font-style: italic; color: #E0E0E0; margin-top: 20px;">
            "{highlighted_verse}"
        </p>
    """
    st.markdown(html_reveal, unsafe_allow_html=True)


def inject_pill_css(is_correct):
    """Inyecta el CSS dinámico para colorear la burbuja seleccionada."""
    pill_color = "#1DB954" if is_correct else "#FF4B4B"
    st.markdown(f"""
        <style>
            div[data-testid="stPills"] label[data-selected="true"] {{
                background-color: {pill_color} !important;
                color: white !important;
                border-color: {pill_color} !important;
            }}
        </style>
    """, unsafe_allow_html=True)

def render_options_and_answer(options, target_word, matched_lines):
    is_disabled = st.session_state.answered or st.session_state.show_answer

    current_track_id = st.session_state.current_song['track_id']

    selection = st.pills(
        "Options:",
        options=options,
        key=f"word_pills_{current_track_id}",  # to avoid making ghost pills
        default=st.session_state.selected_option,
        disabled=is_disabled
    )


    if selection and not st.session_state.answered:
        st.session_state.answered = True
        st.session_state.selected_option = selection
        st.rerun()

    if not is_disabled:
        return

    selected = st.session_state.selected_option
    is_correct = (selected.lower() == target_word.lower()) if selected else False

    if selected:
        inject_pill_css(is_correct)

    status_msg = get_status_message(selected, is_correct)
    highlighted_verse = format_highlighted_verse(matched_lines, target_word)

    html_reveal = f"""
        <p style="text-align: center; font-size: 1.5rem; font-style: italic; margin-top: 20px;">
            {status_msg} The word was <b>{target_word.title()}</b><br><br>
            "{highlighted_verse}"
        </p>
    """
    st.markdown(html_reveal, unsafe_allow_html=True)

def get_status_message(selected_option, is_correct):
    # error
    if not selected_option:
        return "<span style='color: gray; font-weight: bold;'>Answer shown.</span>"
    # right answer
    if is_correct:
        return "<span style='color: #1DB954; font-weight: bold;'>Right!</span>"

    # wrong answer
    return "<span style='color: #FF4B4B; font-weight: bold;'>Wrong.</span>"

  # gets sentence with the target word and highlights it
def format_highlighted_verse(matched_lines, target_word):
    raw_verse = ""
    for line in str(matched_lines).split('|'):
        if re.search(rf'\b{target_word}\b', line, re.IGNORECASE):
            raw_verse = line.strip()
            break

    return re.sub(
        rf'\b({target_word})\b',
        r'<span style="color: #1DB954; font-weight: bold; font-size: 1.8rem;">\1</span>',
        raw_verse,
        flags=re.IGNORECASE
    )

# main flow
st.set_page_config(page_title="Guess the Word", page_icon="assets/img/Yohproject-Crayon-Cute-Folder-music.256.png",
                   layout="centered")

st.header("Guess the Hidden Word in Spanish!")
st.markdown("""<style>.block-container { padding-top: 3rem; }</style>""", unsafe_allow_html=True)

selected_visual_name = st.selectbox("Change Category", options=list(category_options.keys()))
selected_file = category_options[selected_visual_name]

st.markdown("""
    <style>
        /* hide blinking cursor and touch events on selectbox */
        div[data-baseweb="select"] input { caret-color: transparent !important; pointer-events: none !important; }
        
        /* reduce top margin */
        .block-container { padding-top: 2rem; }
        
        /* hide .streamlit header */
        header { visibility: hidden; }
        
        /* force hide scrollbar globally */
        *::-webkit-scrollbar { display: none !important; width: 0px !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        /* change button to darker blue on hover */
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: #0056b3 !important;
            border-color: #0056b3 !important;
        }
    </style>
""", unsafe_allow_html=True)

selected_playlist = load_data(selected_file)

if selected_playlist is None:
    st.error(f"Could not load data from '{selected_file}'.")
else:
    filename = os.path.basename(selected_file)
    cat_key = filename.replace("playlist_", "").replace(".csv", "")
    full_category_words = [w.lower() for w in categories.get(cat_key, [])]

    # category change, so new song
    if st.session_state.current_category != selected_file:
        st.session_state.current_category = selected_file
        new_song()

    if st.session_state.current_song is None:
        new_song()
        st.rerun()

    # press new song or there is no song
    st.button("Draw New Song", use_container_width=True, type="primary", on_click=new_song)

    # game flow
    if st.session_state.current_song is not None:
        c = st.session_state.current_song

        # read target word from session state
        target_word = st.session_state.target_word
        track_id = str(c['track_id'])

        st.subheader("Listen to the track")

        # spotify mini player
        iframe_html = f"""
            <iframe style="border-radius:12px" 
                src="https://open.spotify.com/embed/track/{track_id}?utm_source=generator" 
                width="100%" height="152" frameBorder="0" allowfullscreen="" 
                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
                loading="lazy">
            </iframe>
        """
        components.html(iframe_html, height=152)
        st.markdown("<br>", unsafe_allow_html=True)

        render_options_and_answer(st.session_state.current_options, target_word, c['matchedLines'])
        # render options outside
        # put_options(st.session_state.current_options, target_word)

        # st.button("Reveal Answer", on_click=turn_on_answer, use_container_width=True)

        # if st.session_state.answered:
            # pass params to function
            # answered(c['matchedLines'], target_word)