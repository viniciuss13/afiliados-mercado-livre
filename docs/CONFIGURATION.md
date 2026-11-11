# Configuracao

## Evolution API

| Variavel | Uso |
|---|---|
| `EVO_BASE_URL` | URL local da Evolution API |
| `EVO_INSTANCE_NAME` | instancia conectada ao numero comercial |
| `AUTHENTICATION_API_KEY` | autenticacao server-to-server |
| `WEBHOOK_URL` | receptor `/webhooks/evolution` |
| `WEBHOOK_SECRET` | segredo recomendado para o webhook |

O passo a passo de instalacao, QR Code, webhook e grupos esta em
[`EVOLUTION_SETUP.md`](EVOLUTION_SETUP.md).

## Afiliados

| Variavel | Padrao | Uso |
|---|---:|---|
| `AFFILIATE_ENABLED` | `false` | ativa a captura do grupo |
| `AFFILIATE_SOURCE_GROUP_JIDS` | vazio | grupos monitorados, separados por virgula |
| `AFFILIATE_DESTINATION_GROUP_JID` | vazio | grupo de publicacao |
| `AFFILIATE_DB_PATH` | `data/affiliate.sqlite3` | fila local |
| `AFFILIATE_MERCADO_LIVRE_ENABLED` | `true` | resolve Mercado Livre |
| `AFFILIATE_SHOPEE_ENABLED` | `false` | ativa Shopee depois da liberacao |
| `AFFILIATE_REVIEW_REQUIRED` | `true` | exige decisao antes do envio |
| `AFFILIATE_AUTO_PUBLISH` | `false` | permite envio no worker |
| `AFFILIATE_DEDUPE_DAYS` | `7` | janela por produto |
| `AFFILIATE_MAX_RETRIES` | `3` | falhas antes da quarentena |
| `AFFILIATE_TIMEZONE` | `America/Bahia` | limite diario no fuso local |
| `AFFILIATE_MIN_SEND_INTERVAL_SECONDS` | `90` | pausa entre posts |
| `AFFILIATE_DAILY_LIMIT` | `40` | limite diario |
| `AFFILIATE_MERCADO_LIVRE_MARKER` | vazio | marcador esperado no link final |
| `AFFILIATE_SHOPEE_MARKER` | vazio | marcador esperado no link final |
| `AFFILIATE_MERCADO_LIVRE_PLAYWRIGHT_ENABLED` | `false` | gera links do Mercado Livre no worker |
| `AFFILIATE_PLAYWRIGHT_HEADLESS` | `true` | executa o navegador sem janela depois da homologacao |
| `AFFILIATE_PLAYWRIGHT_BROWSER` | `edge` | escolhe o perfil dedicado da POC (`edge` ou `chrome`) |
| `AFFILIATE_PLAYWRIGHT_CONVERSION_LIMIT` | `1` | conversoes por rodada do worker |

Nunca versione os valores reais dos JIDs, marcadores ou segredos.
