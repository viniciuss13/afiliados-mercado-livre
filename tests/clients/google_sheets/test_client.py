"""Testes unitarios do client Google Sheets."""

import unittest
from unittest.mock import Mock

from automation_whats.clients.google_sheets.client import GoogleSheetsClient
from automation_whats.clients.google_sheets.settings import GoogleSheetsSettings


class GoogleSheetsClientTest(unittest.TestCase):
    """Testa leitura e escrita de mantenedores no Google Sheets."""

    def setUp(self) -> None:
        """Prepara o client com configuracao falsa."""
        self.settings = GoogleSheetsSettings(
            auth_mode="oauth",
            oauth_client_secret_file="credentials/client.json",
            spreadsheet_id="sheet-id",
            worksheet_name="mantenedores",
            former_worksheet_name="antigos_mantenedores",
        )
        self.client = GoogleSheetsClient(settings=self.settings)

    def test_fetch_former_mantenedores_reads_former_worksheet(self) -> None:
        """Deve ler antigos mantenedores da aba configurada."""
        self.client._get_values = Mock(
            return_value=[
                ["nome", "telefone"],
                ["Maria", "5571999999999"],
            ]
        )

        rows = self.client.fetch_former_mantenedores()

        self.assertEqual(rows[0].nome, "Maria")
        self.assertEqual(rows[0].telefone, "5571999999999")
        self.client._get_values.assert_called_once_with(
            spreadsheet_id="sheet-id",
            worksheet_name="antigos_mantenedores",
        )

    def test_fetch_mantenedores_skips_invalid_rows(self) -> None:
        """Deve ignorar linhas invalidas e continuar lendo a planilha."""
        self.client._get_values = Mock(
            return_value=[
                ["nome", "telefone", "valor"],
                ["Maria", "", "50"],
                ["Joao", "5571999999999", "30"],
            ]
        )

        rows = self.client.fetch_mantenedores()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].nome, "Joao")

    def test_fetch_former_mantenedores_skips_invalid_rows(self) -> None:
        """Deve ignorar antigos mantenedores sem telefone valido."""
        self.client._get_values = Mock(
            return_value=[
                ["nome", "telefone"],
                ["Maria", "telefone invalido"],
                ["Joao", "5571999999999"],
            ]
        )

        rows = self.client.fetch_former_mantenedores()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].nome, "Joao")

    def test_find_former_mantenedor_by_phone_returns_matching_row(self) -> None:
        """Deve encontrar antigo mantenedor pelo telefone normalizado."""
        self.client.fetch_former_mantenedores = Mock(
            return_value=[
                Mock(nome="Maria", telefone="(71) 99999-9999"),
                Mock(nome="Joao", telefone="5571888888888"),
            ]
        )

        row = self.client.find_former_mantenedor_by_phone("71999999999")

        self.assertIsNotNone(row)
        self.assertEqual(row.nome, "Maria")

    def test_append_mantenedor_writes_to_main_worksheet(self) -> None:
        """Deve inserir mantenedor na aba principal."""
        execute = Mock(return_value={"updates": {"updatedRows": 1}})
        append = Mock(return_value=Mock(execute=execute))
        values = Mock(return_value=Mock(append=append))
        spreadsheets = Mock(return_value=Mock(values=values))
        service = Mock(spreadsheets=spreadsheets)
        self.client._build_service = Mock(return_value=service)

        response = self.client.append_mantenedor(
            nome="Maria",
            telefone="5571999999999",
            valor="50",
        )

        self.assertEqual(response, {"updates": {"updatedRows": 1}})
        append.assert_called_once_with(
            spreadsheetId="sheet-id",
            range="'mantenedores'!A:C",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [["Maria", "5571999999999", "50"]]},
        )


if __name__ == "__main__":
    unittest.main()
