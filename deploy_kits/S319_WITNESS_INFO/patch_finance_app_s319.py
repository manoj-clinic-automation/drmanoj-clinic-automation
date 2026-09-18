#!/root/wa/venv/bin/python3
# =============================================================================
#  patch_finance_app_s319.py  ·  Session 269 (parent)  ·  S319_WITNESS_INFO  ·  v1
#
#  THE NEVER-FIRED WITNESS NAMES TWO ROWS THAT CANNOT FIRE BY DESIGN, EVERY DAY,
#  AND SO TEACHES THE OWNER TO SKIP ITS LIST.
#
#  D525, answered at S269 by reading the code: of the seven keys the witness
#  names, `flags` (11885-11897) and `margqueue` (11874-11880) have NO warn or bad
#  branch at all. That is deliberate -- the S195 ruling is quoted above the
#  margqueue call: "a known, planned waiting state must not drive the portal
#  tile, or the tile becomes wallpaper". So they will sit in the witness's list
#  for ever, and the witness exists to catch the opposite thing: a check whose
#  red branch cannot be reached (AF-2, born dead at S195, green for five
#  sessions).
#
#  THE CHANGE. A declared set, HEALTH_INFO_ONLY, excluded from the witness's
#  eligibility -- and the card says so in its own hint, naming them, so nobody
#  has to read this code to know why five and not seven.
#
#  WHAT IT DOES NOT DO. It does not stop tracking them: the INSERT OR IGNORE and
#  the non-ok counter above are untouched, so if either ever DID gain a red
#  branch its history is already there. It does not touch any other check, and it
#  does not change one word of what the seven cards themselves say.
#
#  Anchored on the live file's own text, idempotent, and it refuses on any anchor
#  not found exactly once. The pin is advisory (S315 moved this file); the
#  anchors decide.
# =============================================================================
import hashlib
import os
import py_compile
import shutil
import sys
import tempfile
import time

TARGET = "/root/finance/finance_app.py"
FROM_MD5_SEEN = ("8dc77ef48c96bec7382f1c8aaf40f38e",   # the 18-Sep 01:35 bundle
                 "c9f73b181d3b28b93d71aa3781addb61")  # after S315
MARK = "HEALTH_INFO_ONLY"

DECL = '''RENEWALS_WINDOW_DAYS = 30       # the tile line's window (owner spec, Task #8)

# --- S319 (D525): CHECKS THAT ARE INFORMATIONAL BY DESIGN ---------------------
#  The never-fired witness in B2 below exists to catch a check whose RED branch
#  cannot be reached -- AF-2 was born dead at S195 and stayed green for five
#  sessions. Two rows on this page have no red branch ON PURPOSE, by the S195
#  ruling quoted above the margqueue card ("a known, planned waiting state must
#  not drive the portal tile, or the tile becomes wallpaper"):
#
#     flags      -- "Notes, not failures"; only ok or info is ever added
#     margqueue  -- bills with no clinic ID, parked for the Docterz cross-match
#
#  Left in, they are named by the witness every single day, and a list that is
#  always the same is a list nobody reads -- the very alert fatigue that ruling
#  was written to prevent. Excluded here BY NAME, so that every key the witness
#  does name is one that COULD have gone red and did not.
#
#  A key belongs in this set only when the code above has no warn/bad branch for
#  it AT ALL. A check that is merely quiet does not belong here: backup, outbox
#  and watcher stay in, and at S269 watcher was the finding precisely because its
#  red branch is nearly unreachable in practice (S269 evidence paper, D525).
HEALTH_INFO_ONLY = ("flags", "margqueue")'''

OLD_FILTER = '''        _never = [r["key"] for r in con.execute(
            "SELECT key, first_seen FROM health_check_seen WHERE nonok_count=0")
            if r["key"] in _keys
            and (dt.datetime.fromisoformat(_nowi[:19])
                 - dt.datetime.fromisoformat(r["first_seen"][:19])).days >= 14]'''

NEW_FILTER = '''        _never = [r["key"] for r in con.execute(
            "SELECT key, first_seen FROM health_check_seen WHERE nonok_count=0")
            if r["key"] in _keys
            and r["key"] not in HEALTH_INFO_ONLY          # S319 (D525)
            and (dt.datetime.fromisoformat(_nowi[:19])
                 - dt.datetime.fromisoformat(r["first_seen"][:19])).days >= 14]'''

OLD_HINT = '''                "Either they guard something that never breaks, or they are dead "
                "and cannot say so. AF-2 was born dead and stayed green for five "
                "sessions. Worth one look each, once.")'''

NEW_HINT = '''                "Either they guard something that never breaks, or they are dead "
                "and cannot say so. AF-2 was born dead and stayed green for five "
                "sessions. Worth one look each, once. "
                + ("The %d row(s) that are informational by design (%s) are not "
                   "counted here -- they have no red branch at all, on purpose."
                   % (len(HEALTH_INFO_ONLY), ", ".join(HEALTH_INFO_ONLY))))'''

EDITS = [("RENEWALS_WINDOW_DAYS = 30       # the tile line's window (owner spec, Task #8)", DECL),
         (OLD_FILTER, NEW_FILTER),
         (OLD_HINT, NEW_HINT)]


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def apply_to_text(text):
    if MARK in text:
        return text, ["ALREADY -- this file already carries the S319 change"]
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
        print("usage: patch_finance_app_s319.py --check|--apply [--file=PATH]")
        return 2
    if not os.path.isfile(target):
        print("RED -- %s is not there" % target)
        return 3
    before = md5_file(target)
    with open(target, "r", encoding="utf-8") as fh:
        text = fh.read()
    print("    file  : %s (md5 %s)" % (target, before))
    if MARK not in text and before not in FROM_MD5_SEEN:
        print("    note  : an unseen pin -- anchors decide, not the pin")
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
    bak = "%s.bak_S319_%s" % (target, time.strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(target, bak)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(target), prefix=".s319_")
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
    after = md5_file(target)
    print("    backup: %s" % bak)
    print("    pin   : %s -> %s" % (before, after))
    print("RESULT APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
