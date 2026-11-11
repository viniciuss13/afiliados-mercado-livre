"""Testes offline dos auxiliares da conversao Playwright."""

import unittest

from automation_whats.affiliate.marketplaces.mercado_livre_playwright import (
    extract_mercado_livre_url,
    has_affiliate_tracking,
    mercado_livre_product_id,
)


class MercadoLivrePlaywrightTest(unittest.TestCase):
    def test_extracts_only_mercado_livre_url(self) -> None:
        self.assertEqual(
            extract_mercado_livre_url(
                "Oferta https://meli.la/abc e https://example.com/outro"
            ),
            "https://meli.la/abc",
        )

    def test_ignores_unrelated_clipboard_content(self) -> None:
        self.assertIsNone(
            extract_mercado_livre_url(
                "senha qualquer e https://example.com/nao-e-marketplace"
            )
        )

    def test_finds_product_before_catalog_redirect(self) -> None:
        self.assertEqual(
            mercado_livre_product_id(
                (
                    "https://produto.mercadolivre.com.br/MLB-2907859698-item-_JM",
                    "https://www.mercadolivre.com.br/p/MLB123456",
                )
            ),
            "MLB2907859698",
        )

    def test_requires_affiliate_tracking_signal(self) -> None:
        self.assertTrue(
            has_affiliate_tracking(
                ("https://produto.mercadolivre.com.br/MLB-123?matt_tool=456",)
            )
        )
        self.assertFalse(
            has_affiliate_tracking(
                ("https://produto.mercadolivre.com.br/MLB-123",)
            )
        )


if __name__ == "__main__":
    unittest.main()
