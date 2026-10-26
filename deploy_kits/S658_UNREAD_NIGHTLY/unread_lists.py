#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
unread_lists.py  (kit S658_UNREAD_NIGHTLY, S357, 26-Oct-2026)  --  each person's UNREAD "Aaj ka kaam" lines, counted nightly.

Why (F-1024, S349). On 22-Oct a change to one duty's SQL in DUTY_MAP left reception's list unable to read that line: the
list hid it and showed "Poori list abhi nahin khul paayi" -- fail-closed, as designed -- and nobody knew until a person
saw the banner three days later. This step lets the system see it first: every night it builds every staff list exactly
as the server would, from the server's own files and last night's copy of the database, and counts the lines that
could not be read.

READ-ONLY. It changes nothing on the server, nothing in the repository and nothing in any database.
   from D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz  : root/finance/aaj_kaam.py, aaj_seed.py, aaj_duties.json --
                                                             each checked against the bundle's own MANIFEST.md5
   from D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz : the database (unzipped to a scratch folder, opened mode=ro)
   from D:\dr-manoj-git\drmanoj-clinic-automation\claude_code_briefs\DUTY_MAP.json : the duty map (the server pulls this
                                                             same repository)
The scratch folder (D:\Downloads\_r658) holds a copy of the database, which carries patient data; it stays on this PC
and is REMOVED at the end of every run, pass or fail. The report names duty ids and counts only -- no patient data.

Writes D:\Downloads\_kbtools\UNREAD_LISTS_LATEST.txt and a dated copy in reports\.
stdlib only.  Exit 0 = OK (no unread line).  2 = WARN (an unread line, or a stale source).  3 = FAIL (could not count).
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time

VERSION = "S658 v1"
RC_OK, RC_WARN, RC_FAIL = 0, 2, 3
WANT = ("root/finance/aaj_kaam.py", "root/finance/aaj_seed.py", "root/finance/aaj_duties.json")
STALE_H = 30


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


def md5_of(path, chunk=1024 * 1024):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def clean(s):
    return re.sub(r"\d{7,}", "#######", str(s or ""))[:90]       # never a long number in a report (F-185 habit)


def child(fin, db):
    """Runs in its own python: imports the bundle's aaj_kaam and builds every person's list, as the walks of S645/S650."""
    sys.path.insert(0, fin)
    import aaj_kaam as A                                            # noqa: E402
    assert os.path.dirname(os.path.abspath(A.__file__)) == os.path.abspath(fin), A.__file__
    rd = A.Reader(db)
    out = {"seed_err": getattr(A, "SEED_ERR", None), "people": {}}
    for k, doc in rd.people.items():
        lst = A.person_list(rd, doc, view_as=True)
        bad = []                                                    # which lines: person_list's own two unread tests
        for ln in doc["lines"]:
            if not ln.get("on") or not A.clean(ln.get("hi"), A.TEXT_MAX):
                continue
            st = A.line_state(rd, ln)
            if st["kind"] is None or (st["kind"] == "job" and st.get("err")):
                bad.append([ln.get("when"), ln.get("id"), clean(st.get("err"))])
        out["people"][k] = {"on": bool(doc.get("on")), "lines": sum(len(rs) for rs in lst["sections"].values()),
                            "unread": lst.get("unread"), "bad": bad}
    sys.stdout.write(json.dumps(out))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", default=r"D:\Downloads\_kbtools")
    ap.add_argument("--repo", default=r"D:\dr-manoj-git\drmanoj-clinic-automation")
    ap.add_argument("--map", default=None, help="the duty map to use (default: the repository's)")
    ap.add_argument("--scratch", default=r"D:\Downloads\_r658")
    ap.add_argument("--report-dir", default=None, help="where the report is written (default: --tools)")
    ap.add_argument("--child", nargs=2, metavar=("FIN", "DB"), help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.child:
        return child(*a.child)

    t0 = time.time()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out, worst = [], [RC_OK]

    def say(s=""):
        out.append(s)

    def verdict(rc):
        worst[0] = max(worst[0], rc)

    say("UNREAD LISTS -- %s  (each person's 'Aaj ka kaam' lines that could not be read; read-only)" % VERSION)
    say("when       : %s (local clock on this PC)" % time.strftime("%Y-%m-%d %H:%M:%S"))
    vps = os.path.join(a.tools, "vps_code")
    tar_p = os.path.join(vps, "code_nightly.tar.gz")
    db_p = os.path.join(vps, "finance_nightly.db.gz")
    map_p = a.map or os.path.join(a.repo, "claude_code_briefs", "DUTY_MAP.json")
    say()
    say("SOURCES")
    for label, p in (("bundle", tar_p), ("database", db_p), ("duty map", map_p)):
        if not os.path.isfile(p):
            say("  %-9s: MISSING  %s" % (label, p))
            verdict(RC_FAIL)
            continue
        age = (time.time() - os.path.getmtime(p)) / 3600.0
        stale = label != "duty map" and age > STALE_H
        say("  %-9s: %s  md5 %s  %s%s" % (label, p, md5_of(p), time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p))),
                                          ("   STALE (%.0f h old)" % age) if stale else ""))
        if stale:
            verdict(RC_WARN)
    if worst[0] == RC_FAIL:
        return finish(a, out, worst[0], stamp, t0)

    fin = os.path.join(a.scratch, "fin")
    dbx = os.path.join(a.scratch, "finance.db")
    res, gone = None, False
    try:
        if os.path.isdir(a.scratch):
            shutil.rmtree(a.scratch)                                # a scratch a cut run left behind
        os.makedirs(fin)
        say()
        say("THE SERVER'S OWN FILES (from the bundle, checked against its MANIFEST.md5)")
        with tarfile.open(tar_p, "r:gz") as tf:
            names = {m.name.lstrip("./"): m for m in tf.getmembers() if m.isfile()}
            man = {}
            mf = names.get("MANIFEST.md5")
            if mf is not None:
                for line in tf.extractfile(mf).read().decode("utf-8", "replace").splitlines():
                    p = line.strip().split(None, 1)
                    if len(p) == 2:
                        man[p[1].lstrip("*").lstrip("./")] = p[0]
            for w in WANT:
                m = names.get(w)
                if m is None:
                    say("  %-28s MISSING from the bundle" % w)
                    verdict(RC_FAIL)
                    continue
                b = tf.extractfile(m).read()
                h = md5_bytes(b)
                ok = man.get(w) == h
                say("  %-28s %s  %s" % (w, h, "= its MANIFEST row" if ok else "DISAGREES with its MANIFEST row"))
                if not ok:
                    verdict(RC_FAIL)
                with open(os.path.join(fin, os.path.basename(w)), "wb") as fh:
                    fh.write(b)
        if worst[0] == RC_FAIL:
            raise RuntimeError("a server file is missing from the bundle or disagrees with its MANIFEST")
        with gzip.open(db_p, "rb") as g, open(dbx, "wb") as fh:
            shutil.copyfileobj(g, fh)
        env = dict(os.environ, DUTY_MAP_JSON=map_p, AAJ_DUTIES_JSON=os.path.join(fin, "aaj_duties.json"),
                   PYTHONDONTWRITEBYTECODE="1")
        cp = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child", fin, dbx.replace("\\", "/")],
                            capture_output=True, text=True, env=env, timeout=600, cwd=a.scratch)
        if cp.returncode != 0:
            say()
            say("COULD NOT BUILD THE LISTS (rc %s): %s" % (cp.returncode, clean((cp.stderr or "").strip().splitlines()[-1:] or "")))
            verdict(RC_FAIL)
        else:
            res = json.loads(cp.stdout)
    except Exception as ex:                                         # noqa: BLE001 -- a report, never a traceback
        say()
        say("COULD NOT COUNT: %s: %s" % (type(ex).__name__, clean(ex)))
        verdict(RC_FAIL)
    finally:
        try:
            if os.path.isdir(a.scratch):
                shutil.rmtree(a.scratch)
        except OSError:
            pass
        gone = not os.path.exists(a.scratch)
        if not gone:
            verdict(RC_WARN)

    if res is not None:
        say()
        say("EACH PERSON'S LIST")
        if res.get("seed_err"):
            say("  aaj_seed.py did not load: %s" % clean(res["seed_err"]))
            verdict(RC_FAIL)
        total = 0
        for k in sorted(res["people"]):
            p = res["people"][k]
            n = p.get("unread") or 0
            total += n if p.get("on") else 0
            say("  %-10s %-3s  lines %3d   UNREAD %d" % (k, "on" if p.get("on") else "off", p.get("lines") or 0, n))
            for sec, lid, err in p.get("bad") or []:
                say("      unread: %s  (section %s)  %s" % (lid, sec, err))
        say()
        say("  UNREAD on lists that are switched on: %d" % total)
        if total:
            verdict(RC_WARN)
            say("  A list with an unread line shows the person 'Poori list abhi nahin khul paayi'. The usual cause: a duty's SQL")
            say("  changed in DUTY_MAP and aaj_seed.REWRITE no longer fits it (F-1024). The next session reads it first.")
    say()
    say("scratch    : %s %s" % (a.scratch, "removed (the database copy is gone)" if gone
                                else "NOT REMOVED -- it holds a database copy; remove it"))
    return finish(a, out, worst[0], stamp, t0)


def finish(a, out, worst, stamp, t0):
    out.append("took       : %.1f s" % (time.time() - t0))
    out.append("VERDICT    : %s" % {RC_OK: "OK", RC_WARN: "WARN", RC_FAIL: "FAIL"}[worst])
    text = "\n".join(out) + "\n"
    sys.stdout.write(text)
    rd = a.report_dir or a.tools
    try:
        os.makedirs(os.path.join(rd, "reports"), exist_ok=True)
        latest = os.path.join(rd, "UNREAD_LISTS_LATEST.txt")
        with open(latest, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        shutil.copyfile(latest, os.path.join(rd, "reports", "UNREAD_LISTS_%s.txt" % stamp))
    except OSError as ex:
        sys.stderr.write("could not write the report: %s\n" % ex)
        return RC_FAIL
    return worst


if __name__ == "__main__":
    sys.exit(main())
