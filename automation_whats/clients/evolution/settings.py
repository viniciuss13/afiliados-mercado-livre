"""Configuracoes do client da Evolution API."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .exceptions import EvolutionConfigError


class EvolutionSettings(BaseModel):
    """Configuracoes necessarias para chamar a Evolution API.

    Attributes:
        base_url: URL base da Evolution API.
        instance_name: Nome da instancia configurada na Evolution API.
        api_key: Chave usada no header `apikey`.
        timeout: Tempo maximo, em segundos, para uma requisicao HTTP.
        request_origin: Valor opcional do header `Origin` para ambientes onde a
            Evolution API valida CORS em chamadas server to server.
    """

    model_config = ConfigDict(frozen=True)

    base_url: str = Field(min_length=1)
    instance_name: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    timeout: float = Field(default=30.0, gt=0)
    request_origin: str | None = None

    @field_validator("base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        """Remove a barra final da URL base.

        Args:
            value: URL base informada.

        Returns:
            URL base sem barra final.
        """
        return value.rstrip("/")

    @classmethod
    def from_env(cls) -> "EvolutionSettings":
        """Cria as configuracoes a partir das variaveis de ambiente.

        Returns:
            Instancia validada de `EvolutionSettings`.

        Raises:
            EvolutionConfigError: Quando alguma variavel obrigatoria esta
                ausente ou invalida.
        """
        load_dotenv()

        try:
            return cls(
                base_url=os.getenv("EVO_BASE_URL"),
                instance_name=os.getenv("EVO_INSTANCE_NAME"),
                api_key=os.getenv("AUTHENTICATION_API_KEY"),
                timeout=os.getenv("EVO_TIMEOUT", "30"),
                request_origin=os.getenv("EVO_REQUEST_ORIGIN"),
            )
        except ValidationError as error:
            raise EvolutionConfigError(
                f"Invalid Evolution API configuration: {error}"
            ) from error
