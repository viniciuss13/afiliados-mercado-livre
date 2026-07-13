# Estrutura do Projeto

Este projeto separa integrações externas, regras de negócio e entrada HTTP para manter o código simples de evoluir.

```text
automation_whats/
  main.py
  clients/
    evolution/
      client.py       # Chamadas HTTP para a Evolution API
      settings.py     # Configurações da Evolution API
      schemas.py      # Modelos Pydantic dos payloads
      exceptions.py   # Exceções específicas do client
    google_sheets/
      client.py       # Leitura e escrita no Google Sheets
      settings.py     # Configurações da planilha
      schemas.py      # Modelos das linhas da planilha
  services/
    admin_recipients.py              # Lista de destinatários administrativos
    mantenedor_media.py              # Carregamento da imagem do We Care
    mantenedor_payment_reminder.py   # Lembrete mensal e chave Pix
    mantenedor_reactivation.py       # Retomada de antigos mantenedores
    mantenedor_welcome.py            # Boas-vindas para novos mantenedores
    sheet_former_mantenedor_import.py # Processamento de antigos mantenedores
    sheet_mantenedor_import.py       # Processamento da planilha ativa
  webhooks/
    app.py           # Aplicação FastAPI
    server.py        # Runner Uvicorn
    handlers.py      # Processamento dos eventos recebidos
    schemas.py       # Modelos Pydantic dos eventos

scripts/
  configure_webhook.py                 # Configura webhook na Evolution API
  process_antigos_mantenedores_sheet.py # Envia retomada aos antigos mantenedores
  process_mantenedores_sheet.py         # Envia lembretes mensais
  send_media.py                         # Teste manual de mídia
  send_text.py                          # Teste manual de texto
```

## Regras dos Clients

- Clients sabem apenas conversar com APIs externas.
- Regras de negócio ficam em `services`.
- Configurações são carregadas e validadas com Pydantic.
- Payloads são representados por schemas Pydantic quando fazem parte da borda externa.
- Erros HTTP da Evolution API são convertidos em exceções específicas.
- Testes injetam dependências falsas em vez de chamar serviços reais.

## Fluxos

### Boas-vindas

Recebe um cadastro novo em:

```text
POST /webhooks/google-form/mantenedor
```

Envia mensagem, imagem e notificação administrativa.

### Lembrete Mensal

Lê a aba **mantenedores** e envia lembrete de pagamento:

```powershell
.\venv\Scripts\python.exe -m scripts.process_mantenedores_sheet
```

### Retomada de Antigos Mantenedores

Lê a aba **antigos_mantenedores** e envia convite de retomada:

```powershell
.\venv\Scripts\python.exe -m scripts.process_antigos_mantenedores_sheet
```

Quando a pessoa responde `SIM 50`, o webhook da Evolution API recebe o evento:

```text
POST /webhooks/evolution
```

O handler identifica a resposta e cadastra a pessoa na aba **mantenedores** caso o telefone ainda não exista.

## Endpoints da Evolution API Usados

- `POST /message/sendText/{instance}`
- `POST /message/sendMedia/{instance}`
- `GET /webhook/find/{instance}`
- `POST /webhook/set/{instance}`
