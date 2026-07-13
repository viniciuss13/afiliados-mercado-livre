"""Schemas Pydantic dos payloads enviados para a Evolution API."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class EvolutionSchema(BaseModel):
    """Classe base para schemas enviados a Evolution API."""

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    def to_payload(self) -> dict[str, Any]:
        """Converte o schema para payload JSON da Evolution API.

        Returns:
            Dicionario com aliases da API e sem campos `None`.
        """
        return self.model_dump(by_alias=True, exclude_none=True)


class TextMessageRequest(EvolutionSchema):
    """Payload para envio de mensagem de texto.

    Attributes:
        number: Numero de destino com codigo do pais.
        text: Texto que sera enviado.
        delay: Tempo de presenca, em milissegundos, antes do envio.
        link_preview: Indica se links devem gerar preview.
        mentions_everyone: Indica se todos devem ser mencionados.
        mentioned: Lista de numeros ou identificadores mencionados.
        quoted: Estrutura de mensagem citada, quando houver resposta.
    """

    number: str = Field(min_length=1)
    text: str = Field(min_length=1)
    delay: int | None = Field(default=None, ge=0)
    link_preview: bool | None = Field(default=None, alias="linkPreview")
    mentions_everyone: bool | None = Field(default=None, alias="mentionsEveryOne")
    mentioned: list[str] | None = None
    quoted: dict[str, Any] | None = None


MediaType = Literal["image", "video", "document", "audio"]
"""Tipos de midia aceitos pelo endpoint `sendMedia` da Evolution API."""


class MediaMessageRequest(EvolutionSchema):
    """Payload para envio de midia.

    Attributes:
        number: Numero de destino com codigo do pais.
        media: URL ou conteudo base64 da midia.
        media_type: Tipo da midia enviada.
        mime_type: MIME type do arquivo.
        caption: Legenda da midia.
        file_name: Nome do arquivo enviado.
        delay: Tempo de presenca, em milissegundos, antes do envio.
        link_preview: Indica se links devem gerar preview.
        mentions_everyone: Indica se todos devem ser mencionados.
        mentioned: Lista de numeros ou identificadores mencionados.
        quoted: Estrutura de mensagem citada, quando houver resposta.
    """

    number: str = Field(min_length=1)
    media: str = Field(min_length=1)
    media_type: MediaType = Field(alias="mediatype")
    mime_type: str = Field(min_length=1, alias="mimetype")
    caption: str = Field(min_length=1)
    file_name: str = Field(min_length=1, alias="fileName")
    delay: int | None = Field(default=None, ge=0)
    link_preview: bool | None = Field(default=None, alias="linkPreview")
    mentions_everyone: bool | None = Field(default=None, alias="mentionsEveryOne")
    mentioned: list[str] | None = None
    quoted: dict[str, Any] | None = None


class WebhookConfigRequest(EvolutionSchema):
    """Payload para configurar webhook da instancia.

    Attributes:
        enabled: Indica se o webhook fica ativo.
        url: URL publica que recebera os eventos.
        events: Lista de eventos enviados para o webhook.
        webhook_by_events: Indica se a API deve separar chamadas por evento.
        webhook_base64: Indica se midias devem ser enviadas em base64.
        headers: Headers adicionais enviados pela Evolution API ao webhook.
    """

    enabled: bool = True
    url: str = Field(min_length=1)
    events: list[str] = Field(default_factory=lambda: ["MESSAGES_UPSERT"])
    webhook_by_events: bool = Field(default=False, alias="webhookByEvents")
    webhook_base64: bool = Field(default=False, alias="webhookBase64")
    headers: dict[str, str] | None = None

    def to_body(self) -> dict[str, Any]:
        """Converte o schema para o corpo esperado pelo endpoint de webhook.

        Returns:
            Dicionario com a chave raiz `webhook`.
        """
        return {"webhook": self.to_payload()}
