# Automation Whats

Automação em Python para os fluxos de mantenedores do **We Care**. O projeto
integra Google Sheets, Google Forms e WhatsApp por meio da Evolution API.

## O que o projeto faz

| Fluxo | Entrada | Resultado |
|---|---|---|
| Boas-vindas | `POST /webhooks/google-form/mantenedor` | Envia mensagem/imagem ao novo mantenedor e avisa administradores |
| Lembrete mensal | Aba `mantenedores` do Google Sheets | Envia lembrete, chave Pix e aviso administrativo |
| Retomada | Aba `antigos_mantenedores` | Envia convite para antigos mantenedores |
| Resposta de retomada | `POST /webhooks/evolution` | Aceita `SIM 50`, evita duplicidade e inclui a pessoa na aba ativa |

O servidor HTTP é FastAPI/Uvicorn. A Evolution API, o PostgreSQL e o Redis são
executados com Docker Compose. Em produção, o processo Python é executado
separadamente; veja [Produção](docs/PRODUCTION.md).

## Pré-requisitos

- Python 3.12 (versão usada nas validações atuais);
- Docker Desktop no Windows ou Docker Engine + Compose Plugin no Linux;
- uma instância conectada na Evolution API;
- uma planilha Google com as abas `mantenedores` e `antigos_mantenedores`;
- uma credencial OAuth para desenvolvimento ou service account para produção.

## Início rápido local — Windows PowerShell

Execute os comandos a partir da raiz do repositório.

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Edite `.env` e, no mínimo, configure:

```env
AUTHENTICATION_API_KEY=uma-chave-local-forte
EVO_INSTANCE_NAME=wecare
EVO_PHONE_LOGGER=5571999999999
EVO_TEST_PHONE=5571999999999
GOOGLE_AUTH_MODE=oauth
GOOGLE_OAUTH_CLIENT_SECRET_FILE=credentials/google-oauth-client-secret.json
GOOGLE_SPREADSHEET_ID=ID_DA_SUA_PLANILHA
```

Não versione `.env`, tokens ou arquivos JSON de credenciais.

Suba a infraestrutura local:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

Acesse o Manager em <http://localhost:8080/manager>, crie/conecte a instância
definida em `EVO_INSTANCE_NAME` e confirme que o WhatsApp está conectado.

Em outro terminal, inicie o receptor de webhooks:

```powershell
.\venv\Scripts\python.exe -m automation_whats.webhooks.server
```

Confirme a aplicação Python:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Configure a Evolution API para entregar eventos ao servidor local:

```powershell
.\venv\Scripts\python.exe -m scripts.configure_webhook
```

O `WEBHOOK_URL` local deve ser
`http://host.docker.internal:8000/webhooks/evolution`, pois a Evolution API
roda no Docker e o FastAPI roda no host.

## Início rápido local — Linux/macOS

```bash
test -e .env || cp .env.example .env
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
./venv/bin/python -m automation_whats.webhooks.server
```

Em Linux, `host.docker.internal` pode exigir `host-gateway`. Se não resolver,
use uma URL acessível pelo container ou coloque o receptor em uma rede Docker.

## Testes

Os testes automatizados usam mocks e não enviam mensagens nem alteram a
planilha:

```powershell
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m unittest discover -v
```

Para integrações reais com números e planilha de homologação, siga
[Testes e homologação](docs/TESTING.md). Os scripts `send_*` e `process_*`
causam efeitos reais quando apontados para serviços reais.

## Comandos principais

```powershell
# Envio controlado de texto e mídia
.\venv\Scripts\python.exe -m scripts.send_text
.\venv\Scripts\python.exe -m scripts.send_media

# Lote de mantenedores ativos
.\venv\Scripts\python.exe -m scripts.process_mantenedores_sheet

# Lote de antigos mantenedores
.\venv\Scripts\python.exe -m scripts.process_antigos_mantenedores_sheet

# Entrada equivalente ao lote mensal
.\venv\Scripts\python.exe -m automation_whats
```

## Documentação

- [Arquitetura e fluxos](ARCHITECTURE.md)
- [Configuração e variáveis](docs/CONFIGURATION.md)
- [Docker e ambientes](DOCKER.md)
- [Testes e homologação](docs/TESTING.md)
- [Implantação em produção](docs/PRODUCTION.md)
- [Operação, backup e incidentes](docs/OPERATIONS.md)
- [Etapas e roadmap](docs/ROADMAP.md)
- [Google Sheets](GOOGLE_SHEETS.md)
- [Google Forms](GOOGLE_FORMS.md)
- [Como contribuir](CONTRIBUTING.md)
- [Contexto curto para IA](AI_CONTEXT.md)
- [Instruções automáticas para agentes](AGENTS.md)

## Estado e limites atuais

- O Compose base contém Evolution API, PostgreSQL e Redis.
- O FastAPI ainda não possui imagem Docker própria; em produção ele deve ser
  mantido por `systemd` ou outro supervisor.
- Não há pipeline CI/CD, migrations próprias ou banco de dados Python.
- Os lotes são iniciados manualmente; agende-os somente após homologação.
- Em produção, configure o segredo do webhook e publique somente por HTTPS.
