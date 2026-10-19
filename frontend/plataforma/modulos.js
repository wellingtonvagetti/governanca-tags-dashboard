/* Plataforma FinOps: lista de modulos e seletor do topo.
   Uso: <div data-mod-seletor="rec"></div> + este script. */
(function () {
  'use strict';
  var MODULOS = [
    { id: 'inicio', nome: 'Início', url: '/' },
    { id: 'rec', nome: 'Recomendações FinOps', url: '/recomendacoes' },
    { id: 'tags', nome: 'Governança de Tags', url: '/tags' },
    { id: 'auditoria-vms', nome: 'Auditoria de Tags de VMs', emBreve: true }
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

  function iniciar() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-mod-seletor]'), montar);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
