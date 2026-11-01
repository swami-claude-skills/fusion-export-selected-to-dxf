#!/usr/bin/env python3
"""Keep the documentation dashboard in step with the add-in.

Usage:  python3 tools/build_docs.py PAGE.html [PAGE2.html ...]

For each page it:
- fills every <!--VERSION-->...<!--/VERSION--> with the add-in's VERSION,
- fills every <!--DATE-->...<!--/DATE--> with that version's release date
  (the "Released:" line of notes/vX.Y.Z.md, else today),
- rebuilds the What's New section between <!-- WHATSNEW:BEGIN --> and
  <!-- WHATSNEW:END --> from notes/v*.md, newest first,
- sets <meta name="addin-version" content="X.Y.Z">, which the release workflow
  checks so a release can't go out with documentation for an older version.
"""
import datetime, html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
NOTES = os.path.join(ROOT, 'notes')
ADDIN_PY = os.path.join(ROOT, 'ExportSelectedToDXF', 'ExportSelectedToDXF.py')


def addin_version():
    src = open(ADDIN_PY, encoding='utf-8').read()
    return re.search(r"^VERSION\s*=\s*'([^']+)'", src, re.M).group(1)


def vkey(v):
    return tuple(int(x) for x in re.findall(r'\d+', v)[:3])


def inline(md):
    """Escape, then apply **bold**, `code` and [text](url)."""
    t = html.escape(md, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)',
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    return t


def parse_note(path):
    lines = open(path, encoding='utf-8').read().splitlines()
    date, summary, items = '', '', []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = re.match(r'Released:\s*(.+)$', line)
        if m:
            date = m.group(1).strip()
            continue
        m = re.match(r'\*\*Export Selected.*?v[\d.]+\*\*:\s*(.*)$', line)
        if m and not summary:
            summary = m.group(1).strip()
            continue
        if re.match(r'\*\*Download:\*\*', line) or re.fullmatch(r'\*\*[^*]+\*\*', line):
            continue                                   # download hint / bare sub-heading
        m = re.match(r'[-*]\s+\*\*(.+?)\*\*\s*(.*)$', line)
        if m:                                          # - **Lead.** rest
            items.append((m.group(1).rstrip('.:'), m.group(2)))
            continue
        m = re.match(r'[-*]\s+(.*)$', line)
        if m:
            items.append(('Change', m.group(1)))
            continue
        m = re.match(r'\*\*(.+?):\*\*\s*(.*)$', line)
        if m:                                          # **Upgrading ...:** rest
            items.append((m.group(1), m.group(2)))
            continue
        items.append(('Note', line))
    return date, summary, items


def whatsnew_html():
    files = [f for f in os.listdir(NOTES) if re.fullmatch(r'v\d+\.\d+\.\d+\.md', f)]
    files.sort(key=lambda f: vkey(f), reverse=True)
    out, dates = [], {}
    for f in files:
        v = f[:-3]
        date, summary, items = parse_note(os.path.join(NOTES, f))
        dates[v] = date
        lis = ''.join('<li><span class="tid">%s</span>%s</li>' % (html.escape(lead), inline(rest))
                      for lead, rest in items)
        out.append('      <div class="callout"><span class="lbl">%s%s</span>%s%s</div>' % (
            v, (' · ' + html.escape(date)) if date else '', inline(summary),
            ('<ul>%s</ul>' % lis) if lis else ''))
    return '\n'.join(out), dates


def build(page, version, block, date):
    t = open(page, encoding='utf-8').read()
    b, e = '<!-- WHATSNEW:BEGIN -->', '<!-- WHATSNEW:END -->'
    if b not in t or e not in t:
        sys.exit('%s: What\'s New markers not found' % page)
    i, j = t.index(b) + len(b), t.index(e)
    t = t[:i] + '\n' + block + '\n' + t[j:]
    t = re.sub(r'<!--VERSION-->.*?<!--/VERSION-->', '<!--VERSION-->%s<!--/VERSION-->' % version, t, flags=re.S)
    t = re.sub(r'<!--DATE-->.*?<!--/DATE-->', '<!--DATE-->%s<!--/DATE-->' % date, t, flags=re.S)
    meta = '<meta name="addin-version" content="%s">' % version
    if re.search(r'<meta name="addin-version" content="[^"]*">', t):
        t = re.sub(r'<meta name="addin-version" content="[^"]*">', meta, t)
    else:
        t = t.replace('<head>', '<head>\n' + meta, 1)
    open(page, 'w', encoding='utf-8').write(t)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    version = addin_version()
    block, dates = whatsnew_html()
    if ('v' + version) not in dates:
        sys.exit('notes/v%s.md is missing: write the release notes first' % version)
    date = dates.get('v' + version) or datetime.date.today().strftime('%b %d, %Y').replace(' 0', ' ')
    for page in sys.argv[1:]:
        build(page, version, block, date)
        print('%s -> v%s (%s), %d releases in What\'s New' % (page, version, date, len(dates)))


if __name__ == '__main__':
    main()
