"""Publicacao validada no grupo de destino."""

from typing import Any

from automation_whats.clients.evolution import EvolutionClient


class AffiliatePublisher:
    """Envia uma oferta pelo client existente da Evolution API."""

    def __init__(self, client: EvolutionClient | None = None) -> None:
        self._client = client or EvolutionClient()

    def send(self, destination_jid: str, text: str) -> dict[str, Any]:
        if not destination_jid.endswith("@g.us"):
            raise ValueError("Destination must be a WhatsApp group JID")
        return self._client.send_text(
            number=destination_jid,
            text=text,
            link_preview=True,
        )

