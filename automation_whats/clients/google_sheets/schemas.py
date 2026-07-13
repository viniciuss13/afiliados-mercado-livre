"""Schemas dos dados lidos da planilha de mantenedores."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_phone(value: str) -> str:
    """Valida telefone lido da planilha."""
    digits = re.sub(r"\D", "", value)
    if not 10 <= len(digits) <= 15:
        raise ValueError("telefone deve conter entre 10 e 15 digitos")

    return value


class MantenedorSheetRow(BaseModel):
    """Linha de mantenedor lida do Google Sheets.

    Attributes:
        nome: Nome da pessoa cadastrada.
        telefone: Telefone/WhatsApp da pessoa cadastrada.
        valor: Valor informado na planilha.
    """

    model_config = ConfigDict(extra="ignore")

    nome: str = Field(min_length=1)
    telefone: str = Field(min_length=1)
    valor: str = Field(min_length=1)

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, value: str) -> str:
        """Valida telefone da linha ativa."""
        return _validate_phone(value)


class FormerMantenedorSheetRow(BaseModel):
    """Linha de antigo mantenedor lida do Google Sheets.

    Attributes:
        nome: Nome da pessoa que ja foi mantenedora.
        telefone: Telefone/WhatsApp da pessoa que ja foi mantenedora.
    """

    model_config = ConfigDict(extra="ignore")

    nome: str = Field(min_length=1)
    telefone: str = Field(min_length=1)

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, value: str) -> str:
        """Valida telefone da linha de antigo mantenedor."""
        return _validate_phone(value)
