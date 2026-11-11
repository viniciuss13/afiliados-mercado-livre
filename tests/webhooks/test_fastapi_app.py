"""Testes das rotas HTTP sem chamadas externas."""

import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from automation_whats.webhooks.app import create_app


class FastAPIWebhookAppTest(unittest.TestCase):
    def test_health_returns_ok(self) -> None:
        client = TestClient(create_app(evolution_handler=Mock()))
        self.assertEqual(client.get("/health").json(), {"status": "ok"})

    @patch.dict(
        "os.environ",
        {
            "AFFILIATE_ENABLED": "true",
            "AFFILIATE_SOURCE_GROUP_JIDS": (
                "120363111111111111@g.us,120363333333333333@g.us"
            ),
            "AFFILIATE_DESTINATION_GROUP_JID": "120363222222222222@g.us",
        },
        clear=False,
    )
    def test_ready_reports_safe_configuration(self) -> None:
        client = TestClient(create_app(evolution_handler=Mock()))
        response = client.get("/ready")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["groups_configured"])
        self.assertFalse(response.json()["auto_publish"])

    @patch.dict("os.environ", {"WEBHOOK_SECRET": ""}, clear=False)
    def test_evolution_route_calls_handler(self) -> None:
        handler = Mock()
        handler.handle.return_value = {"status": "queued", "offers": 1}
        client = TestClient(create_app(evolution_handler=handler))
        payload = {"event": "MESSAGES_UPSERT", "data": {}}
        response = client.post("/webhooks/evolution", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "queued", "offers": 1})
        handler.handle.assert_called_once_with(payload)

    @patch.dict("os.environ", {"WEBHOOK_SECRET": "secret"}, clear=False)
    def test_webhook_secret_is_required(self) -> None:
        client = TestClient(create_app(evolution_handler=Mock()))
        response = client.post("/webhooks/evolution", json={})
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
