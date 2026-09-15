# Arquitetura

## Visão geral

O projeto separa bordas externas, regras de negócio e entradas operacionais.

```text
Google Forms/Apps Script ----> FastAPI webhooks ----> services ----> Evolution API
                                      |                 |
Evolution API events ----------------+                 +----> Google Sheets

CLI scripts -------------------------> services

Docker Compose: Evolution API <----> PostgreSQL
                       |
                       +------------> Redis
```

O pacote Python **não acessa PostgreSQL nem Redis diretamente**. Eles pertencem
à Evolution API. O estado de mantenedores usado pelo Python está no Sheets.

## Camadas

```text
automation_whats/
  clients/
    evolution/       HTTP, schemas, settings e erros da Evolution API
    google_sheets/   autenticação, leitura e escrita no Google Sheets
  services/          regras de negócio e composição dos clients
  webhooks/          FastAPI, schemas HTTP e handlers
  img/               mídia padrão
  main.py            entrada do lote mensal

scripts/             operações manuais e smoke tests reais
tests/               testes unitários com mocks
```

### Clients

- Traduzem chamadas e respostas dos provedores externos.
- Carregam configuração validada por Pydantic.
- Não decidem regras de mantenedores.
- O client Google usa OAuth local ou service account.

### Services

- Normalizam telefone brasileiro.
- Montam mensagens e mídia.
- Coordenam envio, leitura e escrita.
- Lotes continuam após erro em uma linha e retornam `sent` ou `error`.

### Webhooks

- `GET /health`: verifica o processo FastAPI.
- `POST /webhooks/google-form/mantenedor`: valida e envia boas-vindas.
- `POST /webhooks/evolution`: recebe eventos e processa retomada.
- Com `WEBHOOK_SECRET`, todas as rotas POST exigem o header configurado.

## Fluxos de negócio

### Novo mantenedor

1. Apps Script envia `nome`, `telefone` e `valor`.
2. O schema rejeita payload incompleto com HTTP 422.
3. O telefone é normalizado.
4. O serviço envia imagem/legenda ou texto como fallback.
5. Administradores recebem aviso.

Esse fluxo não escreve na planilha: pressupõe que o Forms já gravou a resposta
na planilha vinculada.

### Lembrete mensal

1. Lê `mantenedores` (`nome`, `telefone`, `valor`).
2. Ignora linhas inválidas.
3. Envia lembrete/mídia, chave Pix separada e aviso administrativo.
4. Uma falha individual não interrompe as próximas linhas.

### Retomada e resposta

1. Lê `antigos_mantenedores` (`nome`, `telefone`) e envia convite.
2. Evolution entrega `MESSAGES_UPSERT` ao webhook.
3. Mensagens `fromMe=true` são ignoradas.
4. `NÃO`/`NAO` retorna `declined`; texto fora do padrão retorna `ignored`.
5. `SIM 50` e variações suportadas extraem o valor.
6. Consulta `mantenedores` para impedir duplicidade.
7. Resolve o nome pelo WhatsApp ou pela aba antiga.
8. Sem nome confiável, bloqueia; caso contrário, adiciona a linha ativa.

## Integrações e contratos

| Integração | Contrato relevante |
|---|---|
| Evolution API | header `apikey`; `sendText`, `sendMedia`, `webhook/find`, `webhook/set` |
| Google Sheets | abas/cabeçalhos reconhecidos; escrita em `A:C` |
| Google Forms | JSON com `nome`, `telefone`, `valor` |
| PostgreSQL/Redis | usados internamente pela Evolution API |

Detalhes: [GOOGLE_FORMS.md](GOOGLE_FORMS.md) e
[GOOGLE_SHEETS.md](GOOGLE_SHEETS.md).

## Invariantes

- Execute módulos a partir da raiz do repositório.
- Telefones são usados somente com dígitos e recebem DDI `55` no formato local.
- A suíte unitária nunca chama serviços reais.
- Nunca registre `.env`, OAuth, chaves ou JSON de service account.
- Mudanças em payload externo exigem teste e documentação correspondentes.

## Limites atuais

- Sem fila, retry persistente ou idempotência distribuída.
- A consulta antes do append não é atômica em eventos concorrentes.
- Logs resumidos em stdout, sem métricas/tracing.
- Agendamento dos lotes fora do código.
- Processo FastAPI fora do Compose.
