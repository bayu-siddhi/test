import os
import re
import pandas as pd
import streamlit as st
from datetime import datetime
from parser import WhatssAppParser


def load_css():
    with open(os.path.join('static', 'styles.css'), "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

def get_chat_history(path: str):
    if "history" not in st.session_state and "history_df" not in st.session_state:
        st.session_state.history = list()
        st.session_state.history_df = pd.DataFrame()
        wa_parser = WhatssAppParser()
        try:
            is_chat_csv_exist = False
            chat_file_extension = re.search(r'\.(.*)$', path)
            if chat_file_extension is not None:
                file_extension_len = len(chat_file_extension[1])
                csv_path = path[:-file_extension_len] + 'csv'
                is_chat_csv_exist = os.path.isfile(csv_path)
            else:
                raise Exception("File extension not found")
            if is_chat_csv_exist:
                st.session_state.history_df = pd.read_csv(csv_path)
                st.session_state.history = st.session_state.history_df.to_dict('records')
            else:
                print("CSV tidak ditemukan")
                st.session_state.history = wa_parser.parse(path)
                st.session_state.history_df = pd.DataFrame(st.session_state.history)
        except Exception as e:
            print(e)

def display_chat_history(user: str):

    input_message = st.chat_input("Say something")
    if input_message:
        st.session_state.history.append({
            'datetime': datetime.now(),
            'username': user,
            'message': input_message,
            'is_file': False
        })
    
    chat_placeholder = st.container()

    if st.session_state.history:
        with chat_placeholder:
            for chat in st.session_state.history:

                image_src = '<img src="{}" class="chat-icon" width=32 height=32>'

                if chat['username'] == user:
                    chat_position = 'row-reverse'
                    image_src = image_src.format(os.path.join('static', 'user_icon.png'))
                elif chat['username'] in st.session_state.users:
                    chat_position = ''
                    image_src = image_src.format(os.path.join('static', 'ai_icon.png'))
                else:
                    chat_position = 'text-center'
                    image_src = None

                # print(image_src)
                chat_row = f"""
                <div class="chat-row {chat_position}">
                    {image_src if image_src is not None else '<div></div>'}
                    <div class="chat-bubble {'human-bubble' if image_src is not None else ''}">
                        &#8203;{chat['message']}
                    </div>
                </div>"""

                st.markdown(chat_row, unsafe_allow_html=True)

# Konfigurasi
chat_directory = 'data'
chat_file = 'chat.txt'
path = os.path.join(chat_directory, chat_file)
get_chat_history(path)
load_css()

# User Interface
st.title("Hello Custom CSS Chatbot 🤖")

with st.sidebar:
    if 'users' not in st.session_state:
        st.session_state.users = list(st.session_state.history_df['username'].unique())
        st.session_state.users.remove("SYSTEM")
    user = st.radio("Who is user?", st.session_state.users)

if user:
    display_chat_history(user)
    