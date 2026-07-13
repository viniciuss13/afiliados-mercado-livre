"""Aplicacao FastAPI para receber webhooks."""

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status

from .handlers import EvolutionWebhookHandler, GoogleFormMantenedorWebhookHandler
from .schemas import GoogleFormMantenedorPayload


def create_app(
    evolution_handler: EvolutionWebhookHandler | None = None,
    google_form_handler: GoogleFormMantenedorWebhookHandler | None = None,
) -> FastAPI:
    """Cria a aplicacao FastAPI de webhooks.

    Args:
        evolution_handler: Handler para eventos enviados pela Evolution API.
        google_form_handler: Handler para cadastros vindos do Google Forms.

    Returns:
        Aplicacao FastAPI configurada.
    """
    app = FastAPI(
        title="Automation Whats Webhooks",
        version="1.0.0",
    )

    evolution_event_handler = evolution_handler or EvolutionWebhookHandler()
    mantenedor_handler = google_form_handler or GoogleFormMantenedorWebhookHandler()

    @app.get("/health")
    def health() -> dict[str, str]:
        """Retorna o status do servidor.

        Returns:
            Dicionario com status `ok`.
        """
        return {"status": "ok"}

    @app.post("/webhooks/evolution")
    async def receive_evolution_webhook(
        request: Request,
        payload: dict[str, Any],
    ) -> dict[str, str]:
        """Recebe eventos enviados pela Evolution API.

        Args:
            request: Requisicao HTTP recebida.
            payload: Corpo JSON enviado pela Evolution API.

        Returns:
            Resultado do processamento do evento.
        """
        _validate_webhook_secret(request)
        return evolution_event_handler.handle(payload)

    @app.post("/webhooks/google-form/mantenedor")
    async def receive_google_form_mantenedor(
        request: Request,
        payload: GoogleFormMantenedorPayload,
    ) -> dict[str, str]:
        """Recebe cadastro de mantenedor vindo do Google Forms.

        Args:
            request: Requisicao HTTP recebida.
            payload: Dados validados do cadastro.

        Returns:
            Resultado do processamento do cadastro.
        """
        _validate_webhook_secret(request)
        return mantenedor_handler.handle(payload.model_dump())

    return app


def _validate_webhook_secret(request: Request) -> None:
    """Valida o segredo opcional do webhook.

    Args:
        request: Requisicao HTTP recebida.

    Raises:
        HTTPException: Quando `WEBHOOK_SECRET` esta configurado e o header
            recebido nao corresponde ao valor esperado.
    """
    expected_secret = os.getenv("WEBHOOK_SECRET")
    if not expected_secret:
        return

    header_name = os.getenv("WEBHOOK_SECRET_HEADER", "X-Webhook-Secret")
    received_secret = request.headers.get(header_name)
    if received_secret != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


app = create_app()
