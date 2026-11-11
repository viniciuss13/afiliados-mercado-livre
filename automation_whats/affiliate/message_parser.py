"""Normalizacao de eventos de mensagem da Evolution API."""

import re
from typing import Any

from .models import IncomingMessage


URL_PATTERN = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)


class EvolutionMessageParser:
    """Extrai somente os dados necessários de `MESSAGES_UPSERT`."""

    def parse(self, payload: dict[str, Any]) -> IncomingMessage | None:
        event = str(payload.get("event") or "").lower().replace("_", ".")
        if event != "messages.upsert":
            return None

        data = payload.get("data")
        if not isinstance(data, dict):
            return None
        key = data.get("key") if isinstance(data.get("key"), dict) else {}
        if key.get("fromMe") is True:
            return None

        remote_jid = str(key.get("remoteJid") or data.get("remoteJid") or "")
        message_id = str(key.get("id") or data.get("messageId") or "")
        if not remote_jid or not message_id:
            return None

        text, media_type = self._extract_content(data)
        if not text:
            return None
        urls = tuple(dict.fromkeys(self._extract_urls(text)))
        if not urls:
            return None

        participant = key.get("participant") or data.get("participant")
        return IncomingMessage(
            instance=str(payload.get("instance") or ""),
            message_id=message_id,
            remote_jid=remote_jid,
            participant_jid=str(participant) if participant else None,
            text=text,
            urls=urls,
            media_type=media_type,
        )

    def _extract_content(self, data: dict[str, Any]) -> tuple[str | None, str | None]:
        message = data.get("message")
        if not isinstance(message, dict):
            value = data.get("messageText")
            return (value.strip(), None) if isinstance(value, str) and value.strip() else (None, None)

        candidates: tuple[tuple[Any, str | None], ...] = (
            (message.get("conversation"), None),
            (self._nested(message, "extendedTextMessage", "text"), None),
            (self._nested(message, "imageMessage", "caption"), "image"),
            (self._nested(message, "videoMessage", "caption"), "video"),
            (self._nested(message, "documentMessage", "caption"), "document"),
            (
                self._nested(
                    message,
                    "documentWithCaptionMessage",
                    "message",
                    "documentMessage",
                    "caption",
                ),
                "document",
            ),
            (message.get("text"), None),
        )
        for value, media_type in candidates:
            if isinstance(value, str) and value.strip():
                return value.strip(), media_type
        return None, None

    def _extract_urls(self, text: str) -> list[str]:
        return [match.rstrip(".,;:!?)]}\"") for match in URL_PATTERN.findall(text)]

    @staticmethod
    def _nested(value: dict[str, Any], *keys: str) -> Any:
        current: Any = value
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current
