"""Service para enviar lembretes de contribuição aos mantenedores."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from dotenv import load_dotenv

from automation_whats.clients.evolution import EvolutionClient
from automation_whats.services.admin_recipients import get_admin_recipients
from automation_whats.services.mantenedor_media import get_wecare_image_media
from automation_whats.services.phone import normalize_brazilian_phone


PAYMENT_REMINDER_MESSAGE_TEMPLATE = """Olá, {nome}! 💙

Passando para lembrar com carinho da sua contribuição mensal como mantenedor do We Care.

Valor combinado: {valor}

A sua generosidade nos ajuda a continuar cuidando de famílias e transformando vidas.

Caso você já tenha realizado sua contribuição, por favor desconsidere esta mensagem.

Que Deus abençoe sua generosidade! 🙏"""

PIX_KEY = """*Chave pix*:
wecare@lagoinhacajazeiras.com"""
"""Mensagem com chave Pix enviada como texto separado."""


class MantenedorPaymentReminderService:
    """Envia lembretes de contribuição para mantenedores existentes."""

    def __init__(self, client: EvolutionClient | None = None) -> None:
        """Inicializa o service.

        Args:
            client: Client da Evolution API. Quando ausente, um novo client é
                criado a partir das variáveis de ambiente.
        """
        load_dotenv()
        self._client = client or EvolutionClient()

    def send(self, nome: str, telefone: str, valor: str) -> dict[str, Any]:
        """Envia lembrete de contribuição e chave Pix para um mantenedor.

        Args:
            nome: Nome da pessoa mantenedora.
            telefone: Telefone/WhatsApp da pessoa mantenedora.
            valor: Valor da contribuição registrada na planilha.

        Returns:
            Dicionário com as respostas da Evolution API.
        """
        recipient_number = self._normalize_phone(telefone)
        image_media = get_wecare_image_media()
        formatted_value = self._format_brl(valor)
        message = PAYMENT_REMINDER_MESSAGE_TEMPLATE.format(
            nome=nome,
            valor=formatted_value,
        )
        if image_media:
            reminder_response = self._client.send_media(
                number=recipient_number,
                media=image_media["media"],
                media_type="image",
                mime_type=image_media["mime_type"],
                caption=message,
                file_name=image_media["file_name"],
            )
        else:
            reminder_response = self._client.send_text(
                number=recipient_number,
                text=message,
            )

        pix_response = self._client.send_text(number=recipient_number, text=PIX_KEY)
        admin_response = self._send_admin_messages(
            message=self._build_admin_message(nome=nome, valor=formatted_value)
        )

        return {
            "recipient": {
                "reminder": reminder_response,
                "pix": pix_response,
            },
            "admin": admin_response,
        }

    def _send_admin_messages(self, message: str) -> list[dict[str, Any]]:
        """Envia a mensagem administrativa para todos os destinatários.

        Args:
            message: Texto administrativo que será enviado.

        Returns:
            Lista de respostas da Evolution API.
        """
        responses: list[dict[str, Any]] = []
        for admin_number in get_admin_recipients():
            responses.append(self._client.send_text(number=admin_number, text=message))

        return responses

    def _build_admin_message(self, nome: str, valor: str) -> str:
        """Monta a mensagem administrativa do lembrete enviado.

        Args:
            nome: Nome da pessoa mantenedora.
            valor: Valor da contribuição formatado.

        Returns:
            Texto da mensagem administrativa.
        """
        return f"Lembrete enviado para mantenedor.\n\nNome: *{nome}*\nValor: *{valor}*"

    def _format_brl(self, value: str) -> str:
        """Formata valor em moeda brasileira.

        Args:
            value: Valor vindo da planilha em formato simples ou brasileiro.

        Returns:
            Valor formatado como Real brasileiro.
        """
        decimal_value = self._parse_decimal(value)
        if decimal_value is None:
            stripped = value.strip()
            return stripped if stripped.startswith("R$") else f"R$ {stripped}"

        quantized = decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        formatted = f"{quantized:,.2f}"
        return f"R$ {formatted}".replace(",", "_").replace(".", ",").replace("_", ".")

    def _parse_decimal(self, value: str) -> Decimal | None:
        """Converte textos numéricos comuns em `Decimal`.

        Args:
            value: Valor informado na planilha.

        Returns:
            Decimal quando o texto puder ser interpretado, ou `None`.
        """
        normalized = value.strip().replace("R$", "").replace(" ", "")
        if not normalized:
            return None

        if "," in normalized and "." in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        elif "," in normalized:
            normalized = normalized.replace(",", ".")

        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None

    def _normalize_phone(self, phone: str) -> str:
        """Remove caracteres não numéricos do telefone.

        Args:
            phone: Telefone informado na planilha.

        Returns:
            Telefone contendo apenas dígitos.
        """
        return normalize_brazilian_phone(phone)
