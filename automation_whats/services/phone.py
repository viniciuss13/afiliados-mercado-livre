"""Utilitarios para normalizacao de telefones."""

import re


def normalize_brazilian_phone(phone: str) -> str:
    """Normaliza telefone brasileiro para envio via WhatsApp.

    Args:
        phone: Telefone informado em formulario ou planilha.

    Returns:
        Telefone apenas com digitos e DDI 55 quando vier apenas com DDD.
    """
    digits = re.sub(r"\D", "", phone)
    if len(digits) in (10, 11) and not digits.startswith("55"):
        return f"55{digits}"

    return digits
