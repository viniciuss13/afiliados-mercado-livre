# Implantação em produção

Desenho suportado pelo repositório atual em uma VPS Linux:

- Evolution API, PostgreSQL e Redis em Docker Compose;
- FastAPI em virtualenv, mantido por `systemd`;
- reverse proxy terminando HTTPS;
- Google Sheets autenticado por service account.

O Compose atual não contém o processo Python. Não execute apenas o Compose e
presuma que os webhooks estão ativos.

## 1. Preparar o servidor

Instale Git, Python 3.12, Docker Engine, Compose Plugin, Nginx e um cliente ACME
como Certbot. Crie um usuário de serviço e mantenha o repositório em um caminho
estável, por exemplo `/opt/automation_whats`.

```bash
cd /opt/automation_whats
python3.12 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
test -e .env || cp .env.example .env
chmod 600 .env credentials/google-service-account.json
```

## 2. Configurar produção

Use domínios separados, por exemplo:

- `evolution.exemplo.com` -> `127.0.0.1:8080`;
- `webhooks.exemplo.com` -> `127.0.0.1:8000`.

Configuração mínima conceitual:

```env
SERVER_URL=https://evolution.exemplo.com
EVO_BASE_URL=http://127.0.0.1:8080
AUTHENTICATION_API_KEY=SEGREDO_FORTE_E_UNICO
EVO_INSTANCE_NAME=wecare

WEBHOOK_HOST=127.0.0.1
WEBHOOK_PORT=8000
WEBHOOK_URL=https://webhooks.exemplo.com/webhooks/evolution
GOOGLE_FORM_WEBHOOK_URL=https://webhooks.exemplo.com/webhooks/google-form/mantenedor
WEBHOOK_SECRET=OUTRO_SEGREDO_FORTE

GOOGLE_AUTH_MODE=service_account
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google-service-account.json
GOOGLE_SPREADSHEET_ID=ID_DE_PRODUCAO

POSTGRES_USER=evolution
POSTGRES_PASSWORD=SEGREDO_POSTGRES
REDIS_PASSWORD=SEGREDO_REDIS
CORS_ORIGIN=https://evolution.exemplo.com
EVOLUTION_API_BIND=127.0.0.1
```

Não copie valores de exemplo para produção. Compartilhe a planilha com o e-mail
da service account como editor.

## 3. Subir a Evolution API

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

`config` deve falhar se segredos obrigatórios estiverem ausentes. PostgreSQL e
Redis não são publicados no host em produção.

## 4. Manter o FastAPI com systemd

Crie `/etc/systemd/system/automation-whats.service`, ajustando usuário/caminho:

```ini
[Unit]
Description=Automation Whats webhooks
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
User=automation-whats
Group=automation-whats
WorkingDirectory=/opt/automation_whats
EnvironmentFile=/opt/automation_whats/.env
ExecStart=/opt/automation_whats/venv/bin/python -m automation_whats.webhooks.server
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now automation-whats
sudo systemctl status automation-whats
curl --fail http://127.0.0.1:8000/health
```

## 5. Publicar com HTTPS

Encaminhe o domínio Evolution para `127.0.0.1:8080` e o domínio de webhooks
para `127.0.0.1:8000`. Preserve `Host`, `X-Forwarded-For` e
`X-Forwarded-Proto`, limite o corpo e habilite TLS.

Não publique PostgreSQL/Redis. Restrinja o Manager por autenticação/rede sempre
que possível. Depois de emitir os certificados:

```bash
curl --fail https://webhooks.exemplo.com/health
```

## 6. Conectar os produtores

1. Conecte a instância WhatsApp no Manager.
2. Execute `./venv/bin/python -m scripts.configure_webhook`.
3. Confirme que a URL configurada é HTTPS pública.
4. Atualize o Apps Script com a URL de Forms e o mesmo segredo.
5. Faça os testes controlados de [TESTING.md](TESTING.md).

## 7. Atualização segura

Mantenha `.env`, credenciais e backups fora do diretório de release.

```bash
git pull --ff-only
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m unittest discover -v
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
sudo systemctl restart automation-whats
curl --fail https://webhooks.exemplo.com/health
```

Em falha, volte ao release anterior, reinstale suas dependências fixadas,
reaplique o Compose e reinicie o serviço. Não remova volumes no rollback.

## 8. Checklist de aceite

- DNS e TLS válidos;
- somente portas necessárias expostas;
- segredos distintos para API, webhook, PostgreSQL e Redis;
- service account limitada à planilha necessária;
- containers e serviço Python reiniciando após reboot;
- health, texto, mídia, Forms e `SIM 50` validados;
- logs sem chaves, tokens ou dados pessoais completos;
- backup automatizado e restauração ensaiada.
