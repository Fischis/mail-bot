import openai
import streamlit as st
from typing import Optional

def summarize_email(content, openai_api_key):
    try:
        if not openai_api_key or not openai_api_key.startswith("sk-"):
            return "⚠️ Kein gültiger OpenAI API Key vorhanden."
        
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Du bist ein Assistent, der E-Mails zusammenfasst."},
                {"role": "user", "content": f"Fasse die folgende E-Mail kurz und prägnant zusammen:\n\n{content}"}
            ],
            max_tokens=150,
            temperature=0.7,
            response_format={"type": "text"}
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Fehler bei der KI-Zusammenfassung: {e}"
    

def llm_query_answer(query: str, search_results: list, openai_api_key) -> str:
    """
    Generate a summary of search results based on the query using OpenAI.
    
    Args:
        query: The search query string
        search_results: List of email search results
    
    Returns:
        str: Generated summary of the search results
    """



    try:
        # Prepare the email content for the prompt
        email_contents = []
        for email in search_results:
            message = email["message"]

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

            email_text = (
                f"Datum: {email['date'].strftime('%d.%m.%Y')}\n"
                f"Betreff: {email['subject']}\n"
                f"Von: {email['sender']}\n"
                f"Inhalt: {content}..."  # todo Limit content length
            )
            email_contents.append(email_text)

        # Create the prompt for OpenAI
        prompt = f"""
        Suche: {query}
        
        Gefundene E-Mails:
        {'***'.join(email_contents)}
        
        Bitte fasse die wichtigsten Informationen aus den gefundenen E-Mails zusammen, 
        die relevant für die Suchanfrage sind.
        """

        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent, der E-Mails analysiert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7,
            response_format={"type": "text"}
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Fehler bei der Zusammenfassung: {str(e)}"
    

  

def llm_suggest_email_response(email_body: str, suggest_keywords: Optional[str], openai_api_key) -> str:
    """
    Generate a response to an email based on the email body using OpenAI.
    
    Args:
        email_body: The email body text.
        suggest_keywords: Keywords to suggest in the response.
    
    Returns:
        Generated response to the email.
    """
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        
        if suggest_keywords:
            user_message = (
                f"{email_body}\n\n"
                f"Bitte berücksichtige die folgenden Schlüsselwörter in deiner Antwort: {suggest_keywords}"
            )
        else:
            user_message = email_body
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein hilfreicher Assistent, der E-Mails im Namen des Empfängers beantwortet."
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=350,
            temperature=0.7,
            response_format={"type": "text"}
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Fehler bei der KI-Antwort: {e}"