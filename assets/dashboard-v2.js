/* Dashboard executivo v2: universo único de recursos elegíveis + cadastro corporativo de subscriptions. */
(function(){
  'use strict';
  scope='esc';
  const iconBase='/assets/azure-icons/';
  const iconMap=[
    ['microsoft.compute/virtualmachines','virtual-machine.svg'],
    ['microsoft.compute/virtualmachines/extensions','extension.svg'],
    ['microsoft.compute/virtualmachinescalesets','vm-scale-set.svg'],
    ['microsoft.compute/disks','disk.svg'],
    ['microsoft.compute/snapshots','snapshot.svg'],
    ['microsoft.compute/availabilitysets','availability-set.svg'],
    ['microsoft.compute/restorepointcollections','restore-point.svg'],
    ['microsoft.compute/images','image.svg'],
    ['microsoft.compute/galleries','compute-gallery.svg'],
    ['microsoft.compute/galleries/images','compute-gallery.svg'],
    ['microsoft.compute/sshpublickeys','ssh-key.svg'],
    ['microsoft.storage/storageaccounts','storage-account.svg'],
    ['microsoft.containerservice/managedclusters','kubernetes-service.svg'],
    ['microsoft.containerregistry/registries','container-registry.svg'],
    ['microsoft.containerregistry/registries/replications','container-registry.svg'],
    ['microsoft.containerinstance/containergroups','container-instance.svg'],
    ['microsoft.app/containerapps','container-app.svg'],
    ['microsoft.app/managedenvironments','container-app.svg'],
    ['microsoft.sql/servers/databases','sql-database.svg'],
    ['microsoft.sql/servers','sql-server.svg'],
    ['microsoft.sqlvirtualmachine/sqlvirtualmachines','sql-database.svg'],
    ['microsoft.dbforpostgresql/flexibleservers','postgresql.svg'],
    ['microsoft.cache/redis','redis.svg'],
    ['microsoft.cache/redisenterprise','redis.svg'],
    ['microsoft.web/sites','app-service.svg'],
    ['microsoft.web/serverfarms','app-service.svg'],
    ['microsoft.keyvault/vaults','key-vault.svg'],
    ['microsoft.keyvault/managedhsms','key-vault.svg'],
    ['microsoft.network/virtualnetworks','virtual-network.svg'],
    ['microsoft.network/privateendpoints','private-endpoint.svg'],
    ['microsoft.network/networkinterfaces','network-interface.svg'],
    ['microsoft.network/networksecuritygroups','network-security-group.svg'],
    ['microsoft.network/publicipaddresses','public-ip.svg'],
    ['microsoft.network/routetables','route-table.svg'],
    ['microsoft.network/loadbalancers','load-balancer.svg'],
    ['microsoft.network/applicationgateways','application-gateway.svg'],
    ['microsoft.network/applicationgatewaywebapplicationfirewallpolicies','waf-policy.svg'],
    ['microsoft.network/privatednszones','private-dns.svg'],
    ['microsoft.network/privatednszones/virtualnetworklinks','private-dns.svg'],
    ['microsoft.network/networkwatchers','network-watcher.svg'],
    ['microsoft.network/bastionhosts','bastion.svg'],
    ['microsoft.network/expressroutecircuits','express-route.svg'],
    ['microsoft.network/connections','connection.svg'],
    ['microsoft.network/virtualnetworkgateways','virtual-network-gateway.svg'],
    ['microsoft.eventhub/namespaces','event-hub.svg'],
    ['microsoft.servicebus/namespaces','service-bus.svg'],
    ['microsoft.operationalinsights/workspaces','log-analytics.svg'],
    ['microsoft.operationalinsights/querypacks','log-analytics.svg'],
    ['microsoft.operationsmanagement/solutions','solution.svg'],
    ['microsoft.insights/components','application-insights.svg'],
    ['microsoft.insights/actiongroups','alerts.svg'],
    ['microsoft.insights/metricalerts','alerts.svg'],
    ['microsoft.insights/scheduledqueryrules','alerts.svg'],
    ['microsoft.insights/activitylogalerts','alerts.svg'],
    ['microsoft.alertsmanagement/smartdetectoralertrules','alerts.svg'],
    ['microsoft.insights/autoscalesettings','monitor.svg'],
    ['microsoft.insights/datacollectionrules','monitor.svg'],
    ['microsoft.insights/datacollectionendpoints','monitor.svg'],
    ['microsoft.recoveryservices/vaults','recovery-vault.svg'],
    ['microsoft.dataprotection/backupvaults','backup-vault.svg'],
    ['microsoft.managedidentity/userassignedidentities','managed-identity.svg'],
    ['microsoft.automation/automationaccounts','automation.svg'],
    ['microsoft.automation/automationaccounts/runbooks','automation.svg'],
    ['microsoft.resourcegraph/queries','resource-graph.svg'],
    ['microsoft.portal/dashboards','dashboard.svg'],
    ['microsoft.hybridcompute/machines','arc-machine.svg'],
    ['microsoft.hybridcompute/machines/extensions','azure-arc.svg'],
    ['microsoft.azurearcdata/sqlserverinstances','azure-arc.svg'],
    ['microsoft.azurearcdata/sqlserverinstances/databases','azure-arc.svg'],
    ['microsoft.migrate/movecollections','migration.svg']
  ];
  const resourceIcon=type=>iconBase+(iconMap.find(([key])=>String(type||'').toLowerCase()===key)?.[1]||'all-resources.svg');
  const resourceTypeLabels={
    'microsoft.azurearcdata/sqlserverinstances':'Azure Arc-enabled SQL Server','microsoft.hybridcompute/machines':'Azure Arc-enabled Server',
    'microsoft.compute/restorepointcollections':'Restore Point Collection','microsoft.storage/storageaccounts':'Storage Account',
    'microsoft.insights/datacollectionrules':'Data Collection Rule','microsoft.operationalinsights/workspaces':'Log Analytics Workspace',
    'microsoft.operationsmanagement/solutions':'Operations Management Solution','microsoft.compute/disks':'Managed Disk',
    'microsoft.compute/virtualmachinescalesets':'Virtual Machine Scale Set','microsoft.managedidentity/userassignedidentities':'User Assigned Managed Identity',
    'microsoft.network/loadbalancers':'Load Balancer','microsoft.network/networkinterfaces':'Network Interface',
    'microsoft.network/networksecuritygroups':'Network Security Group','microsoft.network/privateendpoints':'Private Endpoint',
    'microsoft.network/publicipaddresses':'Public IP Address','microsoft.network/routetables':'Route Table',
    'microsoft.compute/snapshots':'Snapshot','microsoft.network/privatednszones':'Private DNS Zone',
    'microsoft.network/privatednszones/virtualnetworklinks':'Virtual Network Link','microsoft.compute/virtualmachines':'Virtual Machine',
    'microsoft.recoveryservices/vaults':'Recovery Services Vault','microsoft.network/virtualnetworks':'Virtual Network',
    'microsoft.network/networkwatchers':'Network Watcher','microsoft.migrate/movecollections':'Resource Mover Collection',
    'microsoft.containerservice/managedclusters':'Azure Kubernetes Service (AKS)','microsoft.keyvault/vaults':'Key Vault',
    'microsoft.network/applicationgateways':'Application Gateway','microsoft.network/applicationgatewaywebapplicationfirewallpolicies':'Web Application Firewall Policy',
    'microsoft.automation/automationaccounts':'Automation Account','microsoft.automation/automationaccounts/runbooks':'Automation Runbook',
    'microsoft.dbforpostgresql/flexibleservers':'Azure Database for PostgreSQL Flexible Server','microsoft.dbformysql/flexibleservers':'Azure Database for MySQL Flexible Server',
    'microsoft.sqlvirtualmachine/sqlvirtualmachines':'SQL Virtual Machine','microsoft.alertsmanagement/smartdetectoralertrules':'Smart Detector Alert Rule',
    'microsoft.cache/redis':'Azure Cache for Redis','microsoft.cache/redisenterprise':'Azure Cache for Redis Enterprise',
    'microsoft.eventhub/namespaces':'Event Hubs Namespace','microsoft.web/serverfarms':'App Service Plan','microsoft.web/sites':'App Service',
    'microsoft.insights/datacollectionendpoints':'Data Collection Endpoint','microsoft.network/bastionhosts':'Azure Bastion',
    'microsoft.sql/servers':'Azure SQL Server','microsoft.sql/servers/databases':'SQL Database','microsoft.sql/servers/elasticpools':'SQL Elastic Pool',
    'microsoft.compute/galleries':'Azure Compute Gallery','microsoft.compute/galleries/images':'Compute Gallery Image Definition',
    'microsoft.compute/galleries/images/versions':'Compute Gallery Image Version','microsoft.containerregistry/registries':'Azure Container Registry',
    'microsoft.containerregistry/registries/replications':'Container Registry Replication','microsoft.containerregistry/registries/webhooks':'Container Registry Webhook',
    'microsoft.dataprotection/backupvaults':'Backup Vault','microsoft.insights/components':'Application Insights',
    'microsoft.web/certificates':'App Service Certificate','microsoft.web/sites/slots':'App Service Deployment Slot',
    'microsoft.web/connectiongateways':'On-premises Data Gateway','microsoft.web/connections':'API Connection',
    'microsoft.kubernetesconfiguration/privatelinkscopes':'Azure Arc Private Link Scope','github.network/networksettings':'GitHub Network Settings',
    'microsoft.compute/images':'Managed Image','microsoft.devtestlab/schedules':'DevTest Labs Schedule',
    'microsoft.network/natgateways':'NAT Gateway','microsoft.network/publicipprefixes':'Public IP Prefix',
    'microsoft.network/applicationsecuritygroups':'Application Security Group','microsoft.insights/activitylogalerts':'Activity Log Alert',
    'microsoft.network/ddosprotectionplans':'DDoS Protection Plan','microsoft.security/automations':'Microsoft Defender for Cloud Automation',
    'microsoft.insights/actiongroups':'Action Group','microsoft.insights/metricalerts':'Metric Alert','microsoft.insights/scheduledqueryrules':'Log Search Alert Rule',
    'microsoft.compute/capacityreservationgroups':'Capacity Reservation Group','microsoft.compute/capacityreservationgroups/capacityreservations':'Capacity Reservation',
    'microsoft.migrate/assessmentprojects':'Azure Migrate Assessment Project','microsoft.migrate/migrateprojects':'Azure Migrate Project',
    'microsoft.offazure/mastersites':'Azure Migrate Appliance Site','microsoft.offazure/serversites':'Azure Migrate Server Site','microsoft.offazure/vmwaresites':'Azure Migrate VMware Site',
    'microsoft.certificateregistration/certificateorders':'App Service Certificate Order','microsoft.saas/resources':'SaaS Resource',
    'microsoft.compute/sshpublickeys':'SSH Key','microsoft.confluent/organizations':'Confluent Organization','microsoft.insights/workbooks':'Azure Workbook',
    'microsoft.servicebus/namespaces':'Service Bus Namespace','microsoft.app/containerapps':'Container App','microsoft.app/managedenvironments':'Container Apps Environment',
    'microsoft.app/managedenvironments/certificates':'Container Apps Environment Certificate','microsoft.app/jobs':'Container Apps Job',
    'microsoft.containerinstance/containergroups':'Container Instance','microsoft.search/searchservices':'Azure AI Search',
    'microsoft.fabric/capacities':'Microsoft Fabric Capacity','microsoft.datafactory/factories':'Azure Data Factory',
    'microsoft.cognitiveservices/accounts/projects':'Azure AI Foundry Project','microsoft.documentdb/databaseaccounts':'Azure Cosmos DB Account',
    'microsoft.documentdb/mongoclusters':'Azure Cosmos DB for MongoDB vCore Cluster','microsoft.resources/templatespecs':'Template Spec',
    'microsoft.resources/templatespecs/versions':'Template Spec Version','microsoft.keyvault/managedhsms':'Managed HSM',
    'microsoft.eventgrid/systemtopics':'Event Grid System Topic','microsoft.maintenance/maintenanceconfigurations':'Maintenance Configuration',
    'microsoft.desktopvirtualization/applicationgroups':'Azure Virtual Desktop Application Group','microsoft.desktopvirtualization/hostpools':'Azure Virtual Desktop Host Pool',
    'microsoft.desktopvirtualization/workspaces':'Azure Virtual Desktop Workspace','microsoft.powerbidedicated/capacities':'Power BI Embedded Capacity',
    'microsoft.compute/availabilitysets':'Availability Set','microsoft.network/connections':'VPN Connection',
    'microsoft.network/expressroutecircuits':'ExpressRoute Circuit','microsoft.network/virtualnetworkgateways':'Virtual Network Gateway',
    'microsoft.botservice/botservices':'Azure Bot Service','microsoft.logic/workflows':'Logic App',
    'microsoft.portal/dashboards':'Azure Portal Dashboard','microsoft.purview/accounts':'Microsoft Purview Account',
    'microsoft.web/staticsites':'Static Web App','microsoft.network/dnszones':'DNS Zone','microsoft.visualstudio/account':'Azure DevOps Organization',
    'microsoft.alertsmanagement/prometheusrulegroups':'Prometheus Rule Group','microsoft.monitor/accounts':'Azure Monitor Workspace',
    'microsoft.databricks/accessconnectors':'Azure Databricks Access Connector','microsoft.databricks/workspaces':'Azure Databricks Workspace',
    'microsoft.apimanagement/service':'API Management Service','microsoft.appconfiguration/configurationstores':'App Configuration Store',
    'microsoft.insights/webtests':'Application Insights Availability Test','microsoft.network/networkintentpolicies':'Network Intent Policy',
    'microsoft.fileshares/fileshares':'Azure File Share','microsoft.machinelearningservices/workspaces':'Azure Machine Learning Workspace',
    'microsoft.network/networkprofiles':'Network Profile','microsoft.azureactivedirectory/b2cdirectories':'Azure AD B2C Tenant',
    'microsoft.cdn/profiles':'Front Door/CDN Profile','microsoft.cdn/profiles/endpoints':'CDN Endpoint',
    'microsoft.datamigration/services':'Azure Database Migration Service','microsoft.datamigration/services/projects':'Database Migration Project',
    'microsoft.network/dnsresolvers':'DNS Private Resolver','microsoft.network/dnsresolvers/inboundendpoints':'DNS Resolver Inbound Endpoint',
    'microsoft.datashare/accounts':'Azure Data Share Account','microsoft.logic/integrationaccounts':'Integration Account',
    'microsoft.communication/communicationservices':'Azure Communication Services','microsoft.communication/emailservices':'Email Communication Service',
    'microsoft.communication/emailservices/domains':'Email Communication Domain','microsoft.syntex/accounts':'Microsoft Syntex Account',
    'microsoft.domainregistration/domains':'App Service Domain','microsoft.network/networksecurityperimeters':'Network Security Perimeter',
    'microsoft.synapse/workspaces':'Azure Synapse Workspace','microsoft.synapse/workspaces/bigdatapools':'Apache Spark Pool',
    'microsoft.storagesync/storagesyncservices':'Storage Sync Service','microsoft.network/trafficmanagerprofiles':'Traffic Manager Profile',
    'microsoft.operationalinsights/querypacks':'Log Analytics Query Pack','microsoft.resourcegraph/queries':'Resource Graph Query'
  };
  const typeLabel=type=>{const raw=String(type||'').trim(),key=raw.toLowerCase();if(resourceTypeLabels[key])return resourceTypeLabels[key];const leaf=(raw.replace(/^[^/]+\//,'').split('/').pop()||raw).replace(/[-_]+/g,' ').replace(/([a-z0-9])([A-Z])/g,'$1 $2');return leaf.replace(/\b\w/g,c=>c.toUpperCase())||'Tipo não informado'};
  const shortResourceName=(id,name)=>{const raw=String(id||'').replace(/\/+$/,'').split('/').pop();try{return decodeURIComponent(raw||name||'Recurso sem nome')}catch(_){return raw||name||'Recurso sem nome'}};
  const globalFilters={ambiente:'',bu:'',capex:'',type:'',search:''};
  const matchesGlobal=i=>(!globalFilters.ambiente||val('AMBIENTE',i)===globalFilters.ambiente)&&(!globalFilters.bu||val('BU',i)===globalFilters.bu)&&(!globalFilters.capex||val('CAPEX',i)===globalFilters.capex)&&(!globalFilters.type||DI.type[R.t[i]]===globalFilters.type)&&(!globalFilters.search||`${R.n[i]} ${R.id[i]} ${D.rgs[R.g[i]][0]} ${D.subs[R.s[i]].name}`.toLowerCase().includes(globalFilters.search));
  const baseIdxsV2=idxs;idxs=()=>baseIdxsV2().filter(matchesGlobal);
  const eligibleIndexes=()=>{const out=[];for(let i=0;i<N;i++)if(R.sc[i]&&matchesGlobal(i))out.push(i);return out};
  const observedSubscriptionIds=ix=>new Set(ix.map(i=>String(D.subs[R.s[i]]?.id||'').toLowerCase()));
  const masterSubscriptions=()=>Array.isArray(governanceConfig?.subscriptions)?governanceConfig.subscriptions:[];
  const icon=(name,cls='')=>`<img class="azure-icon ${cls}" src="${iconBase+name}" alt="">`;

  document.body.classList.add('scope-v2');
  const headerRow=document.querySelector('.top .hrow');
  const oldBrandMark=document.querySelector('.evertec-mark');
  if(oldBrandMark)oldBrandMark.remove();
  if(headerRow){
    headerRow.insertAdjacentHTML('afterbegin',`<div class="partner-brand" aria-label="Solo Network e Evertec">
      <span class="partner-logo-slot solo-slot"><img id="soloThemeLogo" src="/assets/solo-white.png" alt="Solo Network"></span>
      <span class="partner-amp" aria-hidden="true">&amp;</span>
      <span class="partner-logo-slot evertec-slot"><img id="evertecThemeLogo" src="/assets/evertec-white.png" alt="Evertec"></span>
    </div>`);
    const meta=headerRow.querySelector('.meta');
    if(meta){
      const tools=document.createElement('div');tools.className='header-tools';tools.setAttribute('aria-label','Controles de visualização');
      tools.innerHTML='<button type="button" class="header-tool" id="themeBtn" title="Alternar tema claro e escuro">DARK</button><button type="button" class="header-tool" id="fontBtn" title="Alternar tamanho da fonte">FONTE: NORMAL</button>';
      const presentation=$('presentationBtn'),print=$('printBtn');
      if(presentation){presentation.className='header-tool';presentation.textContent='APRESENTAR';tools.appendChild(presentation)}
      if(print){print.className='header-tool';print.textContent='PDF';tools.appendChild(print)}
      meta.insertBefore(tools,meta.firstChild);
    }
  }

  const themeBtn=$('themeBtn'),fontBtn=$('fontBtn'),soloLogo=$('soloThemeLogo'),evertecLogo=$('evertecThemeLogo');
  function applyTheme(theme){
    const dark=theme==='dark';document.body.classList.toggle('dark-theme',dark);
    soloLogo.src='/assets/solo-white.png';
    evertecLogo.src='/assets/evertec-white.png';
    themeBtn.textContent=dark?'LIGHT':'DARK';themeBtn.setAttribute('aria-pressed',String(dark));
    try{localStorage.setItem('governanca-theme',dark?'dark':'light')}catch(_){ }
  }
  let savedTheme='light';try{savedTheme=localStorage.getItem('governanca-theme')||'light'}catch(_){ }
  applyTheme(savedTheme);themeBtn.addEventListener('click',()=>applyTheme(document.body.classList.contains('dark-theme')?'light':'dark'));

  const fontModes=[['font-normal','FONTE: NORMAL'],['font-large','FONTE: GRANDE'],['font-xlarge','FONTE: EXTRA GRANDE']];
  let fontIndex=0;try{fontIndex=Math.max(0,Math.min(2,+localStorage.getItem('governanca-font')||0))}catch(_){ }
  function applyFont(){document.body.classList.remove(...fontModes.map(x=>x[0]));document.body.classList.add(fontModes[fontIndex][0]);fontBtn.textContent=fontModes[fontIndex][1];try{localStorage.setItem('governanca-font',String(fontIndex))}catch(_){ }syncHeaderHeight()}
  fontBtn.addEventListener('click',()=>{fontIndex=(fontIndex+1)%fontModes.length;applyFont()});

  const syncHeaderHeight=()=>document.documentElement.style.setProperty('--header-height',`${document.querySelector('.top')?.offsetHeight||0}px`);
  new ResizeObserver(syncHeaderHeight).observe(document.querySelector('.top'));
  syncHeaderHeight();
  applyFont();
  const presentationBtn=$('presentationBtn');
  if(presentationBtn){
    const syncPresentation=()=>{const active=!!document.fullscreenElement;document.body.classList.toggle('presentation-mode',active);presentationBtn.textContent=active?'SAIR':'APRESENTAR';presentationBtn.setAttribute('aria-pressed',String(active));syncHeaderHeight()};
    document.addEventListener('fullscreenchange',syncPresentation);syncPresentation();
  }
  const evidence=document.querySelector('.evidence-strip');
  if(evidence){evidence.children[0].innerHTML='<b>Recursos elegíveis de Governança</b> · mg-evertecbrasil';evidence.children[1].textContent='Subscriptions corporativas e recursos observados são universos separados';}
  evidence?.insertAdjacentHTML('afterend',`<div class="global-filter-bar" aria-label="Filtros rápidos globais"><div class="global-filter-title"><b>Filtros rápidos</b><span id="globalFilterCount"></span></div><label>AMBIENTE<select id="globalAmbiente"><option value="">Todos</option></select></label><label>BU<select id="globalBu"><option value="">Todas</option></select></label><label>CAPEX<select id="globalCapex"><option value="">Todos</option></select></label><label>TIPO<select id="globalType"><option value="">Todos</option></select></label><label class="global-search">BUSCAR<input id="globalSearch" type="search" placeholder="Recurso, RG, Subscription ou ID"></label><button class="action-btn" id="globalClear">Limpar</button></div>`);
  function refreshGlobalFilterOptions(){const all=[];for(let i=0;i<N;i++)if(R.sc[i])all.push(i);const fill=(id,values,label,key)=>{const el=$(id),current=globalFilters[key],items=[...new Set(values.filter(Boolean))].sort((a,b)=>(key==='type'?typeLabel(a):a).localeCompare(key==='type'?typeLabel(b):b,'pt-BR'));el.innerHTML=`<option value="">${label}</option>`+items.map(x=>`<option value="${esc(x)}">${esc(key==='type'?typeLabel(x):x)}</option>`).join('');if([...el.options].some(o=>o.value===current))el.value=current};fill('globalAmbiente',all.map(i=>val('AMBIENTE',i)),'Todos','ambiente');fill('globalBu',all.map(i=>val('BU',i)),'Todas','bu');fill('globalCapex',all.map(i=>val('CAPEX',i)),'Todos','capex');fill('globalType',all.map(i=>DI.type[R.t[i]]),'Todos','type');$('globalFilterCount').textContent=`${fmt(eligibleIndexes().length)} recursos no universo atual`}
  function applyGlobalFilters(){globalFilters.ambiente=$('globalAmbiente').value;globalFilters.bu=$('globalBu').value;globalFilters.capex=$('globalCapex').value;globalFilters.type=$('globalType').value;globalFilters.search=$('globalSearch').value.trim().toLowerCase();$('globalFilterCount').textContent=`${fmt(eligibleIndexes().length)} recursos no universo atual`;detailOptions();render()}
  ['globalAmbiente','globalBu','globalCapex','globalType'].forEach(id=>$(id).addEventListener('change',applyGlobalFilters));let globalTimer;$('globalSearch').addEventListener('input',()=>{clearTimeout(globalTimer);globalTimer=setTimeout(applyGlobalFilters,160)});$('globalClear').addEventListener('click',()=>{Object.keys(globalFilters).forEach(k=>globalFilters[k]='');$('globalSearch').value='';refreshGlobalFilterOptions();detailOptions();render()});

  $('p-exec').innerHTML=`
    <div class="grid" id="execKpisV2"></div>
    <div class="grid">
      <div class="panel c7"><h2>Preenchimento × classificação</h2><p class="sub">INDEFINIDO conta como preenchimento técnico, mas não como classificação definitiva.</p><div class="legend"><span><i style="background:var(--ok)"></i>Informado</span><span><i style="background:var(--warn)"></i>INDEFINIDO</span><span><i style="background:var(--bad)"></i>Vazio</span></div><div id="stackTagsV2"></div></div>
      <div class="panel c5"><h2>Tipos de recursos mais presentes</h2><p class="sub">Recursos elegíveis na fotografia atual.</p><div class="type-grid" id="typesV2"></div></div>
    </div>
    <div class="grid">
      <div class="panel c8"><div class="hrow"><div><h2>Visão das assinaturas</h2><p class="sub">O cadastro corporativo não depende de a assinatura possuir recursos na coleta.</p></div><button class="action-btn" id="openSubscriptionsV2">Abrir detalhamento</button></div><div class="subscription-summary" id="subscriptionSummaryV2"></div><div id="subscriptionCoverageV2"></div></div>
      <div class="panel c4"><h2>Azure Policy</h2><p class="sub">Indicadores informados pelo portal; não são recalculados pelos CSVs.</p><div class="policy" id="policyV2"></div><p class="note info" style="margin:14px 0 0">Compliance geral e iniciativas de Tags são indicadores diferentes.</p></div>
    </div>
    <div class="panel"><div class="hrow"><div><h2>Assinaturas no escopo</h2><p class="sub">Cadastro completo do escopo, incluindo assinaturas sem recursos elegíveis na fotografia atual.</p></div><div class="subscription-filters"><input id="subscriptionSearchV2" type="search" placeholder="Buscar nome ou ID"><select id="subscriptionMgV2"><option value="">Todos os Management Groups</option></select><select id="subscriptionStatusV2"><option value="">Todos os status</option><option value="ACTIVE">Ativas</option><option value="DISABLED">Desativadas</option></select><select id="subscriptionPresenceV2"><option value="">Com e sem recursos</option><option value="with">Com recursos</option><option value="without">Sem recursos</option></select></div></div><div class="result-count" id="subscriptionCountV2"></div><div class="tbl scroll subscriptions-table"><table id="subscriptionPreviewV2"></table></div></div>`;

  function stackRow(tag,ix){
    if(tag==='FOLIO')ix=ix.filter(i=>val('CAPEX',i)==='SIM');
    const s=tstat(tag,ix),w=x=>s.n?100*x/s.n:0;
    return `<div class="srow"><div class="lab">${tag}</div><div class="sbar">${s.cl?`<span style="width:${w(s.cl)}%;background:var(--ok)"></span>`:''}${s.ind?`<span style="width:${w(s.ind)}%;background:var(--warn)"></span>`:''}${s.vz?`<span style="width:${Math.max(.6,w(s.vz))}%;background:var(--bad)"></span>`:''}</div><div class="vals"><b>${pct(s.fill,s.n)}</b> preench. · <b>${pct(s.cl,s.n)}</b> informado</div></div>`;
  }
  renderExec=function(){
    const ix=eligibleIndexes(),observed=observedSubscriptionIds(ix),rgs=new Set(ix.map(i=>R.g[i]));
    const master=masterSubscriptions(),active=master.filter(x=>norm(x.status)==='ACTIVE'),inScope=master.filter(x=>x.inScope),activeScope=inScope.filter(x=>norm(x.status)==='ACTIVE'),without=activeScope.filter(x=>!observed.has(String(x.id).toLowerCase()));
    const cliente=tstat('CLIENTE',ix),produto=tstat('PRODUTO',ix),folioBase=ix.filter(i=>val('CAPEX',i)==='SIM'),folio=tstat('FOLIO',folioBase);
    const cards=[
      ['subscription.svg','Subscriptions corporativas',master.length||D.subs.length,`${active.length||'—'} ativas · ${master.filter(x=>norm(x.status)==='DISABLED').length||0} desativadas`],
      ['subscription.svg','Ativas no escopo',activeScope.length||'—',`${inScope.length||'—'} marcadas como escopo Sim`],
      ['all-resources.svg','Com recursos elegíveis',observed.size,'subscriptions observadas nesta coleta'],
      ['resource-group.svg','Resource Groups',rgs.size,'com ao menos um recurso elegível'],
      ['resource-graph.svg','Recursos elegíveis',ix.length,'ResourceId distinto'],
      ['managed-identity.svg','CLIENTE classificado',pct(cliente.cl,cliente.n),`${fmt(cliente.cl)} de ${fmt(cliente.n)}`],
      ['solution.svg','PRODUTO classificado',pct(produto.cl,produto.n),`${fmt(produto.cl)} de ${fmt(produto.n)}`],
      ['dashboard.svg','Cobertura FOLIO',D.meta?.folioCollected?pct(folio.fill,folio.n):'—',D.meta?.folioCollected?`${fmt(folio.fill)} de ${fmt(folio.n)} CAPEX=SIM`:'FOLIO não coletado']
    ];
    $('execKpisV2').innerHTML=cards.map(c=>`<div class="panel kpi c3"><div class="kpi-head"><div><div class="eyebrow">${c[1]}</div><div class="v">${typeof c[2]==='number'?fmt(c[2]):c[2]}</div></div>${icon(c[0])}</div><div class="d">${c[3]}</div></div>`).join('');
    $('stackTagsV2').innerHTML=TAGS.map(t=>stackRow(t,ix)).join('');
    const tm=new Map();for(const i of ix){const t=DI.type[R.t[i]];tm.set(t,(tm.get(t)||0)+1)}const top=[...tm].sort((a,b)=>b[1]-a[1]).slice(0,10);
    $('typesV2').innerHTML=top.map(([t,n])=>`<div class="type-row">${icon(resourceIcon(t).split('/').pop(),'sm')}<div class="name" title="${esc(t)}">${esc(typeLabel(t))}</div><div class="count">${fmt(n)}</div></div>`).join('');
    $('subscriptionSummaryV2').innerHTML=[['Total corporativo',master.length||'—'],['Ativas no escopo',activeScope.length||'—'],['Com recursos elegíveis',observed.size],['Sem recursos elegíveis',master.length?without.length:'—']].map(x=>`<div><b>${typeof x[1]==='number'?fmt(x[1]):x[1]}</b><span>${x[0]}</span></div>`).join('');
    const den=activeScope.length||observed.size,covered=master.length?activeScope.filter(x=>observed.has(String(x.id).toLowerCase())).length:observed.size;
    $('subscriptionCoverageV2').innerHTML=`<div class="coverage-bar"><span style="width:${den?100*covered/den:0}%;background:var(--accent)"></span></div><div class="muted">${fmt(covered)} de ${fmt(den)} assinaturas ativas do escopo possuem recursos elegíveis nesta fotografia.</div>`;
    $('policyV2').innerHTML=`<div><div class="eyebrow">Geral</div><div class="kpi"><div class="v">≈98%</div></div><div class="gauge"><span style="width:98%"></span></div></div><div><div class="eyebrow">Tags</div><div class="kpi"><div class="v">100%</div></div><div class="gauge"><span style="width:100%"></span></div></div>`;
    renderSubscriptionListV2(ix,master);
  };

  function renderSubscriptionListV2(ix,master=masterSubscriptions()){
    const base=master.length?master.filter(x=>x.inScope):D.subs.filter(x=>x.inScope).map(x=>({name:x.name,id:x.id,status:'',managementGroup:'',inScope:true}));
    const mg=$('subscriptionMgV2'),currentMg=mg.value,mgs=[...new Set(base.map(x=>x.managementGroup).filter(Boolean))].sort();mg.innerHTML='<option value="">Todos os Management Groups</option>'+mgs.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');if(mgs.includes(currentMg))mg.value=currentMg;
    const q=$('subscriptionSearchV2').value.trim().toLowerCase(),status=$('subscriptionStatusV2').value,presence=$('subscriptionPresenceV2').value;
    const rows=base.map(s=>{const si=D.subs.findIndex(x=>String(x.id).toLowerCase()===String(s.id).toLowerCase()),n=si<0?0:ix.filter(i=>R.s[i]===si).length;return {...s,n}}).filter(s=>(!q||`${s.name} ${s.id}`.toLowerCase().includes(q))&&(!mg.value||s.managementGroup===mg.value)&&(!status||norm(s.status)===status)&&(!presence||(presence==='with'?s.n>0:s.n===0)));
    $('subscriptionCountV2').textContent=`${fmt(rows.length)} de ${fmt(base.length)} assinaturas do escopo`;
    $('subscriptionPreviewV2').innerHTML=`<thead><tr><th>Subscription</th><th>Status</th><th>Management Group</th><th>Recursos elegíveis</th><th>Situação</th></tr></thead><tbody>${rows.map(s=>`<tr><td><b>${esc(s.name)}</b><br><span class="muted num">${esc(s.id)}</span></td><td>${esc(s.status||'—')}</td><td>${esc(s.managementGroup||'—')}</td><td class="r">${fmt(s.n)}</td><td>${s.n?'<span class="scope-state good">Com recursos</span>':'<span class="scope-state off">Sem recursos elegíveis</span>'}</td></tr>`).join('')||'<tr><td colspan="5" class="muted">Nenhuma assinatura encontrada para os filtros selecionados.</td></tr>'}</tbody>`;
  }

  const oldRenderTags=renderTags;
  renderTags=function(){
    oldRenderTags();const ix=eligibleIndexes();
    if($('deParaPanel'))$('deParaPanel').hidden=true;
    if(curTag==='CCOWNER')for(const p of [...$('tagVariants').querySelectorAll('p')])if(/De\/Para|tabela abaixo/i.test(p.textContent))p.remove();
    if(!$('tagTypesV2')){$('p-tags').querySelector('.grid:nth-of-type(2)')?.insertAdjacentHTML('afterend','<div class="panel"><h2>Contexto por tipo de recurso</h2><p class="sub">Onde a Tag selecionada está concentrada.</p><div class="type-grid" id="tagTypesV2"></div></div>');}
    const base=curTag==='FOLIO'?ix.filter(i=>val('CAPEX',i)==='SIM'):ix,s=tstat(curTag,base);
    if(curTag==='FOLIO'){
      $('tagKpis').innerHTML=[['Preenchida',s.fill,pct(s.fill,s.n)],['Informada',s.cl,pct(s.cl,s.n)],['INDEFINIDO',s.ind,pct(s.ind,s.n)],['Vazia / inexistente',s.vz,pct(s.vz,s.n)]].map(k=>`<div class="panel kpi c3"><div class="eyebrow">FOLIO · ${k[0]}</div><div class="v">${fmt(k[1])}<small>${k[2]}</small></div><div class="d">de ${fmt(s.n)} recursos CAPEX=SIM</div></div>`).join('');
      $('tagDistSub').textContent=`Distribuição somente entre ${fmt(base.length)} recursos CAPEX=SIM. Recursos CAPEX=NAO não entram no denominador.`;
      $('tagDist').insertAdjacentHTML('beforebegin','<div id="folioContextV2" class="folio-context">Universo elegível do FOLIO: somente recursos com CAPEX=SIM.</div>');
    } else $('folioContextV2')?.remove();
    const byType=new Map();for(const i of base){const t=DI.type[R.t[i]],o=byType.get(t)||{n:0,filled:0};o.n++;if(val(curTag,i)!=null)o.filled++;byType.set(t,o)}
    $('tagTypesV2').innerHTML=[...byType].sort((a,b)=>b[1].n-a[1].n).slice(0,10).map(([t,o])=>`<div class="type-row">${icon(resourceIcon(t).split('/').pop(),'sm')}<div class="name">${esc(typeLabel(t))}<small class="muted"> · ${pct(o.filled,o.n)} preenchida</small></div><div class="count">${fmt(o.n)}</div></div>`).join('');
  };

  $('p-det').innerHTML=`<div class="panel"><div class="detail-filters">
    <label>Nível<select id="detailLevelV2"><option value="resources">Recursos</option><option value="resourceGroups">Resource Groups</option><option value="subscriptions">Subscriptions</option></select></label>
    <label>Subscription<select id="detailSubV2"><option value="">Todas</option></select></label><label>Resource Group<select id="detailRgV2"><option value="">Todos</option></select></label><label>Tipo de recurso<input type="search" id="detailTypeV2" list="detailTypeOptionsV2" placeholder="Digite para buscar"><datalist id="detailTypeOptionsV2"></datalist></label><label>Pendência<select id="detailPendingV2"><option value="">Todas</option><option value="classification">CLIENTE/PRODUTO</option><option value="folio">FOLIO em CAPEX=SIM</option><option value="folioNo">FOLIO em CAPEX=NAO</option></select></label><label>Buscar<input type="search" id="detailSearchV2" placeholder="Nome, RG ou ResourceId"></label>
    </div><div class="filter-actions"><div class="result-count" id="detailCountV2"></div><div><button class="action-btn" id="clearDetailV2">Limpar filtros</button> <button class="action-btn primary" id="exportDetailV2">Exportar CSV</button></div></div></div><div class="panel"><div class="detail-table tbl"><table id="detailTableV2"></table></div></div>`;
  function detailOptions(){
    const ix=eligibleIndexes(),subs=[...new Set(ix.map(i=>D.subs[R.s[i]].name))].sort(),rgs=[...new Set(ix.map(i=>D.rgs[R.g[i]][0]))].sort(),types=[...new Set(ix.map(i=>DI.type[R.t[i]]))].sort((a,b)=>typeLabel(a).localeCompare(typeLabel(b),'pt-BR'));
    $('detailSubV2').innerHTML='<option value="">Todas</option>'+subs.map(x=>`<option>${esc(x)}</option>`).join('');$('detailRgV2').innerHTML='<option value="">Todos</option>'+rgs.map(x=>`<option>${esc(x)}</option>`).join('');$('detailTypeOptionsV2').innerHTML=types.map(x=>`<option value="${esc(typeLabel(x))}" label="${esc(x)}"></option>`).join('');
  }
  function filteredResources(){const q=$('detailSearchV2').value.trim().toLowerCase(),sub=$('detailSubV2').value,rg=$('detailRgV2').value,type=norm($('detailTypeV2').value),p=$('detailPendingV2').value,knownTypes=[...new Set(eligibleIndexes().map(i=>DI.type[R.t[i]]))],exactType=knownTypes.find(t=>norm(typeLabel(t))===type);return eligibleIndexes().filter(i=>{const sv=D.subs[R.s[i]].name,rv=D.rgs[R.g[i]][0],tv=DI.type[R.t[i]],folio=val('FOLIO',i),typeText=norm(`${typeLabel(tv)} ${tv}`);if(sub&&sv!==sub||rg&&rv!==rg||exactType&&tv!==exactType||type&&!exactType&&!typeText.includes(type))return false;if(q&&!(`${R.n[i]} ${R.id[i]} ${rv} ${sv}`.toLowerCase().includes(q)))return false;if(p==='classification'&&!isPend(i))return false;if(p==='folio'&&!(val('CAPEX',i)==='SIM'&&folio==null))return false;if(p==='folioNo'&&!(val('CAPEX',i)==='NAO'&&folio!=null))return false;return true})}
  const cell=v=>v==null?'<span class="pill bad">vazio</span>':v==='INDEFINIDO'?'<span class="pill warn">INDEFINIDO</span>':esc(v);
  renderDet=function(){
    const level=$('detailLevelV2').value,ix=filteredResources();
    if(level==='subscriptions'){
      const master=masterSubscriptions(),subFilter=$('detailSubV2').value,q=$('detailSearchV2').value.trim().toLowerCase(),rows=master.filter(s=>(!subFilter||s.name===subFilter)&&(!q||`${s.name} ${s.id} ${s.managementGroup}`.toLowerCase().includes(q)));$('detailCountV2').textContent=`${fmt(rows.length)} de ${fmt(master.length)} assinaturas cadastradas`;
      $('detailTableV2').innerHTML=`<thead><tr><th>Subscription</th><th>Status</th><th>Management Group</th><th>Escopo</th><th>Recursos elegíveis</th><th>Situação</th></tr></thead><tbody>${rows.map(s=>{const si=D.subs.findIndex(x=>String(x.id).toLowerCase()===String(s.id).toLowerCase()),n=si<0?0:ix.filter(i=>R.s[i]===si).length;return `<tr><td><b>${esc(s.name)}</b><br><span class="muted num">${esc(s.id)}</span></td><td>${esc(s.status)}</td><td>${esc(s.managementGroup)}</td><td>${s.inScope?'<span class="scope-state good">Sim</span>':'<span class="scope-state off">Não</span>'}</td><td class="r">${fmt(n)}</td><td>${norm(s.status)==='DISABLED'?'<span class="scope-state bad">Desativada</span>':n?'<span class="scope-state good">Com recursos</span>':'<span class="scope-state off">Sem recursos elegíveis</span>'}</td></tr>`}).join('')}</tbody>`;return;
    }
    if(level==='resourceGroups'){
      const m=new Map();for(const i of ix){const k=String(D.subs[R.s[i]].id).toLowerCase()+'|'+D.rgs[R.g[i]][0].toLowerCase(),o=m.get(k)||{sub:D.subs[R.s[i]].name,rg:D.rgs[R.g[i]][0],n:0,p:0};o.n++;if(isPend(i))o.p++;m.set(k,o)}const rows=[...m.values()].sort((a,b)=>b.n-a.n);$('detailCountV2').textContent=`${fmt(rows.length)} Resource Groups encontrados`;$('detailTableV2').innerHTML=`<thead><tr><th>Resource Group</th><th>Subscription</th><th class="r">Recursos</th><th class="r">Pendências</th><th>Status</th></tr></thead><tbody>${rows.map(o=>`<tr><td><div class="resource-name">${icon('resource-group.svg','sm')}<strong>${esc(o.rg)}</strong></div></td><td>${esc(o.sub)}</td><td class="r">${fmt(o.n)}</td><td class="r">${fmt(o.p)}</td><td>${o.p?'<span class="status-dot warn">Revisar</span>':'<span class="status-dot">Conforme</span>'}</td></tr>`).join('')}</tbody>`;return;
    }
    $('detailCountV2').textContent=`${fmt(ix.length)} recursos encontrados`;$('detailTableV2').innerHTML=`<thead><tr><th>Recurso</th><th>Subscription</th><th>Resource Group</th><th>Tipo</th><th>CAPEX</th><th>FOLIO</th><th>CLIENTE</th><th>PRODUTO</th></tr></thead><tbody>${ix.slice(0,500).map(i=>{const t=DI.type[R.t[i]];return `<tr><td><div class="resource-name" title="${esc(R.id[i])}">${icon(resourceIcon(t).split('/').pop(),'sm')}<strong>${esc(shortResourceName(R.id[i],R.n[i]))}</strong></div></td><td>${esc(D.subs[R.s[i]].name)}</td><td>${esc(D.rgs[R.g[i]][0])}</td><td>${esc(typeLabel(t))}</td><td>${cell(val('CAPEX',i))}</td><td>${cell(val('FOLIO',i))}</td><td>${cell(val('CLIENTE',i))}</td><td>${cell(val('PRODUTO',i))}</td></tr>`}).join('')}</tbody>`+(ix.length>500?`<caption>Mostrando 500 de ${fmt(ix.length)}. Refine os filtros para reduzir o resultado.</caption>`:'');
  };
  ['detailLevelV2','detailSubV2','detailRgV2','detailPendingV2'].forEach(id=>$(id).addEventListener('change',renderDet));let detailTimer;$('detailSearchV2').addEventListener('input',()=>{clearTimeout(detailTimer);detailTimer=setTimeout(renderDet,180)});$('detailTypeV2').addEventListener('input',()=>{clearTimeout(detailTimer);detailTimer=setTimeout(renderDet,140)});$('clearDetailV2').addEventListener('click',()=>{['detailSubV2','detailRgV2','detailTypeV2','detailPendingV2'].forEach(id=>$(id).value='');$('detailSearchV2').value='';renderDet()});
  $('openSubscriptionsV2').addEventListener('click',()=>{openPage('det');$('detailLevelV2').value='subscriptions';renderDet()});
  ['subscriptionMgV2','subscriptionStatusV2','subscriptionPresenceV2'].forEach(id=>$(id).addEventListener('change',()=>renderSubscriptionListV2(eligibleIndexes())));let subscriptionTimer;$('subscriptionSearchV2').addEventListener('input',()=>{clearTimeout(subscriptionTimer);subscriptionTimer=setTimeout(()=>renderSubscriptionListV2(eligibleIndexes()),150)});

  function exportDetailV2(){
    const ix=filteredResources(),level=$('detailLevelV2').value;let headers,rows,name;
    if(level==='resources'){
      headers=['ResourceId','Subscription','ResourceGroup','ResourceName','ResourceType',...TAGS];rows=ix.map(i=>[R.id[i],D.subs[R.s[i]].name,D.rgs[R.g[i]][0],R.n[i],DI.type[R.t[i]],...TAGS.map(t=>val(t,i)||'')]);name='Recursos';
    }else if(level==='resourceGroups'){
      headers=['Subscription','ResourceGroup','Recursos','PendenciasClienteProduto'];const m=new Map();for(const i of ix){const key=`${R.s[i]}|${R.g[i]}`,o=m.get(key)||{sub:D.subs[R.s[i]].name,rg:D.rgs[R.g[i]][0],n:0,p:0};o.n++;if(isPend(i))o.p++;m.set(key,o)}rows=[...m.values()].map(o=>[o.sub,o.rg,o.n,o.p]);name='ResourceGroups';
    }else{
      headers=['SubscriptionId','Subscription','Status','ManagementGroup','NoEscopo','RecursosElegiveis'];const master=masterSubscriptions(),bySub=new Map();for(const i of ix)bySub.set(String(D.subs[R.s[i]].id).toLowerCase(),(bySub.get(String(D.subs[R.s[i]].id).toLowerCase())||0)+1);const subFilter=$('detailSubV2').value,q=$('detailSearchV2').value.trim().toLowerCase();rows=master.filter(s=>(!subFilter||s.name===subFilter)&&(!q||`${s.name} ${s.id} ${s.managementGroup}`.toLowerCase().includes(q))).map(s=>[s.id,s.name,s.status,s.managementGroup,s.inScope?'SIM':'NAO',bySub.get(String(s.id).toLowerCase())||0]);name='Subscriptions';
    }
    const lines=[headers.map(csvCell).join(';'),...rows.map(row=>row.map(csvCell).join(';'))];downloadText(`Detalhamento_${name}_${D.meta?.date||'sem_data'}.csv`,lines.join('\r\n'));
  }
  const oldExport=$('exportDetailV2'),newExport=oldExport.cloneNode(true);oldExport.replaceWith(newExport);newExport.addEventListener('click',exportDetailV2);

  const matrixControls=$('ccOnlyMulti').closest('.ctrls');matrixControls.insertAdjacentHTML('afterbegin','<label>Filtrar BU <select id="buMatrixFilter"><option value="">Todas as BUs</option></select></label>');
  const priorRenderFinV2=renderFin;
  renderFin=function(){
    priorRenderFinV2();const select=$('buMatrixFilter'),current=select.value,bus=[...new Set(eligibleIndexes().map(i=>val('BU',i)||'(vazio)'))].sort();select.innerHTML='<option value="">Todas as BUs</option>'+bus.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');if(bus.includes(current))select.value=current;
    let visible=!select.value;for(const tr of $('buccTbl').tBodies[0]?.rows||[]){if(tr.classList.contains('grp'))visible=!select.value||norm(tr.cells[0].textContent)===norm(select.value);tr.hidden=!visible}
    for(const tr of [...$('capexBox').querySelectorAll('tbody tr')])if(norm(tr.cells[0]?.textContent).startsWith('FOLIO PREENCHIDO'))tr.remove();const note=$('capexBox').querySelector('.note');if(note&&/depende da coluna FOLIO/i.test(note.textContent))note.remove();
  };
  $('buMatrixFilter').addEventListener('change',renderFin);
  $('ccOnlyMulti').addEventListener('change',()=>renderFin());

  const evoTab=$('tabs').querySelector('[data-p="evo"]');evoTab.textContent='Análise Avançada';
  $('p-evo').innerHTML=`<div class="panel advanced-builder"><div class="hrow"><div><h2>Análise avançada de Governança</h2><p class="sub">Combine Tags e atributos com condições E/OU. Os resultados usam somente os recursos elegíveis da fotografia atual.</p></div><div class="advanced-actions"><button class="action-btn" id="advancedAdd">+ Adicionar condição</button><button class="action-btn" id="advancedClear">Limpar</button><button class="action-btn primary" id="advancedExport">Exportar CSV</button></div></div><div class="advanced-top"><label>Combinar condições<select id="advancedLogic"><option value="AND">Todas (E)</option><option value="OR">Qualquer uma (OU)</option></select></label><label>Resultado por<select id="advancedLevel"><option value="resources">Recursos</option><option value="resourceGroups">Resource Groups</option><option value="subscriptions">Subscriptions relacionadas</option></select></label><label>Buscar no resultado<input id="advancedSearch" type="search" placeholder="Nome, RG, Subscription ou ID"></label></div><div id="advancedRules"></div><datalist id="advancedTypeOptions"></datalist></div><div class="grid" id="advancedKpis"></div><div class="panel"><div class="hrow"><div><h2>Resultado da análise</h2><p class="sub" id="advancedSummary"></p></div></div><div class="detail-table tbl"><table id="advancedTable"></table></div></div>`;
  const advancedFields=[['AMBIENTE','Tag AMBIENTE'],['BU','Tag BU'],['CAPEX','Tag CAPEX'],['CC','Tag CC'],['CCOWNER','Tag CCOWNER'],['CLIENTE','Tag CLIENTE'],['PRODUTO','Tag PRODUTO'],['FOLIO','Tag FOLIO'],['ResourceType','Tipo de recurso'],['ResourceGroup','Resource Group'],['Subscription','Subscription'],['ResourceName','Nome do recurso']];
  const advancedOperators=[['eq','Igual'],['neq','Diferente'],['contains','Contém'],['notcontains','Não contém'],['empty','Está vazio'],['notempty','Não está vazio'],['in','Está em uma lista']];let advancedRules=[];
  function advancedValue(field,i){if(TAGS.includes(field))return val(field,i)||'';if(field==='ResourceType')return typeLabel(DI.type[R.t[i]]||'');if(field==='ResourceGroup')return D.rgs[R.g[i]][0]||'';if(field==='Subscription')return D.subs[R.s[i]].name||'';return R.n[i]||''}
  function advancedMatch(rule,i){const actual=norm(advancedValue(rule.field,i)),expected=norm(rule.value),values=expected.split(',').map(x=>x.trim()).filter(Boolean);if(rule.op==='empty')return !actual;if(rule.op==='notempty')return !!actual;if(rule.op==='eq')return actual===expected;if(rule.op==='neq')return actual!==expected;if(rule.op==='contains')return actual.includes(expected);if(rule.op==='notcontains')return !actual.includes(expected);if(rule.op==='in')return values.includes(actual);return true}
  function advancedIndexes(){const logic=$('advancedLogic').value,q=$('advancedSearch').value.trim().toLowerCase();return eligibleIndexes().filter(i=>(!advancedRules.length||(logic==='AND'?advancedRules.every(r=>advancedMatch(r,i)):advancedRules.some(r=>advancedMatch(r,i))))&&(!q||`${R.n[i]} ${R.id[i]} ${D.rgs[R.g[i]][0]} ${D.subs[R.s[i]].name} ${DI.type[R.t[i]]}`.toLowerCase().includes(q)))}
  function renderAdvancedRules(){const types=[...new Set(eligibleIndexes().map(i=>DI.type[R.t[i]]))].sort((a,b)=>typeLabel(a).localeCompare(typeLabel(b),'pt-BR'));$('advancedTypeOptions').innerHTML=types.map(t=>`<option value="${esc(typeLabel(t))}"></option>`).join('');$('advancedRules').innerHTML=advancedRules.map((r,n)=>`<div class="advanced-rule" data-rule="${n}"><span class="rule-join">${n?$('advancedLogic').value==='AND'?'E':'OU':'ONDE'}</span><select data-key="field">${advancedFields.map(([v,l])=>`<option value="${v}" ${v===r.field?'selected':''}>${l}</option>`).join('')}</select><select data-key="op">${advancedOperators.map(([v,l])=>`<option value="${v}" ${v===r.op?'selected':''}>${l}</option>`).join('')}</select><input data-key="value" value="${esc(r.value)}" ${r.field==='ResourceType'?'list="advancedTypeOptions"':''} placeholder="${r.field==='ResourceType'?'Digite o nome do tipo':`Valor${r.op==='in'?'1, Valor2':''}`}" ${['empty','notempty'].includes(r.op)?'disabled':''}><button class="action-btn danger" data-remove-rule="${n}" aria-label="Remover condição">×</button></div>`).join('')||'<div class="advanced-empty">Nenhuma condição aplicada. O resultado considera todos os recursos elegíveis.</div>';}
  function renderAdvanced(skipRules=false){
    if(!skipRules)renderAdvancedRules();const ix=advancedIndexes(),rgs=new Set(ix.map(i=>`${R.s[i]}|${R.g[i]}`)),subs=new Set(ix.map(i=>R.s[i]));$('advancedKpis').innerHTML=[['Recursos',ix.length],['Resource Groups',rgs.size],['Subscriptions relacionadas',subs.size]].map(x=>`<div class="panel kpi c4"><div class="eyebrow">${x[0]}</div><div class="v">${fmt(x[1])}</div><div class="d">resultado das condições atuais</div></div>`).join('');const level=$('advancedLevel').value;let rows='';
    if(level==='resources')rows=`<thead><tr><th>Recurso</th><th>Tipo</th><th>Subscription</th><th>Resource Group</th><th>AMBIENTE</th><th>BU</th><th>CC</th><th>CAPEX</th><th>CLIENTE</th><th>PRODUTO</th></tr></thead><tbody>${ix.slice(0,500).map(i=>{const t=DI.type[R.t[i]];return `<tr><td><div class="resource-name" title="${esc(R.id[i])}">${icon(resourceIcon(t).split('/').pop(),'sm')}<strong>${esc(shortResourceName(R.id[i],R.n[i]))}</strong></div></td><td>${esc(typeLabel(t))}</td><td>${esc(D.subs[R.s[i]].name)}</td><td>${esc(D.rgs[R.g[i]][0])}</td>${['AMBIENTE','BU','CC','CAPEX','CLIENTE','PRODUTO'].map(tg=>`<td>${cell(val(tg,i))}</td>`).join('')}</tr>`}).join('')}</tbody>`;
    else if(level==='resourceGroups'){const m=new Map();for(const i of ix){const k=`${R.s[i]}|${R.g[i]}`,o=m.get(k)||{sub:D.subs[R.s[i]].name,rg:D.rgs[R.g[i]][0],n:0};o.n++;m.set(k,o)}rows=`<thead><tr><th>Resource Group</th><th>Subscription</th><th class="r">Recursos encontrados</th></tr></thead><tbody>${[...m.values()].sort((a,b)=>b.n-a.n).map(o=>`<tr><td><div class="resource-name">${icon('resource-group.svg','sm')}<strong>${esc(o.rg)}</strong></div></td><td>${esc(o.sub)}</td><td class="r">${fmt(o.n)}</td></tr>`).join('')}</tbody>`}
    else{const m=new Map();for(const i of ix){const k=R.s[i],o=m.get(k)||{id:D.subs[k].id,name:D.subs[k].name,n:0};o.n++;m.set(k,o)}rows=`<thead><tr><th>Subscription</th><th>Subscription ID</th><th class="r">Recursos encontrados</th></tr></thead><tbody>${[...m.values()].sort((a,b)=>b.n-a.n).map(o=>`<tr><td><div class="resource-name">${icon('subscription.svg','sm')}<strong>${esc(o.name)}</strong></div></td><td class="num">${esc(o.id)}</td><td class="r">${fmt(o.n)}</td></tr>`).join('')}</tbody>`}$('advancedTable').innerHTML=rows;$('advancedSummary').textContent=`${fmt(ix.length)} recursos atendem às condições. Exibição limitada a 500 linhas no nível Recursos; a exportação contém todo o resultado.`;
  }
  renderEvo=renderAdvanced;$('advancedAdd').addEventListener('click',()=>{advancedRules.push({field:'AMBIENTE',op:'eq',value:'PRD'});renderAdvanced()});$('advancedClear').addEventListener('click',()=>{advancedRules=[];$('advancedSearch').value='';renderAdvanced()});$('advancedRules').addEventListener('input',e=>{const row=e.target.closest('[data-rule]');if(!row||e.target.dataset.key!=='value')return;advancedRules[+row.dataset.rule].value=e.target.value;renderAdvanced(true)});$('advancedRules').addEventListener('change',e=>{const row=e.target.closest('[data-rule]');if(!row)return;advancedRules[+row.dataset.rule][e.target.dataset.key]=e.target.value;renderAdvanced()});$('advancedRules').addEventListener('click',e=>{const b=e.target.closest('[data-remove-rule]');if(!b)return;advancedRules.splice(+b.dataset.removeRule,1);renderAdvanced()});$('advancedLogic').addEventListener('change',()=>renderAdvanced());$('advancedLevel').addEventListener('change',()=>renderAdvanced(true));let advancedTimer;$('advancedSearch').addEventListener('input',()=>{clearTimeout(advancedTimer);advancedTimer=setTimeout(()=>renderAdvanced(true),150)});$('advancedExport').addEventListener('click',()=>{const ix=advancedIndexes(),headers=['ResourceId','Subscription','ResourceGroup','ResourceName','ResourceType',...TAGS],lines=[headers.map(csvCell).join(';'),...ix.map(i=>[R.id[i],D.subs[R.s[i]].name,D.rgs[R.g[i]][0],R.n[i],DI.type[R.t[i]],...TAGS.map(t=>val(t,i)||'')].map(csvCell).join(';'))];downloadText(`Analise_Avancada_${D.meta?.date||'sem_data'}.csv`,lines.join('\r\n'))});

  function parseSubscriptions(rows){
    const get=(r,...keys)=>{for(const key of keys)if(r[key]!=null)return r[key];return ''};
    const clean=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toUpperCase();
    const parsed=rows.map(r=>({name:get(r,'SUBSCRIPTION NAME','SUBSCRIPTION','NAME').trim(),id:get(r,'SUBSCRIPTION ID','SUBSCRIPTIONID','ID').trim().toLowerCase(),managementGroup:get(r,'PARENT MANAGEMENT GROUP','MANAGEMENT GROUP').trim(),status:get(r,'STATUS','STATE').trim(),inScope:clean(get(r,'MANAGEMENT GROUP (MG-EVERTECBRASIL)?','NO ESCOPO?','IN SCOPE?'))==='SIM'})).filter(x=>x.name&&/^[0-9a-f-]{36}$/.test(x.id));
    if(!parsed.length)throw Error('O cadastro de subscriptions não contém linhas válidas.');return parsed;
  }
  const box=$('p-pbi').querySelector('.import-box'),fields=box.querySelector('.import-fields'),labels=fields.querySelectorAll('label');
  box.querySelector('.sub').textContent='Carregue o CSV de recursos elegíveis da Governança. O cadastro corporativo de subscriptions é um arquivo mestre e só precisa ser reenviado quando houver alteração.';
  labels[0].childNodes[0].nodeValue='1. CSV de recursos elegíveis da Governança';labels[1].hidden=true;labels[2].childNodes[0].nodeValue='3. Data de coleta';
  labels[0].insertAdjacentHTML('afterend','<label>2. Cadastro de subscriptions (opcional)<input id="subscriptionsFileV2" type="file" accept=".csv,text/csv"><small class="muted">Mantém o cadastro atual se não for selecionado.</small></label>');
  const oldButton=$('applyImport'),newButton=oldButton.cloneNode(true);newButton.textContent='Gravar nova fotografia';oldButton.replaceWith(newButton);
  newButton.addEventListener('click',async()=>{const msg=$('importMessage');newButton.disabled=true;try{const file=$('csvFull').files[0];if(!file)throw Error('Selecione o CSV de recursos elegíveis da Governança.');msg.textContent='Lendo e validando os recursos elegíveis…';const parsed=parseCSV(await file.text());let date=$('collectionDate').value;if(!date){const dates=[...new Set(parsed.dates.map(x=>x.slice(0,10)))];if(dates.length===1)date=dates[0]}if(!/^\d{4}-\d{2}-\d{2}$/.test(date||''))throw Error('Informe a Data de Coleta.');if(parsed.dates.some(x=>x.slice(0,10)!==date))throw Error('A DataColeta do arquivo diverge da data selecionada.');const sf=$('subscriptionsFileV2').files[0];if(sf){governanceConfig.subscriptions=parseSubscriptions(simpleCSV(await sf.text()));await saveConfig()}const candidate=buildData(parsed,parsed,{date,fullFile:file.name,scopeFile:file.name,eligibleFile:file.name,subscriptionFile:sf?.name||D.meta?.subscriptionFile||'cadastro persistido',singleScope:true},H);candidate.R.sc=candidate.R.sc.map(()=>1);candidate.subs.forEach(s=>s.inScope=true);msg.textContent='Validação concluída. Gravando fotografia…';await persistSnapshot(candidate);D=candidate;R=D.R;N=R.s.length;DI=D.dict;curTag='AMBIENTE';selSub=null;selRg=null;Object.keys(globalFilters).forEach(k=>globalFilters[k]='');$('globalSearch').value='';refreshGlobalFilterOptions();detailOptions();render();syncEvidence();await loadSnapshotHistory();msg.textContent='Fotografia gravada. O painel agora utiliza somente os recursos elegíveis da Governança.'}catch(error){msg.textContent='Não atualizado: '+error.message}finally{newButton.disabled=false}});

  const originalLoad=loadGovernanceConfig;
  loadGovernanceConfig=async function(){await originalLoad();detailOptions();render()};
  refreshGlobalFilterOptions();detailOptions();render();
  fetch('/api/governance-config').then(response=>response.ok?response.json():null).then(config=>{if(config){governanceConfig=config;detailOptions();render()}}).catch(()=>{});
})();
