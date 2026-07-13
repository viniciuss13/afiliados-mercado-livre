"""Services para retomada de antigos mantenedores."""

import re
import unicodedata
from typing import Any

from dotenv import load_dotenv

from automation_whats.clients.evolution import EvolutionClient
from automation_whats.clients.google_sheets import GoogleSheetsClient
from automation_whats.services.phone import normalize_brazilian_phone


REACTIVATION_MESSAGE_TEMPLATE = """Olá, {nome}! 💙

Você já caminhou conosco como mantenedor do We Care.

Estamos retomando o projeto de mantenedores na Lagoinha Cajazeiras e gostaríamos muito de contar com você mais uma vez nessa caminhada de cuidado, generosidade e transformação de vidas.

Se você deseja continuar conosco como mantenedor, responda esta mensagem com:

SIM + o valor que deseja contribuir

Exemplo:
SIM 50

Caso não deseje continuar neste momento, pode responder apenas:
NÃO

Será uma alegria ter você novamente conosco. Que Deus abençoe sua vida! 🙏"""


class MantenedorReactivationService:
    """Envia convite de retomada para antigos mantenedores."""

    def __init__(self, client: EvolutionClient | None = None) -> None:
        """Inicializa o service.

        Args:
            client: Client da Evolution API.
        """
        load_dotenv()
        self._client = client or EvolutionClient()

    def send(self, nome: str, telefone: str) -> dict[str, Any]:
        """Envia mensagem de reativacao para um antigo mantenedor.

        Args:
            nome: Nome da pessoa.
            telefone: Telefone/WhatsApp da pessoa.

        Returns:
            Resposta JSON retornada pela Evolution API.
        """
        return self._client.send_text(
            number=self._normalize_phone(telefone),
            text=REACTIVATION_MESSAGE_TEMPLATE.format(nome=nome),
        )

    def _normalize_phone(self, phone: str) -> str:
        """Remove caracteres nao numericos do telefone."""
        return normalize_brazilian_phone(phone)


class MantenedorReactivationReplyService:
    """Cadastra antigos mantenedores que responderem SIM com valor."""

    def __init__(self, sheets_client: GoogleSheetsClient | None = None) -> None:
        """Inicializa o service.

        Args:
            sheets_client: Client do Google Sheets.
        """
        self._sheets_client = sheets_client or GoogleSheetsClient()

    def process_reply(self, nome: str, telefone: str, message: str) -> dict[str, str]:
        """Processa uma resposta recebida pelo WhatsApp.

        Args:
            nome: Nome exibido pelo WhatsApp.
            telefone: Telefone/WhatsApp de quem respondeu.
            message: Texto recebido.

        Returns:
            Status do processamento.
        """
        if self._is_decline(message):
            return {"status": "declined"}

        value = self._extract_value(message)
        if value is None:
            return {"status": "ignored"}

        normalized_phone = self._normalize_phone(telefone)
        if self._sheets_client.find_mantenedor_by_phone(normalized_phone):
            return {"status": "already_registered"}

        resolved_name = self._resolve_name(nome=nome, telefone=normalized_phone)
        if resolved_name is None:
            return {"status": "missing_name"}

        self._sheets_client.append_mantenedor(
            nome=resolved_name,
            telefone=normalized_phone,
            valor=value,
        )
        return {"status": "registered"}

    def _extract_value(self, message: str) -> str | None:
        """Extrai valor de respostas no formato `SIM valor`."""
        match = re.match(
            r"^\s*sim\b\s*[-:+]?\s*(?:r\$)?\s*([0-9]+(?:[,.][0-9]{1,2})?)\s*$",
            message,
            flags=re.IGNORECASE,
        )
        if not match:
            return None

        return match.group(1)

    def _is_decline(self, message: str) -> bool:
        """Identifica respostas negativas como `nao` ou `não`."""
        normalized = self._remove_accents(message).strip().lower()
        return bool(re.match(r"^nao\b", normalized))

    def _remove_accents(self, value: str) -> str:
        """Remove acentos para aceitar respostas com ou sem acentuacao."""
        return "".join(
            char
            for char in unicodedata.normalize("NFD", value)
            if unicodedata.category(char) != "Mn"
        )

    def _resolve_name(self, nome: str, telefone: str) -> str | None:
        """Resolve o nome sem permitir cadastro com telefone como nome."""
        clean_name = nome.strip()
        if clean_name and self._normalize_phone(clean_name) != telefone:
            return clean_name

        former_mantenedor = self._sheets_client.find_former_mantenedor_by_phone(
            telefone
        )
        if former_mantenedor:
            return former_mantenedor.nome

        return None

    def _normalize_phone(self, phone: str) -> str:
        """Remove caracteres nao numericos do telefone."""
        return normalize_brazilian_phone(phone)
