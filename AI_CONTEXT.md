# Contexto para IA

Resumo canônico e curto para evitar redescoberta do repositório.

## Leia nesta ordem

1. Este arquivo.
2. `README.md` para comandos e onboarding.
3. Apenas o documento ligado à tarefa:
   - arquitetura: `ARCHITECTURE.md`;
   - configuração: `docs/CONFIGURATION.md` e `.env.example`;
   - Docker: `DOCKER.md`;
   - testes: `docs/TESTING.md`;
   - produção: `docs/PRODUCTION.md`;
   - incidentes: `docs/OPERATIONS.md`;
   - Google: `GOOGLE_SHEETS.md` ou `GOOGLE_FORMS.md`.

Não leia `.env`, `credentials/`, `venv/`, `.git/` ou `__pycache__/` para mapear
o projeto. Eles contêm segredos, dependências instaladas ou ruído.

## Estado atual (2026-09-14)

- Python 3.12; dependências fixadas em `requirements.txt`.
- 37 testes unitários aprovados e `pip check` sem conflitos na última validação.
- Compose: Evolution API v2.3.7, PostgreSQL 15 e Redis 7.4.
- Dev usa `docker-compose.yml` + `docker-compose.dev.yml`.
- Produção usa `docker-compose.yml` + `docker-compose.prod.yml`.
- Manager local: `http://localhost:8080/manager`.
- FastAPI local: `http://localhost:8000`; health: `/health`.
- O FastAPI não está no Compose; produção documentada com `systemd`.

Verifique novamente fatos sujeitos a mudança antes de afirmá-los como atuais.

## Mapa de decisão

- Evolution API: `automation_whats/clients/evolution/`.
- Google Sheets/auth: `automation_whats/clients/google_sheets/`.
- Mensagens/regras: `automation_whats/services/`.
- HTTP/eventos: `automation_whats/webhooks/`.
- Operações reais: `scripts/`.
- Regressões: `tests/`.

## Invariantes

- O Python não acessa PostgreSQL/Redis; eles pertencem à Evolution API.
- Forms dispara boas-vindas, mas a linha é gravada pela planilha vinculada.
- `SIM valor` escreve em `mantenedores`; a consulta prévia não é transação.
- `fromMe=true` é ignorado para não processar as próprias mensagens.
- Testes automatizados não enviam WhatsApp nem escrevem no Google.
- Scripts `send_*`, `process_*` e POST do Forms podem causar efeitos reais.
- Nunca exponha `.env`, tokens, JSON de credencial ou dados pessoais.

## Fluxo de trabalho esperado

1. Rode `git status --short` e leia os arquivos centrais da área.
2. Faça uma alteração pequena e preserve mudanças existentes.
3. Rode teste focado e depois a suíte completa.
4. Para Docker, valide `docker compose ... config` e o estado real.
5. Para integrações, separe mock, homologação e produção.
6. Atualize documentação, estado, riscos e próximos passos no mesmo ciclo.

## Validação segura

```powershell
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m unittest discover -v
docker compose -f docker-compose.yml -f docker-compose.dev.yml config
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

Não rode scripts de envio/lote sem confirmar ambiente, planilha e destinatário.

## Lacunas conhecidas

- sem CI/CD, fila, retry persistente, métricas ou tracing;
- sem container do FastAPI e sem scheduler embutido;
- sem idempotência atômica para respostas concorrentes;
- aceite de produção depende de VPS, DNS, TLS, credenciais e smoke real.

## Skill local

Use `$automation-whats-maintenance`, em
`.agents/skills/automation-whats-maintenance/SKILL.md`, para manutenção,
diagnóstico, testes e operação deste repositório.

