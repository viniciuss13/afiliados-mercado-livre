"""Configuracoes do client do Google Sheets."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, ValidationError


class GoogleSheetsSettingsError(Exception):
    """Erro de configuracao do Google Sheets."""


class GoogleSheetsSettings(BaseModel):
    """Configuracoes necessarias para ler uma planilha do Google Sheets.

    Attributes:
        auth_mode: Modo de autenticacao: `oauth` para local ou
            `service_account` para servidor/VPS.
        oauth_client_secret_file: Caminho do JSON OAuth baixado no Google
            Developers Console.
        oauth_token_file: Caminho onde o token local autorizado sera salvo.
        service_account_file: Caminho do JSON da service account.
        spreadsheet_id: ID da planilha. Quando informado, tem prioridade.
        spreadsheet_name: Nome da planilha no Google Drive.
        worksheet_name: Nome da aba dentro da planilha.
        former_worksheet_name: Nome da aba de antigos mantenedores.
        read_range: Intervalo lido na aba.
    """

    model_config = ConfigDict(frozen=True)

    auth_mode: str = "oauth"
    oauth_client_secret_file: str | None = None
    oauth_token_file: str = "credentials/google-oauth-token.json"
    service_account_file: str | None = None
    spreadsheet_id: str | None = None
    spreadsheet_name: str | None = None
    worksheet_name: str = "mantenedores"
    former_worksheet_name: str = "antigos_mantenedores"
    read_range: str = "A:Z"

    @classmethod
    def from_env(cls) -> "GoogleSheetsSettings":
        """Cria configuracoes a partir das variaveis de ambiente.

        Returns:
            Instancia validada de `GoogleSheetsSettings`.

        Raises:
            GoogleSheetsSettingsError: Quando a configuracao esta invalida.
        """
        load_dotenv()

        try:
            settings = cls(
                auth_mode=os.getenv("GOOGLE_AUTH_MODE", "oauth"),
                oauth_client_secret_file=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_FILE")
                or None,
                oauth_token_file=os.getenv(
                    "GOOGLE_OAUTH_TOKEN_FILE",
                    "credentials/google-oauth-token.json",
                ),
                service_account_file=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
                or None,
                spreadsheet_id=os.getenv("GOOGLE_SPREADSHEET_ID") or None,
                spreadsheet_name=os.getenv("GOOGLE_SPREADSHEET_NAME") or None,
                worksheet_name=os.getenv("GOOGLE_WORKSHEET_NAME", "mantenedores"),
                former_worksheet_name=os.getenv(
                    "GOOGLE_FORMER_WORKSHEET_NAME",
                    "antigos_mantenedores",
                ),
                read_range=os.getenv("GOOGLE_SHEETS_RANGE", "A:Z"),
            )
        except ValidationError as error:
            raise GoogleSheetsSettingsError(
                f"Invalid Google Sheets configuration: {error}"
            ) from error

        if settings.auth_mode not in {"oauth", "service_account"}:
            raise GoogleSheetsSettingsError(
                "GOOGLE_AUTH_MODE must be 'oauth' or 'service_account'"
            )

        if settings.auth_mode == "oauth" and not settings.oauth_client_secret_file:
            raise GoogleSheetsSettingsError("Set GOOGLE_OAUTH_CLIENT_SECRET_FILE")

        if settings.auth_mode == "service_account" and not settings.service_account_file:
            raise GoogleSheetsSettingsError("Set GOOGLE_SERVICE_ACCOUNT_FILE")

        if not settings.spreadsheet_id and not settings.spreadsheet_name:
            raise GoogleSheetsSettingsError(
                "Set GOOGLE_SPREADSHEET_ID or GOOGLE_SPREADSHEET_NAME"
            )

        return settings
