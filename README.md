# Dashboard Evertec — GitHub → Azure Web App

O dashboard fica compactado em `dashboard.html.gz.b64`; o servidor o descompacta ao abrir o site e injeta automaticamente a fotografia mais recente gravada no Web App.

## Configuração inicial

1. Use um repositório GitHub privado. Copie o conteúdo desta pasta para a raiz, preservando os arquivos na raiz.
2. Use um Azure Web App com publicação de **Código**, sistema **Linux**, runtime **Node.js 24 LTS** e comando de inicialização **npm start**. Este pacote não presume configuração de um App Service Windows, PHP ou container existente.
3. Configure login de visitantes no App Service com Microsoft Entra ID para o público interno autorizado. O servidor deste projeto não implementa login próprio; o controle de acesso é do App Service.
4. Configure a identidade de publicação GitHub→Azure usando OpenID Connect e credencial federada. O subject esperado pelo workflow é `repo:SEU_USUARIO/SEU_REPOSITORIO:environment:production`. O ambiente precisa se chamar `production`. A identidade precisa de permissão de publicação no Web App de destino.
5. No GitHub, crie o Environment **production** e configure nele:

| Tipo | Nome | Conteúdo |
|---|---|---|
| Variable | AZURE_WEBAPP_NAME | Nome exato do Web App |
| Secret | AZURE_CLIENT_ID | Client ID da identidade federada |
| Secret | AZURE_TENANT_ID | Tenant ID |
| Secret | AZURE_SUBSCRIPTION_ID | Subscription ID |

Esses valores devem ser inseridos nas configurações do GitHub; não precisam ser enviados em conversa. Não há client secret no modelo de autenticação escolhido.

6. Em GitHub → Actions, execute o workflow de publicação na branch `main`. Commits posteriores na branch também publicam a nova versão.
7. Ao concluir, abra a URL padrão do Web App exibida pelo Azure. `/health` deve responder `{"status":"ok"}`.

## Atualização das extrações

Na aba **Modelo Power BI**, o carregamento valida os arquivos no navegador e grava a fotografia processada no armazenamento persistente do App Service. O dashboard trabalha com um único universo operacional: **recursos elegíveis da Governança**.

1. Abra o dashboard autenticado.
2. Entre em **Modelo Power BI**.
3. Selecione o CSV de recursos elegíveis da Governança.
4. Opcionalmente, selecione o cadastro corporativo de subscriptions quando ele tiver sido alterado.
5. Informe a Data de Coleta.
6. Clique em **Gravar nova fotografia**.

O cadastro de subscriptions usa as colunas `SUBSCRIPTION NAME`, `SUBSCRIPTION ID`, `PARENT MANAGEMENT GROUP`, `STATUS` e `Management Group (mg-evertecbrasil)?`. Ele permite diferenciar o total corporativo, as assinaturas ativas no escopo e as que efetivamente possuem recursos elegíveis na fotografia.

O Web App grava somente a fotografia processada, não os CSVs brutos, em `/home/data/governanca-tags-dashboard`. Cada coleta gera um arquivo compactado e metadados auditáveis; `latest.txt` aponta para a versão exibida a todos. O cadastro de subscriptions, o mapa oficial e as ações registradas ficam em `governance-config.json`. O histórico aparece nas abas **Evolução da Governança** e **Modelo Power BI**. Para usar outro armazenamento, defina `DASHBOARD_DATA_DIR`.

Fotografias antigas, criadas com o modelo de dois CSVs, continuam disponíveis no histórico. As novas fotografias usam somente o CSV de recursos elegíveis.

## Teste local opcional

Na raiz do repositório, com Node.js 22 ou 24 instalado:

```sh
npm test
npm start
```

Abra http://localhost:8080 . Em Azure, a aplicação respeita a porta definida pelo serviço.

## Documentação oficial

- Publicação com GitHub Actions: https://learn.microsoft.com/azure/app-service/deploy-github-actions
- Configuração Node.js: https://learn.microsoft.com/azure/app-service/configure-language-nodejs
- Autenticação do App Service: https://learn.microsoft.com/azure/app-service/overview-authentication-authorization

Antes de integrar em um repositório existente, conferir a estrutura e outros workflows para preservar as aplicações que já estiverem nele.

