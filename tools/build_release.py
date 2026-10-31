#!/usr/bin/env python3
"""Build the release zip and refresh version.json for ExportSelectedToDXF.

Usage:  python3 tools/build_release.py "One-line release notes"

- Reads VERSION from ExportSelectedToDXF/ExportSelectedToDXF.py and checks the manifest agrees.
- Writes dist/ExportSelectedToDXF.zip (one folder, installers inside) with a fixed name,
  so https://github.com/<repo>/releases/latest/download/ExportSelectedToDXF.zip always
  serves the newest release.
- Rewrites version.json, which the add-in reads to tell users a newer version exists.
"""
import json, os, re, sys, zipfile, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ADDIN = os.path.join(ROOT, 'ExportSelectedToDXF')
REPO = 'swami-claude-skills/fusion-export-selected-to-dxf'


def main():
    notes = sys.argv[1] if len(sys.argv) > 1 else ''
    py = open(os.path.join(ADDIN, 'ExportSelectedToDXF.py'), encoding='utf-8').read()
    version = re.search(r"^VERSION\s*=\s*'([^']+)'", py, re.M).group(1)
    man = json.load(open(os.path.join(ADDIN, 'ExportSelectedToDXF.manifest'), encoding='utf-8'))
    if man.get('version') != version:
        sys.exit('version mismatch: .py=%s manifest=%s' % (version, man.get('version')))

    dist = os.path.join(ROOT, 'dist')
    os.makedirs(dist, exist_ok=True)
    zpath = os.path.join(dist, 'ExportSelectedToDXF.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(ADDIN):
            dirs[:] = sorted(d for d in dirs if d != '__pycache__')
            for f in sorted(files):
                if f.endswith('.pyc') or f == '.DS_Store':
                    continue
                full = os.path.join(base, f)
                arc = os.path.relpath(full, ROOT)
                info = zipfile.ZipInfo(arc, date_time=(2026, 1, 1, 0, 0, 0))
                info.external_attr = (0o755 if f.endswith('.command') else 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, open(full, 'rb').read())

    vj = {
        'version': version,
        'date': datetime.date.today().strftime('%b %d, %Y').replace(' 0', ' '),
        'notes': notes,
        'zip': 'https://github.com/%s/releases/latest/download/ExportSelectedToDXF.zip' % REPO,
        'dashboard': 'https://swami-claude-skills.github.io/fusion-export-selected-to-dxf/',
    }
    with open(os.path.join(ROOT, 'version.json'), 'w', encoding='utf-8') as f:
        json.dump(vj, f, indent=2)
        f.write('\n')
    print('built', zpath, os.path.getsize(zpath), 'bytes; version.json ->', version)


if __name__ == '__main__':
    main()
