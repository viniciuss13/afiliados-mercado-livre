"""Conversao assistida de links do Mercado Livre usando Playwright."""

from dataclasses import dataclass
import os
from pathlib import Path
import re
import time
from urllib.parse import urlparse

from ..link_resolver import SafeLinkResolver
from .links import identify_marketplace


URL_PATTERN = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)


class AffiliateLinkCaptureTimeout(TimeoutError):
    """Indica que nenhum link de afiliado valido foi copiado a tempo."""


class MercadoLivreAutomationError(RuntimeError):
    """Indica que a interface do Mercado Livre nao concluiu a conversao."""


@dataclass(frozen=True)
class MercadoLivreConversionResult:
    """Resultado validado de uma conversao assistida."""

    source_url: str
    source_product_id: str
    affiliate_url: str
    affiliate_final_url: str | None = None


def extract_mercado_livre_url(text: str) -> str | None:
    """Retorna a primeira URL do Mercado Livre presente no texto."""
    for match in URL_PATTERN.findall(text):
        candidate = match.rstrip(".,;:!?)]}\"")
        product = identify_marketplace(candidate)
        if product is not None and product.marketplace == "mercado_livre":
            return candidate
    return None


def mercado_livre_product_id(urls: tuple[str, ...]) -> str | None:
    """Localiza o produto em qualquer etapa de uma cadeia de URLs."""
    for url in urls:
        product = identify_marketplace(url)
        if (
            product is not None
            and product.marketplace == "mercado_livre"
            and product.product_id
        ):
            return product.product_id
    return None


def has_affiliate_tracking(urls: tuple[str, ...]) -> bool:
    """Confirma sinais de rastreamento gerados pelas ferramentas de afiliado."""
    markers = ("matt_tool=", "matt_word=", "utm_medium=affiliates", "mmp_pid=")
    lowered = tuple(url.lower() for url in urls)
    return any(marker in url for marker in markers for url in lowered)


class MercadoLivrePlaywrightConverter:
    """Abre o produto e captura o link copiado pelo usuario no navegador."""

    def __init__(
        self,
        profile_dir: Path | str = Path("playwright-profile/mercado-livre"),
        browsers_dir: Path | str = Path(".playwright-browsers"),
        timeout_seconds: int = 600,
        poll_interval_seconds: float = 1.0,
        resolver: SafeLinkResolver | None = None,
    ) -> None:
        self.profile_dir = Path(profile_dir).resolve()
        self.browsers_dir = Path(browsers_dir).resolve()
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.resolver = resolver or SafeLinkResolver(
            (
                "meli.la",
                "mercadolivre.com.br",
                "www.mercadolivre.com.br",
            )
        )

    def convert(self, source_url: str) -> MercadoLivreConversionResult:
        """Executa o teste assistido e valida que o produto nao mudou."""
        source = self.resolver.resolve(source_url)
        source_product_id = mercado_livre_product_id(
            (*source.redirect_chain, source.final_url)
        )

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.browsers_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault(
            "PLAYWRIGHT_BROWSERS_PATH",
            str(self.browsers_dir),
        )

        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                no_viewport=True,
                args=["--start-maximized"],
            )
            try:
                context.grant_permissions(["clipboard-read"])
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(source.final_url, wait_until="domcontentloaded", timeout=60_000)
                page.bring_to_front()
                baseline = self._clipboard_text(page)
                if source_product_id:
                    print(
                        "Navegador aberto. Entre na conta se necessario, use a "
                        "opcao de afiliado do Mercado Livre e clique em copiar link.",
                        flush=True,
                    )
                else:
                    print(
                        "Pagina de oferta aberta. Clique no produto anunciado para "
                        "abrir a pagina dele; depois use a opcao de afiliado e clique "
                        "em copiar link.",
                        flush=True,
                    )
                print(
                    "O teste apenas validara o link; nenhuma mensagem sera publicada.",
                    flush=True,
                )

                deadline = time.monotonic() + self.timeout_seconds
                source_product_url = source.final_url
                while time.monotonic() < deadline:
                    if not source_product_id:
                        source_product_id = mercado_livre_product_id((page.url,))
                        if source_product_id:
                            source_product_url = page.url
                            print(
                                f"Produto detectado: {source_product_id}. "
                                "Agora gere e copie o link de afiliado.",
                                flush=True,
                            )
                    clipboard = self._clipboard_text(page)
                    if clipboard and clipboard != baseline:
                        candidate = extract_mercado_livre_url(clipboard)
                        if candidate and source_product_id:
                            affiliate = self.resolver.resolve(candidate)
                            affiliate_product_id = mercado_livre_product_id(
                                (*affiliate.redirect_chain, affiliate.final_url)
                            )
                            if affiliate_product_id != source_product_id:
                                raise ValueError(
                                    "O link de afiliado aponta para outro produto"
                                )
                            return MercadoLivreConversionResult(
                                source_url=source_product_url,
                                source_product_id=source_product_id,
                                affiliate_url=candidate,
                                affiliate_final_url=affiliate.final_url,
                            )
                    page.wait_for_timeout(int(self.poll_interval_seconds * 1000))
            finally:
                context.close()

        if not source_product_id:
            raise AffiliateLinkCaptureTimeout(
                "Nenhuma pagina de produto Mercado Livre foi aberta dentro do prazo"
            )
        raise AffiliateLinkCaptureTimeout(
            "Nenhum link de afiliado valido foi copiado dentro do prazo"
        )

    @staticmethod
    def _clipboard_text(page: object) -> str:
        try:
            value = page.evaluate("async () => await navigator.clipboard.readText()")
        except Exception:
            return ""
        return value.strip() if isinstance(value, str) else ""


class MercadoLivreAutomaticConverter:
    """Gera um link pela Barra de Afiliados sem interacao manual."""

    def __init__(
        self,
        profile_dir: Path | str = Path("playwright-profile/mercado-livre"),
        browsers_dir: Path | str = Path(".playwright-browsers"),
        timeout_seconds: int = 90,
        headless: bool = True,
        resolver: SafeLinkResolver | None = None,
    ) -> None:
        self.profile_dir = Path(profile_dir).resolve()
        self.browsers_dir = Path(browsers_dir).resolve()
        self.timeout_seconds = timeout_seconds
        self.headless = headless
        self.resolver = resolver or SafeLinkResolver(
            ("meli.la", "mercadolivre.com.br", "www.mercadolivre.com.br")
        )

    def convert(self, source_url: str) -> MercadoLivreConversionResult:
        """Abre o anuncio, usa Compartilhar e captura o link gerado."""
        source = self.resolver.resolve(source_url)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.browsers_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(self.browsers_dir))

        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=self.headless,
                no_viewport=True,
                args=["--start-maximized"],
            )
            try:
                context.grant_permissions(["clipboard-read", "clipboard-write"])
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(source.final_url, wait_until="domcontentloaded", timeout=60_000)
                page, source_product_url, source_product_id = self._ensure_product_page(
                    page,
                    mercado_livre_product_id((*source.redirect_chain, source.final_url)),
                )
                self._wait_for_security_check(page)
                affiliate_url = self._generate_link(page)
                affiliate = self.resolver.resolve(affiliate_url)
                affiliate_urls = (*affiliate.redirect_chain, affiliate.final_url)
                affiliate_product_id = mercado_livre_product_id(affiliate_urls)
                if affiliate_product_id != source_product_id:
                    raise MercadoLivreAutomationError(
                        "O link gerado aponta para outro produto"
                    )
                if not has_affiliate_tracking(affiliate_urls):
                    raise MercadoLivreAutomationError(
                        "O link gerado nao apresentou rastreamento de afiliado"
                    )
                return MercadoLivreConversionResult(
                    source_url=source_product_url,
                    source_product_id=source_product_id,
                    affiliate_url=affiliate_url,
                    affiliate_final_url=affiliate.final_url,
                )
            finally:
                context.close()

    def _ensure_product_page(
        self, page: object, product_id: str | None
    ) -> tuple[object, str, str]:
        if product_id:
            return page, page.url, product_id

        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            current_id = mercado_livre_product_id((page.url,))
            if current_id:
                return page, page.url, current_id

            for locator in (
                page.get_by_role("link", name=re.compile(r"ir para produto", re.I)),
                page.get_by_role("button", name=re.compile(r"ir para produto", re.I)),
                page.get_by_text(re.compile(r"^ir para produto$", re.I)),
            ):
                try:
                    if locator.count() and locator.first.is_visible():
                        locator.first.click(timeout=5000)
                        page.wait_for_timeout(1500)
                        destination = page.context.pages[-1]
                        destination.bring_to_front()
                        destination.wait_for_load_state(
                            "domcontentloaded", timeout=60_000
                        )
                        destination_id = mercado_livre_product_id((destination.url,))
                        if destination_id:
                            return destination, destination.url, destination_id
                except Exception:
                    continue

            links = page.locator("a[href]")
            for index in range(min(links.count(), 100)):
                link = links.nth(index)
                try:
                    href = link.get_attribute("href") or ""
                    absolute = page.evaluate(
                        "href => new URL(href, document.baseURI).href", href
                    )
                except Exception:
                    continue
                candidate_id = mercado_livre_product_id((absolute,))
                parsed = urlparse(absolute)
                if (
                    candidate_id
                    and parsed.scheme == "https"
                    and parsed.hostname
                    and parsed.hostname.endswith("mercadolivre.com.br")
                ):
                    page.goto(
                        absolute,
                        wait_until="domcontentloaded",
                        timeout=60_000,
                    )
                    return page, page.url, candidate_id
            page.wait_for_timeout(1000)
        raise MercadoLivreAutomationError(
            "Nao foi possivel localizar o produto na pagina social"
        )

    def _generate_link(self, page: object) -> str:
        try:
            page.evaluate("async () => await navigator.clipboard.writeText('')")
        except Exception:
            pass

        self._click_first(page, (r"Aceitar cookies",), required=False)
        entry_patterns = (r"^Compartilhar$", r"Gerar link", r"Ganhar")
        if not self._click_first(page, entry_patterns):
            self._wait_for_security_check(page)
            if not self._click_first(page, entry_patterns):
                raise MercadoLivreAutomationError(
                    "A Barra de Afiliados nao foi encontrada; ative-a na Central"
                )
        page.wait_for_timeout(800)

        self._click_first(page, (r"^Gerar$", r"Gerar link"), required=False)
        page.wait_for_timeout(800)
        if not self._click_first(
            page,
            (r"^Copiar dados$", r"Copiar link", r"^Copiar$"),
        ):
            raise MercadoLivreAutomationError(
                "O comando Copiar dados do Link do produto nao foi encontrado"
            )

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            copied = MercadoLivrePlaywrightConverter._clipboard_text(page)
            candidate = extract_mercado_livre_url(copied)
            if candidate:
                return candidate
            page.wait_for_timeout(300)

        inputs = page.locator("input[value^='https://']")
        for index in range(inputs.count()):
            try:
                candidate = extract_mercado_livre_url(inputs.nth(index).input_value())
            except Exception:
                continue
            if candidate:
                return candidate
        raise MercadoLivreAutomationError("O link gerado nao pode ser capturado")

    def _wait_for_security_check(self, page: object) -> None:
        def challenged() -> bool:
            try:
                text = page.locator("body").inner_text(timeout=2000)
            except Exception:
                return False
            normalized = text.lower().replace("ç", "c").replace("ã", "a")
            return (
                "complete esta etapa" in normalized
                or "ir para o login" in normalized
            )

        if not challenged():
            return
        if self.headless:
            raise MercadoLivreAutomationError(
                "O Mercado Livre solicitou verificacao de seguranca; execute "
                "uma rodada visivel"
            )
        print(
            "O Mercado Livre solicitou uma verificacao de seguranca. "
            "Conclua-a na janela aberta; o processo retomara automaticamente.",
            flush=True,
        )
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            if not challenged():
                page.wait_for_timeout(1500)
                return
            page.wait_for_timeout(500)
        raise MercadoLivreAutomationError(
            "A verificacao de seguranca nao foi concluida dentro do prazo"
        )

    @staticmethod
    def _click_first(
        page: object, patterns: tuple[str, ...], required: bool = True
    ) -> bool:
        deadline = time.monotonic() + (12 if required else 0)
        while True:
            for pattern in patterns:
                regex = re.compile(pattern, re.IGNORECASE)
                for locator in (
                    page.get_by_role("button", name=regex),
                    page.get_by_role("link", name=regex),
                    page.get_by_text(regex),
                ):
                    try:
                        if locator.count() and locator.first.is_visible():
                            locator.first.click(timeout=5000)
                            return True
                    except Exception:
                        continue
            if time.monotonic() >= deadline:
                return False
            page.wait_for_timeout(250)
