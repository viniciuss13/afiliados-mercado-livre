"""Valida e associa um link de afiliado gerado para uma oferta."""

import argparse
import json

from automation_whats.affiliate import AffiliateWorker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offer", type=int, required=True)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    result = AffiliateWorker().apply_affiliate_link(args.offer, args.url)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
