"""Adapta a coleta da POC ao fluxo de ofertas do worker."""

import argparse
import asyncio

from playwright.async_api import Error, TimeoutError, async_playwright

from poc.mercadolivre_affiliate.run import (
    CHANNELS,
    TestResult,
    UnexpectedProductPage,
    mercado_livre_url,
    run_browser,
)

from ..link_resolver import SafeLinkResolver
from .mercado_livre_playwright import (
    MercadoLivreAutomationError,
    MercadoLivreConversionResult,
    mercado_livre_product_id,
)


class MercadoLivrePocConverter:
    """Usa o perfil dedicado da POC e devolve o link confirmado na cópia."""

    def __init__(self, resolver: SafeLinkResolver, *, browser: str, headless: bool) -> None:
        if browser not in CHANNELS:
            raise ValueError("Selecione edge ou chrome para o conversor do Mercado Livre")
        self.resolver = resolver
        self.browser = browser
        self.headless = headless

    async def _collect(self, url: str) -> TestResult:
        async with async_playwright() as playwright:
            return await run_browser(
                playwright,
                self.browser,
                argparse.Namespace(url=url, no_login=self.headless),
                headless=self.headless,
            )

    def convert(self, source_url: str) -> MercadoLivreConversionResult:
        if not mercado_livre_url(source_url):
            raise UnexpectedProductPage("A origem não é uma URL HTTPS do Mercado Livre")
        source = self.resolver.resolve(source_url)
        if not mercado_livre_url(source.final_url):
            raise UnexpectedProductPage("A origem redirecionou para fora do Mercado Livre")
        try:
            result = asyncio.run(self._collect(source_url))
        except TimeoutError:
            raise MercadoLivreAutomationError(
                "Tempo esgotado enquanto o navegador aguardava uma etapa da conversão."
            ) from None
        except Error:
            raise MercadoLivreAutomationError(
                "O Playwright interrompeu a conversão. Confira se a janela permaneceu aberta."
            ) from None
        if not result.copy_success or not mercado_livre_url(result.link):
            raise MercadoLivreAutomationError("A POC não confirmou a cópia do link do produto")
        if not result.product_url:
            raise UnexpectedProductPage("A POC não identificou a página do produto de origem")
        product_id = mercado_livre_product_id((result.product_url,))
        if not product_id:
            raise UnexpectedProductPage("A POC não identificou a página do produto de origem")
        return MercadoLivreConversionResult(
            source_url=result.product_url,
            source_product_id=product_id,
            affiliate_url=result.link,
        )
