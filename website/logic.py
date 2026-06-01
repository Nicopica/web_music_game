import random
import streamlit as st

POSSIBILITIES = 5

# logic functions
def reset_game():
    st.session_state.answered = False
    st.session_state.current_song = None
    st.session_state.selected_option = None
    st.session_state.current_options = []
    st.session_state.played_songs = []
    st.session_state.target_word = ""
    st.session_state.current_category = None
    st.session_state.translate_to = None

def turn_on_answer():
    st.session_state.answered = True

def handle_category_change():
    st.session_state.visual_category = st.session_state.category_selector
    st.session_state.played_songs = []
    st.session_state.current_song = None

def handle_language_change():
    st.session_state.visual_category = None
    st.session_state.current_song = None
    st.session_state.played_songs = []

def new_song(selected_playlist, full_category_words):
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
