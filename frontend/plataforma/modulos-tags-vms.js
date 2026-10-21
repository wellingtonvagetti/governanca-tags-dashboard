/* Complemento temporário de navegação do módulo Auditoria de Tags de VMs.
   Carregado após o seletor corporativo comum. */
(() => {
  const habilitar = () => {
    const folhas = [...document.body.querySelectorAll('*')].filter(item =>
      /Auditoria de Tags de VMs/i.test(item.textContent || '') &&
      ![...item.children].some(child => /Auditoria de Tags de VMs/i.test(child.textContent || ''))
    );

    folhas.forEach(item => {
      if (item.dataset.auditoriaVmHabilitada) return;
      item.dataset.auditoriaVmHabilitada = '1';
      const alvo = item.closest('button,a,[role="menuitem"],[role="option"]') || item;
      [alvo, item].forEach(elemento => {
        elemento.disabled = false;
        elemento.removeAttribute('disabled');
        elemento.removeAttribute('aria-disabled');
        elemento.classList.remove('disabled', 'off');
        elemento.style.setProperty('opacity', '1', 'important');
        elemento.style.setProperty('cursor', 'pointer', 'important');
      });
      const walker = document.createTreeWalker(alvo, NodeFilter.SHOW_TEXT);
      const textos = [];
      while (walker.nextNode()) textos.push(walker.currentNode);
      textos.forEach(texto => { texto.nodeValue = texto.nodeValue.replace(/\s*EM\s+BREVE\s*/ig, ' '); });
      [item, alvo].forEach(elemento => elemento.addEventListener('click', event => {
        event.preventDefault();
        event.stopPropagation();
        window.location.assign('/auditoria-vms');
      }, true));
    });
  };

  habilitar();
  new MutationObserver(habilitar).observe(document.body, { childList: true, subtree: true });
  window.addEventListener('load', habilitar, { once: true });
})();
