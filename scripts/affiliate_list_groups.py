"""Lista nomes e JIDs de grupos acessiveis pela instancia Evolution."""

import argparse
import json
import sys
from typing import Any

from automation_whats.clients.evolution import EvolutionClient


def compact_groups(payload: Any, query: str = "") -> list[dict[str, str]]:
    groups = (
        payload
        if isinstance(payload, list)
        else payload.get("data", [])
        if isinstance(payload, dict)
        else []
    )
    result: list[dict[str, str]] = []
    normalized_query = query.casefold().strip()
    for group in groups:
        if not isinstance(group, dict):
            continue
        jid = group.get("id") or group.get("remoteJid")
        name = str(group.get("subject") or group.get("name") or "")
        if jid and name and (
            not normalized_query or normalized_query in name.casefold()
        ):
            result.append({"name": name, "jid": str(jid)})
    return result


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filter",
        default="",
        help="Mostra apenas grupos cujo nome contem este texto.",
    )
    args = parser.parse_args()
    response = EvolutionClient().fetch_groups(include_participants=False)
    print(json.dumps(compact_groups(response, args.filter), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
