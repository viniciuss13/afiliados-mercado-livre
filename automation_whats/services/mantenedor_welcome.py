"""Service para enviar boas-vindas a novos mantenedores."""

from typing import Any

from dotenv import load_dotenv

from automation_whats.clients.evolution import EvolutionClient
from automation_whats.services.admin_recipients import get_admin_recipients
from automation_whats.services.mantenedor_media import get_wecare_image_media
from automation_whats.services.phone import normalize_brazilian_phone


WELCOME_MESSAGE_TEMPLATE = """Olá, {nome}! 💙

É uma alegria ter você como mantenedor do We Care.

Passando apenas para confirmar que seu cadastro foi realizado com sucesso. Agradecemos por caminhar conosco nessa missão de cuidar de famílias e transformar vidas.

Que Deus abençoe sua generosidade! 🙏"""


class MantenedorWelcomeService:
    """Envia mensagem de boas-vindas para novos mantenedores."""

    def __init__(self, client: EvolutionClient | None = None) -> None:
        """Inicializa o service.

        Args:
            client: Client da Evolution API. Quando ausente, um novo client é
                criado a partir das variáveis de ambiente.
        """
        load_dotenv()
        self._client = client or EvolutionClient()

    def send(self, nome: str, telefone: str, valor: str) -> dict[str, Any]:
        """Envia boas-vindas ao novo mantenedor e avisa os administradores.

        Args:
            nome: Nome da pessoa mantenedora.
            telefone: Telefone/WhatsApp da pessoa mantenedora.
            valor: Valor informado no cadastro.

        Returns:
            Dicionário com as respostas da Evolution API.
        """
        recipient_number = self._normalize_phone(telefone)
        image_media = get_wecare_image_media()
        message = WELCOME_MESSAGE_TEMPLATE.format(nome=nome)

        if image_media:
            recipient_response = self._client.send_media(
                number=recipient_number,
                media=image_media["media"],
                media_type="image",
                mime_type=image_media["mime_type"],
                caption=message,
                file_name=image_media["file_name"],
            )
        else:
            recipient_response = self._client.send_text(
                number=recipient_number,
                text=message,
            )

        admin_responses = self._send_admin_messages(
            message=self._build_admin_message(nome=nome, valor=valor)
        )

        return {"recipient": recipient_response, "admin": admin_responses}

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
        """Monta a mensagem administrativa de novo cadastro.

        Args:
            nome: Nome da pessoa cadastrada.
            valor: Valor informado no cadastro.

        Returns:
            Texto da mensagem administrativa.
        """
        return f"Novo mantenedor cadastrado.\n\nNome: {nome}\nValor: {valor}"

    def _normalize_phone(self, phone: str) -> str:
        """Remove caracteres não numéricos do telefone.

        Args:
            phone: Telefone informado no cadastro.

        Returns:
            Telefone contendo apenas dígitos.
        """
        return normalize_brazilian_phone(phone)
