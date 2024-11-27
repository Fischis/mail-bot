import streamlit as st
import openai
import numpy as np
from utils.fetch_emails import fetch_emails
from utils.summarize_emails import summarize_email, llm_query_answer, llm_suggest_email_response
from utils.faiss_utils import generate_faiss_index, search_faiss_index

# App Titel
st.title("🛩 E-Mail AI Demo ")

# Modell-Dialog für API Key und E-Mail Zugangsdaten
@st.dialog("🔑 Zugangsdaten Eingeben")
def show_credentials_dialog():
    with st.form("credentials_form", clear_on_submit=False):
        try:
            openai_api_key = st.secrets["openai_api_key"]
        except:
            openai_api_key = st.text_input("OpenAI API Key", type="password")
        email_address = st.text_input("E-Mail-Adresse", placeholder="z.B. benutzer@web.de")
        email_password = st.text_input("Passwort", type="password", placeholder="Dein Passwort")
        submitted = st.form_submit_button("Speichern und Schließen")
        if submitted:
            st.session_state.openai_api_key = openai_api_key
            st.session_state.email_address = email_address
            st.session_state.email_password = email_password
            with st.spinner("E-Mails werden abgerufen und verarbeitet..."):
                try:
                    st.session_state.emails = fetch_emails(email_address, email_password, "imap.web.de")
                    st.session_state.current_page = 0
                    if st.session_state.emails:
                        st.session_state.faiss_index, st.session_state.email_vectors = generate_faiss_index(
                            st.session_state.emails, openai_api_key)
                        if st.session_state.faiss_index:
                            st.success("FAISS-Index erfolgreich erstellt.")
                            st.session_state.show_dialog = False
                            st.rerun()
                except Exception as e:
                    st.error(f"Fehler beim Abrufen der E-Mails: {e}")
                    st.session_state.show_dialog = True
    
def show_email_details(email_data):
    message = email_data["message"]
    content = ""
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
    summary = summarize_email(content, openai_api_key)
    st.markdown(f"### 📜 Betreff: {email_data['subject']}")
    st.markdown(f"**Von:** {email_data['sender']}")
    st.markdown(f"**Zusammenfassung:**\n{summary}")
    st.text_area("Inhalt der E-Mail", content, height=300)

    col1, col2 = st.columns([3, 1])
    with col1:
        custom_keywords = st.text_input("Stichworte für Antwort", value="", placeholder="Bitte hier Stichworte eingeben")
        suggested_response = ""
    with col2:
        if st.button("Vorschlag für Antwort"):
            suggested_response = llm_suggest_email_response(custom_keywords, content, openai_api_key)
    st.markdown(f"**Vorschlag für Antwort:**\n{suggested_response}")

# Initialisiere Zugangsdaten
if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = True
if "email_address" not in st.session_state:
    st.session_state.email_address = ""
if "email_password" not in st.session_state:
    st.session_state.email_password = ""
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""

# Zeige Dialog für Zugangsdaten bei Bedarf
if st.session_state.show_dialog:
    show_credentials_dialog()

# E-Mail Zugangsdaten abrufen
openai_api_key = st.session_state.openai_api_key
email_address = st.session_state.email_address
email_password = st.session_state.email_password
imap_server = "imap.web.de"

# Seitenstatus
if "details_visible" not in st.session_state:
    st.session_state.details_visible = -1
if "emails" not in st.session_state:
    st.session_state.emails = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "faiss_index" not in st.session_state:
    st.session_state.faiss_index = None
if "email_vectors" not in st.session_state:
    st.session_state.email_vectors = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_active" not in st.session_state:
    st.session_state.search_active = False
if "last_search_query" not in st.session_state:
    st.session_state.last_search_query = ""
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "📧 E-Mails"

def toggle_email_details(index, context="main"):
    detail_key = f"details_visible_{context}"
    if detail_key not in st.session_state:
        st.session_state[detail_key] = -1
    if st.session_state[detail_key] == index:
        st.session_state[detail_key] = -1
    else:
        st.session_state[detail_key] = index

def display_email_list(emails, context="main"):
    for i, email_data in enumerate(emails):
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Datum:** {email_data['date'].strftime('%d.%m.%Y')}")
            with col2:
                st.markdown(f"**Betreff:** {email_data['subject']}")
            with col3:
                st.markdown(f"**Von:** {email_data['sender']}")
            detail_key = f"details_visible_{context}"
            button_text = "Details ausblenden" if st.session_state.get(detail_key) == i else "Details anzeigen"
            st.button(
                button_text,
                key=f"email_{context}_{i}",
                on_click=toggle_email_details,
                args=(i, context)
            )
            if st.session_state.get(detail_key) == i:
                show_email_details(email_data)
            st.markdown("---")

def handle_search(query):
    if query and query != st.session_state.last_search_query:
        try:
            if st.session_state.faiss_index is None:
                st.error("Bitte erst die E-Mails abrufen und den FAISS-Index erstellen.")
                return False
            search_results = search_faiss_index(
                query,
                st.session_state.faiss_index,
                st.session_state.email_vectors,
                st.session_state.openai_api_key
            )
            llm_search_summary = llm_query_answer(query, search_results, st.session_state.openai_api_key)
            if search_results:
                st.session_state.search_results.append({
                    "query": query,
                    "results": search_results,
                    "llm_summary": llm_search_summary
                })
                st.session_state.search_active = True
                st.session_state.last_search_query = query
                st.session_state.active_tab = f"🔍 {query[:10]}..."
                return True
        except Exception as e:
            st.error(f"Fehler bei der Suche: {e}")
    return False

def remove_search_tab(tab_title):
    index = None
    for i, result in enumerate(st.session_state.search_results):
        if f"🔍 {result['query'][:10]}..." == tab_title:
            index = i
            break
    if index is not None:
        st.session_state.search_results.pop(index)
    if not st.session_state.search_results:
        st.session_state.search_active = False
        st.session_state.active_tab = "📧 E-Mails"
    else:
        st.session_state.active_tab = "📧 E-Mails"
    st.rerun()

# Suchfunktion in der Seitenleiste
search_query = st.sidebar.text_input("🔍 Suche in E-Mails")
search_button = st.sidebar.button("Suchen")

if search_button and search_query:
    if handle_search(search_query):
        st.rerun()

# Tab-Titel erstellen
tab_titles = ["📧 E-Mails"]
if st.session_state.search_active and st.session_state.search_results:
    for result in st.session_state.search_results:
        tab_title = f"🔍 {result['query'][:10]}..."
        tab_titles.append(tab_title)

# Aktiven Tab auswählen
selected_tab = st.radio(
    "Tabs",
    tab_titles,
    index=tab_titles.index(st.session_state.active_tab)
)

# Aktiven Tab in der Session State speichern
st.session_state.active_tab = selected_tab

# Inhalt basierend auf dem aktiven Tab anzeigen
if selected_tab == "📧 E-Mails":
    if st.session_state.emails:
        total_pages = (len(st.session_state.emails) + 19) // 20
        current_page_emails = st.session_state.emails[
            st.session_state.current_page * 20: (st.session_state.current_page + 1) * 20
        ]
        display_email_list(current_page_emails, "main")

        # Navigationsbuttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Zurück", disabled=st.session_state.current_page <= 0, key="prev"):
                st.session_state.current_page -= 1
        with col3:
            if st.button("➡️ Weiter", disabled=st.session_state.current_page >= total_pages - 1, key="next"):
                st.session_state.current_page += 1
else:
    # Suchergebnisse anzeigen
    index = tab_titles.index(selected_tab) - 1
    result = st.session_state.search_results[index]
    # Schließen-Button
    if st.button("✖️ Tab schließen"):
        remove_search_tab(selected_tab)
    st.markdown("### 🔍 Suchergebnisse")
    st.markdown(f"LLM Antwort: {result['llm_summary']}")
    display_email_list(result["results"], f"search_{result['query']}")