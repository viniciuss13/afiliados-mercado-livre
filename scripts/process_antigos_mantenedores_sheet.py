"""Envia retomada para antigos mantenedores a partir do Google Sheets."""

import json

from automation_whats.services.sheet_former_mantenedor_import import (
    SheetFormerMantenedorImportService,
)


def main() -> None:
    """Executa a leitura da planilha e imprime o resumo do envio."""
    results = SheetFormerMantenedorImportService().process()
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
