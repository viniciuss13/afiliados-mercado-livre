"""Testes do processamento de planilha de mantenedores."""

import unittest
from unittest.mock import Mock

from automation_whats.clients.google_sheets.schemas import MantenedorSheetRow
from automation_whats.services.sheet_mantenedor_import import (
    SheetMantenedorImportService,
)


class SheetMantenedorImportServiceTest(unittest.TestCase):
    """Testa a importacao de mantenedores da planilha."""

    def test_process_registers_each_sheet_row(self) -> None:
        """Deve enviar cada linha lida para o service de lembrete."""
        sheets_client = Mock()
        sheets_client.fetch_mantenedores.return_value = [
            MantenedorSheetRow(
                nome="Maria",
                telefone="5571999999999",
                valor="50,00",
            )
        ]
        reminder_service = Mock()
        reminder_service.send.return_value = {"ok": True}
        service = SheetMantenedorImportService(
            sheets_client=sheets_client,
            reminder_service=reminder_service,
        )

        results = service.process()

        self.assertEqual(results[0]["nome"], "Maria")
        reminder_service.send.assert_called_once_with(
            nome="Maria",
            telefone="5571999999999",
            valor="50,00",
        )

    def test_process_continues_when_one_send_fails(self) -> None:
        """Deve registrar erro da linha e continuar enviando as proximas."""
        sheets_client = Mock()
        sheets_client.fetch_mantenedores.return_value = [
            MantenedorSheetRow(
                nome="Maria",
                telefone="5571000000000",
                valor="50,00",
            ),
            MantenedorSheetRow(
                nome="Joao",
                telefone="5571999999999",
                valor="30,00",
            ),
        ]
        reminder_service = Mock()
        reminder_service.send.side_effect = [
            RuntimeError("number does not exist"),
            {"ok": True},
        ]
        service = SheetMantenedorImportService(
            sheets_client=sheets_client,
            reminder_service=reminder_service,
        )

        results = service.process()

        self.assertEqual(results[0]["status"], "error")
        self.assertEqual(results[0]["error"], "number does not exist")
        self.assertEqual(results[1]["status"], "sent")
        self.assertEqual(results[1]["response"], {"ok": True})
        self.assertEqual(reminder_service.send.call_count, 2)


if __name__ == "__main__":
    unittest.main()
