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

## Testar a prévia do link

O envio de texto já solicita `linkPreview=true`. Para diagnosticar a ausência da
miniatura, cole no WhatsApp o mesmo link de afiliado que o worker publicou e
espere a prévia no editor antes de enviar. Se a miniatura aparecer na composição
manual, compare com o envio da automação em um grupo de teste. A Evolution usa
seu próprio mecanismo de geração e a disponibilidade da prévia pode variar.
No diagnóstico local de 2026-11-11, um link curto do Mercado Livre retornou
HTTP 403 de dentro do container, e o Baileys não gerou a prévia. Esse teste
fez apenas a leitura pública do link, sem publicar no WhatsApp.
Um envio real autorizado com somente esse link e `linkPreview=true` foi aceito
pela Evolution, mas a resposta não incluiu título nem miniatura de prévia.

O Evolution GO de teste usa a porta local 4000. O GO 0.7.2 baixou uma versão
atual do WhatsApp Web, mas recebeu `405 Client outdated` ao tentar conectar com
a versão compilada. A correção proposta em [evolution-go#228](https://github.com/evolution-foundation/evolution-go/issues/228)
está preparada em `poc/evolution_go_preview/Dockerfile`. A primeira compilação
foi interrompida quando o Docker Desktop reiniciou. A imagem corrigida ainda
precisa ser compilada e validada antes de trocar o container de teste.

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

Para executar continuamente no terminal, use `scripts.affiliate_worker --watch`
com a Evolution ativa. Esse modo inicia o receptor, converte e publica até
Ctrl+C. Veja a configuração do perfil no [README](../README.md#modo-contínuo-no-windows).

Para rodar por cron ou timer:

1. valide com grupos de homologação;
2. confirme fuso e dia de envio;
3. impeça execuções simultâneas;
4. capture stdout/stderr e alerte em falha;
5. mantenha uma forma simples de desabilitar o agendamento.

Comando para uma rodada segura do worker:

```bash
/opt/affiliate-whats/venv/bin/python -m scripts.affiliate_worker
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

### Oferta não entra na fila

Confira `MESSAGES_UPSERT`, `fromMe=false`, os JIDs exatos dos grupos de origem,
`AFFILIATE_ENABLED` e se o ID da mensagem ja existe.

## Evidência mínima para incidentes

Registre horário/fuso, commit, ambiente, comando, status HTTP sanitizado, trecho
de log e serviços afetados. Nunca cole `.env`, QR code, tokens, chaves ou dados
pessoais completos.
