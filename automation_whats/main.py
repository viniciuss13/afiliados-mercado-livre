"""Processa uma rodada da fila de ofertas."""

import json

from automation_whats.affiliate import AffiliateWorker


def main() -> None:
    """Resolve ofertas pendentes e publica somente quando habilitado."""
    worker = AffiliateWorker()
    result = {
        "processed": worker.process_pending(),
        "published": worker.publish_approved(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
