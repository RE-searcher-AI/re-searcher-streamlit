from dotenv import find_dotenv, load_dotenv
from streamlit_theme import st_theme

import streamlit as st
from services.chat.chat_response_service import generate_chat_response
from utils import LOGO_URL, LOGO_TEXT_LIGHT_URL, LOGO_TEXT_DARK_URL, AUTHORS, INTRODUCTION_MESSAGE, ABOUT_PROJECT

# Load environment variables from the .env file.
load_dotenv(find_dotenv())

# Set Streamlit page configuration with custom title and icon.
st.set_page_config(page_title="RE:searcher", page_icon=LOGO_URL)
st.title("RE\:searcher")
st.divider()

# Determine the theme and set the appropriate logo
theme_data = st_theme()
st.session_state.theme = (
    theme_data["base"] if theme_data is not None else "default_theme"
)
logo_url = (
    LOGO_TEXT_DARK_URL if st.session_state.theme == "dark" else LOGO_TEXT_LIGHT_URL
)

# Display the logo and set up the sidebar with useful information and links.
st.logo(logo_url, icon_image=logo_url)
with st.sidebar:
    st.subheader("👋️ O projektu")
    with st.container(border=True):
        st.markdown(ABOUT_PROJECT)

    st.subheader("✍️ Autori")
    st.markdown(AUTHORS)

# Initialize or update the session state for storing chat messages.
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.chat_message("assistant"):
    st.markdown(INTRODUCTION_MESSAGE)

# Display all chat messages stored in the session state.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input and generate responses.
if prompt := st.chat_input("Postavi pitanje vezano za testne dokumente..."):
    # Display user message in chat container.
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        response = generate_chat_response(
            {
                "active_document": {
                    "filename": "orbitalni_istrazivac_marsa.pdf",
                    "name": "Orbitalni istrazivac Marsa",
                    "description": "O Marsu"
                },
                "conversation": st.session_state.messages
            }
        )
        st.write(response["assistant_response"])
        if len(response.get("citations", [])) != 0:
            st.divider()
            for index, citation in enumerate(response["citations"]):
                with st.expander(f"Citat [{index + 1}]"):
                    st.caption(citation)

    # Update message history
    st.session_state.messages = response["conversation"]
