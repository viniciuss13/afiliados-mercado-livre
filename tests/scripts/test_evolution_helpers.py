"""Testes dos dados sanitizados dos comandos Evolution."""

import unittest

from scripts.affiliate_list_groups import compact_groups
from scripts.evolution_status import _connection_state, _safe_webhook


class EvolutionHelpersTest(unittest.TestCase):
    def test_group_filter_returns_only_matching_name_and_jid(self) -> None:
        payload = [
            {
                "subject": "PROMOS DA LUH #98",
                "id": "source@g.us",
                "token": "hidden",
            },
            {"subject": "Outro grupo", "id": "other@g.us"},
        ]
        self.assertEqual(
            compact_groups(payload, "promos da luh"),
            [{"name": "PROMOS DA LUH #98", "jid": "source@g.us"}],
        )

    def test_status_helpers_do_not_return_credentials(self) -> None:
        self.assertEqual(
            _connection_state({"instance": {"state": "open", "token": "secret"}}),
            "open",
        )
        webhook = _safe_webhook(
            {
                "url": "http://host.docker.internal:8000/webhooks/evolution",
                "events": ["MESSAGES_UPSERT"],
                "headers": {"X-Webhook-Secret": "secret"},
            }
        )
        self.assertNotIn("headers", webhook)
        self.assertTrue(webhook["configured"])


if __name__ == "__main__":
    unittest.main()
