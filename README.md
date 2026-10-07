# Dashboard Evertec — GitHub → Azure Web App

Projeto pronto para configurar o destino e publicar. O dashboard atual fica compactado em `app/dashboard.html.gz.b64`; o servidor o descompacta ao abrir o site. Ainda não foi publicado no Azure.

## Configuração inicial

1. Use um repositório GitHub privado. Copie o conteúdo desta pasta para a raiz, preservando `app/` e `.github/workflows/`.
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

6. Em GitHub → Actions → **Publicar dashboard Evertec**, execute **Run workflow** na branch main. Um commit posterior em `app/` também dispara a publicação.
7. Ao concluir, abra a URL padrão do Web App exibida pelo Azure. `/health` deve responder `{"status":"ok"}`.

## Atualização das extrações

O carregamento dos CSVs atualiza a página no navegador. Para disponibilizar os novos dados para todos:

1. Abra o dashboard, carregue os dois CSVs e informe a data de coleta.
2. Clique em **Salvar dashboard atualizado**.
3. Salve o HTML atualizado como **app/index.html** em uma cópia local do repositório.
4. Dentro de `app/`, execute `npm run pack-dashboard`. Isso atualiza `dashboard.html.gz.b64`.
5. Remova o `index.html` local para não duplicar os dados no commit.
6. Faça commit de `app/dashboard.html.gz.b64`. O GitHub Actions publica a nova versão no mesmo Web App.

Esta versão não recebe nem armazena CSVs no servidor. Upload compartilhado direto pelo site exigiria uma API e armazenamento, que não fazem parte deste pacote. Os históricos ficam no HTML exportado e o compliance Policy continua sendo o valor informado anteriormente.

## Teste local opcional

Na pasta `app`, com Node.js 22 ou 24 instalado:

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
