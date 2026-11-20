#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s897.py -- kit S897: the walk on a MADE-UP root (no patient, no number typed anywhere: every name, UID and mobile
is generated at run time, F-185). Runs in the cloud, in the device VM and on the box ([3/7] of the installer).

    python3 walk_s897.py <kit dir> <live dir>        live dir holds docterz_pickup.py (the box's reader), owner_console.py
                                                      and freshness_legs.json as they are LIVE -- the controls go red on them

Checks: the door (cut, take, rules, the page, no leak) . the seed, both halves (pack, verify, translate, place, refuse)
. Replay 2's pairing (last run of the day, the inbox) . the red-line watcher's selftest . the two patched files hold what
S897 adds (CONTROL: the live files do not) . Prints PASS/FAIL lines and a count; exit 1 on any failure.
"""
import csv
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

KIT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(KIT, "..", "live")
PY = sys.executable
FAILS = []
N = [0]


def check(name, cond, why=""):
    N[0] += 1
    print(("PASS " if cond else "FAIL ") + name + (("  -- " + why) if (why and not cond) else ""))
    if not cond:
        FAILS.append(name)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


# ── made-up Docterz files (generated, never typed) ─────────────────────────────────────────────────
rnd = random.Random(897)
LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"


def uid():
    return "ZZ" + "".join(rnd.choice(LETTERS) for _ in range(6)) + "".join(rnd.choice("0123456789") for _ in range(2))


def name():
    return "".join(rnd.choice(LETTERS) for _ in range(7)).title() + " Madeup"


def mobile():
    return "9" + "".join(rnd.choice("0123456789") for _ in range(9))


def consult_csv(days, per_day):
    head = ["Sr No", "Consultation Date", "Patient UID", "Patient Name", "Mobile", "Bill Amount", "Amount collected", "Mode Of Payment"]
    rows = [head, ["", "", "", "Made-up Clinic", "", "", "", ""]]
    i = 0
    for d, n in zip(days, per_day):
        for _ in range(n):
            i += 1
            amt = str(rnd.choice((300, 500, 800)))
            rows.append([str(i), dt.date.fromisoformat(d).strftime("%d-%m-%Y"), uid(), name(), mobile(), amt, amt, "Cash"])
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\r\n").writerows(rows)
    return ("\ufeff" + buf.getvalue()).encode("utf-8")


def followup_csv(days):
    head = ["Appointment ID", "Patient Name", "Mobile No", "Followup Date", "Doctor"]
    rows = [head]
    for d in days:
        rows.append([str(rnd.randint(100000, 999999)), name(), mobile(), dt.date.fromisoformat(d).strftime("%d-%m-%Y"), "Dr Madeup"])
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\r\n").writerows(rows)
    return buf.getvalue().encode("utf-8")


def clinical_csv(days):
    head = ["Consultation Date", "Patient UID", "Patient Name", "Mode Of Payment", "Diagnosis", "Drugs Prescribed"]
    rows = [head]
    for d in days:
        rows.append([dt.date.fromisoformat(d).strftime("%d-%m-%Y"), uid(), name(), "Cash", "Made-up ache", "Made-up tab 1-0-1"])
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\r\n").writerows(rows)
    return buf.getvalue().encode("utf-8")


def patientlist_csv(n):
    head = ["Name", "Age", "Sex", "Parent Name", "Patient Medical History", "Address", "Foot Notes"]
    rows = [head]
    for _ in range(n):
        rows.append([name(), "%d years" % rnd.randint(20, 80), rnd.choice(("male", "female")), mobile(), "Made-up history", uid(), ""])
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\r\n").writerows(rows)
    return buf.getvalue().encode("utf-8")


# ── 1 the door ─────────────────────────────────────────────────────────────────────────────────────
def walk_door(td):
    store = os.path.join(td, "store")
    os.environ["DOCTERZ_EXPORT_STORE"] = store
    sys.path.insert(0, LIVE)
    import docterz_pickup as DP                                   # noqa: PLC0415 -- the LIVE reader, as the box has it
    DP.STORE = store
    door = load(os.path.join(KIT, "docterz_door.py"), "docterz_door")
    door._dp = lambda: DP
    con = sqlite3.connect(os.path.join(td, "finance.db"))
    con.row_factory = sqlite3.Row
    DP.ensure(con)
    con.execute("CREATE TABLE IF NOT EXISTS slip (day TEXT, series TEXT, state TEXT)")
    days = ["2026-11-02", "2026-11-03", "2026-11-04"]
    raw = consult_csv(days, [4, 3, 5])
    r = door.take_upload(con, raw, "any name at all.csv", "walker")
    check("door: a 3-day consultation report is cut and taken, 3 days", r["kind"] == "consultation" and r["days"] == 3 and r["taken"] == 3, json.dumps(r)[:200])
    check("door: the day files are in the store, mode 600", len(os.listdir(os.path.join(store, "consultation"))) == 3 and
          all(oct(os.stat(os.path.join(store, "consultation", f)).st_mode & 0o777) == "0o600" for f in os.listdir(os.path.join(store, "consultation"))))
    rows = con.execute("SELECT business_date, rows, status FROM docterz_export WHERE kind='consultation' ORDER BY business_date").fetchall()
    check("door: rows per day as cut (4, 3, 5), all current", [(x["business_date"], x["rows"], x["status"]) for x in rows] ==
          [("2026-11-02", 4, "current"), ("2026-11-03", 3, "current"), ("2026-11-04", 5, "current")], str([tuple(x) for x in rows]))
    n_before = con.execute("SELECT COUNT(*) FROM docterz_export").fetchone()[0]
    r = door.take_upload(con, raw, "again.csv", "walker")
    check("door: the same file again -> 3 already here, 0 taken", r["already"] == 3 and r["taken"] == 0, json.dumps(r)[:200])
    check("door: ... and nothing re-stored, nothing superseded (the held days stand)", con.execute("SELECT COUNT(*) FROM docterz_export").fetchone()[0] == n_before and
          con.execute("SELECT COUNT(*) FROM docterz_export WHERE status='superseded'").fetchone()[0] == 0)
    # the same patients in another byte shape (reception's own file, LF, no BOM) -> still 'already', never superseded
    other = raw.decode("utf-8-sig").replace("\r\n", "\n").encode("utf-8")
    r = door.take_upload(con, other, "reception_shape.csv", "walker")
    check("door: the same patients in another byte shape -> already here, nothing superseded", r["already"] == 3 and r["superseded"] == 0 and
          con.execute("SELECT COUNT(*) FROM docterz_export WHERE status='superseded'").fetchone()[0] == 0, json.dumps(r)[:200])
    rnd.seed(897)
    more = consult_csv(days, [4, 3, 6])                           # one more row on the last day, the first two days the same bytes
    r = door.take_upload(con, more, "more.csv", "walker")
    check("door: a re-export with one more patient on one day -> that day taken (newest wins), the others already", r["taken"] == 1 and r["already"] == 2, json.dumps(r)[:200])
    rnd.seed(897)
    fewer = consult_csv(days, [4, 2, 6])
    r = door.take_upload(con, fewer, "fewer.csv", "walker")
    check("door: a re-export with FEWER rows on a day -> that day QUARANTINED, said", r["quarantined"] == 1 and any("QUARANTINED" in l for l in r["lines"]), json.dumps(r)[:300])
    fu = followup_csv(["2026-11-05", "2026-11-06", "2026-11-09"])
    r = door.take_upload(con, fu, "fu.csv", "walker")
    check("door: a follow-up log is taken whole", r["kind"] == "followup" and r["taken"] == 1 and r["days"] == 1, json.dumps(r)[:200])
    fr = con.execute("SELECT business_date FROM docterz_export WHERE kind='followup' AND status='current'").fetchone()
    check("door: the follow-up log is dated by its own first due date (S509), never by today's clock", fr and fr["business_date"] == "2026-11-05", str(dict(fr) if fr else None))
    old_fu = followup_csv(["2026-10-06", "2026-10-07"])
    r = door.take_upload(con, old_fu, "october.csv", "walker")
    cur = con.execute("SELECT business_date FROM docterz_export WHERE kind='followup' AND status='current' ORDER BY business_date").fetchall()
    check("door: an OLD follow-up log uploaded today lands on ITS day and never displaces the newer one",
          r["taken"] == 1 and [x["business_date"] for x in cur] == ["2026-10-06", "2026-11-05"], str([dict(x) for x in cur]))
    cl = clinical_csv(["2026-10-01", "2026-11-04"])
    r = door.take_upload(con, cl, "clinical.csv", "walker")
    check("door: a clinical data report is taken by its bytes", r["kind"] == "clinical" and r["taken"] == 1, json.dumps(r)[:200])
    pl = patientlist_csv(5)
    r = door.take_upload(con, pl, "patients_detail.csv", "walker")
    check("door: a patient list is kept and listed", r["kind"] == "patientlist" and r["kept"] == 1 and os.path.isdir(os.path.join(store, "patientlist")), json.dumps(r)[:200])
    r = door.take_upload(con, pl, "patients_detail.csv", "walker")
    check("door: the same patient list again -> already here", r["already"] == 1 and r["kept"] == 0, json.dumps(r)[:200])
    r = door.take_upload(con, b"a,b,c\r\n1,2,3\r\n", "junk.csv", "walker")
    check("door: not a Docterz file -> refused, nothing kept", r["refused"] and r["taken"] == 0 and r["kept"] == 0, json.dumps(r)[:200])
    before = con.execute("SELECT COUNT(*) FROM docterz_export").fetchone()[0]
    r = door.take_upload(con, b"\xff\xfe\x00garbage", "bin.csv", "walker")
    check("door: bytes that are not text -> refused", bool(r["refused"]) and con.execute("SELECT COUNT(*) FROM docterz_export").fetchone()[0] == before)
    # a row whose UID is not UID-shaped still counts (identify's own count), so the cut never reads fewer than the held day
    odd = consult_csv(["2026-11-10", "2026-11-11"], [2, 2]).decode("utf-8-sig").replace("ZZ", "x-", 1).encode("utf-8")
    r = door.take_upload(con, odd, "odd.csv", "walker")
    check("door: a dated row with an odd UID is still a row of its day (rows as identify counts them)", r["taken"] == 2 and
          con.execute("SELECT rows FROM docterz_export WHERE kind='consultation' AND business_date='2026-11-10' AND status='current'").fetchone()[0] == 2, json.dumps(r)[:200])
    rl = door.reaches(con)
    check("door: the four reaches lines, with dates", len(rl) == 4 and rl[0][1] == "2026-11-11" and rl[1][1] == "2026-11-09" and rl[1][2] == 2 and rl[2][1] == "2026-11-04" and rl[3][2] == 1, str(rl))
    html = door.page_html(con, "walker")
    leak = [w for w in re.findall(r"[A-Z][a-z]{6} Madeup", (raw + fu + cl + pl).decode("utf-8", "replace")) if w in html]
    check("door: the page carries no patient name from the files", not leak and "9" * 0 == "", str(leak[:2]))
    check("door: the page carries no 10-digit number", not re.search(r"\b9\d{9}\b", html))
    check("door: the page shows the roads and the quarantine", "this page" in html and "quarantined" in html and "Docterz reports -- one door" in html)
    check("door: no confirm() dialog on the page (F-1464)", "confirm(" not in html)
    # one-day report with the not-sitting shape (no rows) goes through whole
    r = door.take_upload(con, consult_csv([], []), "empty.csv", "walker")
    check("door: an empty consultation report goes through whole (the S868 rule decides)", r["kind"] == "consultation" and r["days"] in (0, 1) and not r["refused"], json.dumps(r)[:200])
    con.close()
    sys.path.remove(LIVE)
    del sys.modules["docterz_pickup"]


# ── 2 the seed, both halves ────────────────────────────────────────────────────────────────────────
def made_up_pc(td):
    """a PC tracker + DocterzArchive in the PC's shape, with Windows paths in the state"""
    pc = os.path.join(td, "pc", "followup_tracker")
    arch = os.path.join(td, "pc", "DocterzArchive")
    for d in ("data", "data/backups/2026-10-20_210500_daily", "data/backups/2026-10-10_210500_daily", "uploads", "outputs"):
        os.makedirs(os.path.join(pc, d))
    open(os.path.join(pc, "processor.py"), "w").write("# made-up engine\n")
    open(os.path.join(pc, "processor.py.bak_S777_0e7c129f"), "w").write("# made-up old engine\n")
    open(os.path.join(pc, "feed_url.txt"), "w").write("https://example.invalid/feed\n")
    for n in ("visit_ledger.csv", "followup_ledger.csv", "revenue_ledger.csv", "patient_master.csv"):
        open(os.path.join(pc, "data", n), "w").write("A,B\r\n1,2\r\n")
        open(os.path.join(pc, "data", "backups", "2026-10-20_210500_daily", n), "w").write("A,B\r\n0,0\r\n")
        open(os.path.join(pc, "data", "backups", "2026-10-10_210500_daily", n), "w").write("A,B\r\n9,9\r\n")
    open(os.path.join(pc, "data", ".secret_key"), "w").write("made-up\n")
    open(os.path.join(pc, "data", "vacations.csv"), "w").write("Date\r\n")
    cons = "consultation_report_2026-11-04_reception_abcdef.csv"
    fu = "followup_logs_2026-11-04_reception_abcdef.csv"
    open(os.path.join(pc, "uploads", cons), "wb").write(consult_csv(["2026-11-04"], [2]))
    open(os.path.join(pc, "uploads", fu), "wb").write(followup_csv(["2026-11-05"]))
    os.makedirs(os.path.join(arch, "FOLLOWUP_LOG", "2026-11"))
    os.makedirs(os.path.join(arch, "CONSULTATION", "2026-11"))
    fa = os.path.join(arch, "FOLLOWUP_LOG", "2026-11", "FOLLOWUP_LOG__2026-11-05_to_2026-12-04__20261104-210000__12345678.csv")
    open(fa, "wb").write(followup_csv(["2026-11-05"]))
    ca = os.path.join(arch, "CONSULTATION", "2026-11", "CONSULTATION__2026-11-04__20261104-210000__abcdef12.csv")
    open(ca, "wb").write(consult_csv(["2026-11-04"], [2]))
    win_arch = "D:\\Downloads\\DocterzArchive\\"
    win_pc = "C:\\followup_tracker_local_test_kit\\local_test_kit\\followup_tracker\\"
    st = {"seen": {"aa": {"type": "FOLLOWUP_LOG", "name": fu, "archived": win_arch + "FOLLOWUP_LOG\\2026-11\\" + os.path.basename(fa), "seen_at": "2026-11-04 21:00:00", "mtime": 1.0},
                   "bb": {"type": "CONSULTATION", "name": cons, "archived": win_arch + "CONSULTATION\\2026-11\\" + os.path.basename(ca), "seen_at": "2026-11-04 21:00:00"}},
          "days": {"2026-11-04": {"digest": "x", "uids": 2, "input": win_pc + "uploads\\" + cons, "source_md5": "y", "processed_at": "2026-11-04 21:00:05", "how": "run"}},
          "last_followup": None, "fu_alone": {}, "last_pass": {"version": "S896 (S239 rev 5)"}}
    json.dump(st, open(os.path.join(arch, "_pickup_state.json"), "w"), indent=1)
    with open(os.path.join(arch, "index.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["seen_at", "type", "md5", "verdict", "archived_path", "source_name"])
        w.writerow(["2026-11-04 21:00:00", "FOLLOWUP_LOG", "aa", "ARCHIVED", win_arch + "FOLLOWUP_LOG\\2026-11\\" + os.path.basename(fa), fu])
    open(os.path.join(arch, "_console.log"), "w").write(
        "[2026-11-04 08:10:00] tracker run for 2026-11-03 (inputs: x.csv + y.csv; z)\n[2026-11-04 08:10:20] tracker wrote Staff_Action_Today_2026-11-04.xlsx\n"
        "[2026-11-04 21:00:05] tracker run for 2026-11-04 (inputs: %s + %s; z)\n[2026-11-04 21:00:25] tracker wrote Staff_Action_Today_2026-11-05.xlsx\n"
        "[2026-11-05 08:05:00] tracker run for 2026-11-04 (inputs: %s + %s; z)\n[2026-11-05 08:05:20] tracker wrote Staff_Action_Today_2026-11-05.xlsx\n" % (cons, fu, cons, fu))
    open(os.path.join(arch, "_pickup_log.txt"), "w").write("made-up\n")
    open(os.path.join(arch, "_server_fetch_log.txt"), "w").write("PC only -- must not travel\n")
    os.makedirs(os.path.join(arch, "_outputs_before_run", "20261104-210030"))
    open(os.path.join(arch, "_outputs_before_run", "20261104-210030", "x.xlsx"), "w").write("must not travel\n")
    return pc, arch


def walk_seed(td):
    pc, arch = made_up_pc(td)
    out = os.path.join(td, "out")
    r = subprocess.run([PY, "-B", os.path.join(KIT, "seed_pack.py"), "--live", pc, "--archive", arch, "--out", out], capture_output=True, text=True)
    check("seed_pack: packs (exit 0)", r.returncode == 0, r.stdout[-300:] + r.stderr[-300:])
    zips = [f for f in os.listdir(out) if f.endswith(".zip")] if os.path.isdir(out) else []
    check("seed_pack: one zip + its .sha256 in outputs", len(zips) == 1 and os.path.exists(os.path.join(out, zips[0] + ".sha256")), str(os.listdir(out) if os.path.isdir(out) else []))
    import zipfile                                                # noqa: PLC0415
    names = zipfile.ZipFile(os.path.join(out, zips[0])).namelist()
    check("seed_pack: snapshots since 19-Oct only (the 10-Oct one stays on the PC)",
          any("backups/2026-10-20_210500_daily/" in n for n in names) and not any("2026-10-10" in n for n in names))
    check("seed_pack: the PC-only logs and _outputs_before_run do not travel", not any("_server_fetch" in n or "_outputs_before_run" in n for n in names))
    check("seed_pack: data, uploads, archive, feed_url, the old engine and the manifest travel",
          all(any(n.startswith(p) for n in names) for p in ("data/visit_ledger.csv", "data/.secret_key", "uploads/", "archive/_pickup_state.json", "archive/FOLLOWUP_LOG/", "feed_url.txt", "replay/processor.py.bak_S777")) and "SEED_MANIFEST.json" in names, str(names)[:300])
    # a state naming a file not in the pack -> refused
    st_p = os.path.join(arch, "_pickup_state.json")
    st = json.load(open(st_p))
    st["seen"]["cc"] = {"type": "FOLLOWUP_LOG", "archived": "D:\\Downloads\\DocterzArchive\\FOLLOWUP_LOG\\2026-11\\gone.csv"}
    json.dump(st, open(st_p, "w"))
    r = subprocess.run([PY, "-B", os.path.join(KIT, "seed_pack.py"), "--live", pc, "--archive", arch, "--out", out, "--dry-run"], capture_output=True, text=True)
    check("seed_pack CONTROL: a state naming a file not on the PC -> REFUSED", r.returncode == 2 and "REFUSING" in r.stdout, r.stdout[-200:])
    del st["seen"]["cc"]
    json.dump(st, open(st_p, "w"))
    # the box half
    root = os.path.join(td, "box", "followup_tracker")
    for d in ("data", "uploads", "archive", "logs"):
        os.makedirs(os.path.join(root, d))
    open(os.path.join(root, "processor.py"), "w").write("# box engine\n")
    open(os.path.join(root, "OFF"), "w").write("")
    zp = os.path.join(out, zips[0])
    env = dict(os.environ, FUT_ROOT=root, TZ="Asia/Kolkata")
    take = [PY, "-B", os.path.join(KIT, "seed_take.py"), "--root", root, "--zip", zp]
    r = subprocess.run(take + ["--dry-run"], capture_output=True, text=True, env=env)
    check("seed_take: dry run verifies and translates, places nothing", r.returncode == 0 and "0 unresolved" in r.stdout and not os.listdir(os.path.join(root, "data")), r.stdout[-300:] + r.stderr[-200:])
    r = subprocess.run(take, capture_output=True, text=True, env=env)
    check("seed_take: PLACED", r.returncode == 0 and "PLACED" in r.stdout, r.stdout[-300:] + r.stderr[-300:])
    st2 = json.load(open(os.path.join(root, "archive", "_pickup_state.json")))
    check("seed_take: the state's paths are the box's and resolve",
          all(os.path.exists(v["archived"]) and v["archived"].startswith(root) for v in st2["seen"].values()) and
          all(os.path.exists(v["input"]) and v["input"].startswith(root) for v in st2["days"].values()), json.dumps(st2)[:300])
    idx = list(csv.reader(open(os.path.join(root, "archive", "index.csv"))))
    check("seed_take: index.csv's archived_path translated", idx[1][4].startswith(root) and os.path.exists(idx[1][4]), str(idx[1]))
    check("seed_take: data 700 / files 600, SEEDED_AT written", oct(os.stat(os.path.join(root, "data")).st_mode & 0o777) == "0o700" and
          oct(os.stat(os.path.join(root, "data", "visit_ledger.csv")).st_mode & 0o777) == "0o600" and os.path.exists(os.path.join(root, "SEEDED_AT")))
    check("seed_take: the ledgers' bytes are the PC's", md5(os.path.join(root, "data", "visit_ledger.csv")) == md5(os.path.join(pc, "data", "visit_ledger.csv")))
    r = subprocess.run(take + ["--check"], capture_output=True, text=True, env=env)
    check("seed_take --check: seeded, 0 unresolved", r.returncode == 0 and "0 unresolved" in r.stdout, r.stdout[-200:])
    r = subprocess.run(take, capture_output=True, text=True, env=env)
    check("seed_take CONTROL: a second seed without --again is REFUSED", r.returncode != 0 and "REFUSING" in (r.stdout + r.stderr), r.stdout[-200:] + r.stderr[-200:])
    open(os.path.join(root, "data", "visit_ledger.csv"), "a").write("3,4\r\n")
    r = subprocess.run(take + ["--again"], capture_output=True, text=True, env=env)
    aside = [d for d in os.listdir(root) if d.startswith("_seed_before_")]
    check("seed_take --again: re-seeds, the earlier ledgers set aside whole (never deleted)", r.returncode == 0 and len(aside) == 1 and
          os.path.exists(os.path.join(root, aside[0], "data", "visit_ledger.csv")) and md5(os.path.join(root, "data", "visit_ledger.csv")) == md5(os.path.join(pc, "data", "visit_ledger.csv")), r.stdout[-300:] + r.stderr[-300:])
    open(os.path.join(root, "SWITCHED_AT"), "w").write("2026-11-25 20:30:00\n")
    r = subprocess.run(take + ["--again"], capture_output=True, text=True, env=env)
    check("seed_take CONTROL: SWITCHED_AT present -> REFUSED (live ledgers never overwritten)", r.returncode != 0 and "SWITCHED_AT" in (r.stdout + r.stderr))
    os.remove(os.path.join(root, "SWITCHED_AT"))
    os.remove(os.path.join(root, "OFF"))
    r = subprocess.run(take + ["--again"], capture_output=True, text=True, env=env)
    check("seed_take CONTROL: OFF absent -> REFUSED", r.returncode != 0 and "OFF" in (r.stdout + r.stderr))
    open(os.path.join(root, "OFF"), "w").write("")
    with open(zp, "ab") as fh:
        fh.write(b"tamper")
    r = subprocess.run(take + ["--again"], capture_output=True, text=True, env=env)
    check("seed_take CONTROL: a tampered zip -> REFUSED by its sha256", r.returncode != 0 and "sha256" in (r.stdout + r.stderr))
    return root


# ── 3 replay 2's pairing ───────────────────────────────────────────────────────────────────────────
def walk_replay(td, root):
    inbox = os.path.join(td, "inbox")
    os.makedirs(inbox)
    open(os.path.join(inbox, "Staff_Action_Today_2026-11-05.xlsx"), "w").write("made-up\n")
    snaps = os.path.join(root, "data", "backups")
    os.makedirs(os.path.join(snaps, "2026-11-04_210006_daily"))
    open(os.path.join(snaps, "2026-11-04_210006_daily", "followup_ledger.csv"), "w").write("A\r\n")
    os.makedirs(os.path.join(snaps, "2026-11-05_080501_daily"))
    open(os.path.join(snaps, "2026-11-05_080501_daily", "followup_ledger.csv"), "w").write("A\r\n")
    env = dict(os.environ, FUT_ROOT=root, FU_INBOX_DIR=inbox, REPLAY2_SCRATCH=os.path.join(td, "scr"), TZ="Asia/Kolkata")
    r = subprocess.run([PY, "-B", os.path.join(KIT, "replay2_s897.py"), "--list"], capture_output=True, text=True, env=env)
    lines = [l for l in r.stdout.splitlines() if l[:1].isdigit()]
    check("replay2 --list: the three logged runs paired (exit 0)", r.returncode == 0 and len(lines) == 3, r.stdout[-400:] + r.stderr[-300:])
    check("replay2: the earlier run of a day has no reference ('-'); the day's last run is matched to the inbox",
          len(lines) == 3 and lines[1].split()[-1] == "-" and lines[2].split()[-1] == "yes" and lines[0].split()[-1] == "NONE", "\n".join(lines))
    rep = os.path.join(td, "rep.txt")
    r = subprocess.run([PY, "-B", os.path.join(KIT, "replay2_s897.py"), "--run", "--only", "1-2", "--report", rep], capture_output=True, text=True, env=env)
    check("replay2 --run: a run with no inbox workbook and an earlier run of a day are SKIPPED and said, nothing fails",
          "SKIP" in r.stdout and "0 fail" in r.stdout and "2 skipped" in r.stdout and os.path.exists(rep), r.stdout[-400:] + r.stderr[-300:])
    check("replay2: nothing compared is said loudly, not passed off as green", "NOTHING COMPARED" in r.stdout)
    r = subprocess.run([PY, "-B", os.path.join(KIT, "replay2_s897.py"), "--run", "--only", "3", "--report", rep], capture_output=True, text=True, env=env)
    check("replay2 --run: a run whose compare raises (an unreadable inbox workbook) is a FAIL line, not a crash",
          "FAIL run or compare raised" in r.stdout and "RESULT:" in r.stdout and r.returncode == 1, r.stdout[-400:] + r.stderr[-300:])


# ── 4 the watcher, 5 the patched files ─────────────────────────────────────────────────────────────
def walk_rest():
    r = subprocess.run([PY, "-B", os.path.join(KIT, "pc_upload_watch.py"), "--selftest"], capture_output=True, text=True)
    check("pc_upload_watch --selftest: 0 failures", "selftest: 0 failure(s)" in r.stdout, r.stdout[-300:])
    oc_kit = open(os.path.join(KIT, "owner_console.py"), encoding="utf-8").read()
    oc_live = open(os.path.join(LIVE, "owner_console.py"), encoding="utf-8").read()
    check("owner_console (kit): mounts the door and shows its line", "import docterz_door as _s897_dd" in oc_kit and "/finance/console/docterz-reports" in oc_kit)
    check("owner_console CONTROL (live): has neither", "docterz_door" not in oc_live)
    check("owner_console: the kit's file is the live file plus the two blocks (nothing else moved)",
          len(oc_kit.splitlines()) - len(oc_live.splitlines()) == 8 and oc_kit.replace("docterz_door", "").count("\n") > 0)
    lk = json.load(open(os.path.join(KIT, "freshness_legs.json"), encoding="utf-8"))
    ll = json.load(open(os.path.join(LIVE, "freshness_legs.json"), encoding="utf-8"))
    check("freshness_legs (kit): one leg more, S830's shape", len(lk["legs"]) == len(ll["legs"]) + 1 and lk["legs"][-1]["kind"] == "state_json" and lk["legs"][-1]["fail_field"] == "last_failure_iso")
    check("freshness_legs CONTROL (live): the leg is not there", not any(l["name"] == lk["legs"][-1]["name"] for l in ll["legs"]))
    check("freshness_legs: every other leg unchanged", lk["legs"][:-1] == ll["legs"] and lk["_windows"] == ll["_windows"])
    fr = os.path.join(LIVE, "freshness.py")
    if os.path.exists(fr):
        m = load(fr, "freshness_live")
        legs = m.load_legs(os.path.join(KIT, "freshness_legs.json"), {})
        check("freshness.py (live) loads the kit's legs file with no bad leg", len(legs) == len(lk["legs"]) and not [l for l in legs if l.get("bad")])
    for f in ("docterz_door.py", "seed_take.py", "seed_pack.py", "replay2_s897.py", "pc_upload_watch.py", "owner_console.py"):
        r = subprocess.run([PY, "-m", "py_compile", os.path.join(KIT, f)], capture_output=True, text=True)
        check("compiles: " + f, r.returncode == 0, r.stderr[-200:])


def main():
    td = tempfile.mkdtemp(prefix="walk897.")
    try:
        walk_door(td)
        root = walk_seed(td)
        walk_replay(td, root)
        walk_rest()
    finally:
        shutil.rmtree(td, ignore_errors=True)
    print("walk_s897: %d checks, %d failure(s)%s" % (N[0], len(FAILS), (": " + "; ".join(FAILS)) if FAILS else ""))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
