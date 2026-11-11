"""Testes offline do modo contínuo do worker."""

import os
import unittest
from unittest.mock import Mock, patch

from automation_whats.clients.evolution.exceptions import EvolutionAPIError
from automation_whats.affiliate.settings import AffiliateSettings
from scripts import affiliate_worker


class AffiliateWorkerCliTest(unittest.TestCase):
    def test_watch_enables_automatic_flow_for_this_process(self) -> None:
        with (
            patch("sys.argv", ["affiliate_worker", "--watch"]),
            patch.dict("os.environ", {
                "AFFILIATE_SOURCE_GROUP_JIDS": "source@g.us",
                "AFFILIATE_DESTINATION_GROUP_JID": "destination@g.us",
                "AFFILIATE_MERCADO_LIVRE_ENABLED": "true",
            }),
            patch.object(affiliate_worker, "AffiliateWorker") as worker_class,
            patch.object(affiliate_worker, "watch") as watch,
        ):
            affiliate_worker.main()

        settings: AffiliateSettings = worker_class.call_args.kwargs["settings"]
        self.assertTrue(settings.enabled and settings.groups_configured)
        self.assertTrue(settings.mercado_livre_playwright_enabled and settings.auto_publish)
        self.assertFalse(settings.review_required)
        watch.assert_called_once_with(worker_class.return_value)

    def test_watch_keeps_processing_and_closes_receiver_on_ctrl_c(self) -> None:
        worker = Mock()
        worker.process_pending.return_value = []
        worker.process_conversions.return_value = []
        worker.publish_approved.return_value = []
        with (
            patch.object(affiliate_worker.uvicorn, "Server") as server_class,
            patch.object(affiliate_worker, "Thread") as thread_class,
            patch.object(affiliate_worker, "sleep", side_effect=[None, KeyboardInterrupt]),
            patch("builtins.print"),
        ):
            server = server_class.return_value
            server.started = True
            receiver = thread_class.return_value
            affiliate_worker.watch(worker)

        self.assertEqual(worker.process_pending.call_count, 2)
        self.assertEqual(worker.process_conversions.call_count, 2)
        self.assertEqual(worker.publish_approved.call_count, 2)
        self.assertTrue(server.should_exit)
        receiver.join.assert_called_once_with(timeout=6)

    def test_watch_pauses_sending_on_evolution_failure(self) -> None:
        worker = Mock()
        worker.process_pending.return_value = []
        worker.process_conversions.return_value = []
        worker.publish_approved.side_effect = EvolutionAPIError
        with (
            patch.object(affiliate_worker.uvicorn, "Server"),
            patch.object(affiliate_worker, "Thread"),
            patch.object(affiliate_worker, "sleep", side_effect=[None, KeyboardInterrupt]),
            patch("builtins.print"),
        ):
            affiliate_worker.watch(worker)

        self.assertEqual(worker.process_conversions.call_count, 2)
        worker.publish_approved.assert_called_once()
