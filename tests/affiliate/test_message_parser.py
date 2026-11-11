"""Testes do parser de eventos da Evolution API."""

import unittest

from automation_whats.affiliate.message_parser import EvolutionMessageParser


class EvolutionMessageParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = EvolutionMessageParser()

    def test_extracts_group_image_caption_and_unique_urls(self) -> None:
        message = self.parser.parse(
            {
                "event": "messages.upsert",
                "instance": "affiliate",
                "data": {
                    "key": {
                        "remoteJid": "120363000000000000@g.us",
                        "participant": "5571000000000@s.whatsapp.net",
                        "fromMe": False,
                        "id": "MSG-1",
                    },
                    "message": {
                        "imageMessage": {
                            "caption": "Oferta https://meli.la/abc https://meli.la/abc"
                        }
                    },
                },
            }
        )

        self.assertIsNotNone(message)
        self.assertEqual(message.remote_jid, "120363000000000000@g.us")
        self.assertEqual(message.urls, ("https://meli.la/abc",))
        self.assertEqual(message.media_type, "image")

    def test_ignores_outgoing_and_unrelated_events(self) -> None:
        outgoing = {
            "event": "MESSAGES_UPSERT",
            "data": {
                "key": {
                    "remoteJid": "120363000000000000@g.us",
                    "fromMe": True,
                    "id": "MSG-2",
                },
                "message": {"conversation": "https://meli.la/abc"},
            },
        }
        self.assertIsNone(self.parser.parse(outgoing))
        self.assertIsNone(self.parser.parse({"event": "connection.update"}))


if __name__ == "__main__":
    unittest.main()
