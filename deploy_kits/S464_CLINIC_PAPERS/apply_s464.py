#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s464.py -- S464_CLINIC_PAPERS (D664, session 292, 03-Oct-2026): three small edits to asset_register.py.

Built from the real file (/root/assetapp/asset_register.py at 446c671d, as S441 left it). Everything D664 does lives
in a NEW file beside it, clinic_papers.py; this only (1) mounts that file by one guarded import at the foot,
(2) puts two links on the Purchases page and (3) one line on the bill page -- both behind 'is defined', so the asset
app's pages do not need the new file. No lane, no status, no intake and no existing route is changed.
Each anchor must be found exactly once; anything else leaves the file as it was.   usage: apply_s464.py <asset_register.py>
"""
import hashlib
import sys

FROM = "446c671ddc7589fa8b367c463d49cbaa"
EDITS = []


def ed(name, old, new):
    EDITS.append((name, old, new))


ed("the mount, at the foot",
   '    return "ok", 200, {"Content-Type": "text/plain"}\n'
   '\n\n'
   '# ---------------------------------------------------------------- main\n',
   '    return "ok", 200, {"Content-Type": "text/plain"}\n'
   '\n\n'
   '# --- S464_CLINIC_PAPERS begin -- D664: clinic consumables by group, the papers to sort (owner, 03-Oct-2026) ---\n'
   '# Guarded: if clinic_papers.py is absent or cannot load, this app runs exactly as before -- its two links on the\n'
   '# Purchases page and its line on the bill page are behind \'is defined\'.\n'
   'try:\n'
   '    _d664_here = os.path.dirname(os.path.abspath(__file__))\n'
   '    if _d664_here not in _sys.path:\n'
   '        _sys.path.insert(0, _d664_here)\n'
   '    import clinic_papers as _clinic_papers\n'
   '    _clinic_papers.init(_sys.modules[__name__])\n'
   'except Exception as _ex_d664:                                  # noqa: BLE001\n'
   '    print("clinic_papers NOT mounted: %s" % _ex_d664, file=_sys.stderr)\n'
   '# --- S464_CLINIC_PAPERS end ---\n'
   '\n\n'
   '# ---------------------------------------------------------------- main\n')

ed("the Purchases page: two links",
   '''<a class="btn small" href="{{url_for('intake')}}">\U0001F4F7 Scan intake</a>\n''',
   '''<a class="btn small" href="{{url_for('intake')}}">\U0001F4F7 Scan intake</a>\n'''
   '''{% if d664_to_sort is defined %}<a class="btn small" href="{{url_for('d664_papers')}}">Clinic papers to sort'''
   '''{% set _d664n = d664_to_sort() %}{% if _d664n %} ({{_d664n}}){% endif %}</a> '''
   '''<a class="btn small" href="{{url_for('d664_month')}}">Clinic consumables by month</a>{% endif %}\n''')

ed("the bill page: its group",
   '''<b>Kind:</b> {{b['kind']}}<br>\n''',
   '''<b>Kind:</b> {{b['kind']}}<br>\n'''
   '''{% if d664_group_label is defined and (b['lane'] or 'clinic')=='clinic' and b['status']!='rejected' %}'''
   '''<b>Group:</b> {{d664_group_label(b) or 'not sorted yet'}} <a class="btn small" href="{{url_for('d664_paper',bid=b['id'],back=(request.script_root or '')~request.path)}}">'''
   '''{{'change' if d664_group_label(b) else 'choose'}}</a><br>{% endif %}\n''')


def apply(src):
    for name, old, new in EDITS:
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! anchor '%s' found %d time(s), expected 1 - nothing written" % (name, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s464.py <path to asset_register.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("asset_register.py %s -> %s (%d edits; %+d bytes)"
          % (have[:8], hashlib.md5(out).hexdigest()[:8], len(EDITS), len(out) - len(raw)))


if __name__ == "__main__":
    main()
