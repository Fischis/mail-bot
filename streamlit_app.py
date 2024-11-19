import streamlit as st
import openai
import numpy as np
from utils.fetch_emails import fetch_emails
from utils.summarize_emails import summarize_email
from utils.faiss_utils import generate_faiss_index, search_faiss_index

# App Titel
st.title("🛩 E-Mail AI Demo ")

# API Key Setup
try:
    openai_api_key = st.secrets["openai_api_key"]
except:
    openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")

# E-Mail Zugangsdaten
st.sidebar.header("E-Mail Zugang")
email_address = st.sidebar.text_input("E-Mail-Adresse", placeholder="z.B. benutzer@web.de")
email_password = st.sidebar.text_input("Passwort", type="password", placeholder="Dein Passwort")
imap_server = "imap.web.de"

# Seiten-Status
if "emails" not in st.session_state:
    st.session_state.emails = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "selected_email" not in st.session_state:
    st.session_state.selected_email = None
if "faiss_index" not in st.session_state:
    st.session_state.faiss_index = None
if "email_vectors" not in st.session_state:
    st.session_state.email_vectors = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_active" not in st.session_state:
    st.session_state.search_active = False

# E-Mails abrufen und in FAISS speichern
if st.sidebar.button("E-Mails abrufen"):
    st.session_state.emails = fetch_emails(email_address, email_password, imap_server)
    st.session_state.current_page = 0
    if st.session_state.emails:
        st.session_state.faiss_index, st.session_state.email_vectors = generate_faiss_index(st.session_state.emails, openai_api_key)
        if st.session_state.faiss_index:
            st.success("FAISS-Index erfolgreich erstellt.")

# Restliche Logik bleibt hier unverändert.
# Pagination
if st.session_state.emails and not st.session_state.search_active:
    total_pages = (len(st.session_state.emails) + 19) // 20
    current_page_emails = st.session_state.emails[
        st.session_state.current_page * 20 : (st.session_state.current_page + 1) * 20
    ]

    for i, email_data in enumerate(current_page_emails):
        with st.container():
            st.markdown(f"**Betreff:** {email_data['subject']}")
            st.markdown(f"**Von:** {email_data['sender']}")
            if st.button("Anzeigen", key=f"email_{i}"):
                st.session_state.selected_email = email_data
            st.markdown("---")

    # Pagination Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Zurück", disabled=st.session_state.current_page <= 0):
            st.session_state.current_page -= 1
    with col3:
        if st.button("➡️ Weiter", disabled=st.session_state.current_page >= total_pages - 1):
            st.session_state.current_page += 1

# Sidebar-Suche hinzufügen
search_query = st.sidebar.text_input("🔍 Suche in E-Mails")
if search_query:
    try:
        if st.session_state.faiss_index is None:
            st.error("Bitte erst die E-Mails abrufen und den FAISS-Index erstellen.")
        else:
            # Suche im FAISS-Index durchführen
            st.session_state.search_results = search_faiss_index(search_query, st.session_state.faiss_index, st.session_state.email_vectors, openai_api_key)
            st.session_state.search_active = True
    except Exception as e:
        st.error(f"Fehler bei der Suche: {e}")

# Suchergebnisse anzeigen
if st.session_state.search_active:
    st.markdown("### 🔍 Suchergebnisse")
    for i, email_data in enumerate(st.session_state.search_results):
        with st.container():
            st.markdown(f"**Betreff:** {email_data['subject']}")
            st.markdown(f"**Von:** {email_data['sender']}")
            if st.button("Anzeigen", key=f"search_email_{i}"):
                st.session_state.selected_email = email_data
            st.markdown("---")
    if st.button("Schließen Suche"):
        st.session_state.search_active = False
        st.session_state.search_results = []

# Overlay mit E-Mail-Details
if st.session_state.selected_email:
    email_data = st.session_state.selected_email
    message = email_data["message"]

    # E-Mail-Inhalt dekodieren
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            try:
                if content_type == "text/plain":
                    content = part.get_payload(decode=True).decode()
                    break
            except:
                pass
    else:
        content = message.get_payload(decode=True).decode()

    # Zusammenfassung
    summary = summarize_email(content, openai_api_key)

    # Overlay anzeigen
    with st.expander("📬 E-Mail Details anzeigen", expanded=True):
        st.markdown(f"### 📜 Betreff: {email_data['subject']}")
        st.markdown(f"**Von:** {email_data['sender']}")
        st.markdown(f"**Zusammenfassung:**\n{summary}")
        st.text_area("Inhalt der E-Mail", content, height=300)
        if st.button("Schließen"):
            st.session_state.selected_email = None
