/* Gruvbox Icon Studio: draw and edit Gruvbox Clean glyphs. No dependencies, no build step.
 * Glyphs use the repo's glyph JSON format (see scripts/glyph_store.py); the checks here mirror
 * the CI validator so an exported file passes the pipeline. */
(() => {
  'use strict';

  // ---------- constants ----------
  const G = window.GRUVBOX || {};
  const LIBRARY = (window.ICON_LIBRARY || []).slice().sort((a, b) => a.label.localeCompare(b.label));
  const DEFAULT_PALETTE = {
    tile: G.bg1 || '#3c3836', fg: G.fg || '#ebdbb2', accent: G.orange || '#fe8019', bg: G.bg0_h || '#1d2021',
    red: G.red || '#fb4934', green: G.green || '#b8bb26', yellow: G.yellow || '#fabd2f', blue: G.blue || '#83a598',
    purple: G.purple || '#d3869b', aqua: G.aqua || '#8ec07c', gray: G.gray || '#928374',
  };
  // Colour roles a shape can use; the pack renders each role from its own palette
  const ROLES = [
    { key: 'fg', name: 'Cream' }, { key: 'accent', name: 'Accent' }, { key: 'red', name: 'Red' },
    { key: 'green', name: 'Green' }, { key: 'yellow', name: 'Yellow' }, { key: 'blue', name: 'Blue' },
    { key: 'purple', name: 'Purple' }, { key: 'aqua', name: 'Aqua' }, { key: 'gray', name: 'Gray' },
  ];
  const ROLE_KEYS = ROLES.map(r => r.key);
  const ROLE_NAME = Object.fromEntries(ROLES.map(r => [r.key, r.name]));
  const STROKE = { min: 0.5, max: 4, def: 2 };  // line width range for stroke and ring shapes
  const PRESETS = [
    { id: 'dark', label: 'Gruvbox', pal: { ...DEFAULT_PALETTE } },
    { id: 'aqua', label: 'Aqua', pal: { ...DEFAULT_PALETTE, accent: G.aqua || '#8ec07c' } },
    { id: 'yellow', label: 'Yellow', pal: { ...DEFAULT_PALETTE, accent: G.yellow || '#fabd2f' } },
    { id: 'blue', label: 'Blue', pal: { ...DEFAULT_PALETTE, accent: G.blue || '#83a598' } },
    { id: 'purple', label: 'Purple', pal: { ...DEFAULT_PALETTE, accent: G.purple || '#d3869b' } },
    {
      id: 'light', label: 'Light', pal: {
        tile: '#ebdbb2', fg: '#3c3836', accent: '#d65d0e', bg: '#fbf1c7', red: '#9d0006', green: '#79740e',
        yellow: '#b57614', blue: '#076678', purple: '#8f3f71', aqua: '#427b58', gray: '#7c6f64',
      },
    },
  ];
  const SLOTS = [
    { key: 'tile', name: 'Tile', hint: 'icon background' },
    { key: 'fg', name: 'Lines', hint: 'main glyph colour' },
    { key: 'accent', name: 'Accent', hint: 'the one highlight' },
    { key: 'bg', name: 'Wallpaper', hint: 'preview background' },
  ];
  const GLYPH_BOX = 13;
  const OFF = (24 - GLYPH_BOX) / 2;
  const SCALE = (GLYPH_BOX / 24).toFixed(6);
  const MAX_ELEMENTS = 40;
  const TYPES = ['stroke', 'fill', 'ring', 'knock'];
  const TYPE_LABEL = { stroke: 'Stroke', fill: 'Fill', ring: 'Ring', knock: 'Cut-out' };
  const NAME_RE = /^[a-z][a-z0-9_]{1,40}$/;
  const PACKAGE_RE = /^[A-Za-z]\w*(\.[A-Za-z]\w*)+$/;
  const COMPONENT_RE = /^[A-Za-z]\w*(\.[A-Za-z]\w*)+\/[A-Za-z_$][\w.$]*$/;
  const RESERVED = new Set(`abstract assert boolean break byte case catch char class const continue default do
    double else enum extends final finally float for goto if implements import instanceof int interface long
    native new package private protected public return short static strictfp super switch synchronized this
    throw throws transient try void volatile while true false null iconback ic_launcher`.split(/\s+/));
  const KEYS = { doc: 'gis.doc.v1', palette: 'gis.palette.v1', prefs: 'gis.prefs.v1' };
  const HINTS = {
    select: 'Click a shape to select it, drag to move. Drag the round handles to reshape.',
    line: 'Drag to draw a line.',
    poly: 'Click to add points. Double-click or Enter to finish; click the first point to close the shape.',
    rect: 'Drag to draw a rounded rectangle.',
    circle: 'Drag out from the centre to draw a circle.',
  };

  // ---------- small utilities ----------
  const $ = (s, r = document) => r.querySelector(s);
  const fmt = v => { const n = Math.round(v * 100) / 100; return String(Object.is(n, -0) ? 0 : n); };
  const P = (x, y) => `${fmt(x)} ${fmt(y)}`;
  const clone = o => JSON.parse(JSON.stringify(o));
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  let uid = 0;
  const newId = () => `e${++uid}`;
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* storage unavailable */ } },
  };
  const slug = s => {
    let n = s.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 41);
    if (n && !/^[a-z]/.test(n)) n = `app_${n}`.slice(0, 41);
    return n;
  };
  const lines = s => s.split(/[\s,]+/).map(x => x.trim()).filter(Boolean);
  const roundShape = s => Object.fromEntries(Object.entries(s).map(([k, v]) => [k, typeof v === 'number' ? Math.round(v * 100) / 100 : v]));

  // ---------- SVG path model (absolute M L C Q A Z) ----------
  const TOKEN_RE = /[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?/g;
  const PATH_CHARS_RE = /^[MmLlHhVvCcSsQqTtAaZz0-9eE.,\s+-]+$/;
  const isCmd = t => /^[a-z]$/i.test(t);
  const XY = [['x', 'y'], ['x1', 'y1'], ['x2', 'y2']];

  function parsePath(d) {
    if (!PATH_CHARS_RE.test(d)) throw new Error('only path commands and numbers are allowed');
    const t = d.match(TOKEN_RE) || [];
    if (!t.length || !/^[Mm]$/.test(t[0])) throw new Error('a path must start with M');
    const segs = [];
    let i = 0, cmd = null, x = 0, y = 0, sx = 0, sy = 0, prev = null;
    const num = () => {
      if (i >= t.length || isCmd(t[i])) throw new Error(`"${cmd}" is missing numbers`);
      return parseFloat(t[i++]);
    };
    while (i < t.length) {
      if (isCmd(t[i])) cmd = t[i++];
      else if (!cmd) throw new Error(`unexpected number ${t[i]}`);
      const C = cmd.toUpperCase();
      const rel = cmd !== C;
      const ox = rel ? x : 0, oy = rel ? y : 0;
      let s;
      switch (C) {
        case 'Z': s = { c: 'Z' }; break;
        case 'M': s = { c: 'M', x: num() + ox, y: num() + oy }; break;
        case 'L': s = { c: 'L', x: num() + ox, y: num() + oy }; break;
        case 'H': s = { c: 'L', x: num() + ox, y }; break;
        case 'V': s = { c: 'L', x, y: num() + oy }; break;
        case 'C': s = { c: 'C', x1: num() + ox, y1: num() + oy, x2: num() + ox, y2: num() + oy, x: num() + ox, y: num() + oy }; break;
        case 'S': {
          const r = prev && prev.c === 'C' ? [2 * x - prev.x2, 2 * y - prev.y2] : [x, y];
          s = { c: 'C', x1: r[0], y1: r[1], x2: num() + ox, y2: num() + oy, x: num() + ox, y: num() + oy };
          break;
        }
        case 'Q': s = { c: 'Q', x1: num() + ox, y1: num() + oy, x: num() + ox, y: num() + oy }; break;
        case 'T': {
          const r = prev && prev.c === 'Q' ? [2 * x - prev.x1, 2 * y - prev.y1] : [x, y];
          s = { c: 'Q', x1: r[0], y1: r[1], x: num() + ox, y: num() + oy };
          break;
        }
        case 'A': {
          const rx = num(), ry = num(), rot = num(), large = num(), sweep = num();
          if (rx < 0 || ry < 0 || (large !== 0 && large !== 1) || (sweep !== 0 && sweep !== 1)) throw new Error('bad arc parameters');
          s = { c: 'A', rx, ry, rot, large, sweep, x: num() + ox, y: num() + oy };
          break;
        }
        default: throw new Error(`unknown command ${cmd}`);
      }
      segs.push(s);
      prev = s;
      if (C === 'Z') { x = sx; y = sy; cmd = null; continue; }
      x = s.x; y = s.y;
      if (C === 'M') { sx = x; sy = y; cmd = rel ? 'l' : 'L'; }
    }
    return segs;
  }

  function serializePath(segs) {
    return segs.map(s => {
      switch (s.c) {
        case 'M': return `M${P(s.x, s.y)}`;
        case 'L': return `L${P(s.x, s.y)}`;
        case 'C': return `C${P(s.x1, s.y1)} ${P(s.x2, s.y2)} ${P(s.x, s.y)}`;
        case 'Q': return `Q${P(s.x1, s.y1)} ${P(s.x, s.y)}`;
        case 'A': return `A${fmt(s.rx)} ${fmt(s.ry)} ${fmt(s.rot)} ${s.large} ${s.sweep} ${P(s.x, s.y)}`;
        default: return 'Z';
      }
    }).join(' ');
  }

  const translateSegs = (segs, dx, dy) => {
    segs.forEach(s => XY.forEach(([kx, ky]) => { if (kx in s) { s[kx] += dx; s[ky] += dy; } }));
    return segs;
  };
  const pathPoints = segs => segs.flatMap(s => XY.filter(([kx]) => kx in s).map(([kx, ky]) => [s[kx], s[ky]]));

  // ---------- shapes ----------
  function rectD({ x, y, w, h, r }) {
    r = Math.max(0, Math.min(r, w / 2, h / 2));
    if (r <= 0) return `M${P(x, y)} H${fmt(x + w)} V${fmt(y + h)} H${fmt(x)} Z`;
    const a = `A${fmt(r)} ${fmt(r)} 0 0 1`;
    return `M${P(x + r, y)} H${fmt(x + w - r)} ${a} ${P(x + w, y + r)} V${fmt(y + h - r)} ${a} ${P(x + w - r, y + h)} ` +
      `H${fmt(x + r)} ${a} ${P(x, y + h - r)} V${fmt(y + r)} ${a} ${P(x + r, y)} Z`;
  }
  const circleD = ({ cx, cy, r }) =>
    `M${P(cx - r, cy)} A${fmt(r)} ${fmt(r)} 0 1 0 ${P(cx + r, cy)} A${fmt(r)} ${fmt(r)} 0 1 0 ${P(cx - r, cy)} Z`;
  const shapeD = s => (s.kind === 'rect' ? rectD(s) : circleD(s));
  // Smallest allowed sizes; a negative radius would make an invalid arc
  const SHAPE_MIN = { w: 0.5, h: 0.5, rectR: 0, circleR: 0.25 };
  function rectFrom(a, b) {
    const w = Math.abs(b[0] - a[0]), h = Math.abs(b[1] - a[1]);
    return { kind: 'rect', x: Math.min(a[0], b[0]), y: Math.min(a[1], b[1]), w, h, r: Math.min(2.5, w / 2, h / 2) };
  }
  function sanitizeShape(s) {
    const nums = keys => keys.every(k => typeof s[k] === 'number' && Number.isFinite(s[k]));
    if (s.kind === 'rect' && nums(['x', 'y', 'w', 'h', 'r'])) {
      return roundShape({ kind: 'rect', x: s.x, y: s.y, w: Math.max(SHAPE_MIN.w, s.w), h: Math.max(SHAPE_MIN.h, s.h), r: Math.max(0, s.r) });
    }
    if (s.kind === 'circle' && nums(['cx', 'cy', 'r'])) {
      return roundShape({ kind: 'circle', cx: s.cx, cy: s.cy, r: Math.max(SHAPE_MIN.circleR, s.r) });
    }
    return null;
  }

  // ---------- rendering (same markup as scripts/glyph_store.py) ----------
  const TILE_D = (() => {
    const r = 5.28, e = fmt(24 - r);
    return `M${r} 0 H${e} A${r} ${r} 0 0 1 24 ${r} V${e} A${r} ${r} 0 0 1 ${e} 24 H${r} A${r} ${r} 0 0 1 0 ${e} V${r} A${r} ${r} 0 0 1 ${r} 0 Z`;
  })();

  function elementMarkup(el, pal) {
    const col = pal[el.color] || pal.fg;
    const d = esc(el.d);
    const w = el.width != null && el.width !== STROKE.def ? ` stroke-width="${fmt(el.width)}"` : '';
    switch (el.type) {
      case 'fill': return `<path d="${d}" fill="${col}"${el.soft ? ` stroke="${col}" stroke-width="1.2"` : ''}/>`;
      case 'ring': return `<path d="${d}" fill="${pal.tile}" stroke="${col}"${w}/>`;
      case 'knock': return `<path d="${d}" fill="${pal.tile}" stroke="${pal.tile}" stroke-width="${fmt(el.width ?? 5)}"/>`;
      default: return `<path d="${d}" stroke="${col}"${w}/>`;
    }
  }
  const hasLineWidth = el => el.type === 'stroke' || el.type === 'ring';

  function iconSVG(elements, pal, size = 192, attrs = '') {
    const body = elements.map(e => elementMarkup(e, pal)).join('\n    ');
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24"${attrs}>\n` +
      `  <path d="${TILE_D}" fill="${pal.tile}"/>\n` +
      `  <g transform="translate(${OFF} ${OFF}) scale(${SCALE})" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n` +
      `    ${body}\n  </g>\n</svg>\n`;
  }

  // ---------- document model ----------
  const state = {
    doc: null,
    sourceName: null,      // library icon this document was opened from
    nameTouched: false,
    dirty: false,
    selected: null,
    tool: 'select',
    draft: null,
    history: [],
    future: [],
    activeSlot: 'accent',
    palette: { ...DEFAULT_PALETTE, ...store.get(KEYS.palette, {}) },
    prefs: { grid: true, snap: true, brushColor: 'fg', brushFill: false, author: '', ...store.get(KEYS.prefs, {}) },
  };

  const blankDoc = () => ({ name: '', label: '', packages: [], components: [], author: state.prefs.author || '', elements: [] });
  const selected = () => state.doc.elements.find(e => e.id === state.selected) || null;
  const str = v => (typeof v === 'string' ? v : '');
  const strs = v => (Array.isArray(v) ? v.filter(x => typeof x === 'string') : []);

  function normalizeDoc(raw) {
    if (!raw || typeof raw !== 'object' || !Array.isArray(raw.elements)) throw new Error('not a glyph file (no "elements" list)');
    const doc = {
      name: str(raw.name), label: str(raw.label), packages: strs(raw.packages),
      components: strs(raw.components), author: str(raw.author), elements: [],
    };
    let skipped = 0;
    for (const e of raw.elements.slice(0, 200)) {
      try {
        if (!e || typeof e.d !== 'string') throw new Error('no path');
        const el = { id: newId(), type: TYPES.includes(e.type) ? e.type : 'stroke', color: ROLE_KEYS.includes(e.color) ? e.color : 'fg', d: e.d };
        if (el.type === 'fill' && e.soft) el.soft = true;
        if (el.type === 'knock') el.width = typeof e.width === 'number' ? clamp(e.width, 0, 8) : 5;
        else if (hasLineWidth(el) && typeof e.width === 'number') el.width = clamp(e.width, STROKE.min, STROKE.max);
        const shape = e.shape && sanitizeShape(e.shape);
        if (shape) { el.shape = shape; el.d = shapeD(shape); }  // also repairs a broken saved shape
        parsePath(el.d);
        doc.elements.push(el);
      } catch { skipped++; }
    }
    if (skipped) toast(`${skipped} unreadable shape${skipped > 1 ? 's were' : ' was'} skipped`, true);
    return doc;
  }

  function exportDoc(doc) {
    const out = { name: doc.name, label: doc.label };
    if (doc.packages.length) out.packages = doc.packages;
    if (doc.components.length) out.components = doc.components;
    if (doc.author) out.author = doc.author;
    out.elements = doc.elements.map(e => {
      const o = { type: e.type };
      if (e.type !== 'knock') o.color = e.color;
      o.d = e.d;
      if (e.type === 'fill' && e.soft) o.soft = true;
      if (e.type === 'knock') o.width = e.width ?? 5;
      else if (hasLineWidth(e) && e.width != null && e.width !== STROKE.def) o.width = e.width;
      if (e.shape) o.shape = roundShape(e.shape);
      return o;
    });
    return `${JSON.stringify(out, null, 2)}\n`;
  }

  function validateDoc(doc) {
    const errors = [], warnings = [];
    if (!NAME_RE.test(doc.name)) errors.push('Icon name: 2–41 lowercase letters, digits or _, starting with a letter.');
    else if (RESERVED.has(doc.name)) errors.push(`“${doc.name}” is a reserved name.`);
    if (!doc.label || doc.label.length > 40 || /[<>&\x00-\x1f]/.test(doc.label)) errors.push('App name: 1–40 characters, without < > &.');
    doc.packages.forEach(p => { if (!PACKAGE_RE.test(p)) errors.push(`Not a package name: ${p}`); });
    doc.components.forEach(c => { if (!COMPONENT_RE.test(c)) errors.push(`Not a launcher component: ${c}`); });
    if (doc.author.length > 60 || /[<>\x00-\x1f]/.test(doc.author)) errors.push('Author: a short plain name.');
    if (!doc.packages.length && !doc.components.length) warnings.push('No package yet: the icon won’t be applied to any app.');
    if (!doc.elements.length) errors.push('Draw at least one shape.');
    if (doc.elements.length > MAX_ELEMENTS) errors.push(`At most ${MAX_ELEMENTS} shapes per icon.`);
    let out = 0, edge = 0, bad = 0;
    for (const e of doc.elements) {
      let pts;
      try { pts = pathPoints(parsePath(e.d)); } catch { bad++; continue; }
      const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
      const lo = Math.min(...xs, ...ys), hi = Math.max(...xs, ...ys);
      if (lo < -0.5 || hi > 24.5) out++;
      else if (lo < 1 || hi > 23) edge++;
    }
    if (bad) errors.push(`${bad} shape${bad > 1 ? 's have' : ' has'} invalid path data: select it in Layers, then fix the path or delete it.`);
    if (out) errors.push(`${out} shape${out > 1 ? 's go' : ' goes'} outside the 24 × 24 grid.`);
    else if (edge) warnings.push(`${edge} shape${edge > 1 ? 's reach' : ' reaches'} the edge; keep content inside the dashed square.`);
    if (doc.elements.length && !doc.elements.some(e => e.type !== 'knock' && e.color !== 'fg')) {
      warnings.push('No colour yet: the style uses at least one accent-coloured shape.');
    }
    if (doc.name && doc.name !== state.sourceName && LIBRARY.some(g => g.name === doc.name)) {
      warnings.push(`An icon called “${doc.name}” already exists; this export will replace it.`);
    }
    for (const p of doc.packages) {
      const other = LIBRARY.find(g => g.name !== doc.name && (g.packages || []).includes(p));
      if (other) errors.push(`${p} is already mapped by ${other.label} (${other.name}).`);
    }
    return { errors, warnings };
  }

  // ---------- history & persistence ----------
  const snapshot = () => JSON.stringify({ doc: state.doc, selected: state.selected });
  function checkpoint() {
    state.history.push(snapshot());
    if (state.history.length > 150) state.history.shift();
    state.future.length = 0;
  }
  function restore(s) {
    const o = JSON.parse(s);
    state.doc = o.doc;
    state.selected = o.selected;
    markDirty();
    render();
  }
  function undo() {
    if (!state.history.length) return toast('Nothing to undo');
    state.future.push(snapshot());
    restore(state.history.pop());
  }
  function redo() {
    if (!state.future.length) return toast('Nothing to redo');
    state.history.push(snapshot());
    restore(state.future.pop());
  }
  let pendingCheckpoint = false;
  function beginEdit() {
    if (pendingCheckpoint) { checkpoint(); pendingCheckpoint = false; }
  }
  let saveTimer;
  function saveSoon() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => store.set(KEYS.doc, {
      doc: state.doc, sourceName: state.sourceName, nameTouched: state.nameTouched, dirty: state.dirty,
    }), 250);
  }
  function markDirty() { state.dirty = true; saveSoon(); }
  const savePrefs = () => store.set(KEYS.prefs, state.prefs);

  // ---------- element operations ----------
  function addElement(el) {
    if (state.doc.elements.length >= MAX_ELEMENTS) return toast(`At most ${MAX_ELEMENTS} shapes per icon`, true);
    checkpoint();
    el.id = newId();
    state.doc.elements.push(el);
    state.selected = el.id;
    markDirty();
    render();
  }
  function translated(orig, dx, dy) {
    const el = clone(orig);
    if (el.shape) {
      const s = el.shape;
      if (s.kind === 'rect') { s.x += dx; s.y += dy; } else { s.cx += dx; s.cy += dy; }
      el.shape = roundShape(s);
      el.d = shapeD(el.shape);
    } else {
      try { el.d = serializePath(translateSegs(parsePath(el.d), dx, dy)); } catch { /* unreadable path stays put */ }
    }
    return el;
  }
  function select(id) {
    state.selected = id;
    render();
  }
  function deleteSelected() {
    const els = state.doc.elements, i = els.findIndex(e => e.id === state.selected);
    if (i < 0) return;
    checkpoint();
    els.splice(i, 1);
    state.selected = els[Math.min(i, els.length - 1)]?.id ?? null;
    markDirty();
    render();
  }
  function duplicate() {
    const el = selected();
    if (!el) return;
    if (state.doc.elements.length >= MAX_ELEMENTS) return toast(`At most ${MAX_ELEMENTS} shapes per icon`, true);
    checkpoint();
    const copy = { ...translated(el, 1, 1), id: newId() };
    state.doc.elements.splice(state.doc.elements.indexOf(el) + 1, 0, copy);
    state.selected = copy.id;
    markDirty();
    render();
  }
  function moveLayer(dir) {
    const els = state.doc.elements, i = els.findIndex(e => e.id === state.selected), j = i + dir;
    if (i < 0 || j < 0 || j >= els.length) return;
    checkpoint();
    [els[i], els[j]] = [els[j], els[i]];
    markDirty();
    render();
  }
  function nudge(dx, dy) {
    const el = selected();
    if (!el) return;
    checkpoint();
    Object.assign(el, translated(el, dx, dy));
    markDirty();
    render();
  }
  function setProp(key, val) {
    const el = selected();
    if (!el || el[key] === val) return;
    checkpoint();
    const prev = el[key];
    el[key] = val;
    if (key === 'type') {
      // width means the cut-out margin for knock shapes and the line width for stroke / ring
      if (val === 'knock') el.width = 5;
      else if (val === 'fill' || prev === 'knock') delete el.width;
      if (val !== 'fill') delete el.soft;
    }
    markDirty();
    render();
  }
  function swapColor() {
    const el = selected();
    if (el && el.type !== 'knock') return setProp('color', el.color === 'accent' ? 'fg' : 'accent');
    state.prefs.brushColor = state.prefs.brushColor === 'accent' ? 'fg' : 'accent';
    savePrefs();
    syncToolbar();
  }

  // ---------- DOM ----------
  const svg = $('#canvas');
  const gGrid = $('#grid'), gContent = $('#content'), gHits = $('#hits'), gOverlay = $('#overlay'), gDraft = $('#draft');
  gContent.style.pointerEvents = 'none';
  gDraft.style.pointerEvents = 'none';

  function buildGrid() {
    let h = '';
    for (let i = 0; i <= 24; i++) {
      const cls = i === 12 ? 'center' : i % 6 === 0 ? 'major' : '';
      h += `<line x1="${i}" y1="0" x2="${i}" y2="24" class="${cls}"/><line x1="0" y1="${i}" x2="24" y2="${i}" class="${cls}"/>`;
    }
    gGrid.innerHTML = `${h}<rect class="safe" x="2" y="2" width="20" height="20" rx="0.6"/>`;
  }

  let frame = 0;
  function scheduleRender() {
    if (!frame) frame = requestAnimationFrame(() => { frame = 0; render(); });
  }

  function render() {
    renderCanvas();
    renderElementPanel();
    renderLayers();
    renderPreview();
    renderAppFields();
    renderChecks();
    $('#btn-undo').disabled = !state.history.length;
    $('#btn-redo').disabled = !state.future.length;
    $('#dirty-dot').classList.toggle('on', state.dirty && state.doc.elements.length > 0);
    $('#empty-hint').classList.toggle('hide', state.doc.elements.length > 0 || !!state.draft);
    document.title = `${state.doc.label || 'Untitled'} · Gruvbox Icon Studio`;
  }

  function renderCanvas() {
    const pal = state.palette, els = state.doc.elements;
    gContent.innerHTML = els.map(e => elementMarkup(e, pal)).join('');
    gHits.innerHTML = els.map(e => `<path class="hit${e.type === 'stroke' ? '' : ' solid'}" data-id="${e.id}" d="${esc(e.d)}"/>`).join('');
    gHits.style.pointerEvents = state.tool === 'select' ? 'auto' : 'none';
    gGrid.classList.toggle('hidden', !state.prefs.grid);
    svg.classList.toggle('tool-select', state.tool === 'select');
    svg.classList.toggle('tool-draw', state.tool !== 'select');
    renderOverlay();
    renderDraft();
  }

  function handlesFor(el) {
    if (el.shape?.kind === 'rect') {
      const { x, y, w, h } = el.shape;
      return [['nw', x, y], ['ne', x + w, y], ['se', x + w, y + h], ['sw', x, y + h]].map(([k, hx, hy]) => ({ key: `r:${k}`, x: hx, y: hy }));
    }
    if (el.shape?.kind === 'circle') return [{ key: 'c:r', x: el.shape.cx + el.shape.r, y: el.shape.cy }];
    let segs;
    try { segs = parsePath(el.d); } catch { return []; }
    const out = [];
    let px = 0, py = 0;
    segs.forEach((s, i) => {
      if (s.c === 'C') {
        out.push({ key: `${i}:1`, x: s.x1, y: s.y1, ctrl: true, from: [px, py] });
        out.push({ key: `${i}:2`, x: s.x2, y: s.y2, ctrl: true, from: [s.x, s.y] });
      }
      if (s.c === 'Q') out.push({ key: `${i}:1`, x: s.x1, y: s.y1, ctrl: true, from: [s.x, s.y] });
      if ('x' in s) { out.push({ key: `${i}:0`, x: s.x, y: s.y }); px = s.x; py = s.y; }
    });
    return out;
  }

  function renderOverlay() {
    const el = selected();
    if (!el || state.tool !== 'select') { gOverlay.innerHTML = ''; return; }
    const hs = handlesFor(el);
    gOverlay.innerHTML = `<path class="sel-outline" d="${esc(el.d)}"/>` +
      hs.filter(h => h.from).map(h => `<line class="handle-line" x1="${h.from[0]}" y1="${h.from[1]}" x2="${h.x}" y2="${h.y}"/>`).join('') +
      hs.map(h => `<circle class="handle${h.ctrl ? ' ctrl' : ''}" data-handle="${h.key}" cx="${h.x}" cy="${h.y}" r="${h.ctrl ? 0.3 : 0.38}"/>`).join('');
  }

  function draftPath(d) {
    switch (d.kind) {
      case 'line': return `M${P(...d.a)} L${P(...d.b)}`;
      case 'rect': { const r = rectFrom(d.a, d.b); return r.w > 0 && r.h > 0 ? rectD(r) : ''; }
      case 'circle': return d.r > 0 ? circleD({ cx: d.c[0], cy: d.c[1], r: d.r }) : '';
      case 'poly': {
        const pts = d.cursor ? [...d.pts, d.cursor] : d.pts;
        return pts.length > 1 ? `M${pts.map(p => P(...p)).join(' L')}` : '';
      }
      default: return '';
    }
  }
  const newType = kind => (state.prefs.brushFill && (kind === 'rect' || kind === 'circle') ? 'fill' : 'stroke');

  function renderDraft() {
    const d = state.draft;
    if (!d) { gDraft.innerHTML = ''; return; }
    const path = draftPath(d);
    let h = path ? elementMarkup({ type: newType(d.kind), color: state.prefs.brushColor, d: path }, state.palette) : '';
    if (d.kind === 'poly') {
      h += d.pts.map((p, i) => `<circle class="draft-dot" cx="${p[0]}" cy="${p[1]}" r="${i === 0 && d.pts.length > 2 ? 0.32 : 0.2}"/>`).join('');
    }
    if (d.kind === 'circle') h += `<line class="draft-guide" x1="${d.c[0]}" y1="${d.c[1]}" x2="${d.c[0] + d.r}" y2="${d.c[1]}"/>`;
    gDraft.innerHTML = h;
  }

  // ----- inspector: element -----
  const elementPanel = $('#element-panel');
  function shapeMin(kind, key) {
    if (kind === 'circle') return key === 'r' ? SHAPE_MIN.circleR : null;
    return { w: SHAPE_MIN.w, h: SHAPE_MIN.h, r: SHAPE_MIN.rectR }[key] ?? null;
  }
  const shapeMinAttr = (kind, key) => (shapeMin(kind, key) == null ? '' : ` min="${shapeMin(kind, key)}"`);
  function renderElementPanel() {
    const ae = document.activeElement;
    if (elementPanel.contains(ae) && ae.matches('input, textarea') && elementPanel.dataset.for === (state.selected || '')) return;
    elementPanel.dataset.for = state.selected || '';
    const el = selected(), pal = state.palette;
    if (!el) {
      elementPanel.innerHTML = '<p class="placeholder">Select a shape on the canvas or in Layers.</p>' +
        '<div class="add-row"><button class="btn" data-act="add-path" title="Add a path you can type or paste">+ Path from text</button></div>';
      return;
    }
    const shape = el.shape
      ? `<div class="num-grid">${(el.shape.kind === 'rect'
        ? [['x', 'X'], ['y', 'Y'], ['w', 'Width'], ['h', 'Height'], ['r', 'Radius']]
        : [['cx', 'Centre X'], ['cy', 'Centre Y'], ['r', 'Radius']])
        .map(([k, l]) => `<label>${l}<input class="field mono" type="number" step="0.5" data-shape="${k}"${shapeMinAttr(el.shape.kind, k)} value="${fmt(el.shape[k])}"></label>`).join('')}</div>`
      : '';
    elementPanel.innerHTML = `
      <div class="seg" data-seg="type">${TYPES.map(t => `<button data-val="${t}" class="${el.type === t ? 'on' : ''}" title="${{
        stroke: '2-unit line', fill: 'Solid shape', ring: 'Outline filled with the tile colour', knock: 'Tile-coloured cut-out that separates shapes',
      }[t]}">${TYPE_LABEL[t]}</button>`).join('')}</div>
      ${el.type !== 'knock' ? `<div class="row">Colour <span class="val">${ROLE_NAME[el.color] || 'Cream'}</span>
        <div class="colors">${ROLES.map(r => `<button data-color-role="${r.key}" class="${el.color === r.key ? 'on' : ''}"
          style="--c:${pal[r.key]}" title="${r.name}" aria-label="${r.name}"></button>`).join('')}</div></div>` : ''}
      ${hasLineWidth(el) ? `<label class="row">Line width <span class="val" data-val-for="stroke-width">${fmt(el.width ?? STROKE.def)}</span>
        <input type="range" min="${STROKE.min}" max="${STROKE.max}" step="0.25" data-prop="stroke-width" value="${el.width ?? STROKE.def}"></label>` : ''}
      ${el.type === 'fill' ? `<div class="toggle-row">Soft edges<label class="switch"><input type="checkbox" data-prop="soft"${el.soft ? ' checked' : ''}><span></span></label></div>` : ''}
      ${el.type === 'knock' ? `<label class="row">Cut-out margin <input type="range" min="0" max="8" step="0.5" data-prop="width" value="${el.width ?? 5}"></label>` : ''}
      ${shape}
      <label class="row">Path data <textarea class="field d-field" data-prop="d" rows="3" spellcheck="false">${esc(el.d)}</textarea></label>
      <div class="el-actions">
        <button class="btn" data-act="dup" title="Duplicate (Ctrl+D)">Copy</button>
        <button class="btn" data-act="down" title="Move down a layer ([)">Down</button>
        <button class="btn" data-act="up" title="Move up a layer (])">Up</button>
        <button class="btn btn-danger" data-act="del" title="Delete (Del)">Delete</button>
      </div>`;
  }

  // ----- inspector: layers -----
  const layerList = $('#layers');
  function renderLayers() {
    const els = state.doc.elements, pal = state.palette;
    $('#layer-count').textContent = els.length ? `${els.length}/${MAX_ELEMENTS}` : '';
    layerList.innerHTML = els.map((e, i) => ({ e, i })).reverse().map(({ e, i }) => `
      <li class="layer${e.id === state.selected ? ' on' : ''}" draggable="true" data-id="${e.id}">
        <span class="n">${i + 1}</span>
        <svg viewBox="-1 -1 26 26"><g fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${elementMarkup(e, pal)}</g></svg>
        <span>${TYPE_LABEL[e.type]}${e.type !== 'knock' && e.color !== 'fg' ? ` · ${(ROLE_NAME[e.color] || '').toLowerCase()}` : ''}${e.shape ? ` · ${e.shape.kind}` : ''}</span>
        <span class="grip" aria-hidden="true">⋮⋮</span>
      </li>`).join('') || '<li class="placeholder">No shapes yet.</li>';
  }

  // ----- inspector: preview -----
  function renderPreview() {
    const pal = state.palette, els = state.doc.elements;
    const neighbours = ['phone', 'messages', 'camera'].map(n => LIBRARY.find(g => g.name === n)).filter(Boolean);
    const me = { label: state.doc.label || 'New icon', elements: els, me: true };
    $('#preview').innerHTML = `
      <div class="pv-hero">${iconSVG(els, pal, 140)}</div>
      <div class="pv-dock">${[...neighbours, me].map(g => `<figure class="${g.me ? 'me' : ''}">${iconSVG(g.elements, pal, 48)}<figcaption>${esc(g.label)}</figcaption></figure>`).join('')}</div>
      <div class="pv-sizes">${[48, 32, 24].map(s => `<figure>${iconSVG(els, pal, s)}${s} px</figure>`).join('')}</div>`;
  }

  // ----- inspector: app mapping and checks -----
  function setVal(sel, v) {
    const el = $(sel);
    if (document.activeElement !== el && el.value !== v) el.value = v;
  }
  function renderAppFields() {
    const d = state.doc;
    setVal('#f-label', d.label);
    setVal('#f-name', d.name);
    setVal('#f-packages', d.packages.join('\n'));
    setVal('#f-components', d.components.join('\n'));
    setVal('#f-author', d.author);
  }
  let lastChecks = '';
  function renderChecks() {
    const { errors, warnings } = validateDoc(state.doc);
    const html = [...errors.map(m => `<li class="err">${esc(m)}</li>`), ...warnings.map(m => `<li class="warn">${esc(m)}</li>`)].join('') ||
      '<li class="ok">Ready to export.</li>';
    if (html !== lastChecks) { $('#checks').innerHTML = html; lastChecks = html; }
    const chip = $('#st-valid');
    chip.className = `chip ${errors.length ? 'err' : warnings.length ? 'warn' : 'ok'}`;
    chip.innerHTML = `<span class="dot"></span>${errors.length ? `${errors.length} to fix` : warnings.length ? `${warnings.length} warning${warnings.length > 1 ? 's' : ''}` : 'Ready to export'}`;
  }

  // ----- palette -----
  function applyPaletteVars() {
    const s = document.documentElement.style;
    Object.keys(DEFAULT_PALETTE).forEach(key => s.setProperty(`--pal-${key}`, state.palette[key]));
  }
  const samePal = p => Object.keys(DEFAULT_PALETTE).every(key => (p[key] || '').toLowerCase() === state.palette[key].toLowerCase());
  const EXTRA_ROLES = ROLES.filter(r => r.key !== 'fg' && r.key !== 'accent');
  function renderPalette() {
    $('#presets').innerHTML = PRESETS.map(p => `<button class="preset${samePal(p.pal) ? ' on' : ''}" data-preset="${p.id}">
      <i>${['tile', 'fg', 'accent'].map(k => `<b style="background:${p.pal[k]}"></b>`).join('')}</i>${p.label}</button>`).join('');
    const slots = $('#slots');
    if (!slots.contains(document.activeElement)) {
      slots.innerHTML = SLOTS.map(s => `<div class="slot${state.activeSlot === s.key ? ' on' : ''}" data-slot="${s.key}">
        <span class="sw" style="background:${state.palette[s.key]}"><input type="color" value="${state.palette[s.key]}" data-color="${s.key}" aria-label="${s.name} colour"></span>
        <span class="name">${s.name}<small>${s.hint}</small></span>
        <input class="field hex" value="${state.palette[s.key]}" data-hex="${s.key}" maxlength="7" spellcheck="false" aria-label="${s.name} hex">
      </div>`).join('');
    } else {
      slots.querySelectorAll('.slot').forEach(row => {
        const k = row.dataset.slot;
        row.classList.toggle('on', state.activeSlot === k);
        row.querySelector('.sw').style.background = state.palette[k];
        const hex = row.querySelector('.hex'), col = row.querySelector('[data-color]');
        if (document.activeElement !== hex) hex.value = state.palette[k];
        if (document.activeElement !== col) col.value = state.palette[k];
      });
    }
    const extra = $('#extra-slots');
    if (!extra.contains(document.activeElement)) {
      extra.innerHTML = EXTRA_ROLES.map(r => `<div class="xslot${state.activeSlot === r.key ? ' on' : ''}" data-slot="${r.key}">
        <span class="sw" style="background:${state.palette[r.key]}"><input type="color" value="${state.palette[r.key]}" data-color="${r.key}" aria-label="${r.name} colour"></span>
        <span>${r.name}</span></div>`).join('');
    }
    const seen = new Set();
    $('#gruvbox-swatches').innerHTML = Object.entries(G)
      .filter(([k, v]) => k !== 'accent' && !seen.has(v) && seen.add(v))
      .map(([k, v]) => `<button style="background:${v}" data-gv="${v}" title="${k} ${v}" aria-label="${k} ${v}"></button>`).join('');
  }
  let libTimer;
  function setPalette(patch) {
    state.palette = { ...state.palette, ...patch };
    store.set(KEYS.palette, state.palette);
    applyPaletteVars();
    renderPalette();
    render();
    thumbCache.clear();
    clearTimeout(libTimer);
    libTimer = setTimeout(renderLibrary, 120);
  }

  // ----- library -----
  const thumbCache = new Map();
  const thumb = g => {
    if (!thumbCache.has(g.name)) thumbCache.set(g.name, iconSVG(g.elements, state.palette, 48, ' aria-hidden="true"'));
    return thumbCache.get(g.name);
  };
  function renderLibrary() {
    const q = $('#lib-search').value.trim().toLowerCase();
    const items = LIBRARY.filter(g => !q || g.label.toLowerCase().includes(q) || g.name.includes(q) ||
      (g.packages || []).some(p => p.toLowerCase().includes(q)));
    $('#lib-count').textContent = q ? `${items.length} of ${LIBRARY.length}` : `${LIBRARY.length}`;
    $('#lib-grid').innerHTML = items.map((g, i) => `
      <button class="lib-item${g.name === state.sourceName ? ' current' : ''}" data-lib="${g.name}" title="${esc(g.label)} · ${g.name}"
        style="animation-delay:${Math.min(i, 30) * 8}ms">${thumb(g)}<span>${esc(g.label)}</span></button>`).join('') ||
      `<p class="lib-empty">No icons match “${esc(q)}”.</p>`;
  }

  // ---------- tools & toolbar ----------
  function setTool(t) {
    if (state.draft && t !== state.tool) state.draft = null;
    state.tool = t;
    document.querySelectorAll('.tool[data-tool]').forEach(b => b.classList.toggle('active', b.dataset.tool === t));
    $('#st-hint').textContent = HINTS[t];
    render();
  }
  function syncToolbar() {
    if (!ROLE_KEYS.includes(state.prefs.brushColor)) state.prefs.brushColor = 'fg';
    const extra = !['fg', 'accent'].includes(state.prefs.brushColor);
    document.querySelectorAll('[data-brush]').forEach(b => b.classList.toggle('active', b.dataset.brush === state.prefs.brushColor));
    const more = $('#brush-more');
    more.classList.toggle('active', extra);
    more.style.background = extra ? `var(--pal-${state.prefs.brushColor})` : '';
    more.title = extra ? `New shapes: ${ROLE_NAME[state.prefs.brushColor]} (click for more colours)` : 'More colours';
    $('#brush-pop').innerHTML = ROLES.map(r => `<button data-pick="${r.key}" class="${r.key === state.prefs.brushColor ? 'on' : ''}"
      style="--c:var(--pal-${r.key})" title="${r.name}" aria-label="${r.name}"></button>`).join('');
    $('#brush-fill').classList.toggle('active', state.prefs.brushFill);
    $('#t-grid').classList.toggle('active', state.prefs.grid);
    $('#t-snap').classList.toggle('active', state.prefs.snap);
  }
  function togglePref(key, label) {
    state.prefs[key] = !state.prefs[key];
    savePrefs();
    syncToolbar();
    render();
    toast(`${label} ${state.prefs[key] ? 'on' : 'off'}`);
  }

  // ---------- canvas interaction ----------
  let drag = null;
  const svgPoint = e => {
    const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(svg.getScreenCTM().inverse());
    return [p.x, p.y];
  };
  const snaps = e => state.prefs.snap && !(e && e.altKey);
  const snapV = (v, e) => (snaps(e) ? Math.round(v * 2) / 2 : Math.round(v * 100) / 100);
  const snapPt = (p, e) => [clamp(snapV(p[0], e), 0, 24), clamp(snapV(p[1], e), 0, 24)];
  function updatePos(p) {
    $('#st-pos').textContent = p ? `x ${fmt(snapV(p[0]))}  y ${fmt(snapV(p[1]))}` : 'x –  y –';
  }

  svg.addEventListener('pointerdown', e => {
    if (e.button !== 0) return;
    const p = svgPoint(e), sp = snapPt(p, e);
    const handle = e.target.closest('[data-handle]'), hit = e.target.closest('[data-id]');
    if (state.tool === 'select') {
      if (handle) drag = { kind: 'handle', key: handle.dataset.handle, orig: clone(selected()), moved: false };
      else if (hit) {
        state.selected = hit.dataset.id;
        drag = { kind: 'move', start: p, orig: clone(selected()), moved: false };
      } else state.selected = null;
    } else if (state.tool === 'poly') {
      polyClick(sp);
    } else {
      state.draft = state.tool === 'circle' ? { kind: 'circle', c: sp, r: 0 } : { kind: state.tool, a: sp, b: sp };
      drag = { kind: 'draw' };
    }
    if (drag) svg.setPointerCapture(e.pointerId);
    render();
  });

  svg.addEventListener('pointermove', e => {
    const p = svgPoint(e);
    updatePos(p);
    if (state.tool === 'poly' && state.draft) {
      state.draft.cursor = snapPt(p, e);
      renderDraft();
      return;
    }
    if (!drag) return;
    if (drag.kind === 'draw') {
      const d = state.draft, sp = snapPt(p, e);
      if (d.kind === 'circle') d.r = snapV(Math.hypot(sp[0] - d.c[0], sp[1] - d.c[1]), e);
      else d.b = sp;
      renderDraft();
    } else if (drag.kind === 'move') {
      let dx = p[0] - drag.start[0], dy = p[1] - drag.start[1];
      dx = snapV(dx, e); dy = snapV(dy, e);
      if (!drag.moved) {
        if (!dx && !dy) return;
        checkpoint();
        drag.moved = true;
      }
      Object.assign(selected(), translated(drag.orig, dx, dy));
      markDirty();
      scheduleRender();
    } else if (drag.kind === 'handle') {
      handleDrag(snapPt(p, e), e);
    }
  });

  function handleDrag(sp, e) {
    if (!drag.moved) { checkpoint(); drag.moved = true; }
    const el = selected(), o = drag.orig;
    const [kind, part] = drag.key.split(':');
    if (kind === 'r') {
      const s = o.shape;
      let x0 = s.x, y0 = s.y, x1 = s.x + s.w, y1 = s.y + s.h;
      if (part.includes('w')) x0 = sp[0];
      if (part.includes('e')) x1 = sp[0];
      if (part.includes('n')) y0 = sp[1];
      if (part.includes('s')) y1 = sp[1];
      el.shape = roundShape({ kind: 'rect', x: Math.min(x0, x1), y: Math.min(y0, y1), w: Math.abs(x1 - x0), h: Math.abs(y1 - y0), r: s.r });
      el.d = shapeD(el.shape);
    } else if (kind === 'c') {
      const s = o.shape;
      el.shape = roundShape({ ...s, r: Math.max(0.5, snapV(Math.hypot(sp[0] - s.cx, sp[1] - s.cy), e)) });
      el.d = shapeD(el.shape);
    } else {
      const segs = parsePath(o.d), s = segs[+kind];
      const [kx, ky] = XY[+part];
      s[kx] = sp[0];
      s[ky] = sp[1];
      el.d = serializePath(segs);
      delete el.shape;
    }
    markDirty();
    scheduleRender();
  }

  svg.addEventListener('pointerup', () => {
    if (!drag) return;
    if (drag.kind === 'draw') finishDraw();
    drag = null;
    render();
  });
  svg.addEventListener('pointerleave', () => updatePos(null));
  svg.addEventListener('dblclick', () => { if (state.tool === 'poly') finishPoly(false); });

  function polyClick(sp) {
    const d = state.draft;
    if (!d) { state.draft = { kind: 'poly', pts: [sp], cursor: sp }; return; }
    const first = d.pts[0], last = d.pts[d.pts.length - 1];
    if (d.pts.length >= 3 && Math.hypot(sp[0] - first[0], sp[1] - first[1]) < 0.6) { finishPoly(true); return; }
    if (last[0] === sp[0] && last[1] === sp[1]) return;
    d.pts.push(sp);
  }
  function finishPoly(closed) {
    const d = state.draft;
    if (!d || d.kind !== 'poly') return;
    state.draft = null;
    const pts = d.pts.filter((p, i, a) => i === 0 || p[0] !== a[i - 1][0] || p[1] !== a[i - 1][1]);
    if (pts.length < 2) { render(); return; }
    addElement({
      type: closed && state.prefs.brushFill ? 'fill' : 'stroke',
      color: state.prefs.brushColor,
      d: `M${pts.map(p => P(...p)).join(' L')}${closed ? ' Z' : ''}`,
    });
  }
  function finishDraw() {
    const d = state.draft, color = state.prefs.brushColor;
    state.draft = null;
    if (d.kind === 'line') {
      if (d.a[0] === d.b[0] && d.a[1] === d.b[1]) return;
      addElement({ type: 'stroke', color, d: `M${P(...d.a)} L${P(...d.b)}` });
    } else if (d.kind === 'rect') {
      const r = rectFrom(d.a, d.b);
      if (r.w < 0.5 || r.h < 0.5) return;
      const shape = roundShape(r);
      addElement({ type: newType('rect'), color, d: rectD(shape), shape });
    } else if (d.kind === 'circle') {
      if (d.r < 0.5) return;
      const shape = roundShape({ kind: 'circle', cx: d.c[0], cy: d.c[1], r: d.r });
      addElement({ type: newType('circle'), color, d: circleD(shape), shape });
    }
  }

  // ---------- inspector events ----------
  document.addEventListener('focusin', e => {
    if (e.target.matches('#inspector input, #inspector textarea, #f-label')) pendingCheckpoint = true;
  });

  elementPanel.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    if (b.dataset.colorRole) return setProp('color', b.dataset.colorRole);
    const seg = b.closest('[data-seg]');
    if (seg) return setProp(seg.dataset.seg, b.dataset.val);
    ({
      dup: duplicate,
      up: () => moveLayer(1),
      down: () => moveLayer(-1),
      del: deleteSelected,
      'add-path': () => { setTool('select'); addElement({ type: 'stroke', color: state.prefs.brushColor, d: 'M6 12 H18' }); toast('Edit the path data below'); },
    })[b.dataset.act]?.();
  });

  elementPanel.addEventListener('input', e => {
    const el = selected(), t = e.target;
    if (!el) return;
    if (t.dataset.prop === 'd') {
      const v = t.value.trim();
      try {
        if (!v) throw new Error('empty path');
        parsePath(v);
      } catch (err) {
        t.classList.add('bad');
        t.title = err.message;
        return;
      }
      t.classList.remove('bad');
      t.title = '';
      beginEdit();
      el.d = v;
      delete el.shape;
    } else if (t.dataset.prop === 'width') {
      beginEdit();
      el.width = parseFloat(t.value);
    } else if (t.dataset.prop === 'stroke-width') {
      beginEdit();
      const w = clamp(parseFloat(t.value), STROKE.min, STROKE.max);
      if (w === STROKE.def) delete el.width; else el.width = w;
      const label = elementPanel.querySelector('[data-val-for="stroke-width"]');
      if (label) label.textContent = fmt(w);
    } else if (t.dataset.prop === 'soft') {
      checkpoint();
      if (t.checked) el.soft = true; else delete el.soft;
    } else if (t.dataset.shape) {
      const k = t.dataset.shape, min = shapeMin(el.shape.kind, k);
      let v = parseFloat(t.value);
      if (!Number.isFinite(v)) return;
      if (min != null && v < min) { v = min; t.value = fmt(min); }
      beginEdit();
      el.shape[k] = v;
      el.shape = roundShape(el.shape);
      el.d = shapeD(el.shape);
    } else return;
    markDirty();
    scheduleRender();
  });
  elementPanel.addEventListener('focusout', () => setTimeout(() => {
    if (!elementPanel.contains(document.activeElement)) renderElementPanel();
  }));

  layerList.addEventListener('click', e => {
    const li = e.target.closest('.layer[data-id]');
    if (!li) return;
    if (state.tool !== 'select') setTool('select');
    select(li.dataset.id);
  });
  let dragLayer = null, dropTarget = null;
  const clearDrop = () => layerList.querySelectorAll('.drop-above, .drop-below').forEach(n => n.classList.remove('drop-above', 'drop-below'));
  layerList.addEventListener('dragstart', e => {
    const li = e.target.closest('.layer[data-id]');
    if (!li) return;
    dragLayer = li.dataset.id;
    li.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', dragLayer);
  });
  layerList.addEventListener('dragover', e => {
    if (!dragLayer) return;
    e.preventDefault();
    clearDrop();
    const li = e.target.closest('.layer[data-id]');
    if (!li || li.dataset.id === dragLayer) { dropTarget = null; return; }
    const r = li.getBoundingClientRect(), above = e.clientY < r.top + r.height / 2;
    li.classList.add(above ? 'drop-above' : 'drop-below');
    dropTarget = { id: li.dataset.id, above };
  });
  layerList.addEventListener('drop', e => {
    e.preventDefault();
    if (!dragLayer || !dropTarget) return;
    const els = state.doc.elements;
    checkpoint();
    const [el] = els.splice(els.findIndex(x => x.id === dragLayer), 1);
    const to = els.findIndex(x => x.id === dropTarget.id);
    els.splice(dropTarget.above ? to + 1 : to, 0, el);  // the list shows the top layer first
    markDirty();
  });
  layerList.addEventListener('dragend', () => { clearDrop(); dragLayer = dropTarget = null; render(); });

  // app mapping fields
  $('#f-label').addEventListener('input', e => {
    beginEdit();
    state.doc.label = e.target.value;
    if (!state.nameTouched) state.doc.name = slug(e.target.value);
    markDirty();
    scheduleRender();
  });
  $('#f-name').addEventListener('input', e => {
    beginEdit();
    state.doc.name = e.target.value.trim();
    state.nameTouched = state.doc.name !== '';
    markDirty();
    scheduleRender();
  });
  $('#f-packages').addEventListener('input', e => { beginEdit(); state.doc.packages = lines(e.target.value); markDirty(); scheduleRender(); });
  $('#f-components').addEventListener('input', e => { beginEdit(); state.doc.components = lines(e.target.value); markDirty(); scheduleRender(); });
  $('#f-author').addEventListener('input', e => {
    beginEdit();
    state.doc.author = e.target.value.trim();
    state.prefs.author = state.doc.author;
    savePrefs();
    markDirty();
    scheduleRender();
  });

  // palette events
  $('#card-palette').addEventListener('click', e => {
    const preset = e.target.closest('[data-preset]');
    if (preset) return setPalette(PRESETS.find(p => p.id === preset.dataset.preset).pal);
    const gv = e.target.closest('[data-gv]');
    if (gv) return setPalette({ [state.activeSlot]: gv.dataset.gv });
    const slot = e.target.closest('[data-slot]');
    if (slot && state.activeSlot !== slot.dataset.slot) { state.activeSlot = slot.dataset.slot; renderPalette(); }
  });
  $('#card-palette').addEventListener('input', e => {
    const t = e.target;
    if (t.dataset.color) { state.activeSlot = t.dataset.color; setPalette({ [t.dataset.color]: t.value }); }
    if (t.dataset.hex) {
      const v = t.value.trim().toLowerCase();
      const hex = /^#?[0-9a-f]{6}$/.test(v) ? (v.startsWith('#') ? v : `#${v}`) : null;
      t.classList.toggle('bad', !hex);
      if (hex) { state.activeSlot = t.dataset.hex; setPalette({ [t.dataset.hex]: hex }); }
    }
  });
  $('#pal-reset').addEventListener('click', () => { setPalette(DEFAULT_PALETTE); toast('Palette reset to Gruvbox'); });

  // library
  let searchTimer;
  $('#lib-search').addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(renderLibrary, 80); });
  $('#lib-grid').addEventListener('click', e => {
    const b = e.target.closest('[data-lib]');
    if (b) openFromLibrary(b.dataset.lib);
  });

  // ---------- documents ----------
  function loadDoc(doc, sourceName = null) {
    Object.assign(state, {
      doc, sourceName, selected: null, history: [], future: [], draft: null, dirty: false, nameTouched: !!doc.name,
    });
    setTool('select');
    renderLibrary();
    saveSoon();
  }
  const isDirty = () => state.dirty && state.doc.elements.length > 0;
  async function openFromLibrary(name) {
    if (name === state.sourceName && !isDirty()) return;
    if (isDirty() && !(await confirmBox(`Discard unsaved changes to “${state.doc.label || 'this icon'}”?`))) return;
    const g = LIBRARY.find(x => x.name === name);
    loadDoc(normalizeDoc(clone(g)), name);
    toast(`Editing ${g.label}`);
  }
  async function newDoc() {
    if (isDirty() && !(await confirmBox('Start a new icon and discard the unsaved changes?', 'Discard'))) return;
    loadDoc(blankDoc());
    $('#f-label').focus();
  }
  $('#btn-new').addEventListener('click', newDoc);
  $('#btn-open').addEventListener('click', () => $('#file-open').click());
  $('#file-open').addEventListener('change', async e => {
    const file = e.target.files[0];
    e.target.value = '';
    if (!file) return;
    if (file.size > 64 * 1024) return toast('That file is too big to be a glyph', true);
    try {
      const doc = normalizeDoc(JSON.parse(await file.text()));
      if (isDirty() && !(await confirmBox('Open this file and discard the unsaved changes?', 'Open'))) return;
      loadDoc(doc, LIBRARY.some(g => g.name === doc.name) ? doc.name : null);
      toast(`Opened ${file.name}`);
    } catch (err) {
      toast(`Couldn’t open ${file.name}: ${err.message}`, true);
    }
  });

  // ---------- export ----------
  const menu = $('#btn-export').parentElement;
  const closeMenu = () => { menu.classList.remove('open'); $('#btn-export').setAttribute('aria-expanded', 'false'); };
  $('#btn-export').addEventListener('click', e => {
    e.stopPropagation();
    const open = !menu.classList.contains('open');
    menu.classList.toggle('open', open);
    $('#btn-export').setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('click', e => { if (!menu.contains(e.target)) closeMenu(); });
  $('#export-menu').addEventListener('click', e => {
    const b = e.target.closest('[data-export]');
    if (b) doExport(b.dataset.export);
  });

  function download(name, blob) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  }
  function renderPNG(elements, size) {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(new Blob([iconSVG(elements, state.palette, size)], { type: 'image/svg+xml' }));
      const img = new Image();
      img.onload = () => {
        const c = document.createElement('canvas');
        c.width = c.height = size;
        c.getContext('2d').drawImage(img, 0, 0, size, size);
        URL.revokeObjectURL(url);
        c.toBlob(b => (b ? resolve(b) : reject(new Error('encode failed'))), 'image/png');
      };
      img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('render failed')); };
      img.src = url;
    });
  }
  function flash(sel) {
    const el = $(sel);
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.classList.remove('flash');
    void el.offsetWidth;
    el.classList.add('flash');
  }
  function doExport(kind) {
    closeMenu();
    const doc = state.doc;
    if (kind === 'json' || kind === 'copy') {
      const { errors } = validateDoc(doc);
      if (errors.length) {
        toast(`Fix ${errors.length} issue${errors.length > 1 ? 's' : ''} under App mapping first`, true);
        flash('#card-app');
        return;
      }
      const json = exportDoc(doc);
      if (kind === 'copy') {
        navigator.clipboard?.writeText(json).then(() => toast('Glyph JSON copied'), () => toast('Copy failed', true));
        return;
      }
      download(`${doc.name}.json`, new Blob([json], { type: 'application/json' }));
      state.dirty = false;
      saveSoon();
      render();
      toast(`Saved ${doc.name}.json. Put it in glyphs/ and push.`);
      return;
    }
    if (!doc.elements.length) return toast('Draw something first', true);
    const base = doc.name || 'icon';
    if (kind === 'svg') {
      download(`${base}.svg`, new Blob([iconSVG(doc.elements, state.palette, 192)], { type: 'image/svg+xml' }));
      return;
    }
    const size = kind === 'png512' ? 512 : 192;
    renderPNG(doc.elements, size).then(b => download(`${base}_${size}.png`, b)).catch(err => toast(`PNG export failed: ${err.message}`, true));
  }

  // ---------- toolbar & top bar events ----------
  document.querySelectorAll('.tool[data-tool]').forEach(b => b.addEventListener('click', () => setTool(b.dataset.tool)));
  function setBrush(role) {
    state.prefs.brushColor = role;
    savePrefs();
    syncToolbar();
  }
  document.querySelectorAll('[data-brush]').forEach(b => b.addEventListener('click', () => setBrush(b.dataset.brush)));
  const brushPop = $('#brush-pop');
  $('#brush-more').addEventListener('click', e => {
    e.stopPropagation();
    brushPop.hidden = !brushPop.hidden;
  });
  brushPop.addEventListener('click', e => {
    const b = e.target.closest('[data-pick]');
    if (!b) return;
    setBrush(b.dataset.pick);
    brushPop.hidden = true;
  });
  document.addEventListener('click', e => { if (!brushPop.hidden && !brushPop.contains(e.target)) brushPop.hidden = true; });
  $('#brush-fill').addEventListener('click', () => togglePref('brushFill', 'Fill new shapes'));
  $('#t-grid').addEventListener('click', () => togglePref('grid', 'Grid'));
  $('#t-snap').addEventListener('click', () => togglePref('snap', 'Snapping'));
  $('#btn-undo').addEventListener('click', undo);
  $('#btn-redo').addEventListener('click', redo);
  $('#btn-help').addEventListener('click', () => $('#help').showModal());
  // On the hosted site docs/ sits next to the Studio; opened from disk, use the hosted docs
  if (location.protocol === 'file:') $('#btn-docs').href = 'https://sabarinathan1611.github.io/gruvbox-mobile-icons/docs/';
  $('#st-valid').addEventListener('click', () => flash('#card-app'));

  // ---------- keyboard ----------
  document.addEventListener('keydown', e => {
    const typing = e.target.matches('input, textarea, select, [contenteditable]');
    const mod = e.ctrlKey || e.metaKey;
    const k = e.key.toLowerCase();
    if (mod && k === 'e') { e.preventDefault(); doExport('json'); return; }
    if (typing) { if (e.key === 'Escape') e.target.blur(); return; }
    if (mod && k === 'z') { e.preventDefault(); if (e.shiftKey) redo(); else undo(); return; }
    if (mod && k === 'y') { e.preventDefault(); redo(); return; }
    if (mod && k === 'd') { e.preventDefault(); duplicate(); return; }
    if (mod || e.altKey) return;
    const step = (state.prefs.snap ? 0.5 : 0.1) * (e.shiftKey ? 4 : 1);
    switch (e.key) {
      case 'v': case 'V': setTool('select'); break;
      case 'l': case 'L': setTool('line'); break;
      case 'p': case 'P': setTool('poly'); break;
      case 'r': case 'R': setTool('rect'); break;
      case 'c': case 'C': setTool('circle'); break;
      case 'g': case 'G': togglePref('grid', 'Grid'); break;
      case 's': case 'S': togglePref('snap', 'Snapping'); break;
      case 'f': case 'F': togglePref('brushFill', 'Fill new shapes'); break;
      case 'x': case 'X': swapColor(); break;
      case 'n': case 'N': newDoc(); break;
      case '?': $('#help').showModal(); break;
      case '[': moveLayer(-1); break;
      case ']': moveLayer(1); break;
      case 'Enter': if (state.draft?.kind === 'poly') finishPoly(false); break;
      case 'Escape':
        if (state.draft) { state.draft = null; render(); } else if (menu.classList.contains('open')) closeMenu(); else select(null);
        break;
      case 'Backspace':
      case 'Delete':
        e.preventDefault();
        if (state.draft?.kind === 'poly' && e.key === 'Backspace') {
          state.draft.pts.pop();
          if (!state.draft.pts.length) state.draft = null;
          render();
        } else deleteSelected();
        break;
      case 'ArrowLeft': e.preventDefault(); nudge(-step, 0); break;
      case 'ArrowRight': e.preventDefault(); nudge(step, 0); break;
      case 'ArrowUp': e.preventDefault(); nudge(0, -step); break;
      case 'ArrowDown': e.preventDefault(); nudge(0, step); break;
      default:
    }
  });

  // ---------- feedback ----------
  let toastTimer;
  function toast(msg, err = false) {
    const t = $('#toast');
    t.textContent = msg;
    t.classList.toggle('err', err);
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), err ? 4000 : 2400);
  }
  function confirmBox(msg, ok = 'Discard') {
    return new Promise(resolve => {
      const dlg = $('#confirm');
      $('#confirm-msg').textContent = msg;
      $('#confirm-ok').textContent = ok;
      dlg.returnValue = '';
      dlg.addEventListener('close', () => resolve(dlg.returnValue === 'ok'), { once: true });
      dlg.showModal();
    });
  }

  // ---------- start ----------
  function init() {
    buildGrid();
    const saved = store.get(KEYS.doc, null);
    state.doc = blankDoc();
    if (saved && saved.doc) {
      try {
        state.doc = normalizeDoc(saved.doc);
        state.sourceName = saved.sourceName || null;
        state.nameTouched = !!saved.nameTouched;
        state.dirty = !!saved.dirty;
      } catch { state.doc = blankDoc(); }
    }
    applyPaletteVars();
    syncToolbar();
    renderPalette();
    renderLibrary();
    setTool('select');
    if (!LIBRARY.length) toast('Icon library not found: run scripts/make_icons.py to create editor/library.js', true);
  }
  init();
})();
