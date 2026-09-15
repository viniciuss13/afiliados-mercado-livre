# Instruções para agentes

Leia primeiro `AI_CONTEXT.md`; ele contém o mapa, invariantes, riscos e a ordem
de leitura econômica. Depois abra somente o documento relacionado à tarefa.

- Preserve alterações existentes e comece por `git status --short`.
- Não leia nem exponha `.env`, `credentials/`, tokens, QR codes ou dados reais.
- Testes unitários não podem acessar WhatsApp ou Google reais.
- Scripts de envio/lote e configuração de webhook têm efeitos externos.
- Rode `pip check` e a suíte completa após mudanças Python.
- Valide ambos os arquivos Compose relevantes após mudanças de infraestrutura.
- Atualize o documento afetado e `AI_CONTEXT.md` no mesmo ciclo.

Para Codex, use também a skill local `$automation-whats-maintenance`.
