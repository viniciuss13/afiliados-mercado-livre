"""Roteamento seguro dos eventos recebidos da Evolution API."""

from typing import Any

from automation_whats.affiliate.message_parser import EvolutionMessageParser
from automation_whats.affiliate.repository import AffiliateRepository
from automation_whats.affiliate.settings import AffiliateSettings


class EvolutionWebhookHandler:
    """Filtra o grupo de origem e coloca ofertas na fila persistente."""

    def __init__(
        self,
        settings: AffiliateSettings | None = None,
        repository: AffiliateRepository | None = None,
        parser: EvolutionMessageParser | None = None,
    ) -> None:
        self._settings = settings or AffiliateSettings.from_env()
        self._repository = repository or AffiliateRepository(self._settings.db_path)
        self._parser = parser or EvolutionMessageParser()

    def handle(self, payload: dict[str, Any]) -> dict[str, str | int]:
        """Ignora outros chats e enfileira apenas ofertas da origem autorizada."""
        if not self._settings.enabled:
            return {"status": "disabled"}
        if not self._settings.groups_configured:
            return {"status": "configuration_required"}

        message = self._parser.parse(payload)
        if message is None:
            return {"status": "ignored"}
        if not message.remote_jid.endswith("@g.us"):
            return {"status": "ignored_direct_message"}
        if message.remote_jid not in self._settings.source_group_jids:
            return {"status": "ignored_group"}

        inserted, offer_count = self._repository.enqueue(message)
        if not inserted:
            return {"status": "duplicate"}
        return {"status": "queued", "offers": offer_count}
