"""Schemas dos eventos recebidos por webhook."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvolutionWebhookEvent(BaseModel):
    """Evento recebido da Evolution API.

    A Evolution API pode variar o formato conforme o tipo de evento. Por isso,
    o schema permite campos extras e modela apenas os campos mais comuns.

    Attributes:
        event: Nome do evento recebido.
        instance: Nome da instancia que gerou o evento.
        data: Conteudo principal do evento.
        destination: URL de destino configurada no webhook.
        date_time: Data/hora informada pela Evolution API.
        sender: Identificador do remetente, quando informado.
        server_url: URL do servidor Evolution API, quando informada.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    event: str | None = None
    instance: str | None = None
    data: dict[str, Any] | list[Any] | None = None
    destination: str | None = None
    date_time: str | None = None
    sender: str | None = None
    server_url: str | None = None


class GoogleFormMantenedorPayload(BaseModel):
    """Payload recebido do Google Forms para cadastro de mantenedor.

    Attributes:
        nome: Nome da pessoa cadastrada.
        telefone: Telefone/WhatsApp da pessoa cadastrada.
        valor: Valor informado no formulario.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    nome: str = Field(min_length=1)
    telefone: str = Field(min_length=1)
    valor: str = Field(min_length=1)
