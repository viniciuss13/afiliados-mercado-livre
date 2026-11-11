# Producao

## Componentes

- Evolution API, PostgreSQL e Redis em Docker Compose;
- FastAPI executado por supervisor fora do Compose;
- worker chamado periodicamente pelo Agendador de Tarefas ou supervisor;
- SQLite em diretorio persistente com backup;
- webhook publicado com HTTPS e segredo configurado.

## Controles iniciais

Mantenha `AFFILIATE_AUTO_PUBLISH=false` ate concluir a homologacao. Configure
JIDs exatos, limite diario, intervalo entre mensagens e segredo do webhook.

O numero conectado precisa participar dos dois grupos. Ele precisa ser
administrador do destino apenas quando o grupo restringe publicacoes a
administradores.

## Processos

Servidor HTTP:

```bash
/opt/affiliate-whats/venv/bin/python -m automation_whats.webhooks.server
```

Rodada do worker:

```bash
/opt/affiliate-whats/venv/bin/python -m scripts.affiliate_worker
```

Nao exponha PostgreSQL ou Redis. Restrinja o Manager da Evolution por rede e
autenticacao. Proteja `.env`, o SQLite e qualquer perfil autenticado usado
futuramente pelo gerador de links.
