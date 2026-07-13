"""Testes da aplicacao FastAPI de webhooks."""

import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from automation_whats.webhooks.app import create_app


class FastAPIWebhookAppTest(unittest.TestCase):
    """Testa as rotas FastAPI expostas pelo webhook."""

    def test_health_returns_ok(self) -> None:
        """Deve retornar status ok no healthcheck."""
        client = TestClient(create_app())

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_google_form_route_calls_handler(self) -> None:
        """Deve processar cadastro valido vindo do Google Forms."""
        handler = Mock()
        handler.handle.return_value = {"status": "processed"}
        client = TestClient(create_app(google_form_handler=handler))

        response = client.post(
            "/webhooks/google-form/mantenedor",
            json={"nome": "Maria", "telefone": "5571999999999", "valor": "50,00"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "processed"})
        handler.handle.assert_called_once_with(
            {"nome": "Maria", "telefone": "5571999999999", "valor": "50,00"}
        )

    def test_google_form_route_validates_payload(self) -> None:
        """Deve retornar 422 quando payload obrigatorio estiver ausente."""
        client = TestClient(create_app())

        response = client.post(
            "/webhooks/google-form/mantenedor",
            json={"nome": "Maria"},
        )

        self.assertEqual(response.status_code, 422)

    @patch.dict(
        "os.environ",
        {"WEBHOOK_SECRET": "secret", "WEBHOOK_SECRET_HEADER": "X-Webhook-Secret"},
        clear=False,
    )
    def test_webhook_secret_is_required_when_configured(self) -> None:
        """Deve bloquear requisicao sem segredo quando configurado."""
        client = TestClient(create_app(google_form_handler=Mock()))

        response = client.post(
            "/webhooks/google-form/mantenedor",
            json={"nome": "Maria", "telefone": "5571999999999", "valor": "50,00"},
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
