#!/root/wa/venv/bin/python3
# =============================================================================
#  patch_owner_sheets_s321.py  ·  Session 269  ·  S321_XRAY_VIEWS  ·  v1
#
#  THE OWNER PRESSED APPROVE AND GOT "page not accessible". THE BUTTONS HAVE
#  NEVER WORKED, AND THE WALK DID NOT NOTICE BECAUSE IT POSTED THE URLS ITSELF.
#
#  Every form on the page carries a RELATIVE action -- action="status",
#  action="rename", action="price", action="add", action="item/add". The page is
#  served at /finance/clinic/sheets WITHOUT a trailing slash (the tile links
#  there, and the route exists both ways). A browser resolves a relative action
#  against the directory of the current URL, so it drops the last segment:
#
#      page  /finance/clinic/sheets   +  action "status"
#         -> POST /finance/clinic/status        <-- does not exist, 404
#
#  With a trailing slash it would have worked, which is why it was never seen in
#  testing. The fix is ONE LINE that makes every relative action resolve from the
#  page's own folder, whichever way the page was reached:
#
#      <base href="/finance/clinic/sheets/">
#
#  Chosen over rewriting eleven action attributes because it cannot miss one, and
#  because any form added later is fixed in advance. BASE is taken from the same
#  url_prefix the blueprint is mounted at, so the two can never disagree.
#
#  Second edit, his words of 19-Sep: the page states his own price rule, so he
#  does not have to hold it in his head while he edits.
# =============================================================================
import hashlib
import os
import py_compile
import shutil
import sys
import tempfile
import time

TARGET = "/root/finance/owner_sheets.py"
FROM_MD5 = "5705f7ff7d6257b478dbb1d8ba16522d"
MARK = "S321"

EDITS = [
    # 1 · BASE, beside the other module constants
    ('KINDS = (("xray", "X-ray"), ("proc", "Procedure"))',
     'KINDS = (("xray", "X-ray"), ("proc", "Procedure"))\n'
     '# S321: the folder every relative form action on this page resolves against.\n'
     '# Set from the blueprint\'s own url_prefix in init(), with the trailing slash\n'
     '# a browser needs -- see the header of patch_owner_sheets_s321.py.\n'
     'BASE = "/finance/clinic/sheets/"'),
    # 2 · keep BASE and the mount in step
    ('    global _db, _require, _audit, UNIT\n'
     '    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit\n'
     '    app.register_blueprint(bp, url_prefix=url_prefix)',
     '    global _db, _require, _audit, UNIT, BASE\n'
     '    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit\n'
     '    BASE = (url_prefix or "").rstrip("/") + "/"          # S321\n'
     '    app.register_blueprint(bp, url_prefix=url_prefix)'),
    # 3 · put the base tag in the page's head
    ('%s%s<p class="mut"><a href="/portal">&larr; Portal</a></p></body></html>""" % (note, body)',
     '%s%s<p class="mut"><a href="/portal">&larr; Portal</a></p></body></html>""" % (note, body)\n'
     '    # S321: every form on this page posts to a RELATIVE action, and without this\n'
     '    # tag a browser drops the last path segment and posts to a route that does\n'
     '    # not exist (the owner got "page not accessible" on Approve, 19-Sep).\n'
     '    return html.replace(\'<meta charset="utf-8">\',\n'
     '                        \'<meta charset="utf-8"><base href="%s">\' % BASE, 1)'),
    # 4 · the return becomes an assignment (part of edit 3's pair)
    ('    return """<!doctype html><html lang="en"><head><meta charset="utf-8">',
     '    html = """<!doctype html><html lang="en"><head><meta charset="utf-8">'),
    # 5 · his price rule, on the page
    ('                   ("Read out of your own X-ray register \\u2014 6,177 entries reduced to these, "\n'
     '                    "spellings corrected, the word X-ray dropped.") if kind == "xray" else',
     '                   ("Read out of your own X-ray register \\u2014 6,177 entries reduced to these, "\n'
     '                    "spellings corrected, the word X-ray dropped. Default prices follow your own "\n'
     '                    "rule: one view 300 \\u00b7 two views 500 \\u00b7 on 11 x 14 film 400 and 600 \\u00b7 "\n'
     '                    "wrist three views 800. Change any of them here.") if kind == "xray" else'),
]


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def apply_to_text(text):
    if MARK in text:
        return text, ["ALREADY -- this file already carries the S321 change"]
    msgs = []
    for i, (anchor, repl) in enumerate(EDITS, 1):
        n = text.count(anchor)
        if n != 1:
            return None, ["edit %d: its anchor appears %d time(s), not once -- refusing" % (i, n)]
        text = text.replace(anchor, repl, 1)
        msgs.append("edit %d applied" % i)
    return text, msgs


def main(argv):
    mode = "--check" if "--check" in argv else ("--apply" if "--apply" in argv else "")
    target = TARGET
    for a in argv[1:]:
        if a.startswith("--file="):
            target = a.split("=", 1)[1]
    if not mode:
        print("usage: patch_owner_sheets_s321.py --check|--apply [--file=PATH]")
        return 2
    if not os.path.isfile(target):
        print("RED -- %s is not there" % target)
        return 3
    before = md5_file(target)
    with open(target, "r", encoding="utf-8") as fh:
        text = fh.read()
    print("    file  : %s (md5 %s)" % (target, before))
    if MARK not in text and before != FROM_MD5:
        print("    note  : not the pinned %s -- anchors decide, not the pin" % FROM_MD5[:8])
    new, msgs = apply_to_text(text)
    for m in msgs:
        print("      " + m)
    if new is None:
        print("RESULT RED -- nothing written")
        return 4
    if new == text:
        print("RESULT ALREADY -- nothing to change")
        return 0
    if mode == "--check":
        print("RESULT PENDING -- --apply would write the edits above")
        return 0
    bak = "%s.bak_S321_%s" % (target, time.strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(target, bak)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(target) or ".", prefix=".s321_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(new)
    try:
        py_compile.compile(tmp, cfile=tmp + ".pyc", doraise=True)
    except py_compile.PyCompileError as ex:
        os.unlink(tmp)
        print("RESULT RED -- the patched file does not compile: %s" % ex)
        return 5
    finally:
        if os.path.exists(tmp + ".pyc"):
            os.unlink(tmp + ".pyc")
    shutil.copymode(target, tmp)
    os.replace(tmp, target)
    print("    backup: %s" % bak)
    print("    pin   : %s -> %s" % (before, md5_file(target)))
    print("RESULT APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
