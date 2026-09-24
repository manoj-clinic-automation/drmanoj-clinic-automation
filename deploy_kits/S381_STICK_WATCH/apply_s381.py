#!/usr/bin/env python3
"""apply_s381.py -- kit S381_STICK_WATCH (F-617). Anchored on the medical PC's marg_watch.py 9f0bf9c4 (S259).

THE OWNER, 24-Sep-2026: "I just exported a report from Marg and now it is saving to the pen drive which is
connected to the medical PC in the root and not to the previous location ... E:\\"

The watcher captures what Marg writes in D:\\MARGERP\\users, D:\\MARG REPORTS and C:\\Users\\Public\\MARG --
the three folders the agent hands it. E:\\ is the Marg backup stick, and nothing looked at it, so the export
went nowhere (heartbeat 07:36 IST: 0 captures today).

WHAT THIS DOES, AND WHAT IT DOES NOT
  * On the medical install ONLY (this file running from D:\\SendToClinic) the TOP LEVEL of E:\\ is swept on
    the watcher's own safety poll, every 5 seconds, beside the folders it already watches.
  * Only .xls / .xlsx / .pdf, only files written in the LAST 24 HOURS, never a subfolder. The stick carries
    the Marg backups and whatever else has been put on it; nothing older and nothing inside a folder is
    ever read, so nothing that was already there can be sent anywhere.
  * No event hook on the stick (a removable drive; the 5-second poll is the mechanism there). A stick that
    is not plugged in is simply skipped.
  * Everything else is byte-for-byte as it was: the three folders, the event capture, the dedup by content,
    the off switch, the pusher.
  * medical_agent.py is NOT touched -- the stick is added inside the watcher, so the agent's own list and
    its heartbeat stay as they are.

  python3 apply_s381.py --src marg_watch.py --out DIR
"""
import argparse, hashlib, os

ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
s = open(a.src, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "9f0bf9c4c5fc285d339541ef3c76179f", "marg_watch.py is not 9f0bf9c4 (S259)"


def rep(old, new):
    global s
    assert s.count(old) == 1, "anchor not unique or absent: " + old[:80]
    s = s.replace(old, new)


rep('''OFF SWITCH (S259)''', '''THE MARG BACKUP STICK (S381, 24-Sep-2026, F-617)
    Marg began saving an export to the root of the pen drive, E:\\\\, instead of its usual folder. On the
    medical install (this file in D:\\\\SendToClinic) the TOP LEVEL of E:\\\\ is swept too, on the safety
    poll: .xls/.xlsx/.pdf written in the last 24 hours only, never a subfolder, never an older file.
    Whatever else lives on the stick is never read, so it can never be sent.

OFF SWITCH (S259)''')

rep('''EXTS = (".xls", ".xlsx", ".pdf")''', '''EXTS = (".xls", ".xlsx", ".pdf")

# S381 (F-617) -- the Marg backup stick. Swept FLAT (its top level only) and only for files written in
# the last FLAT_FRESH_S seconds, and only when this file is the medical install. On any other machine --
# manojz runs its own copy of this file against the share -- the list is empty and nothing changes.
FLAT_ROOTS_MEDICAL = ["E:\\\\"]
FLAT_FRESH_S = 24 * 3600
ON_MEDICAL = os.path.normcase(os.path.abspath(HERE)) == os.path.normcase(r"D:\\SendToClinic")
FLAT_ROOTS = FLAT_ROOTS_MEDICAL if ON_MEDICAL else []''')

rep('''def list_exports(roots):
    files = []
    for root in roots:
        if os.path.isfile(root):
            files.append(root); continue
        for dirpath, _d, names in os.walk(root):
            files += [os.path.join(dirpath, n) for n in names if n.lower().endswith(EXTS)]
    return files''', '''def list_flat(root, now=None, fresh_s=FLAT_FRESH_S):
    """S381: the top level of ROOT only -- report files written in the last FRESH_S seconds. A folder,
    an older file, another extension or a drive that is not there: skipped, silently, every time."""
    got = []
    try:
        if not os.path.isdir(root):
            return got
        now = time.time() if now is None else now
        for n in os.listdir(root):
            if not n.lower().endswith(EXTS):
                continue
            p = os.path.join(root, n)
            try:
                if os.path.isfile(p) and now - os.path.getmtime(p) <= fresh_s:
                    got.append(p)
            except OSError:
                continue
    except OSError:
        return []
    return got


def list_exports(roots, flat=None):
    files = []
    for root in roots:
        if os.path.isfile(root):
            files.append(root); continue
        for dirpath, _d, names in os.walk(root):
            files += [os.path.join(dirpath, n) for n in names if n.lower().endswith(EXTS)]
    for root in (FLAT_ROOTS if flat is None else flat):       # S381: the backup stick, top level only
        files += list_flat(root)
    return files''')

rep('''    out("watching: %s" % ", ".join(roots))''',
    '''    out("watching: %s" % ", ".join(roots))
    if FLAT_ROOTS:
        out("stick   : %s top level only, files of the last %d h, on the %.0fs poll (S381)"
            % (", ".join(FLAT_ROOTS), FLAT_FRESH_S // 3600, poll_s))''')

rep('''    open(junk, "wb").write(body(b"D"))
    ck("...and IS captured once it is complete", capture(junk, spool, cap, lambda m: None) is True)
    shutil.rmtree(d, ignore_errors=True)''', '''    open(junk, "wb").write(body(b"D"))
    ck("...and IS captured once it is complete", capture(junk, spool, cap, lambda m: None) is True)

    # S381: the backup stick -- top level, fresh files, report extensions, and nothing else
    stick = os.path.join(d, "stick"); os.makedirs(os.path.join(stick, "old backups"))
    fresh = os.path.join(stick, "REPORT_1.XLS"); open(fresh, "wb").write(body(b"E"))
    stale = os.path.join(stick, "LAST MONTH.XLS"); open(stale, "wb").write(body(b"F"))
    os.utime(stale, (time.time() - 3 * 86400, time.time() - 3 * 86400))
    deep = os.path.join(stick, "old backups", "REPORT_2.XLS"); open(deep, "wb").write(body(b"G"))
    other = os.path.join(stick, "d1-sanjeevni.mbk"); open(other, "wb").write(b"backup")
    got = list_flat(stick)
    ck("the stick: a fresh export at its top level IS seen", fresh in got)
    ck("the stick: a file older than a day is NOT", stale not in got)
    ck("the stick: nothing inside a folder is read", deep not in got)
    ck("the stick: a Marg backup (.mbk) is never touched", other not in got and len(got) == 1)
    ck("the stick: an absent drive is skipped quietly", list_flat(os.path.join(d, "no such drive")) == [])
    ck("the stick: a sweep with it captures the fresh export",
       any(capture(p, spool, cap, lambda m: None) for p in list_exports([], flat=[stick])))
    shutil.rmtree(d, ignore_errors=True)''')

os.makedirs(a.out, exist_ok=True)
open(os.path.join(a.out, "marg_watch.py"), "w", encoding="utf-8", newline="\n").write(s)
print("marg_watch.py ->", hashlib.md5(s.encode("utf-8")).hexdigest())
