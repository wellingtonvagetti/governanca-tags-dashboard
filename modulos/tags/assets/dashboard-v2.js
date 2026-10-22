/* Dashboard executivo v2: universo único de recursos elegíveis + cadastro corporativo de subscriptions. */
(function(){
  'use strict';
  const vmAuditModule=document.body.dataset.module==='auditoria-vms';
  scope='esc';
  const iconBase='/tags/assets/azure-icons/';
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
    ['microsoft.hybridconnectivity/publiccloudconnectors','azure-arc.svg'],
    ['microsoft.hybridcompute/machines/extensions','azure-arc.svg'],
    ['microsoft.azurearcdata/sqlserverinstances','azure-arc.svg'],
    ['microsoft.azurearcdata/sqlserverinstances/databases','azure-arc.svg'],
    ['microsoft.migrate/movecollections','migration.svg'],
    ['microsoft.apimanagement/service','api-management.svg'],['microsoft.web/connections','api-connection.svg'],['microsoft.web/connectiongateways','api-connection.svg'],
    ['microsoft.appconfiguration/configurationstores','app-configuration.svg'],['microsoft.web/certificates','certificate.svg'],['microsoft.certificateregistration/certificateorders','certificate.svg'],['microsoft.app/managedenvironments/certificates','certificate.svg'],
    ['microsoft.domainregistration/domains','app-domain.svg'],['microsoft.web/sites/slots','deployment-slot.svg'],['microsoft.insights/webtests','application-insights.svg'],['microsoft.network/applicationsecuritygroups','application-security-group.svg'],
    ['microsoft.botservice/botservices','bot-service.svg'],['microsoft.communication/communicationservices','communication-services.svg'],['microsoft.communication/emailservices','communication-services.svg'],['microsoft.communication/emailservices/domains','communication-services.svg'],
    ['microsoft.documentdb/databaseaccounts','cosmos-db.svg'],['microsoft.documentdb/mongoclusters','cosmos-db.svg'],['microsoft.datafactory/factories','data-factory.svg'],['microsoft.datashare/accounts','data-share.svg'],
    ['microsoft.dbformysql/flexibleservers','mysql.svg'],['microsoft.datamigration/services','database-migration.svg'],['microsoft.datamigration/services/projects','database-migration.svg'],['microsoft.databricks/accessconnectors','databricks.svg'],['microsoft.databricks/workspaces','databricks.svg'],
    ['microsoft.visualstudio/account','azure-devops.svg'],['github.network/networksettings','azure-devops.svg'],['microsoft.fileshares/fileshares','file-share.svg'],['microsoft.machinelearningservices/workspaces','machine-learning.svg'],['microsoft.cognitiveservices/accounts','machine-learning.svg'],['microsoft.cognitiveservices/accounts/projects','machine-learning.svg'],
    ['microsoft.awsconnector/ec2accountattributes','azure-arc.svg'],['microsoft.awsconnector/ec2addresses','public-ip.svg'],['microsoft.awsconnector/ec2flowlogs','network-watcher.svg'],['microsoft.awsconnector/ec2images','image.svg'],['microsoft.awsconnector/ec2instancestatuses','virtual-machine.svg'],['microsoft.awsconnector/ec2ipams','virtual-network.svg'],['microsoft.awsconnector/ec2keypairs','ssh-key.svg'],['microsoft.awsconnector/ec2networkacls','network-security-group.svg'],['microsoft.awsconnector/ec2networkinterfaces','network-interface.svg'],['microsoft.awsconnector/ec2routetables','route-table.svg'],['microsoft.awsconnector/ec2securitygroups','network-security-group.svg'],['microsoft.awsconnector/ec2subnets','virtual-network.svg'],['microsoft.awsconnector/ec2volumes','disk.svg'],['microsoft.awsconnector/ec2vpcendpoints','private-endpoint.svg'],['microsoft.awsconnector/ec2vpcpeeringconnections','connection.svg'],['microsoft.awsconnector/ec2vpcs','virtual-network.svg'],
    ['microsoft.insights/workbooks','workbook.svg'],['microsoft.compute/capacityreservationgroups','capacity-reservation.svg'],['microsoft.compute/capacityreservationgroups/capacityreservations','capacity-reservation.svg'],['microsoft.compute/galleries/images/versions','compute-gallery.svg'],
    ['microsoft.cdn/profiles','cdn.svg'],['microsoft.cdn/profiles/endpoints','cdn.svg'],['microsoft.confluent/organizations','event-hub.svg'],['microsoft.app/jobs','container-app.svg'],['microsoft.app/managedenvironments','container-environment.svg'],
    ['microsoft.desktopvirtualization/applicationgroups','avd-application-group.svg'],['microsoft.desktopvirtualization/hostpools','avd-host-pool.svg'],['microsoft.desktopvirtualization/workspaces','virtual-desktop.svg'],
    ['microsoft.synapse/workspaces','synapse.svg'],['microsoft.synapse/workspaces/bigdatapools','synapse.svg'],['microsoft.network/trafficmanagerprofiles','traffic-manager.svg'],['microsoft.logic/workflows','logic-app.svg'],['microsoft.logic/integrationaccounts','integration-account.svg'],
    ['microsoft.resources/templatespecs','template-spec.svg'],['microsoft.resources/templatespecs/versions','template-spec.svg'],['microsoft.purview/accounts','purview.svg'],['microsoft.search/searchservices','search.svg'],['microsoft.powerbidedicated/capacities','power-bi.svg'],['microsoft.fabric/capacities','power-bi.svg'],
    ['microsoft.web/staticsites','static-app.svg'],['microsoft.sql/servers/elasticpools','elastic-pool.svg'],['microsoft.storagesync/storagesyncservices','storage-sync.svg'],['microsoft.azureactivedirectory/b2cdirectories','b2c.svg'],
    ['microsoft.network/ddosprotectionplans','ddos.svg'],['microsoft.network/dnsresolvers','dns-resolver.svg'],['microsoft.network/dnsresolvers/inboundendpoints','dns-resolver.svg'],['microsoft.network/networksecurityperimeters','network-security-perimeter.svg'],
    ['microsoft.network/networkintentpolicies','network-security-group.svg'],['microsoft.network/networkprofiles','network-interface.svg'],['microsoft.network/dnszones','private-dns.svg'],['microsoft.network/natgateways','virtual-network-gateway.svg'],['microsoft.network/publicipprefixes','public-ip.svg'],
    ['microsoft.maintenance/maintenanceconfigurations','maintenance.svg'],['microsoft.eventgrid/systemtopics','event-grid.svg'],['microsoft.devtestlab/schedules','schedule.svg'],['microsoft.alertsmanagement/prometheusrulegroups','monitor.svg'],['microsoft.monitor/accounts','monitor.svg'],
    ['microsoft.offazure/mastersites','migration.svg'],['microsoft.offazure/serversites','migration.svg'],['microsoft.offazure/vmwaresites','migration.svg'],['microsoft.migrate/assessmentprojects','migration.svg'],['microsoft.migrate/migrateprojects','migration.svg'],
    ['microsoft.containerregistry/registries/webhooks','container-registry.svg'],['microsoft.security/automations','automation.svg'],['microsoft.saas/resources','solution.svg'],['microsoft.syntex/accounts','solution.svg'],
    ['microsoft.kubernetesconfiguration/privatelinkscopes','azure-arc.svg']
  ];
  const resourceIcon=type=>iconBase+(iconMap.find(([key])=>String(type||'').toLowerCase()===key)?.[1]||'all-resources.svg');
  const resourceTypeLabels={
    'microsoft.azurearcdata/sqlserverinstances':'Azure Arc-enabled SQL Server','microsoft.hybridcompute/machines':'Azure Arc-enabled Server','microsoft.hybridconnectivity/publiccloudconnectors':'Azure Arc Multicloud Connector','microsoft.cognitiveservices/accounts':'Cognitive Services Account',
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

  const normalizedResourceId=id=>String(id||'').trim().toLowerCase().replace(/\/+$/,'');
  function identityFromResourceId(id){
    const raw=normalizedResourceId(id),parts=raw.split('/').filter(Boolean),subAt=parts.indexOf('subscriptions'),rgAt=parts.indexOf('resourcegroups'),providerAt=parts.indexOf('providers');
    const typeParts=[];if(providerAt>=0&&parts[providerAt+1]&&parts[providerAt+2]){typeParts.push(parts[providerAt+1],parts[providerAt+2]);for(let i=providerAt+4;i<parts.length;i+=2)typeParts.push(parts[i])}
    return {id:raw,name:parts.at(-1)||'',subscriptionId:subAt>=0?parts[subAt+1]||'':'',resourceGroup:rgAt>=0?parts[rgAt+1]||'':'',type:typeParts.join('/')};
  }
  function inventoryCategory(eligibility,inventoryClass){
    const eligible=norm(eligibility),cls=norm(inventoryClass).replace(/[_-]+/g,' ');
    if(eligible==='SIM')return 'Elegível';
    if(!eligible||eligible==='(VAZIO)'||eligible==='A VALIDAR'||eligible==='A_VALIDAR'||eligible==='DESCONHECIDO')return 'Aguardando classificação';
    if(cls.includes('FORA')&&cls.includes('ESCOPO'))return 'Fora do escopo';
    if(cls.includes('EXCLU'))return 'Excluído por regra';
    return 'Aguardando classificação';
  }
  let inventoryCache=null;
  function fullInventory(){
    if(inventoryCache)return inventoryCache;
    const rows=new Map(),subNames=new Map(D.subs.map(s=>[String(s.id||'').toLowerCase(),s.name||s.id]));
    for(let i=0;i<N;i++){
      const id=normalizedResourceId(R.id[i]),identity=identityFromResourceId(id),sub=D.subs[R.s[i]]||{},rg=D.rgs[R.g[i]]||[];
      rows.set(id,{id,name:R.n[i]||identity.name,type:DI.type[R.t[i]]||identity.type,subscription:sub.name||sub.id||identity.subscriptionId,subscriptionId:sub.id||identity.subscriptionId,resourceGroup:rg[0]||identity.resourceGroup,eligibility:'SIM',inventoryClass:'ELEGIVEL',classification:'Elegível',reason:'',rule:'',scope:'',managementGroups:''});
    }
    const trace=D.inventoryTrace||{},traceRows=Array.isArray(trace.rows)?trace.rows:(trace.id||[]).map((id,i)=>({id,eligibility:trace.eligibility?.[i],inventoryClass:trace.inventoryClass?.[i],reason:trace.reason?.[i],rule:trace.rule?.[i]}));
    for(const item of traceRows){
      const identity=identityFromResourceId(item.id),id=identity.id;if(!id)continue;const sid=String(item.subscriptionId||identity.subscriptionId||'').toLowerCase();
      rows.set(id,{id,name:item.name||identity.name,type:String(item.type||identity.type||'').toLowerCase(),subscription:item.subscription||subNames.get(sid)||sid,subscriptionId:sid,resourceGroup:item.resourceGroup||identity.resourceGroup,eligibility:item.eligibility||'',inventoryClass:item.inventoryClass||'',classification:inventoryCategory(item.eligibility,item.inventoryClass),reason:item.reason||'',rule:item.rule||'',scope:item.scope||'',managementGroups:item.managementGroups||''});
    }
    inventoryCache=[...rows.values()];return inventoryCache;
  }

  document.body.classList.add('scope-v2');
  const headerRow=document.querySelector('.top .hrow');
  if(headerRow){
    const meta=headerRow.querySelector('.meta');
    if(meta){
      const tools=document.createElement('div');tools.className='header-tools';tools.setAttribute('aria-label','Controles de visualização');
      tools.innerHTML='<button type="button" class="header-tool scope-inventory-tool" id="scopeInventoryBtn">ESCOPO E EXCLUSÕES</button><button type="button" class="header-tool" id="themeBtn" title="Tema atualmente ativo; clique para alternar">LIGHT</button><button type="button" class="header-tool" id="fontBtn" title="Alternar tamanho da fonte">FONTE: NORMAL</button>';
      meta.insertBefore(tools,meta.firstChild);
    }
  }

  const themeBtn=$('themeBtn'),fontBtn=$('fontBtn');
  function applyTheme(theme){
    const dark=theme==='dark';document.body.classList.toggle('dark-theme',dark);
    themeBtn.textContent=dark?'DARK':'LIGHT';themeBtn.title=`Tema ${dark?'escuro':'claro'} ativo; clique para alternar`;themeBtn.setAttribute('aria-pressed',String(dark));
    try{localStorage.setItem('governanca-theme',dark?'dark':'light')}catch(_){ }
  }
  let savedTheme='light';try{savedTheme=localStorage.getItem('governanca-theme')||'light'}catch(_){ }
  applyTheme(savedTheme);themeBtn.addEventListener('click',()=>applyTheme(document.body.classList.contains('dark-theme')?'light':'dark'));

  const fontModes=[['font-normal','FONTE: NORMAL'],['font-large','FONTE: GRANDE'],['font-xlarge','FONTE: EXTRA GRANDE']];
  let fontIndex=0;try{fontIndex=Math.max(0,Math.min(2,+localStorage.getItem('governanca-font')||0))}catch(_){ }
  function applyFont(animate=false){document.body.classList.remove(...fontModes.map(x=>x[0]));document.body.classList.add(fontModes[fontIndex][0]);fontBtn.textContent=fontModes[fontIndex][1];if(animate){document.body.classList.remove('font-changing');void document.body.offsetWidth;document.body.classList.add('font-changing');setTimeout(()=>document.body.classList.remove('font-changing'),320)}try{localStorage.setItem('governanca-font',String(fontIndex))}catch(_){ }requestAnimationFrame(syncHeaderHeight)}
  fontBtn.addEventListener('click',()=>{fontIndex=(fontIndex+1)%fontModes.length;applyFont(true)});

  const syncHeaderHeight=()=>document.documentElement.style.setProperty('--header-height',`${document.querySelector('.top')?.offsetHeight||0}px`);
  new ResizeObserver(syncHeaderHeight).observe(document.querySelector('.top'));
  syncHeaderHeight();
  applyFont();
  const evidence=document.querySelector('.evidence-strip');
  if(evidence){evidence.children[0].innerHTML='<b>Recursos elegíveis de Governança</b> · mg-evertecbrasil';evidence.children[1].textContent='Subscriptions corporativas e recursos observados são universos separados';}
  evidence?.insertAdjacentHTML('afterend',`<div class="global-filter-bar" aria-label="Filtros rápidos globais"><div class="global-filter-title"><b>Filtros rápidos</b><span id="globalFilterCount"></span></div><label>AMBIENTE<select id="globalAmbiente"><option value="">Todos</option></select></label><label>BU<select id="globalBu"><option value="">Todas</option></select></label><label>CAPEX<select id="globalCapex"><option value="">Todos</option></select></label><label>TIPO<select id="globalType"><option value="">Todos</option></select></label><label class="global-search">BUSCAR<input id="globalSearch" type="search" placeholder="Recurso, RG, Subscription ou ID"></label><button class="action-btn" id="globalClear">Limpar</button></div>`);
  document.querySelector('main>.wrap')?.insertAdjacentHTML('beforeend',`<section class="page inventory-page" id="p-inventory" hidden>
    <div class="inventory-heading"><button class="action-btn" id="inventoryBack">← Voltar à visão anterior</button><div><span class="eyebrow">RASTREABILIDADE DA FOTOGRAFIA</span><h1>Inventário e justificativas da fotografia</h1><p id="inventoryOrigin" class="sub"></p></div></div>
    <div class="grid inventory-totals" id="inventoryTotals"></div>
    <div class="panel"><div class="hrow"><div><h2>Consultar inventário completo</h2><p class="sub">Filtros de Tags da visão de Governança não são aplicados aqui; assim, recursos sem Tags continuam localizáveis.</p></div><button class="action-btn primary" id="inventoryExport">Exportar resultado CSV</button></div><div class="inventory-filters"><label>TIPO<select id="inventoryType"><option value="">Todos</option></select></label><label>CLASSIFICAÇÃO<select id="inventoryClass"><option value="">Todas</option></select></label><label>SUBSCRIPTION<select id="inventorySubscription"><option value="">Todas</option></select></label><label>RESOURCE GROUP<select id="inventoryRg"><option value="">Todos</option></select></label><label class="inventory-search">BUSCAR<input id="inventorySearch" type="search" placeholder="Nome, motivo, regra ou ResourceId"></label><button class="action-btn" id="inventoryClear">Limpar</button></div></div>
    <div class="grid inventory-summary-grid"><div class="panel c5"><h2>Resultado filtrado</h2><p class="sub">Relatório de reconciliação por classificação.</p><div class="tbl"><table id="inventoryReconciliation"></table></div></div><div class="panel c7"><h2>Resumo do detalhamento</h2><div class="inventory-summary-columns"><div><span class="eyebrow">POR TIPO</span><div id="inventoryByType"></div></div><div><span class="eyebrow">POR SUBSCRIPTION</span><div id="inventoryBySubscription"></div></div><div><span class="eyebrow">POR MOTIVO</span><div id="inventoryByReason"></div></div></div></div></div>
    <div class="panel"><div class="hrow"><div><h2>Recursos e justificativas</h2><p class="sub" id="inventoryFilteredCount"></p></div></div><div class="tbl inventory-detail"><table id="inventoryTable"></table></div></div>
  </section>`);
  function refreshGlobalFilterOptions(){const all=[];for(let i=0;i<N;i++)if(R.sc[i])all.push(i);const fill=(id,values,label,key)=>{const el=$(id),current=globalFilters[key],items=[...new Set(values.filter(Boolean))].sort((a,b)=>(key==='type'?typeLabel(a):a).localeCompare(key==='type'?typeLabel(b):b,'pt-BR'));el.innerHTML=`<option value="">${label}</option>`+items.map(x=>`<option value="${esc(x)}">${esc(key==='type'?typeLabel(x):x)}</option>`).join('');if([...el.options].some(o=>o.value===current))el.value=current};fill('globalAmbiente',all.map(i=>val('AMBIENTE',i)),'Todos','ambiente');fill('globalBu',all.map(i=>val('BU',i)),'Todas','bu');fill('globalCapex',all.map(i=>val('CAPEX',i)),'Todos','capex');fill('globalType',all.map(i=>DI.type[R.t[i]]),'Todos','type');$('globalFilterCount').textContent=`${fmt(eligibleIndexes().length)} recursos no universo atual`}
  function applyGlobalFilters(){globalFilters.ambiente=$('globalAmbiente').value;globalFilters.bu=$('globalBu').value;globalFilters.capex=$('globalCapex').value;globalFilters.type=$('globalType').value;globalFilters.search=$('globalSearch').value.trim().toLowerCase();$('globalFilterCount').textContent=`${fmt(eligibleIndexes().length)} recursos no universo atual`;detailOptions();render()}
  ['globalAmbiente','globalBu','globalCapex','globalType'].forEach(id=>$(id).addEventListener('change',applyGlobalFilters));let globalTimer;$('globalSearch').addEventListener('input',()=>{clearTimeout(globalTimer);globalTimer=setTimeout(applyGlobalFilters,160)});$('globalClear').addEventListener('click',()=>{Object.keys(globalFilters).forEach(k=>globalFilters[k]='');$('globalSearch').value='';refreshGlobalFilterOptions();detailOptions();render()});

  let inventoryReturnPage='exec',inventoryFiltered=[];
  const inventoryClasses=['Elegível','Fora do escopo','Excluído por regra','Aguardando classificação'];
  function fillInventorySelect(id,items,allLabel,label=x=>x){const el=$(id),current=el.value;el.innerHTML=`<option value="">${allLabel}</option>`+[...new Set(items.filter(Boolean))].sort((a,b)=>label(a).localeCompare(label(b),'pt-BR')).map(x=>`<option value="${esc(x)}">${esc(label(x))}</option>`).join('');if([...el.options].some(o=>o.value===current))el.value=current}
  function inventoryRowsFiltered(){const type=$('inventoryType').value,classification=$('inventoryClass').value,subscription=$('inventorySubscription').value,rg=$('inventoryRg').value,q=$('inventorySearch').value.trim().toLowerCase();return fullInventory().filter(r=>(!type||r.type===type)&&(!classification||r.classification===classification)&&(!subscription||r.subscription===subscription)&&(!rg||r.resourceGroup===rg)&&(!q||`${r.name} ${r.type} ${r.subscription} ${r.subscriptionId} ${r.resourceGroup} ${r.reason} ${r.rule} ${r.id}`.toLowerCase().includes(q)))}
  function countGroups(rows,key){const m=new Map();for(const r of rows){const value=r[key]||'(não informado)';m.set(value,(m.get(value)||0)+1)}return [...m].sort((a,b)=>b[1]-a[1]||String(a[0]).localeCompare(String(b[0]),'pt-BR'))}
  function renderMiniSummary(id,items,label=x=>x){$(id).innerHTML=items.slice(0,6).map(([name,n])=>`<div class="inventory-mini-row"><span title="${esc(name)}">${esc(label(name))}</span><strong>${fmt(n)}</strong></div>`).join('')||'<p class="muted">Nenhum registro.</p>'}
  function renderInventory(){
    const all=fullInventory(),totals=new Map(inventoryClasses.map(c=>[c,all.filter(r=>r.classification===c).length]));
    const photoDate=D.meta?.date?String(D.meta.date).slice(0,10).split('-').reverse().join('/'):'não informada';$('inventoryOrigin').textContent=`Fotografia ${photoDate} · arquivo ${D.meta?.eligibleFile||D.meta?.scopeFile||D.meta?.fullFile||'origem não informada'} · total do Azure Resource Graph, não do Portal Azure`;
    const totalCards=[['resource-graph.svg','Observados no ARG',all.length,'ResourceIds distintos'],['resource-graph.svg','Elegíveis',totals.get('Elegível'),'denominador dos indicadores'],['all-resources.svg','Fora do escopo',totals.get('Fora do escopo'),'classificados fora da atuação'],['maintenance.svg','Excluídos por regra',totals.get('Excluído por regra'),'preservados para rastreabilidade'],['monitor.svg','Aguardando classificação',totals.get('Aguardando classificação'),'fora dos indicadores até validação']];
    $('inventoryTotals').innerHTML=totalCards.map(c=>`<div class="panel kpi inventory-total c-auto"><div class="kpi-head"><div><div class="eyebrow">${c[1]}</div><div class="v">${fmt(c[2])}</div></div>${icon(c[0])}</div><div class="d">${c[3]}</div></div>`).join('');
    inventoryFiltered=inventoryRowsFiltered();const grouped=countGroups(inventoryFiltered,'classification').filter(([,n])=>n>0),sum=inventoryFiltered.length;
    $('inventoryReconciliation').innerHTML=`<thead><tr><th>Classificação</th><th class="r">Quantidade</th><th class="r">% do resultado</th></tr></thead><tbody>${grouped.map(([name,n])=>`<tr><td>${esc(name)}</td><td class="r"><b>${fmt(n)}</b></td><td class="r">${pct(n,sum)}</td></tr>`).join('')}<tr class="inventory-total-row"><td><b>Total do resultado filtrado</b></td><td class="r"><b>${fmt(sum)}</b></td><td class="r"><b>${sum?'100,0%':'—'}</b></td></tr></tbody>`;
    renderMiniSummary('inventoryByType',countGroups(inventoryFiltered,'type'),typeLabel);renderMiniSummary('inventoryBySubscription',countGroups(inventoryFiltered,'subscription'));renderMiniSummary('inventoryByReason',countGroups(inventoryFiltered,'reason'));
    $('inventoryFilteredCount').textContent=`${fmt(sum)} ResourceIds distintos no resultado; a tabela exibe até 500 linhas e a exportação contém todos.`;
    $('inventoryTable').innerHTML=`<thead><tr><th>Recurso</th><th>Tipo</th><th>Subscription</th><th>Resource Group</th><th>Elegibilidade</th><th>Classificação</th><th>Motivo</th><th>Regra</th><th>ResourceId</th></tr></thead><tbody>${inventoryFiltered.slice(0,500).map(r=>`<tr><td><b>${esc(r.name)}</b></td><td>${esc(typeLabel(r.type))}</td><td>${esc(r.subscription)}</td><td>${esc(r.resourceGroup)}</td><td><span class="pill ${r.eligibility==='SIM'?'ok':r.classification==='Aguardando classificação'?'warn':'n'}">${esc(r.eligibility||'(vazio)')}</span></td><td>${esc(r.classification)}</td><td>${esc(r.reason||'—')}</td><td>${esc(r.rule||'—')}</td><td class="num inventory-id" title="${esc(r.id)}">${esc(r.id)}</td></tr>`).join('')}</tbody>`;
  }
  function inventoryOptions(){const all=fullInventory();fillInventorySelect('inventoryType',all.map(r=>r.type),'Todos',typeLabel);fillInventorySelect('inventoryClass',inventoryClasses,'Todas');fillInventorySelect('inventorySubscription',all.map(r=>r.subscription),'Todas');fillInventorySelect('inventoryRg',all.map(r=>r.resourceGroup),'Todos')}
  function openInventory(seed={}){inventoryReturnPage=page==='inventory'?inventoryReturnPage:page;page='inventory';document.body.classList.add('inventory-mode');document.querySelectorAll('section.page').forEach(s=>s.hidden=s.id!=='p-inventory');$('tabs').hidden=true;inventoryOptions();$('inventoryType').value=seed.type||'';$('inventoryClass').value=seed.classification||'';$('inventorySubscription').value=seed.subscription||'';$('inventoryRg').value=seed.resourceGroup||'';$('inventorySearch').value='';renderInventory();scrollTo({top:0,behavior:'smooth'})}
  function closeInventory(){page=inventoryReturnPage||'exec';document.body.classList.remove('inventory-mode');$('tabs').hidden=false;document.querySelectorAll('section.page').forEach(s=>s.hidden=s.id!==`p-${page}`);$('tabs').querySelectorAll('button').forEach(b=>b.setAttribute('aria-selected',b.dataset.p===page));render();scrollTo({top:0,behavior:'smooth'})}
  $('scopeInventoryBtn').addEventListener('click',()=>openInventory({type:globalFilters.type}));$('inventoryBack').addEventListener('click',closeInventory);$('inventoryClear').addEventListener('click',()=>{for(const id of ['inventoryType','inventoryClass','inventorySubscription','inventoryRg','inventorySearch'])$(id).value='';renderInventory()});
  for(const id of ['inventoryType','inventoryClass','inventorySubscription','inventoryRg'])$(id).addEventListener('change',renderInventory);let inventoryTimer;$('inventorySearch').addEventListener('input',()=>{clearTimeout(inventoryTimer);inventoryTimer=setTimeout(renderInventory,150)});
  $('inventoryExport').addEventListener('click',()=>{const headers=['ResourceName','ResourceType','Subscription','SubscriptionId','ResourceGroup','ELEGIVEL_GOVERNANCA','CLASSE_INVENTARIO','ClassificacaoDashboard','MOTIVO_NAO_ELEGIVEL','REGRA_EXCLUSAO','ESCOPO_HIERARQUIA','ManagementGroups','ResourceId'],lines=[headers.map(csvCell).join(';'),...inventoryFiltered.map(r=>[r.name,r.type,r.subscription,r.subscriptionId,r.resourceGroup,r.eligibility,r.inventoryClass,r.classification,r.reason,r.rule,r.scope,r.managementGroups,r.id].map(csvCell).join(';'))];downloadText(`Inventario_Justificativas_${D.meta?.date||'sem_data'}.csv`,lines.join('\r\n'))});

  $('p-exec').innerHTML=`
    <div class="grid" id="execKpisV2"></div>
    <div class="grid">
      <div class="panel c7"><h2>Preenchimento × classificação</h2><p class="sub">INDEFINIDO conta como preenchimento técnico, mas não como classificação definitiva.</p><div class="legend"><span><i style="background:var(--ok)"></i>Informado</span><span><i style="background:var(--warn)"></i>INDEFINIDO</span><span><i style="background:var(--bad)"></i>Vazio</span></div><div id="stackTagsV2"></div></div>
      <div class="panel c5"><h2>Tipos de recursos mais presentes</h2><p class="sub">Recursos elegíveis na fotografia atual.</p><div class="type-grid" id="typesV2"></div></div>
    </div>
    <div class="grid">
      <div class="panel c12"><div class="hrow"><div><h2>Visão das assinaturas</h2><p class="sub">O cadastro corporativo não depende de a assinatura possuir recursos na coleta.</p></div><button class="action-btn" id="openSubscriptionsV2">Abrir detalhamento</button></div><div class="subscription-summary" id="subscriptionSummaryV2"></div><div id="subscriptionCoverageV2"></div></div>
      <div class="panel c4" hidden aria-hidden="true"><div id="policyV2"></div></div>
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
    const inventoryScope=fullInventory().filter(r=>!globalFilters.type||r.type===globalFilters.type),complements=inventoryClasses.slice(1).map(classification=>[classification,inventoryScope.filter(r=>r.classification===classification).length]).filter(([,n])=>n>0);
    $('execKpisV2').innerHTML=cards.map((c,index)=>`<div class="panel kpi c3"><div class="kpi-head"><div><div class="eyebrow">${c[1]}</div><div class="v">${typeof c[2]==='number'?fmt(c[2]):c[2]}</div></div>${icon(c[0])}</div><div class="d">${c[3]}</div>${index===4&&complements.length?`<div class="inventory-card-links">${complements.map(([classification,n])=>`<button type="button" data-inventory-class="${esc(classification)}">${fmt(n)} ${esc(classification.toLowerCase())}</button>`).join('')}</div><small class="inventory-filter-note">Complementos usam Tipo; filtros de Tags não ocultam excluídos.</small>`:''}</div>`).join('');
    $('stackTagsV2').innerHTML=TAGS.map(t=>stackRow(t,ix)).join('');
    const tm=new Map();for(const i of ix){const t=DI.type[R.t[i]];tm.set(t,(tm.get(t)||0)+1)}const top=[...tm].sort((a,b)=>b[1]-a[1]).slice(0,10);
    $('typesV2').innerHTML=top.map(([t,n])=>`<div class="type-row">${icon(resourceIcon(t).split('/').pop(),'sm')}<div class="name" title="${esc(t)}">${esc(typeLabel(t))}</div><div class="count">${fmt(n)}</div></div>`).join('');
    $('subscriptionSummaryV2').innerHTML=[['Total corporativo',master.length||'—'],['Ativas no escopo',activeScope.length||'—'],['Com recursos elegíveis',observed.size],['Sem recursos elegíveis',master.length?without.length:'—']].map(x=>`<div><b>${typeof x[1]==='number'?fmt(x[1]):x[1]}</b><span>${x[0]}</span></div>`).join('');
    const den=activeScope.length||observed.size,covered=master.length?activeScope.filter(x=>observed.has(String(x.id).toLowerCase())).length:observed.size;
    $('subscriptionCoverageV2').innerHTML=`<div class="coverage-bar"><span style="width:${den?100*covered/den:0}%;background:var(--accent)"></span></div><div class="muted">${fmt(covered)} de ${fmt(den)} assinaturas ativas do escopo possuem recursos elegíveis nesta fotografia.</div>`;
    renderSubscriptionListV2(ix,master);
  };
  $('execKpisV2').addEventListener('click',event=>{const button=event.target.closest('[data-inventory-class]');if(button)openInventory({type:globalFilters.type,classification:button.dataset.inventoryClass})});

  function renderSubscriptionListV2(ix,master=masterSubscriptions()){
    const base=master.length?master.filter(x=>x.inScope):D.subs.filter(x=>x.inScope).map(x=>({name:x.name,id:x.id,status:'',managementGroup:'',inScope:true}));
    const mg=$('subscriptionMgV2'),currentMg=mg.value,mgs=[...new Set(base.map(x=>x.managementGroup).filter(Boolean))].sort();mg.innerHTML='<option value="">Todos os Management Groups</option>'+mgs.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');if(mgs.includes(currentMg))mg.value=currentMg;
    const q=$('subscriptionSearchV2').value.trim().toLowerCase(),status=$('subscriptionStatusV2').value,presence=$('subscriptionPresenceV2').value;
    const rows=base.map(s=>{const si=D.subs.findIndex(x=>String(x.id).toLowerCase()===String(s.id).toLowerCase()),n=si<0?0:ix.filter(i=>R.s[i]===si).length;return {...s,n}}).filter(s=>(!q||`${s.name} ${s.id}`.toLowerCase().includes(q))&&(!mg.value||s.managementGroup===mg.value)&&(!status||norm(s.status)===status)&&(!presence||(presence==='with'?s.n>0:s.n===0)));
    $('subscriptionCountV2').textContent=`${fmt(rows.length)} de ${fmt(base.length)} assinaturas do escopo`;
    $('subscriptionPreviewV2').innerHTML=`<thead><tr><th>Subscription</th><th>Status</th><th>Management Group</th><th>Recursos elegíveis</th><th>Situação</th></tr></thead><tbody>${rows.map(s=>`<tr><td><b>${esc(s.name)}</b><br><span class="muted num">${esc(s.id)}</span></td><td>${esc(s.status||'—')}</td><td>${esc(s.managementGroup||'—')}</td><td class="r">${fmt(s.n)}</td><td>${s.n?'<span class="scope-state good">Com recursos</span>':'<span class="scope-state off">Sem recursos elegíveis</span>'}</td></tr>`).join('')||'<tr><td colspan="5" class="muted">Nenhuma assinatura encontrada para os filtros selecionados.</td></tr>'}</tbody>`;
  }

  const longValueStore=new Map(),longValueKeys=new Map();let longValueSequence=0;const LONG_VALUE_LIMIT=28;
  function valueParts(value){return String(value||'').split(/[,;|\n\r]+/).map(x=>x.trim()).filter(Boolean)}
  function compactValueCell(value,label='Valor'){
    if(value==null||String(value).trim()==='')return '<span class="pill bad">vazio</span>';
    const text=String(value).trim();if(text==='INDEFINIDO')return '<span class="pill warn">INDEFINIDO</span>';
    const parts=valueParts(text),forceProductList=norm(label)==='PRODUTO'&&parts.length>=2;if(text.length<=LONG_VALUE_LIMIT&&!forceProductList)return esc(text);
    const signature=`${label}\u0001${text}`;let key=longValueKeys.get(signature);if(!key){key=`long-${++longValueSequence}`;longValueKeys.set(signature,key);longValueStore.set(key,{label,text,parts})}
    const summary=parts.length>1?`${fmt(parts.length)} valores`:`${text.slice(0,22).trim()}…`;
    return `<button type="button" class="compact-value" data-long-value="${key}" title="Abrir valor completo"><span>${esc(summary)}</span><small>Ver detalhes →</small></button>`;
  }
  function compactLongCells(root,label){for(const td of root?.querySelectorAll('td')||[]){const text=td.textContent.trim();if(text.length>LONG_VALUE_LIMIT)td.innerHTML=compactValueCell(text,label)}}

  const oldRenderTags=renderTags;
  renderTags=function(){
    oldRenderTags();const ix=eligibleIndexes();
    if($('deParaPanel'))$('deParaPanel').hidden=true;
    const tagQualityPanel=$('tagVariants')?.closest('.panel');if(tagQualityPanel){tagQualityPanel.hidden=true;tagQualityPanel.setAttribute('aria-hidden','true')}
    const tagDistributionPanel=$('tagDist')?.closest('.panel');if(tagDistributionPanel){tagDistributionPanel.classList.remove('c7');tagDistributionPanel.classList.add('c12')}
    if(curTag==='CCOWNER')for(const p of [...$('tagVariants').querySelectorAll('p')])if(/De\/Para|tabela abaixo/i.test(p.textContent))p.remove();
    if(!$('tagTypesV2')){$('p-tags').querySelector('.grid:nth-of-type(2)')?.insertAdjacentHTML('afterend','<div class="panel"><h2>Contexto por tipo de recurso</h2><p class="sub">Onde a Tag selecionada está concentrada.</p><div class="type-grid" id="tagTypesV2"></div></div>');}
    const base=curTag==='FOLIO'?ix.filter(i=>val('CAPEX',i)==='SIM'):ix,s=tstat(curTag,base);
    if(curTag==='FOLIO'){
      $('tagKpis').innerHTML=[['Preenchida',s.fill,pct(s.fill,s.n)],['Informada',s.cl,pct(s.cl,s.n)],['INDEFINIDO',s.ind,pct(s.ind,s.n)],['Vazia / inexistente',s.vz,pct(s.vz,s.n)]].map(k=>`<div class="panel kpi c3"><div class="eyebrow">FOLIO · ${k[0]}</div><div class="v">${fmt(k[1])}<small>${k[2]}</small></div><div class="d">de ${fmt(s.n)} recursos CAPEX=SIM</div></div>`).join('');
      $('tagDistSub').textContent=`Distribuição somente entre ${fmt(base.length)} recursos CAPEX=SIM. Recursos CAPEX=NAO não entram no denominador.`;
      $('tagDist').insertAdjacentHTML('beforebegin','<div id="folioContextV2" class="folio-context">Universo elegível do FOLIO: somente recursos com CAPEX=SIM.</div>');
    } else $('folioContextV2')?.remove();
    const byType=new Map();for(const i of base){const t=DI.type[R.t[i]],o=byType.get(t)||{n:0,filled:0};o.n++;if(val(curTag,i)!=null)o.filled++;byType.set(t,o)}
    $('tagTypesV2').innerHTML=[...byType].sort((a,b)=>b[1].n-a[1].n).slice(0,10).map(([t,o])=>`<div class="type-row">${icon(resourceIcon(t).split('/').pop(),'sm')}<div class="name">${esc(typeLabel(t))}<small class="muted"> · ${pct(o.filled,o.n)} preenchida</small></div><div class="count">${fmt(o.n)}</div></div>`).join('');compactLongCells($('tagVariants'),curTag);
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
  const cell=(v,label='Valor')=>compactValueCell(v,label);
  renderDet=function(){
    const level=$('detailLevelV2').value,ix=filteredResources();
    if(level==='subscriptions'){
      const master=masterSubscriptions(),subFilter=$('detailSubV2').value,q=$('detailSearchV2').value.trim().toLowerCase(),rows=master.filter(s=>(!subFilter||s.name===subFilter)&&(!q||`${s.name} ${s.id} ${s.managementGroup}`.toLowerCase().includes(q)));$('detailCountV2').textContent=`${fmt(rows.length)} de ${fmt(master.length)} assinaturas cadastradas`;
      $('detailTableV2').innerHTML=`<thead><tr><th>Subscription</th><th>Status</th><th>Management Group</th><th>Escopo</th><th>Recursos elegíveis</th><th>Situação</th></tr></thead><tbody>${rows.map(s=>{const si=D.subs.findIndex(x=>String(x.id).toLowerCase()===String(s.id).toLowerCase()),n=si<0?0:ix.filter(i=>R.s[i]===si).length;return `<tr><td><b>${esc(s.name)}</b><br><span class="muted num">${esc(s.id)}</span></td><td>${esc(s.status)}</td><td>${esc(s.managementGroup)}</td><td>${s.inScope?'<span class="scope-state good">Sim</span>':'<span class="scope-state off">Não</span>'}</td><td class="r">${fmt(n)}</td><td>${norm(s.status)==='DISABLED'?'<span class="scope-state bad">Desativada</span>':n?'<span class="scope-state good">Com recursos</span>':'<span class="scope-state off">Sem recursos elegíveis</span>'}</td></tr>`}).join('')}</tbody>`;return;
    }
    if(level==='resourceGroups'){
      const m=new Map();for(const i of ix){const k=String(D.subs[R.s[i]].id).toLowerCase()+'|'+D.rgs[R.g[i]][0].toLowerCase(),o=m.get(k)||{sub:D.subs[R.s[i]].name,rg:D.rgs[R.g[i]][0],n:0,p:0};o.n++;if(isPend(i))o.p++;m.set(k,o)}const rows=[...m.values()].sort((a,b)=>b.n-a.n);$('detailCountV2').textContent=`${fmt(rows.length)} Resource Groups encontrados`;$('detailTableV2').innerHTML=`<thead><tr><th>Resource Group</th><th>Subscription</th><th class="r">Recursos</th><th class="r">Pendências</th><th>Status</th></tr></thead><tbody>${rows.map(o=>`<tr><td><div class="resource-name">${icon('resource-group.svg','sm')}<strong>${esc(o.rg)}</strong></div></td><td>${esc(o.sub)}</td><td class="r">${fmt(o.n)}</td><td class="r">${fmt(o.p)}</td><td>${o.p?'<span class="status-dot warn">Revisar</span>':'<span class="status-dot">Conforme</span>'}</td></tr>`).join('')}</tbody>`;return;
    }
    $('detailCountV2').textContent=`${fmt(ix.length)} recursos encontrados`;$('detailTableV2').innerHTML=`<thead><tr><th>Recurso</th><th>Contexto</th><th>Tipo</th><th>FinOps</th><th>Classificação</th></tr></thead><tbody>${ix.slice(0,500).map(i=>{const t=DI.type[R.t[i]];return `<tr><td><div class="resource-name" title="${esc(R.id[i])}">${icon(resourceIcon(t).split('/').pop(),'sm')}<strong>${esc(shortResourceName(R.id[i],R.n[i]))}</strong></div></td><td><div class="table-stack"><span>${esc(D.subs[R.s[i]].name)}</span><span>${esc(D.rgs[R.g[i]][0])}</span></div></td><td>${esc(typeLabel(t))}</td><td><div class="table-stack"><span>CAPEX: ${cell(val('CAPEX',i),'CAPEX')}</span><span>FOLIO: ${cell(val('FOLIO',i),'FOLIO')}</span></div></td><td><div class="table-stack"><span>CLIENTE: ${cell(val('CLIENTE',i),'CLIENTE')}</span><span>PRODUTO: ${cell(val('PRODUTO',i),'PRODUTO')}</span></div></td></tr>`}).join('')}</tbody>`+(ix.length>500?`<caption>Mostrando 500 de ${fmt(ix.length)}. Refine os filtros para reduzir o resultado.</caption>`:'');
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
  matrixControls.closest('.panel').insertAdjacentHTML('beforebegin','<div class="panel official-quality" id="officialQuality"><div class="hrow"><div><h2>Qualidade do mapa oficial BU × CC × CCOWNER</h2><p class="sub">Clique em qualquer pendência para abrir os recursos, Resource Groups ou subscriptions já filtrados na Análise Avançada.</p></div></div><div class="official-quality-grid" id="officialQualityGrid"></div></div>');
  window.ownerBreakdowns=window.ownerBreakdowns||new Map();
  document.body.insertAdjacentHTML('beforeend',`<dialog id="ownerBreakdownDialog" class="data-dialog"><div class="data-dialog-head"><div><span class="eyebrow">CCOWNER ATUAL</span><h2 id="ownerBreakdownTitle">Responsáveis encontrados</h2><p class="sub" id="ownerBreakdownSubtitle"></p></div><button class="data-dialog-close" type="button" aria-label="Fechar">×</button></div><div class="data-dialog-body" id="ownerBreakdownBody"></div></dialog>`);
  const priorRenderFinV2=renderFin;
  renderFin=function(){
    window.ownerBreakdowns.clear();priorRenderFinV2();const select=$('buMatrixFilter'),current=select.value,bus=[...new Set(eligibleIndexes().map(i=>val('BU',i)||'(vazio)'))].sort();select.innerHTML='<option value="">Todas as BUs</option>'+bus.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');if(bus.includes(current))select.value=current;
    let visible=!select.value;for(const tr of $('buccTbl').tBodies[0]?.rows||[]){if(tr.classList.contains('grp'))visible=!select.value||norm(tr.cells[0].textContent)===norm(select.value);tr.hidden=!visible}
    for(const tr of [...$('capexBox').querySelectorAll('tbody tr')])if(norm(tr.cells[0]?.textContent).startsWith('FOLIO PREENCHIDO'))tr.remove();const note=$('capexBox').querySelector('.note');if(note&&/depende da coluna FOLIO/i.test(note.textContent))note.remove();
    const officialMap=new Map((governanceConfig.officialMap||[]).map(x=>[norm(x.CC),x])),ix=eligibleIndexes();
    const sets={bu:[],owner:[],unmapped:[],all:[]};for(const i of ix){const off=officialMap.get(norm(val('CC',i))),buBad=!!off&&norm(val('BU',i))!==norm(off.BU),ownerBad=!!off&&!!off.CCOWNER&&norm(val('CCOWNER',i))!==norm(off.CCOWNER),unmapped=!off;if(buBad)sets.bu.push(i);if(ownerBad)sets.owner.push(i);if(unmapped)sets.unmapped.push(i);if(buBad||ownerBad||unmapped)sets.all.push(i)}
    const cards=[['all','Pendências totais',sets.all.length,'BU, CCOWNER ou CC sem mapa'],['bu','BU divergente',sets.bu.length,'valor atual diferente da BU oficial'],['owner','CCOWNER divergente',sets.owner.length,'responsável atual diferente do oficial'],['unmapped','CC sem mapeamento',sets.unmapped.length,'Centro de Custo ausente no mapa']];
    $('officialQuality').hidden=!officialMap.size;$('officialQualityGrid').innerHTML=cards.map(([mode,label,note,detail])=>`<button class="official-quality-card" data-official-summary="${mode}" ${note?'':'disabled'}><span>${label}</span><strong>${fmt(note)}</strong><small>${detail}</small><em>Ver itens →</em></button>`).join('');
  };
  $('buMatrixFilter').addEventListener('change',renderFin);
  $('ccOnlyMulti').addEventListener('change',()=>renderFin());
  $('ownerBreakdownDialog').addEventListener('click',e=>{if(e.target.closest('.data-dialog-close')||e.target===$('ownerBreakdownDialog'))$('ownerBreakdownDialog').close()});
  document.addEventListener('click',e=>{const button=e.target.closest('[data-long-value]');if(!button)return;const data=longValueStore.get(button.dataset.longValue);if(!data)return;const multi=data.parts.length>1;$('ownerBreakdownTitle').textContent=multi?`${fmt(data.parts.length)} valores encontrados`:`${data.label} · valor completo`;$('ownerBreakdownSubtitle').textContent=`Tag ${data.label} · valor preservado integralmente na extração`;$('ownerBreakdownBody').innerHTML=multi?`<div class="owner-list">${data.parts.map((item,index)=>`<div class="owner-list-row"><span><small class="value-index">${index+1}</small>${esc(item)}</span></div>`).join('')}</div>`:`<div class="full-value">${esc(data.text)}</div>`;$('ownerBreakdownDialog').showModal()});

  const evoTab=$('tabs').querySelector('[data-p="evo"]');evoTab.textContent='Análise Avançada';
  $('p-evo').innerHTML=`<div id="advancedContext" class="advanced-context" hidden></div><div class="panel advanced-builder"><div class="hrow"><div><h2>Análise avançada de Governança</h2><p class="sub">Combine Tags e atributos com condições E/OU. Os resultados usam somente os recursos elegíveis da fotografia atual.</p></div><div class="advanced-actions"><button class="action-btn" id="advancedAdd">+ Adicionar condição</button><button class="action-btn" id="advancedClear">Limpar</button><button class="action-btn primary" id="advancedExport">Exportar CSV</button></div></div><div class="advanced-top"><label>Combinar condições<select id="advancedLogic"><option value="AND">Todas (E)</option><option value="OR">Qualquer uma (OU)</option></select></label><label>Resultado por<select id="advancedLevel"><option value="resources">Recursos</option><option value="resourceGroups">Resource Groups</option><option value="subscriptions">Subscriptions relacionadas</option></select></label><label>Buscar no resultado<input id="advancedSearch" type="search" placeholder="Nome, RG, Subscription ou ID"></label></div><div id="advancedRules"></div><datalist id="advancedTypeOptions"></datalist></div><div class="grid" id="advancedKpis"></div><div class="panel"><div class="hrow"><div><h2>Resultado da análise</h2><p class="sub" id="advancedSummary"></p><p class="sub compact-table-note">Colunas agrupadas para leitura em tela; a exportação preserva todos os campos.</p></div></div><div class="detail-table tbl"><table id="advancedTable"></table></div></div>`;
  const advancedFields=[['AMBIENTE','Tag AMBIENTE'],['BU','Tag BU'],['CAPEX','Tag CAPEX'],['CC','Tag CC'],['CCOWNER','Tag CCOWNER'],['CLIENTE','Tag CLIENTE'],['PRODUTO','Tag PRODUTO'],['FOLIO','Tag FOLIO'],['ResourceType','Tipo de recurso'],['ResourceGroup','Resource Group'],['Subscription','Subscription'],['ResourceName','Nome do recurso']];
  const advancedOperators=[['eq','Igual'],['neq','Diferente'],['contains','Contém'],['notcontains','Não contém'],['empty','Está vazio'],['notempty','Não está vazio'],['in','Está em uma lista']];let advancedRules=[],advancedPreset=null;
  function advancedValue(field,i){if(TAGS.includes(field))return val(field,i)||'';if(field==='ResourceType')return typeLabel(DI.type[R.t[i]]||'');if(field==='ResourceGroup')return D.rgs[R.g[i]][0]||'';if(field==='Subscription')return D.subs[R.s[i]].name||'';return R.n[i]||''}
  function advancedMatch(rule,i){const actual=norm(advancedValue(rule.field,i)),expected=norm(rule.value),values=expected.split(',').map(x=>x.trim()).filter(Boolean);if(rule.op==='empty')return !actual;if(rule.op==='notempty')return !!actual;if(rule.op==='eq')return actual===expected;if(rule.op==='neq')return actual!==expected;if(rule.op==='contains')return actual.includes(expected);if(rule.op==='notcontains')return !actual.includes(expected);if(rule.op==='in')return values.includes(actual);return true}
  function advancedIndexes(){const logic=$('advancedLogic').value,q=$('advancedSearch').value.trim().toLowerCase();return eligibleIndexes().filter(i=>(!advancedPreset||advancedPreset.test(i))&&(!advancedRules.length||(logic==='AND'?advancedRules.every(r=>advancedMatch(r,i)):advancedRules.some(r=>advancedMatch(r,i))))&&(!q||`${R.n[i]} ${R.id[i]} ${D.rgs[R.g[i]][0]} ${D.subs[R.s[i]].name} ${DI.type[R.t[i]]}`.toLowerCase().includes(q)))}
  function renderAdvancedRules(){const types=[...new Set(eligibleIndexes().map(i=>DI.type[R.t[i]]))].sort((a,b)=>typeLabel(a).localeCompare(typeLabel(b),'pt-BR'));$('advancedTypeOptions').innerHTML=types.map(t=>`<option value="${esc(typeLabel(t))}"></option>`).join('');$('advancedRules').innerHTML=advancedRules.map((r,n)=>`<div class="advanced-rule" data-rule="${n}"><span class="rule-join">${n?$('advancedLogic').value==='AND'?'E':'OU':'ONDE'}</span><select data-key="field">${advancedFields.map(([v,l])=>`<option value="${v}" ${v===r.field?'selected':''}>${l}</option>`).join('')}</select><select data-key="op">${advancedOperators.map(([v,l])=>`<option value="${v}" ${v===r.op?'selected':''}>${l}</option>`).join('')}</select><input data-key="value" value="${esc(r.value)}" ${r.field==='ResourceType'?'list="advancedTypeOptions"':''} placeholder="${r.field==='ResourceType'?'Digite o nome do tipo':`Valor${r.op==='in'?'1, Valor2':''}`}" ${['empty','notempty'].includes(r.op)?'disabled':''}><button class="action-btn danger" data-remove-rule="${n}" aria-label="Remover condição">×</button></div>`).join('')||'<div class="advanced-empty">Nenhuma condição aplicada. O resultado considera todos os recursos elegíveis.</div>';}
  function renderAdvanced(skipRules=false){
    if(!skipRules)renderAdvancedRules();const ix=advancedIndexes(),rgs=new Set(ix.map(i=>`${R.s[i]}|${R.g[i]}`)),subs=new Set(ix.map(i=>R.s[i]));$('advancedContext').hidden=!advancedPreset;$('advancedContext').innerHTML=advancedPreset?`<div><b>Filtro originado de um indicador:</b> ${esc(advancedPreset.label)}<span>Os valores oficiais abaixo vêm do mapa BU × CC × CCOWNER carregado.</span></div><button class="action-btn" id="clearAdvancedPreset">Remover filtro do indicador</button>`:'';$('advancedKpis').innerHTML=[['resources','Recursos',ix.length],['resourceGroups','Resource Groups',rgs.size],['subscriptions','Subscriptions relacionadas',subs.size]].map(([key,label,total])=>`<button type="button" class="panel kpi c4 advanced-kpi ${$('advancedLevel').value===key?'active':''}" data-advanced-level="${key}" aria-label="Exibir ${label.toLowerCase()}"><div class="eyebrow">${label}</div><div class="v">${fmt(total)}</div><div class="d">Clique para listar o resultado</div><span class="advanced-kpi-link">Ver ${label.toLowerCase()} →</span></button>`).join('');const level=$('advancedLevel').value;let rows='',officialMap=new Map((governanceConfig.officialMap||[]).map(x=>[norm(x.CC),x]));
    if(level==='resources')rows=`<thead><tr><th>Recurso</th><th>Contexto</th><th>Financeiro</th><th>Responsável</th><th>Classificação</th><th>Situação</th></tr></thead><tbody>${ix.slice(0,500).map(i=>{const t=DI.type[R.t[i]],off=officialMap.get(norm(val('CC',i))),buBad=!!off&&norm(val('BU',i))!==norm(off.BU),ownerBad=!!off&&!!off.CCOWNER&&norm(val('CCOWNER',i))!==norm(off.CCOWNER),status=!off?'CC sem mapeamento':buBad&&ownerBad?'BU e CCOWNER divergentes':buBad?'BU divergente':ownerBad?'CCOWNER divergente':'Conforme';return `<tr><td><div class="resource-name" title="${esc(R.id[i])}">${icon(resourceIcon(t).split('/').pop(),'sm')}<strong>${esc(shortResourceName(R.id[i],R.n[i]))}</strong></div></td><td><div class="table-stack"><b>${esc(typeLabel(t))}</b><span>${esc(D.subs[R.s[i]].name)}</span><span>${esc(D.rgs[R.g[i]][0])}</span></div></td><td><div class="table-stack finance-stack"><span>AMBIENTE: ${cell(val('AMBIENTE',i),'AMBIENTE')}</span><span>BU: ${cell(val('BU',i),'BU')} → <b>${compactValueCell(off?.BU||'—','BU OFICIAL')}</b></span><span>CC: ${cell(val('CC',i),'CC')}</span></div></td><td><div class="table-stack"><span>Atual: ${cell(val('CCOWNER',i),'CCOWNER')}</span><span>Oficial: <b>${compactValueCell(off?.CCOWNER||'—','CCOWNER OFICIAL')}</b></span></div></td><td><div class="table-stack"><span>CAPEX: ${cell(val('CAPEX',i),'CAPEX')}</span><span>CLIENTE: ${cell(val('CLIENTE',i),'CLIENTE')}</span><span>PRODUTO: ${cell(val('PRODUTO',i),'PRODUTO')}</span></div></td><td><span class="pill ${!off?'n':buBad?'bad':ownerBad?'warn':'ok'}">${status}</span></td></tr>`}).join('')}</tbody>`;
    else if(level==='resourceGroups'){const m=new Map();for(const i of ix){const k=`${R.s[i]}|${R.g[i]}`,o=m.get(k)||{sub:D.subs[R.s[i]].name,rg:D.rgs[R.g[i]][0],n:0};o.n++;m.set(k,o)}rows=`<thead><tr><th>Resource Group</th><th>Subscription</th><th class="r">Recursos encontrados</th></tr></thead><tbody>${[...m.values()].sort((a,b)=>b.n-a.n).map(o=>`<tr><td><div class="resource-name">${icon('resource-group.svg','sm')}<strong>${esc(o.rg)}</strong></div></td><td>${esc(o.sub)}</td><td class="r">${fmt(o.n)}</td></tr>`).join('')}</tbody>`}
    else{const m=new Map();for(const i of ix){const k=R.s[i],o=m.get(k)||{id:D.subs[k].id,name:D.subs[k].name,n:0};o.n++;m.set(k,o)}rows=`<thead><tr><th>Subscription</th><th>Subscription ID</th><th class="r">Recursos encontrados</th></tr></thead><tbody>${[...m.values()].sort((a,b)=>b.n-a.n).map(o=>`<tr><td><div class="resource-name">${icon('subscription.svg','sm')}<strong>${esc(o.name)}</strong></div></td><td class="num">${esc(o.id)}</td><td class="r">${fmt(o.n)}</td></tr>`).join('')}</tbody>`}$('advancedTable').innerHTML=rows;$('advancedSummary').textContent=`${fmt(ix.length)} recursos atendem às condições. Exibição limitada a 500 linhas no nível Recursos; a exportação contém todo o resultado.`;
  }
  function openAdvancedPreset(label,test,rules=[]){advancedPreset={label,test};advancedRules=rules;$('advancedLogic').value='AND';$('advancedLevel').value='resources';$('advancedSearch').value='';openPage('evo');renderAdvanced()}
  function officialPredicate(mode){const map=new Map((governanceConfig.officialMap||[]).map(x=>[norm(x.CC),x]));return i=>{const off=map.get(norm(val('CC',i))),buBad=!!off&&norm(val('BU',i))!==norm(off.BU),ownerBad=!!off&&!!off.CCOWNER&&norm(val('CCOWNER',i))!==norm(off.CCOWNER);return mode==='bu'?buBad:mode==='owner'?ownerBad:mode==='unmapped'?!off:!off||buBad||ownerBad}}
  $('officialQualityGrid').addEventListener('click',e=>{const b=e.target.closest('[data-official-summary]');if(!b||b.disabled)return;const labels={all:'Todas as pendências do mapa oficial',bu:'Recursos com BU diferente da oficial',owner:'Recursos com CCOWNER diferente do oficial',unmapped:'Recursos cujo CC não existe no mapa oficial'};openAdvancedPreset(labels[b.dataset.officialSummary],officialPredicate(b.dataset.officialSummary))});
  $('buccTbl').addEventListener('click',e=>{const b=e.target.closest('[data-official-drill]');if(!b)return;const cc=b.dataset.cc,bu=b.dataset.buCurrent,rules=[{field:'CC',op:'eq',value:cc},{field:'BU',op:'eq',value:bu}],offBu=b.dataset.buOfficial,offOwner=b.dataset.ownerOfficial;let label=`CC ${cc} · BU atual ${bu}`;if(offBu)label+=` → BU oficial ${offBu}`;if(offOwner)label+=` · CCOWNER oficial ${offOwner}`;openAdvancedPreset(label,i=>norm(val('CC',i))===norm(cc)&&norm(val('BU',i))===norm(bu),rules)});

  /* ================= AUDITORIA DE TAGS DE VMs ================= */
  /* A auditoria possui rota propria (/auditoria-vms). Ela nao e mais uma guia
     permanente do modulo de Governanca de Tags. */
  if(vmAuditModule){
  const vmTab=document.createElement('button');vmTab.type='button';vmTab.setAttribute('role','tab');vmTab.dataset.p='vm';vmTab.setAttribute('aria-selected','false');vmTab.textContent='Auditoria de VMs';$('tabs').insertBefore(vmTab,$('tabs').querySelector('[data-p="evo"]'));
  document.querySelector('main>.wrap')?.insertAdjacentHTML('beforeend',`<section class="page vm-audit-page" id="p-vm" hidden>
    <div class="vm-audit-heading"><div><h1>Auditoria operacional de VMs</h1></div></div>
    <div class="panel vm-filter-panel"><div class="hrow"><div><h2>Filtros de auditoria</h2><p class="sub" id="vmAuditCount"></p></div><div class="advanced-actions"><button class="action-btn" id="vmClear">Limpar</button><button class="action-btn primary" id="vmExport">Exportar resultado CSV</button></div></div><div class="vm-filters"><label>AMBIENTE<select id="vmEnv"><option value="">Todos</option></select></label><label>DISPONIBILIDADE<select id="vmAvailability"><option value="">Todas</option></select></label><label>WAVE<select id="vmWave"><option value="">Todas</option></select></label><label>ENDOFLIFE<select id="vmEol"><option value="">Todos</option></select></label><label>BU<select id="vmBu"><option value="">Todas</option></select></label><label>SUBSCRIPTION<select id="vmSub"><option value="">Todas</option></select></label><label>RESOURCE GROUP<select id="vmRg"><option value="">Todos</option></select></label><label class="vm-search">BUSCAR<input id="vmSearch" type="search" placeholder="VM, ResourceId, RG ou subscription"></label></div></div>
    <div class="grid vm-kpis" id="vmKpis"></div>
    <div class="panel"><div class="hrow"><div><h2>Resultado das regras de auditoria</h2><p class="sub">Uma VM pode aparecer em mais de uma regra; o total geral não a duplica.</p></div><span class="muted">Clique em uma regra para listar as VMs</span></div><div class="vm-rule-grid" id="vmRules"></div></div>
    <div class="grid vm-analysis-grid"><div class="panel c6"><h2>Matriz operacional de disponibilidade</h2><p class="sub">Regra esperada para as Tags START e STOP.</p><div class="tbl"><table id="vmAvailabilityMatrix"></table></div></div><div class="panel c6"><h2>Distribuição por AMBIENTE</h2><p class="sub">FULL em DEV ou HML requer avaliação de aderência operacional.</p><div class="tbl"><table id="vmEnvironmentMatrix"></table></div></div></div>
    <div class="grid vm-analysis-grid"><div class="panel c5"><h2>WAVE × AMBIENTE</h2><p class="sub">Classificação de ondas observada; não infere automaticamente se o contexto é corporativo ou de cliente.</p><div class="tbl"><table id="vmWaveMatrix"></table></div></div><div class="panel c7"><h2>Cobertura das Tags de VM</h2><p class="sub">Presença técnica das Tags de FinOps e operacionais utilizadas na auditoria.</p><div class="vm-tag-coverage" id="vmTagCoverage"></div></div></div>
    <div class="panel"><div class="hrow"><div><h2>Detalhamento das VMs</h2><p class="sub" id="vmDetailSummary"></p></div></div><div class="detail-table tbl"><table id="vmDetailTable"></table></div></div>
  </section>`);
  const vmFields=['AMBIENTE','BU','CC','CCOWNER','PRODUTO','BACKUP','DISPONIBILIDADE','DOMINIO','ENDOFLIFE','FUNCAO','SQUAD','SO','START','STOP','RESERVA','WAVE'];
  let vmRuleFilter='',vmInventoryClass='',vmTimer;
  const vmValue=(tag,i)=>R[tag]?val(tag,i):null;
  const vmBase=()=>{const out=[];for(let i=0;i<N;i++)if(R.sc[i]&&String(DI.type[R.t[i]]||'').toLowerCase()==='microsoft.compute/virtualmachines')out.push(i);return out};
  const vmIsFilled=(tag,i)=>{const v=vmValue(tag,i);return v!=null&&String(v).trim()!==''};
  function vmViolations(i){const env=norm(vmValue('AMBIENTE',i)),availability=norm(vmValue('DISPONIBILIDADE',i)),eol=norm(vmValue('ENDOFLIFE',i)),start=vmIsFilled('START',i),stop=vmIsFilled('STOP',i),issues=[];
    if((env==='DEV'||env==='HML')&&availability==='FULL')issues.push('FULL em DEV/HML');
    if(availability==='FULL'&&(start||stop))issues.push('START/STOP em FULL');
    if(availability==='PARCIAL'&&(!start||!stop))issues.push('START/STOP obrigatório em PARCIAL');
    if((availability==='SOBDEMANDA'||availability==='DISTRATO')&&!stop)issues.push('STOP obrigatório em SOBDEMANDA/DISTRATO');
    if(!['SIM','NAO'].includes(eol))issues.push('ENDOFLIFE vazio ou inválido');
    return issues;
  }
  const vmRuleDefs=[['FULL em DEV/HML','FULL em DEV ou HML','DISPONIBILIDADE=FULL não é recomendada nesses ambientes.'],['START/STOP em FULL','START ou STOP preenchido em FULL','FULL não requer agendamento operacional.'],['START/STOP obrigatório em PARCIAL','PARCIAL sem START/STOP','PARCIAL precisa das duas Tags preenchidas.'],['STOP obrigatório em SOBDEMANDA/DISTRATO','STOP em SOBDEMANDA/DISTRATO','SOBDEMANDA e DISTRATO exigem STOP.'],['ENDOFLIFE vazio ou inválido','ENDOFLIFE inválido','ENDOF LIFE deve ter valor válido.']];
  const vmMatch=(value,filter)=>!filter||(filter==='__EMPTY__'?String(value??'').trim()==='':String(value??'')===filter);
  function vmFiltered(){const env=$('vmEnv').value,availability=$('vmAvailability').value,wave=$('vmWave').value,eol=$('vmEol').value,bu=$('vmBu').value,sub=$('vmSub').value,rg=$('vmRg').value,q=$('vmSearch').value.trim().toLowerCase();return vmBase().filter(i=>{const sv=D.subs[R.s[i]]?.name||'',rv=D.rgs[R.g[i]]?.[0]||'';return vmMatch(vmValue('AMBIENTE',i),env)&&vmMatch(vmValue('DISPONIBILIDADE',i),availability)&&vmMatch(vmValue('WAVE',i),wave)&&vmMatch(vmValue('ENDOFLIFE',i),eol)&&vmMatch(vmValue('BU',i),bu)&&vmMatch(sv,sub)&&vmMatch(rv,rg)&&(!q||`${R.n[i]} ${R.id[i]} ${sv} ${rv}`.toLowerCase().includes(q))})}
  function fillVmSelect(id,values,label){const el=$(id),current=el.value,items=[...new Set(values.filter(v=>v!=null&&v!==''))].sort((a,b)=>String(a).localeCompare(String(b),'pt-BR'));el.innerHTML=`<option value="">${label}</option><option value="__EMPTY__">Vazio</option>`+items.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('');if(current==='__EMPTY__'||items.includes(current))el.value=current}
  function vmOptions(){const ix=vmBase();fillVmSelect('vmEnv',ix.map(i=>vmValue('AMBIENTE',i)),'Todos');fillVmSelect('vmAvailability',ix.map(i=>vmValue('DISPONIBILIDADE',i)),'Todas');fillVmSelect('vmWave',ix.map(i=>vmValue('WAVE',i)),'Todas');fillVmSelect('vmEol',ix.map(i=>vmValue('ENDOFLIFE',i)),'Todos');fillVmSelect('vmBu',ix.map(i=>vmValue('BU',i)),'Todas');fillVmSelect('vmSub',ix.map(i=>D.subs[R.s[i]]?.name),'Todas');fillVmSelect('vmRg',ix.map(i=>D.rgs[R.g[i]]?.[0]),'Todos')}
  function vmCell(tag,i){const v=vmValue(tag,i);return v==null?'<span class="pill bad">vazio</span>':compactValueCell(v,tag)}
  function vmTraceFiltered(){const sub=$('vmSub').value,rg=$('vmRg').value,q=$('vmSearch').value.trim().toLowerCase();return fullInventory().filter(r=>r.type==='microsoft.compute/virtualmachines'&&r.classification===vmInventoryClass&&vmMatch(r.subscription,sub)&&vmMatch(r.resourceGroup,rg)&&(!q||`${r.name} ${r.id} ${r.subscription} ${r.resourceGroup} ${r.reason} ${r.rule}`.toLowerCase().includes(q)))}
  function renderVmAudit(){const ix=vmFiltered(),all=vmBase(),bad=ix.filter(i=>vmViolations(i).length),conform=ix.filter(i=>!vmViolations(i).length),missingAvailability=ix.filter(i=>!vmIsFilled('DISPONIBILIDADE',i)),schedule=ix.filter(i=>vmViolations(i).some(x=>/START|STOP/.test(x))),eolYes=ix.filter(i=>norm(vmValue('ENDOFLIFE',i))==='SIM'),missingWave=ix.filter(i=>!vmIsFilled('WAVE',i));
    $('vmAuditCount').textContent=`${fmt(ix.length)} de ${fmt(all.length)} VMs elegíveis no resultado atual`;
    const kpis=[['virtual-machine.svg','VMs elegíveis',ix.length,'universo filtrado da auditoria'],['monitor.svg','VMs conformes',conform.length,`${pct(conform.length,ix.length)} sem violação das regras de auditoria`],['alerts.svg','VMs não conformes',bad.length,`${pct(bad.length,ix.length)} com uma ou mais violações`],['availability-set.svg','Sem DISPONIBILIDADE',missingAvailability.length,'Tag ausente ou vazia'],['schedule.svg','Agendamento inadequado',schedule.length,'regras envolvendo START e STOP'],['maintenance.svg','ENDOFLIFE=SIM',eolYes.length,'VMs marcadas em fim de vida'],['monitor.svg','Sem WAVE',missingWave.length,'classificação pendente']];
    const vmComplements=inventoryClasses.slice(1).map(classification=>[classification,fullInventory().filter(r=>r.type==='microsoft.compute/virtualmachines'&&r.classification===classification).length]).filter(([,n])=>n>0);
    $('vmKpis').innerHTML=kpis.map((c,n)=>`<div class="panel kpi c-auto vm-kpi" role="button" tabindex="0" data-vm-kpi="${n}"><div class="kpi-head"><div><div class="eyebrow">${c[1]}</div><div class="v">${fmt(c[2])}</div></div>${icon(c[0])}</div><div class="d">${c[3]}</div>${n===0&&vmComplements.length?`<div class="inventory-card-links">${vmComplements.map(([classification,total])=>`<button type="button" data-vm-inventory-class="${esc(classification)}">${fmt(total)} ${esc(classification.toLowerCase())}</button>`).join('')}</div><small class="inventory-filter-note">Clique para listar justificativas no detalhamento de VMs.</small>`:''}</div>`).join('');
    $('vmRules').innerHTML=vmRuleDefs.map(([key,title,desc])=>{const n=ix.filter(i=>vmViolations(i).includes(key)).length;return `<button class="vm-rule-card ${n?'has-issues':'ok'}" type="button" data-vm-rule="${esc(key)}"><span class="eyebrow">${esc(title)}</span><strong>${fmt(n)}</strong><small>${esc(desc)}</small><em>${n?'Ver VMs →':'Nenhuma pendência'}</em></button>`}).join('');
    const availabilityRows=[['FULL','Ausente','Ausente','Operação contínua'],['PARCIAL','Obrigatório','Obrigatório','Janela programada'],['SOBDEMANDA','Ausente','Obrigatório','Desligamento controlado'],['DISTRATO','Ausente','Obrigatório','Desligamento por encerramento']];$('vmAvailabilityMatrix').innerHTML=`<thead><tr><th>DISPONIBILIDADE</th><th>START</th><th>STOP</th><th>Expectativa</th><th class="r">VMs</th></tr></thead><tbody>${availabilityRows.map(([a,s,t,d])=>`<tr><td><b>${a}</b></td><td>${s}</td><td>${t}</td><td>${d}</td><td class="r">${fmt(ix.filter(i=>norm(vmValue('DISPONIBILIDADE',i))===a).length)}</td></tr>`).join('')}</tbody>`;
    const envs=['DEV','HML','PRD'];$('vmEnvironmentMatrix').innerHTML=`<thead><tr><th>AMBIENTE</th><th class="r">FULL</th><th class="r">PARCIAL</th><th class="r">SOBDEMANDA</th><th class="r">DISTRATO</th><th class="r">Sem DISP.</th></tr></thead><tbody>${envs.map(e=>`<tr><td><b>${e}</b></td>${['FULL','PARCIAL','SOBDEMANDA','DISTRATO'].map(a=>`<td class="r ${['DEV','HML'].includes(e)&&a==='FULL'?'vm-red':''}">${fmt(ix.filter(i=>norm(vmValue('AMBIENTE',i))===e&&norm(vmValue('DISPONIBILIDADE',i))===a).length)}</td>`).join('')}<td class="r">${fmt(ix.filter(i=>norm(vmValue('AMBIENTE',i))===e&&!vmIsFilled('DISPONIBILIDADE',i)).length)}</td></tr>`).join('')}</tbody>`;
    const vmWaveGroups={WAVE1:['WAVE1','WAVEPIX1','WAVESIMPLY1','WAVESCAF1','WAVEAD1','WAVEDB1'],WAVE2:['WAVE2','WAVEPIX2','WAVESIMPLY2','WAVESCAF2','WAVEAD2','WAVEDB2'],WAVE3:['WAVE3','WAVEPIX3','WAVESIMPLY3','WAVESCAF3','WAVEAD3','WAVEDB3'],WAVE4:['WAVE4','WAVEPIX4','WAVESIMPLY4','WAVESCAF4','WAVEAD4','WAVEDB4']};const vmWaveGroup=value=>Object.entries(vmWaveGroups).find(([,values])=>values.includes(norm(value)))?.[0]||'';
    const waves=['WAVE1','WAVE2','WAVE3','WAVE4'];$('vmWaveMatrix').innerHTML=`<thead><tr><th>GRUPO WAVE</th><th class="r">DEV</th><th class="r">HML</th><th class="r">PRD</th><th class="r">Total</th></tr></thead><tbody>${waves.map(w=>`<tr><td><div class="vm-wave-group"><b>${w}</b></div><small class="vm-wave-aliases">${vmWaveGroups[w].join(' · ')}</small></td>${['DEV','HML','PRD'].map(e=>`<td class="r">${fmt(ix.filter(i=>vmWaveGroup(vmValue('WAVE',i))===w&&norm(vmValue('AMBIENTE',i))===e).length)}</td>`).join('')}<td class="r">${fmt(ix.filter(i=>vmWaveGroup(vmValue('WAVE',i))===w).length)}</td></tr>`).join('')}<tr><td><b>NAO SE APLICA</b></td>${['DEV','HML','PRD'].map(e=>`<td class="r">${fmt(ix.filter(i=>norm(vmValue('WAVE',i))==='NAO SE APLICA'&&norm(vmValue('AMBIENTE',i))===e).length)}</td>`).join('')}<td class="r">${fmt(ix.filter(i=>norm(vmValue('WAVE',i))==='NAO SE APLICA').length)}</td></tr><tr><td><b>Sem WAVE</b></td><td class="r" colspan="3">—</td><td class="r"><b>${fmt(missingWave.length)}</b></td></tr></tbody>`;
    $('vmTagCoverage').innerHTML=vmFields.map(tag=>{const n=ix.filter(i=>vmIsFilled(tag,i)).length;return `<div class="vm-tag-row"><span>${tag}</span><div><i style="width:${ix.length?100*n/ix.length:0}%"></i></div><b>${pct(n,ix.length)}</b><small>${fmt(n)}</small></div>`}).join('');
    const trace=vmInventoryClass?vmTraceFiltered():null;
    $('vmDetailSummary').textContent=trace?`${fmt(trace.length)} VMs ${vmInventoryClass.toLowerCase()} exibidas; justificativas preservadas da fotografia. Filtros de Tags não são aplicados a itens fora dos indicadores.`:`${fmt(ix.length)} VMs exibidas; ${fmt(bad.length)} possuem uma ou mais regras em não conformidade. Tabela limitada a 500 linhas.`;
    $('vmDetailTable').innerHTML=trace?`<thead><tr><th>VM</th><th>Subscription</th><th>Resource Group</th><th>Elegibilidade</th><th>Classificação</th><th>Motivo</th><th>Regra</th></tr></thead><tbody>${trace.slice(0,500).map(r=>`<tr><td><div class="resource-name">${icon('virtual-machine.svg','sm')}<strong>${esc(r.name)}</strong></div></td><td>${esc(r.subscription)}</td><td>${esc(r.resourceGroup)}</td><td><span class="pill ${r.eligibility==='SIM'?'ok':r.classification==='Aguardando classificação'?'warn':'n'}">${esc(r.eligibility||'(vazio)')}</span></td><td>${esc(r.classification)}</td><td>${esc(r.reason||'—')}</td><td>${esc(r.rule||'—')}</td></tr>`).join('')}</tbody>`:`<thead><tr><th>VM</th><th>Subscription</th><th>Resource Group</th><th>AMBIENTE</th><th>DISPONIBILIDADE</th><th>START</th><th>STOP</th><th>WAVE</th><th>ENDOFLIFE</th><th>BU</th><th>PRODUTO</th><th>FUNCAO</th><th>Regras violadas</th></tr></thead><tbody>${ix.slice(0,500).map(i=>{const issues=vmViolations(i);return `<tr><td><div class="resource-name">${icon('virtual-machine.svg','sm')}<strong>${esc(shortResourceName(R.id[i],R.n[i]))}</strong></div></td><td>${esc(D.subs[R.s[i]]?.name||'')}</td><td>${esc(D.rgs[R.g[i]]?.[0]||'')}</td>${['AMBIENTE','DISPONIBILIDADE','START','STOP','WAVE','ENDOFLIFE','BU','PRODUTO','FUNCAO'].map(t=>`<td>${vmCell(t,i)}</td>`).join('')}<td>${issues.length?`<button type="button" class="compact-value" data-vm-issues="${i}"><span>${fmt(issues.length)} regra${issues.length>1?'s':''}</span><small>Ver →</small></button>`:'<span class="pill ok">Conforme</span>'}</td></tr>`}).join('')}</tbody>`;
  }
  $('vmKpis').addEventListener('click',e=>{const inventory=e.target.closest('[data-vm-inventory-class]');if(inventory){vmInventoryClass=inventory.dataset.vmInventoryClass;vmRuleFilter='';renderVmAudit();$('vmDetailTable').closest('.panel').scrollIntoView({behavior:'smooth',block:'start'});return}const b=e.target.closest('[data-vm-kpi]');if(!b)return;vmInventoryClass='';const actions=[()=>vmRuleFilter='',()=>vmRuleFilter='__CONFORME__',()=>vmRuleFilter='__NAO_CONFORME__',()=>vmRuleFilter='__SEM_DISP__',()=>vmRuleFilter='__AGENDAMENTO__',()=>{$('vmEol').value='SIM';vmRuleFilter=''},()=>{$('vmWave').value='';vmRuleFilter='__SEM_WAVE__'}];actions[+b.dataset.vmKpi]();renderVmAudit()});
  const vmFilteredBase=vmFiltered;vmFiltered=function(){const raw=vmFilteredBase();if(!vmRuleFilter)return raw;if(vmRuleDefs.some(x=>x[0]===vmRuleFilter))return raw.filter(i=>vmViolations(i).includes(vmRuleFilter));return raw.filter(i=>vmRuleFilter==='__CONFORME__'?!vmViolations(i).length:vmRuleFilter==='__NAO_CONFORME__'?!!vmViolations(i).length:vmRuleFilter==='__SEM_DISP__'?!vmIsFilled('DISPONIBILIDADE',i):vmRuleFilter==='__AGENDAMENTO__'?vmViolations(i).some(x=>/START|STOP/.test(x)):vmRuleFilter==='__SEM_WAVE__'?!vmIsFilled('WAVE',i):true)};
  $('vmRules').addEventListener('click',e=>{const b=e.target.closest('[data-vm-rule]');if(!b)return;vmInventoryClass='';vmRuleFilter=b.dataset.vmRule;renderVmAudit();$('vmDetailTable').closest('.panel').scrollIntoView({behavior:'smooth',block:'start'})});
  $('vmDetailTable').addEventListener('click',e=>{const b=e.target.closest('[data-vm-issues]');if(!b)return;const i=+b.dataset.vmIssues,issues=vmViolations(i);$('ownerBreakdownTitle').textContent='Regras de auditoria';$('ownerBreakdownSubtitle').textContent=`${R.n[i]} · valores atuais preservados na fotografia`;$('ownerBreakdownBody').innerHTML=issues.map((x,n)=>`<div class="owner-list-row"><span><small class="value-index">${n+1}</small>${esc(x)}</span></div>`).join('');$('ownerBreakdownDialog').showModal()});
  for(const id of ['vmEnv','vmAvailability','vmWave','vmEol','vmBu','vmSub','vmRg'])$(id).addEventListener('change',()=>{vmInventoryClass='';vmRuleFilter='';renderVmAudit()});$('vmSearch').addEventListener('input',()=>{clearTimeout(vmTimer);vmTimer=setTimeout(()=>{vmRuleFilter='';renderVmAudit()},160)});$('vmClear').addEventListener('click',()=>{vmInventoryClass='';vmRuleFilter='';for(const id of ['vmEnv','vmAvailability','vmWave','vmEol','vmBu','vmSub','vmRg','vmSearch'])$(id).value='';renderVmAudit()});$('vmExport').addEventListener('click',()=>{const trace=vmInventoryClass?vmTraceFiltered():null,headers=trace?['VM','Subscription','ResourceGroup','ELEGIVEL_GOVERNANCA','ClassificacaoDashboard','MOTIVO_NAO_ELEGIVEL','REGRA_EXCLUSAO','ResourceId']:['ResourceId','VM','Subscription','ResourceGroup',...vmFields,'REGRAS_VIOLADAS'],lines=[headers.map(csvCell).join(';'),...(trace?trace.map(r=>[r.name,r.subscription,r.resourceGroup,r.eligibility,r.classification,r.reason,r.rule,r.id].map(csvCell).join(';')):vmFiltered().map(i=>[R.id[i],R.n[i],D.subs[R.s[i]]?.name,D.rgs[R.g[i]]?.[0],...vmFields.map(t=>vmValue(t,i)||''),vmViolations(i).join(' | ')].map(csvCell).join(';')))];downloadText(`Auditoria_Tags_VMs_${D.meta?.date||'sem_data'}.csv`,lines.join('\r\n'))});
  vmOptions();renderVmAudit();
  const renderWithVmAudit=render;
  render=function(){if(page==='vm'){vmOptions();renderVmAudit();return}renderWithVmAudit();if($('p-vm')){vmOptions();renderVmAudit()}};
  }
  $('advancedContext').addEventListener('click',e=>{if(!e.target.closest('#clearAdvancedPreset'))return;advancedPreset=null;renderAdvanced()});
  $('advancedKpis').addEventListener('click',e=>{const card=e.target.closest('[data-advanced-level]');if(!card)return;$('advancedLevel').value=card.dataset.advancedLevel;renderAdvanced(true);$('advancedTable').closest('.panel').scrollIntoView({behavior:'smooth',block:'start'})});
  renderEvo=renderAdvanced;$('advancedAdd').addEventListener('click',()=>{advancedPreset=null;advancedRules.push({field:'AMBIENTE',op:'eq',value:'PRD'});renderAdvanced()});$('advancedClear').addEventListener('click',()=>{advancedPreset=null;advancedRules=[];$('advancedSearch').value='';renderAdvanced()});$('advancedRules').addEventListener('input',e=>{const row=e.target.closest('[data-rule]');if(!row||e.target.dataset.key!=='value')return;advancedPreset=null;advancedRules[+row.dataset.rule].value=e.target.value;renderAdvanced(true)});$('advancedRules').addEventListener('change',e=>{const row=e.target.closest('[data-rule]');if(!row)return;advancedPreset=null;advancedRules[+row.dataset.rule][e.target.dataset.key]=e.target.value;renderAdvanced()});$('advancedRules').addEventListener('click',e=>{const b=e.target.closest('[data-remove-rule]');if(!b)return;advancedPreset=null;advancedRules.splice(+b.dataset.removeRule,1);renderAdvanced()});$('advancedLogic').addEventListener('change',()=>renderAdvanced());$('advancedLevel').addEventListener('change',()=>renderAdvanced(true));let advancedTimer;$('advancedSearch').addEventListener('input',()=>{clearTimeout(advancedTimer);advancedTimer=setTimeout(()=>renderAdvanced(true),150)});$('advancedExport').addEventListener('click',()=>{const ix=advancedIndexes(),map=new Map((governanceConfig.officialMap||[]).map(x=>[norm(x.CC),x])),headers=['ResourceId','Subscription','ResourceGroup','ResourceName','ResourceType',...TAGS,'BU_OFICIAL','CCOWNER_OFICIAL','STATUS_MAPA_OFICIAL'],lines=[headers.map(csvCell).join(';'),...ix.map(i=>{const off=map.get(norm(val('CC',i))),buBad=!!off&&norm(val('BU',i))!==norm(off.BU),ownerBad=!!off&&!!off.CCOWNER&&norm(val('CCOWNER',i))!==norm(off.CCOWNER),status=!off?'CC SEM MAPEAMENTO':buBad&&ownerBad?'BU E CCOWNER DIVERGENTES':buBad?'BU DIVERGENTE':ownerBad?'CCOWNER DIVERGENTE':'CONFORME';return [R.id[i],D.subs[R.s[i]].name,D.rgs[R.g[i]][0],R.n[i],DI.type[R.t[i]],...TAGS.map(t=>val(t,i)||''),off?.BU||'',off?.CCOWNER||'',status].map(csvCell).join(';')})];downloadText(`Analise_Avancada_${D.meta?.date||'sem_data'}.csv`,lines.join('\r\n'))});

  function parseSubscriptions(rows){
    // Aceita o cadastro corporativo atual e variações PT/EN comuns em exportações.
    const get=(r,...keys)=>{for(const key of keys)if(r[key]!=null)return r[key];return ''};
    const clean=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toUpperCase();
    const parsed=rows.map(r=>({
      name:get(r,'SUBSCRIPTION NAME','SUBSCRIPTION','NAME','NOME DA ASSINATURA','NOME ASSINATURA','ASSINATURA').trim(),
      id:get(r,'SUBSCRIPTION ID','SUBSCRIPTIONID','ID','ID DA ASSINATURA','ID ASSINATURA').trim().toLowerCase(),
      managementGroup:get(r,'PARENT MANAGEMENT GROUP','MANAGEMENT GROUP','GRUPO DE GERENCIAMENTO PAI','GRUPO DE GERENCIAMENTO').trim(),
      status:get(r,'STATUS','STATE','ESTADO','SITUACAO','SITUAÇÃO').trim(),
      inScope:clean(get(r,'MANAGEMENT GROUP (MG-EVERTECBRASIL)?','NO ESCOPO?','IN SCOPE?','ESCOPO','ESCOPO GOVERNANCA','ESCOPO GOVERNANÇA'))==='SIM'
    })).filter(x=>x.name&&/^[0-9a-f-]{36}$/.test(x.id));
    if(!parsed.length)throw Error('O cadastro de subscriptions não contém linhas válidas. Confira Nome e ID da Assinatura.');return parsed;
  }
  const box=$('p-pbi').querySelector('.import-box'),fields=box.querySelector('.import-fields'),labels=fields.querySelectorAll('label');
  box.querySelector('.sub').textContent='Carregue o CSV de recursos elegíveis da Governança. O cadastro corporativo de subscriptions é um arquivo mestre e só precisa ser reenviado quando houver alteração.';
  labels[0].childNodes[0].nodeValue='1. CSV de recursos elegíveis da Governança';labels[1].hidden=true;labels[2].childNodes[0].nodeValue='3. Data de coleta';
  labels[0].insertAdjacentHTML('afterend','<label>2. Cadastro de subscriptions (opcional)<input id="subscriptionsFileV2" type="file" accept=".csv,text/csv"><small class="muted">Mantém o cadastro atual se não for selecionado.</small></label>');
  const oldButton=$('applyImport'),newButton=oldButton.cloneNode(true);newButton.textContent='Gravar nova fotografia';oldButton.replaceWith(newButton);
  newButton.addEventListener('click',async()=>{const msg=$('importMessage');newButton.disabled=true;try{const file=$('csvFull').files[0];if(!file)throw Error('Selecione o CSV de recursos elegíveis da Governança.');msg.textContent='Lendo e validando os recursos elegíveis de Governança…';const source=parseCSV(await file.text()),parsed=prepareGovernanceImport(source);const sourceDates=[...new Set(parsed.dates.map(x=>x.slice(0,10)).filter(Boolean))];if(sourceDates.length>1)throw Error('O CSV possui mais de uma Data de Coleta. Gere uma única fotografia antes de importar.');let date=$('collectionDate').value;let dateAdjusted=false;if(sourceDates.length===1){const sourceDate=sourceDates[0];dateAdjusted=!!date&&date!==sourceDate;date=sourceDate;$('collectionDate').value=sourceDate;}if(!/^\d{4}-\d{2}-\d{2}$/.test(date||''))throw Error('Informe a Data de Coleta ou utilize um CSV que contenha essa informação.');const sf=$('subscriptionsFileV2').files[0];if(sf){governanceConfig.subscriptions=parseSubscriptions(simpleCSV(await sf.text()));await saveConfig()}const candidate=buildData(parsed,parsed,{date,fullFile:file.name,scopeFile:file.name,eligibleFile:file.name,subscriptionFile:sf?.name||D.meta?.subscriptionFile||'cadastro persistido',singleScope:true},H);candidate.R.sc=candidate.R.sc.map(()=>1);candidate.subs.forEach(s=>s.inScope=true);msg.textContent='Validação concluída. Gravando fotografia…';await persistSnapshot(candidate);D=candidate;R=D.R;N=R.s.length;DI=D.dict;curTag='AMBIENTE';selSub=null;selRg=null;Object.keys(globalFilters).forEach(k=>globalFilters[k]='');$('globalSearch').value='';refreshGlobalFilterOptions();detailOptions();render();syncEvidence();await loadSnapshotHistory();msg.textContent=`Fotografia gravada com ${fmt(parsed.index.size)} recursos elegíveis de Governança.${dateAdjusted?' A data foi ajustada para a data declarada no CSV.':''}`}catch(error){msg.textContent='Não atualizado: '+error.message}finally{newButton.disabled=false}});

  /* Estado de análise é deliberadamente efêmero: F5 retorna à visão inicial limpa. */
  Object.keys(globalFilters).forEach(key=>globalFilters[key]='');
  advancedPreset=null;advancedRules=[];selSub=null;selRg=null;
  for(const id of ['globalAmbiente','globalBu','globalCapex','globalType','globalSearch','detSubV2','detRgV2','detTypeV2','detPendV2','detSearchV2','advancedSearch']){const control=$(id);if(control){if(control.type==='checkbox')control.checked=false;else control.value=''}}
  page=vmAuditModule?'vm':'exec';
  if(vmAuditModule){
    document.title='Auditoria de Tags de VMs — Evertec';
    $('moduleBrandTitle').textContent='FinOps · Auditoria de Tags de VMs';
    $('scopeSeg').hidden=true;
    $('globalType').closest('label')?.setAttribute('hidden','');
    globalFilters.type='';
    document.querySelector('.evidence-strip').hidden=true;
    $('tabs').querySelectorAll('button:not([data-p="vm"])').forEach(button=>button.remove());
  }
  $('tabs').querySelectorAll('button').forEach(button=>button.setAttribute('aria-selected',button.dataset.p===page));document.querySelectorAll('section.page').forEach(section=>section.hidden=section.id!==`p-${page}`);

  const originalLoad=loadGovernanceConfig;
  loadGovernanceConfig=async function(){await originalLoad();detailOptions();render()};
  refreshGlobalFilterOptions();detailOptions();render();
  fetch('/api/tags/governance-config').then(response=>response.ok?response.json():null).then(config=>{if(config){governanceConfig=config;detailOptions();render()}}).catch(()=>{});
  requestAnimationFrame(()=>document.body.classList.remove('v2-loading'));
})();
