import json
import os
import random
import glob
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from data.logic import handle_category_change, new_song
from data.ui import render_options_and_answer
from utils.state import init_session_state
from utils.utils import make_name_pretty, extract_category_key

# run locally:
# python -m .streamlit run app.py
# python -m .streamlit run app.py --server.headless true

LANGUAGE = "es"
# POSSIBILITIES = 5

category_path = os.path.join("data", LANGUAGE, f"{LANGUAGE}_categories.json")

@st.cache_data
def load_categories_json():
    with open(category_path, "r", encoding="utf-8") as file:
        return json.load(file)

@st.cache_data
def get_category_options():
    temp_list = []
    for file in glob.glob("data/es/game/playlist_*.csv"):
        df = pd.read_csv(file)
        cat_name = make_name_pretty(file)
        visual_name = f"{cat_name} ({len(df)})"
        temp_list.append((visual_name, file, len(df)))
    temp_list.sort(key=lambda x: x[2], reverse=True)
    options = {item[0]: item[1] for item in temp_list}
    return options


@st.cache_data
def load_data(filepath):
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        return None

categories = load_categories_json()
category_options = get_category_options()

init_session_state(list(category_options.keys())[0])

# main flow
st.set_page_config(page_title="Guess the Word", page_icon="assets/img/Yohproject-Crayon-Cute-Folder-music.256.png",
                   layout="centered")

# st.header("Guess the Hidden Word in Spanish!")
# st.markdown("""<style>.block-container { padding-top: 3rem; }</style>""", unsafe_allow_html=True)

# categories bar
with st.popover(f"Current category: {st.session_state.visual_category}", use_container_width=True):
    st.radio(
        "",
        options=list(category_options.keys()),
        index=list(category_options.keys()).index(st.session_state.visual_category),
        key="category_selector",
        on_change=handle_category_change,
        label_visibility="collapsed"
    )

selected_file = category_options[st.session_state.visual_category]

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
        }
    </style>
""", unsafe_allow_html=True)

selected_playlist = load_data(selected_file)

cat_key = extract_category_key(selected_file)
full_category_words = [w.lower() for w in categories.get(cat_key, [])]

if st.session_state.current_song is None:
    new_song(selected_playlist, full_category_words)
    st.rerun()

# press new song or there is no song
st.button("Draw New Song", use_container_width=True, type="primary",
          on_click=new_song, args=(selected_playlist, full_category_words))
# game flow
if st.session_state.current_song is not None:
    c = st.session_state.current_song

    # read target word from session state
    target_word = st.session_state.target_word
    track_id = str(c['track_id'])

    # st.subheader("Listen to the track")

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
