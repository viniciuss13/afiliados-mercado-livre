"""Envia lembretes para mantenedores a partir de uma planilha Google."""

import json

from automation_whats.services.sheet_mantenedor_import import (
    SheetMantenedorImportService,
)


def main() -> None:
    """Executa a leitura da planilha, envia lembretes e imprime o resumo."""
    results = SheetMantenedorImportService().process()
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
