# Ambientes Docker

A configuração do Docker Compose está separada por ambiente.

## Desenvolvimento

A Evolution API está configurada para usar a imagem:

```env
EVOLUTION_API_IMAGE=evoapicloud/evolution-api:v2.3.7
```

Essa versão usa o repositório atual da Evolution API no Docker Hub e atende ao
fluxo do projeto para envio de mensagens de texto e mídia.

Use o arquivo base junto com o override de desenvolvimento:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

No ambiente de desenvolvimento, os serviços são publicados apenas em localhost:

- Evolution API: `127.0.0.1:8080`
- PostgreSQL: `127.0.0.1:5432`
- Redis: `127.0.0.1:6379`

## Produção

Use o arquivo base junto com o override de produção:

```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Variáveis obrigatórias em produção:

```env
AUTHENTICATION_API_KEY=
SERVER_URL=
POSTGRES_PASSWORD=
REDIS_PASSWORD=
CORS_ORIGIN=
```

Em produção, PostgreSQL e Redis não são publicados no host. Apenas a Evolution
API é publicada, por padrão vinculada a `127.0.0.1`, para ficar atrás de um
reverse proxy.

Para publicar a API diretamente, defina:

```env
EVOLUTION_API_BIND=0.0.0.0
EVOLUTION_API_PORT=8080
```

Em uma implantação pública real, prefira usar um reverse proxy com HTTPS.

## Testes manuais

Execute os scripts manuais como módulos a partir da raiz do projeto:

```powershell
.\venv\Scripts\python.exe -m scripts.send_text
.\venv\Scripts\python.exe -m scripts.send_media
.\venv\Scripts\python.exe -m scripts.configure_webhook
```
