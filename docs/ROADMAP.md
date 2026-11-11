# Roadmap

## Implementado

- filtro de grupo por JID;
- texto e legendas de midia;
- extracao de URLs;
- SQLite e idempotencia;
- resolucao HTTPS com allowlist;
- identificacao de Mercado Livre/Shopee;
- associacao e validacao de link afiliado;
- revisao estruturada;
- deduplicacao, intervalo e limite diario;
- publicacao controlada pelo client Evolution;
- comandos compactos para agente.
- conversao assistida do Mercado Livre com Playwright e validacao do produto;

## Proxima etapa obrigatoria

- criar venv e executar a suite completa;
- descobrir e homologar os JIDs reais;
- homologar o marcador de propriedade e ligar o conversor Mercado Livre a fila;
- instalar a skill no Codex e configurar a tarefa agendada.

## Depois da liberacao

- implementar o adaptador da Shopee;
- ativar publicacao automatica gradualmente;
- adicionar metricas e alerta de falhas;
- supervisionar FastAPI e worker na inicializacao do computador.
