"""Configuracao da automacao de afiliados."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _as_int(value: str | None, default: int, minimum: int = 1) -> int:
    try:
        parsed = int(value) if value is not None else default
    except ValueError:
        return default
    return max(parsed, minimum)


def _as_group_jids(value: str | None) -> tuple[str, ...]:
    """Normaliza uma lista separada por virgulas e remove duplicados."""
    if not value:
        return ()
    return tuple(
        dict.fromkeys(item.strip() for item in value.split(",") if item.strip())
    )


@dataclass(frozen=True)
class AffiliateSettings:
    """Opcoes de recepcao, revisao e publicacao."""

    enabled: bool = False
    source_group_jids: tuple[str, ...] = ()
    destination_group_jid: str = ""
    db_path: Path = Path("data/affiliate.sqlite3")
    allowed_domains: tuple[str, ...] = (
        "meli.la",
        "mercadolivre.com.br",
        "www.mercadolivre.com.br",
        "s.shopee.com.br",
        "shopee.com.br",
        "www.shopee.com.br",
    )
    mercado_livre_enabled: bool = True
    shopee_enabled: bool = False
    auto_publish: bool = False
    review_required: bool = True
    review_batch_limit: int = 20
    daily_limit: int = 40
    min_send_interval_seconds: int = 90
    dedupe_days: int = 7
    max_retries: int = 3
    timezone_name: str = "America/Bahia"
    mercado_livre_marker: str = ""
    shopee_marker: str = ""
    mercado_livre_playwright_enabled: bool = False
    playwright_headless: bool = True
    playwright_conversion_limit: int = 1
    playwright_browser: str = "edge"

    @classmethod
    def from_env(cls) -> "AffiliateSettings":
        """Carrega configuracao sem expor valores em logs."""
        load_dotenv()
        domains = tuple(
            item.strip().lower()
            for item in os.getenv(
                "AFFILIATE_ALLOWED_DOMAINS",
                "meli.la,mercadolivre.com.br,www.mercadolivre.com.br,"
                "s.shopee.com.br,shopee.com.br,www.shopee.com.br",
            ).split(",")
            if item.strip()
        )
        return cls(
            enabled=_as_bool(os.getenv("AFFILIATE_ENABLED")),
            source_group_jids=_as_group_jids(
                os.getenv("AFFILIATE_SOURCE_GROUP_JIDS")
                or os.getenv("AFFILIATE_SOURCE_GROUP_JID")
            ),
            destination_group_jid=os.getenv(
                "AFFILIATE_DESTINATION_GROUP_JID", ""
            ).strip(),
            db_path=Path(
                os.getenv("AFFILIATE_DB_PATH", "data/affiliate.sqlite3")
            ),
            allowed_domains=domains,
            mercado_livre_enabled=_as_bool(
                os.getenv("AFFILIATE_MERCADO_LIVRE_ENABLED"), True
            ),
            shopee_enabled=_as_bool(os.getenv("AFFILIATE_SHOPEE_ENABLED")),
            auto_publish=_as_bool(os.getenv("AFFILIATE_AUTO_PUBLISH")),
            review_required=_as_bool(
                os.getenv("AFFILIATE_REVIEW_REQUIRED"), True
            ),
            review_batch_limit=_as_int(
                os.getenv("AFFILIATE_REVIEW_BATCH_LIMIT"), 20
            ),
            daily_limit=_as_int(os.getenv("AFFILIATE_DAILY_LIMIT"), 40),
            min_send_interval_seconds=_as_int(
                os.getenv("AFFILIATE_MIN_SEND_INTERVAL_SECONDS"), 90
            ),
            dedupe_days=_as_int(os.getenv("AFFILIATE_DEDUPE_DAYS"), 7),
            max_retries=_as_int(os.getenv("AFFILIATE_MAX_RETRIES"), 3),
            timezone_name=os.getenv(
                "AFFILIATE_TIMEZONE", "America/Bahia"
            ).strip(),
            mercado_livre_marker=os.getenv(
                "AFFILIATE_MERCADO_LIVRE_MARKER", ""
            ).strip(),
            shopee_marker=os.getenv("AFFILIATE_SHOPEE_MARKER", "").strip(),
            mercado_livre_playwright_enabled=_as_bool(
                os.getenv("AFFILIATE_MERCADO_LIVRE_PLAYWRIGHT_ENABLED")
            ),
            playwright_headless=_as_bool(
                os.getenv("AFFILIATE_PLAYWRIGHT_HEADLESS"), True
            ),
            playwright_conversion_limit=_as_int(
                os.getenv("AFFILIATE_PLAYWRIGHT_CONVERSION_LIMIT"), 1
            ),
            playwright_browser=os.getenv("AFFILIATE_PLAYWRIGHT_BROWSER", "edge").strip().lower(),
        )

    @property
    def groups_configured(self) -> bool:
        """Indica se os dois grupos foram configurados de forma segura."""
        return bool(
            self.source_group_jids
            and all(jid.endswith("@g.us") for jid in self.source_group_jids)
            and len(set(self.source_group_jids)) == len(self.source_group_jids)
            and self.destination_group_jid.endswith("@g.us")
            and self.destination_group_jid not in self.source_group_jids
        )
