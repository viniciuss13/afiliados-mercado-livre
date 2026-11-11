"""Formatacao conservadora de ofertas para o WhatsApp."""

import re


URL_PATTERN = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)


def format_offer(source_text: str, original_url: str, affiliate_url: str) -> str:
    """Preserva o texto recebido e deixa somente o link validado."""
    del original_url
    found = False

    def replace_url(match: re.Match[str]) -> str:
        nonlocal found
        if found:
            return ""
        found = True
        return affiliate_url

    formatted = URL_PATTERN.sub(replace_url, source_text).strip()
    if found:
        return formatted
    return f"{formatted}\n\nCompre aqui: {affiliate_url}"
