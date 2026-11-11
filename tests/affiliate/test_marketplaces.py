"""Testes da identificacao e equivalencia dos produtos."""

import unittest

from automation_whats.affiliate.marketplaces import (
    identify_marketplace,
    validate_same_product,
)


class MarketplaceLinksTest(unittest.TestCase):
    def test_identifies_shopee_product(self) -> None:
        product = identify_marketplace("https://shopee.com.br/product/10/20")
        self.assertEqual(product.marketplace, "shopee")
        self.assertEqual(product.product_id, "10:20")

    def test_blocks_changed_product(self) -> None:
        with self.assertRaises(ValueError):
            validate_same_product(
                "https://www.mercadolivre.com.br/item/MLB-123",
                "https://www.mercadolivre.com.br/item/MLB-456",
            )

    def test_requires_product_identity_on_both_links(self) -> None:
        with self.assertRaisesRegex(ValueError, "identity"):
            validate_same_product(
                "https://www.mercadolivre.com.br/social/promocoes",
                "https://www.mercadolivre.com.br/item/MLB-456",
            )


if __name__ == "__main__":
    unittest.main()
