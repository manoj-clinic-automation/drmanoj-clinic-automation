# -*- coding: utf-8 -*-
r"""patch_off_switches_s274.py -- Club 3h, the VPS half.

Runs ON THE BOX. Gives the four Sanjeevni server jobs that had no way to be
stopped the SAME off switch the two PCs were given at S259 and the Marg
collector has had since S240:

    a file whose PRESENCE stops the job, and whose ABSENCE starts it again.

Nothing is stopped, unregistered, restarted or uninstalled in either direction.
No cron line is touched. Each job reads the folder when it next comes round and
does what it finds.

    /root/finance/_off/ALL_OFF              stops all four
    /root/finance/_off/SPINE_OFF            the item spine cadence
    /root/finance/_off/ATTRIBUTION_OFF      the discount attribution
    /root/finance/_off/EXPORT_WATCH_OFF     the "did Amir export" watch
    /root/finance/_off/SALTS_REFRESH_OFF    the salt-list refresh

A trailing ".txt" is honoured on every name, so a marker made on Windows and
copied across still reads.

WHAT IS DELIBERATELY NOT GIVEN AN OFF SWITCH HERE:
  * /root/marg_ingest/marg_ingest.py and marg_shadow.py already have one
    (/root/marg_ingest/OFF, S240). It is untouched and keeps its own name.
  * finance_heal.py, finance_intent.py, bank_match.py, the backups and the
    Docterz ingest are the CLINIC's jobs, not Sanjeevni's. Club 3h names the
    spine, the attribution and the export watch. Widening it past what the
    plan says is how a kit stops being reviewable.

WHERE THE GUARD SITS: after --selftest is handled, before the job reads a
database or a file. A selftest is not a job and still runs when the switch is
on -- that is deliberate, so the switch can never hide a broken file.

    python3 patch_off_switches_s274.py --dir /root/finance
    python3 patch_off_switches_s274.py --dir /root/finance --check
"""
import argparse
import hashlib
import os
import shutil
import sys

HELPER = '''# --- S274 (Club 3h) -- the OFF switch ----------------------------------------
# A file whose presence stops this job and whose absence starts it again. The
# same shape as the PC side (S259) and as /root/marg_ingest/OFF (S240): no cron
# line is touched and nothing is unregistered, so the job simply reads the
# folder when it next comes round. A trailing ".txt" is honoured so a marker
# made on Windows still reads.
_OFF_DIR = "/root/finance/_off"
_OFF_NAMES = ("ALL_OFF", "%(own)s")


def _off_marker():
    for _n in _OFF_NAMES:
        for _p in (os.path.join(_OFF_DIR, _n), os.path.join(_OFF_DIR, _n + ".txt")):
            if os.path.exists(_p):
                return _p
    return None


'''

GUARD = '''    _off = _off_marker()
    if _off:
        print("%(job)s: switched off (%%s exists)" %% _off)
        return 0
'''

# name -> (own marker, job label, from_md5, to_md5, guard anchor)
TARGETS = {
    "spine_cadence.py": dict(
        own="SPINE_OFF", job="spine_cadence",
        frm="0eeed35425e919fa67ff4cce8f8a9acc", to="c1e31012ff3271da76eaba00258f0df6",
        anchor='    a = ap.parse_args(argv)\n'
               '    if a.selftest:\n'
               '        return selftest()\n'
               '    if not a.db:\n'
               '        ap.error("--db is required")\n'
               '    db = a.db'),
    "sale_attribution.py": dict(
        own="ATTRIBUTION_OFF", job="sale_attribution",
        frm="c74f004943c69c59aba7a80f0ed0c7e2", to="82b4f5269b218774b6d9ed3f3a2821e4",
        anchor='    a = ap.parse_args(argv)\n'
               '    if a.selftest:\n'
               '        return selftest()\n'
               '    if not a.db:\n'
               '        ap.error("--db is required")\n'
               '    con = sqlite3.connect(a.db, timeout=30)'),
    "export_watch.py": dict(
        own="EXPORT_WATCH_OFF", job="export_watch",
        frm="0993c4411a34769865bcefbb8c7a05e0", to="2920c28ee7e9f87b89f771d4c1923831",
        anchor='    a = ap.parse_args(argv)\n'
               '    if a.selftest:\n'
               '        return selftest()\n'
               '    day = resolve_day(a.day)'),
    "salts_refresh.py": dict(
        own="SALTS_REFRESH_OFF", job="salts_refresh",
        frm="d7994e3899f79021ebbc133355efaef8", to="40cb26159c59d55d33d871abe36646ef",
        anchor='    when = _now().strftime("%d-%m-%Y %H:%M")\n'
               '    head = "salts_refresh %s " % when'),
}

MAIN_DEF = "def main(argv=None):"


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_text(t, spec):
    """Two anchored inserts. Raises ValueError with a plain reason."""
    if t.count(MAIN_DEF) != 1:
        raise ValueError('"%s" appears %d times, not once' % (MAIN_DEF, t.count(MAIN_DEF)))
    anchor = spec["anchor"]
    if t.count(anchor) != 1:
        raise ValueError("the guard anchor appears %d times, not once" % t.count(anchor))
    if "_off_marker" in t:
        raise ValueError("this file already carries an _off_marker()")
    helper = HELPER % {"own": spec["own"]}
    t = t.replace(MAIN_DEF, helper + MAIN_DEF)
    guard = GUARD % {"job": spec["job"]}
    t = t.replace(anchor, anchor + "\n" + guard.rstrip("\n"))
    return t


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="the folder holding the four files")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    plan, already, bad = [], [], []
    for name, spec in sorted(TARGETS.items()):
        path = os.path.join(a.dir, name)
        if not os.path.isfile(path):
            bad.append("%s: not found" % name)
            continue
        raw = open(path, "rb").read()
        got = md5(raw)
        if not spec["to"].startswith("TO_") and got == spec["to"]:
            already.append(name)
            continue
        if got != spec["frm"]:
            bad.append("%s: reads %s, expected %s" % (name, got, spec["frm"]))
            continue
        try:
            new = patch_text(raw.decode("utf-8"), spec).encode("utf-8")
        except ValueError as exc:
            bad.append("%s: %s" % (name, exc))
            continue
        if not spec["to"].startswith("TO_") and md5(new) != spec["to"]:
            bad.append("%s: would become %s, not the predicted %s"
                       % (name, md5(new), spec["to"]))
            continue
        plan.append((name, path, got, new))

    if bad:
        print("REFUSING -- nothing was written. Reasons:")
        for b in bad:
            print("   %s" % b)
        return 2

    if already and not plan:
        print("ALREADY INSTALLED -- all four files already carry the switch.")
        return 0

    for name, path, got, new in plan:
        print("%-22s %s -> %s" % (name, got, md5(new)))
    for name in already:
        print("%-22s already installed" % name)

    if a.check:
        print("(--check: nothing written)")
        return 0

    # All four are written only after every one of them has been proven above.
    written = []
    for name, path, got, new in plan:
        bak = "%s.bak_S274_%s" % (path, got[:8])
        try:
            if not os.path.exists(bak):
                shutil.copyfile(path, bak)
            tmp = path + ".new"
            with open(tmp, "wb") as fh:
                fh.write(new)
            os.replace(tmp, path)
            back = md5(open(path, "rb").read())
            if back != md5(new):
                raise IOError("read back as %s" % back)
            written.append((path, bak))
            print("INSTALLED %s" % path)
        except (OSError, IOError) as exc:
            print("FAILED on %s: %s" % (path, exc))
            for p, b in written:
                shutil.copyfile(b, p)
                print("rolled back %s" % p)
            if os.path.exists(bak):
                shutil.copyfile(bak, path)
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
