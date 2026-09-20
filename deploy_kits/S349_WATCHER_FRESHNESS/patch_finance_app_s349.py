#!/root/wa/venv/bin/python3
# =============================================================================
#  patch_finance_app_s349.py  ·  Session 276 (parent)  ·  S349_WATCHER_FRESHNESS  ·  v1
#
#  Three anchored edits on /root/finance/finance_app.py, FROM 7866b1ee (S342).
#  Every anchor was copied from the live bytes, reproduced offline from the
#  20-Sep 01:35 bundle through the S332 and S340 patchers (41e0ffb4 -> 3a871f53
#  -> 7866b1ee, byte-exact) and READ WHOLE this session (F-472; no inferred anchor).
#
#  1 · THE WATCHER ROW (D554, F-547). Until now a stale medical-PC heartbeat was
#      always "info", so the realistic failure -- the PC down or unreachable in
#      the middle of the clinic day -- could never turn the card red (the S202
#      false-green shape, named at S269). Now: stale heartbeat DURING THE CLINIC
#      DAY -> bad; outside it -> info, unchanged. The clinic day is the same two
#      settings the pull check already reads (pipeline.clinic_hour_from / _to,
#      defaults 9 and 21), on the server's IST clock; Sunday counts as out of
#      hours unless the setting pipeline.clinic_sunday is "1". The 'alive is
#      False' branch (red) and the 'alive is True' branch (ok) are untouched.
#  2 · ONE LINE on the health page's help box: a link to /finance/freshness.
#  3 · A GUARDED MOUNT (S209) for freshness_page.py after the S332 block --
#      the collector's own freshness table, served read-only (F-540).
#
#  Anchored, idempotent, refuses on any anchor that is not found exactly once.
# =============================================================================
import hashlib
import os
import py_compile
import shutil
import sys
import tempfile
import time

TARGET = "/root/finance/finance_app.py"
FROM_MD5 = "7866b1ee6e70d19b5c096ef1b0099bd3"
MARK = "S349_WATCHER_FRESHNESS"

EDITS = [
    # 1 · the stale-heartbeat branch of the watcher check
    ('            elif _hbstale:\n'
     '                add("watcher", "Medical PC capture", "info",\n'
     '                    "last heard from the medical PC %.1f hours ago — state unknown"\n'
     '                    % float(_hbage),\n'
     '                    "The heartbeat has stopped changing, so \'alive\' in it is a "\n'
     '                    "MEMORY, not a reading. Normal when the PC is off out of "\n'
     '                    "hours; during the clinic day it means the machine is down.")\n',
     '            elif _hbstale:\n'
     '                # D554 (S349, F-547): a stale heartbeat DURING THE CLINIC DAY is the\n'
     '                # machine down or unreachable -- RED; outside it (night, Sunday) it\n'
     '                # is the PC switched off -- info, as before. The clinic day is the\n'
     '                # same two settings the pull check below reads, on the IST clock;\n'
     '                # Sunday is out of hours unless pipeline.clinic_sunday is "1".\n'
     '                _now_ist = dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)\n'
     '                _cfrom = int(setting(con, "pipeline.clinic_hour_from", "9") or 9)\n'
     '                _cto = int(setting(con, "pipeline.clinic_hour_to", "21") or 21)\n'
     '                _csun = str(setting(con, "pipeline.clinic_sunday", "0") or "0").strip() == "1"\n'
     '                _clinic_now = (_cfrom <= _now_ist.hour < _cto) and (_now_ist.weekday() != 6 or _csun)\n'
     '                add("watcher", "Medical PC capture", "bad" if _clinic_now else "info",\n'
     '                    "last heard from the medical PC %.1f hours ago — %s"\n'
     '                    % (float(_hbage), "DURING THE CLINIC DAY: the machine is down or unreachable"\n'
     '                       if _clinic_now else "state unknown (out of hours)"),\n'
     '                    "The heartbeat has stopped changing, so \'alive\' in it is a "\n'
     '                    "MEMORY, not a reading. Normal when the PC is off out of "\n'
     '                    "hours; during the clinic day it means the machine is down: "\n'
     '                    "check the medical PC is on and Tailscale connected.")\n'),
    # 2 · one line in the health page's help box
    ('            \'<p>Refresh to re-check. Nothing on this page changes any \'\n'
     '            \'record.</p></details>\'\n',
     '            \'<p>Refresh to re-check. Nothing on this page changes any \'\n'
     '            \'record.</p>\'\n'
     '            # S349 (F-540): the collector\'s freshness table, one door away.\n'
     '            \'<p><a href="/finance/freshness">Freshness table &#8594;</a> &mdash; every \'\n'
     '            \'job\\\'s last success and its age, as the 08:05 collector last wrote it.</p>\'\n'
     '            \'</details>\'\n'),
    # 3 · the guarded mount, after the S332 block
    ('# --- S332_RECORDS end ---\n'
     '\n'
     '\n'
     'if __name__ == "__main__":\n',
     '# --- S332_RECORDS end ---\n'
     '\n'
     '\n'
     '# --- S349_WATCHER_FRESHNESS begin -- the collector\'s freshness table, served read-only (F-540, owner 20-Sep-2026) ---\n'
     '# /finance/freshness returns /root/finance/freshness.html exactly as freshness.py wrote it, with one line\n'
     '# saying when. Same gate as the health page (checker on the medical unit). Nothing computed, nothing run,\n'
     '# nothing written. GUARDED (S209): a fault inside it is printed, every other page serves.\n'
     'try:\n'
     '    import freshness_page                                     # noqa: E402\n'
     '    freshness_page.init(app, require)\n'
     'except Exception as _ex_fp:                                    # noqa: BLE001\n'
     '    print("freshness_page NOT mounted: %s" % _ex_fp, file=sys.stderr)\n'
     '# --- S349_WATCHER_FRESHNESS end ---\n'
     '\n'
     '\n'
     'if __name__ == "__main__":\n'),
]


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def apply_to_text(text):
    if MARK in text:
        return text, ["ALREADY -- this file already carries the S349 change"]
    if "# --- S332_RECORDS end ---" not in text:
        return None, ["this file does not carry S332 -- refusing"]
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
        print("usage: patch_finance_app_s349.py --check|--apply [--file=PATH]")
        return 2
    if not os.path.isfile(target):
        print("RESULT REFUSED -- %s is not there" % target)
        return 3
    live = md5_file(target)
    with open(target, "r", encoding="utf-8") as fh:
        text = fh.read()
    print("file   :", target)
    print("md5    :", live, "" if live == FROM_MD5 or MARK in text else "(expected FROM %s)" % FROM_MD5)
    new, msgs = apply_to_text(text)
    for m in msgs:
        print("       :", m)
    if new is None:
        print("RESULT REFUSED -- nothing changed")
        return 4
    if new == text:
        print("RESULT ALREADY")
        return 0
    if mode == "--check":
        print("RESULT WOULD APPLY -- %d edit(s), no write in --check" % len(EDITS))
        return 0
    if live != FROM_MD5:
        print("RESULT REFUSED -- the live file is not the FROM this patch was read from (%s); nothing changed" % FROM_MD5)
        return 6
    stamp = time.strftime("%Y%m%d_%H%M%S")
    bak = "%s.bak_S349_%s" % (target, stamp)
    shutil.copy2(target, bak)
    tmpdir = tempfile.mkdtemp(prefix="s349_")
    tmp = os.path.join(tmpdir, "candidate.py")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(new)
    try:
        py_compile.compile(tmp, cfile=os.path.join(tmpdir, "c.pyc"), doraise=True)
    except py_compile.PyCompileError as ex:
        print("RESULT REFUSED -- the patched text does not compile:", ex)
        shutil.rmtree(tmpdir, ignore_errors=True)
        return 5
    shutil.copystat(target, tmp)
    shutil.move(tmp, target)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("backup :", bak)
    print("md5 now:", md5_file(target))
    print("RESULT APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
