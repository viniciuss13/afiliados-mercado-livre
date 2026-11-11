"""Orquestracao da resolucao, validacao e publicacao de ofertas."""

import re
from typing import Any

from poc.mercadolivre_affiliate.run import PocError, UnexpectedProductPage

from .formatter import format_offer
from .link_resolver import SafeLinkResolver, UnsafeUrlError
from .marketplaces import identify_marketplace, validate_same_product
from .marketplaces.mercado_livre_poc import MercadoLivrePocConverter
from .marketplaces.mercado_livre_playwright import (
    MercadoLivreAutomaticConverter,
    MercadoLivreAutomationError,
)
from .models import OfferStatus
from .publisher import AffiliatePublisher
from .repository import AffiliateRepository
from .settings import AffiliateSettings


class AffiliateWorker:
    """Processa a fila sem depender de IA para tarefas deterministicas."""

    def __init__(
        self,
        settings: AffiliateSettings | None = None,
        repository: AffiliateRepository | None = None,
        resolver: SafeLinkResolver | None = None,
        publisher: AffiliatePublisher | None = None,
        mercado_livre_converter: MercadoLivreAutomaticConverter | MercadoLivrePocConverter | None = None,
    ) -> None:
        self.settings = settings or AffiliateSettings.from_env()
        self.repository = repository or AffiliateRepository(self.settings.db_path)
        self.resolver = resolver or SafeLinkResolver(self.settings.allowed_domains)
        self.publisher = publisher
        self.mercado_livre_converter = mercado_livre_converter

    def process_pending(self, limit: int | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        offers = self.repository.list_offers(
            (OfferStatus.RECEIVED, OfferStatus.RETRY),
            limit or self.settings.review_batch_limit,
        )
        for offer in offers:
            try:
                resolved = self.resolver.resolve(offer["original_url"])
                product = identify_marketplace(resolved.final_url)
                if product is None:
                    raise ValueError("Unsupported marketplace")
                if product.marketplace == "shopee" and not self.settings.shopee_enabled:
                    self.repository.set_status(
                        offer["id"], OfferStatus.NEEDS_REVIEW, "Shopee is disabled"
                    )
                    results.append({"id": offer["id"], "status": "NEEDS_REVIEW"})
                    continue
                if product.marketplace == "mercado_livre" and not self.settings.mercado_livre_enabled:
                    self.repository.set_status(
                        offer["id"],
                        OfferStatus.NEEDS_REVIEW,
                        "Mercado Livre is disabled",
                    )
                    results.append({"id": offer["id"], "status": "NEEDS_REVIEW"})
                    continue
                self.repository.update_resolution(
                    offer["id"],
                    resolved.final_url,
                    product.marketplace,
                    product.product_id,
                )
                results.append({"id": offer["id"], "status": "NEEDS_CONVERSION"})
            except Exception as error:
                reason = self._safe_error(error)
                status = self.repository.record_failure(
                    offer["id"],
                    reason,
                    self.settings.max_retries,
                )
                if status is not None:
                    results.append({"id": offer["id"], "status": status.value, "error": reason})
        return results

    def process_conversions(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Converte automaticamente ofertas do Mercado Livre com Playwright."""
        if not self.settings.mercado_livre_playwright_enabled:
            return []
        converter = self.mercado_livre_converter or MercadoLivrePocConverter(
            self.resolver,
            browser=self.settings.playwright_browser,
            headless=self.settings.playwright_headless,
        )
        remaining = limit or self.settings.playwright_conversion_limit
        offers = self.repository.list_offers(
            (OfferStatus.NEEDS_CONVERSION,),
            max(remaining, self.settings.review_batch_limit),
            marketplace="mercado_livre",
        )
        results: list[dict[str, Any]] = []
        for offer in offers:
            try:
                converted = converter.convert(offer["original_url"])
                status = (
                    OfferStatus.NEEDS_REVIEW
                    if self.settings.review_required
                    else OfferStatus.APPROVED
                )
                if self.repository.complete_conversion(
                    offer["id"], converted.source_url, converted.source_product_id,
                    converted.affiliate_url, status,
                ):
                    results.append({"id": offer["id"], "status": status.value})
            except Exception as error:
                reason = self._safe_error(error)
                unexpected_page = isinstance(error, UnexpectedProductPage)
                status = self.repository.record_failure(
                    offer["id"], reason, 1 if unexpected_page else self.settings.max_retries,
                    expected_status=OfferStatus.NEEDS_CONVERSION,
                )
                if status is not None:
                    results.append({"id": offer["id"], "status": status.value, "error": reason})
                if unexpected_page:
                    continue
            remaining -= 1
            if remaining <= 0:
                break
        return results

    def apply_affiliate_link(self, offer_id: int, affiliate_url: str) -> dict[str, Any]:
        offer = self.repository.get_offer(offer_id)
        if offer is None or not offer.get("resolved_url"):
            raise ValueError("Offer has not been resolved")
        resolved = self.resolver.resolve(affiliate_url)
        product = validate_same_product(offer["resolved_url"], resolved.final_url)
        marker = (
            self.settings.mercado_livre_marker
            if product.marketplace == "mercado_livre"
            else self.settings.shopee_marker
        )
        if not marker:
            raise ValueError("Affiliate ownership marker is not configured")
        resolved_values = (*resolved.redirect_chain, resolved.final_url)
        if not any(marker in value for value in resolved_values):
            raise ValueError("Affiliate ownership marker was not found")
        status = (
            OfferStatus.NEEDS_REVIEW
            if self.settings.review_required
            else OfferStatus.APPROVED
        )
        self.repository.set_affiliate_link(offer_id, affiliate_url, status=status)
        return {"id": offer_id, "status": status.value}

    def publish_approved(self, force: bool = False) -> list[dict[str, Any]]:
        if not (self.settings.auto_publish or force):
            return []
        if not self.settings.groups_configured:
            raise ValueError("Source and destination group JIDs are not configured")
        publisher = self.publisher or AffiliatePublisher()
        results: list[dict[str, Any]] = []
        offers = self.repository.list_offers(
            (OfferStatus.APPROVED,), self.settings.review_batch_limit
        )
        for offer in offers:
            if not self.repository.publication_allowed(
                self.settings.daily_limit,
                self.settings.min_send_interval_seconds,
                self.settings.timezone_name,
            ):
                break
            if self.repository.already_sent_recently(
                offer["marketplace"], offer["product_id"], self.settings.dedupe_days
            ):
                self.repository.set_status(
                    offer["id"], OfferStatus.REJECTED, "Product sent recently"
                )
                continue
            text = format_offer(
                offer["source_text"], offer["original_url"], offer["affiliate_url"]
            )
            response = publisher.send(self.settings.destination_group_jid, text)
            message_id = self._response_message_id(response)
            self.repository.record_publication(
                offer["id"],
                self.settings.destination_group_jid,
                message_id,
                response,
            )
            results.append({"id": offer["id"], "status": "SENT"})
        return results

    @staticmethod
    def _response_message_id(response: dict[str, Any]) -> str | None:
        key = response.get("key")
        return str(key.get("id")) if isinstance(key, dict) and key.get("id") else None

    @staticmethod
    def _safe_error(error: Exception) -> str:
        if isinstance(error, (PocError, MercadoLivreAutomationError, UnsafeUrlError)):
            return str(error)
        if type(error) is ValueError and re.fullmatch(
            r"Link returned HTTP [0-9]{3}|Unsupported marketplace", str(error)
        ):
            return str(error)
        return type(error).__name__
