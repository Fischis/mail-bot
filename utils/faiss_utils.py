import openai
import faiss
import numpy as np
import streamlit as st

def generate_faiss_index(emails, openai_api_key):
    try:
        if not openai_api_key or not openai_api_key.startswith("sk-"):
            st.error("⚠️ Kein gültiger OpenAI API Key vorhanden.")
            return
        
        client = openai.OpenAI(api_key=openai_api_key)
        embeddings = []
        for email_data in emails:
            message = email_data["message"]
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
            
            # Generieren des Embeddings mit den neuen Parametern
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=content,
            )
            embedding = response.data[0].embedding
            embeddings.append(embedding)

        # FAISS Index initialisieren
        dimension = len(embeddings[0])
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings, dtype=np.float32))

        return index, emails
    except Exception as e:
        st.error(f"Fehler beim Erstellen des FAISS-Indexes: {e}")
        return None, None


def search_faiss_index(search_query, faiss_index, email_vectors, openai_api_key):
    """
    Sucht relevante E-Mails im FAISS-Index basierend auf der Suchanfrage.

    Args:
    - search_query (str): Die Suchanfrage des Benutzers.
    - faiss_index (faiss.Index): Der FAISS-Index, in dem gesucht wird.
    - email_vectors (list): Liste der E-Mails, die Vektoren enthalten.
    - openai_api_key (str): Der API-Schlüssel für OpenAI.

    Returns:
    - list: Eine Liste relevanter E-Mails.
    """

    if not openai_api_key or not openai_api_key.startswith("sk-"):
        st.error("⚠️ Kein gültiger OpenAI API Key vorhanden.")
        return


    # Erzeuge OpenAI Client
    client = openai.OpenAI(api_key=openai_api_key)

    # Generiere das Embedding für die Suchanfrage
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=search_query,
    )
    search_embedding = response.data[0].embedding
    search_embedding = np.array([search_embedding], dtype=np.float32)

    # Suche im FAISS-Index
    D, I = faiss_index.search(search_embedding, k=5)

    # Finde relevante E-Mails basierend auf den Indexen, die vom FAISS-Index zurückgegeben wurden
    search_results = [email_vectors[i] for i in I[0] if i != -1]

    return search_results

