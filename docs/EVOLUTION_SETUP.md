# Configurar e acessar a Evolution API

## O que o projeto precisa

1. Evolution API 2.3.7 executando localmente;
2. PostgreSQL e Redis do Compose;
3. uma instancia chamada `affiliate`;
4. integracao `WHATSAPP-BAILEYS`;
5. numero comercial conectado pelo QR Code;
6. opcao de ignorar grupos desligada;
7. webhook com o evento `MESSAGES_UPSERT`;
8. numero comercial dentro do grupo de origem e do grupo de destino.

O numero nao precisa ser administrador no grupo de origem. No destino ele
precisa ser administrador somente se o grupo permitir mensagens apenas de
administradores.

## 1. Instalar o Docker Desktop

Em 2026-11-10, o Docker Desktop iniciou e o servidor respondeu com a versao
29.9.2. O aplicativo e o disco de dados ainda estavam no C:, que tinha 0,55 GB
livres. Mova o disco de dados para o D: nas configuracoes do Docker Desktop antes
de baixar as imagens. Para instalar o WSL em outro ambiente, abra PowerShell
como administrador e execute:

```powershell
wsl --install
```

Ou clique com o botao direito no PowerShell, escolha **Executar como
administrador** e rode:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_wsl_admin.ps1
```

Reinicie o Windows. Depois instale e abra o Docker Desktop com backend WSL 2.
Espere o aplicativo indicar que o mecanismo esta em execucao. Neste computador,
se o script nao conseguir abrir o aplicativo automaticamente, abra **Docker
Desktop** pelo menu Iniciar e execute o script novamente.

## 2. Preparar e iniciar a Evolution

Abra PowerShell na raiz do projeto e execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_evolution_windows.ps1
```

O script cria `.env` quando necessario, gera as chaves locais sem mostra-las no
terminal e inicia Evolution, PostgreSQL e Redis.

Como as portas do Compose estao limitadas a `127.0.0.1`, o ambiente local usa
`CORS_ORIGIN=*`. Isso permite que a primeira navegacao para `/manager`, que nao
envia o header `Origin`, carregue corretamente no navegador.

## 3. Acessar o Manager

Abra no navegador:

<http://localhost:8080/manager>

Use a chave global guardada em `.env` quando o Manager solicitar autenticacao.
Digite a chave diretamente no Manager; nao a envie em conversa ou captura de
tela.

## 4. Criar e conectar a instancia

No Manager:

1. crie a instancia `affiliate`;
2. escolha `WHATSAPP-BAILEYS`;
3. habilite QR Code;
4. deixe `Ignorar grupos` desligado;
5. abra no celular WhatsApp > Aparelhos conectados > Conectar aparelho;
6. leia o QR Code exibido no computador;
7. aguarde o estado `open` ou `connected`.

## 5. Iniciar o receptor Python

Em outro PowerShell na raiz:

```powershell
.\venv\Scripts\python.exe -m automation_whats.webhooks.server
```

Confira:

- <http://localhost:8000/health>
- <http://localhost:8000/ready>

`health` confirma que o servidor esta ativo. `ready` mostra somente indicadores
seguros de configuracao, sem chaves.

## 6. Configurar o webhook

Com a Evolution e o FastAPI ativos:

```powershell
.\venv\Scripts\python.exe -m scripts.configure_webhook
```

O webhook configurado sera:

```text
http://host.docker.internal:8000/webhooks/evolution
```

Evento necessario: `MESSAGES_UPSERT`. O segredo do webhook e enviado em header,
sem ser impresso pelo comando.

## 7. Encontrar os JIDs dos grupos

```powershell
.\venv\Scripts\python.exe -m scripts.affiliate_list_groups --filter "PROMOS DA LUH"
.\venv\Scripts\python.exe -m scripts.affiliate_list_groups --filter "ARTEFATOS E UTILIDADES"
```

Copie os JIDs terminados em `@g.us` para o `.env`:

```env
AFFILIATE_SOURCE_GROUP_JIDS=JID_ORIGEM_1,JID_ORIGEM_2,JID_ORIGEM_3
AFFILIATE_DESTINATION_GROUP_JID=JID_DO_GRUPO_DE_DESTINO
```

Os JIDs precisam ser diferentes.

## 8. Diagnosticar a integracao

```powershell
.\venv\Scripts\python.exe -m scripts.evolution_status --filter "PROMOS DA LUH"
```

O resultado mostra somente estado da conexao, webhook, grupos encontrados e
controles da automacao. Tokens e headers secretos sao removidos.

## 9. Ativar somente a captura

Depois de conferir os grupos:

```env
AFFILIATE_ENABLED=true
AFFILIATE_AUTO_PUBLISH=false
AFFILIATE_REVIEW_REQUIRED=true
AFFILIATE_SHOPEE_ENABLED=false
```

Reinicie o FastAPI. Envie uma unica oferta de teste no grupo de origem e
confira a fila. A publicacao permanece bloqueada.

## Portas locais

| Endereco | Funcao |
|---|---|
| `http://localhost:8080/manager` | Manager da Evolution |
| `http://localhost:8080` | API Evolution |
| `http://localhost:8000/health` | processo FastAPI |
| `http://localhost:8000/ready` | prontidao da automacao |

PostgreSQL e Redis nao precisam ser acessados para operar o projeto.
