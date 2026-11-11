"""Testes do filtro de grupos no webhook."""

import tempfile
import unittest
from pathlib import Path

from automation_whats.affiliate.repository import AffiliateRepository
from automation_whats.affiliate.settings import AffiliateSettings
from automation_whats.webhooks.handlers import EvolutionWebhookHandler


class AffiliateWebhookHandlerTest(unittest.TestCase):
    def test_only_source_group_is_queued_and_duplicate_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = AffiliateSettings(
                enabled=True,
                source_group_jids=(
                    "120363111111111111@g.us",
                    "120363444444444444@g.us",
                ),
                destination_group_jid="120363222222222222@g.us",
                db_path=Path(directory) / "affiliate.sqlite3",
            )
            handler = EvolutionWebhookHandler(
                settings=settings,
                repository=AffiliateRepository(settings.db_path),
            )
            payload = {
                "event": "MESSAGES_UPSERT",
                "instance": "affiliate",
                "data": {
                    "key": {
                        "remoteJid": settings.source_group_jids[0],
                        "fromMe": False,
                        "id": "MSG-1",
                    },
                    "message": {"conversation": "Oferta https://meli.la/abc"},
                },
            }

            self.assertEqual(handler.handle(payload), {"status": "queued", "offers": 1})
            self.assertEqual(handler.handle(payload), {"status": "duplicate"})

            payload["data"]["key"]["id"] = "MSG-2"
            payload["data"]["key"]["remoteJid"] = settings.source_group_jids[1]
            self.assertEqual(
                handler.handle(payload), {"status": "queued", "offers": 1}
            )

            payload["data"]["key"]["id"] = "MSG-3"
            payload["data"]["key"]["remoteJid"] = "120363333333333333@g.us"
            self.assertEqual(handler.handle(payload), {"status": "ignored_group"})


if __name__ == "__main__":
    unittest.main()
