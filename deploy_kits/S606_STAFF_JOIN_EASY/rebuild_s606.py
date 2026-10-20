#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""rebuild_s606.py -- kit S606: rebuild the two changed live files from the LIVE bytes,
by exact counted edits, and compare with the kit's copies.  READ ONLY on the live files.

    python3 rebuild_s606.py LIVE_DIR KIT_DIR OUT_DIR
Exit 0 = the kit's staff_pages.py and staff_manage.html are exactly live + these edits.
"""
import hashlib
import os
import sys

live, kit, out = sys.argv[1:4]
EDITS = {
    "staff_pages.py": [(
        'def init(app, require_fn):\n'
        '    global _require\n'
        '    _require = require_fn\n'
        '    app.register_blueprint(bp)\n'
        '    return bp\n',
        'def init(app, require_fn):\n'
        '    global _require\n'
        '    _require = require_fn\n'
        '    app.register_blueprint(bp)\n'
        '    # S606 (S331, 20-Oct-2026): the two-touch Add-staff flow at /finance/staff/new.\n'
        '    # Mounted from here so finance_app.py is not touched; if it fails to load, the\n'
        '    # old ladder above still mounts and the failure is printed to the journal.\n'
        '    try:\n'
        '        import staff_easy\n'
        '        staff_easy.init(app, require_fn)\n'
        '    except Exception as ex:                       # never take the old page down with it\n'
        '        import sys\n'
        '        print("staff_easy (S606) NOT mounted: %r" % (ex,), file=sys.stderr)\n'
        '    return bp\n')],
    "staff_manage.html": [(
        '<h1>Staff — joining and leaving</h1>\n',
        '<h1>Staff — joining and leaving</h1>\n'
        '<div class="sec" style="border-color:#2e6b34;background:#eef5ef"><b>New, simpler way to add staff:</b>'
        ' one form, then the machine. <a class="btn primary" href="/finance/staff/new">➕ Add staff</a></div>\n')],
}
bad = 0
os.makedirs(out, exist_ok=True)
for name, edits in EDITS.items():
    s = open(os.path.join(live, name), encoding="utf-8").read()
    for old, new in edits:
        n = s.count(old)
        if n != 1:
            print("  REFUSED %s: an anchor occurs %d times (expected 1)" % (name, n))
            bad += 1
            break
        s = s.replace(old, new)
    with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(os.path.join(out, name), "rb").read()).hexdigest()
    b = hashlib.md5(open(os.path.join(kit, name), "rb").read()).hexdigest()
    print("  %-18s rebuilt %s  kit %s  %s" % (name, a[:8], b[:8], "same" if a == b else "DIFFERENT"))
    bad += (a != b)
sys.exit(1 if bad else 0)
