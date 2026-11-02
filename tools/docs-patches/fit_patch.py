import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
if 'function bodyWordMin(' in s:
    print('table-fit patch: already applied'); sys.exit()
R = [
("    const wrapHeads = headMin.reduce((a,b)=>a+b, 0) > avail;",
"""    // (also wrap when the first column's share plus the other one-line headers overflow)
    const wrapHeads = headMin.reduce((a,b)=>a+b, 0) > avail ||
      Math.min(natural[0], Math.round(avail * 0.4)) + headMin.slice(1).reduce((a,b)=>a+b, 0) > avail;"""),
("""    const widths = natural.slice();
    const sumNat = natural.reduce((a,b)=>a+b, 0);""",
"""    // never squeeze a body column below its longest single word (no mid-word breaks),
    // capped so one very long token can't hog the table
    // (only when all those floors still fit the page; otherwise fitting to width wins)
    { const wm = headMin.map((h,ci) => Math.max(h, Math.min(160, bodyWordMin(table, ci))));
      if(wm.reduce((a,b)=>a+b, 0) <= avail) headMin = wm; }
    const widths = natural.slice();
    const sumNat = natural.reduce((a,b)=>a+b, 0);"""),
("""      for(const o of order){ if(over<=0) break; const cut=Math.max(0, Math.min(over, rounded[o.ci]-headMin[o.ci])); rounded[o.ci]-=cut; over-=cut; }
    }""",
"""      for(const o of order){ if(over<=0) break; const cut=Math.max(0, Math.min(over, rounded[o.ci]-headMin[o.ci])); rounded[o.ci]-=cut; over-=cut; }
      // still over (long one-line first column, e.g. video titles): let col 0 wrap too
      if(over > 0){ const cut = Math.max(0, Math.min(over, rounded[0] - headMin[0])); rounded[0] -= cut; over -= cut; }
    }"""),
("function fitVisibleTables(){",
"""/* narrowest a column's body cells can be without breaking inside a word */
function bodyWordMin(table, ci){
  let max = 0;
  [...table.tBodies[0].rows].forEach(r => {
    const c = r.cells[ci]; if(!c) return;
    const m = c.cloneNode(true), cs = getComputedStyle(c);
    m.style.cssText = 'position:absolute;left:-9999px;top:-9999px;white-space:normal;overflow-wrap:normal;word-break:normal;width:min-content;visibility:hidden;';
    m.style.font = cs.font; m.style.padding = cs.padding; m.style.letterSpacing = cs.letterSpacing;
    document.body.appendChild(m); max = Math.max(max, m.getBoundingClientRect().width); m.remove();
  });
  return Math.ceil(max) + 2;
}
function fitVisibleTables(){"""),
]
for old, new in R:
    if s.count(old) != 1:
        sys.exit('table-fit patch: anchor not found (template changed?) — ' + old.strip()[:60])
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8').write(s)
print('table-fit patch: applied')
