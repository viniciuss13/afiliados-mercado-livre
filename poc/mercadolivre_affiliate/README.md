# POC de links da Barra de Afiliados do Mercado Livre

A POC usa Playwright assíncrono com o Microsoft Edge Stable (`msedge`) e o
Google Chrome Stable (`chrome`) instalados no Windows. Ambos abrem em modo
visível. O modo `all` executa primeiro Edge e depois Chrome, com diagnósticos
independentes. [Canais de navegador do Playwright](https://playwright.dev/python/docs/browsers#google-chrome--microsoft-edge)

Na raiz do repositório, com CPython 3.11 ou superior, instale a dependência
e execute um dos comandos abaixo. O exemplo usa a instalação padrão do
Python 3.14.

```powershell
py -3.14 -m venv poc\mercadolivre_affiliate\.venv
$pocPython = ".\poc\mercadolivre_affiliate\.venv\Scripts\python.exe"
& $pocPython -m pip install -r poc\mercadolivre_affiliate\requirements.txt
& $pocPython -m poc.mercadolivre_affiliate --browser edge
& $pocPython -m poc.mercadolivre_affiliate --browser chrome --dedicated-profile
& $pocPython -m poc.mercadolivre_affiliate --browser all --dedicated-profile
```

A URL padrão aponta para a Epson EcoTank L3250, catálogo `MLB34229008`,
com os filtros do item `MLB4030651099` e da loja oficial. Use `--url 'URL'`
para testar outro anúncio. Se o terminal solicitar login, entre na conta
de afiliado pela janela aberta, conclua pessoalmente as verificações do
site e pressione Enter no terminal. A Barra deve estar ativa na Central de
Afiliados. Os perfis `.browser_profiles/edge/` e
`.browser_profiles/chrome/` são reutilizados nas próximas execuções. Use
`--no-login` para testar sem pausa interativa.

O perfil padrão do Chrome tem restrições para inicialização via depuração.
Com o Chrome 144 ou posterior já aberto no perfil logado, abra
`chrome://inspect/#remote-debugging` e habilite a depuração remota. Use o
arquivo de conexão `DevToolsActivePort` para montar o endereço WebSocket
local. Aceite o pedido de conexão no Chrome quando aparecer.

```powershell
$porta, $caminho = Get-Content -LiteralPath "$env:LOCALAPPDATA\Google\Chrome\User Data\DevToolsActivePort" -TotalCount 2
$endpoint = "ws://127.0.0.1:${porta}${caminho}"
& $pocPython -m poc.mercadolivre_affiliate --browser chrome --cdp $endpoint
```

O comando abre apenas uma aba temporária no Chrome existente. Sem endereço
CDP, o Chrome separado só abre com `--dedicated-profile`.
[Restrições do Chrome](https://developer.chrome.com/blog/remote-debugging-port)
[Conexão autorizada a uma sessão existente](https://developer.chrome.com/docs/devtools/agents/get-started/configuration#connect_to_an_existing_browser_session)

## Elementos verificados no Edge autenticado

| Elemento | Locator |
| --- | --- |
| Barra de Afiliados | `get_by_role("navigation", name="Afiliados", exact=True)` |
| Compartilhar da Barra | `get_by_test_id("generate_link_button")` dentro da Barra |
| Painel | `get_by_test_id("popper")` filtrado pelo texto **Gerar link / ID de produto** |
| Campo **Link do produto** | `get_by_test_id("text-field__label_link")` dentro do painel |
| Copiar | `get_by_role("button", name="Link do produto", exact=True)` dentro do painel. Também foi observado o ID de teste `copy-button__label_link` |
| Número do anúncio exibido | `#denounce` |

A leitura do campo registra `EXTRACTION_SUCCESS`. O script usa um marcador
temporário no clipboard antes do clique para detectar uma escrita nova,
inclusive se o mesmo link já estiver copiado. Registra `COPY_SUCCESS`
somente quando o valor novo coincide com o campo. Em caso de falha na cópia,
preserva o link extraído e registra `COPY_UNVERIFIED`. A atribuição continua
como `AFFILIATE_VALIDATION_PENDING`.

Os logs `etapas.log` e a captura recortada `campo.png`, quando disponível,
ficam em `.artifacts/`. Traces do Playwright foram gerados com HTML
simulado em `.artifacts/simulacao/` para evitar registrar o DOM e a rede de
uma sessão autenticada. Os perfis e artefatos são ignorados pelo Git.

## Resultados reais e simulados

No Edge com a sessão pessoal autenticada, a Barra retornou
`https://meli.la/15R3ZPN`. Cliquei em Copiar e o clipboard mudou para o
mesmo link. A confirmação veio da leitura do clipboard. O catálogo era
`MLB34229008`, mas o número renderizado foi `MLB4828637949`, diferente do
filtro `MLB4030651099`. A correspondência com o item solicitado e a
atribuição de comissão seguem pendentes.

A extração e a comparação com o clipboard passaram em páginas simuladas
nos dois navegadores instalados. Esse teste valida o código sem depender
de uma sessão real. O Chrome autenticado ainda precisa ser verificado.
O `pip check` e os 34 testes unitários passaram em ambiente isolado.

| Verificação real | Edge Stable | Chrome Stable |
| --- | --- | --- |
| Abertura pela POC | `156.0.4314.58` | `157.0.8103.39` |
| Perfil dedicado | Chegou ao produto e pediu login na última execução | Mercado Livre apresentou verificação de segurança |
| Sessão autenticada observada | Sim, no Edge local habitual | Pendente |
| Produto e anúncio exibidos | Catálogo `MLB34229008`, item `MLB4828637949` na sessão habitual | Pendente |
| Barra, Compartilhar e Copiar | Confirmados na sessão habitual | Pendentes |
| Link e clipboard | `https://meli.la/15R3ZPN` em ambos | Pendentes |

O worker consome o `TestResult` retornado pela coleta e passa a URL original
da oferta recebida no WhatsApp. A URL padrão acima é usada pela CLI de teste.
A cópia confirmada e a validação do destino do link são etapas separadas.
