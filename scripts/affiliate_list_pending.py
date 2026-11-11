"""Exporta um lote compacto para revisao humana ou por agente."""

import json

from automation_whats.affiliate.models import OfferStatus
from automation_whats.affiliate.repository import AffiliateRepository
from automation_whats.affiliate.settings import AffiliateSettings


def main() -> None:
    settings = AffiliateSettings.from_env()
    repository = AffiliateRepository(settings.db_path)
    rows = repository.list_offers(
        (OfferStatus.NEEDS_CONVERSION, OfferStatus.NEEDS_REVIEW),
        settings.review_batch_limit,
    )
    if not rows:
        print("EMPTY")
        return
    output = [
        {
            "id": row["id"],
            "marketplace": row["marketplace"],
            "product_id": row["product_id"],
            "source_text": row["source_text"],
            "resolved_url": row["resolved_url"],
            "affiliate_url": row["affiliate_url"],
            "status": row["status"],
            "alert": row["last_error"],
        }
        for row in rows
    ]
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
