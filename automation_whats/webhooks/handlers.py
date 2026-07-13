"""Handlers para eventos recebidos via webhook."""

import json
from typing import Any

from automation_whats.services.mantenedor_reactivation import (
    MantenedorReactivationReplyService,
)
from automation_whats.services.mantenedor_welcome import MantenedorWelcomeService

from .schemas import EvolutionWebhookEvent, GoogleFormMantenedorPayload


class EvolutionWebhookHandler:
    """Processa eventos de webhook enviados pela Evolution API."""

    def __init__(
        self,
        reactivation_reply_service: MantenedorReactivationReplyService | None = None,
    ) -> None:
        """Inicializa o handler.

        Args:
            reactivation_reply_service: Service que cadastra respostas de
                reativacao de antigos mantenedores.
        """
        self._reactivation_reply_service = (
            reactivation_reply_service or MantenedorReactivationReplyService()
        )

    def handle(self, payload: dict[str, Any]) -> dict[str, str]:
        """Processa um payload recebido da Evolution API.

        Args:
            payload: Corpo JSON recebido no webhook.

        Returns:
            Dicionario simples indicando que o evento foi recebido.
        """
        event = EvolutionWebhookEvent.model_validate(payload)
        self._log_event(event)
        reactivation_reply = self._extract_reactivation_reply(event)
        if reactivation_reply:
            return self._reactivation_reply_service.process_reply(
                nome=reactivation_reply["nome"],
                telefone=reactivation_reply["telefone"],
                message=reactivation_reply["message"],
            )

        return {"status": "received"}

    def _log_event(self, event: EvolutionWebhookEvent) -> None:
        """Registra o evento recebido no stdout.

        Args:
            event: Evento validado.
        """
        summary = {
            "event": event.event,
            "instance": event.instance,
            "sender": event.sender,
        }
        print(json.dumps(summary, ensure_ascii=False))

    def _extract_reactivation_reply(
        self,
        event: EvolutionWebhookEvent,
    ) -> dict[str, str] | None:
        """Extrai dados de uma mensagem recebida no WhatsApp.

        Args:
            event: Evento validado da Evolution API.

        Returns:
            Dados da resposta ou `None` quando o evento nao for uma mensagem de
            usuario.
        """
        data = event.data
        if not isinstance(data, dict):
            return None

        key = data.get("key") if isinstance(data.get("key"), dict) else {}
        if key.get("fromMe") is True:
            return None

        message = self._extract_text(data)
        telefone = self._extract_phone(data=data, event=event)
        if not message or not telefone:
            return None

        nome = str(data.get("pushName") or data.get("senderName") or telefone)
        return {"nome": nome, "telefone": telefone, "message": message}

    def _extract_text(self, data: dict[str, Any]) -> str | None:
        """Extrai texto de formatos comuns de mensagem da Evolution API."""
        message = data.get("message")
        if not isinstance(message, dict):
            message_text = data.get("messageText")
            return message_text if isinstance(message_text, str) else None

        candidates = [
            message.get("conversation"),
            message.get("extendedTextMessage", {}).get("text")
            if isinstance(message.get("extendedTextMessage"), dict)
            else None,
            message.get("text"),
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

        return None

    def _extract_phone(
        self,
        data: dict[str, Any],
        event: EvolutionWebhookEvent,
    ) -> str | None:
        """Extrai telefone de formatos comuns de remetente."""
        key = data.get("key") if isinstance(data.get("key"), dict) else {}
        candidates = [
            key.get("remoteJid"),
            data.get("remoteJid"),
            data.get("sender"),
            event.sender,
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate:
                phone = candidate.split("@", maxsplit=1)[0]
                digits = "".join(char for char in phone if char.isdigit())
                if digits:
                    return digits

        return None


class GoogleFormMantenedorWebhookHandler:
    """Processa cadastros de mantenedores vindos do Google Forms."""

    def __init__(
        self,
        welcome_service: MantenedorWelcomeService | None = None,
    ) -> None:
        """Inicializa o handler.

        Args:
            welcome_service: Service responsável pelos disparos de boas-vindas
                no WhatsApp.
        """
        self._welcome_service = welcome_service or MantenedorWelcomeService()

    def handle(self, payload: dict[str, Any]) -> dict[str, str]:
        """Processa o cadastro recebido do Google Forms.

        Args:
            payload: Corpo JSON enviado pelo Google Apps Script.

        Returns:
            Dicionario simples indicando que o cadastro foi processado.
        """
        form_payload = GoogleFormMantenedorPayload.model_validate(payload)
        self._welcome_service.send(
            nome=form_payload.nome,
            telefone=form_payload.telefone,
            valor=form_payload.valor,
        )
        return {"status": "processed"}
