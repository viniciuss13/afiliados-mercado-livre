# Etapas e roadmap

Este documento separa capacidade existente de trabalho futuro. Itens futuros
não estão implementados nem autorizados automaticamente.

## Etapa 1 — Base local (concluída)

- client Evolution para texto, mídia e webhook;
- Compose com Evolution API, PostgreSQL e Redis;
- FastAPI com healthcheck e duas rotas;
- `.env` validado e testes unitários principais.

## Etapa 2 — Fluxos Google/mantenedores (concluída)

- leitura das abas ativa e antiga;
- OAuth local e service account;
- boas-vindas, lembrete mensal e retomada;
- `SIM valor`/`NÃO` e prevenção básica de duplicidade.

## Etapa 3 — Preparação operacional (documentada)

- segredos de produção;
- VPS, `systemd`, reverse proxy e TLS;
- ambientes de homologação e produção;
- backup, rollback, monitoramento e smoke real.

## P0 — antes de produção

- executar o checklist de homologação;
- monitorar externamente o `/health`;
- automatizar backup do PostgreSQL e testar restauração;
- restringir o Manager;
- definir responsável e janela dos lotes.

## P1 — confiabilidade

- idempotência forte para webhooks concorrentes;
- retry com backoff/fila;
- correlação de logs sem dados pessoais;
- testes de integração em homologação.

## P2 — entrega e manutenção

- containerizar o FastAPI ou consolidar a opção `systemd`;
- adicionar CI para `pip check` e `unittest`;
- separar dependências diretas de lock reproduzível;
- automatizar release e rollback.

Produção só está concluída quando infraestrutura, Python, HTTPS, credenciais,
webhooks, envio, escrita na planilha, backup e monitoramento forem validados no
ambiente real. Testes unitários isolados não substituem esse aceite.

