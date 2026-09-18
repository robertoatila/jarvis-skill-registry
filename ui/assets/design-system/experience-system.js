(() => {
  'use strict';

  const SIDEBAR_KEY = 'jarvis.sidebar.collapsed';
  const STYLE_PATHS = [
    '/assets/design-system/tokens.css',
    '/assets/design-system/components.css',
    '/assets/design-system/patterns.css'
  ];

  const NAV_ITEMS = [
    { group: 'Command', id: 'tabNeural', label: 'Assistente J.A.R.V.I.S.', icon: 'AI', shortcut: 'Alt+1' },
    { group: 'Command', id: 'tabPipeline', label: 'Auditoria & Missões', icon: 'EX', shortcut: 'Alt+6' },
    { group: 'Intelligence', id: 'tabArsenal', label: 'Arsenal de Skills', icon: 'SK', shortcut: 'Alt+2' },
    { group: 'Intelligence', id: 'tabIngest', label: 'Radar do GitHub', icon: 'GH', shortcut: 'Alt+3' },
    { group: 'Operations', id: 'tabSubagents', label: 'Agentes & Esquadrões', icon: 'AG', shortcut: 'Alt+4' },
    { group: 'Operations', id: 'tabSecurity', label: 'Segurança', icon: 'SE', shortcut: 'Alt+5' },
    { group: 'Knowledge', id: 'tabObsidian', label: 'Cofre Cognitivo', icon: 'KB', shortcut: 'Alt+7' }
  ];

  const METRICS = [
    { target: 'jv-progress-events', key: 'eventCount', label: 'Eventos', meta: 'receipts estruturados' },
    { target: 'jv-progress-attempts', key: 'attemptCount', label: 'Tentativas', meta: 'attempt IDs observados' },
    { target: 'jv-progress-verified', key: 'verifiedCount', label: 'VERIFIED', meta: 'verification receipts' },
    { target: 'jv-progress-rate', key: 'verificationRate', label: 'Taxa verificada', meta: 'somente quando medida' }
  ];

  function injectStyles() {
    STYLE_PATHS.forEach((href) => {
      if (document.querySelector(`link[data-jarvis-design-system="${href}"]`)) return;
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.dataset.jarvisDesignSystem = href;
      document.head.appendChild(link);
    });
  }

  function readCollapsedPreference() {
    try {
      const stored = localStorage.getItem(SIDEBAR_KEY);
      if (stored === null) return window.matchMedia('(max-width: 900px)').matches;
      return stored === 'true';
    } catch (_) {
      return window.matchMedia('(max-width: 900px)').matches;
    }
  }

  function writeCollapsedPreference(value) {
    try {
      localStorage.setItem(SIDEBAR_KEY, String(value));
    } catch (_) {}
  }

  function setCollapsed(value, persist = true) {
    document.body.dataset.sidebarCollapsed = String(Boolean(value));
    const toggle = document.getElementById('sidebar-toggle');
    if (toggle) {
      toggle.setAttribute('aria-expanded', String(!value));
      toggle.setAttribute('aria-label', value ? 'Expandir menu lateral JARVIS' : 'Recolher menu lateral JARVIS');
      toggle.textContent = value ? '»' : '«';
    }
    if (persist) writeCollapsedPreference(Boolean(value));
  }

  function selectedTabId() {
    const active = document.querySelector('.nav-tab.active[data-tab]');
    return active ? active.getAttribute('data-tab') : 'tabNeural';
  }

  function syncSidebarSelection(sidebar) {
    const activeId = selectedTabId();
    sidebar.querySelectorAll('[data-jarvis-tab]').forEach((button) => {
      const selected = button.dataset.jarvisTab === activeId;
      button.classList.toggle('is-selected', selected);
      button.setAttribute('aria-current', selected ? 'page' : 'false');
    });
  }

  function activateExistingTab(tabId) {
    const source = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
    if (!source) return;
    source.click();
    if (window.matchMedia('(max-width: 900px)').matches) setCollapsed(true);
  }

  function createSidebar() {
    if (document.getElementById('jarvis-sidebar')) return;

    const toggle = document.createElement('button');
    toggle.id = 'sidebar-toggle';
    toggle.type = 'button';
    toggle.className = 'jv-sidebar-toggle';
    toggle.setAttribute('aria-controls', 'jarvis-sidebar');
    toggle.addEventListener('click', () => {
      setCollapsed(document.body.dataset.sidebarCollapsed !== 'true');
    });

    const sidebar = document.createElement('aside');
    sidebar.id = 'jarvis-sidebar';
    sidebar.className = 'jv-sidebar';
    sidebar.setAttribute('aria-label', 'Navegação principal JARVIS');
    sidebar.innerHTML = `
      <div class="jv-sidebar__brand">
        <div class="jv-sidebar__eyebrow">J.A.R.V.I.S. // CONTROL PLANE</div>
        <div class="jv-sidebar__title">Cognitive Runtime</div>
      </div>
    `;

    let currentGroup = '';
    let section = null;
    let nav = null;

    NAV_ITEMS.forEach((item) => {
      if (item.group !== currentGroup) {
        currentGroup = item.group;
        section = document.createElement('section');
        section.className = 'jv-sidebar__section';
        section.innerHTML = `<div class="jv-sidebar__section-label">${item.group}</div>`;
        nav = document.createElement('nav');
        nav.className = 'jv-sidebar__nav';
        nav.setAttribute('aria-label', `${item.group} navigation`);
        section.appendChild(nav);
        sidebar.appendChild(section);
      }

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'jv-sidebar__item';
      button.dataset.jarvisTab = item.id;
      button.innerHTML = `
        <span class="jv-sidebar__icon" aria-hidden="true">${item.icon}</span>
        <span class="jv-sidebar__label">${item.label}</span>
        <span class="jv-sidebar__shortcut">${item.shortcut}</span>
      `;
      button.addEventListener('click', () => activateExistingTab(item.id));
      nav.appendChild(button);
    });

    const footer = document.createElement('div');
    footer.className = 'jv-sidebar__footer';
    footer.innerHTML = `
      <div>Alt+B alterna o menu.</div>
      <a href="/assets/design-system/index.html" target="_blank" rel="noopener noreferrer">Design system ↗</a>
    `;
    sidebar.appendChild(footer);

    document.body.prepend(sidebar);
    document.body.prepend(toggle);
    setCollapsed(readCollapsedPreference(), false);
    syncSidebarSelection(sidebar);

    const legacyNav = document.getElementById('hudNavigation');
    if (legacyNav) {
      new MutationObserver(() => syncSidebarSelection(sidebar)).observe(legacyNav, {
        subtree: true,
        attributes: true,
        attributeFilter: ['class', 'aria-selected']
      });
    }
  }

  function metricMarkup(metric) {
    return `
      <div class="jv-metric">
        <span class="jv-metric__label">${metric.label}</span>
        <strong class="jv-metric__value" id="${metric.target}">—</strong>
        <span class="jv-metric__meta">${metric.meta}</span>
      </div>
    `;
  }

  function applyOperationalProgression(detail) {
    if (!detail || typeof detail !== 'object') return;
    const mission = document.querySelector('#jarvis-progress-rail .jv-progress-rail__title');
    const note = document.querySelector('#jarvis-progress-rail .jv-progress-rail__note');
    if (mission) mission.textContent = detail.missionId || '—';
    if (note) note.textContent = detail.state
      ? `Estado derivado de receipts: ${detail.state}`
      : '— Sem estado derivado de receipts.';

    const progression = detail.progression || {};
    METRICS.forEach((metric) => {
      const target = document.getElementById(metric.target);
      if (!target) return;
      const value = progression[metric.key];
      if (metric.key === 'verificationRate') {
        const display = value && typeof value.display === 'string' ? value.display : '—';
        target.textContent = display;
        target.setAttribute('aria-label', value && value.accessible ? value.accessible : 'Sem dados de verificação');
        return;
      }
      const measured = Number.isInteger(value) && value >= 0;
      target.textContent = measured ? String(value) : '—';
      target.setAttribute('aria-label', measured ? `${value} ${metric.meta}` : `Sem dados para ${metric.label}`);
    });
  }

  function createProgressRail() {
    if (document.getElementById('jarvis-progress-rail')) return;
    const header = document.getElementById('jarvisHeader');
    if (!header || !header.parentNode) return;

    const rail = document.createElement('section');
    rail.id = 'jarvis-progress-rail';
    rail.className = 'jv-progress-rail';
    rail.setAttribute('aria-label', 'Progressão operacional baseada em receipts');
    rail.innerHTML = `
      <div class="jv-progress-rail__mission">
        <span class="jv-progress-rail__kicker">Progressão operacional</span>
        <strong class="jv-progress-rail__title">—</strong>
        <span class="jv-progress-rail__note">— Sem receipts carregados. Nenhum percentual é inferido.</span>
      </div>
      ${METRICS.map(metricMarkup).join('')}
    `;
    header.insertAdjacentElement('afterend', rail);
  }

  function bindKeyboard() {
    window.addEventListener('keydown', (event) => {
      if (event.altKey && !event.ctrlKey && !event.metaKey && event.key.toLowerCase() === 'b') {
        event.preventDefault();
        setCollapsed(document.body.dataset.sidebarCollapsed !== 'true');
      }
    });
  }

  function init() {
    if (document.body.classList.contains('jv-experience-ready')) return;
    injectStyles();
    document.body.classList.add('jv-experience-ready');
    createSidebar();
    createProgressRail();
    document.addEventListener('jarvis:operational-cockpit', (event) => {
      applyOperationalProgression(event.detail);
    });
    bindKeyboard();
    document.dispatchEvent(new CustomEvent('jarvis:experience-ready'));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
