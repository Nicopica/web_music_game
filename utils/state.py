import streamlit as st

# session state variables
def init_session_state(default_category):
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
    if 'visual_category' not in st.session_state:
        st.session_state.visual_category = default_category

