"""Configura o webhook da Evolution API para a instancia atual."""

import os

from dotenv import load_dotenv

from automation_whats.clients.evolution import EvolutionClient


def main() -> None:
    """Configura o webhook usando variaveis de ambiente.

    Variaveis usadas:
        WEBHOOK_URL: URL publica do receptor.
        WEBHOOK_EVENTS: Eventos separados por virgula.
        WEBHOOK_SECRET: Segredo opcional enviado como header.
        WEBHOOK_SECRET_HEADER: Nome do header do segredo.
    """
    load_dotenv()

    webhook_url = os.getenv(
        "WEBHOOK_URL",
        "http://host.docker.internal:8000/webhooks/evolution",
    )
    events = [
        event.strip()
        for event in os.getenv("WEBHOOK_EVENTS", "MESSAGES_UPSERT").split(",")
        if event.strip()
    ]

    secret = os.getenv("WEBHOOK_SECRET")
    secret_header = os.getenv("WEBHOOK_SECRET_HEADER", "X-Webhook-Secret")
    headers = {secret_header: secret} if secret else None

    response = EvolutionClient().set_webhook(
        url=webhook_url,
        events=events,
        headers=headers,
    )

    print(response)


if __name__ == "__main__":
    main()
