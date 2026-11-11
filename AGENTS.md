# Instruções para agentes

Leia primeiro `AI_CONTEXT.md`; ele contém o mapa, invariantes, riscos e a ordem
de leitura econômica. Depois abra somente o documento relacionado à tarefa.

- Preserve alterações existentes e comece por `git status --short`.
- Não leia nem exponha `.env`, tokens, QR codes, JIDs reais, SQLite real ou
  perfis autenticados de navegador.
- Testes unitários não podem acessar WhatsApp, marketplaces ou Evolution reais.
- Scripts de publicação, listagem de grupos e configuração de webhook acessam
  serviços externos; `affiliate_publish --confirm` envia mensagens reais.
- Preserve `AFFILIATE_ENABLED=false` e `AFFILIATE_AUTO_PUBLISH=false` em
  exemplos e homologacoes iniciais.
- Rode `pip check` e a suíte completa após mudanças Python.
- Valide ambos os arquivos Compose relevantes após mudanças de infraestrutura.
- Atualize o documento afetado e `AI_CONTEXT.md` no mesmo ciclo.

Para manutencao geral, use `$automation-whats-maintenance`. Para revisar ofertas,
siga `skills/affiliate-review/SKILL.md`; a copia automatica para `.agents` pode
ser feita quando a pasta protegida estiver disponivel para escrita.
