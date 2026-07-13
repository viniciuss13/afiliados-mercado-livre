"""Client HTTP para comunicacao com a Evolution API."""

from typing import Any

import requests

from .exceptions import EvolutionAPIError, EvolutionResponseError
from .schemas import (
    MediaMessageRequest,
    MediaType,
    TextMessageRequest,
    WebhookConfigRequest,
)
from .settings import EvolutionSettings


class EvolutionClient:
    """Client de baixo nivel para endpoints da Evolution API."""

    def __init__(
        self,
        settings: EvolutionSettings | None = None,
        session: requests.Session | None = None,
    ) -> None:
        """Inicializa o client da Evolution API.

        Args:
            settings: Configuracoes explicitas do client. Quando ausente, serao
                carregadas do ambiente.
            session: Sessao HTTP injetavel. Util para testes e reutilizacao de
                conexoes.
        """
        self._settings = settings or EvolutionSettings.from_env()
        self._session = session or requests.Session()

    def send_text(
        self,
        number: str,
        text: str,
        delay: int | None = None,
        link_preview: bool | None = None,
    ) -> dict[str, Any]:
        """Envia uma mensagem de texto pela Evolution API.

        Args:
            number: Numero de destino com codigo do pais.
            text: Texto que sera enviado.
            delay: Tempo de presenca, em milissegundos, antes do envio.
            link_preview: Indica se links no texto devem gerar preview.

        Returns:
            Resposta JSON retornada pela Evolution API.
        """
        request = TextMessageRequest(
            number=number,
            text=text,
            delay=delay,
            link_preview=link_preview,
        )

        return self._post(
            path=f"/message/sendText/{self._settings.instance_name}",
            payload=request.to_payload(),
        )

    def send_media(
        self,
        number: str,
        media: str,
        media_type: MediaType,
        mime_type: str,
        caption: str,
        file_name: str,
        delay: int | None = None,
    ) -> dict[str, Any]:
        """Envia uma midia pela Evolution API.

        Args:
            number: Numero de destino com codigo do pais.
            media: URL ou conteudo base64 da midia.
            media_type: Tipo da midia.
            mime_type: MIME type do arquivo.
            caption: Legenda da midia.
            file_name: Nome do arquivo enviado.
            delay: Tempo de presenca, em milissegundos, antes do envio.

        Returns:
            Resposta JSON retornada pela Evolution API.
        """
        request = MediaMessageRequest(
            number=number,
            media=media,
            media_type=media_type,
            mime_type=mime_type,
            caption=caption,
            file_name=file_name,
            delay=delay,
        )

        return self._post(
            path=f"/message/sendMedia/{self._settings.instance_name}",
            payload=request.to_payload(),
        )

    def send_message(self, number: str, text: str) -> dict[str, Any]:
        """Envia uma mensagem de texto usando o nome legado do metodo.

        Args:
            number: Numero de destino com codigo do pais.
            text: Texto que sera enviado.

        Returns:
            Resposta JSON retornada pela Evolution API.
        """
        return self.send_text(number=number, text=text)

    def find_webhook(self) -> dict[str, Any] | None:
        """Consulta a configuracao de webhook da instancia.

        Returns:
            Configuracao atual do webhook ou `None` quando nao houver webhook.
        """
        return self._get(path=f"/webhook/find/{self._settings.instance_name}")

    def set_webhook(
        self,
        url: str,
        events: list[str] | None = None,
        enabled: bool = True,
        webhook_by_events: bool = False,
        webhook_base64: bool = False,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Configura o webhook da instancia na Evolution API.

        Args:
            url: URL que recebera os eventos enviados pela Evolution API.
            events: Lista de eventos habilitados no webhook.
            enabled: Indica se o webhook deve ficar ativo.
            webhook_by_events: Indica se a API deve separar chamadas por evento.
            webhook_base64: Indica se midias devem ser enviadas em base64.
            headers: Headers adicionais enviados pela Evolution API ao webhook.

        Returns:
            Configuracao retornada pela Evolution API.
        """
        request = WebhookConfigRequest(
            enabled=enabled,
            url=url,
            events=events or ["MESSAGES_UPSERT"],
            webhook_by_events=webhook_by_events,
            webhook_base64=webhook_base64,
            headers=headers,
        )

        return self._post(
            path=f"/webhook/set/{self._settings.instance_name}",
            payload=request.to_body(),
        )

    def _get(self, path: str) -> dict[str, Any] | None:
        """Executa uma requisicao GET para a Evolution API.

        Args:
            path: Caminho relativo do endpoint.

        Returns:
            Resposta JSON retornada pela Evolution API.
        """
        return self._request(method="GET", path=path)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Executa uma requisicao POST para a Evolution API.

        Args:
            path: Caminho relativo do endpoint.
            payload: Corpo JSON da requisicao.

        Returns:
            Resposta JSON retornada pela Evolution API.
        """
        return self._request(method="POST", path=path, payload=payload)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Executa uma requisicao HTTP e normaliza erros de infraestrutura.

        Args:
            method: Metodo HTTP.
            path: Caminho relativo do endpoint.
            payload: Corpo JSON da requisicao, quando houver.

        Returns:
            Resposta JSON retornada pela Evolution API.

        Raises:
            EvolutionAPIError: Quando a requisicao falha antes de receber uma
                resposta HTTP.
            EvolutionResponseError: Quando a resposta tem status de erro ou
                payload JSON invalido.
        """
        url = f"{self._settings.base_url}{path}"

        try:
            request_kwargs: dict[str, Any] = {
                "method": method,
                "url": url,
                "headers": self._headers,
                "timeout": self._settings.timeout,
            }
            if payload is not None:
                request_kwargs["json"] = payload

            response = self._session.request(**request_kwargs)
        except requests.RequestException as error:
            raise EvolutionAPIError(f"Evolution API request failed: {error}") from error

        if response.status_code >= 400:
            raise EvolutionResponseError(
                f"Evolution API returned HTTP {response.status_code}: {response.text}"
            )

        try:
            return response.json()
        except ValueError as error:
            raise EvolutionResponseError("Evolution API returned invalid JSON") from error

    @property
    def _headers(self) -> dict[str, str]:
        """Headers padrao usados nas requisicoes para a Evolution API.

        Returns:
            Headers HTTP com `apikey` e `Content-Type`.
        """
        headers = {
            "apikey": self._settings.api_key,
            "Content-Type": "application/json",
        }
        if self._settings.request_origin:
            headers["Origin"] = self._settings.request_origin

        return headers
