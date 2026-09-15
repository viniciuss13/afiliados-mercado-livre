# Configuração

Use `.env.example` como catálogo e crie um `.env` por ambiente. Nunca reutilize
segredos de desenvolvimento em produção.

## Evolution API e mensagens

| Variável | Obrigatória | Uso |
|---|---:|---|
| `EVO_BASE_URL` | sim | URL acessada pelo Python, como `http://localhost:8080` |
| `EVO_INSTANCE_NAME` | sim | nome exato da instância conectada |
| `AUTHENTICATION_API_KEY` | sim | header `apikey` e autenticação da Evolution API |
| `EVO_TIMEOUT` | não | timeout HTTP; padrão `30` segundos |
| `EVO_REQUEST_ORIGIN` | não | header Origin quando exigido pelo ambiente |
| `EVO_PHONE_LOGGER` | recomendado | fallback de destinatário/administrador |
| `EVO_ADMIN_PHONES` | não | administradores separados por vírgula |
| `EVO_TEST_PHONE` | para smoke | destino explícito do teste de texto |
| `EVO_TEST_MEDIA_PHONE` | para smoke | destino explícito do teste de mídia |

Use números com DDI e DDD, somente dígitos, como `5571999999999`. Os scripts
também normalizam máscaras brasileiras.

## Webhooks

| Variável | Obrigatória | Uso |
|---|---:|---|
| `WEBHOOK_HOST` | não | bind do Uvicorn; padrão `0.0.0.0` |
| `WEBHOOK_PORT` | não | porta do Uvicorn; padrão `8000` |
| `WEBHOOK_URL` | para configurar | destino que a Evolution API chamará |
| `GOOGLE_FORM_WEBHOOK_URL` | referência | destino usado pelo Apps Script |
| `WEBHOOK_EVENTS` | não | padrão `MESSAGES_UPSERT` |
| `WEBHOOK_SECRET` | sim em produção | segredo compartilhado das rotas POST |
| `WEBHOOK_SECRET_HEADER` | não | padrão `X-Webhook-Secret` |

Em produção, as URLs devem usar HTTPS público. O `/health` não exige segredo;
as rotas POST exigem quando `WEBHOOK_SECRET` está configurado.

## Google Sheets

| Variável | Obrigatória | Uso |
|---|---:|---|
| `GOOGLE_AUTH_MODE` | sim | `oauth` local ou `service_account` no servidor |
| `GOOGLE_OAUTH_CLIENT_SECRET_FILE` | em OAuth | JSON do cliente OAuth |
| `GOOGLE_OAUTH_TOKEN_FILE` | não | token gerado em `credentials/` |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | em produção | JSON da service account |
| `GOOGLE_SPREADSHEET_ID` | recomendado | ID estável da planilha |
| `GOOGLE_SPREADSHEET_NAME` | alternativa | busca pelo nome quando não há ID |
| `GOOGLE_WORKSHEET_NAME` | não | padrão `mantenedores` |
| `GOOGLE_FORMER_WORKSHEET_NAME` | não | padrão `antigos_mantenedores` |
| `GOOGLE_SHEETS_RANGE` | não | padrão `A:Z` |

Em produção, compartilhe a planilha com o e-mail da service account como
**editor**, pois respostas positivas escrevem na aba ativa.

## Mídia

Defina `WECARE_WELCOME_IMAGE_URL` para uma URL pública ou deixe vazio para usar
`WECARE_WELCOME_IMAGE_PATH`. O padrão é
`automation_whats/img/we_care.jpeg`.

## Infraestrutura Docker

As variáveis `EVOLUTION_API_*`, `POSTGRES_*`, `REDIS_*`, `DATABASE_*`,
`CACHE_*`, `CORS_*` e `LOG_LEVEL` pertencem à Evolution API/Compose. Em
produção, use segredos fortes e distintos para API, banco, Redis e webhook.

## Validação sem revelar segredos

```powershell
.\venv\Scripts\python.exe -c "from automation_whats.clients.evolution.settings import EvolutionSettings; s=EvolutionSettings.from_env(); print(s.base_url, s.instance_name)"
.\venv\Scripts\python.exe -c "from automation_whats.clients.google_sheets.settings import GoogleSheetsSettings; print(GoogleSheetsSettings.from_env().auth_mode)"
```

Não imprima o conteúdo de `.env` em logs, issues ou conversas com IA.

