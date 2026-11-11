"""Testes do fluxo conversao, revisao e publicacao."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from automation_whats.affiliate.models import IncomingMessage, OfferStatus, ResolvedLink
from automation_whats.affiliate.marketplaces.mercado_livre_poc import MercadoLivrePocConverter
from automation_whats.affiliate.marketplaces.mercado_livre_playwright import (
    MercadoLivreConversionResult,
)
from poc.mercadolivre_affiliate.run import TestResult, UnexpectedProductPage, VerificationRequired
from automation_whats.affiliate.repository import AffiliateRepository
from automation_whats.affiliate.settings import AffiliateSettings
from automation_whats.affiliate.worker import AffiliateWorker


class AffiliateWorkerTest(unittest.TestCase):
    def test_conversion_skips_unexpected_page_and_respects_round_limit(self) -> None:
        settings = AffiliateSettings(mercado_livre_playwright_enabled=True)
        repository = Mock()
        repository.list_offers.return_value = [
            {"id": 1, "original_url": "https://meli.la/showcase"},
            {"id": 2, "original_url": "https://meli.la/product"},
            {"id": 3, "original_url": "https://meli.la/next"},
        ]
        repository.record_failure.return_value = OfferStatus.QUARANTINED
        converter = Mock()
        product_url = "https://produto.mercadolivre.com.br/MLB-123-item"
        converter.convert.side_effect = [
            UnexpectedProductPage("Vitrine sem produto específico"),
            MercadoLivreConversionResult(product_url, "MLB123", "https://meli.la/affiliate", product_url),
        ]
        worker = AffiliateWorker(settings, repository, mercado_livre_converter=converter)

        self.assertEqual(worker.process_conversions(), [
            {"id": 1, "status": "QUARANTINED", "error": "Vitrine sem produto específico"},
            {"id": 2, "status": "NEEDS_REVIEW"},
        ])
        repository.record_failure.assert_called_once_with(
            1, "Vitrine sem produto específico", 1, expected_status=OfferStatus.NEEDS_CONVERSION,
        )
        self.assertEqual(converter.convert.call_count, 2)

    def test_verification_failure_uses_the_normal_attempt_limit(self) -> None:
        settings = AffiliateSettings(mercado_livre_playwright_enabled=True)
        repository = Mock()
        repository.list_offers.return_value = [
            {"id": 1, "original_url": "https://meli.la/first"},
            {"id": 2, "original_url": "https://meli.la/next"},
        ]
        repository.record_failure.return_value = OfferStatus.RETRY
        converter = Mock()
        converter.convert.side_effect = VerificationRequired("Verificação pendente")
        worker = AffiliateWorker(settings, repository, mercado_livre_converter=converter)

        self.assertEqual(worker.process_conversions(), [
            {"id": 1, "status": "RETRY", "error": "Verificação pendente"},
        ])
        repository.record_failure.assert_called_once_with(
            1, "Verificação pendente", settings.max_retries, expected_status=OfferStatus.NEEDS_CONVERSION,
        )
        converter.convert.assert_called_once_with("https://meli.la/first")

    def test_poc_saves_confirmed_short_link_without_resolving_it(self) -> None:
        product_url = "https://www.mercadolivre.com.br/produto/p/MLB123"
        source_url = f"{product_url}?pdp_filters=item_id%3AMLB456"
        affiliate_url = "https://meli.la/affiliate"
        resolver = Mock()
        resolver.resolve.return_value = ResolvedLink(source_url, source_url, (source_url,))
        converter = MercadoLivrePocConverter(resolver, browser="edge", headless=False)
        with patch.object(
            converter, "_collect",
            return_value=TestResult(affiliate_url, affiliate_url, product_url, "MLB789"),
        ):
            converted = converter.convert(source_url)
        self.assertEqual(converted.affiliate_url, affiliate_url)
        self.assertEqual(converted.source_product_id, "MLB123")
        resolver.resolve.assert_called_once_with(source_url)

    def test_automatic_conversion_moves_offer_to_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = AffiliateSettings(
                enabled=True,
                source_group_jids=("120363111111111111@g.us",),
                destination_group_jid="120363222222222222@g.us",
                db_path=Path(directory) / "affiliate.sqlite3",
                mercado_livre_playwright_enabled=True,
                playwright_headless=False,
                review_required=True,
            )
            repository = AffiliateRepository(settings.db_path)
            repository.enqueue(
                IncomingMessage(
                    instance="affiliate",
                    message_id="MSG-AUTO",
                    remote_jid=settings.source_group_jids[0],
                    participant_jid=None,
                    text="Oferta https://meli.la/source",
                    urls=("https://meli.la/source",),
                )
            )
            offer = repository.list_offers((OfferStatus.RECEIVED,))[0]
            repository.update_resolution(
                offer["id"],
                "https://www.mercadolivre.com.br/social/origem",
                "mercado_livre",
                None,
            )
            source_url = "https://www.mercadolivre.com.br/social/origem"
            product_url = "https://produto.mercadolivre.com.br/MLB-123-item"
            affiliate_url = "https://meli.la/affiliate"
            resolver = Mock()
            resolver.resolve.return_value = ResolvedLink("https://meli.la/source", source_url, (source_url,))
            worker = AffiliateWorker(settings, repository, resolver)
            module = "automation_whats.affiliate.marketplaces.mercado_livre_poc"
            with (
                patch(f"{module}.async_playwright"),
                patch(
                    f"{module}.run_browser",
                    return_value=TestResult(affiliate_url, affiliate_url, product_url),
                ) as collect,
            ):
                self.assertEqual(
                    worker.process_conversions(),
                    [{"id": offer["id"], "status": "NEEDS_REVIEW"}],
                )
            collect.assert_awaited_once()
            self.assertEqual(collect.call_args.args[1], "edge")
            self.assertEqual(collect.call_args.args[2].url, "https://meli.la/source")
            self.assertFalse(collect.call_args.args[2].no_login)
            updated = repository.get_offer(offer["id"])
            self.assertEqual(updated["product_id"], "MLB123")
            self.assertEqual(updated["affiliate_url"], "https://meli.la/affiliate")
            resolver.resolve.assert_called_once_with("https://meli.la/source")

    def test_validated_link_requires_review_before_single_publication(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = AffiliateSettings(
                enabled=True,
                source_group_jids=("120363111111111111@g.us",),
                destination_group_jid="120363222222222222@g.us",
                db_path=Path(directory) / "affiliate.sqlite3",
                review_required=True,
                mercado_livre_marker="ref=affiliate",
            )
            repository = AffiliateRepository(settings.db_path)
            repository.enqueue(
                IncomingMessage(
                    instance="affiliate",
                    message_id="MSG-1",
                    remote_jid=settings.source_group_jids[0],
                    participant_jid=None,
                    text=(
                        "Oferta https://www.mercadolivre.com.br/item/MLB-123"
                    ),
                    urls=("https://www.mercadolivre.com.br/item/MLB-123",),
                )
            )
            offer = repository.list_offers((OfferStatus.RECEIVED,))[0]
            repository.update_resolution(
                offer["id"],
                "https://www.mercadolivre.com.br/item/MLB-123",
                "mercado_livre",
                "MLB123",
            )

            resolver = Mock()
            resolver.resolve.side_effect = lambda url: ResolvedLink(url, url, (url,))
            publisher = Mock()
            publisher.send.return_value = {"key": {"id": "OUT-1"}}
            worker = AffiliateWorker(settings, repository, resolver, publisher)

            result = worker.apply_affiliate_link(
                offer["id"],
                "https://www.mercadolivre.com.br/item/MLB-123?ref=affiliate",
            )
            self.assertEqual(result["status"], "NEEDS_REVIEW")
            self.assertEqual(worker.publish_approved(force=True), [])

            repository.add_review(
                offer["id"],
                "approve",
                final_text="Oferta revisada https://meli.la/affiliate",
            )
            self.assertEqual(
                worker.publish_approved(force=True),
                [{"id": offer["id"], "status": "SENT"}],
            )
            publisher.send.assert_called_once_with(
                settings.destination_group_jid,
                (
                    "Oferta "
                    "https://www.mercadolivre.com.br/item/MLB-123?ref=affiliate"
                ),
            )
            self.assertEqual(
                repository.get_offer(offer["id"])["status"], OfferStatus.SENT.value
            )


if __name__ == "__main__":
    unittest.main()
