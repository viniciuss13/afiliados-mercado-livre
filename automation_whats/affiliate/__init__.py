"""Automacao de ofertas de afiliados recebidas pelo WhatsApp."""

from .repository import AffiliateRepository
from .settings import AffiliateSettings
from .worker import AffiliateWorker

__all__ = ["AffiliateRepository", "AffiliateSettings", "AffiliateWorker"]
