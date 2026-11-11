"""Regras deterministicas para Mercado Livre e Shopee."""

import re
from urllib.parse import parse_qs, urlparse

from ..models import MarketplaceProduct


def identify_marketplace(url: str) -> MarketplaceProduct | None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host == "meli.la" or host.endswith("mercadolivre.com.br"):
        return MarketplaceProduct("mercado_livre", _mercado_livre_id(url))
    if host == "s.shopee.com.br" or host.endswith("shopee.com.br"):
        return MarketplaceProduct("shopee", _shopee_id(parsed.path))
    return None


def validate_same_product(source_url: str, affiliate_url: str) -> MarketplaceProduct:
    source = identify_marketplace(source_url)
    affiliate = identify_marketplace(affiliate_url)
    if source is None or affiliate is None:
        raise ValueError("Unsupported marketplace")
    if source.marketplace != affiliate.marketplace:
        raise ValueError("Affiliate link changed marketplace")
    if not source.product_id or not affiliate.product_id:
        raise ValueError("Product identity could not be verified")
    if source.product_id != affiliate.product_id:
        raise ValueError("Affiliate link points to a different product")
    return affiliate


def _mercado_livre_id(url: str) -> str | None:
    match = re.search(r"\bMLB-?(\d+)\b", url, re.IGNORECASE)
    if match:
        return f"MLB{match.group(1)}"
    query = parse_qs(urlparse(url).query)
    for key in ("item_id", "itemId"):
        if query.get(key):
            value = query[key][0]
            match = re.search(r"MLB-?(\d+)", value, re.IGNORECASE)
            if match:
                return f"MLB{match.group(1)}"
    return None


def _shopee_id(path: str) -> str | None:
    match = re.search(r"/product/(\d+)/(\d+)", path)
    if not match:
        match = re.search(r"-i\.(\d+)\.(\d+)", path)
    return f"{match.group(1)}:{match.group(2)}" if match else None
