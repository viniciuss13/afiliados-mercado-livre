"""Interface pública do client da Evolution API."""

from .client import EvolutionClient
from .exceptions import EvolutionAPIError, EvolutionConfigError, EvolutionResponseError
from .settings import EvolutionSettings

__all__ = [
    "EvolutionAPIError",
    "EvolutionClient",
    "EvolutionConfigError",
    "EvolutionResponseError",
    "EvolutionSettings",
]
