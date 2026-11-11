# Testes e homologacao

## Automatizados

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m unittest discover -v
```

Os testes cobrem parser, legenda de imagem, filtro de grupo, duplicidade SQLite,
marketplaces, captura segura de URL no teste Playwright, webhook HTTP e client
Evolution com mocks.

O teste assistido do Mercado Livre esta descrito em
[`MERCADO_LIVRE_PLAYWRIGHT.md`](MERCADO_LIVRE_PLAYWRIGHT.md).

## Homologacao segura

1. mantenha `AFFILIATE_ENABLED=false` e `AFFILIATE_AUTO_PUBLISH=false`;
2. liste os grupos e confira os dois JIDs;
3. use primeiro grupos de homologacao;
4. ative apenas a captura;
5. envie uma oferta controlada no grupo de origem;
6. confirme uma unica linha na fila;
7. execute o worker e confira `NEEDS_CONVERSION`;
8. associe um link seu e confira `NEEDS_REVIEW`;
9. aprove a oferta;
10. publique uma unica vez com `affiliate_publish --confirm`;
11. reenvie o mesmo webhook e confirme `duplicate`.

Nunca execute scripts de publicacao contra o grupo real sem revisar o destino.
