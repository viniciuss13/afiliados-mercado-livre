"""Testes offline dos dados públicos e do resultado da POC."""

import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from playwright.async_api import TimeoutError

from poc.mercadolivre_affiliate.run import (
    TEST_URL,
    AffiliatePoc,
    PocError,
    VerificationRequired,
    collect,
    TestResult,
    mercado_livre_url,
    requested_item,
    run_browser,
)


class AffiliatePocNavigationTest(unittest.IsolatedAsyncioTestCase):
    async def test_repeated_verification_reports_failure_after_manual_prompt(self):
        poc = Mock(open_product=AsyncMock(side_effect=VerificationRequired))
        with patch("builtins.input") as prompt:
            with self.assertRaisesRegex(PocError, "voltou a pedir verificação"):
                await collect(poc, TEST_URL, interactive=True)
        prompt.assert_called_once()
        self.assertEqual(poc.open_product.await_count, 2)

    async def test_uses_profile_configured_for_chrome(self):
        playwright = Mock()
        context = Mock(pages=[Mock()])
        context.close = AsyncMock()
        context.new_cdp_session = AsyncMock()
        cdp = context.new_cdp_session.return_value
        cdp.send.return_value = {"product": "Chrome"}
        launch = AsyncMock(return_value=context)
        playwright.chromium.launch_persistent_context = launch
        profile = Path("test-chrome-profile")
        with (
            patch.dict("os.environ", {"AFFILIATE_PLAYWRIGHT_CHROME_PROFILE_DIR": str(profile)}),
            patch("poc.mercadolivre_affiliate.run.collect", new_callable=AsyncMock),
        ):
            await run_browser(playwright, "chrome", Namespace(url=TEST_URL, no_login=True))
        self.assertEqual(launch.await_args.args[0], profile)
        self.assertEqual(launch.await_args.kwargs["channel"], "chrome")
        self.assertTrue(launch.await_args.kwargs["chromium_sandbox"])

    async def test_social_showcase_without_product_shortcut_reports_reason(self):
        page = Mock(url="https://www.mercadolivre.com.br/social/teste")
        page.goto = AsyncMock(return_value=None)
        cta = page.get_by_role.return_value.filter.return_value
        cta.first.wait_for = AsyncMock(side_effect=TimeoutError("timeout"))

        with self.assertRaisesRegex(PocError, "perfil social sem atalho"):
            await AffiliatePoc(page).open_product("https://meli.la/teste")

        page.goto.assert_awaited_once()
        cta.first.wait_for.assert_awaited_once_with(timeout=3_000)


class AffiliatePocTest(unittest.TestCase):
    def test_reads_item_filter_alongside_other_filters(self):
        self.assertEqual(requested_item(TEST_URL), "MLB4030651099")
        self.assertIsNone(requested_item("https://meli.la/teste"))

    def test_rejects_lookalike_urls_and_credentials(self):
        self.assertTrue(mercado_livre_url("https://meli.la/teste"))
        self.assertFalse(mercado_livre_url("https://meli.la.example.com/teste"))
        self.assertFalse(mercado_livre_url("https://user@meli.la/teste"))

    def test_copy_requires_same_value_as_extraction(self):
        link = "https://meli.la/teste"
        self.assertFalse(TestResult(link).copy_success)
        self.assertFalse(TestResult(link, "https://meli.la/outro").copy_success)
        self.assertTrue(TestResult(link, link).copy_success)
