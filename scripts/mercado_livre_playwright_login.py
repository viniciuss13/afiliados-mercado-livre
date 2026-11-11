"""Prepara e salva a sessao do Mercado Livre no perfil da automacao."""

import argparse
import os
from pathlib import Path
import time


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    browsers_dir = Path(".playwright-browsers").resolve()
    profile_dir = Path("playwright-profile/mercado-livre").resolve()
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(browsers_dir))

    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            no_viewport=True,
            args=["--start-maximized"],
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(
                "https://www.mercadolivre.com.br/",
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            page.bring_to_front()
            print(
                "Entre na conta de afiliado nesta janela. Ela fechara "
                "automaticamente quando o login for confirmado.",
                flush=True,
            )
            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                active = context.pages[-1]
                url = active.url.lower()
                if "mercadolivre.com.br" in url and "login" not in url:
                    enter = active.get_by_text("Entre", exact=True)
                    create = active.get_by_text("Crie a sua conta", exact=True)
                    enter_visible = enter.count() and enter.first.is_visible()
                    create_visible = create.count() and create.first.is_visible()
                    if not enter_visible and not create_visible:
                        active.wait_for_timeout(2000)
                        print("AUTHENTICATED", flush=True)
                        return
                active.wait_for_timeout(500)
            raise TimeoutError("O login nao foi concluido dentro do prazo")
        finally:
            context.close()


if __name__ == "__main__":
    main()
