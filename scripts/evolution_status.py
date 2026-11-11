"""Diagnostico sanitizado da Evolution API, sem exibir chaves ou tokens."""

import argparse
import json
import sys
from typing import Any

from automation_whats.affiliate.settings import AffiliateSettings
from automation_whats.clients.evolution import EvolutionClient
from scripts.affiliate_list_groups import compact_groups


def _connection_state(payload: Any) -> str:
    if not isinstance(payload, dict):
        return "unknown"
    instance = payload.get("instance")
    if isinstance(instance, dict):
        return str(
            instance.get("state") or instance.get("connectionStatus") or "unknown"
        )
    return str(payload.get("state") or "unknown")


def _safe_webhook(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"configured": False}
    webhook = (
        payload.get("webhook")
        if isinstance(payload.get("webhook"), dict)
        else payload
    )
    return {
        "configured": bool(webhook.get("url")),
        "enabled": bool(webhook.get("enabled", True)),
        "url": str(webhook.get("url") or ""),
        "events": [str(item) for item in webhook.get("events", [])]
        if isinstance(webhook.get("events"), list)
        else [],
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", default="")
    args = parser.parse_args()
    settings = AffiliateSettings.from_env()
    client = EvolutionClient()
    result = {
        "connection_state": _connection_state(client.connection_state()),
        "webhook": _safe_webhook(client.find_webhook()),
        "groups": compact_groups(client.fetch_groups(False), args.filter),
        "affiliate": {
            "enabled": settings.enabled,
            "groups_configured": settings.groups_configured,
            "auto_publish": settings.auto_publish,
            "shopee_enabled": settings.shopee_enabled,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
