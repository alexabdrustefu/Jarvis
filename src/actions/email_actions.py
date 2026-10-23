"""Gmail inbox access and threaded replies for J.A.R.V.I.S."""

import base64
import binascii
import html
import os
import re
import threading
from pathlib import Path
from email.header import decode_header, make_header
from email.mime.text import MIMEText
from email.utils import parseaddr

import httplib2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from storage.paths import data_directory, is_frozen


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


class EmailActions:
    """Read Gmail messages and send replies in their original thread."""

    def __init__(self):
        self.base_dir = data_directory() if is_frozen() else Path(__file__).resolve().parents[1]
        self.client_secret_path = str(self.base_dir / "client_secret.json")
        self.token_path = str(self.base_dir / "token.json")
        self.service = None
        # google-api-python-client's httplib2 transport is not thread-safe.
        # The desktop UI requests message details on background workers.
        self._api_lock = threading.RLock()

    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_path):
            # Keep the scopes actually granted in token.json so that an old
            # read-only token is correctly detected and can request consent.
            creds = Credentials.from_authorized_user_file(self.token_path)

        # A previous read-only token cannot send. Request the additional Gmail
        # permission through Google's consent flow instead of failing at send time.
        if creds and creds.expired and creds.refresh_token and creds.has_scopes(SCOPES):
            creds.refresh(Request())

        if not creds or not creds.valid or not creds.has_scopes(SCOPES):
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secret_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open(self.token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())

        authorized_http = AuthorizedHttp(creds, http=httplib2.Http(timeout=12))
        return build(
            "gmail", "v1", http=authorized_http, cache_discovery=False
        )

    def _get_service(self):
        with self._api_lock:
            if self.service is None:
                self.service = self._authenticate()
            return self.service

    @staticmethod
    def _headers(payload):
        return {
            header.get("name", "").lower(): header.get("value", "")
            for header in payload.get("headers", [])
        }

    @staticmethod
    def _decoded_header(value):
        if not value:
            return ""
        try:
            return str(make_header(decode_header(value)))
        except (TypeError, ValueError):
            return value

    def get_recent_emails(self, limit=30):
        """Return inbox summaries, newest first, for the desktop mail view."""
        with self._api_lock:
            return self._get_recent_emails(limit)

    def _get_recent_emails(self, limit):
        service = self._get_service()
        result = service.users().messages().list(
            userId="me", labelIds=["INBOX"], maxResults=max(1, min(limit, 50))
        ).execute(num_retries=2)
        message_refs = result.get("messages", [])
        metadata_by_id = {}
        batch_errors = []

        def collect_metadata(request_id, response, exception):
            if exception is not None:
                batch_errors.append(exception)
            else:
                metadata_by_id[request_id] = response

        if message_refs:
            batch = service.new_batch_http_request(callback=collect_metadata)
            for message in message_refs:
                batch.add(
                    service.users().messages().get(
                        userId="me", id=message["id"], format="metadata",
                        metadataHeaders=["From", "Reply-To", "Subject", "Date", "Message-ID", "References"],
                    ),
                    request_id=message["id"],
                )
            # BatchHttpRequest.execute() does not accept num_retries, unlike
            # individual googleapiclient HttpRequest.execute() calls.
            batch.execute()
        if batch_errors:
            raise batch_errors[0]

        emails = []
        for message in message_refs:
            item = metadata_by_id.get(message["id"])
            if item is None:
                continue
            headers = self._headers(item.get("payload", {}))
            sender_name, sender_address = parseaddr(headers.get("from", ""))
            emails.append({
                "id": item["id"],
                "thread_id": item.get("threadId", ""),
                "sender": sender_name or sender_address or headers.get("from", "Mittente sconosciuto"),
                "sender_address": sender_address,
                "reply_to": parseaddr(headers.get("reply-to", ""))[1] or sender_address,
                "subject": self._decoded_header(headers.get("subject")) or "Senza oggetto",
                "date": headers.get("date", ""),
                "message_id": headers.get("message-id", ""),
                "references": headers.get("references", ""),
                "snippet": item.get("snippet", ""),
                "unread": "UNREAD" in item.get("labelIds", []),
            })
        return emails

    def get_email_details(self, message_id):
        """Return the readable body and reply headers for one Gmail message."""
        with self._api_lock:
            item = self._get_service().users().messages().get(
                userId="me", id=message_id, format="full"
            ).execute(num_retries=2)
        payload = item.get("payload", {})
        headers = self._headers(payload)
        sender_name, sender_address = parseaddr(headers.get("from", ""))
        return {
            "id": item["id"],
            "thread_id": item.get("threadId", ""),
            "sender": sender_name or sender_address or headers.get("from", "Mittente sconosciuto"),
            "sender_address": sender_address,
            "reply_to": parseaddr(headers.get("reply-to", ""))[1] or sender_address,
            "subject": self._decoded_header(headers.get("subject")) or "Senza oggetto",
            "date": headers.get("date", ""),
            "message_id": headers.get("message-id", ""),
            "references": headers.get("references", ""),
            "body": (
                self._extract_plain_text(payload, item["id"])
                or self._extract_html_text(payload, item["id"])
                or item.get("snippet", "(Messaggio senza testo)")
            ),
        }

    def _part_data(self, part, message_id):
        body = part.get("body", {})
        data = body.get("data")
        if data:
            return data
        attachment_id = body.get("attachmentId")
        if not attachment_id:
            return None
        with self._api_lock:
            response = self._get_service().users().messages().attachments().get(
                userId="me", messageId=message_id, id=attachment_id,
            ).execute(num_retries=2)
        return response.get("data")

    def _extract_plain_text(self, part, message_id):
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            data = self._part_data(part, message_id)
        else:
            data = None
        if data:
            try:
                return base64.urlsafe_b64decode(data.encode("ascii")).decode(
                    "utf-8", errors="replace"
                )
            except (binascii.Error, ValueError, UnicodeError):
                return ""
        for child in part.get("parts", []):
            text = self._extract_plain_text(child, message_id)
            if text:
                return text
        return ""

    def _extract_html_text(self, part, message_id):
        """Turn HTML-only Gmail bodies into readable text for the desktop pane."""
        if part.get("mimeType") == "text/html":
            data = self._part_data(part, message_id)
            try:
                markup = base64.urlsafe_b64decode(data.encode("ascii")).decode(
                    "utf-8", errors="replace"
                ) if data else ""
            except (binascii.Error, ValueError, UnicodeError):
                markup = ""
            if markup:
                markup = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", markup)
                markup = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h[1-6])\s*>", "\n", markup)
                text = html.unescape(re.sub(r"<[^>]+>", " ", markup))
                return "\n".join(line.strip() for line in text.splitlines() if line.strip())
        for child in part.get("parts", []):
            text = self._extract_html_text(child, message_id)
            if text:
                return text
        return ""

    def reply_to_email(self, email_data, body):
        """Send a plain-text reply linked to the selected Gmail thread."""
        body = body.strip()
        recipient = email_data.get("reply_to") or email_data.get("sender_address")
        if not recipient or "@" not in recipient:
            raise ValueError("Il messaggio selezionato non contiene un indirizzo valido.")
        if not body:
            raise ValueError("Scrivi o detta il testo della risposta prima di inviarla.")

        subject = email_data.get("subject", "")
        message = MIMEText(body, "plain", "utf-8")
        message["To"] = recipient
        message["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        original_id = email_data.get("message_id")
        if original_id:
            message["In-Reply-To"] = original_id
            references = email_data.get("references", "").strip()
            message["References"] = f"{references} {original_id}".strip()

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        with self._api_lock:
            result = self._get_service().users().messages().send(
                userId="me",
                body={"raw": raw, "threadId": email_data.get("thread_id")},
            ).execute(num_retries=2)
        return result.get("id", "")

    def get_unread_emails_summary(self) -> str:
        """Return a short unread inbox summary for voice commands."""
        try:
            messages = [email for email in self.get_recent_emails(50) if email["unread"]]
            if not messages:
                return "Non hai email non lette nella posta in arrivo."
            preview = "; ".join(
                f"Da {item['sender']}, oggetto: {item['subject']}"
                for item in messages[:3]
            )
            return f"Hai {len(messages)} email non lette. Le più recenti: {preview}."
        except Exception as error:
            return f"Errore durante il recupero delle email: {error}"
