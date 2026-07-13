"""Utilitários para carregar mídia enviada aos mantenedores."""

import base64
import mimetypes
import os
from pathlib import Path


def get_wecare_image_media() -> dict[str, str] | None:
    """Carrega a imagem We Care configurada por URL ou arquivo local.

    Returns:
        Dicionário com `media`, `mime_type` e `file_name`, ou `None` quando
        nenhuma imagem estiver configurada.
    """
    image_url = os.getenv("WECARE_WELCOME_IMAGE_URL")
    if image_url:
        return {
            "media": image_url,
            "mime_type": os.getenv("WECARE_WELCOME_IMAGE_MIME", "image/png"),
            "file_name": os.getenv("WECARE_WELCOME_IMAGE_NAME", "we-care.png"),
        }

    image_path = os.getenv("WECARE_WELCOME_IMAGE_PATH")
    if not image_path:
        return None

    path = Path(image_path)
    if not path.is_absolute():
        path = Path.cwd() / path

    media = base64.b64encode(path.read_bytes()).decode("ascii")
    mime_type = (
        os.getenv("WECARE_WELCOME_IMAGE_MIME")
        or mimetypes.guess_type(path.name)[0]
        or "image/jpeg"
    )

    return {
        "media": media,
        "mime_type": mime_type,
        "file_name": os.getenv("WECARE_WELCOME_IMAGE_NAME", path.name),
    }
