"""Service para importar mantenedores de uma planilha Google."""

from typing import Any

from automation_whats.clients.google_sheets import GoogleSheetsClient
from automation_whats.services.mantenedor_payment_reminder import (
    MantenedorPaymentReminderService,
)


class SheetMantenedorImportService:
    """Processa mantenedores lidos de uma planilha Google."""

    def __init__(
        self,
        sheets_client: GoogleSheetsClient | None = None,
        reminder_service: MantenedorPaymentReminderService | None = None,
    ) -> None:
        """Inicializa o service.

        Args:
            sheets_client: Client para ler dados da planilha.
            reminder_service: Service responsável pelo envio dos lembretes.
        """
        self._sheets_client = sheets_client or GoogleSheetsClient()
        self._reminder_service = reminder_service or MantenedorPaymentReminderService()

    def process(self) -> list[dict[str, Any]]:
        """Lê a planilha e envia lembretes para todos os mantenedores.

        Returns:
            Lista com resultado de cada linha processada.
        """
        results: list[dict[str, Any]] = []
        for mantenedor in self._sheets_client.fetch_mantenedores():
            try:
                response = self._reminder_service.send(
                    nome=mantenedor.nome,
                    telefone=mantenedor.telefone,
                    valor=mantenedor.valor,
                )
            except Exception as exc:
                results.append(
                    {
                        "nome": mantenedor.nome,
                        "telefone": mantenedor.telefone,
                        "valor": mantenedor.valor,
                        "status": "error",
                        "error": str(exc),
                    }
                )
                continue

            results.append(
                {
                    "nome": mantenedor.nome,
                    "telefone": mantenedor.telefone,
                    "valor": mantenedor.valor,
                    "status": "sent",
                    "response": response,
                }
            )

        return results
