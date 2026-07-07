#!/usr/bin/env python3
"""
Telegram Job Scraper
======================
Reads messages from a Telegram group using the user's own account (Telethon).
Translation is handled by Google Translate (same as AllJobs tab).

Requirements:
    pip install telethon python-dotenv

Setup:
    1. Get API credentials at https://my.telegram.org → App configuration
    2. Copy .env.example to .env and fill in your credentials
    3. On first run you'll receive a code in your Telegram app to verify
"""

import os
from datetime import timezone


SESSION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telegram")


class TelegramJobFetcher:
    """
    Wraps Telethon's sync client to fetch Telegram job posts.
    Creates a fresh client for each operation to avoid asyncio event loop
    conflicts with Streamlit's rerun model.
    """

    def __init__(self, api_id: int, api_hash: str, phone: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone

    def _new_client(self):
        """Always create a fresh TelegramClient (session file handles auth persistence)."""
        from telethon.sync import TelegramClient
        return TelegramClient(SESSION_PATH, self.api_id, self.api_hash)

    def is_authorized(self) -> bool:
        """Check if a valid session exists without starting a persistent connection."""
        client = self._new_client()
        try:
            client.connect()
            return client.is_user_authorized()
        finally:
            client.disconnect()

    def send_code(self) -> str:
        """Send verification code to Telegram app. Returns phone_code_hash."""
        client = self._new_client()
        try:
            client.connect()
            result = client.send_code_request(self.phone)
            return result.phone_code_hash
        finally:
            client.disconnect()

    def sign_in(self, code: str, phone_code_hash: str, password: str = "") -> bool:
        """Complete sign-in with received code. Pass password if 2FA is enabled."""
        from telethon.errors import SessionPasswordNeededError
        client = self._new_client()
        try:
            client.connect()
            try:
                client.sign_in(self.phone, code, phone_code_hash=phone_code_hash)
            except SessionPasswordNeededError:
                if not password:
                    raise RuntimeError("2FA_REQUIRED")
                client.sign_in(password=password)
            return True
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Sign-in failed: {e}") from e
        finally:
            client.disconnect()

    def list_dialogs(self) -> list[dict]:
        """Return groups and channels the user is a member of."""
        client = self._new_client()
        try:
            client.connect()
            dialogs = []
            for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    dialogs.append({
                        "id": dialog.id,
                        "name": dialog.name or "(unnamed)",
                        "is_channel": dialog.is_channel,
                        "username": getattr(dialog.entity, "username", None),
                    })
            return dialogs
        finally:
            client.disconnect()

    def fetch_messages(self, entity_id: int, limit: int = 200) -> list[dict]:
        """
        Fetch recent text messages from a group/channel.
        First line of each message becomes the title; rest is description.
        """
        from telethon.tl.types import MessageService

        client = self._new_client()
        try:
            client.connect()

            try:
                chat = client.get_entity(entity_id)
                chat_username = getattr(chat, "username", None)
            except Exception:
                chat_username = None

            messages = []
            for msg in client.iter_messages(entity_id, limit=limit):
                if isinstance(msg, MessageService):
                    continue
                text = (msg.text or "").strip()
                if len(text) < 30:
                    continue

                # Sender display name
                sender_name = ""
                if msg.sender:
                    if hasattr(msg.sender, "first_name"):
                        parts = [msg.sender.first_name or "", msg.sender.last_name or ""]
                        sender_name = " ".join(p for p in parts if p).strip()
                    elif hasattr(msg.sender, "title"):
                        sender_name = msg.sender.title or ""

                # Deep link
                if chat_username:
                    source_url = f"https://t.me/{chat_username}/{msg.id}"
                else:
                    source_url = f"https://t.me/c/{abs(entity_id)}/{msg.id}"

                # Date
                date_utc = msg.date.astimezone(timezone.utc)
                date_str = date_utc.strftime("%Y-%m-%d %H:%M UTC")

                # First line = title, full text = description (so nothing is hidden)
                title = text.split("\n", 1)[0].strip()

                messages.append({
                    "message_id": str(msg.id),
                    "title": title,
                    "company": sender_name,
                    "location": "",
                    "job_type": "",
                    "description": text,
                    "requirements": "",
                    "date_posted": date_str,
                    "date_ts": date_utc.timestamp(),
                    "sender": sender_name,
                    "source_url": source_url,
                })

            return messages
        finally:
            client.disconnect()
