"""Executa o worker de afiliados em uma rodada ou em modo contínuo."""

import argparse
import json
import os
from threading import Thread
from time import monotonic, sleep

import uvicorn

from automation_whats.affiliate import AffiliateWorker
from automation_whats.affiliate.settings import AffiliateSettings
from automation_whats.clients.evolution.exceptions import EvolutionAPIError


def watch(worker: AffiliateWorker) -> None:
    """Recebe webhooks e processa a fila no terminal até Ctrl+C."""
    server = uvicorn.Server(uvicorn.Config(
        "automation_whats.webhooks.app:app",
        host=os.getenv("WEBHOOK_HOST", "0.0.0.0"),
        port=int(os.getenv("WEBHOOK_PORT", "8000")),
        timeout_graceful_shutdown=5,
    ))
    receiver = Thread(target=server.run, name="affiliate-webhook", daemon=True)
    receiver.start()
    try:
        deadline = monotonic() + 10
        while not server.started and receiver.is_alive() and monotonic() < deadline:
            sleep(0.1)
        if not server.started:
            raise SystemExit("O FastAPI não iniciou. Confira se outro processo já usa a porta do webhook.")

        print("Captura, conversão e envio automático ativos. Pressione Ctrl+C para parar.", flush=True)
        sending_paused = False
        while receiver.is_alive():
            result = {
                "processed": worker.process_pending(),
                "converted": worker.process_conversions(),
                "published": [],
            }
            if not sending_paused:
                try:
                    result["published"] = worker.publish_approved()
                except EvolutionAPIError:
                    sending_paused = True
                    print(
                        "Envios pausados após falha na Evolution. Confira o grupo e a conexão "
                        "antes de reiniciar. A captura e a conversão continuam.",
                        flush=True,
                    )
            if any(result.values()):
                print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            sleep(30)
        raise SystemExit("O receptor de webhooks encerrou. O worker foi interrompido.")
    except KeyboardInterrupt:
        print("Automação encerrada.", flush=True)
    finally:
        server.should_exit = True
        receiver.join(timeout=6)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--watch", action="store_true",
        help="Inicia o webhook e converte e envia ofertas reais continuamente até Ctrl+C.",
    )
    mode.add_argument(
        "--conversion-only", action="store_true",
        help="Converte ofertas pendentes sem processar a fila de entrada ou publicar.",
    )
    mode.add_argument(
        "--retry-copied-links", action="store_true",
        help="Recoloca na fila links bloqueados pela validação antiga e roda apenas a conversão.",
    )
    args = parser.parse_args()
    if args.watch:
        os.environ.update({
            "AFFILIATE_ENABLED": "true",
            "AFFILIATE_MERCADO_LIVRE_PLAYWRIGHT_ENABLED": "true",
            "AFFILIATE_REVIEW_REQUIRED": "false",
            "AFFILIATE_AUTO_PUBLISH": "true",
        })
        settings = AffiliateSettings.from_env()
        if not settings.groups_configured:
            parser.error("Configure os grupos de origem e destino antes de iniciar o modo contínuo.")
        if not settings.mercado_livre_enabled:
            parser.error("Habilite AFFILIATE_MERCADO_LIVRE_ENABLED para o modo contínuo.")
        watch(AffiliateWorker(settings=settings))
        return
    worker = AffiliateWorker()
    conversion_only = args.conversion_only or args.retry_copied_links
    result = {}
    if args.retry_copied_links:
        if not worker.settings.mercado_livre_playwright_enabled:
            parser.error("Habilite AFFILIATE_MERCADO_LIVRE_PLAYWRIGHT_ENABLED antes de tentar novamente.")
        result["requeued"] = worker.repository.requeue_legacy_copy_failures()
    result.update({
        "processed": [] if conversion_only else worker.process_pending(),
        "converted": worker.process_conversions(),
        "published": [] if conversion_only else worker.publish_approved(),
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
