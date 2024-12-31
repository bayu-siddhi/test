import os
import utils
import datetime
import streamlit as st


with st.sidebar:
    # Configuration
    utils.load_css()
    theme = utils.get_theme()
    st.session_state.user = None
    st.title('WhatsApp Chat History UI')
    
    # Getting the uploaded file
    uploaded_file = st.file_uploader(
        label="Choose a chat history ZIP file to begin",
        type=['zip'],
        accept_multiple_files=False,
    )

if uploaded_file:
    # Load dataset
    uploaded_file_name = os.path.splitext(uploaded_file.name)[0]
    if 'dataset_session' not in st.session_state or st.session_state.dataset_session != uploaded_file_name:
        st.session_state.history_df = utils.get_chat_history(uploaded_file)
        st.session_state.users = list(st.session_state.history_df['username'].unique())
        st.session_state.users.remove("SYSTEM")
        # Set dataset session
        st.session_state.dataset_session = uploaded_file_name

with st.sidebar:
    if uploaded_file:
        # Dataset download button
        download = st.download_button(
            label="Download dataset as CSV",
            data=utils.prepare_history_df(st.session_state.history_df, st.session_state.dataset_session)\
                    .to_csv(index=False).encode("utf-8"),
            file_name=f"{st.session_state.dataset_session}.csv",
            mime="text/csv",
        )

        # Select user
        st.session_state.user = st.selectbox(
            "View chat as",
            st.session_state.users,
            index=None,
            placeholder='Select a user to view in Chat Mode'
        )
        opponent = [u for u in st.session_state.users if u != st.session_state.user][0]

        # Go to chat by date
        if st.session_state.user:
            go_to_date = st.selectbox(
                "Go to date",
                utils.get_unique_dates(st.session_state.history_df),
                index=None,
                placeholder="Select a date"
            )
            if go_to_date is not None:
                utils.navigate_to_element(go_to_date)


# # DISPLAY THE CHAT
if st.session_state.user:
    # Custom CSS for the sticky header
    # https://discuss.streamlit.io/t/is-it-possible-to-create-a-sticky-header/33145/3
    header = st.container()
    header.title(opponent)
    header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True) 
    header_background = '#0e1117' if theme['base'] == 'dark' else '#ffffff'
    st.markdown(utils.STICKY_HEADER.format(header_background=header_background), unsafe_allow_html=True)
    
    # Getting input message
    input_message = st.chat_input("Say something")
    if input_message:
        st.session_state.history_df.loc[len(st.session_state.history_df)] = [
            datetime.datetime.now(),
            st.session_state.user,
            input_message,
            False
        ]

    # Display the chat
    utils.display_chat_history(st.session_state.user, st.session_state.users, st.session_state.history_df, theme['base'])

# DISPLAY THE DATASET IN TABLE
elif uploaded_file and st.session_state.user is None:
    st.title('Table Mode')
    descending = st.toggle("Sort from newest to oldest", value=False, )
    if descending:
        st.write(utils.prepare_history_df(st.session_state.history_df, st.session_state.dataset_session)\
                 .sort_values(by='datetime', ascending=False))
    else:
        st.write(utils.prepare_history_df(st.session_state.history_df, st.session_state.dataset_session))
