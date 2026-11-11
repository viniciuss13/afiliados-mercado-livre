"""Aplicacao FastAPI para receber webhooks da Evolution API."""

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status

from automation_whats.affiliate.settings import AffiliateSettings

from .handlers import EvolutionWebhookHandler


def create_app(evolution_handler: EvolutionWebhookHandler | None = None) -> FastAPI:
    """Cria a aplicacao HTTP da automacao de afiliados."""
    app = FastAPI(title="Affiliate Whats Webhooks", version="2.0.0")
    event_handler = evolution_handler or EvolutionWebhookHandler()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, str | bool]:
        settings = AffiliateSettings.from_env()
        return {
            "status": (
                "ready"
                if settings.enabled and settings.groups_configured
                else "configuration_required"
            ),
            "affiliate_enabled": settings.enabled,
            "groups_configured": settings.groups_configured,
            "auto_publish": settings.auto_publish,
            "shopee_enabled": settings.shopee_enabled,
        }

    @app.post("/webhooks/evolution")
    async def receive_evolution_webhook(
        request: Request,
        payload: dict[str, Any],
    ) -> dict[str, str | int]:
        _validate_webhook_secret(request)
        return event_handler.handle(payload)

    return app


def _validate_webhook_secret(request: Request) -> None:
    expected_secret = os.getenv("WEBHOOK_SECRET")
    if not expected_secret:
        return
    header_name = os.getenv("WEBHOOK_SECRET_HEADER", "X-Webhook-Secret")
    if request.headers.get(header_name) != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


app = create_app()
