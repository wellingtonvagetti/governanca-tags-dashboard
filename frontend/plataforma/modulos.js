/* Plataforma FinOps: lista de modulos e seletor do topo.
   Uso: <div data-mod-seletor="rec"></div> + este script. */
(function () {
  'use strict';
  var MODULOS = [
    { id: 'inicio', nome: 'Início', url: '/' },
    { id: 'rec', nome: 'Recomendações FinOps', url: '/recomendacoes' },
    { id: 'tags', nome: 'Governança de Tags', url: '/tags' },
    { id: 'auditoria-vms', nome: 'Auditoria de Tags de VMs', url: '/auditoria-vms' }
  ];
  window.PLATAFORMA_MODULOS = MODULOS;

  function esc(t) {
    return String(t).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function montar(alvo) {
    var atual = alvo.getAttribute('data-mod-seletor');
    var sel = MODULOS.filter(function (m) { return m.id === atual; })[0] || MODULOS[0];
    var itens = MODULOS.map(function (m) {
      if (m.emBreve) return '<span>' + esc(m.nome) + '<small>EM BREVE</small></span>';
      return '<a href="' + m.url + '"' + (m.id === sel.id ? ' aria-current="page"' : '') + '>' + esc(m.nome) + '</a>';
    }).join('');
    alvo.classList.add('mod-v5');
    alvo.innerHTML = '<span class="mod-label-v5">MÓDULO</span>' +
      '<details class="mod-dd-v5"><summary aria-label="Módulo">' + esc(sel.nome) +
      '<span class="mod-arrow-v5" aria-hidden="true">▼</span></summary>' +
      '<nav class="mod-list-v5" aria-label="Módulos">' + itens + '</nav></details>';
    var dd = alvo.querySelector('details');
    document.addEventListener('click', function (e) { if (!dd.contains(e.target)) dd.removeAttribute('open'); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') dd.removeAttribute('open'); });
  }

  // Cada modulo carrega uma vez por aba e continua vivo: trocar de modulo (seletor do topo ou cards do Inicio) nao
  // sai da pagina; o modulo escolhido abre num quadro por cima, e voltar para um modulo ja aberto e instantaneo.
  // A barra de endereco acompanha (F5 abre o modulo atual) e o Voltar do navegador funciona.
  function caminho(u) { return u.pathname.replace(/\/+$/, '') || '/'; }
  var URLS_MODULOS = MODULOS.map(function (m) { return m.url.replace(/\/+$/, '') || '/'; });
  var DENTRO = false;
  try { DENTRO = window.top !== window && window.top.location.origin === location.origin; } catch (_) { DENTRO = false; }
  var ORIGEM = caminho(location), TITULO = document.title, quadros = {}, atual = ORIGEM;

  function mostrar(para, empilhar) {
    if (para === atual) return;
    atual = para;
    Object.keys(quadros).forEach(function (k) { quadros[k].style.display = k === para ? 'block' : 'none'; });
    if (para === ORIGEM) {
      document.documentElement.style.overflow = '';
      document.title = TITULO;
    } else {
      if (!quadros[para]) {
        var f = document.createElement('iframe');
        f.src = para;
        f.title = para;
        f.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;border:0;z-index:2147483640;background:#0d0e13;display:block';
        f.addEventListener('load', function () {
          try { if (atual === para) document.title = f.contentDocument.title || document.title; } catch (_) {}
        });
        document.body.appendChild(f);
        quadros[para] = f;
      }
      document.documentElement.style.overflow = 'hidden';
      try { document.title = quadros[para].contentDocument.title || document.title; } catch (_) {}
    }
    if (empilhar) history.pushState({ modV5: para }, '', para);
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a || e.defaultPrevented || e.ctrlKey || e.metaKey || e.shiftKey || e.button || a.target === '_blank') return;
    var u;
    try { u = new URL(a.getAttribute('href'), location.href); } catch (_) { return; }
    if (u.origin !== location.origin) return;
    var para = caminho(u);
    if (URLS_MODULOS.indexOf(para) < 0) return;
    // fecha o seletor antes de trocar: a pagina continua viva e, ao voltar, ele estaria aberto
    Array.prototype.forEach.call(document.querySelectorAll('.mod-dd-v5[open]'), function (d) { d.removeAttribute('open'); });
    if (DENTRO) {
      e.preventDefault();
      window.top.postMessage({ modV5: para }, location.origin);
      return;
    }
    e.preventDefault();
    mostrar(para, true);
  });

  if (!DENTRO) {
    try { history.replaceState(Object.assign({}, history.state || {}, { modV5: ORIGEM }), ''); } catch (_) {}
    window.addEventListener('popstate', function (e) {
      var para = e.state && e.state.modV5;
      if (para && URLS_MODULOS.indexOf(para) >= 0) mostrar(para, false);
    });
    window.addEventListener('message', function (e) {
      if (e.origin === location.origin && e.data && e.data.modV5 && URLS_MODULOS.indexOf(e.data.modV5) >= 0) {
        mostrar(e.data.modV5, true);
      }
    });
  }

  function iniciar() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-mod-seletor]'), montar);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
