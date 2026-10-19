# infra/empresa/ - subir o dash no Azure da empresa (PowerShell + az CLI, sem Terraform)

Cria o mesmo ambiente da POC (Web App Linux Python 3.12 com login Entra ID, Azure SQL Basic, Logic App de
e-mail), copia os dados do SQLite local e publica o código. Pode rodar de novo: o que já existe é mantido.

| Arquivo | Para quê |
|---|---|
| `ambiente.example.json` | modelo da configuração; copie para `ambiente.json` (ignorado pelo Git) |
| `subir_ambiente.ps1` | o script, em 9 passos |
| `logicapp.json` | template ARM do Logic App + conexão de e-mail (usado no passo 7) |
| `cloudshell_recursos.ps1` | só o RG e os recursos, pelo **Cloud Shell** do portal (para quem não pode criar pela máquina). Copie o arquivo inteiro e cole no Cloud Shell: isso só carrega a função. `Dash-Recursos` valida (não cria nada); `Dash-Recursos -Modo criar` cria |

## Antes de rodar

1. **Publicar a versão na `main`** (o passo 6 publica `git_ref`, padrão `origin/main`).
2. **Preencher `ambiente.json`**:
   - subscription e tenant da empresa;
   - nomes únicos no Azure (`app_name`, `sql_server`);
   - região permitida pela empresa;
   - tags obrigatórias.
3. Na raiz do repo, rodar `az login` (com a conta da empresa) e ativar o `.venv`.
4. Confirmar com o time de cloud/identidade da empresa (as policies costumam barrar estes pontos):

| Precisa de | Se não tiver |
|---|---|
| Contributor no RG ou na subscription | pedir o RG criado e tirar o passo 1 |
| Criar App Registration no Entra ID | pedir uma, com Redirect URI `https://<app_name>.azurewebsites.net/.auth/login/aad/callback` e um secret; colocar o Client ID em `auth_client_id` |
| SQL com login por usuário e senha | se a policy exigir "Microsoft Entra-only authentication", o app não conecta: avisar antes |
| Acesso público ao SQL e ao App Service | se exigirem Private Endpoint/VNet, este script não cobre |
| Conector Office 365 liberado | sem ele, o e-mail (passos 7 a 9) fica de fora; o resto funciona |

## Rodar

```powershell
copy infra\empresa\ambiente.example.json infra\empresa\ambiente.json   # 1a vez; preencher
powershell -ExecutionPolicy Bypass -File infra\empresa\subir_ambiente.ps1
```

### Em duas etapas: primeiro só os recursos, depois o login

Quando o App Registration é criado por outro time, ele precisa dos nomes antes de criar:

```powershell
# 1a etapa: RG, SQL, Web App (sem codigo) e Logic App. Nao precisa de auth_client_id.
powershell -ExecutionPolicy Bypass -File infra\empresa\subir_ambiente.ps1 -Passos 1,2,3,7
```

Peça o App Registration com a Redirect URI `https://<app_name>.azurewebsites.net/.auth/login/aad/callback`.
Quando receber o Client ID, preencha `auth_client_id` e rode o resto:

```powershell
# 2a etapa: login, dados, codigo e e-mail (o script pede o secret)
powershell -ExecutionPolicy Bypass -File infra\empresa\subir_ambiente.ps1 -Passos 4,5,6,8,9
```

Entre as duas etapas, o Web App fica no ar só com a página padrão do Azure, sem o código e sem dados.

Padrão de nomes do `ambiente.example.json`: `rg-`, `asp-`, `app-`, `sql-`, `sqldb-`, `logic-` e `con-` +
`dash-rec-finops`.

A senha do SQL é pedida uma vez. Ela não é gravada em arquivo nem impressa.

| Passo | O que faz | Precisa de você |
|---|---|---|
| 1 | Resource Group | - |
| 2 | Azure SQL: servidor, banco `finops` Basic, regra `AllowAzureServices` | - |
| 3 | App Service Plan, Web App e appsettings (incluindo a senha do SQL) | - |
| 4 | Login: App Registration (cria se `auth_client_id` estiver vazio), Redirect URI, secret e Easy Auth | se não tiver permissão: colar o secret recebido do dono da app |
| 5 | Dados: confere setembro contra o golden, libera seu IP no SQL e copia o SQLite local | depois: `--triggers` e fechar o firewall (o script imprime os comandos) |
| 6 | Código: `git archive` do `git_ref` + `az webapp deploy` e conferência de que o site responde | - |
| 7 | Logic App + conexão `office365` | - |
| 8 | Autorizar a conexão de e-mail | portal: API connection > Edit API connection > Authorize > Save |
| 9 | Grava `LOGIC_APP_URL` e `FINOPS_EMAIL_OVERRIDE_TO` (todo e-mail vai só para você, com [TESTE]) | seu e-mail |

- O login (4) vem antes do código (6), para o site nunca ficar aberto sem login.
- Os dados (5) vêm antes do código, para o app já subir com as tabelas.
- Para rodar só alguns passos, use `-Passos`. Por exemplo, `-Passos 6` publica só uma versão nova do código.

## Depois

- Testar em janela anônima: login, uma importação de custos e um envio de e-mail.
- Para os e-mails irem aos destinatários reais:
  `az webapp config appsettings delete -g <rg> -n <app> --setting-names FINOPS_EMAIL_OVERRIDE_TO`.
- O secret do login vale **1 ano**. Anote a data para renovar (rodar o passo 4 depois de apagar o appsetting `MICROSOFT_PROVIDER_AUTHENTICATION_SECRET`).
- **Nunca** listar os appsettings com valores na tela, porque eles incluem senhas. Listar só os nomes:
  `az webapp config appsettings list -g <rg> -n <app> --query "[].name" -o tsv`.
