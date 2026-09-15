# Docker e ambientes

O Docker executa somente a infraestrutura da Evolution API. O FastAPI Python é
iniciado separadamente.

## Arquivos

- `docker-compose.yml`: serviços e volumes comuns;
- `docker-compose.dev.yml`: publica Evolution, PostgreSQL e Redis em localhost;
- `docker-compose.prod.yml`: exige segredos, protege banco/cache e limita logs.

Sempre informe o arquivo base e exatamente um override.

## Desenvolvimento

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml config
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

Portas locais padrão:

- Evolution/Manager: `127.0.0.1:8080`;
- PostgreSQL: `127.0.0.1:5432`;
- Redis: `127.0.0.1:6379`.

Painel: <http://localhost:8080/manager>.

Para encerrar preservando dados:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

## Produção

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

O override exige `AUTHENTICATION_API_KEY`, `SERVER_URL`, `POSTGRES_PASSWORD`,
`REDIS_PASSWORD` e `CORS_ORIGIN`. PostgreSQL e Redis permanecem internos. A
Evolution fica em `127.0.0.1:8080` por padrão, atrás do proxy.

Veja [Produção](docs/PRODUCTION.md) para FastAPI, `systemd`, HTTPS e aceite.

## Logs e saúde

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs --tail 100 evolution-api
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs --tail 100 postgres redis
```

O Compose verifica PostgreSQL e Redis. O FastAPI tem healthcheck separado em
`http://localhost:8000/health`.

## Persistência

Volumes: `evolution_instances`, `postgres_data` e `redis_data`.

Não use `docker compose down --volumes` em produção: essa opção apaga dados.
Consulte [Operação](docs/OPERATIONS.md) para backup e incidentes.
