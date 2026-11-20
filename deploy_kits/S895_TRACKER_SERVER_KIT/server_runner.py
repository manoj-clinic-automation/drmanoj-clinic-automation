#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server_runner.py -- S895 (session 492, 20-Nov-2026): the Follow-up Tracker's engine runs on the server.

WHAT IT IS. The clinic PC's own orchestrator, docterz_pickup.py (S892 / ddbed001), and engine, processor.py
(f1c02736), run here UNCHANGED. This file only gives them a server to stand on:

  1. THE CLOCK is pinned to IST before anything is imported (every tracker file reads the local clock and
     assumes the clinic's time; the server's own zone is not relied on).
  2. THE INTAKE. The PC watches D:\\Downloads, where docterz_fetch.py saves what the server holds. Here the
     server already holds the exports (/root/finance/docterz_exports/<kind>/, table docterz_export). Each pass
     hard-links every CURRENT export of the last few days into one flat folder, intake/, under the very name
     docterz_fetch.py would have given it on the PC -- consultation_report_<day>_reception_<6 hex>.csv,
     followup_logs_<day>_reception_<6 hex>.csv, clinical_data_report_<day>_reception_<6 hex>.csv -- so the
     pickup's own rules (content, quiet time, RUN / skip / newest wins / QUARANTINE, S540, S892) see exactly
     what they see on the PC, and the names inside the ledgers stay the PC's names.
  3. THE SENDS. The call sheet goes to the receiver on this very box (127.0.0.1:8100 /fu-upload, header
     X-FU-Origin: server, so an upload WITHOUT that header after the switch can only be the PC's -- the red
     line). The patient join goes by the pickup's own push_patient_join.py --push (its door, this box).
     --refresh-latest hands the Sheet write to the box's own one writer (clinic-followup-push.service).
  4. THE SWITCHES. /root/finance/_off/ALL_OFF or /root/followup_tracker/OFF present -> this pass does nothing
     and says so once. The OFF file is PRESENT at install; the switch evening removes it.

NEVER: deletes an export; parses a patient row itself; prints a name or a number. Counts, dates, file names.

    /root/wa/venv/bin/python3 -B server_runner.py                one pass (cron */5)
    /root/wa/venv/bin/python3 -B server_runner.py --dry-run      say what the pass would do; write nothing
    /root/wa/venv/bin/python3 -B server_runner.py --refresh-latest
    /root/wa/venv/bin/python3 -B server_runner.py --selftest     offline checks on a made-up root; touches nothing
"""
import os
import time

os.environ["TZ"] = "Asia/Kolkata"          # (1) the clock, before any tracker module is imported
time.tzset()

import argparse        # noqa: E402
import datetime as dt  # noqa: E402
import glob            # noqa: E402
import io              # noqa: E402
import json            # noqa: E402
import shutil          # noqa: E402
import sqlite3         # noqa: E402
import subprocess      # noqa: E402
import sys             # noqa: E402
import tempfile        # noqa: E402
import urllib.request  # noqa: E402
import uuid            # noqa: E402

VERSION = "S895.2"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("FUT_ROOT", HERE)
INTAKE = os.environ.get("FUT_INTAKE", os.path.join(ROOT, "intake"))
ARCHIVE = os.environ.get("FUT_ARCHIVE", os.path.join(ROOT, "archive"))
STORE = os.environ.get("DOCTERZ_EXPORT_STORE", "/root/finance/docterz_exports")
DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
OFF_FILES = [os.environ.get("FUT_ALL_OFF", "/root/finance/_off/ALL_OFF"), os.environ.get("FUT_OFF", os.path.join(ROOT, "OFF"))]
RECEIVER_URL = os.environ.get("FUT_RECEIVER_URL", "http://127.0.0.1:8100/fu-upload")
FU_ENV = os.environ.get("FUT_FU_ENV", os.path.join(ROOT, "fu_upload.env"))
PUSH_UNIT = os.environ.get("FUT_PUSH_UNIT", "clinic-followup-push.service")
INTAKE_DAYS = int(os.environ.get("FUT_INTAKE_DAYS", "7"))        # how far back the intake reaches (the PC: 3)
INTAKE_KEEP_DAYS = int(os.environ.get("FUT_INTAKE_KEEP_DAYS", "60"))
PREFIX = {"consultation": "consultation_report", "followup": "followup_logs", "clinical": "clinical_data_report"}
STATE = os.path.join(ARCHIVE, "_runner_state.json")


def say(msg):
    print("[%s] %s" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg), flush=True)


def off_file():
    for p in OFF_FILES:
        if os.path.exists(p):
            return p
    return ""


# ── (2) the intake ─────────────────────────────────────────────────────────────────────────────────
def intake_name(kind, day, md5):
    return "%s_%s_reception_%s.csv" % (PREFIX[kind], day or "nodate", (md5 or "")[:6])


def current_exports(db=DB, days=INTAKE_DAYS, now=None):
    """[(kind, day, md5, stored)] -- what docterz_fetch.py would be given: CURRENT, stored, taken lately."""
    now = now or dt.datetime.now()
    since = (now - dt.timedelta(days=days)).isoformat(sep=" ")
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    try:
        rows = con.execute("SELECT kind, business_date, md5, stored FROM docterz_export "
                           "WHERE status='current' AND stored<>'' AND taken_at>=? ORDER BY taken_at, id", (since,)).fetchall()
    finally:
        con.close()
    return [(k, d, m, s) for (k, d, m, s) in rows if k in PREFIX]


def refresh_intake(dry=False, db=DB, intake=INTAKE, now=None):
    """Hard-link each current export into intake/ under its PC name; never touches a file already there.
    Returns (linked, present, pruned). A link failing across filesystems falls back to a copy."""
    if not dry:
        os.makedirs(intake, mode=0o700, exist_ok=True)
    linked = present = pruned = 0
    for kind, day, md5, stored in current_exports(db, now=now):
        if not os.path.exists(stored):
            say("export on the table but not on disk: %s %s -- left alone" % (kind, day))
            continue
        dest = os.path.join(intake, intake_name(kind, day, md5))
        if os.path.exists(dest):
            present += 1
            continue
        if dry:
            say("DRY RUN -- would link %s" % os.path.basename(dest))
            linked += 1
            continue
        try:
            os.link(stored, dest)
        except OSError:
            shutil.copy2(stored, dest)
        linked += 1
    # links older than the keep window go (the archive holds the bytes; the pickup never reads intake for history)
    cutoff = time.time() - INTAKE_KEEP_DAYS * 86400
    for p in glob.glob(os.path.join(intake, "*.csv")):
        try:
            if os.path.getmtime(p) < cutoff:
                if not dry:
                    os.unlink(p)
                pruned += 1
        except OSError:
            pass
    return linked, present, pruned


# ── (3) the sends ──────────────────────────────────────────────────────────────────────────────────
def fu_secret(env_file=FU_ENV):
    try:
        with open(env_file, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("FU_UPLOAD_SECRET="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


def local_upload(xlsx_path, url=RECEIVER_URL, secret=None, timeout=30):
    """POST the workbook to the receiver on this box, marked as the server's own. (ok, message)."""
    secret = fu_secret() if secret is None else secret
    if not secret:
        return False, "upload skipped: no FU_UPLOAD_SECRET in %s" % FU_ENV
    name = os.path.basename(xlsx_path)
    boundary = "----s895" + uuid.uuid4().hex
    with open(xlsx_path, "rb") as fh:
        data = fh.read()
    body = io.BytesIO()
    body.write(("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
                "Content-Type: application/octet-stream\r\n\r\n" % (boundary, name)).encode("utf-8"))
    body.write(data)
    body.write(("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    req = urllib.request.Request(url, data=body.getvalue(), method="POST", headers={
        "Content-Type": "multipart/form-data; boundary=%s" % boundary,
        "X-FU-Secret": secret, "X-FU-Origin": "server", "User-Agent": "server_runner/%s" % VERSION})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            txt = resp.read(300).decode("utf-8", "replace").strip()
    except Exception as e:                                        # noqa: BLE001
        return False, "upload failed: %s" % str(e)[:160]
    return (200 <= code < 300), "receiver %s %s (%s, %d bytes)" % (code, txt[:80], name, len(data))


def patient_push_local():
    """push_patient_join.py --push, in-process, its upload pointed at the receiver on this box (so the join
    workbooks also carry X-FU-Origin: server). Returns (ok, tail lines) as the pickup expects."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    buf = io.StringIO()
    old = sys.stdout
    ok = False
    try:
        sys.stdout = buf
        import push_to_vps                                          # noqa: PLC0415
        import push_patient_join as PJ                              # noqa: PLC0415
        push_to_vps.upload_workbook = lambda path, timeout=30: local_upload(path)
        try:
            rc = PJ.main(["--push"])
            ok = (rc or 0) == 0
        except SystemExit as e:
            ok = (e.code or 0) == 0
    except Exception as e:                                          # noqa: BLE001
        buf.write("patient push raised: %s: %s\n" % (type(e).__name__, str(e)[:160]))
    finally:
        sys.stdout = old
    tail = [x for x in buf.getvalue().splitlines() if x.strip()][-3:]
    return ok, tail


def sheet_push_via_unit(_staff_path):
    """The box's one Sheet writer (push_followups_vps.py, with the Do_Not_Call filter from S895)."""
    r = subprocess.run(["systemctl", "start", PUSH_UNIT], capture_output=True, text=True, timeout=120)
    ok = r.returncode == 0
    return ok, ["%s %s" % (PUSH_UNIT, "started" if ok else ("failed: " + (r.stderr or r.stdout).strip()[:120]))]


# ── the pass ───────────────────────────────────────────────────────────────────────────────────────
def load_pickup():
    """the PC's own docterz_pickup.py, unchanged: beside this file on the box; in tracker/ inside the kit"""
    for d in (ROOT, os.path.join(ROOT, "tracker")):
        if os.path.exists(os.path.join(d, "docterz_pickup.py")):
            if d not in sys.path:
                sys.path.insert(0, d)
            break
    import docterz_pickup as DP
    return DP


def one_pass(dry=False, refresh=False):
    off = off_file()
    if off:
        say("OFF (%s) -- nothing done" % off)
        return 0
    if not os.path.exists(os.path.join(ROOT, "processor.py")):
        say("REFUSING: %s holds no processor.py" % ROOT)
        return 2
    os.makedirs(ARCHIVE, mode=0o700, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "uploads"), mode=0o700, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "outputs"), mode=0o700, exist_ok=True)
    linked, present, pruned = refresh_intake(dry=dry)
    if linked or pruned:
        say("intake: %d new, %d already there, %d pruned" % (linked, present, pruned))
    DP = load_pickup()
    lock = os.path.join(ARCHIVE, "_pickup.lock")
    if not dry and not DP.take_lock(lock):
        say("another pass holds the lock -- not now")
        return 0
    try:
        p = DP.Pass(tracker=ROOT, downloads=INTAKE, archive=ARCHIVE, dry_run=dry,
                      vps_upload=local_upload, patient_push=patient_push_local)
        rc = p.refresh_latest(sheet_push=sheet_push_via_unit) if refresh else p.run()
    finally:
        if not dry:
            try:
                os.unlink(lock)
            except OSError:
                pass
    try:
        st = {"at": dt.datetime.now().isoformat(sep=" "), "rc": rc, "version": VERSION,
              "intake": {"linked": linked, "present": present, "pruned": pruned}}
        tmp = STATE + ".part"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(st, fh, indent=1, sort_keys=True)
        os.replace(tmp, STATE)
    except OSError:
        pass
    return rc or 0


# ── the self-test (made-up root; touches nothing live) ─────────────────────────────────────────────
def selftest():
    fails = []
    def check(name, cond):
        print("  %s %s" % ("ok  " if cond else "FAIL", name))
        if not cond:
            fails.append(name)
    check("clock is IST", time.strftime("%z") == "+0530")
    check("intake name consultation", intake_name("consultation", "2026-10-02", "ab" * 16) == "consultation_report_2026-10-02_reception_ababab.csv")
    check("intake name followup", intake_name("followup", "2026-10-02", "cd" * 16) == "followup_logs_2026-10-02_reception_cdcdcd.csv")
    check("intake name clinical", intake_name("clinical", "2026-10-02", "ef" * 16) == "clinical_data_report_2026-10-02_reception_efefef.csv")
    root = tempfile.mkdtemp(prefix="s895_selftest_")
    try:
        db = os.path.join(root, "f.db")
        store = os.path.join(root, "store", "consultation")
        os.makedirs(store)
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE docterz_export (id INTEGER PRIMARY KEY, kind TEXT, business_date TEXT, md5 TEXT, stored TEXT, status TEXT, taken_at TEXT)")
        now = dt.datetime.now()
        rows = []
        for i, (st, age) in enumerate([("current", 1), ("current", 2), ("superseded", 1), ("current", 30), ("quarantined", 1)]):
            p = os.path.join(store, "2026-11-%02d__abc%07x.csv" % (10 + i, i + 1))
            with open(p, "w") as fh:
                fh.write("Sr No,Consultation Date,Patient UID,Amount collected,Bill Amount\n")
            rows.append(("consultation", "2026-11-%02d" % (10 + i), ("abcdef" + "%026x" % (i + 1)), p, st, (now - dt.timedelta(days=age)).isoformat(sep=" ")))
        con.executemany("INSERT INTO docterz_export (kind, business_date, md5, stored, status, taken_at) VALUES (?,?,?,?,?,?)", rows)
        con.commit(); con.close()
        intake = os.path.join(root, "intake")
        linked, present, pruned = refresh_intake(dry=False, db=db, intake=intake, now=now)
        names = sorted(os.listdir(intake))
        check("only CURRENT exports of the window are linked (2)", linked == 2 and len(names) == 2)
        check("linked under the PC's names", names == ["consultation_report_2026-11-10_reception_abcdef.csv", "consultation_report_2026-11-11_reception_abcdef.csv"])
        check("a hard link, not a copy", bool(names) and os.stat(os.path.join(intake, names[0])).st_nlink == 2)
        linked2, present2, _ = refresh_intake(dry=False, db=db, intake=intake, now=now)
        check("second pass links nothing, finds 2 present", linked2 == 0 and present2 == 2)
        old = os.path.join(intake, "consultation_report_2026-01-01_reception_aaaaaa.csv")
        open(old, "w").close(); os.utime(old, (time.time() - 90 * 86400,) * 2)
        _, _, pruned3 = refresh_intake(dry=False, db=db, intake=intake, now=now)
        check("a link older than the keep window is pruned", pruned3 == 1 and not os.path.exists(old))
        # control: the window must go red when the table is empty
        con = sqlite3.connect(db); con.execute("DELETE FROM docterz_export"); con.commit(); con.close()
        l4, p4, _ = refresh_intake(dry=False, db=db, intake=intake, now=now)
        check("CONTROL: empty table links nothing (red if it did)", l4 == 0 and p4 == 0)
        # the OFF switch
        global OFF_FILES
        keep = OFF_FILES
        OFF_FILES = [os.path.join(root, "nope"), os.path.join(root, "OFF")]
        check("no OFF file -> runs", off_file() == "")
        open(OFF_FILES[1], "w").close()
        check("OFF file -> says OFF", off_file().endswith("OFF"))
        OFF_FILES = keep
        check("upload without a secret refuses, says why", local_upload(__file__, secret="")[0] is False)
        # the wiring against the pickup itself (the PC's docterz_pickup.py beside this file)
        try:
            import inspect
            DP = load_pickup()
            sig = inspect.signature(DP.Pass.__init__).parameters
            check("docterz_pickup.Pass takes tracker/downloads/archive/dry_run/vps_upload/patient_push",
                  all(k in sig for k in ("tracker", "downloads", "archive", "dry_run", "vps_upload", "patient_push")))
            check("Pass.run / refresh_latest(sheet_push) / take_lock present",
                  callable(getattr(DP.Pass, "run", None)) and "sheet_push" in inspect.signature(DP.Pass.refresh_latest).parameters and callable(getattr(DP, "take_lock", None)))
            check("the pickup's own names are the PC's (NAME_PREFIXES)", tuple(DP.NAME_PREFIXES) == ("consultation_report", "followup_logs", "clinical_data_report"))
        except Exception as e:                                        # noqa: BLE001
            check("docterz_pickup.py loads beside the runner (%s: %s)" % (type(e).__name__, str(e)[:80]), False)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("selftest: %d failure(s)" % len(fails))
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh-latest", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    return one_pass(dry=a.dry_run, refresh=a.refresh_latest)


if __name__ == "__main__":
    sys.exit(main())
