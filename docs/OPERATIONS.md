# Operação e incidentes

## Verificações

Desenvolvimento:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs --tail 100 evolution-api
Invoke-RestMethod http://localhost:8000/health
```

Produção:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
systemctl status automation-whats
journalctl -u automation-whats --since today
curl --fail https://webhooks.exemplo.com/health
```

## Iniciar, parar e reiniciar

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker compose -f docker-compose.yml -f docker-compose.dev.yml stop
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart evolution-api
```

Em produção, use o override `prod` e reinicie o Python com
`sudo systemctl restart automation-whats`.

`docker compose down` preserva volumes sem `--volumes`. Nunca use
`down --volumes` em produção sem backup e solicitação explícita: ele apaga os
dados persistentes.

## Backups

Os volumes persistentes são `postgres_data`, `redis_data` e
`evolution_instances`. O PostgreSQL é o item mais crítico.

Exemplo de dump lógico em diretório protegido:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T postgres \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > evolution-$(date +%F).dump
```

Mantenha cópias seguras de `.env`, service account e proxy fora do Git. Teste
a restauração em ambiente isolado; ela é destrutiva e exige procedimento e
aprovação próprios.

## Agendamento dos lotes

O projeto não contém scheduler. Antes de criar cron/timer:

1. valide contra planilha e números de homologação;
2. confirme fuso e dia de envio;
3. impeça execuções simultâneas;
4. capture stdout/stderr e alerte em falha;
5. mantenha uma forma simples de desabilitar o agendamento.

Comando para um timer externo:

```bash
/opt/automation_whats/venv/bin/python -m scripts.process_mantenedores_sheet
```

## Diagnóstico rápido

### Manager não abre

Confirme Docker ativo, `compose ps`, logs dos três serviços e conflito na porta
8080. No Windows, aguarde o Docker Desktop indicar estado `running`.

### FastAPI não responde

Rode o módulo manualmente, confira bind/porta/firewall e, em produção, consulte
`journalctl -u automation-whats`.

### Evolution retorna 401

Confirme que `AUTHENTICATION_API_KEY` coincide no Compose e no Python. Não
imprima a chave; compare de forma controlada.

### Webhook retorna 401

Confira segredo, nome do header e o header enviado pela Evolution/Apps Script.

### Google retorna 403

Confira APIs habilitadas, scopes, credencial e compartilhamento da planilha.
Em OAuth com escopo antigo, gere novamente o token.

### `SIM 50` não cadastra

Confira `MESSAGES_UPSERT`, `fromMe=false`, telefone, permissão de escrita, nomes
das abas e duplicidade existente.

## Evidência mínima para incidentes

Registre horário/fuso, commit, ambiente, comando, status HTTP sanitizado, trecho
de log e serviços afetados. Nunca cole `.env`, QR code, tokens, chaves ou dados
pessoais completos.
