import glob
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from website.logic import handle_category_change, new_song, handle_language_change
from website.ui import render_options_and_answer
from website.state import init_session_state
from utils.utils import make_name_pretty, extract_category_key, dictionary_languages

# setup
st.set_page_config(
    page_title="Guess the Word",
    page_icon="assets/img/Yohproject-Crayon-Cute-Folder-music.256.png",
    layout="centered"
)
st.markdown("""
    <style>
        /* hide bottom */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# cache
@st.cache_data
def get_category_options(language="esp"):
    temp_list = []
    for file in glob.glob(f"data/{language}/game/playlist_*.csv"):
        df = pd.read_csv(file)
        cat_name = make_name_pretty(file)
        visual_name = f"{cat_name} ({len(df)})"
        temp_list.append((visual_name, file, len(df)))
    temp_list.sort(key=lambda x: x[2], reverse=True)
    return {item[0]: item[1] for item in temp_list}


@st.cache_data
def load_data(filepath):
    return pd.read_csv(filepath)

@st.cache_data
def load_master_categories():
    return pd.read_csv("data/master_categories.csv")

master_dict = load_master_categories()

if 'language' not in st.session_state:
    st.session_state.language = "esp"

current_lang = st.session_state.language
category_options = get_category_options(current_lang)
options_translation = list(dictionary_languages.keys())
options_translation.remove(current_lang)

init_session_state(list(category_options.keys())[0])

if st.session_state.get('visual_category') not in category_options:
    st.session_state.visual_category = list(category_options.keys())[0]

if 'translate_to' not in st.session_state or st.session_state.translate_to not in dictionary_languages:
    st.session_state.translate_to = options_translation[0]

# sidebar
with st.sidebar:
    st.write("**Settings**")

    with st.popover("**Change language**", use_container_width=True):
        st.radio(
            "lan_change",
            options=list(dictionary_languages.keys()),
            format_func=lambda x: dictionary_languages[x],
            key="language",
            on_change=handle_language_change,
            label_visibility="collapsed"
        )

    with st.popover("**Translate word to**", use_container_width=True):
        st.radio(
            "transl_change",
            options=options_translation,
            format_func=lambda x: dictionary_languages[x],
            key="translate_to",
            label_visibility="collapsed"
        )

with st.popover(f"Current: {st.session_state.visual_category}", use_container_width=True):
    st.radio(
        "Select Category",
        options=list(category_options.keys()),
        index=list(category_options.keys()).index(st.session_state.visual_category),
        key="category_selector",
        on_change=handle_category_change,
        label_visibility="collapsed"
    )

st.markdown("""
    <style>
        .block-container { padding-top: 4rem; }
        div[data-baseweb="select"] input { caret-color: transparent !important; pointer-events: none !important; }
    </style>
""", unsafe_allow_html=True)

selected_file = category_options[st.session_state.visual_category]
selected_playlist = load_data(selected_file)
cat_key = extract_category_key(selected_file)

if cat_key.lower() in master_dict['category'].str.lower().values:
    df_cat = master_dict[master_dict['category'].str.lower() == cat_key.lower()]
    full_category_words = df_cat[current_lang].dropna().str.lower().tolist()
else:
    full_category_words = []
    st.warning(f"ERROR: Can't find words for '{cat_key}'.")

if st.session_state.current_song is None:
    new_song(selected_playlist, full_category_words)
    st.rerun()

st.button("Draw New Song", use_container_width=True, type="primary",
          on_click=new_song, args=(selected_playlist, full_category_words))

# game flow
if st.session_state.current_song is not None:
    c = st.session_state.current_song
    target_word = st.session_state.target_word
    track_id = str(c['track_id'])

    # calculate translation
    st.session_state.current_translation = None
    if st.session_state.get('translate_to'):
        idioma_origen = st.session_state.language
        idioma_destino = st.session_state.translate_to

        match = master_dict[master_dict[idioma_origen].str.lower() == target_word.lower()]
        if not match.empty:
            st.session_state.current_translation = str(match.iloc[0][idioma_destino]).capitalize()

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