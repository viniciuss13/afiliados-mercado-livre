"""Modelos internos da automacao de afiliados."""

from dataclasses import dataclass
from enum import StrEnum


class OfferStatus(StrEnum):
    """Estados persistidos de uma oferta."""

    RECEIVED = "RECEIVED"
    NEEDS_CONVERSION = "NEEDS_CONVERSION"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    APPROVED = "APPROVED"
    RETRY = "RETRY"
    QUARANTINED = "QUARANTINED"
    SENT = "SENT"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class IncomingMessage:
    """Mensagem normalizada recebida da Evolution API."""

    instance: str
    message_id: str
    remote_jid: str
    participant_jid: str | None
    text: str
    urls: tuple[str, ...]
    media_type: str | None = None


@dataclass(frozen=True)
class ResolvedLink:
    """Resultado da resolucao segura de um link."""

    original_url: str
    final_url: str
    redirect_chain: tuple[str, ...]


@dataclass(frozen=True)
class MarketplaceProduct:
    """Marketplace e identificador extraidos de uma URL."""

    marketplace: str
    product_id: str | None
