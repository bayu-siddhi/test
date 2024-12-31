import os
import utils
import datetime
import streamlit as st


# SIDEBAR SETTINGS
with st.sidebar:
    # Configuration
    user = None
    history_df = None
    utils.load_css()
    theme = utils.get_theme()
    st.title('WhatsApp Chat History UI')
    
    # Getting the uploaded file
    uploaded_file = st.file_uploader(
        label="Choose a chat history ZIP file to begin",
        type=['zip'],
        accept_multiple_files=False,
    )

    if uploaded_file:
        # Load dataset
        if 'dataset_session' not in st.session_state or st.session_state.dataset_session != uploaded_file.name:
            history_df = utils.get_chat_history(uploaded_file)
            users = list(history_df['username'].unique())
            users.remove("SYSTEM")
            # Set dataset session
            st.session_state.dataset_session = os.path.splitext(uploaded_file.name)[0]

        # Dataset download button
        is_download = st.download_button(
            label="Download dataset as CSV",
            data=utils.prepare_history_df(history_df, st.session_state.dataset_session)\
                      .to_csv(index=False).encode("utf-8"),
            file_name=f"{st.session_state.dataset_session}.csv",
            mime="text/csv",
        )

        # Select user
        user = st.selectbox(
            "View chat as",
            users,
            index=None,
            placeholder='Select a user to view in Chat Mode'
        )
        opponent = [u for u in users if u != user][0]

        # Go to chat by date
        if user:
            go_to_date = st.selectbox(
                "Go to date",
                utils.get_unique_dates(history_df),
                index=None,
                placeholder="Select a date"
            )
            if go_to_date is not None:
                utils.navigate_to_element(go_to_date)


# DISPLAY THE CHAT
if 'user' in globals() and user is not None:
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
        history_df.loc[len(history_df)] = [
            datetime.datetime.now(),
            st.session_state.user,
            input_message,
            False
        ]

    # Display the chat
    utils.display_chat_history(user, users, history_df, theme['base'])

# DISPLAY THE DATASET IN TABLE
elif 'history_df' in globals() and history_df is not None:
    st.title('Table Mode')
    descending = st.toggle("Sort from newest to oldest", value=False, )
    if descending:
        st.write(utils.prepare_history_df(history_df, st.session_state.dataset_session)\
                 .sort_values(by='datetime', ascending=False))
    else:
        st.write(utils.prepare_history_df(history_df, st.session_state.dataset_session))
