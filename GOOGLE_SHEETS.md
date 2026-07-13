# Google Sheets

Este projeto usa a planilha **Mantenedores We Care** como base dos fluxos de mantenedores.

## Aba de Mantenedores Ativos

A aba **mantenedores** deve conter:

```text
nome | telefone | valor
```

O telefone pode estar com máscara, mas precisa conter entre 10 e 15 dígitos após remover espaços, parênteses e traços. Linhas com telefone vazio ou inválido são ignoradas para não travar o processamento.

Esse fluxo é usado para quem já está cadastrado como mantenedor. Para cada linha, o sistema:

- envia uma imagem com legenda de lembrete de contribuição;
- envia a chave Pix em uma mensagem separada;
- inclui um aviso amigável para desconsiderar a mensagem caso a contribuição já tenha sido feita;
- envia uma notificação administrativa para todos os números de `EVO_ADMIN_PHONES`.

Comando local:

```powershell
.\venv\Scripts\python.exe -m scripts.process_mantenedores_sheet
```

## Aba de Antigos Mantenedores

A aba **antigos_mantenedores** deve conter:

```text
nome | telefone
```

O mesmo tratamento de telefone é aplicado aqui: linhas inválidas são ignoradas antes do envio.

Esse fluxo convida pessoas que já caminharam como mantenedoras do We Care. A mensagem informa que a Lagoinha Cajazeiras está retomando o projeto de mantenedores.

Mensagem enviada:

```text
Olá, {nome}! 💙

Você já caminhou conosco como mantenedor do We Care.

Estamos retomando o projeto de mantenedores na Lagoinha Cajazeiras e gostaríamos muito de contar com você mais uma vez nessa caminhada de cuidado, generosidade e transformação de vidas.

Se você deseja continuar conosco como mantenedor, responda esta mensagem com:

SIM + o valor que deseja contribuir

Exemplo:
SIM 50

Caso não deseje continuar neste momento, pode responder apenas:
NÃO

Será uma alegria ter você novamente conosco. Que Deus abençoe sua vida! 🙏
```

Comando local:

```powershell
.\venv\Scripts\python.exe -m scripts.process_antigos_mantenedores_sheet
```

## Cadastro Automático Pela Resposta

Quando uma pessoa responder no WhatsApp com `SIM 50`, o webhook da Evolution API recebe a mensagem em:

```text
POST /webhooks/evolution
```

O sistema então:

- identifica respostas no formato `SIM + valor`;
- identifica respostas como `NÃO` ou `NAO` como desinteresse e desconsidera o cadastro;
- verifica se o telefone já existe na aba **mantenedores**;
- usa o nome recebido pelo WhatsApp ou, quando ele não vier, busca o nome na aba **antigos_mantenedores** pelo telefone;
- se ainda não existir, cadastra automaticamente `nome`, `telefone` e `valor` na aba **mantenedores**.

Se o nome não puder ser resolvido, o cadastro é bloqueado para evitar linhas com telefone preenchido no lugar do nome.

## Tratamento de Erros no Envio

Os envios em lote não param quando uma pessoa falha. Se a Evolution API retornar erro para um número inexistente, inválido ou indisponível, o resultado daquela linha volta com:

```json
{
  "status": "error",
  "error": "mensagem do erro"
}
```

Depois disso, a automação continua processando as próximas linhas normalmente. Linhas enviadas com sucesso voltam com:

```json
{
  "status": "sent"
}
```

## Variáveis

```env
GOOGLE_AUTH_MODE=oauth
GOOGLE_OAUTH_CLIENT_SECRET_FILE=credentials/google-oauth-client-secret.json
GOOGLE_OAUTH_TOKEN_FILE=credentials/google-oauth-token.json
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google-service-account.json
GOOGLE_SPREADSHEET_ID=1IRVyir9AxtKlGCOHOo6JfZp1vQZ73_UmZOENz3_zJ7U
GOOGLE_SPREADSHEET_NAME=Mantenedores We Care
GOOGLE_WORKSHEET_NAME=mantenedores
GOOGLE_FORMER_WORKSHEET_NAME=antigos_mantenedores
GOOGLE_SHEETS_RANGE=A:Z
```

## OAuth Local

O arquivo JSON do Google Developers Console deve ficar em:

```text
credentials/google-oauth-client-secret.json
```

Na primeira execução, o navegador será aberto para autorizar o acesso ao Google Sheets. Depois da autorização, o token será salvo em:

```text
credentials/google-oauth-token.json
```

O fluxo de retomada precisa escrever na aba **mantenedores**. Se você já autorizou antes com permissão somente de leitura, apague `credentials/google-oauth-token.json` e rode novamente para autorizar o novo escopo.

## Service Account Para VPS

Em VPS ou produção, prefira service account:

```env
GOOGLE_AUTH_MODE=service_account
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google-service-account.json
```

Depois compartilhe a planilha com o e-mail da service account. Para leitura e cadastro automático, ela precisa ter permissão de editor.

## Imagem do We Care

Quando `WECARE_WELCOME_IMAGE_URL` estiver vazio, o sistema usa o arquivo local:

```env
WECARE_WELCOME_IMAGE_PATH=automation_whats/img/we_care.jpeg
WECARE_WELCOME_IMAGE_MIME=image/jpeg
WECARE_WELCOME_IMAGE_NAME=we_care.jpeg
```
