import os
import datetime
import streamlit as st
from dotenv import load_dotenv
from utils import (
    load_css,
    get_theme,
    STICKY_HEADER,
    get_chat_history,
    get_unique_dates,
    navigate_to_element,
    display_chat_history
)

# CONFIGURATION
load_css()
load_dotenv()
CHAT_FILE = os.getenv('CHAT_FILE')
CHAT_DIRECTORY = os.getenv('CHAT_DIRECTORY')
PATH = os.path.join(CHAT_DIRECTORY, CHAT_FILE)

# LOAD CHAT HISTORY
if "history" not in st.session_state and "history_df" not in st.session_state:
    st.session_state.history, st.session_state.history_df = get_chat_history(PATH)

# LOAD ALL USERS
if 'users' not in st.session_state:
    st.session_state.users = list(st.session_state.history_df['username'].unique())
    st.session_state.users.remove("SYSTEM")

# SIDEBAR SETTINGS
with st.sidebar:
    theme = get_theme()
    user = st.radio("Who is user?", st.session_state.users)
    opponent = [u for u in st.session_state.users if u != user][0]
    
    go_to_date = st.selectbox(
        "Go to date", get_unique_dates(st.session_state.history_df),
        index=None, placeholder="Select a date"
    )

    if go_to_date is not None:
        navigate_to_element(go_to_date)

# CUSTOM CSS FOR THE STICKY HEAADER
# https://discuss.streamlit.io/t/is-it-possible-to-create-a-sticky-header/33145/3
header = st.container()
header.title(opponent)
header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)
header_background = '#0e1117' if theme['base'] == 'dark' else '#ffffff'
st.markdown(STICKY_HEADER.format(header_background=header_background), unsafe_allow_html=True)

# GETTING INPUT MESSAGE
input_message = st.chat_input("Say something")
if input_message:
    current_datetime = datetime.datetime.now()
    st.session_state.history.append({
        'datetime': current_datetime,
        'username': user,
        'message': input_message,
        'is_file': False
    })

    st.session_state.history_df.loc[len(st.session_state.history_df)] = [
        current_datetime,
        user,
        input_message,
        False
    ]

# DISPLAY CHAT
st.session_state.history = display_chat_history(user, st.session_state.history_df)
