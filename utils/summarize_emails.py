import openai
import streamlit as st

def summarize_email(content, openai_api_key):
    try:
        if not openai_api_key or not openai_api_key.startswith("sk-"):
            return "⚠️ Kein gültiger OpenAI API Key vorhanden."
        
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
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