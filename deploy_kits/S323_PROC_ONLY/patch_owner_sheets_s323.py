#!/root/wa/venv/bin/python3
# =============================================================================
#  patch_owner_sheets_s323.py  ·  Session 269  ·  S323_PROC_ONLY  ·  v1
#
#  HIS WORDS, 19-Sep-2026, after the procedures landed:
#    "the xray section is done, no need on page, obstructs flow · in cast / slab
#     side column - no need to turn it off · consumables are same and to be
#     accepted as such · each one has a display with its abbreviation first, and
#     name in brackets as in A/E (Above elbow) · and in xrays, ask side to be
#     there where relevant"
#
#  FOUR PAGE CHANGES, all of them removals -- the page gets shorter, not longer:
#
#   1. THE X-RAY SECTION COMES OFF THE PAGE. It is finished; twenty lines above
#      the procedures is twenty lines in his way. The page now opens on the
#      procedures alone, with one line saying the X-rays are done and a link that
#      still opens them when he wants them (?kind=xray).
#   2. NO TURN-OFF ON A SIDE THAT IS ALWAYS ASKED. A line that asks right / left
#      simply says "R / L". Only a line that does NOT ask carries a small button,
#      so he can switch one on -- never off, because a cast is always one side.
#   3. THE CONSUMABLES BECOME READ-ONLY. "consumables are same and to be accepted
#      as such": the list still shows under each procedure, with the sizes and the
#      way each is asked, but the remove buttons and the add box are gone.
#   4. The naming is data, not code (update_proc_s323.py).
#
#  The item/add and item/drop routes stay in place, unused by the page: a route
#  that answers is not a fault, and the next screen may want them. Nothing about
#  the gate, the prices or his approvals changes.
# =============================================================================
import hashlib
import os
import py_compile
import shutil
import sys
import tempfile
import time

TARGET = "/root/finance/owner_sheets.py"
FROM_MD5 = "70963a9175a1e9f16f83f71ff66c3d68"
MARK = "S323"

EDITS = [
    # 1 · the page shows the procedures; the X-rays only on ?kind=xray
    ('    body = []\n'
     '    for kind, label in KINDS:\n'
     '        rows = [r for r in all_rows if r["kind"] == kind]',
     '    body = []\n'
     '    # S323: his words -- "the xray section is done, no need on page, obstructs\n'
     '    # flow". The procedures are the work now; the X-rays stay one click away.\n'
     '    only = "xray" if request.args.get("kind") == "xray" else "proc"\n'
     '    for kind, label in KINDS:\n'
     '        if kind != only:\n'
     '            continue\n'
     '        rows = [r for r in all_rows if r["kind"] == kind]'),
    # 2 · the line that replaces it, and the way back
    ('    body.append("<div class=\'card\'><h2>Add one that is not on either list</h2>"',
     '    xc = counts(con, "xray" if only == "proc" else "proc")\n'
     '    body.append("<div class=\'card\'><p class=\'mut\'>%s</p></div>"\n'
     '                % (("The X-ray list is done and is off this page — %d line(s), "\n'
     '                    "%d approved. <a href=\'?kind=xray\'>Open the X-rays</a> if you need them."\n'
     '                    % (xc["pending"] + xc["approved"] + xc["rejected"], xc["approved"]))\n'
     '                   if only == "proc" else\n'
     '                   "<a href=\'?\'>&larr; Back to the procedures</a>"))\n'
     '    body.append("<div class=\'card\'><h2>Add one that is not on either list</h2>"'),
    # 3 · a side that is asked is stated, not offered for switching off
    ('        asks = (s_.get("side") or "") == "ask"                        # S322\n'
     '        side_cell = ("<span class=\'%s\'>%s</span> "\n'
     '                     "<form class=\'inline\' method=\'post\' action=\'side\'>"\n'
     '                     "<input type=\'hidden\' name=\'id\' value=\'%d\'>"\n'
     '                     "<input type=\'hidden\' name=\'ask\' value=\'%s\'>"\n'
     '                     "<button class=\'lite\' type=\'submit\'>%s</button></form>"\n'
     '                     % ("yes" if asks else "mut", "R / L asked" if asks else "no side",\n'
     '                        s_["id"], "0" if asks else "1",\n'
     '                        "turn off" if asks else "turn on"))',
     '        asks = (s_.get("side") or "") == "ask"                        # S322\n'
     '        # S323: no turn-off. A cast, a slab or an injection is always one side,\n'
     '        # so an asked side is a statement; only an unasked one offers a button.\n'
     '        side_cell = ("<span class=\'yes\'>R / L</span>" if asks else\n'
     '                     ("<form class=\'inline\' method=\'post\' action=\'side\'>"\n'
     '                      "<input type=\'hidden\' name=\'id\' value=\'%d\'>"\n'
     '                      "<input type=\'hidden\' name=\'ask\' value=\'1\'>"\n'
     '                      "<button class=\'lite\' type=\'submit\'>ask R / L</button></form>"\n'
     '                      % s_["id"]))'),
    # 4 · the consumables, read-only
    ('            lis = "".join(\n'
     '                "<li>%s%s <form class=\'inline\' method=\'post\' action=\'item/drop\'>"\n'
     '                "<input type=\'hidden\' name=\'id\' value=\'%d\'><button class=\'lite\' type=\'submit\'>remove</button>"\n'
     '                "</form></li>" % (_esc(i["item"]), _ask_text(i), i["id"]) for i in s_["items"]) \\\n'
     '                or "<li class=\'mut\'>nothing tracked</li>"\n'
     '            pick = ("<form class=\'inline\' method=\'post\' action=\'item/add\' style=\'margin-top:6px\'>"\n'
     '                    "<input type=\'hidden\' name=\'id\' value=\'%d\'>"\n'
     '                    "<input class=\'name\' name=\'item\' list=\'items\' placeholder=\'add an item\' required>"\n'
     '                    "<input class=\'q\' name=\'qty\' value=\'1\' inputmode=\'decimal\'>"\n'
     '                    "<button type=\'submit\'>Add</button></form>" % s_["id"])',
     '            # S323: "consumables are same and to be accepted as such" -- the list\n'
     '            # is shown and nothing on it is editable here.\n'
     '            lis = "".join("<li>%s%s</li>" % (_esc(i["item"]), _ask_text(i))\n'
     '                          for i in s_["items"]) or "<li class=\'mut\'>nothing tracked</li>"\n'
     '            pick = ""'),
]


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def apply_to_text(text):
    if MARK in text:
        return text, ["ALREADY -- this file already carries the S323 change"]
    if "S322" not in text:
        return None, ["this file does not carry S322 yet -- install S322 first"]
    msgs = []
    for i, (anchor, repl) in enumerate(EDITS, 1):
        n = text.count(anchor)
        if n != 1:
            return None, ["edit %d: its anchor appears %d time(s), not once -- refusing" % (i, n)]
        text = text.replace(anchor, repl, 1)
        msgs.append("edit %d applied" % i)
    return text.replace("# S322", "# S322 / S323", 1), msgs


def main(argv):
    mode = "--check" if "--check" in argv else ("--apply" if "--apply" in argv else "")
    target = TARGET
    for a in argv[1:]:
        if a.startswith("--file="):
            target = a.split("=", 1)[1]
    if not mode:
        print("usage: patch_owner_sheets_s323.py --check|--apply [--file=PATH]")
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
    bak = "%s.bak_S323_%s" % (target, time.strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(target, bak)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(target) or ".", prefix=".s323_")
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
