"""Persistencia SQLite da fila de ofertas."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo

from .models import IncomingMessage, OfferStatus


class AffiliateRepository:
    """Fila persistente, idempotente e independente do banco da Evolution."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS incoming_messages (
                    id INTEGER PRIMARY KEY,
                    instance TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    remote_jid TEXT NOT NULL,
                    participant_jid TEXT,
                    text TEXT NOT NULL,
                    media_type TEXT,
                    received_at TEXT NOT NULL,
                    UNIQUE(instance, message_id)
                );

                CREATE TABLE IF NOT EXISTS offers (
                    id INTEGER PRIMARY KEY,
                    incoming_message_id INTEGER NOT NULL,
                    original_url TEXT NOT NULL,
                    resolved_url TEXT,
                    marketplace TEXT,
                    product_id TEXT,
                    affiliate_url TEXT,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(incoming_message_id, original_url),
                    FOREIGN KEY(incoming_message_id) REFERENCES incoming_messages(id)
                );

                CREATE TABLE IF NOT EXISTS publications (
                    id INTEGER PRIMARY KEY,
                    offer_id INTEGER NOT NULL,
                    destination_jid TEXT NOT NULL,
                    evolution_message_id TEXT,
                    response_json TEXT,
                    sent_at TEXT NOT NULL,
                    UNIQUE(offer_id, destination_jid),
                    FOREIGN KEY(offer_id) REFERENCES offers(id)
                );

                CREATE TABLE IF NOT EXISTS agent_reviews (
                    id INTEGER PRIMARY KEY,
                    offer_id INTEGER NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT,
                    final_text TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(offer_id) REFERENCES offers(id)
                );
                """
            )

    def enqueue(self, message: IncomingMessage) -> tuple[bool, int]:
        """Grava mensagem e URLs uma única vez."""
        now = self._now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO incoming_messages
                (instance, message_id, remote_jid, participant_jid, text,
                 media_type, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.instance,
                    message.message_id,
                    message.remote_jid,
                    message.participant_jid,
                    message.text,
                    message.media_type,
                    now,
                ),
            )
            inserted = cursor.rowcount == 1
            row = connection.execute(
                "SELECT id FROM incoming_messages WHERE instance = ? AND message_id = ?",
                (message.instance, message.message_id),
            ).fetchone()
            if not inserted or row is None:
                return False, 0
            for url in message.urls:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO offers
                    (incoming_message_id, original_url, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (row["id"], url, OfferStatus.RECEIVED.value, now, now),
                )
            return True, len(message.urls)

    def list_offers(
        self, statuses: tuple[OfferStatus, ...], limit: int = 20,
        *, marketplace: str | None = None,
    ) -> list[dict[str, Any]]:
        placeholders = ",".join("?" for _ in statuses)
        query = f"""
            SELECT o.*, m.text AS source_text, m.media_type, m.remote_jid,
              (SELECT ar.final_text FROM agent_reviews ar
               WHERE ar.offer_id = o.id ORDER BY ar.id DESC LIMIT 1)
               AS reviewed_text
            FROM offers o
            JOIN incoming_messages m ON m.id = o.incoming_message_id
            WHERE o.status IN ({placeholders}) AND (? IS NULL OR o.marketplace = ?)
            ORDER BY o.id
            LIMIT ?
        """
        with self._connect() as connection:
            rows = connection.execute(
                query, (*[status.value for status in statuses], marketplace, marketplace, limit)
            ).fetchall()
        return [dict(row) for row in rows]

    def get_offer(self, offer_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT o.*, m.text AS source_text, m.media_type, m.remote_jid,
                  (SELECT ar.final_text FROM agent_reviews ar
                   WHERE ar.offer_id = o.id ORDER BY ar.id DESC LIMIT 1)
                   AS reviewed_text
                FROM offers o
                JOIN incoming_messages m ON m.id = o.incoming_message_id
                WHERE o.id = ?
                """,
                (offer_id,),
            ).fetchone()
        return dict(row) if row else None

    def update_resolution(
        self,
        offer_id: int,
        resolved_url: str,
        marketplace: str,
        product_id: str | None,
    ) -> None:
        self._update_offer(
            offer_id,
            status=OfferStatus.NEEDS_CONVERSION,
            resolved_url=resolved_url,
            marketplace=marketplace,
            product_id=product_id,
            last_error=None,
        )

    def set_affiliate_link(
        self,
        offer_id: int,
        affiliate_url: str,
        status: OfferStatus = OfferStatus.NEEDS_REVIEW,
    ) -> None:
        self._update_offer(
            offer_id,
            status=status,
            affiliate_url=affiliate_url,
            last_error=None,
        )

    def complete_conversion(
        self,
        offer_id: int,
        product_url: str,
        product_id: str,
        affiliate_url: str,
        status: OfferStatus,
    ) -> bool:
        """Grava a conversão de uma vez se a oferta ainda estiver pendente."""
        with self._connect() as connection:
            result = connection.execute(
                """
                UPDATE offers
                SET resolved_url = ?, product_id = ?, affiliate_url = ?,
                    status = ?, last_error = NULL, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    product_url, product_id, affiliate_url, status.value,
                    self._now(), offer_id, OfferStatus.NEEDS_CONVERSION.value,
                ),
            )
            return result.rowcount == 1

    def set_status(
        self, offer_id: int, status: OfferStatus, error: str | None = None
    ) -> None:
        self._update_offer(offer_id, status=status, last_error=error)

    def requeue_legacy_copy_failures(self) -> int:
        """Recupera ofertas bloqueadas pela validação antiga do link copiado."""
        with self._connect() as connection:
            result = connection.execute(
                """
                UPDATE offers
                SET status = ?, attempts = 0, last_error = NULL, updated_at = ?
                WHERE marketplace = 'mercado_livre' AND status IN (?, ?)
                  AND affiliate_url IS NULL AND resolved_url IS NOT NULL
                  AND last_error IN (?, ?, ?)
                """,
                (
                    OfferStatus.NEEDS_CONVERSION, self._now(),
                    OfferStatus.RETRY, OfferStatus.QUARANTINED,
                    "O link copiado não resolveu para um produto identificável",
                    "O link gerado aponta para outro produto",
                    "O link gerado não apresentou rastreamento de afiliado",
                ),
            )
            return result.rowcount

    def record_failure(
        self, offer_id: int, error: str, max_retries: int,
        *, expected_status: OfferStatus | None = None,
    ) -> OfferStatus | None:
        """Incrementa tentativas e coloca falhas repetidas em quarentena."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT attempts FROM offers WHERE id = ?", (offer_id,)
            ).fetchone()
            if row is None:
                raise ValueError("Offer not found")
            attempts = int(row["attempts"]) + 1
            status = (
                OfferStatus.QUARANTINED
                if attempts >= max_retries
                else OfferStatus.RETRY
            )
            result = connection.execute(
                """
                UPDATE offers
                SET attempts = ?, status = ?, last_error = ?, updated_at = ?
                WHERE id = ? AND (? IS NULL OR status = ?)
                """,
                (attempts, status.value, error, self._now(), offer_id,
                 expected_status, expected_status),
            )
        return status if result.rowcount else None

    def _update_offer(self, offer_id: int, status: OfferStatus, **values: Any) -> None:
        allowed = {
            "resolved_url",
            "marketplace",
            "product_id",
            "affiliate_url",
            "last_error",
        }
        fields = {key: value for key, value in values.items() if key in allowed}
        fields["status"] = status.value
        fields["updated_at"] = self._now()
        assignments = ", ".join(f"{key} = ?" for key in fields)
        with self._connect() as connection:
            connection.execute(
                f"UPDATE offers SET {assignments} WHERE id = ?",
                (*fields.values(), offer_id),
            )

    def already_sent_recently(
        self, marketplace: str, product_id: str | None, days: int
    ) -> bool:
        if not product_id:
            return False
        threshold = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM offers o
                JOIN publications p ON p.offer_id = o.id
                WHERE o.marketplace = ? AND o.product_id = ? AND p.sent_at >= ?
                LIMIT 1
                """,
                (marketplace, product_id, threshold),
            ).fetchone()
        return row is not None

    def publication_allowed(
        self,
        daily_limit: int,
        minimum_interval: int,
        timezone_name: str = "America/Bahia",
    ) -> bool:
        now = datetime.now(UTC)
        local_now = now.astimezone(ZoneInfo(timezone_name))
        today = local_now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ).astimezone(UTC).isoformat()
        with self._connect() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM publications WHERE sent_at >= ?", (today,)
            ).fetchone()[0]
            latest = connection.execute(
                "SELECT sent_at FROM publications ORDER BY sent_at DESC LIMIT 1"
            ).fetchone()
        if count >= daily_limit:
            return False
        if latest:
            sent_at = datetime.fromisoformat(latest["sent_at"])
            if (now - sent_at).total_seconds() < minimum_interval:
                return False
        return True

    def record_publication(
        self,
        offer_id: int,
        destination_jid: str,
        evolution_message_id: str | None,
        response: dict[str, Any],
    ) -> None:
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO publications
                (offer_id, destination_jid, evolution_message_id, response_json, sent_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    offer_id,
                    destination_jid,
                    evolution_message_id,
                    json.dumps(response, ensure_ascii=False),
                    now,
                ),
            )
            connection.execute(
                "UPDATE offers SET status = ?, updated_at = ? WHERE id = ?",
                (OfferStatus.SENT.value, now, offer_id),
            )

    def add_review(
        self, offer_id: int, decision: str, reason: str = "", final_text: str = ""
    ) -> None:
        normalized = decision.strip().lower()
        mapping = {
            "approve": OfferStatus.APPROVED,
            "reject": OfferStatus.REJECTED,
            "needs_human": OfferStatus.NEEDS_REVIEW,
        }
        if normalized not in mapping:
            raise ValueError("Invalid review decision")
        if normalized == "approve":
            offer = self.get_offer(offer_id)
            if offer is None or not offer.get("affiliate_url"):
                raise ValueError("An affiliate link is required before approval")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO agent_reviews
                (offer_id, decision, reason, final_text, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (offer_id, normalized, reason, final_text, self._now()),
            )
        self.set_status(offer_id, mapping[normalized])

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
