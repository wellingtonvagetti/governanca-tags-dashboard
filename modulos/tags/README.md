# Módulo Governança de Tags

Módulo da Plataforma FinOps Evertec, publicado em `/tags`. Quem mantém este módulo altera **somente esta pasta**.

## O que fica aqui

| Arquivo | Conteúdo |
|---|---|
| `index.html` | Tela do módulo (o antigo `dashboard.html`, sem os dados embutidos) |
| `assets/` | `dashboard-v2.js`, `dashboard-v2.css`, logos, fundo e ícones do Azure (servidos em `/tags/assets/...`) |

O servidor injeta os dados no `index.html` em dois marcadores, que precisam continuar no arquivo:

- `<script id="data" type="application/json">__TAGS_SNAPSHOT__</script>` recebe a fotografia atual.
- `<script id="historyData" type="application/json">__TAGS_HISTORICO__</script>` recebe a base histórica.

## Regras

- **Os dados não vão para o repositório.** Fotografias, histórico e cadastro de subscriptions ficam no armazenamento do App Service (`/home/data/modulos/tags`). Nada de CSV, JSON de inventário ou IDs de recursos em `index.html` ou em `assets/`. O teste `tests/test_modulo_tags.py` barra o merge se isso acontecer.
- **Caminhos absolutos com prefixo:** os arquivos ficam em `/tags/assets/...` e a API em `/api/tags/...`.
- **API disponível**, com as mesmas regras do `server.js` original:
  - `GET /api/tags/snapshots` lista as fotografias;
  - `POST /api/tags/snapshots` grava uma fotografia (`{"snapshot": ...}`, até 30 MB);
  - `DELETE /api/tags/snapshots/{id}` exclui uma fotografia;
  - `GET /api/tags/governance-config` lê o mapa oficial, as ações e as subscriptions;
  - `PUT /api/tags/governance-config` grava essa configuração.

  Mudanças na API (`api/modulo_tags.py` e `api/modulo_tags_rotas.py`) são feitas fora desta pasta e passam por revisão do dono da plataforma.
- **O seletor "Módulo" do topo** vem da plataforma (`/plataforma/modulos.css` e `/plataforma/modulos.js`, com o elemento `<div data-mod-seletor="tags">`). Mantenha os três no arquivo.

## Rodar localmente

```powershell
pip install -r requirements.txt
python tools\tags_carregar_base.py <dashboard.html.gz.b64> [subscriptions-master.json]   # base inicial, uma vez
python -m uvicorn api.main:app --port 8000
```

Abra http://localhost:8000/tags. Para testar:

```powershell
python -m unittest tests.test_modulo_tags
```
