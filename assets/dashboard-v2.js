/* Dashboard executivo v2: universo único de recursos elegíveis + cadastro corporativo de subscriptions. */
(function(){
  'use strict';
  scope='esc';
  const iconBase='/assets/azure-icons/';
  const iconMap=[
    ['microsoft.compute/virtualmachines','virtual-machine.svg'],
    ['microsoft.storage/storageaccounts','storage-account.svg'],
    ['microsoft.containerservice/managedclusters','kubernetes-service.svg'],
    ['microsoft.sql/servers/databases','sql-database.svg'],
    ['microsoft.sqlvirtualmachine/sqlvirtualmachines','sql-database.svg'],
    ['microsoft.web/sites','app-service.svg'],
    ['microsoft.keyvault/vaults','key-vault.svg'],
    ['microsoft.network/virtualnetworks','virtual-network.svg'],
    ['microsoft.network/privateendpoints','private-endpoint.svg']
  ];
  const resourceIcon=type=>iconBase+(iconMap.find(([key])=>String(type||'').toLowerCase()===key)?.[1]||'resource-group.svg');
  const typeLabel=type=>({
    'microsoft.compute/virtualmachines':'Máquina Virtual','microsoft.storage/storageaccounts':'Storage Account',
    'microsoft.containerservice/managedclusters':'Kubernetes Service','microsoft.sql/servers/databases':'SQL Database',
    'microsoft.sqlvirtualmachine/sqlvirtualmachines':'SQL Virtual Machine','microsoft.web/sites':'App Service',
    'microsoft.keyvault/vaults':'Key Vault','microsoft.network/virtualnetworks':'Virtual Network',
    'microsoft.network/privateendpoints':'Private Endpoint'
  })[String(type||'').toLowerCase()]||String(type||'').replace(/^microsoft\./i,'');
  const eligibleIndexes=()=>{const out=[];for(let i=0;i<N;i++)if(R.sc[i])out.push(i);return out};
  const observedSubscriptionIds=ix=>new Set(ix.map(i=>String(D.subs[R.s[i]]?.id||'').toLowerCase()));
  const masterSubscriptions=()=>Array.isArray(governanceConfig?.subscriptions)?governanceConfig.subscriptions:[];
  const icon=(name,cls='')=>`<img class="azure-icon ${cls}" src="${iconBase+name}" alt="">`;

  document.body.classList.add('scope-v2');
  const evidence=document.querySelector('.evidence-strip');
  if(evidence){evidence.children[0].innerHTML='<b>Recursos elegíveis de Governança</b> · mg-evertecbrasil';evidence.children[1].textContent='Subscriptions corporativas e recursos observados são universos separados';}

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
    <div class="panel"><h2>Assinaturas no escopo</h2><p class="sub">Situação cadastral e presença de recursos elegíveis. Use o Detalhamento para consultar a lista completa.</p><div class="tbl scroll"><table id="subscriptionPreviewV2"></table></div></div>`;

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
      ['resource-group.svg','Com recursos elegíveis',observed.size,'subscriptions observadas nesta coleta'],
      ['resource-group.svg','Resource Groups',rgs.size,'com ao menos um recurso elegível'],
      ['resource-group.svg','Recursos elegíveis',ix.length,'ResourceId distinto'],
      ['resource-group.svg','CLIENTE classificado',pct(cliente.cl,cliente.n),`${fmt(cliente.cl)} de ${fmt(cliente.n)}`],
      ['resource-group.svg','PRODUTO classificado',pct(produto.cl,produto.n),`${fmt(produto.cl)} de ${fmt(produto.n)}`],
      ['resource-group.svg','Cobertura FOLIO',D.meta?.folioCollected?pct(folio.fill,folio.n):'—',D.meta?.folioCollected?`${fmt(folio.fill)} de ${fmt(folio.n)} CAPEX=SIM`:'FOLIO não coletado']
    ];
    $('execKpisV2').innerHTML=cards.map(c=>`<div class="panel kpi c3"><div class="kpi-head"><div><div class="eyebrow">${c[1]}</div><div class="v">${typeof c[2]==='number'?fmt(c[2]):c[2]}</div></div>${icon(c[0])}</div><div class="d">${c[3]}</div></div>`).join('');
    $('stackTagsV2').innerHTML=TAGS.map(t=>stackRow(t,ix)).join('');
    const tm=new Map();for(const i of ix){const t=DI.type[R.t[i]];tm.set(t,(tm.get(t)||0)+1)}const top=[...tm].sort((a,b)=>b[1]-a[1]).slice(0,10);
    $('typesV2').innerHTML=top.map(([t,n])=>`<div class="type-row">${icon(resourceIcon(t).split('/').pop(),'sm')}<div class="name" title="${esc(t)}">${esc(typeLabel(t))}</div><div class="count">${fmt(n)}</div></div>`).join('');
    $('subscriptionSummaryV2').innerHTML=[['Total corporativo',master.length||'—'],['Ativas no escopo',activeScope.length||'—'],['Com recursos elegíveis',observed.size],['Sem recursos elegíveis',master.length?without.length:'—']].map(x=>`<div><b>${typeof x[1]==='number'?fmt(x[1]):x[1]}</b><span>${x[0]}</span></div>`).join('');
    const den=activeScope.length||observed.size,covered=master.length?activeScope.filter(x=>observed.has(String(x.id).toLowerCase())).length:observed.size;
    $('subscriptionCoverageV2').innerHTML=`<div class="coverage-bar"><span style="width:${den?100*covered/den:0}%;background:var(--accent)"></span></div><div class="muted">${fmt(covered)} de ${fmt(den)} assinaturas ativas do escopo possuem recursos elegíveis nesta fotografia.</div>`;
    $('policyV2').innerHTML=`<div><div class="eyebrow">Geral</div><div class="kpi"><div class="v">≈98%</div></div><div class="gauge"><span style="width:98%"></span></div></div><div><div class="eyebrow">Tags</div><div class="kpi"><div class="v">100%</div></div><div class="gauge"><span style="width:100%"></span></div></div>`;
    const preview=(master.length?master.filter(x=>x.inScope):D.subs.filter(x=>x.inScope).map(x=>({name:x.name,id:x.id,status:'',managementGroup:'',inScope:true}))).slice(0,12);
    $('subscriptionPreviewV2').innerHTML=`<thead><tr><th>Subscription</th><th>Status</th><th>Management Group</th><th>Recursos elegíveis</th><th>Situação</th></tr></thead><tbody>${preview.map(s=>{const si=D.subs.findIndex(x=>String(x.id).toLowerCase()===String(s.id).toLowerCase()),n=si<0?0:ix.filter(i=>R.s[i]===si).length;return `<tr><td><b>${esc(s.name)}</b><br><span class="muted num">${esc(s.id)}</span></td><td>${esc(s.status||'—')}</td><td>${esc(s.managementGroup||'—')}</td><td class="r">${fmt(n)}</td><td>${n?'<span class="scope-state good">Com recursos</span>':'<span class="scope-state off">Sem recursos elegíveis</span>'}</td></tr>`}).join('')}</tbody>`;
  };

  const oldRenderTags=renderTags;
  renderTags=function(){
    oldRenderTags();const ix=eligibleIndexes();
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
    <label>Subscription<select id="detailSubV2"><option value="">Todas</option></select></label><label>Resource Group<select id="detailRgV2"><option value="">Todos</option></select></label><label>Tipo de recurso<select id="detailTypeV2"><option value="">Todos</option></select></label><label>Pendência<select id="detailPendingV2"><option value="">Todas</option><option value="classification">CLIENTE/PRODUTO</option><option value="folio">FOLIO em CAPEX=SIM</option><option value="folioNo">FOLIO em CAPEX=NAO</option></select></label><label>Buscar<input type="search" id="detailSearchV2" placeholder="Nome, RG ou ResourceId"></label>
    </div><div class="filter-actions"><div class="result-count" id="detailCountV2"></div><div><button class="action-btn" id="clearDetailV2">Limpar filtros</button> <button class="action-btn primary" id="exportDetailV2">Exportar CSV</button></div></div></div><div class="panel"><div class="detail-table tbl"><table id="detailTableV2"></table></div></div>`;
  function detailOptions(){
    const ix=eligibleIndexes(),subs=[...new Set(ix.map(i=>D.subs[R.s[i]].name))].sort(),rgs=[...new Set(ix.map(i=>D.rgs[R.g[i]][0]))].sort(),types=[...new Set(ix.map(i=>DI.type[R.t[i]]))].sort();
    $('detailSubV2').innerHTML='<option value="">Todas</option>'+subs.map(x=>`<option>${esc(x)}</option>`).join('');$('detailRgV2').innerHTML='<option value="">Todos</option>'+rgs.map(x=>`<option>${esc(x)}</option>`).join('');$('detailTypeV2').innerHTML='<option value="">Todos</option>'+types.map(x=>`<option value="${esc(x)}">${esc(typeLabel(x))}</option>`).join('');
  }
  function filteredResources(){const q=$('detailSearchV2').value.trim().toLowerCase(),sub=$('detailSubV2').value,rg=$('detailRgV2').value,type=$('detailTypeV2').value,p=$('detailPendingV2').value;return eligibleIndexes().filter(i=>{const sv=D.subs[R.s[i]].name,rv=D.rgs[R.g[i]][0],tv=DI.type[R.t[i]],folio=val('FOLIO',i);if(sub&&sv!==sub||rg&&rv!==rg||type&&tv!==type)return false;if(q&&!(`${R.n[i]} ${R.id[i]} ${rv} ${sv}`.toLowerCase().includes(q)))return false;if(p==='classification'&&!isPend(i))return false;if(p==='folio'&&!(val('CAPEX',i)==='SIM'&&folio==null))return false;if(p==='folioNo'&&!(val('CAPEX',i)==='NAO'&&folio!=null))return false;return true})}
  const cell=v=>v==null?'<span class="pill bad">vazio</span>':v==='INDEFINIDO'?'<span class="pill warn">INDEFINIDO</span>':esc(v);
  renderDet=function(){
    const level=$('detailLevelV2').value,ix=filteredResources();
    if(level==='subscriptions'){
      const observed=observedSubscriptionIds(ix),master=masterSubscriptions();$('detailCountV2').textContent=`${fmt(master.length)} assinaturas cadastradas`;
      $('detailTableV2').innerHTML=`<thead><tr><th>Subscription</th><th>Status</th><th>Management Group</th><th>Escopo</th><th>Recursos elegíveis</th><th>Situação</th></tr></thead><tbody>${master.map(s=>{const si=D.subs.findIndex(x=>String(x.id).toLowerCase()===String(s.id).toLowerCase()),n=si<0?0:eligibleIndexes().filter(i=>R.s[i]===si).length;return `<tr><td><b>${esc(s.name)}</b><br><span class="muted num">${esc(s.id)}</span></td><td>${esc(s.status)}</td><td>${esc(s.managementGroup)}</td><td>${s.inScope?'<span class="scope-state good">Sim</span>':'<span class="scope-state off">Não</span>'}</td><td class="r">${fmt(n)}</td><td>${norm(s.status)==='DISABLED'?'<span class="scope-state bad">Desativada</span>':n?'<span class="scope-state good">Com recursos</span>':'<span class="scope-state off">Sem recursos elegíveis</span>'}</td></tr>`}).join('')}</tbody>`;return;
    }
    if(level==='resourceGroups'){
      const m=new Map();for(const i of ix){const k=String(D.subs[R.s[i]].id).toLowerCase()+'|'+D.rgs[R.g[i]][0].toLowerCase(),o=m.get(k)||{sub:D.subs[R.s[i]].name,rg:D.rgs[R.g[i]][0],n:0,p:0};o.n++;if(isPend(i))o.p++;m.set(k,o)}const rows=[...m.values()].sort((a,b)=>b.n-a.n);$('detailCountV2').textContent=`${fmt(rows.length)} Resource Groups encontrados`;$('detailTableV2').innerHTML=`<thead><tr><th>Resource Group</th><th>Subscription</th><th class="r">Recursos</th><th class="r">Pendências</th><th>Status</th></tr></thead><tbody>${rows.map(o=>`<tr><td><div class="resource-name">${icon('resource-group.svg','sm')}<strong>${esc(o.rg)}</strong></div></td><td>${esc(o.sub)}</td><td class="r">${fmt(o.n)}</td><td class="r">${fmt(o.p)}</td><td>${o.p?'<span class="status-dot warn">Revisar</span>':'<span class="status-dot">Conforme</span>'}</td></tr>`).join('')}</tbody>`;return;
    }
    $('detailCountV2').textContent=`${fmt(ix.length)} recursos encontrados`;$('detailTableV2').innerHTML=`<thead><tr><th>Recurso</th><th>Subscription</th><th>Resource Group</th><th>Tipo</th><th>CAPEX</th><th>FOLIO</th><th>CLIENTE</th><th>PRODUTO</th></tr></thead><tbody>${ix.slice(0,500).map(i=>{const t=DI.type[R.t[i]];return `<tr><td><div class="resource-name">${icon(resourceIcon(t).split('/').pop(),'sm')}<div><strong>${esc(R.n[i])}</strong><small title="${esc(R.id[i])}">${esc(R.id[i])}</small></div></div></td><td>${esc(D.subs[R.s[i]].name)}</td><td>${esc(D.rgs[R.g[i]][0])}</td><td>${esc(typeLabel(t))}</td><td>${cell(val('CAPEX',i))}</td><td>${cell(val('FOLIO',i))}</td><td>${cell(val('CLIENTE',i))}</td><td>${cell(val('PRODUTO',i))}</td></tr>`}).join('')}</tbody>`+(ix.length>500?`<caption>Mostrando 500 de ${fmt(ix.length)}. Refine os filtros para reduzir o resultado.</caption>`:'');
  };
  ['detailLevelV2','detailSubV2','detailRgV2','detailTypeV2','detailPendingV2'].forEach(id=>$(id).addEventListener('change',renderDet));let detailTimer;$('detailSearchV2').addEventListener('input',()=>{clearTimeout(detailTimer);detailTimer=setTimeout(renderDet,180)});$('clearDetailV2').addEventListener('click',()=>{['detailSubV2','detailRgV2','detailTypeV2','detailPendingV2'].forEach(id=>$(id).value='');$('detailSearchV2').value='';renderDet()});
  $('openSubscriptionsV2').addEventListener('click',()=>{openPage('det');$('detailLevelV2').value='subscriptions';renderDet()});
  $('exportDetailV2').addEventListener('click',()=>{const ix=filteredResources(),headers=['ResourceId','Subscription','ResourceGroup','ResourceName','ResourceType',...TAGS],lines=[headers.join(';')];for(const i of ix)lines.push([R.id[i],D.subs[R.s[i]].name,D.rgs[R.g[i]][0],R.n[i],DI.type[R.t[i]],...TAGS.map(t=>val(t,i)||'')].map(csvCell).join(';'));downloadText(`Detalhamento_Governanca_${D.meta?.date||'sem_data'}.csv`,lines.join('\r\n'))});

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
  newButton.addEventListener('click',async()=>{const msg=$('importMessage');newButton.disabled=true;try{const file=$('csvFull').files[0];if(!file)throw Error('Selecione o CSV de recursos elegíveis da Governança.');msg.textContent='Lendo e validando os recursos elegíveis…';const parsed=parseCSV(await file.text());let date=$('collectionDate').value;if(!date){const dates=[...new Set(parsed.dates.map(x=>x.slice(0,10)))];if(dates.length===1)date=dates[0]}if(!/^\d{4}-\d{2}-\d{2}$/.test(date||''))throw Error('Informe a Data de Coleta.');if(parsed.dates.some(x=>x.slice(0,10)!==date))throw Error('A DataColeta do arquivo diverge da data selecionada.');const sf=$('subscriptionsFileV2').files[0];if(sf){governanceConfig.subscriptions=parseSubscriptions(simpleCSV(await sf.text()));await saveConfig()}const candidate=buildData(parsed,parsed,{date,fullFile:file.name,scopeFile:file.name,eligibleFile:file.name,subscriptionFile:sf?.name||D.meta?.subscriptionFile||'cadastro persistido',singleScope:true},H);candidate.R.sc=candidate.R.sc.map(()=>1);candidate.subs.forEach(s=>s.inScope=true);msg.textContent='Validação concluída. Gravando fotografia…';await persistSnapshot(candidate);D=candidate;R=D.R;N=R.s.length;DI=D.dict;curTag='AMBIENTE';selSub=null;selRg=null;detailOptions();render();syncEvidence();await loadSnapshotHistory();msg.textContent='Fotografia gravada. O painel agora utiliza somente os recursos elegíveis da Governança.'}catch(error){msg.textContent='Não atualizado: '+error.message}finally{newButton.disabled=false}});

  const originalLoad=loadGovernanceConfig;
  loadGovernanceConfig=async function(){await originalLoad();detailOptions();render()};
  detailOptions();render();setTimeout(()=>{detailOptions();render()},600);
})();
