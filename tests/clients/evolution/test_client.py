"""Testes unitários do client da Evolution API."""

import unittest
from unittest.mock import Mock

import requests
from pydantic import ValidationError

from automation_whats.clients.evolution import EvolutionClient, EvolutionResponseError
from automation_whats.clients.evolution.schemas import (
    MediaMessageRequest,
    TextMessageRequest,
)
from automation_whats.clients.evolution.settings import EvolutionSettings


class EvolutionClientTest(unittest.TestCase):
    """Testa serialização de payloads e tratamento de respostas do client."""

    def setUp(self) -> None:
        """Prepara um client com sessão HTTP falsa para cada teste."""
        self.settings = EvolutionSettings(
            base_url="http://localhost:8080",
            instance_name="weca",
            api_key="test-key",
            timeout=5,
        )
        self.session = Mock(spec=requests.Session)
        self.client = EvolutionClient(settings=self.settings, session=self.session)

    def test_send_text_posts_expected_payload(self) -> None:
        """Deve enviar texto para o endpoint correto com payload esperado."""
        self.session.request.return_value = self._json_response({"status": "PENDING"})

        response = self.client.send_text(number="5571999999999", text="Ola")

        self.assertEqual(response, {"status": "PENDING"})
        self.session.request.assert_called_once_with(
            method="POST",
            url="http://localhost:8080/message/sendText/weca",
            headers={"apikey": "test-key", "Content-Type": "application/json"},
            json={"number": "5571999999999", "text": "Ola"},
            timeout=5,
        )

    def test_send_media_posts_expected_payload(self) -> None:
        """Deve enviar mídia para o endpoint correto com payload esperado."""
        self.session.request.return_value = self._json_response({"status": "PENDING"})

        self.client.send_media(
            number="5571999999999",
            media="https://example.com/image.png",
            media_type="image",
            mime_type="image/png",
            caption="Imagem",
            file_name="image.png",
        )

        self.session.request.assert_called_once_with(
            method="POST",
            url="http://localhost:8080/message/sendMedia/weca",
            headers={"apikey": "test-key", "Content-Type": "application/json"},
            json={
                "number": "5571999999999",
                "mediatype": "image",
                "mimetype": "image/png",
                "caption": "Imagem",
                "media": "https://example.com/image.png",
                "fileName": "image.png",
            },
            timeout=5,
        )

    def test_http_error_raises_client_exception(self) -> None:
        """Deve converter status HTTP de erro em exceção do client."""
        self.session.request.return_value = self._json_response(
            {"message": "Unauthorized"},
            status_code=401,
            text="Unauthorized",
        )

        with self.assertRaises(EvolutionResponseError):
            self.client.send_text(number="5571999999999", text="Ola")

    def test_find_webhook_gets_expected_endpoint(self) -> None:
        """Deve consultar a configuração de webhook da instância."""
        self.session.request.return_value = self._json_response(None)

        response = self.client.find_webhook()

        self.assertIsNone(response)
        self.session.request.assert_called_once_with(
            method="GET",
            url="http://localhost:8080/webhook/find/weca",
            headers={"apikey": "test-key", "Content-Type": "application/json"},
            timeout=5,
        )

    def test_set_webhook_posts_expected_payload(self) -> None:
        """Deve configurar webhook no endpoint esperado."""
        self.session.request.return_value = self._json_response({"enabled": True})

        response = self.client.set_webhook(
            url="http://host.docker.internal:8000/webhooks/evolution",
            events=["MESSAGES_UPSERT"],
            headers={"X-Webhook-Secret": "secret"},
        )

        self.assertEqual(response, {"enabled": True})
        self.session.request.assert_called_once_with(
            method="POST",
            url="http://localhost:8080/webhook/set/weca",
            headers={"apikey": "test-key", "Content-Type": "application/json"},
            json={
                "webhook": {
                    "enabled": True,
                    "url": "http://host.docker.internal:8000/webhooks/evolution",
                    "events": ["MESSAGES_UPSERT"],
                    "webhookByEvents": False,
                    "webhookBase64": False,
                    "headers": {"X-Webhook-Secret": "secret"},
                }
            },
            timeout=5,
        )

    def test_text_message_requires_number_and_text(self) -> None:
        """Deve validar número e texto obrigatórios no schema de texto."""
        with self.assertRaises(ValidationError):
            TextMessageRequest(number="", text="")

    def test_media_message_uses_evolution_api_aliases(self) -> None:
        """Deve serializar campos Python com aliases esperados pela API."""
        payload = MediaMessageRequest(
            number="5571999999999",
            media="https://example.com/image.png",
            media_type="image",
            mime_type="image/png",
            caption="Imagem",
            file_name="image.png",
        ).to_payload()

        self.assertEqual(payload["mediatype"], "image")
        self.assertEqual(payload["mimetype"], "image/png")
        self.assertEqual(payload["fileName"], "image.png")

    @staticmethod
    def _json_response(
        payload: dict | None,
        status_code: int = 201,
        text: str = "",
    ) -> Mock:
        """Cria uma resposta HTTP falsa compatível com `requests`.

        Args:
            payload: Conteúdo retornado pelo método `json`.
            status_code: Status HTTP simulado.
            text: Corpo textual da resposta simulada.

        Returns:
            Mock com interface mínima de uma resposta `requests.Response`.
        """
        response = Mock()
        response.status_code = status_code
        response.text = text
        response.json.return_value = payload
        return response


if __name__ == "__main__":
    unittest.main()
