#!/root/wa/venv/bin/python3
# =============================================================================
#  patch_owner_sheets_s322.py  ·  Session 269  ·  S322_PROC_SIDE  ·  v1
#
#  HIS WORDS, 19-Sep-2026 (capitals his):
#    "NOW GIVE ONLY THE PROCEDURES, SECTION WISE, WITH FIBRE WORD IN ALL CAST AND
#     SLABS, AND EACH VARIANT IN PLASTERS SHD HAVE CAST AND SLAB, AS BOTH CARRY
#     DIFFERENT CHARGE, AND THE ILI SECTION SHD HAVE RIGHT / LEFT SIDE OPTION,
#     AND SO SHD BE FOR THE XRAYS WHEREVER APPLICABLE"
#
#  The naming and the cast/slab split are data (update_proc_s322.py). This file
#  adds the one thing the page cannot express yet: WHETHER A LINE ASKS WHICH SIDE.
#
#  Side is NOT two more rows. A left knee cast and a right knee cast are the same
#  line at the same charge, so doubling the list would double his reading for
#  nothing -- and the side is only known when the patient is in front of him. So
#  each line carries a marker, he can flip it on any row, and the chamber screen
#  asks R / L at the time for the lines that carry it.
#
#  Five anchored edits: the column (through the migration table that already
#  exists, so an old database gains it on the next page load), the field in the
#  row reader, a setter, its route, and one more column on the table.
# =============================================================================
import hashlib
import os
import py_compile
import shutil
import sys
import tempfile
import time

TARGET = "/root/finance/owner_sheets.py"
FROM_MD5 = "a4e8694e20cf93ae1a1a19953db355cc"
MARK = "S322"

EDITS = [
    # 1 · the column, added by the existing idempotent migration
    ('            ("owner_service_item", "ask", "TEXT NOT NULL DEFAULT \'\'"),',
     '            ("owner_service", "side", "TEXT NOT NULL DEFAULT \'\'"),      # S322: \'\' or \'ask\'\n'
     '            ("owner_service_item", "ask", "TEXT NOT NULL DEFAULT \'\'"),'),
    # 2 · carry it into the row the page renders
    ('                     "grp": r["grp"], "forms": r["forms"], "source": r["source"],',
     '                     "grp": r["grp"], "forms": r["forms"], "source": r["source"],\n'
     '                     "side": r["side"],                                  # S322\n'),
    # 3 · the setter, beside set_active
    ('def set_status(con, who, sid, status):',
     'def set_side(con, who, sid, ask):\n'
     '    """S322: does this line ask which side, right or left? His tap, per row.\n'
     '    Side is never part of the name and never a second row -- the two sides are\n'
     '    one line at one charge, and which side it was belongs to the visit, not to\n'
     '    the list."""\n'
     '    ensure(con)\n'
     '    con.execute("UPDATE owner_service SET side=?, updated_by=?, updated_ts=? WHERE id=?",\n'
     '                ("ask" if ask else "", who, _now(), sid))\n'
     '    con.commit()\n'
     '    return "ask" if ask else ""\n'
     '\n'
     '\n'
     'def set_status(con, who, sid, status):'),
    # 4 · its route
    ('@bp.route("/item/add", methods=["POST"])',
     '@bp.route("/side", methods=["POST"])\n'
     'def route_side():\n'
     '    who, err = _owner()\n'
     '    if err:\n'
     '        return err\n'
     '    on = set_side(_db(), who, int(request.form.get("id", "0")),\n'
     '                  request.form.get("ask") == "1")\n'
     '    return _back("Side asked." if on else "Side not asked.")\n'
     '\n'
     '\n'
     '@bp.route("/item/add", methods=["POST"])'),
    # 5 · the column on the table: header, the cell, and the group row's span
    ('    out = ["<table class=\'grid\'><tr><th>%s</th><th>Price</th><th>%s</th><th>Your call</th></tr>"',
     '    out = ["<table class=\'grid\'><tr><th>%s</th><th>Price</th><th>Side</th>"\n'
     '           "<th>%s</th><th>Your call</th></tr>"'),
    ('            out.append("<tr><td colspan=\'4\' class=\'grp\'>%s</td></tr>" % _esc(last_grp))',
     '            out.append("<tr><td colspan=\'5\' class=\'grp\'>%s</td></tr>" % _esc(last_grp))'),
    ('        out.append("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"\n'
     '                   % (cls, name, price, third, call))',
     '        asks = (s_.get("side") or "") == "ask"                        # S322\n'
     '        side_cell = ("<span class=\'%s\'>%s</span> "\n'
     '                     "<form class=\'inline\' method=\'post\' action=\'side\'>"\n'
     '                     "<input type=\'hidden\' name=\'id\' value=\'%d\'>"\n'
     '                     "<input type=\'hidden\' name=\'ask\' value=\'%s\'>"\n'
     '                     "<button class=\'lite\' type=\'submit\'>%s</button></form>"\n'
     '                     % ("yes" if asks else "mut", "R / L asked" if asks else "no side",\n'
     '                        s_["id"], "0" if asks else "1",\n'
     '                        "turn off" if asks else "turn on"))\n'
     '        out.append("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"\n'
     '                   % (cls, name, price, side_cell, third, call))'),
]


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def apply_to_text(text):
    if MARK in text:
        return text, ["ALREADY -- this file already carries the S322 change"]
    if "S321" not in text:
        return None, ["this file does not carry S321 yet -- install S321 first"]
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
        print("usage: patch_owner_sheets_s322.py --check|--apply [--file=PATH]")
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
    bak = "%s.bak_S322_%s" % (target, time.strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(target, bak)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(target) or ".", prefix=".s322_")
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
