"""Script manual para testar envio de mídia pela Evolution API."""

import os

from automation_whats.clients.evolution import EvolutionClient


def main() -> None:
    """Envia uma imagem de teste.

    O número de destino é lido de `EVO_TEST_MEDIA_PHONE`, `EVO_TEST_PHONE` ou,
    como fallback, de `EVO_PHONE_LOGGER`.

    Raises:
        RuntimeError: Quando nenhum número de teste está configurado.
    """
    client = EvolutionClient()
    number = (
        os.getenv("EVO_TEST_MEDIA_PHONE")
        or os.getenv("EVO_TEST_PHONE")
        or os.getenv("EVO_PHONE_LOGGER")
    )

    if not number:
        raise RuntimeError(
            "EVO_TEST_MEDIA_PHONE, EVO_TEST_PHONE or EVO_PHONE_LOGGER is required"
        )

    response = client.send_media(
        number=number,
        media="https://images.icon-icons.com/2699/PNG/512/python_logo_icon_168886.png",
        media_type="image",
        mime_type="image/png",
        caption="Teste controlado da automacao de afiliados",
        file_name="affiliate-test.png",
    )

    print(response)


if __name__ == "__main__":
    main()
