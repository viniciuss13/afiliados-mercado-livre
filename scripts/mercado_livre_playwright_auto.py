"""Executa uma conversao automatica isolada do Mercado Livre."""

import argparse
import json

from automation_whats.affiliate.marketplaces.mercado_livre_playwright import (
    MercadoLivreAutomaticConverter,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="URL recebida no grupo")
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Mostra o navegador durante a homologacao",
    )
    args = parser.parse_args()
    result = MercadoLivreAutomaticConverter(
        headless=not args.visible,
        timeout_seconds=300 if args.visible else 90,
    ).convert(args.url)
    print(
        json.dumps(
            {
                "status": "VALIDATED",
                "marketplace": "mercado_livre",
                "product_id": result.source_product_id,
                "affiliate_url": result.affiliate_url,
                "same_product": True,
                "published": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
