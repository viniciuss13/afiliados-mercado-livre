"""Abre um teste assistido de conversao de link do Mercado Livre."""

import argparse
import json

from automation_whats.affiliate.marketplaces.mercado_livre_playwright import (
    MercadoLivrePlaywrightConverter,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="URL do produto de origem")
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Tempo para login e copia do link, em segundos",
    )
    args = parser.parse_args()

    result = MercadoLivrePlaywrightConverter(
        timeout_seconds=args.timeout,
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
