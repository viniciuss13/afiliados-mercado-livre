"""Testes da fila SQLite."""

import tempfile
import unittest
from pathlib import Path

from automation_whats.affiliate.models import IncomingMessage, OfferStatus
from automation_whats.affiliate.repository import AffiliateRepository


class AffiliateRepositoryTest(unittest.TestCase):
    def test_requeue_only_recovers_legacy_copy_failures_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = AffiliateRepository(Path(directory) / "affiliate.sqlite3")
            urls = ("https://meli.la/product", "https://meli.la/showcase")
            repository.enqueue(IncomingMessage("affiliate", "MSG", "test@g.us", None, "Oferta", urls))
            copied, showcase = repository.list_offers((OfferStatus.RECEIVED,))
            for offer in (copied, showcase):
                repository.update_resolution(offer["id"], offer["original_url"], "mercado_livre", None)
            repository.record_failure(
                copied["id"], "O link copiado não resolveu para um produto identificável", 1,
            )
            repository.record_failure(showcase["id"], "Vitrine sem produto específico", 1)

            self.assertEqual(repository.requeue_legacy_copy_failures(), 1)
            self.assertEqual(repository.requeue_legacy_copy_failures(), 0)
            restored = repository.get_offer(copied["id"])
            self.assertEqual(restored["status"], OfferStatus.NEEDS_CONVERSION)
            self.assertEqual(restored["attempts"], 0)
            self.assertIsNone(restored["last_error"])
            self.assertEqual(repository.get_offer(showcase["id"])["status"], OfferStatus.QUARANTINED)

    def test_enqueue_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = AffiliateRepository(Path(directory) / "affiliate.sqlite3")
            message = IncomingMessage(
                instance="affiliate",
                message_id="MSG-1",
                remote_jid="120363000000000000@g.us",
                participant_jid=None,
                text="Oferta https://meli.la/abc",
                urls=("https://meli.la/abc",),
            )

            self.assertEqual(repository.enqueue(message), (True, 1))
            self.assertEqual(repository.enqueue(message), (False, 0))
            offers = repository.list_offers((OfferStatus.RECEIVED,))
            self.assertEqual(len(offers), 1)


if __name__ == "__main__":
    unittest.main()
