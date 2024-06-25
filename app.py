from dotenv import find_dotenv, load_dotenv
from streamlit_theme import st_theme

import streamlit as st
from services.chat.chat_response_service import generate_chat_response
from utils import LOGO_URL, LOGO_TEXT_LIGHT_URL, LOGO_TEXT_DARK_URL, AUTHORS, INTRODUCTION_MESSAGE, ABOUT_PROJECT, \
    DOCUMENTS

# Load environment variables from the .env file.
load_dotenv(find_dotenv())

# Initialize state.
if "messages" not in st.session_state:
    st.session_state.messages = []

if "suggestions" not in st.session_state:
    st.session_state.suggestions = []

if "document" not in st.session_state:
    st.session_state.document = DOCUMENTS[0]

if "notes" not in st.session_state:
    st.session_state.notes = []

# Set Streamlit page configuration with custom title and icon.
st.set_page_config(page_title="RE:searcher", page_icon=LOGO_URL, layout='wide')
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
    st.subheader("📚 Odaberi dokument")


    def on_radio_change():
        st.session_state.notes = []
        st.session_state.messages = []


    document = st.radio(
        label="O kom dokumentu želite da razgovarate?",
        options=[e["name"] for e in DOCUMENTS],
        captions=[e["description"] for e in DOCUMENTS],
        on_change=on_radio_change
    )

    st.session_state.document = next((e for e in DOCUMENTS if e["name"] == document), None)

    st.divider()

    st.subheader("📝 Beleške")
    if len(st.session_state.notes) == 0:
        st.caption("Još uvek nemate beleške! Pitajte AI da napravi jednu za vas.")
    else:
        for note in st.session_state.notes:
            with st.container(border=True):
                st.markdown(f"**{note['title']}**: {note['description']}")

    st.divider()

    st.subheader("🤔 Želite da dodate novi dokument?")
    st.caption("Ukoliko želite da dodate novi dokument, isti je moguće dodati klikom na dugme dodaj!")
    add_btn = '''
    <div style="display: flex; justify-content: center;">
        <button style="
            background-color: #ff4b4b; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 10px; 
            cursor: pointer;">
            Dodaj!
        </button>
    </div>
    '''
    st.sidebar.markdown(add_btn, unsafe_allow_html=True)

    st.divider()

    st.subheader("👋️ O projektu")
    with st.container(border=True):
        st.markdown(ABOUT_PROJECT)

    st.divider()

    st.subheader("✍️ Autori")
    st.markdown(AUTHORS)

st.subheader(f"Dokument: {st.session_state.document['name']}")
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
                    "filename": st.session_state.document["filename"],
                    "name": st.session_state.document["name"],
                    "description": st.session_state.document["description"],
                },
                "conversation": st.session_state.messages
            }
        )

        st.write(response["assistant_response"])
        if (response["new_sticky_note"] != None):
            st.session_state.notes.append(response["new_sticky_note"])

        if len(response.get("citations", [])) != 0:
            st.divider()
            for index, citation in enumerate(response["citations"]):
                with st.expander(f"Citat [{index + 1}] - {citation['filename']} - {citation['score']}"):
                    st.caption(citation['content'])

        # Update message history
        st.session_state.messages = response["conversation"]
