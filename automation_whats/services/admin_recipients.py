"""Utilitários para destinatários administrativos."""

import os
import re


def get_admin_recipients() -> list[str]:
    """Carrega os números que devem receber mensagens administrativas.

    A variável principal é `EVO_ADMIN_PHONES`, com números separados por
    vírgula, ponto e vírgula ou quebra de linha. `EVO_PHONE_LOGGER` continua
    funcionando como fallback para compatibilidade.

    Returns:
        Lista de números normalizados apenas com dígitos.
    """
    raw_value = os.getenv("EVO_ADMIN_PHONES") or os.getenv("EVO_PHONE_LOGGER", "")
    recipients: list[str] = []

    for item in re.split(r"[,;\n]+", raw_value):
        number = re.sub(r"\D", "", item)
        if number and number not in recipients:
            recipients.append(number)

    return recipients
