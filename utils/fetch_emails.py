import imaplib
import email
from email.header import decode_header
import streamlit as st

def fetch_emails(email_address, email_password, imap_server, page=0, page_size=20):
    try:
        # IMAP Verbindung aufbauen
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, email_password)
        mail.select("inbox")

        # Nachrichten abrufen
        status, messages = mail.search(None, "ALL")
        messages = messages[0].split()

        # Pagination berechnen
        total_messages = len(messages)
        start = total_messages - (page + 1) * page_size
        end = start + page_size
        if start < 0:
            start = 0

        emails = []
        for i in range(start, end):
            if i < 0 or i >= total_messages:
                continue
            _, msg_data = mail.fetch(messages[i], "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_header(msg["Subject"])[0][0]
                    sender = decode_header(msg["From"])[0][0]

                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    if isinstance(sender, bytes):
                        sender = sender.decode()

                    emails.append({
                        "subject": subject,
                        "sender": sender,
                        "message": msg
                    })

        return emails
    except Exception as e:
        st.error(f"Fehler beim Abrufen der E-Mails: {e}")
        return []
