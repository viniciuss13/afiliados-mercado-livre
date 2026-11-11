"""POC isolada da interface de afiliados do Mercado Livre."""

import argparse
import asyncio
import logging
import os
import re
import sys
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit
from uuid import uuid4

from playwright.async_api import (
    Error,
    Page,
    Playwright,
    TimeoutError,
    async_playwright,
    expect,
)

TEST_URL = (
    "https://www.mercadolivre.com.br/impressora-multifuncional-cor-epson-"
    "ecotank-l3250/p/MLB34229008?pdp_filters=item_id%3AMLB4030651099"
    "&pdp_filters=official_store%3A2398"
)
ROOT = Path(__file__).resolve().parent
CHANNELS = {"edge": "msedge", "chrome": "chrome"}
TIMEOUT = 15_000
PRODUCT_SHORTCUT_TIMEOUT = 3_000
LOG = logging.getLogger("poc")


class PocError(Exception):
    """Etapa bloqueada, com uma mensagem segura para o terminal."""


class VerificationRequired(PocError):
    """O site apresentou uma verificação de segurança."""


class UnexpectedProductPage(PocError):
    """O link de origem ou de afiliado não identifica o anúncio esperado."""


def mercado_livre_url(value: str) -> bool:
    """Aceita URLs HTTPS dos domínios usados no teste."""
    try:
        parts = urlsplit(value)
        host = parts.hostname or ""
        return (
            not any(char.isspace() for char in value)
            and parts.scheme == "https"
            and parts.netloc.lower() == host
            and (
                host in {"meli.la", "mercadolivre.com.br", "mercadolivre.com"}
                or host.endswith((".mercadolivre.com.br", ".mercadolivre.com"))
            )
        )
    except ValueError:
        return False


def public_url(value: str) -> str:
    """Remove parâmetros de navegação e fragmentos do diagnóstico."""
    return urlsplit(value)._replace(query="", fragment="").geturl()


def requested_item(url: str) -> str | None:
    """Lê o item solicitado no filtro público da URL."""
    filters = parse_qs(urlsplit(url).query).get("pdp_filters", [])
    return next(
        (value[8:] for value in filters if re.fullmatch(r"item_id:MLB\d+", value)),
        None,
    )


@dataclass(frozen=True)
class TestResult:
    """Mantém independentes a extração, a cópia e a atribuição."""

    link: str
    copied: str | None = None
    product_url: str | None = None
    displayed_item: str | None = None

    @property
    def copy_success(self) -> bool:
        """Confirma igualdade após a troca observada no clipboard."""
        return self.copied == self.link


@dataclass
class AffiliatePoc:
    """Navega até o produto e captura o link na janela de compartilhamento."""

    page: Page
    allow_clipboard: bool = True
    evidence: Path | None = None
    displayed_item: str | None = None

    async def navigate(self, url: str) -> None:
        """Espera o DOM e trata destinos inesperados e erros HTTP."""
        try:
            response = await self.page.goto(url, wait_until="domcontentloaded")
        except TimeoutError:
            raise PocError("Tempo esgotado ao carregar o link da oferta no Chrome ou Edge.") from None
        except Error:
            raise PocError("A navegação do link foi interrompida. Mantenha a janela aberta até o fim da tentativa.") from None
        if not mercado_livre_url(self.page.url):
            raise UnexpectedProductPage("A navegação terminou fora do Mercado Livre.")
        if urlsplit(self.page.url).path.startswith(("/captcha/", "/login/challenges")):
            raise VerificationRequired("O Mercado Livre apresentou uma verificação de segurança.")
        if response is not None and response.status >= 400:
            raise PocError(f"A página retornou HTTP {response.status}.")

    async def open_product(self, url: str) -> str:
        """Segue o CTA observado no perfil social e verifica o anúncio."""
        self.displayed_item = None
        await self.navigate(url)
        redirected = self.page.url != url
        LOG.info("Redirecionamento observado: %s", "sim" if redirected else "não")
        LOG.info("Host do destino inicial: %s", urlsplit(self.page.url).hostname)
        if urlsplit(self.page.url).path.startswith("/social/"):
            cta = self.page.get_by_role(
                "link", name="Ir para produto", exact=True
            ).filter(visible=True)
            try:
                await cta.first.wait_for(timeout=PRODUCT_SHORTCUT_TIMEOUT)
            except TimeoutError:
                raise UnexpectedProductPage(
                    "O link abriu um perfil social sem atalho para um produto específico. "
                    "Use o link direto do anúncio."
                ) from None
            if await cta.count() != 1:
                raise UnexpectedProductPage(
                    "O perfil social oferece mais de um destino. Use o link direto do anúncio."
                )
            href = await cta.get_attribute("href")
            destination = urljoin(self.page.url, href or "")
            if not href or not mercado_livre_url(destination):
                raise UnexpectedProductPage("O CTA do perfil social não aponta para o Mercado Livre.")
            await self.navigate(destination)
        path = urlsplit(self.page.url).path
        if path.startswith(("/captcha/", "/login/challenges")):
            raise VerificationRequired("O Mercado Livre apresentou uma verificação de segurança.")
        if not re.search(r"(?:/p/MLB\d+|/MLB-\d+)(?:/|-|$)", path, re.I):
            raise UnexpectedProductPage("A navegação terminou fora de uma página de produto.")
        title = self.page.get_by_role("heading", level=1)
        try:
            await title.wait_for()
        except TimeoutError:
            raise PocError("A página do produto abriu, mas o título não carregou a tempo.") from None
        product = public_url(self.page.url)
        LOG.info("URL final do produto: %s", product)
        LOG.info("Título do produto: %s", await title.inner_text())
        requested = requested_item(url)
        LOG.info("Item solicitado: %s", requested or "sem filtro")
        item = self.page.locator("#denounce")
        if await item.count() == 1:
            match = re.search(r"#\s*(\d+)", await item.inner_text())
            if match:
                displayed = f"MLB{match.group(1)}"
                self.displayed_item = displayed
                LOG.info("Item exibido: %s", displayed)
                if requested and displayed != requested:
                    LOG.warning("O item exibido difere do item solicitado na URL.")
        return product

    async def extract(self) -> TestResult:
        """Aciona a Barra e lê o campo específico do gerador de afiliados."""
        bar = self.page.get_by_role("navigation", name="Afiliados", exact=True)
        share = bar.get_by_test_id("generate_link_button")
        LOG.info("Procurando Compartilhar na Barra de Afiliados.")
        try:
            await share.wait_for()
            LOG.info("Barra autenticada: navigation[Afiliados] / generate_link_button")
        except TimeoutError:
            raise PocError(
                "Barra de Afiliados indisponível. Use --login se a sessão "
                "expirou e confira a ativação da Barra na Central de Afiliados."
            ) from None

        panel = self.page.get_by_test_id("popper").filter(
            has_text="Gerar link / ID de produto", visible=True
        )
        if not await panel.is_visible():
            await share.click()
            LOG.info("Compartilhar acionado")
        await panel.wait_for()
        LOG.info("Aberto o componente Gerar link / ID de produto.")
        field = panel.get_by_test_id("text-field__label_link").filter(visible=True)
        try:
            await expect(field).to_have_value(re.compile(r"^https://"), timeout=5_000)
            value = (await field.input_value()).strip()
        except (AssertionError, TimeoutError):
            raise PocError("O campo Link do produto não apresentou uma URL.") from None
        if not mercado_livre_url(value):
            raise PocError("O campo Link do produto retornou uma URL inesperada.")
        LOG.info("EXTRACTION_SUCCESS selector=text-field__label_link link=%s", value)
        if self.evidence:
            try:
                await field.screenshot(path=self.evidence / "campo.png", timeout=3_000)
            except Error:
                LOG.warning("Screenshot do campo indisponível.")
        copy = panel.get_by_role("button", name="Link do produto", exact=True)
        marker = None
        try:
            await self.page.bring_to_front()
            if self.allow_clipboard:
                parts = urlsplit(self.page.url)
                await self.page.context.grant_permissions(
                    ["clipboard-read", "clipboard-write"],
                    origin=f"{parts.scheme}://{parts.netloc}",
                )
            candidate = f"poc-copy-{uuid4().hex}"
            await self.page.evaluate("text => navigator.clipboard.writeText(text)", candidate)
            marker = candidate
        except Error:
            LOG.warning("Clipboard indisponível para preparar a verificação.")
        try:
            await copy.click()
            LOG.info("Botão Copiar acionado: role=button name=Link do produto")
            if marker is None:
                return TestResult(value)
            copied = await asyncio.wait_for(
                self.page.evaluate(
                    """async (marker) => {
                      const deadline = performance.now() + 4500;
                      while (performance.now() < deadline) {
                        const text = (await navigator.clipboard.readText()).trim();
                        if (text && text !== marker) return text;
                        await new Promise(resolve => requestAnimationFrame(resolve));
                      }
                      return "";
                    }""",
                    marker,
                ),
                timeout=5,
            )
        except (Error, asyncio.TimeoutError):
            LOG.warning("Falha no botão Copiar ou na leitura do clipboard.")
            return TestResult(value)
        return TestResult(value, copied if copied == value else None)


async def collect(poc: AffiliatePoc, url: str, *, interactive: bool = False) -> TestResult:
    """Executa a mesma coleta em ambos os navegadores."""
    try:
        product_url = await poc.open_product(url)
    except VerificationRequired:
        if not interactive:
            raise
        LOG.info("O Mercado Livre solicitou uma verificação de segurança.")
        input("Conclua a verificação no navegador e pressione Enter aqui.\n")
        try:
            product_url = await poc.open_product(url)
        except VerificationRequired:
            raise PocError(
                "O Mercado Livre voltou a pedir verificação após a confirmação no terminal."
            ) from None
    login = poc.page.get_by_role("link", name="Entre", exact=True)
    if await login.is_visible():
        LOG.info("Autenticação: sessão ausente ou expirada.")
        if not interactive:
            raise PocError("Entre na conta de afiliado ou execute em terminal interativo.")
        input("Entre na conta na janela do navegador e pressione Enter aqui.\n")
        product_url = await poc.open_product(url)
        if await login.is_visible():
            raise PocError("A sessão continua deslogada após o login manual.")
    result = await poc.extract()
    if result.copy_success:
        LOG.info("COPY_SUCCESS link=%s", result.copied)
    else:
        LOG.warning("COPY_UNVERIFIED clipboard indisponível ou diferente do campo.")
    LOG.info("AFFILIATE_VALIDATION_PENDING")
    return replace(result, product_url=product_url, displayed_item=poc.displayed_item)


async def run(args: argparse.Namespace) -> None:
    """Abre e fecha o perfil persistente sem exportar dados de sessão."""
    if not mercado_livre_url(args.url):
        raise PocError("Informe uma URL HTTPS do Mercado Livre.")
    LOG.info("Link recebido: %s", args.url)
    async with async_playwright() as playwright:
        if args.cdp:
            endpoint = urlsplit(args.cdp)
            if endpoint.scheme not in {"http", "ws"} or endpoint.hostname not in {
                "127.0.0.1", "localhost", "::1"
            } or endpoint.username is not None:
                raise PocError("Informe um endereço CDP local, sem credenciais.")
            try:
                browser = await playwright.chromium.connect_over_cdp(
                    args.cdp, timeout=TIMEOUT, no_defaults=True
                )
            except Error:
                raise PocError(
                    "Conexão CDP indisponível. Verifique o endereço local e "
                    "autorize a conexão na janela do navegador."
                ) from None
            try:
                page = await browser.contexts[0].new_page()
                try:
                    page.set_default_timeout(TIMEOUT)
                    result = await collect(AffiliatePoc(page, allow_clipboard=False), args.url)
                    if not result.copy_success:
                        raise PocError("Cópia pendente na sessão conectada.")
                finally:
                    await page.close()
            finally:
                await browser.close()
            return

        browsers = ("edge", "chrome") if args.browser == "all" else (args.browser,)
        results = {}
        failed = False
        for name in browsers:
            evidence = ROOT / ".artifacts" / f"{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:8]}" / name
            evidence.mkdir(parents=True)
            trace = logging.FileHandler(evidence / "etapas.log", encoding="utf-8")
            trace.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            LOG.addHandler(trace)
            try:
                LOG.info("Navegador: %s | Entrada: %s", name, args.url)
                results[name] = await run_browser(playwright, name, args, evidence)
                failed |= not results[name].copy_success
            except PocError as exc:
                LOG.error("BLOQUEADO [%s] %s", name, exc)
                failed = True
            except Error:
                LOG.error("BLOQUEADO [%s] Falha no navegador, na navegação ou no locator.", name)
                failed = True
            finally:
                LOG.removeHandler(trace)
                trace.close()

        if len(results) == 2:
            identical = results["edge"].link == results["chrome"].link
            LOG.info("Comparação: links %s.", "iguais" if identical else "diferentes")
        if failed:
            raise PocError("Uma ou mais verificações de extração ou cópia ficaram pendentes.")


async def run_browser(
    playwright: Playwright,
    name: str,
    args: argparse.Namespace,
    evidence: Path | None = None,
    *,
    headless: bool = False,
) -> TestResult:
    """Abre o navegador instalado e reutiliza somente seu perfil dedicado."""
    configured_profile = os.getenv(f"AFFILIATE_PLAYWRIGHT_{name.upper()}_PROFILE_DIR")
    profile = Path(configured_profile) if configured_profile else ROOT / ".browser_profiles" / name
    LOG.info("Perfil dedicado: %s (%s)", name, "configurado" if configured_profile else "padrão")
    context = await playwright.chromium.launch_persistent_context(
        profile,
        channel=CHANNELS[name],
        headless=headless,
        chromium_sandbox=True,
        locale="pt-BR",
        accept_downloads=False,
    )
    try:
        context.set_default_timeout(TIMEOUT)
        page = context.pages[0] if context.pages else await context.new_page()
        cdp = await context.new_cdp_session(page)
        try:
            version = await cdp.send("Browser.getVersion")
            LOG.info("Navegador aberto: %s (%s)", name, version["product"])
        finally:
            await cdp.detach()
        return await collect(
            AffiliatePoc(page, evidence=evidence),
            args.url,
            interactive=not args.no_login and sys.stdin.isatty(),
        )
    finally:
        await context.close()


def main() -> int:
    """Executa a POC e sinaliza falhas com código de saída diferente de zero."""
    parser = argparse.ArgumentParser(description=__doc__)
    login_mode = parser.add_mutually_exclusive_group()
    login_mode.add_argument("--login", action="store_true", help="Permite login manual quando necessário (padrão).")
    login_mode.add_argument("--no-login", action="store_true", help="Não pausa para login.")
    parser.add_argument("--url", default=TEST_URL, help="Link do Mercado Livre.")
    browser_mode = parser.add_mutually_exclusive_group()
    browser_mode.add_argument("--browser", choices=("edge", "chrome", "all"), default="edge")
    browser_mode.add_argument("--chrome", dest="browser", action="store_const", const="chrome")
    profile_mode = parser.add_mutually_exclusive_group()
    profile_mode.add_argument("--cdp", help="Conecta a uma sessão existente via CDP local.")
    profile_mode.add_argument(
        "--dedicated-profile",
        action="store_true",
        help="Autoriza abrir o Chrome em um perfil separado.",
    )
    args = parser.parse_args()
    if args.browser == "all" and args.cdp:
        parser.error("Use --cdp com um navegador por vez.")
    if args.browser in {"chrome", "all"} and not (args.cdp or args.dedicated_profile):
        parser.error(
            "Para usar o Chrome já logado, informe --cdp com o endereço local "
            "da sessão autorizada. Para abrir um perfil separado, use "
            "--dedicated-profile."
        )
    if args.cdp and args.login:
        parser.error("Faça login na sessão existente antes de usar --cdp.")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        asyncio.run(run(args))
    except PocError as exc:
        LOG.error("BLOQUEADO. %s", exc)
    except TimeoutError:
        LOG.error("BLOQUEADO. Tempo esgotado na etapa indicada acima.")
    except Error:
        LOG.error(
            "BLOQUEADO. Falha do navegador ou do locator. Verifique a instalação, "
            "a rede e se o perfil já está aberto em outra execução."
        )
    except (EOFError, KeyboardInterrupt):
        LOG.error("INTERROMPIDO. Use um terminal interativo para as etapas manuais.")
    else:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
