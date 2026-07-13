"""Client para buscar mantenedores em uma planilha Google."""

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .schemas import FormerMantenedorSheetRow, MantenedorSheetRow
from .settings import GoogleSheetsSettings


class GoogleSheetsClient:
    """Le dados de mantenedores de uma planilha Google."""

    scopes = (
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    )

    def __init__(self, settings: GoogleSheetsSettings | None = None) -> None:
        """Inicializa o client.

        Args:
            settings: Configuracoes explicitas do Google Sheets. Quando ausente,
                serao carregadas do ambiente.
        """
        self._settings = settings or GoogleSheetsSettings.from_env()

    def fetch_mantenedores(self) -> list[MantenedorSheetRow]:
        """Busca mantenedores na planilha configurada.

        Returns:
            Lista de linhas validada com nome, telefone e valor.
        """
        spreadsheet_id = self._settings.spreadsheet_id or self._find_spreadsheet_id()
        values = self._get_values(
            spreadsheet_id=spreadsheet_id,
            worksheet_name=self._settings.worksheet_name,
        )

        if not values:
            return []

        headers = [self._normalize_header(header) for header in values[0]]
        mantenedores: list[MantenedorSheetRow] = []
        for row in values[1:]:
            raw = self._row_to_dict(headers=headers, row=row)
            if not any(raw.values()):
                continue
            try:
                mantenedores.append(MantenedorSheetRow.model_validate(raw))
            except ValidationError:
                continue

        return mantenedores

    def fetch_former_mantenedores(self) -> list[FormerMantenedorSheetRow]:
        """Busca antigos mantenedores na aba configurada.

        Returns:
            Lista de linhas validada com nome e telefone.
        """
        spreadsheet_id = self._settings.spreadsheet_id or self._find_spreadsheet_id()
        values = self._get_values(
            spreadsheet_id=spreadsheet_id,
            worksheet_name=self._settings.former_worksheet_name,
        )

        if not values:
            return []

        headers = [self._normalize_header(header) for header in values[0]]
        mantenedores: list[FormerMantenedorSheetRow] = []
        for row in values[1:]:
            raw = self._row_to_dict(headers=headers, row=row)
            if not any(raw.values()):
                continue
            try:
                mantenedores.append(FormerMantenedorSheetRow.model_validate(raw))
            except ValidationError:
                continue

        return mantenedores

    def find_mantenedor_by_phone(self, telefone: str) -> MantenedorSheetRow | None:
        """Busca um mantenedor ja cadastrado pelo telefone.

        Args:
            telefone: Telefone recebido na resposta do WhatsApp.

        Returns:
            Linha encontrada ou `None`.
        """
        normalized_phone = self._only_digits(telefone)
        for mantenedor in self.fetch_mantenedores():
            if self._only_digits(mantenedor.telefone) == normalized_phone:
                return mantenedor

        return None

    def find_former_mantenedor_by_phone(
        self,
        telefone: str,
    ) -> FormerMantenedorSheetRow | None:
        """Busca um antigo mantenedor pelo telefone.

        Args:
            telefone: Telefone recebido na resposta do WhatsApp.

        Returns:
            Linha encontrada na aba de antigos mantenedores ou `None`.
        """
        normalized_phone = self._only_digits(telefone)
        for mantenedor in self.fetch_former_mantenedores():
            if self._only_digits(mantenedor.telefone) == normalized_phone:
                return mantenedor

        return None

    def append_mantenedor(self, nome: str, telefone: str, valor: str) -> dict[str, Any]:
        """Insere um mantenedor na aba principal da planilha.

        Args:
            nome: Nome da pessoa mantenedora.
            telefone: Telefone/WhatsApp da pessoa mantenedora.
            valor: Valor informado na resposta.

        Returns:
            Resposta retornada pela API do Google Sheets.
        """
        spreadsheet_id = self._settings.spreadsheet_id or self._find_spreadsheet_id()
        sheets_service = self._build_service("sheets", "v4")
        write_range = f"'{self._settings.worksheet_name}'!A:C"
        body = {"values": [[nome, telefone, valor]]}
        return (
            sheets_service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=write_range,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )

    def _find_spreadsheet_id(self) -> str:
        """Busca o ID da planilha pelo nome no Google Drive.

        Returns:
            ID da planilha encontrada.

        Raises:
            ValueError: Quando nenhuma planilha com o nome configurado e
                encontrada.
        """
        drive_service = self._build_service("drive", "v3")
        query = (
            "mimeType='application/vnd.google-apps.spreadsheet' "
            f"and name='{self._settings.spreadsheet_name}' "
            "and trashed=false"
        )
        response = (
            drive_service.files()
            .list(q=query, fields="files(id,name)", pageSize=1)
            .execute()
        )
        files = response.get("files", [])
        if not files:
            raise ValueError(
                f"Spreadsheet not found: {self._settings.spreadsheet_name}"
            )

        return files[0]["id"]

    def _get_values(self, spreadsheet_id: str, worksheet_name: str) -> list[list[Any]]:
        """Le os valores da aba configurada.

        Args:
            spreadsheet_id: ID da planilha.
            worksheet_name: Nome da aba lida.

        Returns:
            Matriz de valores retornada pelo Google Sheets.
        """
        sheets_service = self._build_service("sheets", "v4")
        read_range = f"'{worksheet_name}'!{self._settings.read_range}"
        response = (
            sheets_service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=read_range)
            .execute()
        )
        return response.get("values", [])

    def _build_service(self, service_name: str, version: str) -> Any:
        """Cria um service da API Google.

        Args:
            service_name: Nome da API Google.
            version: Versao da API.

        Returns:
            Service construido pelo `googleapiclient`.
        """
        from googleapiclient.discovery import build

        return build(service_name, version, credentials=self._build_credentials())

    def _build_credentials(self) -> Any:
        """Cria credenciais Google conforme o modo configurado.

        Returns:
            Credenciais OAuth local ou service account.
        """
        if self._settings.auth_mode == "service_account":
            from google.oauth2.service_account import Credentials

            return Credentials.from_service_account_file(
                self._settings.service_account_file,
                scopes=self.scopes,
            )

        return self._build_oauth_credentials()

    def _build_oauth_credentials(self) -> Any:
        """Cria credenciais OAuth locais e salva o token autorizado.

        Returns:
            Credenciais OAuth validas para as APIs Google.
        """
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        token_path = Path(self._settings.oauth_token_file)
        credentials = None

        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(token_path),
                scopes=self.scopes,
            )

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                self._settings.oauth_client_secret_file,
                scopes=self.scopes,
            )
            credentials = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

    def _row_to_dict(self, headers: list[str], row: list[Any]) -> dict[str, str]:
        """Converte uma linha de celulas em dicionario.

        Args:
            headers: Cabecalhos normalizados.
            row: Valores da linha.

        Returns:
            Dicionario com chaves normalizadas.
        """
        padded_row = row + [""] * (len(headers) - len(row))
        return {
            header: str(value).strip()
            for header, value in zip(headers, padded_row)
            if header
        }

    def _normalize_header(self, value: Any) -> str:
        """Normaliza cabecalhos aceitos na planilha.

        Args:
            value: Nome da coluna.

        Returns:
            Nome normalizado para o schema interno.
        """
        normalized = str(value).strip().lower()
        aliases = {
            "nome completo": "nome",
            "numero": "telefone",
            "número": "telefone",
            "whatsapp": "telefone",
            "celular": "telefone",
            "phone": "telefone",
            "valor mensal": "valor",
            "contribuicao": "valor",
            "contribuição": "valor",
        }
        return aliases.get(normalized, normalized)

    def _only_digits(self, value: str) -> str:
        """Remove caracteres nao numericos de um telefone."""
        return "".join(char for char in value if char.isdigit())
