# Webhook do Google Forms

Este fluxo recebe novos cadastros de mantenedores vindos do Google Forms ou da planilha vinculada ao formulário.

Ele é separado do envio de lembretes e da retomada de antigos mantenedores. Aqui o objetivo é dar boas-vindas a quem acabou de se cadastrar.

## Rota

```text
POST /webhooks/google-form/mantenedor
```

No ambiente local, se o servidor Python estiver rodando na sua máquina e a Evolution API estiver no Docker, use:

```text
http://host.docker.internal:8000/webhooks/google-form/mantenedor
```

## Payload Esperado

```json
{
  "nome": "Maria Silva",
  "telefone": "5571999999999",
  "valor": "50,00"
}
```

Quando esse payload chega, o sistema:

- envia uma mensagem de boas-vindas para o telefone cadastrado;
- envia a imagem configurada em `WECARE_WELCOME_IMAGE_PATH` ou `WECARE_WELCOME_IMAGE_URL`;
- envia uma notificação administrativa para todos os números de `EVO_ADMIN_PHONES`.

## Mensagem Enviada

```text
Olá, {nome}! 💙

É uma alegria ter você como mantenedor do We Care.

Passando apenas para confirmar que seu cadastro foi realizado com sucesso. Agradecemos por caminhar conosco nessa missão de cuidar de famílias e transformar vidas.

Que Deus abençoe sua generosidade! 🙏
```

## Respostas Pelo WhatsApp

As respostas de antigos mantenedores não passam pelo Google Forms. Elas chegam pelo webhook da Evolution API:

```text
POST /webhooks/evolution
```

Quando a mensagem recebida estiver no formato `SIM 50`, o projeto cadastra automaticamente a pessoa na aba **mantenedores** do Google Sheets.

## Variáveis

```env
EVO_PHONE_LOGGER=5571999999999
EVO_ADMIN_PHONES=5571999999999,5571888888888
WECARE_WELCOME_IMAGE_URL=
WECARE_WELCOME_IMAGE_PATH=automation_whats/img/we_care.jpeg
WECARE_WELCOME_IMAGE_MIME=image/jpeg
WECARE_WELCOME_IMAGE_NAME=we_care.jpeg
WEBHOOK_SECRET=
WEBHOOK_SECRET_HEADER=X-Webhook-Secret
```

## Servidor Local FastAPI

Inicie o servidor de webhook:

```powershell
.\venv\Scripts\python.exe -m automation_whats.webhooks.server
```

Teste a rota:

```powershell
.\venv\Scripts\python.exe -c "import requests; payload={'nome':'Maria Silva','telefone':'5571999999999','valor':'50,00'}; r=requests.post('http://localhost:8000/webhooks/google-form/mantenedor', json=payload); print(r.status_code, r.text)"
```

## Google Apps Script

Na planilha de respostas do Google Forms, crie um Apps Script com um gatilho `onFormSubmit`.

```javascript
const WEBHOOK_URL = "https://seu-dominio.com/webhooks/google-form/mantenedor";
const WEBHOOK_SECRET = "";

function onFormSubmit(e) {
  const values = e.namedValues;

  const payload = {
    nome: values["Nome"]?.[0] || "",
    telefone: values["Telefone"]?.[0] || "",
    valor: values["Valor"]?.[0] || ""
  };

  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
    headers: {}
  };

  if (WEBHOOK_SECRET) {
    options.headers["X-Webhook-Secret"] = WEBHOOK_SECRET;
  }

  const response = UrlFetchApp.fetch(WEBHOOK_URL, options);
  Logger.log(response.getResponseCode());
  Logger.log(response.getContentText());
}
```

Os nomes `Nome`, `Telefone` e `Valor` precisam bater com os títulos das perguntas no formulário.
