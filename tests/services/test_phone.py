"""Testes da normalizacao de telefone."""

import unittest

from automation_whats.services.phone import normalize_brazilian_phone


class PhoneTest(unittest.TestCase):
    """Testa formatacao de telefones para envio no WhatsApp."""

    def test_adds_brazil_country_code_to_local_mobile(self) -> None:
        """Deve adicionar DDI 55 quando telefone vier com DDD e numero."""
        self.assertEqual(normalize_brazilian_phone("71993741498"), "5571993741498")

    def test_keeps_existing_brazil_country_code(self) -> None:
        """Deve manter numero que ja possui DDI 55."""
        self.assertEqual(normalize_brazilian_phone("5571993741498"), "5571993741498")

    def test_removes_phone_mask(self) -> None:
        """Deve remover mascara antes de normalizar."""
        self.assertEqual(
            normalize_brazilian_phone("(71) 99374-1498"),
            "5571993741498",
        )


if __name__ == "__main__":
    unittest.main()
