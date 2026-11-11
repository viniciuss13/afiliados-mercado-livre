"""Testes da configuracao de grupos da automacao."""

import unittest
from unittest.mock import patch

from automation_whats.affiliate.settings import AffiliateSettings


class AffiliateSettingsTest(unittest.TestCase):
    @patch.dict(
        "os.environ",
        {
            "AFFILIATE_SOURCE_GROUP_JIDS": (
                "120363111111111111@g.us, 120363222222222222@g.us,"
                "120363111111111111@g.us"
            ),
            "AFFILIATE_DESTINATION_GROUP_JID": "120363333333333333@g.us",
        },
        clear=False,
    )
    def test_source_groups_are_normalized_and_deduplicated(self) -> None:
        settings = AffiliateSettings.from_env()

        self.assertEqual(
            settings.source_group_jids,
            (
                "120363111111111111@g.us",
                "120363222222222222@g.us",
            ),
        )
        self.assertTrue(settings.groups_configured)

    def test_destination_cannot_be_a_source_group(self) -> None:
        settings = AffiliateSettings(
            source_group_jids=("120363111111111111@g.us",),
            destination_group_jid="120363111111111111@g.us",
        )

        self.assertFalse(settings.groups_configured)


if __name__ == "__main__":
    unittest.main()
