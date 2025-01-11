import os
import time
import base64
import zipfile
import pandas as pd
import streamlit as st
from pathlib import Path
from streamlit_theme import st_theme
from parser import WhatssAppParser
from streamlit.components.v1 import html


# https://discuss.streamlit.io/t/is-it-possible-to-create-a-sticky-header/33145/3
STICKY_HEADER = '''
<style>
    div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {{
        position: sticky;
        top: 2.875rem;
        width: 101%;
        background-color: {header_background};
        z-index: 999;
    }}
        
    .fixed-header {{
        border-bottom: 0px solid black;
    }}
</style>
'''


def get_theme(key: str = None) -> dict:
    theme = st_theme(key=key)
    time.sleep(1)
    return theme


def load_css() -> None:
    with open(os.path.join('static', 'styles.css'), "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)


# https://stackoverflow.com/questions/70932538/how-to-center-the-title-and-an-image-in-streamlit
def image_to_bytes(image_path: str) -> str:
    image_bytes = Path(image_path).read_bytes()
    encoded = base64.b64encode(image_bytes).decode()
    return encoded


def get_unique_dates(history_df: pd.DataFrame) -> list:
    return [
        date.strftime('%Y-%m-%d') for date in
        sorted(history_df["datetime"].dt.date.unique(), reverse=True)
    ]


# IMPORTANT: Cache the conversion to prevent computation on every rerun
# https://docs.streamlit.io/develop/api-reference/widgets/st.download_button
@st.cache_data
def prepare_history_df(history_df: pd.DataFrame, uploaded_file_name: str) -> pd.DataFrame:
    history_df = history_df.copy()
    unused_path = os.path.join('data', uploaded_file_name, 'attachment')
    history_df.loc[history_df['is_file'], 'message'] = history_df.loc[history_df['is_file'], 'message']\
        .str.replace(unused_path, '', regex=False).str.replace(r'^.', '', regex=True)
    return history_df


# https://discuss.streamlit.io/t/scroll-to-page-section-that-is-being-rendered/77822/2
# https://gist.github.com/skannan-maf/8c8ee1c5fdc34594c0c3bc0a22fb63f9
def navigate_to_element(id: str) -> None:
    html('''
    <script>
        // Time of creation of this script = {now}.
        // The time changes everytime and hence would force streamlit to execute JS function
        function scrollToMySection() {{
            const element = window.parent.document.getElementById("{id}");
            if (element) {{
                element.scrollIntoView({{ behavior: "smooth" }});
            }} else {{
                setTimeout(scrollToMySection, 100);
            }}
        }}
        scrollToMySection();
    </script>
    '''.format(now=time.time(), id=id)
    )


def check_and_process_path(directory_path: str, file_name: str) -> tuple[str, str]:

    def has_txt_file(directory_path):
        return any(file.endswith(".txt") for file in os.listdir(directory_path))
    
    def has_attachment_dir(directory_path):
        return "attachment" in os.listdir(directory_path) and os.path.isdir(os.path.join(directory_path, "attachment"))
    
    if has_txt_file(directory_path):
        if has_attachment_dir(directory_path):
            attachment_path = os.path.join(directory_path, 'attachment')
            return directory_path, attachment_path
        else:
            return directory_path, directory_path
    
    directory_path = os.path.join(directory_path, file_name)
    attachment_path = os.path.join(directory_path, 'attachment')
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        if has_txt_file(directory_path):
            if has_attachment_dir(directory_path):
                return directory_path, attachment_path
            else:
                return directory_path, directory_path
        else:
            raise FileNotFoundError(f"No .txt file found in the path: {directory_path}")
    else:
        raise FileNotFoundError(f"Invalid path: {directory_path}")


# https://discuss.streamlit.io/t/unzipping/28001/3
# https://stackoverflow.com/questions/3451111/unzipping-files-in-python
def get_chat_history(uploaded_file: str) -> tuple[list, pd.DataFrame]:
    file_name = os.path.splitext(uploaded_file.name)[0]
    directory_path = os.path.join('data', file_name)
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_ref.extractall(directory_path)
    
    directory_path, attachment_path = check_and_process_path(directory_path, file_name)

    wa_parser = WhatssAppParser()
    history_df = wa_parser.parse(directory_path, attachment_path)
    
    return history_df


def display_chat_history(user: str, users: list, history_df: pd.DataFrame, theme_base: str = 'dark') -> None:
    chat_container = st.container()
    user_profile = 'https://raw.githubusercontent.com/bayu-siddhi/whatsapp-chat-history-ui/refs/heads/main/static/user_icon.png'
    opponent_profile = 'https://raw.githubusercontent.com/bayu-siddhi/whatsapp-chat-history-ui/refs/heads/main/static/ai_icon.png'
    history = history_df.to_dict('records')

    if history_df.empty is not True:
        with chat_container:
            for index, chat in enumerate(history):
                profile_src = '<img src="{}" class="chat-icon" width=32 height=32>'
                datetime_obj = chat['datetime']    
                date_str_1 = datetime_obj.strftime("%d/%m/%Y")
                date_str_2 = datetime_obj.strftime("%Y-%m-%d")
                time_str = datetime_obj.strftime("%H:%M")

                new_date_str = False

                if index == 0:
                    prev_date_str = ''
                
                if date_str_1 != prev_date_str:
                    new_date_str = True

                if chat['username'] == user:
                    chat_position = 'row-reverse'
                    profile_src = profile_src.format(user_profile)
                    background_color = 'user-background-dark' if theme_base == 'dark' else 'user-background-light'
                elif chat['username'] in users:
                    chat_position = ''
                    profile_src = profile_src.format(opponent_profile)
                    background_color = 'opponent-background-dark' if theme_base == 'dark' else 'opponent-background-light'
                else:
                    chat_position = 'text-center'
                    background_color = ''
                    profile_src = None
                
                if new_date_str:
                    chat_row = f"""
                    <div class="chat-row text-center">
                        <div id={date_str_2} class="chat-bubble">
                            {date_str_1}
                        </div>
                    </div>"""
                    st.markdown(chat_row, unsafe_allow_html=True)

                # Show image
                if chat['is_file'] == True and (chat['message'].endswith(".jpg") or chat['message'].endswith(".png")):
                    chat_row = f"""
                    <div class="chat-row {chat_position}">
                        {profile_src if profile_src is not None else '<div></div>'}
                        <div class="chat-bubble {'user-bubble' if profile_src is not None else ''} {background_color} img-fluid">
                            <img src='data:image/jpg;base64,{image_to_bytes(chat['message'])}'>
                            <span class="timestamp">{time_str}</span>
                        </div>
                    </div>"""
                    st.markdown(chat_row, unsafe_allow_html=True)
                # Show other file
                # https://stackoverflow.com/questions/55101162/aboutblankblocked-on-a-href-file-xxxlink-a-markdown-page
                elif chat['is_file'] == True:
                    chat_row = f"""
                    <div class="chat-row {chat_position}">
                        {profile_src if profile_src is not None else '<div></div>'}
                        <div class="chat-bubble {'user-bubble' if profile_src is not None else ''} {background_color}">
                            <a href='{os.path.join(Path(__file__).parent.resolve(), chat['message'])}' target='_blank'>{os.path.join(Path(__file__).parent.resolve(), chat['message'])}</a>
                            <span class="timestamp">{time_str}</span>
                        </div>
                    </div>"""
                    st.markdown(chat_row, unsafe_allow_html=True)
                else:
                    chat_row = f"""
                    <div class="chat-row {chat_position}">
                        {profile_src if profile_src is not None else '<div></div>'}
                        <div class="chat-bubble {'user-bubble' if profile_src is not None else ''} {background_color}">
                            {chat['message']}
                            {f'<div class="timestamp">{time_str}</div>' if profile_src is not None else '<div></div>'}
                        </div>
                    </div>"""
                    st.markdown(chat_row, unsafe_allow_html=True)
                
                prev_date_str = date_str_1
        