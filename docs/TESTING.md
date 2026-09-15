# Testes e homologação

## 1. Testes automatizados seguros

```powershell
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m unittest discover -v
```

A suíte usa mocks para Evolution API e Google Sheets. Ela valida clients,
schemas, telefone, lotes, FastAPI e retomada sem enviar WhatsApp ou alterar
dados externos.

## 2. Smoke local sem envio

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
.\venv\Scripts\python.exe -m automation_whats.webhooks.server
```

Em outro terminal:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
Invoke-RestMethod http://localhost:8000/health
```

Resultado esperado: `{"status":"ok"}`.

## 3. Homologação das integrações reais

Use instância WhatsApp, números e planilha exclusivos de homologação. As ações
abaixo têm efeitos reais.

1. Abra <http://localhost:8080/manager> e confirme a instância conectada.
2. Configure `EVO_TEST_PHONE` com um número controlado.
3. Rode `scripts.send_text` e confirme recebimento.
4. Rode `scripts.send_media` e confirme imagem, legenda e MIME type.
5. Configure o webhook e confira-o no Manager.
6. Envie um payload do Forms e confirme boas-vindas.
7. Use uma única linha controlada em cada aba ao testar lotes.
8. Responda `SIM 50` e confira inclusão única em `mantenedores`.
9. Reenvie a resposta e confirme `already_registered`.

Comandos de efeito real:

```powershell
.\venv\Scripts\python.exe -m scripts.send_text
.\venv\Scripts\python.exe -m scripts.send_media
.\venv\Scripts\python.exe -m scripts.configure_webhook
.\venv\Scripts\python.exe -m scripts.process_mantenedores_sheet
.\venv\Scripts\python.exe -m scripts.process_antigos_mantenedores_sheet
```

## 4. POST manual do Google Forms

Este comando envia uma mensagem real quando conectado a uma Evolution real:

```powershell
$headers = @{}
if ($env:WEBHOOK_SECRET) { $headers['X-Webhook-Secret'] = $env:WEBHOOK_SECRET }
$body = @{ nome='Teste Homologacao'; telefone=$env:EVO_TEST_PHONE; valor='1,00' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/webhooks/google-form/mantenedor -Headers $headers -ContentType 'application/json' -Body $body
```

## 5. Critério antes de produção

- suíte unitária verde e `pip check` sem conflitos;
- três serviços Docker ativos/saudáveis;
- `/health` respondendo e instância conectada;
- texto e mídia confirmados em homologação;
- service account lendo e escrevendo a planilha de homologação;
- segredo inválido recebendo HTTP 401;
- webhook público com HTTPS;
- backup e rollback testados.

