#!/usr/bin/env python3
"""Add the vibe-dashboard Search section (section 02) to the Export Selected to DXF docs page.
Adapted from vibe-dashboards/ai-in-fusion-chats (build.py + search.js), layer 1 only:
this page links no other dashboards, so there is no search-index.json.
Usage: python3 add_search.py PAGE.html   (refuses to run twice)"""
import re, sys

p = sys.argv[1]
s = open(p, encoding='utf-8').read()
if 'id="xs"' in s:
    sys.exit('search: already added')

def rep(old, new, count=1):
    global s
    assert s.count(old) >= 1, 'anchor missing: ' + old[:70]
    s = s.replace(old, new, count)

# ---- 1. category "search" (9th colour: yellow-green, >=30 deg from all eight in use)
rep('    --cat-release:#7938fa;\n', '    --cat-release:#7938fa;\n    --cat-search:#79fa38;\n')
rep('  .toc-tip.tc-release .tip-badge{color:var(--cat-release);background:rgba(121,56,250,.10)}\n',
    '  .toc-tip.tc-release .tip-badge{color:var(--cat-release);background:rgba(121,56,250,.10)}\n'
    '  .toc-tip.tc-search .tip-badge{color:var(--cat-search);background:rgba(121,250,56,.10)}\n')
rep('  .toc-chip.tc-release:hover{color:var(--cat-release)}\n',
    '  .toc-chip.tc-release:hover{color:var(--cat-release)}\n'
    '  .cat-search .cat-badge{color:var(--cat-search);background:rgba(121,250,56,.10)}\n'
    '  .cat-search{border-left:3px solid var(--cat-search)}\n'
    '  .toc-chip.tc-search{border-left-color:var(--cat-search)}\n'
    '  .toc-chip.tc-search:hover{color:var(--cat-search)}\n')

# ---- 2. the section, right after the Dashboard Summary; renumber everything after it
BODY = '''      <p>Find anything on this page: options, steps, releases, terms, and every table row, list item and note.</p>
      <div id="xs" class="xs">
        <div class="subsec" data-tag="search" data-desc="Search box and results">
          <div class="xs-bar"><input id="xsq" type="search" placeholder="search options, steps, releases, terms…" autocomplete="off" aria-label="Search this page"><button type="button" id="xsclear" class="tool-btn">clear</button></div>
          <div id="xsstatus" class="xs-status"></div>
          <div id="xsres" class="xs-res" aria-live="polite"></div>
        </div>
        <div class="subsec" data-tag="filters" data-desc="Narrow by type, category, section and date">
          <div class="xs-filters">
            <div class="xs-row"><span class="xs-lab">Show</span><div id="xstypes" class="xs-chips"></div></div>
            <div class="xs-row"><span class="xs-lab">Category</span><div id="xskinds" class="xs-chips"></div></div>
            <div class="xs-row"><span class="xs-lab">Section</span><select id="xssec" aria-label="Section"></select><span class="xs-lab">From</span><input id="xsfrom" type="month" aria-label="From month"><span class="xs-lab">To</span><input id="xsto" type="month" aria-label="To month"></div>
          </div>
          <div class="xs-tipline">Filters work with or without words in the box. With an empty box, they list everything that matches. From and To apply to releases, the only dated items.</div>
        </div>
        <div class="table-wrap no-sort" data-desc="How to write a search">
          <table>
            <thead><tr><th>To do this</th><th>Type</th><th>Example</th></tr></thead>
            <tbody>
              <tr><td><strong>Match several words</strong></td><td>Words in any order</td><td><code>flat bend</code> finds items with both words</td></tr>
              <tr><td><strong>Match the start of a word</strong></td><td>The first few letters</td><td><code>constr</code> finds construction</td></tr>
              <tr><td><strong>Forgive a typo</strong></td><td>Nothing extra; used only when nothing matches as typed</td><td><code>pattrn</code> finds pattern</td></tr>
              <tr><td><strong>Match an exact phrase</strong></td><td>Words in "quotes"</td><td><code>"install update"</code></td></tr>
              <tr><td><strong>Leave a word out</strong></td><td>A minus sign before it</td><td><code>sketch -flat</code></td></tr>
              <tr><td><strong>Open the best match</strong></td><td>Enter</td><td>Jumps to the top result</td></tr>
            </tbody>
          </table>
        </div>
        <div class="callout">
          <span class="lbl">What gets searched and when it updates</span>
          <ul>
            <li><span class="tid">This page</span>every table row, list item, card, note and paragraph, plus each release in What's New and every glossary term.</li>
            <li><span class="tid">Always current</span>the search is built from the page each time it opens, so it always matches what you see, including the newest release.</li>
          </ul>
        </div>
      </div>'''
m = re.search(r'\n  <div class="section cat-[\w-]+" data-title="What&#x27;s New"|\n  <div class="section cat-[\w-]+" data-title="What\'s New"', s)
assert m, 'second section not found'
at = m.start() + 1
after = s[at:]
after = re.sub(r'<span class="sec-num">(\d+)</span>', lambda x: '<span class="sec-num">%02d</span>' % (int(x.group(1)) + 1), after)
section = ('  <div class="section cat-search" data-title="Search" data-cat="search">\n'
           '    <div class="sec-head"><span class="sec-num">02</span><span class="sec-title">Search</span><span class="cat-badge">Search</span><span class="chevron">▶</span></div>\n'
           '    <div class="sec-body">\n' + BODY + '\n    </div>\n  </div>\n\n')
s = s[:at] + section + after

# ---- 3. summary row 02, renumber the hard-coded rows after it
i = s.index('data-desc="What each section covers"'); j = s.index('</tbody>', i)
tb = s[i:j]
tb = re.sub(r'<span class="secnum">(\d+)</span>', lambda x: '<span class="secnum">%02d</span>' % (int(x.group(1)) + (1 if int(x.group(1)) >= 2 else 0)), tb)
row = ('<tr><td><span class="secnum">02</span></td><td><strong>Search</strong></td><td class="sec-cat"></td>'
       '<td>Full-text search of everything on this page, with filters</td><td>Looking for a setting, a step, a release or a term</td></tr>\n            ')
k = tb.index('<tr><td><span class="secnum">03</span>')
tb = tb[:k] + row + tb[k:]
s = s[:i] + tb + s[j:]

# ---- 4. generic-subsection patch (from the skill)
rep("body.querySelectorAll('.callout, .resource, .table-wrap').forEach(el => {\n    let kind, text;\n    if(el.classList.contains('callout')){",
    "body.querySelectorAll('.subsec, .callout, .resource, .table-wrap').forEach(el => {\n    let kind, text;\n    if(el.parentElement.closest('.subsec')) return;\n    if(el.classList.contains('subsec')){\n      kind = el.dataset.tag || 'part';\n      text = (el.dataset.desc || 'Part').trim();\n    } else if(el.classList.contains('callout')){")
rep("const TAG_CH = {callout:'CALLOUT', resource:'RESOURCE', table:'TABLE'};",
    "const TAG_CH = {callout:'CALLOUT', resource:'RESOURCE', table:'TABLE', search:'SEARCH', filters:'FILTERS'};")

# ---- 5. CSS (from the reference build, owner/dashboard bits dropped)
CSS = '''  /* SEARCH-SECTION-CSS */
  .xs{display:flex;flex-direction:column;gap:12px;margin:6px 0 4px}
  .xs > .citem{margin:0}
  .xs-bar{display:flex;gap:8px}
  #xsq{flex:1;min-width:0;background:var(--panel-2);border:1px solid var(--border);color:var(--text);font-family:var(--mono);font-size:14px;padding:11px 14px;border-radius:8px;outline:none}
  #xsq:focus{border-color:#79fa38;box-shadow:0 0 0 2px rgba(121,250,56,.18)}
  .xs-filters{display:flex;flex-direction:column;gap:8px}
  .xs-row{display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px}
  .xs-lab{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--text-mute);min-width:64px}
  .xs-chips{display:flex;flex-wrap:wrap;gap:6px;min-width:0}
  .xs-chip{font-family:var(--mono);font-size:11px;background:var(--panel-2);border:1px solid var(--border);color:var(--text-dim);padding:4px 9px;border-radius:20px;cursor:pointer}
  .xs-chip:hover{border-color:var(--cyan);color:var(--cyan)}
  .xs-chip.on{border-color:var(--cyan);color:var(--bg);background:var(--cyan)}
  .xs-chip .xs-n{opacity:.75}
  .xs-kind{--tc:#38dafa;color:var(--tc);border-color:color-mix(in srgb,var(--tc) 40%,transparent)}
  .xs-kind:hover{color:var(--tc);border-color:var(--tc)}
  .xs-kind.on{background:var(--tc);color:#0d0d0f;border-color:var(--tc)}
  #xssec,#xsfrom,#xsto{background:var(--panel-2);border:1px solid var(--border);color:var(--text);font-family:var(--mono);font-size:12px;padding:4px 8px;border-radius:6px;color-scheme:dark}
  .xs-status{font-family:var(--mono);font-size:11.5px;color:var(--text-mute)}
  .xs-status b{color:var(--text)}
  .xs-res{display:flex;flex-direction:column;gap:14px}
  .xs-gh{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#79fa38;margin:0 0 6px}
  .xs-gh span{color:var(--text-mute);letter-spacing:.04em}
  .xs-group{display:flex;flex-direction:column;gap:8px}
  .xs-item{background:var(--panel-2);border:1px solid var(--border);border-radius:8px;padding:10px 12px;min-width:0}
  .xs-top{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 10px}
  .xs-go{background:none;border:0;padding:0;font:inherit;font-size:14.5px;font-weight:700;color:var(--text);cursor:pointer;text-align:left}
  .xs-go:hover{color:var(--cyan);text-decoration:underline}
  .xs .tid{display:inline-block;font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;border:1px solid;border-radius:4px;padding:0 6px}
  .xs-type{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--text-mute)}
  .xs b.dt{color:var(--text);font-family:var(--mono);font-size:12px}
  .xs-snip{font-size:13.5px;color:var(--text-dim);margin-top:5px;line-height:1.5;overflow-wrap:anywhere}
  .xs-hit{color:#0d0d0f;background:#79fa38;border-radius:2px;padding:0 1px;font-weight:600}
  .xs-meta{display:flex;flex-wrap:wrap;align-items:center;gap:4px;margin-top:7px;font-family:var(--mono);font-size:11.5px}
  .xs-dot{color:var(--text-mute);margin:0 4px}
  .xs-sec{background:none;border:0;padding:0;font:inherit;color:var(--cyan);cursor:pointer}
  .xs-sec:hover{text-decoration:underline}
  .xs-more{align-self:flex-start;background:none;border:1px dashed var(--border);color:var(--text-dim);font-family:var(--mono);font-size:11.5px;padding:5px 10px;border-radius:6px;cursor:pointer}
  .xs-more:hover{border-color:var(--cyan);color:var(--cyan)}
  .xs-tips{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
  .xs-tips .xs-gh{width:100%}
  .xs-try{font-family:var(--mono);font-size:12px;background:var(--panel-2);border:1px solid var(--border);color:var(--text);padding:4px 10px;border-radius:6px;cursor:pointer}
  .xs-try:hover{border-color:#79fa38;color:#79fa38}
  .xs-tipline{width:100%;font-size:13px;color:var(--text-dim);margin-top:6px}
  .xs-empty{font-size:13.5px;color:var(--text-dim)}
  @media (max-width:600px){.xs-lab{min-width:0;width:100%}}
'''
i = s.index('</style>'); s = s[:i] + CSS + s[i:]

# ---- 6. script
JS = open(__file__.replace('add_search.py', 'search_esd.js'), encoding='utf-8').read()
i = s.rfind('</body>'); s = s[:i] + '<!-- SEARCH-SECTION-JS:BEGIN -->\n<script>\n' + JS + '\n</script>\n<!-- SEARCH-SECTION-JS:END -->\n' + s[i:]
open(p, 'w', encoding='utf-8').write(s)
print('search: added as section 02')
