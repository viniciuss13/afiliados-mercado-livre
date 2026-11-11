"""Testes da formatacao que preserva somente o link validado."""

import unittest

from automation_whats.affiliate.formatter import format_offer


class FormatterTest(unittest.TestCase):
    def test_replaces_all_source_urls_with_one_validated_link(self) -> None:
        text = "Oferta https://source.example/a cupom https://source.example/b"
        result = format_offer(text, "https://source.example/a", "https://meli.la/own")
        self.assertEqual(result, "Oferta https://meli.la/own cupom")
        self.assertEqual(result.count("https://"), 1)


if __name__ == "__main__":
    unittest.main()
