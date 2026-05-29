import re
import streamlit as st


def inject_pill_css(is_correct):
    # doesnt work?
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
