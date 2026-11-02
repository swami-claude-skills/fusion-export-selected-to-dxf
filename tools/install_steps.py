#!/usr/bin/env python3
"""One source for the install instructions.

Usage:  python3 tools/install_steps.py PAGE.html [PAGE2.html ...]

- Rebuilds the docs' header install panel (between <!-- INSTALL-PANEL:BEGIN/END -->)
  and section 09's install tables (between <!-- INSTALL-TABLES:BEGIN/END -->).
- Writes ExportSelectedToDXF/READ ME FIRST.txt, which ships in the zip.
Text uses **bold**; it becomes <strong> in HTML and plain text in the .txt.
"""
import html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ZIP = 'https://github.com/swami-claude-skills/fusion-export-selected-to-dxf/releases/latest/download/ExportSelectedToDXF.zip'
OPEN_SAI = ('open **Scripts and Add-Ins**: press **Shift+S**, or click the **UTILITIES** tab, '
            'open the **ADD-INS** drop-down and choose **Scripts and Add-Ins**')

METHODS = [
    ('fusion', 'In Fusion (recommended)', 'Mac and Windows. Nothing to approve, because no installer script runs.', [
        ('Unzip', 'Unzip **ExportSelectedToDXF.zip** and put the **ExportSelectedToDXF** folder somewhere it can stay, '
                  'for example in Documents. Fusion runs the add-in from that folder.'),
        ('Open', 'In Fusion, ' + OPEN_SAI + '.'),
        ('Add', 'Click the **+** next to **My Add-Ins** and choose the **ExportSelectedToDXF** folder.'),
        ('Run', 'Turn on **Run** and **Run on Startup** for ExportSelectedToDXF.'),
        ('Find it', 'The button is on the **SOLID** tab under **CREATE**, and under **UTILITIES ▸ ADD-INS**.'),
    ]),
    ('mac', 'Mac installer', 'Copies the add-in into Fusion\'s own AddIns folder. macOS blocks it the first time.', [
        ('Unzip', 'Unzip **ExportSelectedToDXF.zip**, open the **ExportSelectedToDXF** folder and double-click **install-macos.command**.'),
        ('Blocked', 'macOS says it **could not verify** the file. Click **Done** (not Move to Trash).'),
        ('Allow', 'Open **System Settings ▸ Privacy & Security**, scroll down to **Security**, and next to '
                  '"install-macos.command was blocked" click **Open Anyway**. Confirm with **Open Anyway** again '
                  'and your Mac password or Touch ID.'),
        ('Install', 'A Terminal window copies the add-in and says **Done**. Press any key to close it.'),
        ('Run', 'In Fusion, ' + OPEN_SAI + '. Select **ExportSelectedToDXF** under Add-Ins and turn on **Run** and **Run on Startup**.'),
        ('Note', 'macOS asks again for every newly downloaded zip. Updates from the panel\'s **install update** button never ask.'),
    ]),
    ('win', 'Windows installer', 'Copies the add-in into Fusion\'s own AddIns folder.', [
        ('Unzip', 'Right-click **ExportSelectedToDXF.zip** and choose **Extract All** (the installer can\'t run from inside the zip).'),
        ('Run it', 'Open the extracted **ExportSelectedToDXF** folder and double-click **install-windows.cmd**.'),
        ('Allow', 'If Windows shows **Windows protected your PC**, click **More info**, then **Run anyway**. '
                  'If it shows an **Open File - Security Warning**, click **Run**.'),
        ('Install', 'A window copies the add-in and says **Done**. Press any key to close it.'),
        ('Run', 'In Fusion, ' + OPEN_SAI + '. Select **ExportSelectedToDXF** under Add-Ins and turn on **Run** and **Run on Startup**.'),
    ]),
]


def h(s):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html.escape(s, quote=False))


def panel():
    tabs = ''.join('<button type="button" class="it-tab%s" data-it="%s">%s</button>' % (' on' if i == 0 else '', k, html.escape(t))
                   for i, (k, t, _, _) in enumerate(METHODS))
    panes = ''.join('<div class="it-pane%s" data-it="%s"><p class="it-note">%s</p><ol>%s</ol></div>' % (
        ' on' if i == 0 else '', k, h(n), ''.join('<li>%s</li>' % h(s) for _, s in steps))
        for i, (k, _, n, steps) in enumerate(METHODS))
    return '''<style>
  .getit{margin:14px auto 4px;max-width:760px;text-align:center}
  .getit .dl{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:8px;background:var(--cyan);color:#0d0d0f;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px;text-decoration:none;letter-spacing:.3px}
  .getit .dl:hover{filter:brightness(1.12)}
  .getit details{margin-top:10px;text-align:left}
  .getit summary{cursor:pointer;list-style:none;text-align:center;font-family:'JetBrains Mono',monospace;font-size:12.5px;color:var(--cyan)}
  .getit summary::-webkit-details-marker{display:none}
  .getit summary::before{content:'▸ ';display:inline-block;transition:transform .15s}
  .getit details[open] summary::before{transform:rotate(90deg)}
  .getit .it-box{margin-top:10px;border:1px solid var(--border,#2a2a30);border-radius:10px;background:var(--surface,#141418);padding:12px 14px}
  .getit .it-tabs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
  .getit .it-tab{font-family:'JetBrains Mono',monospace;font-size:12px;padding:5px 10px;border-radius:6px;border:1px solid var(--border,#2a2a30);background:transparent;color:var(--text-dim);cursor:pointer}
  .getit .it-tab.on{border-color:var(--cyan);color:var(--cyan)}
  .getit .it-pane{display:none}
  .getit .it-pane.on{display:block}
  .getit .it-note{margin:0 0 8px;font-size:12.5px;color:var(--text-dim)}
  .getit ol{margin:0;padding-left:20px;font-size:13.5px;line-height:1.55;color:var(--text)}
  .getit ol li{margin:3px 0}
  .getit ol li::marker{color:var(--cyan);font-weight:700}
</style>
<div class="getit">
  <a class="dl" href="%s">⬇ Download ExportSelectedToDXF.zip</a>
  <details>
    <summary>How to install</summary>
    <div class="it-box"><div class="it-tabs">%s</div>%s</div>
  </details>
</div>
<script>
document.querySelectorAll('.getit .it-tab').forEach(function(b){b.addEventListener('click',function(){
  var k=b.dataset.it;document.querySelectorAll('.getit [data-it]').forEach(function(e){e.classList.toggle('on',e.dataset.it===k)});
});});
</script>''' % (ZIP, tabs, panes)


def tables():
    out = []
    for _, title, note, steps in METHODS:
        rows = ''.join('<tr><td><strong>%d</strong></td><td><span class="tid">%s</span></td><td>%s</td></tr>' % (i, html.escape(t), h(s))
                       for i, (t, s) in enumerate(steps, 1))
        out.append('''      <div class="table-wrap no-sort" data-desc="Install: %s">
        <table>
          <thead><tr><th>#</th><th>Topic</th><th>Step</th></tr></thead>
          <tbody>%s</tbody>
        </table>
      </div>''' % (html.escape(title), rows))
    return '\n'.join(out)


def readme():
    plain = lambda s: re.sub(r'\*\*(.+?)\*\*', r'\1', s).replace(' ▸ ', ' > ')
    lines = ['EXPORT SELECTED TO DXF - HOW TO INSTALL', '=' * 40, '',
             'Documentation: https://swami-claude-skills.github.io/fusion-export-selected-to-dxf/', '',
             'Pick ONE of the three ways below.', '']
    for n, (_, title, note, steps) in enumerate(METHODS, 1):
        lines += ['%d. %s' % (n, title.upper()), '   ' + plain(note), '']
        for i, (_, s) in enumerate(steps, 1):
            lines.append('   %d) %s' % (i, plain(s)))
        lines.append('')
    lines += ['UPDATING', '   When a newer version is out, the panel shows a green banner. Click "install update",',
              '   then in Scripts and Add-Ins turn the Run switch for ExportSelectedToDXF off, then on.', '']
    return '\r\n'.join(lines)


def splice(t, name, block):
    b, e = '<!-- %s:BEGIN -->' % name, '<!-- %s:END -->' % name
    if b not in t:
        sys.exit('%s markers not found' % name)
    i, j = t.index(b) + len(b), t.index(e)
    return t[:i] + '\n' + block + '\n' + t[j:]


def main():
    for page in sys.argv[1:]:
        t = open(page, encoding='utf-8').read()
        t = splice(t, 'INSTALL-PANEL', panel())
        t = splice(t, 'INSTALL-TABLES', tables())
        open(page, 'w', encoding='utf-8').write(t)
        print(page, 'install steps updated')
    open(os.path.join(ROOT, 'ExportSelectedToDXF', 'READ ME FIRST.txt'), 'w', encoding='utf-8', newline='').write(readme())
    print('READ ME FIRST.txt written')


if __name__ == '__main__':
    main()
