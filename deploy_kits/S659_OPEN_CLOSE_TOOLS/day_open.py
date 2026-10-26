#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
day_open.py  (kit S658 family, S357, 26-Oct-2026)  --  THE DAY'S OPENING CHECKS, ONCE A DAY, in one run.

The owner, 26-Oct-2026: the nightly's checks were being re-done at every session's open, not once a day. This tool
does the whole of the open's mechanical checks in one run and writes ONE page; the first session of the day runs it,
every later session of the day only reads the page (and re-runs it only if something changed: a publish, a new bundle).

READ-ONLY on every store: it reads files, runs md5sum, extracts the bundle into a scratch under $TEMP and removes it.
It writes only D:\Downloads\_kbtools\DAY_OPEN_LATEST.txt and a dated copy in reports\.

What it checks (the open's list, START_HERE_PROMPT v10 Phase 0 + END_OF_SESSION_PROMPT v18 'moved to the open'):
  1 the three nightly reports + UNREAD_LISTS + PC_STATE: exist . clock time . verdict . age (> 24 h = RED)
  2 the publish landed: .git/refs/heads/main == .git/refs/remotes/origin/main (read as files, never git) + last commit time
  3 the canon gate: md5sum -c MD5SUMS_ALL.txt from INSIDE KB_canon_all (count ok / mismatch)
  4 the CURRENT pin list (as the manifest names it) against the newest bundle: match | mismatch | pending | absent | blind
  5 the SSD: newest KB mirror (date, size, files), newest cold kit (age; DUE at 7 days), the loose brief folder
  6 the folder counts: loose files at each root vs FOLDER_COUNTS_LATEST (growth)
  7 the bundle and database copy: age
  8 the board / project knowledge measures are the assistant's (it appends them below with --note)
Exit 0 = all OK . 2 = WARN . 3 = a RED (a check failed or could not run).

  python day_open.py                 run the checks (default paths)
  python day_open.py --read          only print DAY_OPEN_LATEST.txt (a later session of the day)
  python day_open.py --note "text"   append one dated line to today's page (the assistant's own measures)
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile

VERSION = "S658 day_open v1"
RC_OK, RC_WARN, RC_FAIL = 0, 2, 3


def md5_of(path, chunk=1024 * 1024):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def age_h(path):
    return (time.time() - os.path.getmtime(path)) / 3600.0


def mt(path):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(path)))


def human(n):
    return "{:,}".format(n)


def newest_pins(canon):
    try:
        for line in open(os.path.join(canon, "CANONICAL_MANIFEST.md"), encoding="utf-8"):
            m = re.match(r"^\|\s*`(live_pins_S\d+close\.txt)`\s*\|[^|]*\|[^|]*\|\s*\*\*CURRENT\*\*", line)
            if m and os.path.isfile(os.path.join(canon, m.group(1))):
                return os.path.join(canon, m.group(1))
    except OSError:
        pass
    c = [n for n in os.listdir(canon) if re.match(r"^live_pins_S\d+close\.txt$", n)]
    return os.path.join(canon, max(c, key=lambda n: os.path.getmtime(os.path.join(canon, n)))) if c else None


def bundle_md5s(tar_path):
    got, man = {}, {}
    with tarfile.open(tar_path, "r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            data = tf.extractfile(m).read()
            if m.name.lstrip("./") == "MANIFEST.md5":
                for line in data.decode("utf-8", "replace").splitlines():
                    p = line.split(None, 1)
                    if len(p) == 2:
                        man[p[1].strip().lstrip("*")] = p[0]
                continue
            got["/" + m.name.lstrip("./")] = hashlib.md5(data).hexdigest()
    bad = sum(1 for k, v in man.items() if got.get("/" + k.lstrip("./")) not in (None, v))
    return got, len(man), bad


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", default=r"D:\Downloads\_kbtools")
    ap.add_argument("--repo", default=r"D:\dr-manoj-git\drmanoj-clinic-automation")
    ap.add_argument("--kb", default=r"D:\Downloads\ClaudeCowork")
    ap.add_argument("--ssd", default=r"F:\ClinicBackup\DrManojClinic_Automation")
    ap.add_argument("--roots", nargs="*", default=[r"D:\Downloads", r"D:\dr-manoj-git", r"F:\ClinicBackup"])
    ap.add_argument("--cold-due-days", type=int, default=7)
    ap.add_argument("--read", action="store_true")
    ap.add_argument("--note", default=None)
    a = ap.parse_args(argv)
    latest = os.path.join(a.tools, "DAY_OPEN_LATEST.txt")
    if a.read or a.note:
        if not os.path.isfile(latest):
            print("no DAY_OPEN_LATEST.txt yet -- run the checks")
            return RC_WARN
        if a.note:
            with open(latest, "a", encoding="utf-8", newline="\n") as fh:
                fh.write("note       : %s  %s\n" % (time.strftime("%Y-%m-%d %H:%M"), a.note))
        sys.stdout.write(open(latest, encoding="utf-8").read())
        return RC_OK

    t0 = time.time()
    out, worst = [], [RC_OK]

    def say(s=""):
        out.append(s)

    def verdict(rc):
        worst[0] = max(worst[0], rc)

    canon = os.path.join(a.repo, "deploy_kits", "KB_canon_all")
    say("DAY OPEN -- %s" % VERSION)
    say("when       : %s (local clock on this PC)   roots: %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), ", ".join(a.roots)))
    say("rule       : the first session of the day runs this; later sessions read it (python day_open.py --read);")
    say("             re-run after a publish or a new bundle. A RED here is the session's first work.")

    # 1 -- the nightly's reports
    say()
    say("1  THE NIGHTLY'S REPORTS (exist . clock time . verdict; > 24 h old = RED)")
    for name in ("REBUILD_REPORT_LATEST.txt", "MAINTENANCE_REPORT_LATEST.txt", "CANON_SUMS_LATEST.txt",
                 "UNREAD_LISTS_LATEST.txt", "PC_STATE_BACKUP_LATEST.txt"):
        p = os.path.join(a.tools, name)
        if not os.path.isfile(p):
            core = name in ("REBUILD_REPORT_LATEST.txt", "MAINTENANCE_REPORT_LATEST.txt", "CANON_SUMS_LATEST.txt")
            say("  %-30s MISSING  -- %s" % (name, "RED" if core else "WARN (the step has not run yet)"))
            verdict(RC_FAIL if core else RC_WARN)
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
        when = re.search(r"^when\s*:\s*(\S+ \S+)", txt, re.M)
        ver = re.search(r"^VERDICT\s*:\s*(.*)$", txt, re.M)
        old = age_h(p) > 24
        say("  %-30s %s  %s%s" % (name, when.group(1) if when else mt(p), (ver.group(1).strip()[:90] if ver else "(no VERDICT line)"),
                                 "   OLDER THAN 24 h -- RED" if old else ""))
        if old:
            verdict(RC_FAIL)
        elif ver and ver.group(1).strip().startswith(("WARN", "FAIL", "RED")):
            verdict(RC_WARN if ver.group(1).strip().startswith("WARN") else RC_FAIL)

    # 2 -- the publish landed
    say()
    say("2  THE PUBLISH (git read as files, never run)")
    try:
        g = os.path.join(a.repo, ".git")
        head = open(os.path.join(g, "refs", "heads", "main")).read().strip()
        rem = os.path.join(g, "refs", "remotes", "origin", "main")
        remote = open(rem).read().strip() if os.path.isfile(rem) else None
        if remote is None:
            for line in open(os.path.join(g, "packed-refs")):
                if line.strip().endswith("refs/remotes/origin/main"):
                    remote = line.split()[0]
        last = open(os.path.join(g, "logs", "HEAD"), encoding="utf-8", errors="replace").read().rstrip("\n").split("\n")[-1]
        m = re.search(r"> (\d{10}) ([+-]\d{4})\t(.*)$", last)
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(int(m.group(1)))) if m else "?"
        ok = head == remote
        say("  main %s  origin/main %s  %s   last commit %s  %s" % (head[:8], (remote or "?")[:8], "= LANDED" if ok else "DIFFER -- a publish is waiting (PUBLISH_ALL.bat)",
                                                                   when, (m.group(3)[:50] if m else "")))
        if not ok:
            verdict(RC_WARN)
    except Exception as ex:                                             # noqa: BLE001
        say("  could not read the repository's refs: %s" % ex)
        verdict(RC_FAIL)

    # 3 -- the canon gate
    say()
    say("3  THE CANON GATE (md5sum -c from inside KB_canon_all)")
    try:
        r = subprocess.run(["md5sum", "-c", "MD5SUMS_ALL.txt"], cwd=canon, capture_output=True, text=True, timeout=900)
        lines = r.stdout.splitlines()
        okn = sum(1 for l in lines if l.endswith(": OK"))
        bad = [l for l in lines if not l.endswith(": OK")]
        rows = sum(1 for l in open(os.path.join(canon, "MD5SUMS_ALL.txt"), encoding="utf-8") if l.strip())
        say("  rows %d  ok %d  not ok %d  %s" % (rows, okn, len(bad), "GREEN" if not bad and okn == rows else "RED -- halt until reconciled (D172/D188)"))
        for l in bad[:10]:
            say("    " + l)
        if bad or okn != rows:
            verdict(RC_FAIL)
    except Exception as ex:                                             # noqa: BLE001
        say("  the gate could not run: %s" % ex)
        verdict(RC_FAIL)

    # 4 -- the pin list against the newest bundle
    say()
    say("4  THE CURRENT PIN LIST AGAINST THE NEWEST BUNDLE")
    tar_p = os.path.join(a.tools, "vps_code", "code_nightly.tar.gz")
    pins = newest_pins(canon)
    if not os.path.isfile(tar_p) or not pins:
        say("  no bundle or no pin list in reach -- RED")
        verdict(RC_FAIL)
    else:
        try:
            got, n_man, n_bad = bundle_md5s(tar_p)
            match = pend = absent = blind = 0
            mism = []
            for line in open(pins, encoding="utf-8"):
                if line.startswith("#") or not line.strip():
                    continue
                f = line.rstrip("\n").split("\t")
                if len(f) < 3:
                    continue
                kind, h, path = f[0].strip(), f[1].strip().lower(), f[2].strip()
                note = f[3] if len(f) > 3 else ""
                if kind == "BLIND":
                    blind += 1
                    continue
                if kind not in ("VPS", "SHORT") or not path.startswith("/"):
                    continue
                live = got.get(path)
                if live is None:
                    absent += 1
                elif (live == h) if kind == "VPS" else live.startswith(h[:8]):
                    match += 1
                elif "DECLARED-PENDING" in note:
                    pend += 1
                else:
                    mism.append(path)
            say("  pins   : %s" % os.path.basename(pins))
            say("  bundle : %s  (%s, %d files, %d disagree with its own MANIFEST)" % (mt(tar_p), human(os.path.getsize(tar_p)), len(got), n_bad))
            say("  counts : %d match | %d mismatch | %d DECLARED-PENDING | %d not in the bundle | %d BLIND (not counted)" % (match, len(mism), pend, absent, blind))
            for p in mism[:12]:
                say("  MISMATCH : %s" % p)
            if n_bad or mism:
                verdict(RC_FAIL if n_bad else RC_WARN)
                if mism:
                    say("  a mismatch is a HALT until reconciled -- unless the pin is newer than this bundle (an install after 01:35)")
        except Exception as ex:                                         # noqa: BLE001
            say("  the bundle could not be read: %s -- RED" % ex)
            verdict(RC_FAIL)
    dbp = os.path.join(a.tools, "vps_code", "finance_nightly.db.gz")
    if os.path.isfile(dbp):
        say("  database copy : %s  (%s)%s" % (mt(dbp), human(os.path.getsize(dbp)), "   OLDER THAN 30 h" if age_h(dbp) > 30 else ""))
        if age_h(dbp) > 30:
            verdict(RC_WARN)

    # 5 -- the SSD
    say()
    say("5  THE SSD")
    try:
        md = os.path.join(a.ssd, "01_KB_MIRRORS")
        zs = sorted(n for n in os.listdir(md) if n.startswith("KB_mirror_") and n.endswith(".zip"))
        if zs:
            z = os.path.join(md, zs[-1])
            with zipfile.ZipFile(z) as zf:
                n = len(zf.namelist())
            today = time.strftime("%Y-%m-%d") in zs[-1]
            say("  newest KB mirror : %s  %s B  %d files%s" % (zs[-1], human(os.path.getsize(z)), n, "" if today else "   NOT FROM TODAY -- the nightly did not run; take one by hand"))
            if not today:
                verdict(RC_WARN)
        else:
            say("  no KB mirror found -- RED")
            verdict(RC_FAIL)
        cd = os.path.join(a.ssd, "02_COLD_KITS")
        ks = [n for n in os.listdir(cd) if n.startswith("COLD_KIT_") and n.endswith(".zip")]
        if ks:
            k = max(ks, key=lambda n: os.path.getmtime(os.path.join(cd, n)))
            d = age_h(os.path.join(cd, k)) / 24.0
            say("  newest cold kit  : %s  (%s, %.1f days old)%s" % (k, mt(os.path.join(cd, k)), d, "   DUE -- take one this open" if d >= a.cold_due_days else ""))
            if d >= a.cold_due_days:
                verdict(RC_WARN)
        else:
            say("  no cold kit found -- DUE")
            verdict(RC_WARN)
        bd = os.path.join(a.ssd, "03_BUILD_BRIEFS")
        bs = sorted(os.listdir(bd)) if os.path.isdir(bd) else []
        say("  build briefs     : %d on the SSD, newest %s" % (len(bs), max(bs, key=lambda n: os.path.getmtime(os.path.join(bd, n))) if bs else "-"))
    except Exception as ex:                                             # noqa: BLE001
        say("  the SSD could not be read: %s -- RED" % ex)
        verdict(RC_FAIL)

    # 6 -- the folder counts (loose files at each root, against the nightly's count)
    say()
    say("6  LOOSE FILES AT EACH ROOT (a loose file has no owner)")
    prev = {}
    fc = os.path.join(a.tools, "FOLDER_COUNTS_LATEST.txt")
    if os.path.isfile(fc):
        for line in open(fc, encoding="utf-8", errors="replace"):
            f = line.rstrip("\n").split("\t")
            if len(f) >= 3 and f[0] == "ROW":
                prev[f[1].rstrip("\\").lower()] = int(f[2])
    for root in a.roots:
        try:
            loose = [n for n in os.listdir(root) if os.path.isfile(os.path.join(root, n))]
            pv = prev.get(root.rstrip("\\").lower())
            say("  %-18s loose %3d%s" % (root, len(loose), ("  (nightly counted %d)" % pv) if pv is not None else ""))
            if pv is not None and len(loose) > pv:
                say("     new since the nightly: %s" % ", ".join(sorted(loose)[-5:]))
                verdict(RC_WARN)
        except OSError as ex:
            say("  %-18s not readable: %s -- RED" % (root, ex))
            verdict(RC_FAIL)

    say()
    say("took       : %.1f s" % (time.time() - t0))
    say("VERDICT    : %s" % {RC_OK: "OK -- nothing for the open beyond reading this page", RC_WARN: "WARN -- read the lines above", RC_FAIL: "RED -- the first work of the session"}[worst[0]])
    text = "\n".join(out) + "\n"
    sys.stdout.write(text)
    try:
        os.makedirs(os.path.join(a.tools, "reports"), exist_ok=True)
        with open(latest, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        shutil.copyfile(latest, os.path.join(a.tools, "reports", "DAY_OPEN_%s.txt" % time.strftime("%Y%m%d_%H%M%S")))
    except OSError as ex:
        sys.stderr.write("could not write the page: %s\n" % ex)
        return RC_FAIL
    return worst[0]


if __name__ == "__main__":
    sys.exit(main())
