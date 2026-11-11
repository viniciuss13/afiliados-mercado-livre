# Conversao assistida do Mercado Livre

O teste abre um Chromium visivel com perfil persistente e aguarda o operador
gerar e copiar um link pela interface oficial de afiliados do Mercado Livre.
O processo le somente uma URL do Mercado Livre copiada durante a execucao,
resolve os redirecionamentos e confirma que o identificador do produto nao
mudou. Nenhuma oferta e publicada por esse comando.

## Preparacao

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-affiliate.txt
$env:PLAYWRIGHT_BROWSERS_PATH="$PWD\.playwright-browsers"
.\venv\Scripts\python.exe -m playwright install chromium
```

As pastas `.playwright-browsers/` e `playwright-profile/` nao devem ser
versionadas, inspecionadas ou compartilhadas. O perfil guarda somente a sessao
local usada pelo navegador do teste.

## Executar

```powershell
.\venv\Scripts\python.exe -m scripts.mercado_livre_playwright_test `
  --url "URL_DO_PRODUTO"
```

Na janela aberta:

1. entre na conta de afiliado, se necessario;
2. se o link veio de uma pagina social, clique no produto anunciado para abrir a
   pagina dele;
3. abra a opcao de afiliado do produto;
4. gere o link;
5. clique em copiar link;
6. aguarde a janela fechar e o terminal mostrar `VALIDATED`.

O resultado deste teste ainda nao associa o link a uma oferta da fila. Essa
ligacao so deve ser habilitada depois de validar um marcador confiavel de
propriedade da conta de afiliado.

## Conversao automatica pela POC

O worker reutiliza a coleta da [POC do Mercado Livre](../poc/mercadolivre_affiliate/README.md)
e o perfil dedicado ja autenticado. Use `edge` ou `chrome`, conforme o perfil
testado. Para autenticar o Chrome dedicado, use `--browser chrome --dedicated-profile`
na POC. O worker abre o navegador instalado e usa o perfil dedicado, enquanto o
modo CDP continua disponivel pelo comando da POC.
Chrome e Edge iniciados pelo perfil dedicado usam o sandbox do Chromium.

Para reutilizar o perfil do atalho **Chrome Afiliado**, configure
`AFFILIATE_PLAYWRIGHT_CHROME_PROFILE_DIR` com o caminho de `--user-data-dir`
do atalho. Para **Edge Afiliado**, use `AFFILIATE_PLAYWRIGHT_EDGE_PROFILE_DIR`.
No PowerShell, defina a mesma variavel de ambiente para testar a POC.
Feche o navegador que estiver usando esse perfil antes de executar.

A CLI da POC usa uma URL fixa como padrao. Na fila, cada chamada recebe a URL
original extraida da mensagem do WhatsApp. O navegador segue os redirecionamentos
e abre o produto a partir desse link. A fila seleciona as ofertas do Mercado
Livre em ordem de ID antes de aplicar o limite.
Depois de abrir um perfil social, a POC espera ate 3 segundos por um unico
atalho visivel **Ir para produto**.
Se a pagina mostrar apenas a vitrine, use o link direto do anuncio na origem.
O worker registra `QUARANTINED` quando a origem nao abre um anuncio identificavel
e segue para a proxima oferta no mesmo lote. A rodada examina ate
`AFFILIATE_REVIEW_BATCH_LIMIT` ofertas ou o limite de conversao, se for maior.
Falhas de sessao, verificacao e tempo esgotado contam como tentativa normal.

Para testar uma conversao por rodada, configure no `.env`:

```env
AFFILIATE_MERCADO_LIVRE_PLAYWRIGHT_ENABLED=true
AFFILIATE_PLAYWRIGHT_BROWSER=edge
AFFILIATE_PLAYWRIGHT_HEADLESS=false
AFFILIATE_PLAYWRIGHT_CONVERSION_LIMIT=1
AFFILIATE_REVIEW_REQUIRED=true
AFFILIATE_AUTO_PUBLISH=false
```

Feche a janela do perfil dedicado antes de rodar a fila:

```powershell
.\venv\Scripts\python.exe -m scripts.affiliate_worker --conversion-only
.\venv\Scripts\python.exe -m scripts.affiliate_list_pending
```

O modo `--conversion-only` seleciona ofertas em `NEEDS_CONVERSION`. Ele deixa a
fila de entrada e a publicacao para a rodada normal. A saida `converted` inclui
o campo `error` em tentativas com falha. A oferta convertida passa a
`NEEDS_REVIEW` com a revisao habilitada. Como na POC, a copia precisa coincidir
com a URL no campo da Barra de Afiliados. O link curto e salvo como foi copiado.
Uma divergencia entre o item solicitado e o exibido continua como alerta da POC.
Em terminal interativo, com
`AFFILIATE_PLAYWRIGHT_HEADLESS=false`, o worker permite concluir login ou
verificacao na janela do navegador e continuar ao pressionar Enter no terminal,
como na POC. Execucoes sem janela ou sem terminal exigem sessao ativa. A
atribuicao de comissao precisa ser verificada na conta de afiliado.
Se o site pedir verificacao novamente ou interromper a navegacao, o campo
`error` identifica a falha da tentativa.

Para recuperar ofertas em `RETRY` ou `QUARANTINED` por causa da validacao antiga
do link copiado, execute uma rodada com `--retry-copied-links`. A saida
`requeued` mostra quantas voltaram a `NEEDS_CONVERSION`. O comando reinicia as
tentativas desses itens e executa apenas conversao, sem publicar. As rodadas
seguintes podem usar `--conversion-only`.
