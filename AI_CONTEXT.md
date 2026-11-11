# Contexto curto para IA

Este repositorio automatiza ofertas de afiliados em grupos de WhatsApp usando
Python, FastAPI, SQLite e Evolution API.

## Antes de alterar

1. Leia `AGENTS.md` e a skill `automation-whats-maintenance`.
2. Nao leia `.env`, credenciais, QR codes, perfil de navegador ou banco real.
3. Use mocks; nao envie mensagens reais em testes.
4. Atualize documentacao e este arquivo quando o comportamento mudar.

## Estado

- webhook: `POST /webhooks/evolution`;
- healthcheck: `GET /health`;
- prontidao segura: `GET /ready`;
- fila Python: SQLite, fora do PostgreSQL/Redis da Evolution;
- grupos de origem filtrados por uma lista de JIDs exatos;
- o worker usa a coleta Playwright da POC do Mercado Livre e o perfil dedicado
  selecionado por `AFFILIATE_PLAYWRIGHT_BROWSER`; a conversao depende da flag
  `AFFILIATE_MERCADO_LIVRE_PLAYWRIGHT_ENABLED`, desligada por padrao;
- POC e worker aceitam `AFFILIATE_PLAYWRIGHT_CHROME_PROFILE_DIR` ou
  `AFFILIATE_PLAYWRIGHT_EDGE_PROFILE_DIR` para reutilizar o perfil do atalho;
- os perfis dedicados iniciados pela POC e pelo worker usam o sandbox do Chromium;
- a URL original de cada oferta vai ao navegador; a URL fixa e padrao da CLI
  da POC. A fila filtra Mercado Livre antes de aplicar o limite de conversoes;
- em terminal interativo e navegador visivel, o worker usa a mesma pausa para
  login ou verificacao manual da POC; o erro distingue verificacao repetida,
  navegacao interrompida e tempo esgotado;
- origens que nao abrem um anuncio ficam em quarentena; o worker segue no lote.
  A espera pelo atalho **Ir para produto** em perfis sociais e de ate 3 segundos.
  A conversao pela POC salva a URL da Barra quando a copia coincide com o campo,
  sem resolver a URL gerada nem exigir marcadores de rastreamento;
- `scripts.affiliate_worker --conversion-only` testa conversoes pendentes
  sem processar a fila de entrada ou publicar e mostra o motivo seguro de falhas;
- `scripts.affiliate_worker --watch` inicia FastAPI e roda a fila ate Ctrl+C.
  Ativa captura, conversao e envio no processo, aprova novas conversoes e
  espera 30 segundos entre rodadas. Falha da Evolution pausa o envio na sessao;
- `scripts.affiliate_worker --retry-copied-links` recupera ofertas bloqueadas
  pela validacao antiga do link copiado e executa uma rodada so de conversao;
- Shopee desativada por padrao;
- o envio usa `linkPreview=true` para solicitar a previa do link afiliado;
  a Evolution gera a miniatura a partir dos metadados que consegue obter;
  em 2026-11-11, um link curto do Mercado Livre retornou HTTP 403 de dentro
  do container Evolution e o Baileys nao retornou previa. O envio isolado
  desse link com `linkPreview=true` foi aceito sem titulo nem miniatura;
- Evolution GO de teste na porta 4000: pareamento falha com `405 Client outdated`.
  Correcao preparada em `poc/evolution_go_preview/Dockerfile`; compilacao inicial
  interrompida pela reinicializacao do Docker. O container segue na imagem oficial.
- revisao obrigatoria e publicacao automatica desativada por padrao;
- skill de revisao versionada em `skills/affiliate-review/SKILL.md`;
- instale com `pip install -r requirements.txt`; o arquivo referencia as
  dependencias diretas em `requirements-affiliate.txt`;
- ambiente virtual criado com as dependencias diretas;
- diagnostico sanitizado em `scripts/evolution_status.py`;
- configuracao local em `scripts/setup_evolution_windows.ps1`;
- diagnostico de 2026-11-10: WSL 3.0.5 e Docker Compose v5.6.1 disponiveis;
  apos iniciar o Docker Desktop, cliente e servidor responderam com 29.9.2;
  aplicativo e disco de dados ainda no C:, com 0,55 GB livres na checagem;
  nenhum container da Evolution, PostgreSQL ou Redis foi encontrado ativo;
  `.env` presente, com conteudo e grupos nao verificados;
- `venv` anterior tinha extensoes incompativeis. Em ambiente limpo com Python
  3.13.16, `requirements.txt`, `pip check` e os 34 testes passaram.

## Arquivos centrais

- parser: `automation_whats/affiliate/message_parser.py`;
- persistencia: `automation_whats/affiliate/repository.py`;
- resolvedor: `automation_whats/affiliate/link_resolver.py`;
- worker: `automation_whats/affiliate/worker.py`;
- webhook: `automation_whats/webhooks/handlers.py`;
- Evolution: `automation_whats/clients/evolution/client.py`.

## Riscos e proximos passos

- validar os JIDs reais em homologacao;
- homologar a conversao automatica e uma publicacao controlada;
- obter liberacao da Shopee;
- instalar a skill na pasta reconhecida pelo Codex;
- executar a suite completa em um venv com as dependencias diretas.

## POC e conversao do Mercado Livre

- Entrada em `poc/mercadolivre_affiliate/run.py` e roteiro em
  `poc/mercadolivre_affiliate/README.md`.
- Edge Stable com perfil dedicado. Chrome Stable exige `--cdp` para usar
  a sessão existente ou `--dedicated-profile` para abrir perfil separado.
  `--browser all --dedicated-profile` executa ambos em sequência.
  Extração, confirmação de cópia e atribuição
  são registradas separadamente. No Edge autenticado, o catálogo
  `MLB34229008` retornou um link confirmado no clipboard, com divergência entre
  o item exibido e o filtro solicitado. A sessão real dedicada e a comissão
  ainda precisam ser verificadas. Traces ficam restritos aos testes simulados.
