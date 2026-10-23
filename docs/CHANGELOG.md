# Histórico de versões do frontend

## Virada de mês genérica (outubro/2026)

- Seletor de competência com **"+ Abrir {Mês}/{Ano}"**, liberado 3 dias antes do mês seguinte. Ao abrir, a API herda as pendências do mês anterior (`reconciliar-pendencias`) e o dash já abre no mês novo, com Rescaldo herdado, histórico e importação prontos. Vale para todos os meses (Novembro, Dezembro, ...), não só Outubro.
- A **data recomendada** é a da primeira vez que a recomendação apareceu e **não muda mais na herança** (antes virava `<mês>-01`). `tools/restaurar_data_recomendada.py SIMULAR|APLICAR <competência>` devolve a data original às linhas já herdadas (Outubro: 1068 linhas; o financeiro não muda).
- `GET /api/recomendacoes/{competencia}/historico`: última versão de cada ID em todas as competências anteriores. De Novembro em diante é a referência da importação (capturada/reprovada antes não volta; IDs novos continuam a sequência) e do Rescaldo herdado.
- Importar "Novas recomendações" grava no mês ativo do banco (Outubro, Novembro, ...).
- Ao recarregar a página, abre o último mês aberto pelo usuário ou o mais recente do banco; o mês ativo deixou de ser compartilhado entre usuários (`finops_active_period` fora do `app_state`).
- Correção: o "Rescaldo herdado de Agosto" em Setembro voltou a aparecer (R$ 3.864,34); zerava desde a troca dos nomes de status.
- `tools/fechar_competencia.py SIMULAR|APLICAR <competência>` fecha uma competência no SQLite ou no Azure SQL e confere que os números não mudam; `verifica_numeros.py` aceita `AZURE` no lugar do arquivo do banco.

## Plataforma de módulos (outubro/2026)

- Recomendações com o topo no padrão dos módulos de Tags e Auditoria de VMs: logo | título, botões LIGHT (tema escuro) e FONTE (normal/grande/extra grande), módulo, competência, linha e abas em caixa alta. Tema e fonte usam as mesmas preferências do módulo de Tags (`governanca-theme`/`governanca-font`). O tema escuro é gerado do próprio CSS por `tools/gerar_tema_escuro.py` (rodar de novo quando o CSS mudar cores).
- Página inicial (`/`, `frontend/inicio.html`) com os módulos; o dash de recomendações passa para `/recomendacoes`. Seletor "Módulo" no topo de cada página (`frontend/plataforma/`), no mesmo visual do seletor de competência.
- Módulo Governança de Tags (`/tags`): front-end do dashboard de tags em `modulos/tags/` e o servidor Node portado para `api/modulo_tags.py` (fotografias, histórico e configuração, mesmas regras e validações). Os dados (inventário Azure) ficam fora do repositório, em `FINOPS_TAGS_DATA_DIR` (no App Service, `/home/data/modulos/tags`); `tools/tags_carregar_base.py` grava a base inicial.

## Infraestrutura, banco e desempenho (outubro/2026)

- Novos status da Análise: RASCUNHO, IDENTIFICADA, VALIDAÇÃO TÉCNICA, PLANEJADA, EM IMPLEMENTAÇÃO, CAPTURADO, REPROVADA, ADIADA. Regra em `api/status.py` (aprovada+realizado = CAPTURADO; aprovada com chamado = EM IMPLEMENTAÇÃO; aprovada sem realizar = PLANEJADA). O motor de cálculo do front segue com as classes antigas (mapeadas na borda) e o `verifica_numeros` usa `legado()`, então o golden de setembro continua válido. `tools/converter_status_analise.py SIMULAR|APLICAR <db>` converte as linhas existentes (com backup e prova de que o hash financeiro não muda). Em competência fechada o status segue o `realizado` congelado.
- CI/CD: `ci` (compilação, testes unitários, gitleaks) nos PRs; `deploy-poc` na `main` com login OIDC no Azure (PRs #1 e #2).
- Azure SQL opcional por `FINOPS_SQL_SERVER`, com camada de dialeto e migrador; POC passou a gravar no Azure SQL Basic (PRs #3 e #4).
- Correção: linha editada deixa de sumir da tabela até mudar filtro ou competência (`STICKY_ROWS_V401`, PR #6).
- `/api/custos/persistidos`: gzip, ETag/304 e contagem leve (PR #7); cache gzip em memória por ETag com aquecimento no startup (PR #9). Medido na POC: 95 MB / 34 s → 11 MB / 2,6 s.
- Front não reenvia `estado-completo` idêntico ao último confirmado (PR #11), para cortar a rajada de POSTs ao abrir a página e trocar de competência.
- `GET /api/recomendacoes/{competencia}` (Azure SQL, sem filtros): leitura única com cache em memória por competência, invalidado a cada commit que escreve em `recommendations` (versão em `api/sqldb.py`) e com TTL de 5 min (`FINOPS_RECS_CACHE_TTL_S`). Antes eram COUNT + SELECT em duas conexões, ~2 s cada chamada.
- O cache da listagem deixava de valer a cada abertura da página: o lote de `estado-completo` regravava linhas idênticas e o `reconciliar-pendencias` relia as duas competências inteiras do banco. Agora a gravação de uma recomendação é pulada quando todas as colunas já guardam os mesmos valores (a versão do cache só sobe com mudança real) e o `reconciliar-pendencias` lê pelo cache.
- Limpeza: imports sem uso removidos (`api/main.py`, testes) e o diagnóstico do lote reduzido a uma linha de log (`[lote] competência: N recebidas, M gravadas, tempo`). Branches já mescladas apagadas.
- Lote de `estado-completo` com poucas consultas: o estado atual de todas as linhas é lido de uma vez, dentro da transação, e as linhas que não mudam nada não fazem mais nenhuma consulta (antes ~5 por linha; 73 linhas sem mudança passam de ~365 consultas para 4, ~1,5 s → décimos de segundo). A lista de colunas da tabela é guardada no Azure. As linhas que mudam seguem pelo caminho completo (auditoria, UPDATE).
- Cache da listagem: o TTL (5 min) deixou de forçar leitura fria. Vencido o TTL, serve o que está em memória e relê em segundo plano; versão nova (escrita no app) continua exigindo releitura imediata. Antes, quem abria a página depois de >5 min sem uso pagava ~2 s por competência.
- Aquecimento do cache da listagem no startup (Azure SQL): as 2 competências mais recentes são lidas em segundo plano, para a 1ª abertura depois do deploy não pagar a leitura fria.
- Gravação em lote: `POST /api/recomendacoes/{competencia}/estado-completo-lote` grava várias recomendações numa só transação, e o front agrupa as chamadas (fila de 60 ms). Na abertura da página, ~65 POSTs viram 1.
- Limpeza de código morto: versão V214 duplicada em `api/cost_service.py`, `atualizar_recomendacao`/`APP_ENV` em `api/db.py`, colunas inexistentes (`id`, `created_at`, `updated_at`, `rescaldo_herdado`) e aliases em `api/main.py`; no front, a migração V164 (inalcançável), os resets de execução única V80/V85/V86/V107/V133 e as funções `breakAt` e `flowPriorityBadgeV208`.
- Correção: num SQLite novo, `cost_records` era criada sem `source_type`, e gravar custos falhava (`ON CONFLICT` de 4 colunas).
- `database/schema.sql` passa a ter todas as tabelas e a API o aplica ao abrir o SQLite; saem `init_db.py`, `migrate_002.py` e `migration_002_audit.sql`. Saem também o modo consulta (`tools/publicar_consulta.py` e arquivos de apoio, quebrado desde o lote), a parte de `freeze_competencia.py` que alterava o `api/main.py` e as rotas sem uso no front (`/resumo`, `/api/squads`, `GET .../{id}`, `.../{id}/estado-completo`, `/app-state/stats`, `POST /custos/persistidos/lote`).
- Infra e docs: `FINOPS_ENV` sai do Terraform (o código não lê); `FINOPS_DB_PATH` e `FINOPS_BACKUP` ficam como reserva para o modo SQLite. O passo 3 do `pos_apply.ps1` dispara o workflow `deploy-poc` em vez de um deploy manual. `infra/README.md` sem o upload do SQLite (o POC usa Azure SQL), checklist atualizado; `MIGRACAO.md` e `AZURE_SQL.md` atualizados; sai `docs/baseline_manifest.json`.
- Frontend: sai o backup HTML portátil (v135: botão, que já estava oculto, exportação e restauração) e o `PAYLOAD`/`payloadRecordsSafeV180`, que nunca recebia dados (o servidor não injeta). Conferido em Chrome headless contra cópia do banco: mesmos números da `dev` em Outubro e Setembro e nenhum erro de JavaScript.
- Frontend: saem as versões originais de `renderTicketSla` e das 4 `flowRecipient*V208`, substituídas mais adiante e nunca chamadas (provado com contadores no navegador), 9 constantes sem uso e 26 regras CSS de 12 classes sem uso. Backend: `@app.on_event` (depreciado) vira `lifespan`, sai o `"ambiente": "dev"` fixo do `/api/health` e o apelido `_cost_conn`.

Notas por versão do frontend:

Notas migradas dos comentários que ficavam no topo de `frontend/index.html`.

- v126: Outubro herda EM ANÃLISE/ADIAR e APROVADO ainda não realizado de Setembro com mesmo FinOpsOpportunityId; rescaldo herdado separado do rescaldo previsto do mês atual
- v134: ciclo de chamados por competência; Outubro inicia com 0 concluídas e só conta respostas/ações registradas em Outubro
- v135: backup HTML portátil embute Setembro + Outubro + alterações + SLA/configurações + exports de custos persistidos e restaura o estado ao abrir
- v136: renomeia Gerenciar Outubro/2026 para Novas recomendações — Outubro
- v137: Novas recomendações compara exports com a base atual de Outubro e adiciona somente oportunidades realmente novas, sem recriar/substituir a competência
- v128: corrige Premium SSD → Standard SSD com validação pós-alteração e atualiza SRV-WAZ-TH014 para 29/09
- v130: Data efetivada da planilha oficial é a fonte de verdade quando preenchida; inferência por custos somente quando a data estiver vazia
- v129: fixa Data efetivada dos discos TH014 em 29/09 mesmo com histórico local e separa dias observados de dias projetados nos resizes
- v127: corrige alinhamento dos botões do modal de custos
- v133: SLA só inicia após chamado + data de abertura; antes disso prazo/SLA ficam zerados. Recomendações > R$ 1K são prioridades desde o início.
- v125: novo SLA relativo à abertura do chamado: abertura avisa Squad + Gestor e destaca > R$ 1K; +10 dias cobra prioridades; +20 dias cobra todas as pendências; Diretor removido do fluxo
- v124: FinOpsOpportunityId conciliado com Planilha2; IDs existentes preservados e novas oportunidades numeradas sequencialmente
- v123: regra de resize corrigida para 4–5 dias completos pós-alteração
- v122: nomenclatura Custos Cloud e neutralização do fornecedor de custos
- v131: Atualizar planilha passa a exibir botão Fechar após aplicação, no mesmo padrão do modal de custos
- v121: preview de custos antes de aplicar, lista itens afetados e botão Fechar após aplicação
- v120: persiste o último export de custos por nuvem/mês no navegador e restaura ao reabrir
- v144: Saving Est. por custo anterior passa a acompanhar base parcial (28/29/30) e preview mostra BU/Squad mapeados
- v145: Atualizar planilha preserva valores existentes quando a célula correspondente vier vazia; vazio não apaga dado do dashboard. Novas recomendações mantêm vazios reais.
- v156: remoções confirmadas no fim do mês usam o último custo bruto disponível (inclusive dia parcial da ação), baseline diário pré-ação e custo pós-remoção zero; projeta rescaldo do mês seguinte. Amplia a regra de remoção para Container Registry, Monitoring, Private DNS, Storage Account e Log Analytics removidos.
- v157: Outubro é reconciliado automaticamente com Setembro; qualquer FinOpsOpportunityId que fique APROVADO + REALIZADO em Setembro é removido da base ativa de Outubro, permanecendo apenas no histórico/Rescaldo herdado.
- v158: auditoria financeira: fallback sem validação passa a Saving Efetivo R$ 0,00; AKS/VMSS sem custo individual comparável fica R$ 0,00; resize real informado na observação pode prevalecer sobre a troca originalmente recomendada; Fargate validado passa a projetar Rescaldo; EKS e weekend recebem rescaldo recorrente quando aplicável.
- v159: para recomendações de remoção, APROVADO + Realizado=SIM é a fonte de verdade operacional; observação não bloqueia a remoção. Saving Efetivo usa baseline pré-ação versus custo real do mês e Rescaldo projeta custo recorrente zerado após a remoção.
- v160: quando o mês atual não possui custo e o baseline vem apenas do mês anterior sem patamar diário estável, normaliza o total anterior pela média diária e projeta pelos dias do mês atual; nunca copia diretamente um mês de 31 dias para um mês de 30.
- v161: FINOPS-000017 / SRV-WAZ-GP045 usa Data efetivada 15/08/2026 conforme decisão operacional; resize efetivado no mês anterior é apurado como mês cheio na competência atual, comparando baseline pré-resize do mês da execução com o patamar estabilizado do mês atual.
- v162: Notas do painel simplificadas: APROVADO+SIM confirma a ação de remoção, custos também validam a queda e calculam o benefício; fórmulas e rescaldo explicados em linguagem direta.
- v163: Squad, Responsável e Responsável Técnico são sincronizados pelo mesmo FinOpsOpportunityId entre Setembro e Outubro; funciona tanto na atualização pela planilha quanto no redirecionamento manual. Ticket não é sincronizado entre competências porque cada mês tem seu próprio ciclo de chamados.
- v164: importação idempotente: Ticket de recomendações existentes é controlado pelo dashboard e não volta a partir de valor antigo da planilha; ação histórica preserva o Saving oficial, zerando apenas Saving Efetivo/Rescaldo da competência; chamado preenchido no Controle de chamados é aplicado somente a recomendações da Squad que ainda estejam sem Ticket.
- v166: corrige XLSX de Recomendações Vigentes por Squad: XML da worksheet passa a respeitar a ordem OOXML (sheetProtection antes de autoFilter/dataValidations) e textos removem caracteres inválidos de XML 1.0, evitando o reparo do Excel.
- v167: planilhas de Recomendações Vigentes por Squad continuam protegidas, mas permitem ao usuário redimensionar colunas e linhas no Excel (formatColumns/formatRows liberados).
- v171: corrige Provider OCI: qualquer Item iniciado por ocid1.* é Oracle Cloud Infrastructure (OCI). FINOPS-000441, FINOPS-000472, FINOPS-001179 e FINOPS-001183 ficam OCI em Setembro/Outubro. Mantém formato BRL das planilhas por Squad.
- v176: APROVADO + Realizado=SIM usa Saving Est. como Saving realizado estimado, independente do Saving Efetivo. Adiciona KPI Saving realizado estimado ao lado do Saving realizado e preserva Saving Est. na coluna Saving mesmo quando Saving Efetivo = R$ 0,00.
- v173: Exportar CSV filtrado formata todos os campos monetários em BRL (R$ #.##0,00), evitando interpretação incorreta de decimais pelo Excel em pt-BR.
- v174: planilhas de recomendações por Squad mantêm o mesmo padrão/colunas, mas ficam temporariamente sem proteção, bloqueios, validações obrigatórias, prompts e avisos condicionais; todos os campos podem ser editados livremente.
- v175: ao gerar planilhas de recomendações em Outubro, itens herdados de Setembro (_carryFrom=2026-09) mantêm Data Recomendada = 01/09/2026; recomendações novas de Outubro permanecem 01/10/2026.
- v179: corrige quota do navegador na importação de Outubro; remove storages legados redundantes antes de persistir a base mensal e exclui esses legados dos backups portáteis.
- v180: corrige fechamento do modal de Novas recomendações após aplicar/importar; estado busy é sempre liberado ao abrir, concluir, falhar ou fechar o modal.
- v177: reconciliação bidirecional Setembro→Outubro por FinOpsOpportunityId. Se uma recomendação antes REPROVADA voltar para ADIAR, EM ANÃLISE ou APROVADO não realizado em Setembro, ela é reinserida automaticamente em Outubro com exatamente o mesmo ID; concluídas/reprovadas são removidas.
- v178: somente para "Instances with low CPU usage that can be stopped on weekends", a identidade de importação ignora SKU e métricas Weekend/Weekday do Item, consolida a mesma VM, preserva o FinOpsOpportunityId existente e atualiza o Item com as métricas mais recentes. Demais recomendações mantêm a regra anterior.
- v172: remove de Outubro os IDs FINOPS-002080, 002081, 002083, 002086, 002087, 002088, 002089, 002090, 002091 e 002093; Setembro permanece intacto. Essas recomendações de weekend ficam bloqueadas de reaparecer em novas importações de Outubro pelo mesmo recurso.
- v165: fecha idempotência dos Savings oficiais: ações históricas preservam a coluna Saving; FINOPS-000436 mantém R$ 68,26; FINOPS-000470 mantém R$ 73,74 e observação oficial "Vm removida."; reimportar a mesma planilha não deve reapresentar esses itens.
- v158: recomendações de ELASTICITY/weekend que tiveram ação real de VM removida/desligada passam a priorizar a ação executada sobre a recomendação original; Saving Efetivo e Rescaldo são calculados como remoção/parada validada.
- v158: FINOPS-000470 (dhp-compartilhado-vault-dev-1) consolidada como VM removida em 20/09/2026 e retirada da base ativa de Outubro.
- v119: remove qualquer teto do Saving Est. no saving efetivo de resize; custo validado define o efetivo
- v115: corrige nomes parecidos, IPv4 AWS sem pontos e duplicidades por componente AWS
- v87: auditoria do recálculo após upload de custos
- v82: importação automática da devolutiva por Squad
