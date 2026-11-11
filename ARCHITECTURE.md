# Arquitetura

```text
WhatsApp (grupo de origem)
        |
Evolution API -- MESSAGES_UPSERT --> FastAPI
                                       |
                              filtro pelo JID exato
                                       |
                                    SQLite
                                       |
                         resolver e validar links
                                       |
                      conversao + revisao compacta
                                       |
                         limites e deduplicacao
                                       |
Evolution API <-- sendText -------- grupo de destino
```

## Camadas

- `automation_whats/clients/evolution`: chamadas HTTP da Evolution API;
- `automation_whats/affiliate`: regras, SQLite, parser, resolvedor e worker;
- `automation_whats/webhooks`: entrada FastAPI e autenticacao do webhook;
- `scripts`: comandos operacionais;
- `skills/affiliate-review`: contrato de revisao para Codex/ChatGPT Work;
- `tests`: testes isolados, sem servicos reais.

PostgreSQL e Redis continuam exclusivos da Evolution API. O estado da
automacao Python fica em `data/affiliate.sqlite3`.

## Estados da oferta

```text
RECEIVED -> NEEDS_CONVERSION -> NEEDS_REVIEW -> APPROVED -> SENT
    |               |                |
    +------------> RETRY          REJECTED
                    |
                QUARANTINED
```

## Invariantes

- o grupo e identificado por JID, nunca pelo nome exibido;
- origem e destino precisam ser grupos diferentes;
- `fromMe=true` e outros eventos sao ignorados;
- `(instance, message_id)` e unico;
- toda URL e validada antes e depois da conversao;
- publicacao exige link afiliado e estado `APPROVED`;
- IA nao recebe segredos nem publica diretamente;
- publicacao automatica inicia desligada.

## Limites atuais

- conversao do Mercado Livre usa associacao manual do link validado;
- Shopee permanece desativada ate a liberacao da integracao;
- a imagem recebida ainda nao e baixada/republicada;
- o worker precisa ser chamado por tarefa externa ou supervisor;
- o FastAPI continua fora do Docker Compose.
