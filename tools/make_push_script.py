#!/usr/bin/env python3
"""Print a Fusion Python script that installs the working-copy add-in straight into
Fusion's AddIns folder (no zip download, so macOS Gatekeeper never sees it).

Usage:  python3 tools/make_push_script.py > /tmp/push.py   (then run it in Fusion)
"""
import base64, os, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ADDIN = os.path.join(ROOT, 'ExportSelectedToDXF')

files = {}
for base, dirs, names in os.walk(ADDIN):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for n in names:
        if n.endswith('.pyc') or n == '.DS_Store':
            continue
        full = os.path.join(base, n)
        files[os.path.relpath(full, ADDIN)] = base64.b64encode(
            zlib.compress(open(full, 'rb').read(), 9)).decode()

print('''import os, base64, zlib, hashlib
FILES = %r
dst = os.path.expanduser('~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/ExportSelectedToDXF')
if os.name == 'nt':
    dst = os.path.join(os.environ['APPDATA'], 'Autodesk', 'Autodesk Fusion 360', 'API', 'AddIns', 'ExportSelectedToDXF')
for rel, data in FILES.items():
    path = os.path.join(dst, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    raw = zlib.decompress(base64.b64decode(data))
    tmp = path + '.tmp'
    open(tmp, 'wb').write(raw)
    os.replace(tmp, path)
    if rel.endswith('.command'):
        os.chmod(path, 0o755)
print('installed %%d files to %%s' %% (len(FILES), dst))
''' % files)
