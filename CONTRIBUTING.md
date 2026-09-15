# Como contribuir

## Antes de alterar

1. Leia `README.md` e `AI_CONTEXT.md`.
2. Consulte o documento específico da área.
3. Rode `git status --short` e preserve mudanças que não são suas.
4. Não abra `.env` ou credenciais sem necessidade explícita.

## Regras do código

- Clients encapsulam provedores; services contêm regras de negócio; webhooks
  validam e encaminham.
- Injete clients falsos nos testes. Testes unitários não acessam rede.
- Preserve a normalização de telefones e a prevenção de duplicidade.
- Execute módulos a partir da raiz com `python -m ...`.
- Mantenha compatibilidade com Python 3.12 até uma mudança deliberada.

## Validação mínima

```powershell
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m unittest discover -v
```

Mudanças em Docker exigem `docker compose ... config`. Mudanças em fluxos
externos exigem smoke em homologação, nunca diretamente com toda a base real.

## Documentação viva

Na mesma alteração:

- atualize `README.md` se comandos ou onboarding mudarem;
- atualize `ARCHITECTURE.md` se responsabilidades/fluxos mudarem;
- atualize `docs/CONFIGURATION.md` e `.env.example` em novas variáveis;
- atualize `docs/TESTING.md` para novos critérios;
- atualize `AI_CONTEXT.md` e `docs/ROADMAP.md` quando estado, risco ou próximos
  passos mudarem.

## Segurança

Nunca versione `.env`, credenciais Google, tokens OAuth, chaves da Evolution,
QR codes, dumps, logs pessoais ou números reais usados em teste.

