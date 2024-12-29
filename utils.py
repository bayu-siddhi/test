import os
import time
import base64
import pandas as pd
import streamlit as st
from pathlib import Path
from parser import WhatssAppParser
from streamlit_theme import st_theme
from streamlit.components.v1 import html


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
</style>'''


def get_theme() -> dict:
    theme = st_theme()
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


# https://discuss.streamlit.io/t/scroll-to-page-section-that-is-being-rendered/77822/2
# https://gist.github.com/skannan-maf/8c8ee1c5fdc34594c0c3bc0a22fb63f9
def navigate_to_element(id: str):
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


def get_chat_history(path: str) -> tuple[list, pd.DataFrame]:

    try:
        is_chat_csv_exist = False
        path_tupple = os.path.splitext(path)
        # path_extension = path_tupple[-1].lower()
        path_csv = path_tupple[0] + '.csv'
        is_chat_csv_exist = os.path.isfile(path_csv)
        if is_chat_csv_exist:
            history_df = pd.read_csv(path_csv)
            history = history_df.to_dict('records')
        else:
            print("CSV tidak ditemukan")
            wa_parser = WhatssAppParser()
            history = wa_parser.parse(path)
            history_df = pd.DataFrame(history)
        history_df['datetime'] = pd.to_datetime(history_df['datetime'])
    except Exception as e:
        print(e)
    
    return history, history_df


def display_chat_history(user: str, history_df: pd.DataFrame) -> list:
    
    chat_container = st.container()
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
                    background_color = 'current-user-background'
                    profile_src = profile_src.format("https://raw.githubusercontent.com/bayu-siddhi/whatsapp-chat-history-ui/refs/heads/main/static/user_icon.png")
                elif chat['username'] in st.session_state.users:
                    chat_position = ''
                    background_color = 'opponent-background'
                    profile_src = profile_src.format("https://raw.githubusercontent.com/bayu-siddhi/whatsapp-chat-history-ui/refs/heads/main/static/ai_icon.png")
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
                    image_path = os.path.join('chat', chat['message'])
                    chat_row = f"""
                    <div class="chat-row {chat_position}">
                        {profile_src if profile_src is not None else '<div></div>'}
                        <div class="chat-bubble {'user-bubble' if profile_src is not None else ''} {background_color} img-fluid">
                            <img src='data:image/jpg;base64,{image_to_bytes(image_path)}'>
                            <span class="timestamp">{time_str}</span>
                        </div>
                    </div>"""
                    st.markdown(chat_row, unsafe_allow_html=True)
                # Show other file
                elif chat['is_file'] == True:
                    chat_row = f"""
                    <div class="chat-row {chat_position}">
                        {profile_src if profile_src is not None else '<div></div>'}
                        <div class="chat-bubble {'user-bubble' if profile_src is not None else ''} {background_color}">
                            <a href='{os.path.join(Path(__file__).parent.resolve(), 'chat', chat['message'])}' target='_blank' style='color: white'>{chat['message']}</a>
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
                            <div class="timestamp">{time_str}</div>
                        </div>
                    </div>"""
                    st.markdown(chat_row, unsafe_allow_html=True)
                
                prev_date_str = date_str_1
    
    return history