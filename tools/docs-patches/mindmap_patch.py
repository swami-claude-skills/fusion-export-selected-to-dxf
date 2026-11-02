import sys, re
"""mindmap_patch.py PAGE.html — add (or refresh) the vibe-dashboard Mind Map section. Idempotent.
First run: inserts the section just before Glossary (else References, else the verbatim section, else at the end of
main), numbers it and renumbers the sections after it, adds its row to the section 01 summary table, adds the CSS and
script, keeps page search out of the map and keeps the Glossary from counting terms in it. Later runs replace the CSS,
the section body and the script with this version, leaving the section's number and position alone."""
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
CSS = r'''  /* ---- mind map (NotebookLM style) ---- */
  .mm-bar{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 2px;padding:8px 0;position:sticky;top:calc(var(--stack-h,0px) + var(--sechead-h,0px));z-index:15;background:var(--panel)}   /* pins under the section header while you scroll the map */
  .mm-wrap{position:relative;overflow:hidden;background:var(--panel);border:1px solid var(--border);border-radius:10px;height:max(300px,calc(100vh - var(--stack-h,0px) - var(--sechead-h,0px) - var(--mmbar-h,48px) - 28px))}
  .mm-wrap svg{display:block;width:100%;height:100%;cursor:grab;touch-action:none;user-select:none;-webkit-user-select:none}
  .mm-wrap.panning svg,.mm-wrap.panning .mm-node{cursor:grabbing}
  .mm-wrap.region svg,.mm-wrap.region .mm-node{cursor:crosshair}
  .mm-rect{position:absolute;border:1.5px dashed var(--cyan);background:rgba(0,229,255,.08);border-radius:3px;pointer-events:none;display:none}
  .mm-ctl-tip .gj-foot.keys{color:var(--cyan)}
  .mm-tipnote{color:rgba(0,255,136,.55)}   /* faint green */
  .mm-zoom[data-tip]{cursor:help}
  .tool-btn.mm-on{color:var(--cyan);border-color:var(--cyan);background:rgba(0,229,255,.10)}
  .mm-bar .mm-sep{width:1px;align-self:stretch;background:var(--border);margin:0 4px}
  .mm-zoom{font-family:var(--mono);font-size:12px;color:var(--text-dim);align-self:center;min-width:44px;text-align:center;font-variant-numeric:tabular-nums}
  .mm-node{cursor:pointer}
  .mm-node rect.box{stroke-width:1.2;transition:filter .15s}
  .mm-node:hover rect.box{filter:brightness(1.35)}
  .mm-node text{font-family:var(--sans);font-size:13px;fill:var(--text);dominant-baseline:central;pointer-events:none}
  .mm-node.root text{font-weight:700;font-size:14px}
  .mm-node .chev circle{fill:var(--panel-2);stroke-width:1.2}
  .mm-node .chev text{font-family:var(--mono);font-size:12px;text-anchor:middle}
  .mm-edge{fill:none;stroke-width:1.6;opacity:.55}
  .mm-hint{font-family:var(--mono);font-size:11px;color:var(--text-mute);margin:6px 0 4px}
  .mm-tip .mm-tip-hint{margin-top:4px;color:var(--gj)}
  .mm-node.linked{cursor:pointer}
  .mm-node.linked:hover rect.box{filter:brightness(1.35)}'''
BODY = r'''      <p>Everything on this page as one map, built from its sections, lists, tables, and callouts. <span class="mm-tipnote">HOVER OVER CONTROL FOR TOOLTIP.</span> Click a bubble's › arrow to open or close its branch, and click a bubble's name to jump to that spot on the page. Hover any bubble for a short summary. The map opens fitted to its frame. Drag to pan; zoom with the − / + buttons, Ctrl/⌘ + scroll, or a pinch. Double-click empty space to fit the whole map again, Shift + click a bubble (or the space near one) to zoom to all the items in that branch, and drag a box with zoom region (or Alt/Option + drag) to zoom to just that area.</p>
      <div class="mm-hint">Drag to pan · Ctrl/⌘ + scroll or pinch to zoom · Double-click empty space to fit · Shift + click to zoom to a branch · Alt/Option + drag (or zoom region) to zoom to a box · Branch colours match each section's category colour.</div>
      <div class="mm-bar">
        <button class="tool-btn" id="mmExpand" data-tip="Expand all" data-tip-body="Opens every branch so every bubble shows. The top bubble stays where it is on screen.">expand all</button>
        <button class="tool-btn" id="mmCollapse" data-tip="Collapse all" data-tip-body="Closes every branch back to the main sections, then fits the map in the frame.">collapse all</button>
        <span class="mm-sep" aria-hidden="true"></span>
        <button class="tool-btn" id="mmZoomOut" data-tip="Zoom out" data-tip-body="Zooms out 20% around the centre of the frame (down to 5%)." data-tip-keys="Also: Ctrl/⌘ + scroll down, or pinch in" aria-label="Zoom out">−</button>
        <span class="mm-zoom" id="mmZoom" data-tip="Zoom level" data-tip-body="The current zoom, from 5% to 300%. 100% is the normal bubble size." aria-live="polite">100%</span>
        <button class="tool-btn" id="mmZoomIn" data-tip="Zoom in" data-tip-body="Zooms in 25% around the centre of the frame (up to 300%)." data-tip-keys="Also: Ctrl/⌘ + scroll up, or pinch out" aria-label="Zoom in">+</button>
        <button class="tool-btn" id="mmFit" data-tip="Fit" data-tip-body="Zooms and centres so the whole map, as currently opened, fits in the frame." data-tip-keys="Also: double-click empty space">fit</button>
        <button class="tool-btn" id="mmRegion" data-tip="Zoom region" data-tip-body="Click to turn on, then drag a box on the map: it zooms to fit that box and the button turns off." data-tip-keys="Shortcut: Alt/Option + drag · Esc cancels" aria-pressed="false">zoom region</button>
        <button class="tool-btn" id="mmReset" data-tip="Reset view" data-tip-body="Back to 100% zoom, with the start of the map at the left edge of the frame.">reset view</button>
      </div>
      <div class="mm-wrap" id="mmWrap"><div class="mm-rect" id="mmRect"></div><svg id="mindmap" role="img" aria-label="Mind map of this page"></svg></div>'''
JS = r'''/* ===== mind map (NotebookLM style): horizontal tree built from this page; click arrows to expand,
   drag to pan, Ctrl/⌘+wheel or pinch to zoom, double-click empty space to fit, Shift+click to zoom to a
   branch, Alt/Option+drag or the zoom region button to zoom to a box. Added by mindmap_patch.py. ===== */
(() => {
  const svg = document.getElementById('mindmap'); if (!svg) return;
  const NS = 'http://www.w3.org/2000/svg';
  /* ---- the tree is built at load from this page itself: every section (number in [ ]), and inside it
     its list items, table rows, callouts, cards and subsections. Branch labels end with {children}.
     Optional hints on the markup: <ul data-mm-label="Features"> names a list's branch;
     <div class="table-wrap" data-mm-group="1" data-mm-group-label="Only in {v}"> groups a table's rows by a column. */
  const TREE = (() => {
    const T = s => (s || '').replace(/\s+/g, ' ').trim();
    const clip = (s, n = 230) => s.length <= n ? s : s.slice(0, n - 1).replace(/\s+\S*$/, '') + '…';
    const txt = el => { if (!el) return ''; const c = el.cloneNode(true);
      c.querySelectorAll('.sort-ind,.col-resizer,.owner-tag,.cat-pill').forEach(x => x.remove());
      return T(c.textContent).replace(/\s*\[\d{2,3}\]/g, ''); };          // drop the [NN] section-number suffixes
    const hidden = el => !!el.closest('[hidden],.owner-only,.own-col');   // never map owner-only content
    const css = getComputedStyle(document.documentElement);
    const catColor = sec => { const v = css.getPropertyValue('--cat-' + sec.dataset.cat).trim(); return /^#[0-9a-f]{6}$/i.test(v) ? v : '#00e5ff'; };
    const secs = [...document.querySelectorAll('main .section')];
    const summary = secs.find(s => s.dataset.title === 'Dashboard Summary');
    const idx = summary && [...summary.querySelectorAll('.table-wrap')].find(w => w.dataset.desc === 'What each section covers');
    const focus = {};
    if (idx) [...idx.querySelectorAll('tbody tr')].forEach(r => { if (r.cells.length >= 5) focus[txt(r.cells[1])] = {f: txt(r.cells[3]), w: txt(r.cells[4])}; });
    const N = (label, tip, el, children, color) => { const n = {label, tip: clip(tip || '')}; if (el) n.go = {el};
      if (children && children.length) { n.children = children; n.label += ' {' + children.length + '}'; } if (color) n.gcolor = color; return n; };
    const rowTip = (heads, r, skip) => [...r.cells].map((c, i) => { if (!i || i === skip) return ''; const v = txt(c); return v ? (heads[i] ? heads[i] + ': ' : '') + v : ''; }).filter(Boolean).join(' · ');
    const LEAF = new Set(['Glossary', 'References', 'Source Document (Verbatim)', 'Search']);
    const top = (body, sel) => [...body.querySelectorAll(sel)].filter(e => !hidden(e) && !(e.parentElement && e.parentElement.closest('.subsec')) && !e.closest('table'));
    const branches = [];
    secs.forEach(sec => {
      const title = sec.dataset.title, body = sec.querySelector('.sec-body');
      if (title === 'Mind Map' || hidden(sec) || !body) return;
      const num = T(sec.querySelector('.sec-num') && sec.querySelector('.sec-num').textContent);
      const tip = focus[title] ? focus[title].f : T(body.querySelector('p') && body.querySelector('p').textContent);
      const kids = [];
      if (sec === summary) {
        if (idx) [...idx.querySelectorAll('tbody tr')].forEach(r => { if (hidden(r) || r.cells.length < 5) return;
          const name = txt(r.cells[1]), f = focus[name]; kids.push(N(name, f ? f.f + (f.w ? ' · Use when: ' + f.w : '') : '', r)); });
        top(body, '.callout').forEach(co => { const l = txt(co.querySelector('.lbl')); kids.push(N(l, txt(co).slice(l.length).trim(), co)); });
      } else if (!LEAF.has(title)) {
        const lists = top(body, 'ul').filter(u => !u.closest('.callout,.resource')), tables = top(body, '.table-wrap'), callouts = top(body, '.callout'), cards = top(body, '.resource'), subs = top(body, '.subsec');
        const others = tables.length + callouts.length + cards.length + subs.length;
        lists.forEach((ul, i) => {
          const items = [...ul.children].filter(li => li.tagName === 'LI' && !hidden(li)).map(li => {
            const tid = li.querySelector('.tid'), all = txt(li);
            const l = tid ? txt(tid) : all.split(' ').slice(0, 6).join(' ') + (all.split(' ').length > 6 ? '…' : '');
            return N(l, tid ? all.slice(l.length).trim() : all, li); });
          if (!items.length) return;
          if (others || lists.length > 1) kids.push(N(ul.dataset.mmLabel || ('Key points' + (lists.length > 1 ? ' ' + (i + 1) : '')), items.length + ' items in this list, one bubble each.', ul, items));
          else kids.push(...items);
        });
        tables.forEach(w => {
          const t = w.querySelector('table'); if (!t || !t.tBodies[0]) return;
          const heads = t.tHead ? [...t.tHead.rows[0].cells].map(txt) : [];
          const rows = [...t.tBodies[0].rows].filter(r => !hidden(r) && r.cells.length);
          if (!rows.length) return;
          const desc = w.dataset.desc || heads[0] || 'Table';
          if (w.dataset.mmGroup !== undefined) {
            const g = +w.dataset.mmGroup, groups = new Map();
            rows.forEach(r => { const v = txt(r.cells[g]); if (!groups.has(v)) groups.set(v, []); groups.get(v).push(N(txt(r.cells[0]), rowTip(heads, r, g), r)); });
            groups.forEach((ch, v) => kids.push(N((w.dataset.mmGroupLabel || '{v}').replace('{v}', v), ch.length + ' row' + (ch.length === 1 ? '' : 's') + ' where ' + (heads[g] || 'the value') + ' is ' + v + '.', ch[0].go.el, ch)));
            return;
          }
          const leaves = rows.map(r => N(txt(r.cells[0]), rowTip(heads, r, -1), r));
          if (tables.length === 1 && !lists.length) kids.push(...leaves);
          else kids.push(N(desc, leaves.length + ' rows in this table.', w, leaves));
        });
        cards.forEach(c => kids.push(N(txt(c.querySelector('.r-name')) || 'Card', txt(c.querySelector('.r-note')), c)));
        subs.forEach(su => kids.push(N(su.dataset.desc || 'Part', '', su)));
        callouts.forEach(co => { const l = txt(co.querySelector('.lbl')); kids.push(N(l || 'Callout', txt(co).slice(l.length).trim(), co)); });
      }
      branches.push(N(title + ' [' + num + ']', tip, sec, kids, catColor(sec)));
    });
    const sub = document.querySelector('header h1 .sub');
    const name = T(document.title.split(' — ')[0]) || T(document.querySelector('header h1') && document.querySelector('header h1').firstChild.textContent);
    return N(name, sub ? T(sub.textContent) : 'This whole page as one map.', summary, branches);
  })();
  const PAL = ['#38dafa','#38fa79','#dafa38','#fa9938','#fa3899','#ea38fa','#7938fa','#3879fa'];
  const ROW = 38, GAP = 64, PADX = 14, BOXH = 28;
  let uid = 0;
  (function prep(n, d, color){ n.id = uid++; n.d = d; n.color = d === 1 ? PAL[(n.id) % PAL.length] : color;
    n.open = d < 1; (n.children || []).forEach((c, i) => { if (d === 0) c.color = PAL[i % PAL.length]; prep(c, d + 1, d === 0 ? PAL[i % PAL.length] : n.color); }); })(TREE, 0, '#00e5ff');
  (function fix(n){ (n.children||[]).forEach((c,i)=>{ if(n.d===0) c.color = c.gcolor || PAL[i % PAL.length]; else c.color = c.gcolor || n.color; fix(c); }); })(TREE);
  TREE.color = '#00e5ff';
  (function par(n){ (n.children || []).forEach(c => { c.parent = n; par(c); }); })(TREE);
  const ctx = document.createElement('canvas').getContext('2d');
  const tw = n => { ctx.font = (n.d === 0 ? '700 14px' : '13px') + ' "DM Sans",sans-serif'; return ctx.measureText(n.label).width; };
  const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
  const rgba = (hex, a) => { const v = parseInt(hex.slice(1), 16); return `rgba(${v>>16},${(v>>8)&255},${v&255},${a})`; };
  /* bubble hover card in the page's own .gj-tip style */
  const tip = document.createElement('div'); tip.className = 'gj-tip mm-tip'; tip.setAttribute('role', 'tooltip'); document.body.appendChild(tip);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);
  let tipFor = null;
  /* where a map bubble points: {sec: title} | {callout: [section title, label]} | {row: [table desc, first-cell text]} | {css: selector} */
  function mmTarget(go){
    if (!go) return null;
    if (go.el) return go.el;
    const secBy = t => [...document.querySelectorAll('.section')].find(s => s.dataset.title === t);
    if (go.sec) return secBy(go.sec) || null;
    if (go.callout) { const s = secBy(go.callout[0]); return s ? [...s.querySelectorAll('.callout')].find(c => (c.querySelector('.lbl')?.textContent || '').trim() === go.callout[1]) || null : null; }
    if (go.row) { const w = [...document.querySelectorAll('.table-wrap')].find(x => x.dataset.desc === go.row[0]);
      return w ? [...w.querySelectorAll('tbody tr')].find(r => (r.cells[0]?.textContent || '').replace(/\s*\[\d+\]\s*$/, '').trim() === go.row[1]) || null : null; }
    if (go.li) { const s = secBy(go.li[0]); return s ? [...s.querySelectorAll('li')].find(l => (l.querySelector('.tid')?.textContent || '').trim() === go.li[1]) || null : null; }
    if (go.css) return document.querySelector(go.css);
    return null;
  }
  function whereOf(el){ if (!el) return '';
    if (el.closest('header')) return 'the audio player under the title';
    const s = el.closest('.section'); const t = s ? s.dataset.title : '';
    if (el === s) return t;
    const it = el.closest('.citem'); const d = it ? (it.querySelector('.citem-desc, .citem-title')?.textContent || '').trim() : '';
    return t + (d ? ' › ' + d : ''); }
  function mmTipShow(n, e){
    {
      const tgt = mmTarget(n.go), kids = (n.children || []).length;
      tip.style.setProperty('--gj', n.color);
      tip.innerHTML = '<div class="gj-head"><span class="gj-title">' + esc(n.label) + '</span></div>' +
        '<div class="gj-def">' + esc(n.tip || '') + '</div>' +
        (tgt ? '<div class="gj-foot mm-tip-hint">click to go to ' + esc(whereOf(tgt)) + '</div>' : '') +
        (kids ? '<div class="gj-foot">' + (n.open ? '‹ closes' : '› opens') + ' this branch (' + kids + ')</div>' : '');
      tipFor = n; tip.classList.add('show');
      place((e && e.currentTarget || document.activeElement).getBoundingClientRect());
      return;
    }
  }
  // sit just below the hovered bubble (above it near the bottom of the window), never covering it
  function place(r){
    const w = tip.offsetWidth, h = tip.offsetHeight, vw = innerWidth, vh = innerHeight;
    let x = Math.min(Math.max(8, r.left), vw - w - 8), y = r.bottom + 8;
    if (y + h > vh - 8) y = Math.max(8, r.top - h - 8);
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }
  function mmTipMove(){}
  function mmTipHide(){ tipFor = null; tip.classList.remove('show'); }
  addEventListener('scroll', mmTipHide, { passive: true });
  /* ---- zoom / pan state (kept across re-renders) ---- */
  const wrap = document.getElementById('mmWrap'), zoomLbl = document.getElementById('mmZoom');
  let Z = 1, TX = 16, TY = 16, W0 = 0, H0 = 0, gView = null, userMoved = false, lastVis = [];
  const ZMIN = 0.05, ZMAX = 3;
  const vw = () => wrap.clientWidth, vh = () => wrap.clientHeight;
  function clampPan(){ const m = 60, w = W0 * Z, h = H0 * Z;
    TX = Math.min(Math.max(vw() - m, 0), Math.max(Math.min(m - w, 0), TX)); TY = Math.min(Math.max(vh() - m, 0), Math.max(Math.min(m - h, 0), TY)); }
  function apply(){ if (!gView) return; clampPan(); gView.setAttribute('transform', `translate(${TX},${TY}) scale(${Z})`); zoomLbl.textContent = Math.round(Z * 100) + '%'; }
  function zoomAt(f, cx, cy){ const nz = Math.min(ZMAX, Math.max(ZMIN, Z * f)); if (nz === Z) return;
    if (cx === undefined) { const v = visBox(); cx = (v.x0 + v.x1) / 2; cy = (v.y0 + v.y1) / 2; }
    TX = cx - (cx - TX) * nz / Z; TY = cy - (cy - TY) * nz / Z; Z = nz; userMoved = true; mmTipHide(); apply(); }
  function resetView(){ Z = 1; TX = 16; TY = H0 < vh() ? (vh() - H0) / 2 : 16; userMoved = true; apply(); }
  // bring the whole frame into view (just under the pinned toolbar) so nothing it fits is hidden
  function frameIntoView(){ const bar = document.querySelector('.mm-bar'), r = wrap.getBoundingClientRect();
    const top = parseFloat(getComputedStyle(bar).top) + bar.offsetHeight + 8;
    if (r.top < top - 1 || r.bottom > innerHeight + 1) window.scrollTo({top: r.top + scrollY - top, behavior: 'smooth'}); }
  // zoom so a box in map coordinates fills the frame (with a margin), centred
  /* the part of the frame you can actually see (not under the pinned toolbar, not past the window edge), in frame
     coordinates. If too little is showing, scroll the frame into view and use all of it. */
  function visBox(){ const r = wrap.getBoundingClientRect(), bar = document.querySelector('.mm-bar').getBoundingClientRect();
    const t = Math.max(r.top, bar.bottom, 0), b = Math.min(r.bottom, innerHeight), l = Math.max(r.left, 0), rt = Math.min(r.right, innerWidth);
    if (b - t < 160 || rt - l < 160) { frameIntoView(); return {x0: 0, y0: 0, x1: vw(), y1: vh()}; }
    return {x0: l - r.left, y0: t - r.top, x1: rt - r.left, y1: b - r.top}; }
  function zoomToBox(x0, y0, x1, y1, maxZ){ if (!vw()) return;
    const v = visBox(), VW = v.x1 - v.x0, VH = v.y1 - v.y0;
    const pad = 28, w = Math.max(1, x1 - x0), h = Math.max(1, y1 - y0);
    Z = Math.min(maxZ || ZMAX, Math.max(ZMIN, Math.min((VW - 2 * pad) / w, (VH - 2 * pad) / h)));
    TX = v.x0 + VW / 2 - (x0 + w / 2) * Z; TY = v.y0 + VH / 2 - (y0 + h / 2) * Z; userMoved = true; mmTipHide(); apply(); }
  function fitView(auto){ if (!vw()) return; if (!auto) frameIntoView();
    const pad = 24, z = Math.min((vw() - 2 * pad) / W0, (vh() - 2 * pad) / H0);
    Z = Math.min(1.5, Math.max(ZMIN, z));
    TX = (vw() - W0 * Z) / 2; TY = (vh() - H0 * Z) / 2; userMoved = !auto; apply(); }
  // keep a bubble where it is on screen when its branch opens or closes
  function anchored(n, fn){ const sy = n.y * Z + TY; fn(); TY = sy - n.y * Z; userMoved = true; apply(); }
  /* Shift + click: zoom to every visible item in the closest branch.
     A bubble with children = its own branch (opened if closed); a final bubble = its parent's branch. */
  const nodeBox = n => [n.x, n.y - BOXH / 2, n.x + n.w + ((n.children || []).length ? 24 : 0), n.y + BOXH / 2];
  function zoomBranch(n){
    let b = (n.children || []).length ? n : (n.parent || n);
    if (!b.open && (b.children || []).length) anchored(b, () => { b.open = true; render(); });
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    (function walk(m){ const [a, c, d, e] = nodeBox(m); x0 = Math.min(x0, a); y0 = Math.min(y0, c); x1 = Math.max(x1, d); y1 = Math.max(y1, e);
      if (m.open) (m.children || []).forEach(walk); })(b);
    zoomToBox(x0, y0, x1, y1, 1.6);
  }
  function nearestNode(mx, my){ let best = null, bd = Infinity;
    for (const n of lastVis) { const [a, c, d, e] = nodeBox(n); const dx = Math.max(a - mx, 0, mx - d), dy = Math.max(c - my, 0, my - e), dd = dx * dx + dy * dy;
      if (dd < bd) { bd = dd; best = n; } }
    return best; }
  function render(){
    mmTipHide();
    svg.textContent = '';
    const vis = [], colW = []; lastVis = vis;
    (function walk(n){ vis.push(n); n.w = tw(n) + PADX * 2; colW[n.d] = Math.max(colW[n.d] || 0, n.w); if (n.open) (n.children || []).forEach(walk); })(TREE);
    const colX = [0]; for (let d = 1; d < colW.length; d++) colX[d] = colX[d-1] + colW[d-1] + GAP;
    let y = 0;
    (function place(n){ const kids = n.open ? (n.children || []) : [];
      if (!kids.length) { n.y = y + BOXH/2; y += ROW; } else { kids.forEach(place); n.y = (kids[0].y + kids[kids.length-1].y) / 2; }
      n.x = colX[n.d]; })(TREE);
    const W = colX[colW.length-1] + colW[colW.length-1] + 40, H = Math.max(y, ROW);
    W0 = W; H0 = H;
    gView = el('g', {}, svg); apply();
    const gE = el('g', {}, gView), gN = el('g', {}, gView);
    vis.forEach(n => { if (n.open) (n.children || []).forEach(c => {
      const x1 = n.x + n.w + ((n.children||[]).length ? 22 : 0), x2 = c.x, mx = (x1 + x2) / 2;
      el('path', {class:'mm-edge', d:`M${x1},${n.y} C${mx},${n.y} ${mx},${c.y} ${x2},${c.y}`, stroke:c.color}, gE); }); });
    vis.forEach(n => {
      const kids = (n.children || []).length;
      const g = el('g', {class:'mm-node' + (n.d===0?' root':'') + (kids?'':' leaf'), transform:`translate(${n.x},${n.y})`, tabindex:'0', role:'button',
        'aria-label': n.label + (kids ? (n.open ? ', expanded' : ', collapsed') : '')}, gN);
      el('rect', {class:'box', x:0, y:-BOXH/2, width:n.w, height:BOXH, rx:BOXH/2, fill:rgba(n.color, n.d===0?.20:.12), stroke:rgba(n.color,.6)}, g);
      g.__node = n;
      const tx = el('text', {x:PADX, y:0}, g); tx.textContent = n.label;
      if (n.tip) { g.addEventListener('mouseenter', e => mmTipShow(n, e)); g.addEventListener('mousemove', mmTipMove);
        g.addEventListener('mouseleave', mmTipHide); g.addEventListener('focus', () => mmTipShow(n)); g.addEventListener('blur', mmTipHide); }
      if (n.go) g.classList.add('linked');
      if (kids) { const c = el('g', {class:'chev', transform:`translate(${n.w + 12},0)`}, g);
        el('circle', {r:9, stroke:rgba(n.color,.7)}, c); const ct = el('text', {y:1, fill:n.color}, c); ct.textContent = n.open ? '‹' : '›'; }
      // the › arrow opens/closes a branch; the bubble itself jumps to where that topic lives on the page
      const toggle = () => anchored(n, () => { n.open = !n.open; render(); });
      const jump = () => { const tgt = mmTarget(n.go);
        if (!tgt) return false; mmTipHide();
        if (tgt.classList.contains('section') && window.scrollToSection) scrollToSection(sections.indexOf(tgt)); else if (window.jumpToEl) jumpToEl(tgt);
        return true; };
      g.addEventListener('click', e => { if (kids && (e.target.closest('.chev') || !n.go)) toggle(); else if (!jump() && kids) toggle(); });
      g.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); if (!jump() && kids) toggle(); }
        else if (e.key === ' ' || e.key === 'ArrowRight' || e.key === 'ArrowLeft') { if (kids) { e.preventDefault(); if ((e.key === 'ArrowRight') !== n.open || e.key === ' ') toggle(); } } });
    });
  }
  const setAll = (n, v) => { if ((n.children||[]).length) { n.open = v; n.children.forEach(c => setAll(c, v)); } };
  document.getElementById('mmExpand').addEventListener('click', () => anchored(TREE, () => { setAll(TREE, true); render(); }));
  document.getElementById('mmCollapse').addEventListener('click', () => { setAll(TREE, false); TREE.open = true; render(); fitView(true); });
  document.getElementById('mmZoomIn').addEventListener('click', () => zoomAt(1.25));
  document.getElementById('mmZoomOut').addEventListener('click', () => zoomAt(1 / 1.25));
  document.getElementById('mmFit').addEventListener('click', () => fitView());
  const regionBtn = document.getElementById('mmRegion'); let regionMode = false;
  const setRegion = v => { regionMode = v; regionBtn.classList.toggle('mm-on', v); regionBtn.setAttribute('aria-pressed', v); wrap.classList.toggle('region', v); };
  regionBtn.addEventListener('click', () => setRegion(!regionMode));
  addEventListener('keydown', e => { if (e.key === 'Escape' && (regionMode || rect)) { cancelRect(); setRegion(false); } });
  document.getElementById('mmReset').addEventListener('click', resetView);
  /* Ctrl/⌘ + wheel (and trackpad pinch, which arrives as ctrl + wheel) zooms at the cursor; plain wheel still scrolls the page */
  svg.addEventListener('wheel', e => { if (!(e.ctrlKey || e.metaKey)) return; e.preventDefault();
    const r = svg.getBoundingClientRect(); zoomAt(Math.exp(-e.deltaY * (e.deltaMode ? 0.05 : 0.0025)), e.clientX - r.left, e.clientY - r.top); }, { passive: false });
  /* drag to pan (mouse, pen or one finger); two fingers pinch-zoom. A drag never counts as a click on a bubble. */
  const ptrs = new Map(); let dragged = false, startX = 0, startY = 0, pinch = null, rect = null;
  const rectEl = document.getElementById('mmRect');
  function cancelRect(){ rect = null; rectEl.style.display = 'none'; }
  function drawRect(cx, cy){ const r = wrap.getBoundingClientRect();
    const x0 = Math.min(rect.x, cx) - r.left, y0 = Math.min(rect.y, cy) - r.top, w = Math.abs(cx - rect.x), h = Math.abs(cy - rect.y);
    Object.assign(rectEl.style, {display: 'block', left: x0 + 'px', top: y0 + 'px', width: w + 'px', height: h + 'px'}); }
  svg.addEventListener('pointerdown', e => { if (e.button !== 0 && e.pointerType === 'mouse') return;
    if ((regionMode || e.altKey) && ptrs.size === 0) {   // zoom region: drag a box instead of panning
      e.preventDefault(); rect = {x: e.clientX, y: e.clientY, id: e.pointerId}; dragged = false; mmTipHide();
      try { svg.setPointerCapture(e.pointerId); } catch (_) {} return; }
    ptrs.set(e.pointerId, {x: e.clientX, y: e.clientY});
    if (ptrs.size === 1) { dragged = false; startX = e.clientX; startY = e.clientY; }
    if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; pinch = {d: Math.hypot(a.x - b.x, a.y - b.y), mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2}; } });
  svg.addEventListener('pointermove', e => {
    if (rect && e.pointerId === rect.id) { if (Math.hypot(e.clientX - rect.x, e.clientY - rect.y) > 4) dragged = true; if (dragged) drawRect(e.clientX, e.clientY); return; }
    const p = ptrs.get(e.pointerId); if (!p) return;
    const r = svg.getBoundingClientRect();
    if (ptrs.size === 2 && pinch) { p.x = e.clientX; p.y = e.clientY; const [a, b] = [...ptrs.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y), mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      TX += mx - pinch.mx; TY += my - pinch.my; zoomAt(d / (pinch.d || d), mx - r.left, my - r.top); pinch = {d, mx, my}; dragged = true; return; }
    if (!dragged && Math.hypot(e.clientX - startX, e.clientY - startY) < 5) return;
    if (!dragged) { dragged = true; wrap.classList.add('panning'); mmTipHide(); try { svg.setPointerCapture(e.pointerId); } catch (_) {} }
    TX += e.clientX - p.x; TY += e.clientY - p.y; p.x = e.clientX; p.y = e.clientY; userMoved = true; apply(); });
  const endPtr = e => {
    if (rect && e.pointerId === rect.id) {
      const r = svg.getBoundingClientRect(), w = Math.abs(e.clientX - rect.x), h = Math.abs(e.clientY - rect.y);
      if (e.type === 'pointerup' && w > 8 && h > 8) {
        const sx = Math.min(rect.x, e.clientX) - r.left, sy = Math.min(rect.y, e.clientY) - r.top;
        zoomToBox((sx - TX) / Z, (sy - TY) / Z, (sx + w - TX) / Z, (sy + h - TY) / Z);
        setRegion(false); }
      cancelRect(); if (dragged) setTimeout(() => { dragged = false; }, 0); return; }
    ptrs.delete(e.pointerId); if (ptrs.size < 2) pinch = null;
    if (!ptrs.size) { wrap.classList.remove('panning'); if (dragged) setTimeout(() => { dragged = false; }, 0); } };
  svg.addEventListener('pointerup', endPtr); svg.addEventListener('pointercancel', endPtr);
  svg.addEventListener('click', e => {
    if (dragged || regionMode) { e.stopPropagation(); e.preventDefault(); return; }
    if (e.shiftKey) {   // Shift + click: zoom to the closest branch (never jumps or toggles)
      e.stopPropagation(); e.preventDefault();
      const g = e.target.closest('.mm-node'), r = svg.getBoundingClientRect();
      const n = g ? g.__node : nearestNode((e.clientX - r.left - TX) / Z, (e.clientY - r.top - TY) / Z);
      if (n) zoomBranch(n); } }, true);
  /* double-click empty space: fit */
  svg.addEventListener('dblclick', e => { if (!e.target.closest('.mm-node') && !e.shiftKey) { e.preventDefault(); fitView(); } });
  /* the section starts collapsed (0 px wide): fit the map once it first becomes visible */
  const mmBar = document.querySelector('.mm-bar');
  const setBarH = () => document.documentElement.style.setProperty('--mmbar-h', mmBar.offsetHeight + 'px');
  setBarH();
  if (window.ResizeObserver) { new ResizeObserver(setBarH).observe(mmBar);
    new ResizeObserver(() => { if (vw() && !userMoved) fitView(true); else apply(); }).observe(wrap); }
  render();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { render(); if (!userMoved) fitView(true); });
})();

/* ---- hover cards for the mind map toolbar controls (same card style as the map bubbles) ---- */
(() => {
  const tip = document.createElement('div'); tip.className = 'gj-tip mm-ctl-tip'; tip.setAttribute('role', 'tooltip'); tip.id = 'mmCtlTip';
  tip.style.setProperty('--gj', 'var(--cyan)'); document.body.appendChild(tip);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);
  let cur = null, timer = 0;
  function show(el){ cur = el;
    tip.innerHTML = '<div class="gj-head"><span class="gj-title">' + esc(el.dataset.tip) + '</span></div>' +
      '<div class="gj-def">' + esc(el.dataset.tipBody) + '</div>' + (el.dataset.tipKeys ? '<div class="gj-foot keys">' + esc(el.dataset.tipKeys) + '</div>' : '');
    tip.classList.add('show');
    const r = el.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    let x = Math.min(Math.max(8, r.left + r.width / 2 - w / 2), innerWidth - w - 8), y = r.bottom + 8;
    if (y + h > innerHeight - 8) y = Math.max(8, r.top - h - 8);
    tip.style.left = x + 'px'; tip.style.top = y + 'px'; el.setAttribute('aria-describedby', 'mmCtlTip'); }
  function hide(){ clearTimeout(timer); if (cur) cur.removeAttribute('aria-describedby'); cur = null; tip.classList.remove('show'); }
  document.querySelectorAll('.mm-bar [data-tip]').forEach(el => {
    el.addEventListener('mouseenter', () => { clearTimeout(timer); timer = setTimeout(() => show(el), 250); });
    el.addEventListener('mouseleave', hide);
    el.addEventListener('focus', () => show(el)); el.addEventListener('blur', hide);
    el.addEventListener('click', () => { if (cur === el) show(el); });   // refresh position after the click
  });
  addEventListener('scroll', hide, { passive: true });
  addEventListener('keydown', e => { if (e.key === 'Escape') hide(); });
})();'''
def block(text, a, b, new):
    i, j = text.find(a), text.find(b)
    return text[:i] + new + text[j + len(b):] if i >= 0 and j > i else None
cssb = '  /* MIND-MAP-CSS:BEGIN */\n' + CSS + '\n  /* MIND-MAP-CSS:END */\n'
jsb = '<!-- MIND-MAP-JS:BEGIN -->\n<script>\n' + JS + '\n</script>\n<!-- MIND-MAP-JS:END -->\n'
bodyb = '<!-- MIND-MAP-BODY:BEGIN -->\n' + BODY + '\n      <!-- MIND-MAP-BODY:END -->'
if 'MIND-MAP-BODY:BEGIN' in s:
    s = block(s, '  /* MIND-MAP-CSS:BEGIN */', '  /* MIND-MAP-CSS:END */\n', cssb)
    s = block(s, '<!-- MIND-MAP-JS:BEGIN -->', '<!-- MIND-MAP-JS:END -->\n', jsb)
    s = block(s, '<!-- MIND-MAP-BODY:BEGIN -->', '<!-- MIND-MAP-BODY:END -->', bodyb)
    open(p, 'w', encoding='utf-8').write(s); print('mind map: refreshed'); sys.exit()
if 'id="mindmap"' in s: sys.exit('mind map: page already has a hand-made mind map; remove it first')
# --- section: same category as the Dashboard Summary, inserted before Glossary / References / verbatim / end of main
m = re.search(r'<div class="section (cat-[\w-]+)" data-title="Dashboard Summary" data-cat="([\w-]+)">.*?<span class="cat-badge">(.*?)</span>', s, re.S)
if not m: sys.exit('mind map: no Dashboard Summary section found')
cat, dcat, badge = m.groups()
anchor = None
for t in ('Glossary', 'References', 'Source Document (Verbatim)'):
    k = re.search(r'\n[ \t]*(<!--(?:(?!-->).)*-->\s*)*<div class="section [\w-]+" data-title="' + re.escape(t) + '"', s, re.S)
    if k: anchor = k.start() + 1; break
if anchor is None: anchor = s.index('</main>')
nums = [int(x) for x in re.findall(r'<span class="sec-num">(\d+)</span>', s[:anchor])]
n = (max(nums) + 1) if nums else 2
w = len(re.search(r'<span class="sec-num">(\d+)</span>', s).group(1)) if nums else 2
after = s[anchor:]
ctr = iter(range(n + 1, n + 1000))   # sections after the map: numbered consecutively (fixes the template's 97/98/99 placeholders too)
after = re.sub(r'<span class="sec-num">(\d+)</span>', lambda x: '<span class="sec-num">%0*d</span>' % (w, next(ctr)), after)
section = ('  <div class="section %s" data-title="Mind Map" data-cat="%s">\n'
           '    <div class="sec-head"><span class="sec-num">%0*d</span><span class="sec-title">Mind Map</span><span class="cat-badge">%s</span><span class="chevron">▶</span></div>\n'
           '    <div class="sec-body">\n      %s\n    </div>\n  </div>\n\n') % (cat, dcat, w, n, badge, bodyb)
s = s[:anchor] + section + after
# --- summary row (number filled at runtime from the section itself)
row = ('<tr><td><span class="secnum" data-target-title="Mind Map"></span></td><td><strong>Mind Map</strong></td><td class="sec-cat"></td>'
       '<td>Clickable map of every section, table row, list item, and callout</td><td>Seeing the whole page at a glance, or jumping straight to a detail</td></tr>')
g = s.find('<tr><td><span class="secnum" data-target-title="Glossary">')
if g < 0:
    t = s.find('data-desc="What each section covers"'); g = s.find('</tbody>', t) if t >= 0 else -1
if g < 0: sys.exit('mind map: no "What each section covers" table found')
s = s[:g] + row + '\n            ' + s[g:]
# --- CSS, script, search + glossary exclusions
i = s.index('</style>'); s = s[:i] + cssb + s[i:]
i = s.rfind('</body>'); i = i if i >= 0 else len(s); s = s[:i] + jsb + s[i:]
old = "node.tagName!=='SCRIPT' && node.tagName!=='STYLE'"
if old in s and "toLowerCase()!=='svg'" not in s: s = s.replace(old, old + " && node.tagName.toLowerCase()!=='svg'", 1)
old = "const EXCLUDE = new Set(['Dashboard Summary','Glossary','References','Source Document (Verbatim)']);"
if old in s: s = s.replace(old, "const EXCLUDE = new Set(['Dashboard Summary','Glossary','References','Source Document (Verbatim)','Mind Map']);", 1)
open(p, 'w', encoding='utf-8').write(s)
print('mind map: added as section %0*d' % (w, n))
