"""Ponto de entrada da aplicação."""

import json

from automation_whats.services.sheet_mantenedor_import import (
    SheetMantenedorImportService,
)


def main() -> None:
    """Processa a planilha de mantenedores e imprime o resumo do envio."""
    results = SheetMantenedorImportService().process()
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
