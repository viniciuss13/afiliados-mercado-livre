# Affiliate Whats

Automacao local para receber ofertas de um grupo do WhatsApp pela Evolution
API, validar links de Mercado Livre/Shopee e publicar ofertas aprovadas em outro
grupo.

## Estado atual

- recebe `MESSAGES_UPSERT` em `POST /webhooks/evolution`;
- aceita somente o JID exato do grupo de origem;
- extrai links de texto e legendas de imagem, video ou documento;
- grava mensagens e ofertas em SQLite com idempotencia;
- resolve links HTTPS apenas em dominios permitidos;
- identifica Mercado Livre e Shopee e compara IDs de produto quando presentes;
- valida um link de afiliado antes de liberar a oferta;
- exige revisao por padrao;
- aplica limite diario, intervalo minimo e deduplicacao antes da publicacao;
- envia texto com o link afiliado e solicita a previa do link pela Evolution;
- deixa Shopee e publicacao automatica desativadas por padrao.

A conversao automatica do Mercado Livre esta disponivel por Playwright e usa a
Barra de Afiliados da sessao local autenticada. Ela fica desativada por padrao
ate a homologacao. A miniatura da previa depende dos metadados que a Evolution
consegue obter do link enviado.

## Preparacao

Requisitos: Python 3.12 ou 3.13, Docker Desktop e uma instancia conectada na
Evolution API. A instalacao e os testes foram verificados com Python 3.13.16.

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Comece com estes controles:

```env
AFFILIATE_ENABLED=false
AFFILIATE_AUTO_PUBLISH=false
AFFILIATE_REVIEW_REQUIRED=true
AFFILIATE_SHOPEE_ENABLED=false
AFFILIATE_MERCADO_LIVRE_PLAYWRIGHT_ENABLED=false
```

Liste os grupos acessiveis e copie os JIDs corretos:

```powershell
.\venv\Scripts\python.exe -m scripts.affiliate_list_groups
```

Configure `AFFILIATE_SOURCE_GROUP_JID` e
`AFFILIATE_DESTINATION_GROUP_JID`. Os dois devem terminar em `@g.us` e precisam
ser diferentes.

Inicie o receptor e configure o webhook:

```powershell
.\venv\Scripts\python.exe -m automation_whats.webhooks.server
.\venv\Scripts\python.exe -m scripts.configure_webhook
```

Somente depois dos testes, altere `AFFILIATE_ENABLED=true`.

## Fluxo operacional

### Modo contínuo no Windows

Com a Evolution em execução, a instância conectada e o webhook já configurado,
encerre o FastAPI separado para liberar a porta do webhook. Feche também a janela
do perfil Chrome Afiliado. Depois, na raiz do projeto, rode:

```powershell
$env:AFFILIATE_PLAYWRIGHT_BROWSER = 'chrome'
$env:AFFILIATE_PLAYWRIGHT_CHROME_PROFILE_DIR = "$env:LOCALAPPDATA\MLAfiliadoPOC\Chrome"
$env:AFFILIATE_PLAYWRIGHT_HEADLESS = 'false'
.\venv\Scripts\python.exe -m scripts.affiliate_worker --watch
```

`--watch` inicia o FastAPI e executa rodadas de captura, conversão e **envio real**,
com 30 segundos de espera entre rodadas. O modo aprova automaticamente as novas
conversões neste processo e envia as ofertas aprovadas ao destino configurado.
Ofertas que já aguardavam revisão precisam ser aprovadas separadamente. Para
parar o receptor e o worker, pressione **Ctrl+C**. Em caso de falha no envio,
a captura e a conversão continuam. Confira o grupo antes de reiniciar o envio.

### Rodada manual

```powershell
# Resolver ofertas recebidas, sem publicar
.\venv\Scripts\python.exe -m scripts.affiliate_worker

# Mostrar itens que precisam de conversao ou revisao
.\venv\Scripts\python.exe -m scripts.affiliate_list_pending

# Associar e validar um link gerado pela conta de afiliado
.\venv\Scripts\python.exe -m scripts.affiliate_set_link --offer 1 --url "https://..."

# Aplicar decisoes de revisao em JSON
.\venv\Scripts\python.exe -m scripts.affiliate_apply_decisions --file decisoes.json

# Envio real, somente depois da homologacao
.\venv\Scripts\python.exe -m scripts.affiliate_publish --confirm
```

O comando de publicacao causa efeito real. O worker comum respeita
`AFFILIATE_AUTO_PUBLISH=false` e nao envia mensagens.

## Codex com baixo consumo de tokens

A skill versionada em `skills/affiliate-review/SKILL.md` recebe somente lotes
compactos. Se o comando de pendencias retornar `EMPTY`, a execucao termina sem
analise adicional. O agente nunca precisa ler `.env`, banco bruto, QR code ou
historico do WhatsApp.

## Testes

```powershell
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m unittest discover -v
```

Os testes usam mocks e arquivos temporarios. Eles nao enviam WhatsApp.

Veja [Arquitetura](ARCHITECTURE.md), [Configuracao](docs/CONFIGURATION.md),
[Evolution API](docs/EVOLUTION_SETUP.md), [Testes](docs/TESTING.md) e
[Roadmap](docs/ROADMAP.md).
