/* Gruvbox Clean docs: search, copy buttons, mobile navigation and "on this page" highlighting. */
(() => {
  'use strict';
  const root = document.body.dataset.root || '';
  const $ = s => document.querySelector(s);
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // ---------- copy buttons on code blocks ----------
  document.querySelectorAll('.prose .highlight').forEach(block => {
    const btn = document.createElement('button');
    btn.className = 'copy';
    btn.type = 'button';
    btn.textContent = 'Copy';
    btn.addEventListener('click', () => {
      const text = block.querySelector('pre').innerText.replace(/\n$/, '');
      navigator.clipboard?.writeText(text).then(() => {
        btn.textContent = 'Copied';
        btn.classList.add('done');
        setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('done'); }, 1600);
      });
    });
    block.appendChild(btn);
  });

  // ---------- mobile navigation ----------
  const toggle = $('#nav-toggle'), sidebar = $('#sidebar');
  toggle?.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('click', e => {
    if (sidebar?.classList.contains('open') && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
      sidebar.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });

  // ---------- "on this page" highlighting ----------
  const tocLinks = [...document.querySelectorAll('.toc a')];
  const heads = tocLinks.map(a => document.getElementById(decodeURIComponent(a.hash.slice(1)))).filter(Boolean);
  if (heads.length && 'IntersectionObserver' in window) {
    const visible = new Set();
    const mark = () => {
      const first = heads.find(h => visible.has(h)) || heads.filter(h => h.getBoundingClientRect().top < 120).pop();
      tocLinks.forEach(a => a.classList.toggle('on', !!first && a.hash === `#${first.id}`));
    };
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => (en.isIntersecting ? visible.add(en.target) : visible.delete(en.target)));
      mark();
    }, { rootMargin: '-70px 0px -60% 0px' });
    heads.forEach(h => io.observe(h));
  }

  // ---------- search ----------
  const index = window.DOCS_INDEX || [];
  const input = $('#q'), box = $('#results');
  let active = -1;

  const reEsc = t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  function highlight(text, terms) {
    let out = esc(text);
    terms.forEach(t => { out = out.replace(new RegExp(`(${reEsc(esc(t))})`, 'gi'), '<mark>$1</mark>'); });
    return out;
  }
  function snippet(text, term) {
    const i = text.toLowerCase().indexOf(term);
    if (i < 0) return text.slice(0, 110);
    const start = Math.max(0, i - 40);
    return (start ? '…' : '') + text.slice(start, start + 120);
  }
  function search(terms) {
    return index
      .map(e => {
        const hay = `${e.heading} ${e.text}`.toLowerCase();
        if (!terms.every(t => hay.includes(t))) return null;
        const score = terms.reduce((s, t) => s + (e.heading.toLowerCase().includes(t) ? 10 : 0) + (e.page.toLowerCase().includes(t) ? 3 : 0), 0);
        return { ...e, score };
      })
      .filter(Boolean)
      .sort((a, b) => b.score - a.score)
      .slice(0, 9);
  }
  function render() {
    const q = input.value.trim();
    if (!q) { box.classList.remove('open'); return; }
    const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    const hits = search(terms);
    active = hits.length ? 0 : -1;
    box.innerHTML = hits.length
      ? hits.map((h, i) => `<a href="${root}${h.url}" class="${i === 0 ? 'active' : ''}" role="option">
          <small>${esc(h.page)}</small><b>${highlight(h.heading, terms)}</b><span>${highlight(snippet(h.text, terms[0]), terms)}</span></a>`).join('')
      : `<div class="none">No results for “${esc(q)}”</div>`;
    box.classList.add('open');
  }
  function move(d) {
    const links = [...box.querySelectorAll('a')];
    if (!links.length) return;
    active = (active + d + links.length) % links.length;
    links.forEach((a, i) => a.classList.toggle('active', i === active));
    links[active].scrollIntoView({ block: 'nearest' });
  }
  input?.addEventListener('input', render);
  input?.addEventListener('focus', render);
  input?.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
    else if (e.key === 'Enter') { const a = box.querySelectorAll('a')[active]; if (a) location.href = a.href; }
    else if (e.key === 'Escape') { input.value = ''; box.classList.remove('open'); input.blur(); }
  });
  document.addEventListener('click', e => { if (!e.target.closest('.search')) box?.classList.remove('open'); });
  document.addEventListener('keydown', e => {
    if (e.key === '/' && !e.target.matches('input, textarea')) { e.preventDefault(); input?.focus(); }
  });
})();
