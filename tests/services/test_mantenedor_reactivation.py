"""Testes do fluxo de reativacao de antigos mantenedores."""

import unittest
from unittest.mock import Mock

from automation_whats.clients.google_sheets.schemas import (
    FormerMantenedorSheetRow,
)
from automation_whats.services.mantenedor_reactivation import (
    MantenedorReactivationReplyService,
    MantenedorReactivationService,
)
from automation_whats.services.sheet_former_mantenedor_import import (
    SheetFormerMantenedorImportService,
)


class MantenedorReactivationServiceTest(unittest.TestCase):
    """Testa o envio de convite para antigos mantenedores."""

    def test_send_sends_reactivation_message(self) -> None:
        """Deve enviar mensagem de retomada para antigo mantenedor."""
        client = Mock()
        client.send_text.return_value = {"status": "PENDING"}
        service = MantenedorReactivationService(client=client)

        response = service.send(nome="Maria", telefone="(71) 99999-9999")

        self.assertEqual(response, {"status": "PENDING"})
        client.send_text.assert_called_once()
        self.assertEqual(client.send_text.call_args.kwargs["number"], "5571999999999")
        message = client.send_text.call_args.kwargs["text"]
        self.assertIn("Olá, Maria!", message)
        self.assertIn("Você já caminhou conosco como mantenedor do We Care", message)
        self.assertIn("Lagoinha Cajazeiras", message)
        self.assertIn("SIM + o valor", message)


class SheetFormerMantenedorImportServiceTest(unittest.TestCase):
    """Testa o processamento da aba de antigos mantenedores."""

    def test_process_sends_each_former_mantenedor(self) -> None:
        """Deve enviar convite para cada antigo mantenedor lido."""
        sheets_client = Mock()
        sheets_client.fetch_former_mantenedores.return_value = [
            FormerMantenedorSheetRow(nome="Maria", telefone="5571999999999")
        ]
        reactivation_service = Mock()
        reactivation_service.send.return_value = {"ok": True}
        service = SheetFormerMantenedorImportService(
            sheets_client=sheets_client,
            reactivation_service=reactivation_service,
        )

        results = service.process()

        self.assertEqual(results[0]["nome"], "Maria")
        reactivation_service.send.assert_called_once_with(
            nome="Maria",
            telefone="5571999999999",
        )

    def test_process_continues_when_one_send_fails(self) -> None:
        """Deve registrar erro e continuar enviando para antigos mantenedores."""
        sheets_client = Mock()
        sheets_client.fetch_former_mantenedores.return_value = [
            FormerMantenedorSheetRow(nome="Maria", telefone="5571000000000"),
            FormerMantenedorSheetRow(nome="Joao", telefone="5571999999999"),
        ]
        reactivation_service = Mock()
        reactivation_service.send.side_effect = [
            RuntimeError("number does not exist"),
            {"ok": True},
        ]
        service = SheetFormerMantenedorImportService(
            sheets_client=sheets_client,
            reactivation_service=reactivation_service,
        )

        results = service.process()

        self.assertEqual(results[0]["status"], "error")
        self.assertEqual(results[0]["error"], "number does not exist")
        self.assertEqual(results[1]["status"], "sent")
        self.assertEqual(results[1]["response"], {"ok": True})
        self.assertEqual(reactivation_service.send.call_count, 2)


class MantenedorReactivationReplyServiceTest(unittest.TestCase):
    """Testa cadastro automatico por resposta SIM."""

    def test_registers_reply_with_sim_and_value(self) -> None:
        """Deve inserir mantenedor quando resposta tiver SIM e valor."""
        sheets_client = Mock()
        sheets_client.find_mantenedor_by_phone.return_value = None
        service = MantenedorReactivationReplyService(sheets_client=sheets_client)

        result = service.process_reply(
            nome="Maria",
            telefone="5571999999999",
            message="SIM 50",
        )

        self.assertEqual(result, {"status": "registered"})
        sheets_client.append_mantenedor.assert_called_once_with(
            nome="Maria",
            telefone="5571999999999",
            valor="50",
        )

    def test_uses_former_mantenedor_name_when_whatsapp_name_is_missing(self) -> None:
        """Deve buscar nome na aba antiga quando webhook nao enviar nome."""
        sheets_client = Mock()
        sheets_client.find_mantenedor_by_phone.return_value = None
        sheets_client.find_former_mantenedor_by_phone.return_value = (
            FormerMantenedorSheetRow(nome="Maria", telefone="5571999999999")
        )
        service = MantenedorReactivationReplyService(sheets_client=sheets_client)

        result = service.process_reply(
            nome="",
            telefone="5571999999999",
            message="SIM 50",
        )

        self.assertEqual(result, {"status": "registered"})
        sheets_client.append_mantenedor.assert_called_once_with(
            nome="Maria",
            telefone="5571999999999",
            valor="50",
        )

    def test_does_not_register_when_name_cannot_be_resolved(self) -> None:
        """Nao deve cadastrar usando telefone como nome."""
        sheets_client = Mock()
        sheets_client.find_mantenedor_by_phone.return_value = None
        sheets_client.find_former_mantenedor_by_phone.return_value = None
        service = MantenedorReactivationReplyService(sheets_client=sheets_client)

        result = service.process_reply(
            nome="5571999999999",
            telefone="5571999999999",
            message="SIM 50",
        )

        self.assertEqual(result, {"status": "missing_name"})
        sheets_client.append_mantenedor.assert_not_called()

    def test_ignores_reply_without_sim(self) -> None:
        """Nao deve cadastrar respostas que nao comecem com SIM."""
        sheets_client = Mock()
        service = MantenedorReactivationReplyService(sheets_client=sheets_client)

        result = service.process_reply(
            nome="Maria",
            telefone="5571999999999",
            message="Tenho interesse",
        )

        self.assertEqual(result, {"status": "ignored"})
        sheets_client.append_mantenedor.assert_not_called()

    def test_ignores_sim_without_value(self) -> None:
        """Nao deve cadastrar SIM sem valor de contribuicao."""
        sheets_client = Mock()
        service = MantenedorReactivationReplyService(sheets_client=sheets_client)

        result = service.process_reply(
            nome="Maria",
            telefone="5571999999999",
            message="SIM",
        )

        self.assertEqual(result, {"status": "ignored"})
        sheets_client.find_mantenedor_by_phone.assert_not_called()
        sheets_client.append_mantenedor.assert_not_called()

    def test_marks_no_reply_as_declined(self) -> None:
        """Deve desconsiderar explicitamente respostas negativas."""
        sheets_client = Mock()
        service = MantenedorReactivationReplyService(sheets_client=sheets_client)

        result = service.process_reply(
            nome="Maria",
            telefone="5571999999999",
            message="Não",
        )

        self.assertEqual(result, {"status": "declined"})
        sheets_client.find_mantenedor_by_phone.assert_not_called()
        sheets_client.append_mantenedor.assert_not_called()

    def test_marks_nao_without_accent_as_declined(self) -> None:
        """Deve aceitar NAO sem acento como resposta negativa."""
        sheets_client = Mock()
        service = MantenedorReactivationReplyService(sheets_client=sheets_client)

        result = service.process_reply(
            nome="Maria",
            telefone="5571999999999",
            message="NAO obrigado",
        )

        self.assertEqual(result, {"status": "declined"})
        sheets_client.find_mantenedor_by_phone.assert_not_called()
        sheets_client.append_mantenedor.assert_not_called()

    def test_skips_existing_mantenedor(self) -> None:
        """Nao deve duplicar telefone ja cadastrado."""
        sheets_client = Mock()
        sheets_client.find_mantenedor_by_phone.return_value = object()
        service = MantenedorReactivationReplyService(sheets_client=sheets_client)

        result = service.process_reply(
            nome="Maria",
            telefone="5571999999999",
            message="SIM 50",
        )

        self.assertEqual(result, {"status": "already_registered"})
        sheets_client.append_mantenedor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
