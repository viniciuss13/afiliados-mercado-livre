"""Testes do webhook de mantenedor."""

import unittest
from unittest.mock import Mock, patch

from automation_whats.services.mantenedor_payment_reminder import (
    MantenedorPaymentReminderService,
)
from automation_whats.services.mantenedor_welcome import MantenedorWelcomeService
from automation_whats.webhooks.handlers import (
    EvolutionWebhookHandler,
    GoogleFormMantenedorWebhookHandler,
)


class MantenedorWelcomeServiceTest(unittest.TestCase):
    """Testa os disparos de boas-vindas para novo mantenedor."""

    @patch.dict(
        "os.environ",
        {
            "EVO_ADMIN_PHONES": "5571888888888, 5571777777777",
            "WECARE_WELCOME_IMAGE_URL": "https://example.com/we-care.png",
        },
        clear=False,
    )
    def test_send_sends_media_to_recipient_and_text_to_admin(self) -> None:
        """Deve enviar imagem para o novo mantenedor e texto para o admin."""
        client = Mock()
        client.send_media.return_value = {"recipient": "ok"}
        client.send_text.return_value = {"text": "ok"}
        service = MantenedorWelcomeService(client=client)

        response = service.send(
            nome="Maria",
            telefone="(71) 99999-9999",
            valor="50,00",
        )

        self.assertEqual(response["recipient"], {"recipient": "ok"})
        self.assertEqual(response["admin"], [{"text": "ok"}, {"text": "ok"}])
        client.send_media.assert_called_once()
        self.assertEqual(client.send_media.call_args.kwargs["number"], "5571999999999")
        self.assertEqual(client.send_text.call_count, 2)
        client.send_text.assert_any_call(
            number="5571888888888",
            text="Novo mantenedor cadastrado.\n\nNome: Maria\nValor: 50,00",
        )
        client.send_text.assert_any_call(
            number="5571777777777",
            text="Novo mantenedor cadastrado.\n\nNome: Maria\nValor: 50,00",
        )


class MantenedorPaymentReminderServiceTest(unittest.TestCase):
    """Testa os disparos de lembrete para mantenedor existente."""

    @patch.dict(
        "os.environ",
        {
            "EVO_ADMIN_PHONES": "5571888888888;5571777777777",
            "WECARE_WELCOME_IMAGE_URL": "https://example.com/we-care.png",
        },
        clear=False,
    )
    def test_send_sends_payment_reminder(self) -> None:
        """Deve enviar imagem, chave Pix em texto e admins."""
        client = Mock()
        client.send_media.return_value = {"recipient": "ok"}
        client.send_text.return_value = {"text": "ok"}
        service = MantenedorPaymentReminderService(client=client)

        response = service.send(
            nome="Maria",
            telefone="(71) 99999-9999",
            valor="50,00",
        )

        self.assertEqual(
            response["recipient"],
            {
                "reminder": {"recipient": "ok"},
                "pix": {"text": "ok"},
            },
        )
        client.send_media.assert_called_once()
        client.send_text.assert_any_call(
            number="5571999999999",
            text="*Chave pix*:\nwecare@lagoinhacajazeiras.com",
        )
        self.assertEqual(client.send_text.call_count, 3)

        reminder_text = client.send_media.call_args.kwargs["caption"]
        self.assertIn("Olá, Maria!", reminder_text)
        self.assertIn("Valor combinado: R$ 50,00", reminder_text)
        self.assertIn(
            "Caso você já tenha realizado sua contribuição",
            reminder_text,
        )

        client.send_text.assert_any_call(
            number="5571888888888",
            text="Lembrete enviado para mantenedor.\n\nNome: *Maria*\nValor: *R$ 50,00*",
        )
        client.send_text.assert_any_call(
            number="5571777777777",
            text="Lembrete enviado para mantenedor.\n\nNome: *Maria*\nValor: *R$ 50,00*",
        )

    def test_format_brl_formats_common_sheet_values(self) -> None:
        """Deve formatar valores comuns da planilha como moeda brasileira."""
        service = MantenedorPaymentReminderService(client=Mock())

        self.assertEqual(service._format_brl("30"), "R$ 30,00")
        self.assertEqual(service._format_brl("50,00"), "R$ 50,00")
        self.assertEqual(service._format_brl("1500.5"), "R$ 1.500,50")
        self.assertEqual(service._format_brl("1.500,5"), "R$ 1.500,50")


class GoogleFormMantenedorWebhookHandlerTest(unittest.TestCase):
    """Testa o handler do payload recebido do Google Forms."""

    def test_handle_processes_google_form_payload(self) -> None:
        """Deve validar o payload e chamar o service de cadastro."""
        service = Mock()
        handler = GoogleFormMantenedorWebhookHandler(welcome_service=service)

        response = handler.handle(
            {"nome": "Maria", "telefone": "5571999999999", "valor": "50,00"}
        )

        self.assertEqual(response, {"status": "processed"})
        service.send.assert_called_once_with(
            nome="Maria",
            telefone="5571999999999",
            valor="50,00",
        )


class EvolutionWebhookHandlerTest(unittest.TestCase):
    """Testa processamento de respostas recebidas pela Evolution API."""

    def test_handle_registers_reactivation_reply(self) -> None:
        """Deve cadastrar mantenedor quando receber resposta SIM com valor."""
        reply_service = Mock()
        reply_service.process_reply.return_value = {"status": "registered"}
        handler = EvolutionWebhookHandler(reactivation_reply_service=reply_service)

        response = handler.handle(
            {
                "event": "MESSAGES_UPSERT",
                "data": {
                    "key": {
                        "remoteJid": "5571999999999@s.whatsapp.net",
                        "fromMe": False,
                    },
                    "pushName": "Maria",
                    "message": {"conversation": "SIM 50"},
                },
            }
        )

        self.assertEqual(response, {"status": "registered"})
        reply_service.process_reply.assert_called_once_with(
            nome="Maria",
            telefone="5571999999999",
            message="SIM 50",
        )


if __name__ == "__main__":
    unittest.main()
