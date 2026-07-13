"""Service para importar antigos mantenedores de uma planilha Google."""

from typing import Any

from automation_whats.clients.google_sheets import GoogleSheetsClient
from automation_whats.services.mantenedor_reactivation import (
    MantenedorReactivationService,
)


class SheetFormerMantenedorImportService:
    """Processa antigos mantenedores lidos de uma planilha Google."""

    def __init__(
        self,
        sheets_client: GoogleSheetsClient | None = None,
        reactivation_service: MantenedorReactivationService | None = None,
    ) -> None:
        """Inicializa o service.

        Args:
            sheets_client: Client para ler dados da planilha.
            reactivation_service: Service responsavel pelo envio da retomada.
        """
        self._sheets_client = sheets_client or GoogleSheetsClient()
        self._reactivation_service = (
            reactivation_service or MantenedorReactivationService()
        )

    def process(self) -> list[dict[str, Any]]:
        """Le a planilha e envia convite para antigos mantenedores.

        Returns:
            Lista com resultado de cada linha processada.
        """
        results: list[dict[str, Any]] = []
        for mantenedor in self._sheets_client.fetch_former_mantenedores():
            try:
                response = self._reactivation_service.send(
                    nome=mantenedor.nome,
                    telefone=mantenedor.telefone,
                )
            except Exception as exc:
                results.append(
                    {
                        "nome": mantenedor.nome,
                        "telefone": mantenedor.telefone,
                        "status": "error",
                        "error": str(exc),
                    }
                )
                continue

            results.append(
                {
                    "nome": mantenedor.nome,
                    "telefone": mantenedor.telefone,
                    "status": "sent",
                    "response": response,
                }
            )

        return results
