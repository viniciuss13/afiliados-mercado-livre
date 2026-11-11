"""Aplica decisoes JSON produzidas por revisao humana ou pelo Codex."""

import argparse
import json
from pathlib import Path

from automation_whats.affiliate.repository import AffiliateRepository
from automation_whats.affiliate.settings import AffiliateSettings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    decisions = json.loads(args.file.read_text(encoding="utf-8"))
    if not isinstance(decisions, list):
        raise ValueError("Decision file must contain a JSON list")

    settings = AffiliateSettings.from_env()
    repository = AffiliateRepository(settings.db_path)
    applied = 0
    for item in decisions:
        if not isinstance(item, dict):
            raise ValueError("Each decision must be an object")
        repository.add_review(
            offer_id=int(item["id"]),
            decision=str(item["decision"]),
            reason=str(item.get("reason", "")),
            final_text=str(item.get("final_text", "")),
        )
        applied += 1
    print(json.dumps({"applied": applied}))


if __name__ == "__main__":
    main()
