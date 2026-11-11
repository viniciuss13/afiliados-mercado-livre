"""Publica ofertas aprovadas mediante confirmacao explicita no comando."""

import argparse
import json

from automation_whats.affiliate import AffiliateWorker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirma que mensagens reais podem ser enviadas ao grupo configurado.",
    )
    args = parser.parse_args()
    if not args.confirm:
        raise SystemExit("Use --confirm para autorizar o envio real desta rodada")
    print(
        json.dumps(
            AffiliateWorker().publish_approved(force=True),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
