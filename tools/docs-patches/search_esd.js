/* ===================== Search section =====================
   Everything on this page — releases, options, steps, table rows, callouts, cards, list items,
   paragraphs and glossary terms — read from the page itself when it opens, so it always matches it.
   Matching: words in any order, start of a word, simple stems, small typos forgiven (only when a word
   matches nothing as typed), "phrases", -exclusions. Adapted from the AI in Fusion Chats dashboard. */
(() => {
const XS = document.getElementById('xs'); if(!XS) return;
const $ = id => document.getElementById(id);
const input = $('xsq'), res = $('xsres'), status = $('xsstatus');
const esc = t => String(t).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const norm = s => String(s).toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g,'').replace(/[‘’]/g,"'");
const toks = s => norm(s).match(/[a-z0-9]+/g) || [];
const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const tx = n => { if(!n) return ''; const c = n.cloneNode(true);
  c.querySelectorAll('.sort-ind,.col-resizer,.owner-tag,.cat-pill').forEach(x => x.remove());
  c.querySelectorAll('li,td,th,p,div,br').forEach(x => x.append(' '));   // keep block texts apart
  return c.textContent.replace(/\s+/g, ' ').replace(/\s*\[\d{2,3}\]/g, '').trim(); };
const css = getComputedStyle(document.documentElement);
const hidden = el => !!(el && el.closest('[hidden],.owner-only,.own-col'));

/* ---------------- documents ---------------- */
const TYPES = [['option','Options'], ['step','Steps'], ['page','Elsewhere on this page'], ['term','Glossary terms'], ['release','Releases']];
const docs = [];
const KINDS = {};                      // section category label -> colour
const secMeta = sec => {
  const badge = tx(sec.querySelector('.cat-badge')), col = css.getPropertyValue('--cat-' + sec.dataset.cat).trim() || '#38dafa';
  if(badge) KINDS[badge] = col;
  return {sec: sec.dataset.title, secNum: tx(sec.querySelector('.sec-num')), kind: badge};
};
const ymOf = s => { const m = /([A-Z][a-z]{2}) (\d{1,2}), (\d{4})/.exec(s || ''); return m ? {ym: m[3] + '-' + String(MON.indexOf(m[1]) + 1).padStart(2, '0'), date: m[0]} : null; };
sections.forEach((sec, si) => {
  const title = sec.dataset.title;
  if(si === 0 || title === 'Search' || title === 'Mind Map' || hidden(sec)) return;
  const body = sec.querySelector('.sec-body'); if(!body) return;
  const meta = secMeta(sec);
  const add = d => docs.push(Object.assign({}, meta, d));
  if(title === "What's New"){
    body.querySelectorAll('.callout').forEach(co => {
      const lbl = tx(co.querySelector('.lbl')), v = lbl.split(' · ')[0], dt = ymOf(lbl) || {};
      add({type:'release', title: v + ' — ', body: tx(co).slice(lbl.length), el: co, date: dt.date, ym: dt.ym, label: v});
      co.querySelectorAll('li').forEach(li => { const t = tx(li.querySelector('.tid'));
        add({type:'release', title: v + ' · ' + t, body: tx(li).slice(t.length).trim(), el: li, date: dt.date, ym: dt.ym, label: v}); });
    });
    body.querySelectorAll(':scope > p').forEach(el => add({type:'page', title, body: tx(el), el}));
    return;
  }
  body.querySelectorAll('tbody tr').forEach(tr => {
    if(hidden(tr)) return;
    const wrap = tr.closest('.table-wrap'), table = tr.closest('table');
    const heads = table.tHead ? [...table.tHead.rows[0].cells].map(tx) : [];
    const cells = [...tr.cells].filter(c => !c.matches('.gloss-uses,.gloss-count,.own-col'));
    const vals = cells.map(tx).filter(Boolean); if(!vals.length) return;
    const isStep = heads.includes('Step');
    const t = title === 'Glossary' ? 'term' : title === 'Options Reference' ? 'option' : isStep ? 'step' : 'page';
    let ttl = vals[0], bod = vals.slice(1).join(' · ');
    if(isStep){ const si2 = heads.indexOf('Step'), ti = heads.indexOf('Topic');
      ttl = (ti >= 0 ? tx(tr.cells[ti]) + ': ' : '') + tx(tr.cells[si2]).split(/(?<=[.!?])\s/)[0];
      bod = tx(tr.cells[si2]); }
    add({type: t, title: ttl, body: bod, el: tr, desc: wrap ? wrap.dataset.desc : ''});
  });
  body.querySelectorAll('.callout, .resource, li').forEach(el => {
    if(hidden(el) || el.closest('table')) return;
    if(el.tagName === 'LI' && el.closest('.callout')) return;     // part of its callout
    let ttl, bod;
    if(el.classList.contains('callout')){ ttl = tx(el.querySelector('.lbl')); bod = tx(el).slice(ttl.length).trim(); }
    else if(el.classList.contains('resource')){ ttl = tx(el.querySelector('.r-name')); bod = tx(el.querySelector('.r-note')); }
    else { ttl = tx(el.querySelector('.tid')) || title; bod = tx(el).slice(tx(el.querySelector('.tid')).length).trim(); }
    add({type:'page', title: ttl || title, body: bod, el});
  });
  body.querySelectorAll(':scope > p').forEach(el => add({type:'page', title, body: tx(el), el}));
});
/* release titles: version + its one-line summary */
docs.forEach(d => { if(d.type === 'release' && / — $/.test(d.title)){ const co = d.el, lb = co.querySelector('.lbl');
  let t = ''; for(let n = lb.nextSibling; n && !(n.nodeType === 1 && n.tagName === 'UL'); n = n.nextSibling) t += n.textContent;
  d.title = d.label + ' — ' + t.replace(/\s+/g, ' ').trim().replace(/\.$/, ''); } });

/* ---------------- index ---------------- */
const POST = new Map();
docs.forEach((d, i) => {
  d.tt = new Set(toks(d.title)); d.bt = new Set(toks(d.body + ' ' + (d.desc || ''))); d.nt = norm(d.title + ' ' + d.body);
  for(const t of d.tt) (POST.get(t) || POST.set(t, new Set()).get(t)).add(i);
  for(const t of d.bt) (POST.get(t) || POST.set(t, new Set()).get(t)).add(i);
});
const VOCAB = [...POST.keys()];
function within(a, b, max){
  if(Math.abs(a.length - b.length) > max) return false;
  let prev = Array.from({length:b.length + 1}, (_, j) => j);
  for(let i = 1; i <= a.length; i++){
    const cur = [i]; let best = i;
    for(let j = 1; j <= b.length; j++){ cur[j] = Math.min(prev[j] + 1, cur[j-1] + 1, prev[j-1] + (a[i-1] === b[j-1] ? 0 : 1)); if(cur[j] < best) best = cur[j]; }
    if(best > max) return false; prev = cur;
  }
  return prev[b.length] <= max;
}
const ALIAS = {f360:'fusion', fusion360:'fusion', dwg:'dxf', sm:'sheet'};
function expand(w){
  w = ALIAS[w] || w;
  const out = new Map(), fz = w.length >= 8 ? 2 : (w.length >= 4 ? 1 : 0);
  const st = w.length > 4 ? w.replace(/ies$/, 'y').replace(/(es|s|ing|ed)$/, '') : w;
  for(const t of VOCAB){
    if(t === w) out.set(t, 3);
    else if(w.length >= 2 && t.startsWith(w)) out.set(t, 2);
    else if(st !== w && st.length >= 3 && t.startsWith(st)) out.set(t, 2);
  }
  if(out.size || !fz || !/^[a-z]+$/.test(w)) return out;
  const near = VOCAB.filter(t => t.length >= 4 && t[0] === w[0] && within(w, t, fz));
  const isSub = t => { let j = 0; for(const ch of t) if(ch === w[j]) j++; return j === w.length; };
  const best = near.filter(isSub);
  (best.length ? best : near).forEach(t => out.set(t, 1));
  out.fuzzy = true; return out;
}
function parse(qs){
  const phrases = [], neg = [], pos = [];
  qs = qs.replace(/"([^"]+)"/g, (m, p) => { const n = norm(p).trim(); if(n) phrases.push(n); return ' '; });
  qs.split(/\s+/).forEach(w => { if(!w) return; if(w[0] === '-' && w.length > 1) toks(w.slice(1)).forEach(t => neg.push(t)); else toks(w).forEach(t => pos.push(t)); });
  return {phrases, neg, pos:[...new Set(pos)]};
}

/* ---------------- filters ---------------- */
const F = {types:new Set(), kinds:new Set(), sec:'', from:'', to:''};
const typeBox = $('xstypes'), kindBox = $('xskinds'), secSel = $('xssec');
typeBox.innerHTML = TYPES.map(([k, n]) => '<button type="button" class="xs-chip" data-t="' + k + '">' + n + ' <span class="xs-n"></span></button>').join('');
kindBox.innerHTML = Object.keys(KINDS).map(k => '<button type="button" class="xs-chip xs-kind" data-k="' + esc(k) + '" style="--tc:' + KINDS[k] + '">' + esc(k) + '</button>').join('');
const secNames = [...new Set(docs.map(d => d.sec))];
secSel.innerHTML = '<option value="">All sections</option>' + secNames.map(s => '<option>' + esc(s) + '</option>').join('');
const yms = docs.map(d => d.ym).filter(Boolean).sort();
if(yms.length){ $('xsfrom').min = $('xsto').min = yms[0]; $('xsfrom').max = $('xsto').max = yms[yms.length - 1]; }
const toggle = (set, v) => set.has(v) ? set.delete(v) : set.add(v);
typeBox.addEventListener('click', e => { const b = e.target.closest('[data-t]'); if(!b) return; toggle(F.types, b.dataset.t); b.classList.toggle('on'); run(); });
kindBox.addEventListener('click', e => { const b = e.target.closest('[data-k]'); if(!b) return; toggle(F.kinds, b.dataset.k); b.classList.toggle('on'); run(); });
secSel.addEventListener('change', () => { F.sec = secSel.value; run(); });
$('xsfrom').addEventListener('change', e => { F.from = e.target.value; run(); });
$('xsto').addEventListener('change', e => { F.to = e.target.value; run(); });
$('xsclear').addEventListener('click', () => {
  input.value = ''; F.types.clear(); F.kinds.clear(); F.sec = ''; F.from = ''; F.to = '';
  secSel.value = ''; $('xsfrom').value = ''; $('xsto').value = '';
  XS.querySelectorAll('.xs-chip.on').forEach(b => b.classList.remove('on')); run(); input.focus();
});
function passFilters(d){
  if(F.types.size && !F.types.has(d.type)) return false;
  if(F.kinds.size && !F.kinds.has(d.kind)) return false;
  if(F.sec && d.sec !== F.sec) return false;
  if(F.from && !(d.ym && d.ym >= F.from)) return false;
  if(F.to && !(d.ym && d.ym <= F.to)) return false;
  return true;
}
const filtersOn = () => F.types.size || F.kinds.size || F.sec || F.from || F.to;

/* ---------------- search ---------------- */
let last = {hits:[], re:null};
function search(qs){
  const {phrases, neg, pos} = parse(qs);
  const exp = pos.map(expand);
  let ids = null;
  exp.forEach(m => { const s = new Set(); for(const t of m.keys()) (POST.get(t) || []).forEach(i => s.add(i)); ids = ids ? new Set([...ids].filter(i => s.has(i))) : s; });
  if(!ids) ids = new Set(docs.map((_, i) => i));
  const negSet = new Set(); neg.forEach(w => VOCAB.forEach(t => { if(t.startsWith(w)) (POST.get(t) || []).forEach(i => negSet.add(i)); }));
  const hits = [];
  ids.forEach(i => {
    if(negSet.has(i)) return;
    const d = docs[i];
    if(phrases.some(p => !d.nt.includes(p)) || !passFilters(d)) return;
    let sc = 0;
    exp.forEach(m => { let b = 0; m.forEach((w, t) => { if(d.tt.has(t)) b = Math.max(b, w * 2.2); else if(d.bt.has(t)) b = Math.max(b, w); }); sc += b; });
    sc += phrases.length * 4 + (d.type === 'option' || d.type === 'term' ? 1 : 0);
    hits.push({d, sc});
  });
  hits.sort((a, b) => b.sc - a.sc);
  const words = [...new Set([].concat(...exp.map(m => [...m.keys()])))].sort((a, b) => b.length - a.length).slice(0, 60);
  const reEsc = w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const alts = words.map(reEsc).concat(phrases.map(p => reEsc(p).replace(/\s+/g, '\\s+')));
  const fuzzy = [].concat(...exp.filter(m => m.fuzzy).map(m => [...m.keys()])).slice(0, 8);
  return {fuzzy, hits, re: alts.length ? new RegExp('(' + alts.join('|') + ')', 'gi') : null};
}
function hl(s, re){
  if(!re) return esc(s);
  let out = '', i = 0;
  for(const m of s.matchAll(re)){ out += esc(s.slice(i, m.index)) + '<b class="xs-hit">' + esc(m[0]) + '</b>'; i = m.index + m[0].length; }
  return out + esc(s.slice(i));
}
function snip(s, re, len){
  len = len || 240; s = s || '';
  if(s.length <= len) return hl(s, re);
  let at = 0;
  if(re){ re.lastIndex = 0; const m = re.exec(s); if(m) at = Math.max(0, m.index - 90); re.lastIndex = 0; }
  if(at){ const sp = s.indexOf(' ', at); at = sp > 0 && sp < at + 20 ? sp + 1 : at; }
  const part = s.slice(at, at + len);
  return (at ? '… ' : '') + hl(part, re) + (at + len < s.length ? ' …' : '');
}

/* ---------------- render ---------------- */
const LIMIT = 6, open = {};
const secIndex = title => sections.findIndex(s => s.dataset.title === title);
function secLink(d){ const si = secIndex(d.sec); if(si < 0) return '';
  return '<button type="button" class="xs-sec" data-si="' + si + '">' + esc(d.sec) + ' [' + esc(d.secNum) + ']</button>'; }
const kindTag = d => d.kind ? '<span class="tid" style="--tc:' + (KINDS[d.kind] || '#38dafa') + '">' + esc(d.kind) + '</span>' : '';
function itemHTML(h, k, re){
  const d = h.d;
  const lab = d.type === 'term' ? 'Term' : d.type === 'option' ? 'Option' : d.type === 'step' ? (d.desc || 'Step') : d.type === 'release' ? 'Release' : (d.desc || 'On this page');
  return '<div class="xs-item"><div class="xs-top">' + (d.date ? '<b class="dt">' + esc(d.date) + '</b>' : '') + kindTag(d)
    + '<span class="xs-type">' + esc(lab) + '</span>'
    + '<button type="button" class="xs-go" data-k="' + k + '">' + hl(d.title, re) + '</button></div>'
    + (d.body ? '<div class="xs-snip">' + snip(d.body, re) + '</div>' : '')
    + '<div class="xs-meta">' + secLink(d) + '</div></div>';
}
let shown = [];
function render(hits, re, browse){
  shown = hits;
  const groups = {}; TYPES.forEach(([k]) => groups[k] = []);
  hits.forEach((h, i) => groups[h.d.type].push([h, i]));
  typeBox.querySelectorAll('[data-t]').forEach(b => { b.querySelector('.xs-n').textContent = (input.value.trim() || browse) ? groups[b.dataset.t].length || '' : ''; });
  let html = '';
  TYPES.forEach(([k, name]) => {
    const g = groups[k]; if(!g.length) return;
    const lim = open['g_' + k] ? g.length : LIMIT;
    html += '<div class="xs-group"><div class="xs-gh">' + name + ' <span>' + g.length + '</span></div>'
      + g.slice(0, lim).map(([h, i]) => itemHTML(h, i, re)).join('')
      + (g.length > lim ? '<button type="button" class="xs-more" data-open="g_' + k + '">Show all ' + g.length + '</button>' : '') + '</div>';
  });
  res.innerHTML = html || '<div class="xs-empty">No matches. Try fewer words, a shorter word, or clear the filters.</div>';
}
function tips(){
  res.innerHTML = '<div class="xs-tips"><div class="xs-gh">Try</div>'
    + ['bend lines', 'units', '"install update"', 'polyline', 'sketch -flat', 'pattrn', 'privacy']
      .map(t => '<button type="button" class="xs-try">' + esc(t) + '</button>').join('')
    + '<div class="xs-tipline">Words match in any order and by the start of a word (<b>constr</b> finds construction). Small typos are forgiven. Use "quotes" for an exact phrase and -word to exclude. Or pick a filter with an empty box to list everything that matches it.</div></div>';
  typeBox.querySelectorAll('.xs-n').forEach(n => n.textContent = '');
}
function run(){
  const qs = input.value.trim();
  Object.keys(open).forEach(k => delete open[k]);
  if(!qs){
    if(!filtersOn()) return tips();
    const hits = docs.filter(passFilters).map(d => ({d, sc:0}));
    last = {hits, re:null}; return render(hits, null, true);
  }
  last = search(qs); render(last.hits, last.re, false);
  if(last.fuzzy && last.fuzzy.length) res.insertAdjacentHTML('afterbegin', '<div class="xs-tipline">No exact match for some words, so similar spellings are included: <b>' + last.fuzzy.map(esc).join(', ') + '</b></div>');
}
let tmr = 0;
input.addEventListener('input', () => { clearTimeout(tmr); tmr = setTimeout(run, 140); });
input.addEventListener('keydown', e => {
  if(e.key === 'Enter'){ e.preventDefault(); const h = shown[0]; if(h && h.d.el) jumpToEl(h.d.el); }   // best match overall
  if(e.key === 'Escape'){ input.value = ''; run(); }
});
res.addEventListener('click', e => {
  const go = e.target.closest('.xs-go');
  if(go){ const h = shown[+go.dataset.k]; if(h && h.d.el) jumpToEl(h.d.el); return; }
  const s = e.target.closest('.xs-sec'); if(s){ scrollToSection(+s.dataset.si); return; }
  const m = e.target.closest('.xs-more'); if(m){ open[m.dataset.open] = 1; render(last.hits, last.re, !input.value.trim()); return; }
  const t = e.target.closest('.xs-try'); if(t){ input.value = t.textContent; run(); input.focus(); }
});
status.innerHTML = 'Searching <b>' + docs.length + '</b> items on this page';
tips();
})();
