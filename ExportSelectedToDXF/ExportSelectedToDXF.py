# ExportSelectedToDXF — Fusion add-in (Swami house spec)
# Exports whatever is selected (sketch curves, whole sketches, planar faces, solid bodies,
# flat patterns) to one DXF per item, from a non-modal dark palette.

import adsk.core, adsk.fusion, traceback
import os, json, copy, re, subprocess, sys, threading, urllib.request, webbrowser
import io, shutil, zipfile, datetime, platform

# ---- single source of truth for the version (must match the .manifest) ----
VERSION    = '1.5.1'
TOOL_NAME  = 'ExportSelectedToDXF'
TITLE      = 'Export Selected to DXF'
CMD_ID     = 'ExportSelectedToDXF_cmd'
PALETTE_ID = 'ExportSelectedToDXF_palette'
UPDATE_EVENT_ID = 'ExportSelectedToDXF_updateInfo'

# ---- where the latest version and the dashboard live (GitHub) ----
REPO          = 'swami-claude-skills/fusion-export-selected-to-dxf'
VERSION_URL   = 'https://raw.githubusercontent.com/%s/main/version.json' % REPO
DOWNLOAD_URL  = 'https://github.com/%s/releases/latest/download/ExportSelectedToDXF.zip' % REPO
DASHBOARD_URL = 'https://swami-claude-skills.github.io/fusion-export-selected-to-dxf/'
RELEASES_URL  = 'https://github.com/%s/releases' % REPO
PLACEMENTS = [
    ('FusionSolidEnvironment', 'SolidCreatePanel'),          # DESIGN > SOLID > CREATE
    ('FusionSolidEnvironment', 'SolidScriptsAddinsPanel'),   # DESIGN > UTILITIES > ADD-INS
]
LEGACY_NAME = 'ExportSelectedDXF'   # name used before v1.2.0; settings are carried over once

_HERE = os.path.dirname(os.path.realpath(__file__))
PALETTE_URL = os.path.join(_HERE, 'palette.html')

app = adsk.core.Application.get()
ui  = app.userInterface
_handlers = []
_last_results = []
_update_info = {'state': 'unchecked'}
_update_event = None
_LOG = []                 # recent log entries shown in the panel
_LOG_LOCK = threading.Lock()
LOG_KEEP = 300            # entries kept in memory / sent to the panel
LOG_FILE_MAX = 400_000    # bytes before log.txt rolls over to log.old.txt

# ---- factory defaults = schema. Every persisted value lives here. ----
DEFAULTS = {
    'options': {
        'folder': os.path.join(os.path.expanduser('~'), 'Desktop', 'DXF Export'),
        'units': 'design',            # design | mm | cm | m | in | ft
        'naming': 'component_item',   # component_item | item
        'overwrite': False,           # False = add -2, -3 ... instead of replacing
        'openFolder': True,
        'construction': False,        # export construction geometry (sketches)
        'points': False,              # export sketch points
        'projected': True,            # export projected geometry
        'bendLines': True,            # flat pattern center (bend) lines
        'extentLines': False,         # flat pattern bend extent lines
        'splinesToPolylines': False,  # flat pattern only
        'polyTolerance': 0.01,        # in mm
        'checkUpdates': True,         # look for a newer version when the panel opens
    },
    'ui': {'collapsed': {'export': False, 'output': True, 'sketch': True, 'flat': True, 'updates': True,
                         'results': True, 'log': True, 'about': True}},
}


def _data_root():
    return os.environ.get('APPDATA', os.path.expanduser('~')) if os.name == 'nt' \
        else os.path.expanduser('~/Library/Application Support')


def _data_dir():
    """Per-user folder outside the add-in (settings, update backups); survives reinstalls."""
    d = os.path.join(_data_root(), 'SwamiFusionAddins', TOOL_NAME)
    os.makedirs(d, exist_ok=True)
    return d


def _settings_path():
    path = os.path.join(_data_dir(), 'settings.json')
    old = os.path.join(_data_root(), 'SwamiFusionAddins', LEGACY_NAME, 'settings.json')
    if not os.path.exists(path) and os.path.exists(old):
        try:
            shutil.copyfile(old, path)
        except Exception:
            pass
    return path


def _deep_merge(b, o):
    out = copy.deepcopy(b)
    for k, v in (o or {}).items():
        out[k] = _deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_settings():
    try:
        with open(_settings_path(), 'r', encoding='utf-8') as f:
            saved = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        saved = {}
    return _deep_merge(DEFAULTS, saved)


def save_settings(state):
    with open(_settings_path(), 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


STATE = load_settings()

# ============================== CORE START ==============================
# Pure export logic. Takes a list of selected entities + an options dict,
# returns one result dict per exported item (or skipped entity).

_UNIT_MAP = {
    'mm': 'MillimeterDistanceUnits', 'cm': 'CentimeterDistanceUnits',
    'm': 'MeterDistanceUnits', 'in': 'InchDistanceUnits', 'ft': 'FootDistanceUnits',
}


def _units_enum(code):
    name = _UNIT_MAP.get(code)
    return getattr(adsk.fusion.DistanceUnits, name) if name else None


def _safe(name):
    name = re.sub(r'[\\/:*?"<>|]+', '_', name or 'unnamed').strip()
    return name or 'unnamed'


def _target_path(folder, comp_name, item_name, opts):
    base = _safe(item_name) if opts.get('naming') == 'item' or not comp_name \
        else '%s - %s' % (_safe(comp_name), _safe(item_name))
    path = os.path.join(folder, base + '.dxf')
    if not opts.get('overwrite'):
        k = 2
        while os.path.exists(path):
            path = os.path.join(folder, '%s-%d.dxf' % (base, k))
            k += 1
    return path


def _native(e):
    try:
        n = e.nativeObject
        return n if n else e
    except Exception:
        return e


def _export_sketch(design, sketch, path, opts, projected_override=None):
    """Export a sketch with ExportManager; fall back to the retired saveAsDXF."""
    em = design.exportManager
    try:
        o = em.createDXFSketchExportOptions(path, sketch)
    except Exception:
        o = None
    if o:
        u = _units_enum(opts.get('units'))
        if u is not None:
            o.units = u
        o.isConstructionExported = bool(opts.get('construction'))
        o.isPointsExported = bool(opts.get('points'))
        o.isProjectedGeometryExported = bool(opts.get('projected')) \
            if projected_override is None else projected_override
        if not em.execute(o):
            raise RuntimeError('Fusion reported the DXF export failed')
        return 'export options'
    if not sketch.saveAsDXF(path):
        raise RuntimeError('Fusion reported the DXF save failed')
    return 'saveAsDXF (design units, all geometry)'


def _face_export(design, face, path, opts):
    """Temporary sketch on the face, export its outline, delete the sketch.
    Fusion auto-projects the face's edges when the sketch is made; project only if it didn't."""
    tmp = design.rootComponent.sketches.add(face)
    try:
        tmp.name = '_ExportSelectedToDXF_temp'
        if tmp.sketchCurves.count == 0:
            try:
                tmp.project2([face], False)
            except Exception:
                tmp.project(face)
        if tmp.sketchCurves.count == 0:
            raise RuntimeError('no edges could be taken from the face')
        how = _export_sketch(design, tmp, path, opts, projected_override=True)
        return tmp.sketchCurves.count, how
    finally:
        try:
            tmp.deleteMe()
        except Exception:
            pass


def _partial_sketch_export(design, sketch, curves, path, opts):
    """Copy the chosen curves (sketch coordinates kept) into a temporary sketch, export, delete it."""
    comp = sketch.parentComponent
    tmp = comp.sketches.add(comp.xYConstructionPlane)
    try:
        tmp.name = '_ExportSelectedToDXF_temp'
        coll = adsk.core.ObjectCollection.create()
        for c in curves:
            coll.add(c)
        sketch.copy(coll, adsk.core.Matrix3D.create(), tmp)
        if tmp.sketchCurves.count == 0:
            raise RuntimeError('the selected curves could not be copied')
        how = _export_sketch(design, tmp, path, opts, projected_override=True)
        return tmp.sketchCurves.count, how
    finally:
        try:
            tmp.deleteMe()
        except Exception:
            pass


def _sheet_metal_body(comp):
    """First sheet-metal body in a component, or None."""
    try:
        for b in comp.bRepBodies:
            if getattr(b, 'isSheetMetal', False):
                return b
    except Exception:
        pass
    return None


def _flat_job(e):
    """For a sheet-metal selection, describe how to get its flat pattern:
    {'fp': existing FlatPattern or None, 'comp': component, 'body': native sheet-metal body}.
    Returns None when the selection isn't sheet metal."""
    t = e.objectType
    if t == adsk.fusion.FlatPattern.classType():
        fp = adsk.fusion.FlatPattern.cast(e)
        return {'fp': fp, 'comp': fp.parentComponent, 'body': None}
    comp, body = None, None
    if t == adsk.fusion.BRepBody.classType():
        body = _native(adsk.fusion.BRepBody.cast(e))
        if not getattr(body, 'isSheetMetal', False):
            return None
        comp = body.parentComponent
    elif t == adsk.fusion.Occurrence.classType():
        comp = adsk.fusion.Occurrence.cast(e).component
    elif t == adsk.fusion.Component.classType():
        comp = adsk.fusion.Component.cast(e)
    if comp is None:
        return None
    fp = None
    try:
        fp = comp.flatPattern
    except Exception:
        fp = None
    if fp is None:
        body = body or _sheet_metal_body(comp)
        if body is None:
            return None
    return {'fp': fp, 'comp': comp, 'body': body}


def _export_flat(design, fp, path, opts):
    em = design.exportManager
    o = em.createDXFFlatPatternExportOptions(path, fp)
    u = _units_enum(opts.get('units'))
    if u is not None:
        o.units = u
    o.isCenterLinesExported = bool(opts.get('bendLines'))
    o.isExtentLinesExported = bool(opts.get('extentLines'))
    o.isSplineConvertedToPolyline = bool(opts.get('splinesToPolylines'))
    if opts.get('splinesToPolylines'):
        o.convertToPolylineTolerance = float(opts.get('polyTolerance') or 0.01) / 10.0  # mm -> cm
    if not em.execute(o):
        raise RuntimeError('Fusion reported the flat pattern export failed')


def _largest_planar_face(body):
    """The biggest flat face of a solid body: usually the outline to cut."""
    best, area = None, -1.0
    for f in body.faces:
        if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType and f.area > area:
            best, area = f, f.area
    return best


def classify(entities):
    """Group a raw selection into export jobs without touching the design."""
    sketches, order, faces, flats, skipped = {}, [], [], [], []
    seen_fp = set()
    for e in entities:
        t = e.objectType
        try:
            if t == adsk.fusion.Sketch.classType():
                sk = _native(e)
                key = sk.entityToken
                if key not in sketches:
                    sketches[key] = {'sketch': sk, 'curves': [], 'whole': True}
                    order.append(key)
                else:
                    sketches[key]['whole'] = True
                continue
            ps = getattr(e, 'parentSketch', None)
            if ps is not None and 'Sketch' in t:
                if 'SketchPoint' in t or 'Dimension' in t or 'Constraint' in t or 'SketchText' in t:
                    skipped.append({'name': t.split('::')[-1], 'reason': 'not a curve'})
                    continue
                n = _native(e)
                sk = n.parentSketch
                key = sk.entityToken
                if key not in sketches:
                    sketches[key] = {'sketch': sk, 'curves': [], 'whole': False}
                    order.append(key)
                sketches[key]['curves'].append(n)
                continue
            if t == adsk.fusion.BRepFace.classType():
                f = adsk.fusion.BRepFace.cast(e)
                if f.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
                    skipped.append({'name': 'face', 'reason': 'not planar'})
                else:
                    faces.append((f, None))
                continue
            job = _flat_job(e)
            if job is not None:
                key = job['comp'].entityToken
                if key not in seen_fp:
                    seen_fp.add(key)
                    flats.append(job)
                continue
            if t == adsk.fusion.BRepBody.classType():
                f = _largest_planar_face(adsk.fusion.BRepBody.cast(e))
                if f is None:
                    skipped.append({'name': e.name, 'reason': 'body has no flat face'})
                else:
                    faces.append((f, e.name))
                continue
            skipped.append({'name': getattr(e, 'name', '') or t.split('::')[-1],
                            'reason': 'unsupported type (%s)' % t.split('::')[-1]})
        except Exception as ex:
            skipped.append({'name': t.split('::')[-1], 'reason': str(ex).strip().splitlines()[-1]})
    return [sketches[k] for k in order], faces, flats, skipped


def summarize(entities):
    sk, faces, flats, skipped = classify(entities)
    whole = sum(1 for s in sk if s['whole'] or len(s['curves']) == s['sketch'].sketchCurves.count)
    return {'count': len(entities), 'sketches': whole, 'partial': len(sk) - whole,
            'faces': sum(1 for f in faces if not f[1]), 'bodies': sum(1 for f in faces if f[1]),
            'flats': len(flats), 'skipped': len(skipped)}


def export_entities(design, entities, opts):
    folder = os.path.expanduser(opts.get('folder') or DEFAULTS['options']['folder'])
    os.makedirs(folder, exist_ok=True)
    jobs, faces, flats, skipped = classify(entities)
    results = []

    for j in jobs:
        sk = j['sketch']
        comp = sk.parentComponent
        total = sk.sketchCurves.count
        n = len(j['curves'])
        r = {'kind': 'sketch', 'name': sk.name, 'component': comp.name}
        try:
            if j['whole'] or n == 0 or n >= total:
                path = _target_path(folder, comp.name, sk.name, opts)
                r['how'] = _export_sketch(design, sk, path, opts)
                r['curves'] = total
            else:
                path = _target_path(folder, comp.name, sk.name + ' (selected)', opts)
                r['curves'], r['how'] = _partial_sketch_export(design, sk, j['curves'], path, opts)
                r['kind'] = 'curves'
                r['note'] = '%d of %d curves' % (n, total)
            r['file'] = path
            r['ok'] = True
        except Exception as ex:
            r['ok'] = False
            r['error'] = str(ex).strip().splitlines()[-1]
        results.append(r)

    root = design.rootComponent
    for i, (f, body_label) in enumerate(faces, 1):
        try:
            body = f.body
            comp_name = _native(body).parentComponent.name
            item = body_label or '%s face %d' % (body.name, i)
        except Exception:
            comp_name, item = root.name, body_label or 'face %d' % i
        r = {'kind': 'body (largest flat face)' if body_label else 'face', 'name': item, 'component': comp_name}
        try:
            path = _target_path(folder, comp_name, item, opts)
            r['curves'], r['how'] = _face_export(design, f, path, opts)
            r['file'] = path
            r['ok'] = True
        except Exception as ex:
            r['ok'] = False
            r['error'] = str(ex).strip().splitlines()[-1]
        results.append(r)

    for job in flats:
        comp = job['comp']
        comp_name = getattr(comp, 'name', '') or ''
        r = {'kind': 'flat pattern', 'name': 'Flat Pattern', 'component': comp_name}
        fp = job['fp']
        try:
            path = _target_path(folder, comp_name, 'Flat Pattern', opts)
            if fp is None:
                # No flat pattern yet: create one (largest flat face stays put) and keep it,
                # exactly like Fusion's own Create Flat Pattern. Deleting it again through the
                # API leaves Fusion's sheet-metal state inconsistent, so it is left in place.
                face = _largest_planar_face(job['body'])
                if face is None:
                    raise RuntimeError('the sheet-metal body has no flat face to unfold from')
                fp = comp.createFlatPattern(face)
                if fp is None:
                    raise RuntimeError('Fusion could not create a flat pattern for this part')
                r['note'] = 'flat pattern created'
            _export_flat(design, fp, path, opts)
            r['file'] = path
            r['ok'] = True
        except Exception as ex:
            r['ok'] = False
            r['error'] = str(ex).strip().splitlines()[-1]
        results.append(r)

    for s in skipped:
        results.append({'kind': 'skipped', 'name': s['name'], 'ok': False, 'error': s['reason']})
    for r in results:
        if r.get('file') and os.path.exists(r['file']):
            r['bytes'] = os.path.getsize(r['file'])
            r['fileName'] = os.path.basename(r['file'])
    return folder, results
# =============================== CORE END ===============================


def _palette():
    return ui.palettes.itemById(PALETTE_ID)


def _vtuple(v):
    return tuple(int(x) for x in re.findall(r'\d+', str(v))[:3]) or (0,)


def _check_update_thread():
    """Runs off the main thread: fetch version.json, then hand the result back to
    Fusion's main thread through a custom event (the API is not thread-safe)."""
    info = {'state': 'error', 'current': VERSION}
    try:
        req = urllib.request.Request(VERSION_URL, headers={'User-Agent': TOOL_NAME + '/' + VERSION,
                                                           'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode('utf-8'))
        latest = str(data.get('version', '')).strip()
        info = {'current': VERSION, 'latest': latest,
                'state': 'newer' if _vtuple(latest) > _vtuple(VERSION) else 'current',
                'zip': data.get('zip') or DOWNLOAD_URL,
                'dashboard': data.get('dashboard') or DASHBOARD_URL,
                'notes': data.get('notes', ''), 'date': data.get('date', '')}
    except Exception as ex:
        info['error'] = str(ex).strip().splitlines()[-1] if str(ex).strip() else type(ex).__name__
    try:
        app.fireCustomEvent(UPDATE_EVENT_ID, json.dumps(info))
    except Exception:
        pass


def _start_update_check():
    global _update_info
    _update_info = {'state': 'checking', 'current': VERSION}
    _push('update', _update_info)
    threading.Thread(target=_check_update_thread, daemon=True).start()


# ---- self-update: download the latest zip and replace this add-in's own files ----
def _apply_update(zip_bytes, target_dir, backup_root, current_version, tool_name=None):
    """Check the package, back up target_dir, then overwrite its files with the zip's.
    Pure Python (no Fusion API) so it can be tested anywhere. Returns (new_version, backup_dir)."""
    tool_name = tool_name or TOOL_NAME
    try:
        z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        raise RuntimeError('the download was not a zip file (GitHub may be unreachable; try again later)')
    prefix = tool_name + '/'
    names = [n for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')]
    main_py, manifest = prefix + tool_name + '.py', prefix + tool_name + '.manifest'
    if main_py not in names or manifest not in names:
        raise RuntimeError('the download is not a %s package' % tool_name)
    for n in names:
        parts = n[len(prefix):].split('/')
        if any(p in ('', '..') for p in parts) or ':' in n or n.startswith('/'):
            raise RuntimeError('the download contains an unsafe path: %s' % n)
    m = re.search(r"^VERSION\s*=\s*'([^']+)'", z.read(main_py).decode('utf-8'), re.M)
    new_version = m.group(1) if m else ''
    if _vtuple(new_version) <= _vtuple(current_version):
        raise RuntimeError('the download (v%s) is not newer than v%s' % (new_version or '?', current_version))
    if not os.access(target_dir, os.W_OK):
        raise RuntimeError('the add-in folder is not writable: %s' % target_dir)
    backup = os.path.join(backup_root, 'backup-v' + current_version)
    if os.path.exists(backup):
        shutil.rmtree(backup)
    shutil.copytree(target_dir, backup, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    try:
        for n in names:
            dest = os.path.join(target_dir, *n[len(prefix):].split('/'))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            tmp = dest + '.updating'
            with open(tmp, 'wb') as f:
                f.write(z.read(n))
            os.replace(tmp, dest)
            if dest.endswith('.command'):
                os.chmod(dest, 0o755)
    except Exception:
        shutil.copytree(backup, target_dir, dirs_exist_ok=True)   # put the old files back
        raise
    return new_version, backup


def _install_update_thread():
    info = dict(_update_info)
    try:
        req = urllib.request.Request(DOWNLOAD_URL, headers={'User-Agent': TOOL_NAME + '/' + VERSION})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        new_version, backup = _apply_update(data, _HERE, _data_dir(), VERSION)
        info.update({'state': 'installed', 'installed': new_version, 'backup': backup})
    except Exception as ex:
        msg = str(ex).strip().splitlines()[-1] if str(ex).strip() else type(ex).__name__
        info.update({'state': 'installFailed', 'error': msg})
    try:
        app.fireCustomEvent(UPDATE_EVENT_ID, json.dumps(info))
    except Exception:
        pass


def _start_install_update():
    global _update_info
    latest = _update_info.get('latest', '')
    res = ui.messageBox('Install %s v%s now?\n\nIt replaces this add-in\'s files with the latest '
                        'version from GitHub. Your current version is backed up first, and your '
                        'settings are kept.' % (TITLE, latest or 'latest'),
                        TITLE, adsk.core.MessageBoxButtonTypes.YesNoButtonType)
    if res != adsk.core.DialogResults.DialogYes:
        return
    log('info', 'Installing update v%s...' % (latest or 'latest'))
    _update_info = dict(_update_info, state='installing')
    _push('update', _update_info)
    threading.Thread(target=_install_update_thread, daemon=True).start()


def _open_url(url):
    try:
        webbrowser.open(url)
    except Exception:
        if sys.platform == 'darwin':
            subprocess.Popen(['open', url])
        elif os.name == 'nt':
            os.startfile(url)


def _push(action, payload):
    p = _palette()
    if p:
        p.sendInfoToHTML(action, json.dumps(payload))


def _push_error(msg):
    log('error', msg.strip().splitlines()[-1] if msg.strip() else msg)
    _push('error', {'msg': msg})


# ---- activity log: shown in the panel's Log section and written to log.txt ----
def _log_path():
    return os.path.join(_data_dir(), 'log.txt')


def log(level, msg):
    """level: info | ok | warn | error. Safe from any thread; only the main thread pushes to the panel."""
    now = datetime.datetime.now()
    entry = {'t': now.strftime('%H:%M:%S'), 'd': now.strftime('%b %d'), 'level': level, 'msg': str(msg)}
    with _LOG_LOCK:
        _LOG.append(entry)
        del _LOG[:-LOG_KEEP]
        try:
            path = _log_path()
            if os.path.exists(path) and os.path.getsize(path) > LOG_FILE_MAX:
                os.replace(path, os.path.join(_data_dir(), 'log.old.txt'))
            with open(path, 'a', encoding='utf-8') as f:
                f.write('%s  %-5s  %s\n' % (now.strftime('%Y-%m-%d %H:%M:%S'), level.upper(), msg))
        except Exception:
            pass
    if threading.current_thread() is threading.main_thread():
        try:
            _push('log', entry)
        except Exception:
            pass


def _log_results(results):
    for r in results:
        name = r.get('fileName') or ('%s - %s' % (r.get('component'), r.get('name')) if r.get('component') else r.get('name'))
        if r.get('ok'):
            extra = r.get('note') or ('%s curves' % r['curves'] if r.get('curves') is not None else '')
            log('ok', '%s: %s%s' % (r.get('kind'), name, (' (%s)' % extra) if extra else ''))
        elif r.get('kind') == 'skipped':
            log('warn', 'skipped %s: %s' % (name, r.get('error')))
        else:
            log('error', '%s %s failed: %s' % (r.get('kind'), name, r.get('error')))


FIT_EXTRA = 0    # the page measures its own end exactly (Fusion's Close bar sits outside the page)


def _canvas_rect():
    """(left, top, width, height) of Fusion's canvas in palette-position units, or None.
    The canvas origin comes from viewToScreen(0,0); its size from the viewport, which is
    in the same units as palette positions (checked on a Retina Mac)."""
    try:
        vp = app.activeViewport
        tl = vp.viewToScreen(adsk.core.Point2D.create(0, 0))
        if not tl or vp.width <= 0 or vp.height <= 0:
            return None
        return int(tl.x), int(tl.y), int(vp.width), int(vp.height)
    except Exception:
        return None


def _place_top_right(p, margin=12):
    """Put the floating palette in the top-right corner of Fusion's canvas."""
    r = _canvas_rect()
    if not r:
        return
    left, top, width, _ = r
    try:
        p.setPosition(left + width - p.width - margin, top + margin)
    except Exception:
        pass


def _fit_palette(data):
    """Resize the palette so its height matches the open sections (floating palettes;
    a docked palette may keep the height its dock gives it). Uses the page's own
    measurement of how much it overflows (or has spare), so no guess about the
    palette's title bar is needed; the page re-measures after each resize."""
    p = _palette()
    if not p:
        return
    content = int(data.get('content') or 0)
    inner = int(data.get('inner') or 0)
    if content <= 0 or inner <= 0:
        return
    cap = 1100
    r = _canvas_rect()
    if r:   # never taller than the room between the panel's top and the bottom of the canvas
        cap = max(300, r[1] + r[3] - p.top - 12)
    before = p.height
    target = max(240, min(before + (content + FIT_EXTRA - inner), cap))
    if abs(target - before) > 3:
        p.setSize(p.width, target)
    applied = abs(p.height - target) <= 3
    try:   # keep the last 40 adjustments for troubleshooting
        path = os.path.join(_data_dir(), 'fit_debug.json')
        try:
            hist = json.load(open(path, encoding='utf-8'))
            hist = hist if isinstance(hist, list) else [hist]
        except Exception:
            hist = []
        hist.append({'t': datetime.datetime.now().strftime('%H:%M:%S'), 'content': content, 'inner': inner,
                     'before': before, 'target': target, 'after': p.height, 'cap': cap,
                     'docking': int(p.dockingState)})
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(hist[-40:], f)
    except Exception:
        pass
    return applied


def _current_entities():
    sels = ui.activeSelections
    return [sels.item(i).entity for i in range(sels.count)]


def _selection_summary():
    try:
        if not adsk.fusion.Design.cast(app.activeProduct):
            return {'count': 0, 'noDesign': True}
        return summarize(_current_entities())
    except Exception:
        return {'count': 0}


def _open_folder(folder):
    try:
        if sys.platform == 'darwin':
            subprocess.Popen(['open', folder])
        elif os.name == 'nt':
            os.startfile(folder)
    except Exception:
        pass


def _do_export():
    global _last_results
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError('Switch to the DESIGN workspace first.')
    ents = _current_entities()
    if not ents:
        raise RuntimeError('Nothing selected. Select sketch curves, sketches, planar faces, bodies or flat patterns.')
    opts = STATE['options']
    log('info', 'Export started: %d selected, units %s, to %s' % (len(ents), opts.get('units'), opts.get('folder')))
    folder, results = export_entities(design, ents, opts)
    _last_results = results
    _log_results(results)
    ok = sum(1 for r in results if r.get('ok'))
    log('ok' if ok == len(results) else 'warn', 'Export finished: %d of %d written' % (ok, len(results)))
    if opts.get('openFolder') and any(r.get('ok') for r in results):
        _open_folder(folder)
    return {'folder': folder, 'results': results}


class CmdCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            palette = _palette()
            if palette is None:
                palette = ui.palettes.add(PALETTE_ID, '%s (v%s)' % (TITLE, VERSION), PALETTE_URL,
                                          True, True, True, 380, 640)
                # Left floating: a docked palette's height is locked, which stops the panel
                # from fitting its contents. It opens in the top-right corner of the canvas.
                _place_top_right(palette)
                h = HtmlHandler();   palette.incomingFromHTML.add(h); _handlers.append(h)
                c = ClosedHandler(); palette.closed.add(c);           _handlers.append(c)
            else:
                palette.isVisible = not palette.isVisible
        except:
            ui.messageBox('%s: %s' % (TITLE, traceback.format_exc()))


class HtmlHandler(adsk.core.HTMLEventHandler):
    def notify(self, args):
        global STATE
        try:
            action = args.action
            data = json.loads(args.data) if args.data else {}
            if action in ('ready', 'getState'):
                shown = copy.deepcopy(STATE)
                shown['ui']['collapsed'] = copy.deepcopy(DEFAULTS['ui']['collapsed'])   # always open as default
                args.returnData = json.dumps({'version': VERSION, 'name': TITLE, 'state': shown,
                                              'selection': _selection_summary(),
                                              'results': _last_results,
                                              'update': _update_info,
                                              'log': list(_LOG),
                                              'links': {'dashboard': DASHBOARD_URL,
                                                        'download': DOWNLOAD_URL,
                                                        'releases': RELEASES_URL}})
                if action == 'ready' and STATE['options'].get('checkUpdates') \
                        and _update_info.get('state') == 'unchecked':
                    _start_update_check()
            elif action == 'setState':
                STATE = _deep_merge(STATE, data)
                save_settings(STATE)
                args.returnData = 'OK'
            elif action == 'selection':
                args.returnData = json.dumps(_selection_summary())
            elif action == 'browse':
                dlg = ui.createFolderDialog()
                dlg.title = 'Export DXF files to'
                start = os.path.expanduser(STATE['options'].get('folder') or '')
                if os.path.isdir(start):
                    dlg.initialDirectory = start
                if dlg.showDialog() == adsk.core.DialogResults.DialogOK:
                    STATE['options']['folder'] = dlg.folder
                    save_settings(STATE)
                    log('info', 'Export folder set to ' + dlg.folder)
                args.returnData = json.dumps({'folder': STATE['options']['folder']})
            elif action == 'openFolder':
                f = os.path.expanduser(STATE['options'].get('folder') or '')
                if os.path.isdir(f):
                    _open_folder(f)
                    args.returnData = 'OK'
                else:
                    args.returnData = json.dumps({'error': 'Folder does not exist yet: ' + f})
            elif action == 'openUrl':
                url = str(data.get('url', ''))
                if url.startswith('https://github.com/') or url.startswith('https://swami-claude-skills.github.io/'):
                    _open_url(url)
                args.returnData = 'OK'
            elif action == 'fitHeight':
                args.returnData = json.dumps({'applied': bool(_fit_palette(data))})
            elif action == 'clearLog':
                with _LOG_LOCK:
                    _LOG.clear()
                args.returnData = 'OK'
            elif action == 'openLog':
                path = _log_path()
                if not os.path.exists(path):
                    log('info', 'Log file created')
                _open_folder(path)
                args.returnData = json.dumps({'path': path})
            elif action == 'checkUpdate':
                _start_update_check()
                args.returnData = 'OK'
            elif action == 'installUpdate':
                _start_install_update()
                args.returnData = 'OK'
            elif action == 'export':
                try:
                    args.returnData = json.dumps(_do_export())
                except Exception as ex:
                    msg = str(ex).strip().splitlines()[-1]
                    log('error', 'Export stopped: ' + msg)
                    args.returnData = json.dumps({'error': msg})
            elif action == 'reset':
                res = ui.messageBox('Reset all %s settings to defaults? This cannot be undone.' % TITLE,
                                    TITLE, adsk.core.MessageBoxButtonTypes.YesNoButtonType)
                if res == adsk.core.DialogResults.DialogYes:
                    STATE = copy.deepcopy(DEFAULTS)
                    save_settings(STATE)
                    log('info', 'Settings reset to defaults')
                    _push('stateChanged', {'version': VERSION, 'name': TITLE, 'state': STATE})
                args.returnData = 'OK'
        except:
            _push_error(traceback.format_exc())


class SelectionChangedHandler(adsk.core.ActiveSelectionEventHandler):
    def notify(self, args):
        try:
            p = _palette()
            if p and p.isVisible:
                _push('selection', _selection_summary())
        except:
            pass


class UpdateInfoHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        global _update_info
        try:
            _update_info = json.loads(args.additionalInfo or '{}')
            st = _update_info.get('state')
            if st == 'current':
                log('info', 'Update check: v%s is the latest' % VERSION)
            elif st == 'newer':
                log('info', 'Update check: v%s is available (you have v%s)' % (_update_info.get('latest'), VERSION))
            elif st == 'error':
                log('warn', 'Update check failed: %s' % _update_info.get('error'))
            elif st == 'installed':
                log('ok', 'Installed v%s (backup of v%s kept). Turn Run off and on in Shift+S to use it.' % (_update_info.get('installed'), VERSION))
            elif st == 'installFailed':
                log('error', 'Update install failed: %s' % _update_info.get('error'))
            _push('update', _update_info)
        except:
            pass


class ClosedHandler(adsk.core.UserInterfaceGeneralEventHandler):
    def notify(self, args):
        try:
            save_settings(STATE)
        except:
            pass


def run(context):
    global _update_event
    try:
        log('info', '%s v%s started (Fusion %s, %s %s)' % (TITLE, VERSION, app.version, platform.system(), platform.release()))
        try:
            app.unregisterCustomEvent(UPDATE_EVENT_ID)
        except Exception:
            pass
        _update_event = app.registerCustomEvent(UPDATE_EVENT_ID)
        u = UpdateInfoHandler(); _update_event.add(u); _handlers.append(u)
        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def is None:
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                CMD_ID, TITLE,
                'Export the selected sketch curves, sketches, planar faces and flat patterns '
                'as one DXF file per item.',
                './resources/command')
        h = CmdCreatedHandler(); cmd_def.commandCreated.add(h); _handlers.append(h)
        s = SelectionChangedHandler(); ui.activeSelectionChanged.add(s); _handlers.append(s)
        for ws_id, panel_id in PLACEMENTS:
            ws = ui.workspaces.itemById(ws_id)
            panel = ws.toolbarPanels.itemById(panel_id) if ws else None
            if panel and panel.controls.itemById(CMD_ID) is None:
                panel.controls.addCommand(cmd_def)
    except:
        ui.messageBox('%s run: %s' % (TITLE, traceback.format_exc()))


def stop(context):
    try:
        for h in _handlers:
            if isinstance(h, SelectionChangedHandler):
                try:
                    ui.activeSelectionChanged.remove(h)
                except Exception:
                    pass
        for ws_id, panel_id in PLACEMENTS:
            ws = ui.workspaces.itemById(ws_id)
            panel = ws.toolbarPanels.itemById(panel_id) if ws else None
            ctrl = panel.controls.itemById(CMD_ID) if panel else None
            if ctrl:
                ctrl.deleteMe()
        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()
        palette = _palette()
        if palette:
            palette.deleteMe()
        try:
            app.unregisterCustomEvent(UPDATE_EVENT_ID)
        except Exception:
            pass
        _handlers.clear()
    except:
        if ui:
            ui.messageBox('%s stop: %s' % (TITLE, traceback.format_exc()))
