"""Script manual para testar envio de texto pela Evolution API."""

import os

from automation_whats.clients.evolution import EvolutionClient


def main() -> None:
    """Envia uma mensagem de texto de teste.

    O número de destino é lido de `EVO_TEST_PHONE` ou, como fallback, de
    `EVO_PHONE_LOGGER`.

    Raises:
        RuntimeError: Quando nenhum número de teste está configurado.
    """
    client = EvolutionClient()
    number = os.getenv("EVO_TEST_PHONE") or os.getenv("EVO_PHONE_LOGGER")

    if not number:
        raise RuntimeError("EVO_TEST_PHONE or EVO_PHONE_LOGGER is required")

    response = client.send_text(
        number=number,
        text="Ola PycodeBR!",
    )

    print(response)


if __name__ == "__main__":
    main()
