#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s449.py -- kit S449_RECEPTION_UPLOAD. THE REAL finance_app.py (a copy of /root/finance) over a SCRATCH COPY of
finance.db, with the door's key file, heartbeat file and export store all in the scratch folder. Two drivers:

  * Flask's test client, through the app's own gate, for every refusal and every verdict;
  * THE RECEPTION AGENT'S OWN CODE (reception/reception_agent.py, S449.1) posting over real HTTP to the same app served
    on 127.0.0.1 -- its key made in the scratch folder, its reports found in a scratch Downloads folder.

Every report here is made up in this file (clinic days in January 2031, no real person, no number). Nothing is posted to
the live door and nothing is written under /root/finance.

  --new NEW --old OLD    copies of /root/finance: the kit's files / the box as it is (the negative control)
  --db PATH              the scratch finance.db; PATH.old is made for the old app
"""
import argparse
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--new", "--old", "--db"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
KDIR = os.path.dirname(os.path.abspath(__file__))


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


copydb(a.db, a.db + ".old")

PROBE = r'''
import datetime as dt, hashlib, importlib.util, json, os, shutil, sqlite3, sys, threading, time
APP = os.environ["APPDIR"]; SCR = os.environ["SCRATCH"]; NEW = os.environ["MODE"] == "new"
sys.path.insert(0, APP); os.chdir(APP)
KEYS = os.path.join(SCR, "keys.txt"); BEAT = os.path.join(SCR, "beat.json"); STORE = os.path.join(SCR, "store")
os.environ.update(RECEPTION_KEYS=KEYS, RECEPTION_BEAT=BEAT, DOCTERZ_EXPORT_STORE=STORE)
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if (got is not None and not cond) else ""))
    if not cond:
        fails.append(label)

# the reception agent's own file is the signer and, later, the real client
AROOT = os.path.join(SCR, "pc"); os.makedirs(AROOT, exist_ok=True)
shutil.copy(os.environ["AGENT"], os.path.join(AROOT, "reception_agent.py"))
spec = importlib.util.spec_from_file_location("ra_walk", os.path.join(AROOT, "reception_agent.py"))
ra = importlib.util.module_from_spec(spec); spec.loader.exec_module(ra)
SK = bytes(range(1, 33)); PK = ra.ed_public(SK)
SK2 = bytes(range(2, 34))

import finance_app as fa
check("the finance app loads with every part mounted", not fa._MOUNT_FAILED, fa._MOUNT_FAILED)
c = fa.app.test_client()
RD = sys.modules.get("reception_door")
HB, RP = "/finance/api/reception/heartbeat", "/finance/api/reception/report"

def post(path, kind, body, name="", mtime="", sk=SK, ts=None, sig=None, sign_kind=None):
    ts = int(time.time()) if ts is None else ts
    msg = ra.upload_message(sign_kind or kind, ts, name, mtime, body)
    sg = (sig or ra.ed_sign(sk, msg)).hex()
    r = c.post(path, data=body, headers={"X-Rx-Time": str(ts), "X-Rx-Sig": sg, "X-Rx-Name": name, "X-Rx-Mtime": str(mtime),
                                         "Content-Type": "application/octet-stream"})
    return r.status_code, (r.get_json(silent=True) or {})

def rows(where="1=1", args=()):
    con = sqlite3.connect(os.environ["FINANCE_DB"]); con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute("SELECT * FROM docterz_export WHERE drive_id LIKE 'reception:%' AND " + where + " ORDER BY id", args)]
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()

def cons(day, people):
    return ("Patient Name,Consultation Date,Mode Of Payment,Amount\n" + "".join(
        "W449 TEST %s,%s,Cash,100\n" % (p, day) for p in people)).encode()

BEATJ = json.dumps({"agent_version": "walk", "attention": [], "google_drive_running": True,
                    "docterz_exports": {"consultation_today": 1}, "downloads_folder": {}}).encode()

if not NEW:
    # ---- the negative control: the box as it is has no door
    code, j = post(HB, "heartbeat", BEATJ)
    check("OLD APP: the heartbeat path is refused by the gate (401 not_signed_in)", code == 401 and j.get("error") == "not_signed_in", (code, j))
    check("OLD APP: no reception_door module", RD is None)
    print("WALK_S449 OLD %s (%d checks, %d failed)" % ("AS EXPECTED" if not fails else "UNEXPECTED", n, len(fails)))
    sys.exit(0 if not fails else 1)

# ---- 1. the signature code: the door verifies what the agent signs
VEC = [("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60", "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155" "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
       ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb", "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
        "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da" "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
       ("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7", "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025", "af82",
        "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac" "18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a")]
check("the door's verify passes the three RFC 8032 vectors",
      all(RD.ed_verify(bytes.fromhex(p), bytes.fromhex(m), bytes.fromhex(s)) for _k, p, m, s in VEC))
check("...and refuses each with one bit changed",
      not any(RD.ed_verify(bytes.fromhex(p), bytes.fromhex(m) + b"x", bytes.fromhex(s)) for _k, p, m, s in VEC))
check("the door and the agent build the same signed bytes",
      RD.upload_message("report", 123, "a (1).csv", 456, b"body") == ra.upload_message("report", 123, "a (1).csv", 456, b"body"))

# ---- 2. the door shut, then the refusals
for f in (KEYS, BEAT):
    if os.path.exists(f):
        os.remove(f)
code, j = post(HB, "heartbeat", BEATJ)
check("no key file on the server: 503 NO_KEY and nothing kept", code == 503 and j.get("status") == "NO_KEY" and not os.path.exists(BEAT), (code, j))
open(KEYS, "w").write("# walk key -- not a secret\n%s  walk-reception\n" % PK.hex())
r = c.post(HB, data=BEATJ)
check("no signature headers: the DOOR's own 401 (the gate let it through)", r.status_code == 401 and (r.get_json(silent=True) or {}).get("status") == "NOT_YOU", r.status_code)
code, j = post(HB, "heartbeat", BEATJ, sk=SK2)
check("a key that is not enrolled: 401, nothing kept", code == 401 and j.get("status") == "NOT_YOU" and not os.path.exists(BEAT), (code, j))
good_sig = ra.ed_sign(SK, ra.upload_message("heartbeat", int(time.time()), "", "", BEATJ))
code, j = post(HB, "heartbeat", BEATJ + b" ", sig=good_sig)
check("a changed body under a good signature: 401", code == 401, (code, j))
code, j = post(RP, "report", cons("07-01-2031", "A"), "x.csv", 1, sign_kind="heartbeat")
check("a signature made for a heartbeat does not open the report path: 401", code == 401, (code, j))
code, j = post(HB, "heartbeat", BEATJ, ts=int(time.time()) - 1200)
check("a request 20 minutes old (a replay): 401 CLOCK, nothing kept", code == 401 and j.get("status") == "CLOCK" and not os.path.exists(BEAT), (code, j))
code, j = post(HB, "heartbeat", b"x" * (RD.MAX_BEAT + 10))
check("an oversized heartbeat: 413", code == 413, (code, j))
code, j = post(HB, "heartbeat", b"[1,2]")
check("a heartbeat that is not a JSON object: 400", code == 400 and not os.path.exists(BEAT), (code, j))
check("GET on the door: 405", c.get(HB).status_code == 405)
r = c.post("/finance/api/reception/anything-else", data=b"{}")
check("the gate is still shut for the door's neighbours (401 not_signed_in)", r.status_code == 401 and (r.get_json(silent=True) or {}).get("error") == "not_signed_in")
check("...and for a page (/finance/health -> the login)", c.get("/finance/health").status_code in (302, 401))

# ---- 3. the heartbeat kept, and the health row
t0 = int(time.time())
code, j = post(HB, "heartbeat", BEATJ)
rec = json.load(open(BEAT)) if os.path.exists(BEAT) else {}
check("a signed heartbeat: 200 KEPT, written with this server's own clock, readable by root only",
      code == 200 and j.get("status") == "KEPT" and abs(rec.get("received_ts", 0) - t0) <= 5 and rec.get("from") == "walk-reception"
      and rec.get("beat", {}).get("agent_version") == "walk" and (os.stat(BEAT).st_mode & 0o777) == 0o600, (code, j, rec))
def hrow(now_ts=None, hour=11, weekday_shift=0):
    got = []
    ist = dt.datetime(2031, 1, 7 + weekday_shift, hour, 0)     # 07-Jan-2031 is a Tuesday; +5 = Sunday
    with fa.app.app_context():
        RD.health_row(lambda k, l, s, d, h="": got.append((k, s, d)), fa.setting, fa.db(), now_ts=now_ts, now_ist=ist)
    return got[0] if got else None
base = rec.get("received_ts", t0)
k, s, d = hrow(base + 60)
check("health: fresh heartbeat in the clinic day -> ok", (k, s) == ("reception", "ok") and "Google Drive running" in d, (k, s, d))
check("health: 20 minutes silent in the clinic day -> warn", hrow(base + 20 * 60)[1] == "warn")
check("health: 50 minutes silent in the clinic day -> bad", hrow(base + 50 * 60)[1] == "bad")
check("health: 50 minutes silent at 23:00 -> info", hrow(base + 50 * 60, hour=23)[1] == "info")
check("health: 50 minutes silent on a Sunday -> info", hrow(base + 50 * 60, weekday_shift=5)[1] == "info")
post(HB, "heartbeat", json.dumps({"agent_version": "walk", "attention": ["Google Drive is NOT running"], "google_drive_running": False}).encode())
k, s, d = hrow(time.time() + 30)
check("health: the PC's own attention line (Drive down) arrives by this road -> warn, in its words", s == "warn" and "Google Drive is NOT running" in d, (s, d))
os.remove(BEAT)
check("health: no heartbeat yet -> info, never a false green", hrow()[1] == "info")
post(HB, "heartbeat", BEATJ)
with fa.app.app_context():
    h = fa._health_state(fa.db())
hr = [x for x in h["checks"] if x["key"] == "reception"]
mr = [x for x in h["checks"] if x["key"] == "mounts"]
check("the REAL /finance/health state carries the Reception PC row", len(hr) == 1 and hr[0]["label"] == "Reception PC", hr)
check("...and counts 26 parts, all loaded", mr and mr[0]["state"] == "ok" and "all 26 parts" in mr[0]["detail"], mr)

# ---- 4. the reports, through docterz_pickup.take() -- the Drive pickup's own door
import docterz_pickup as DP
check("docterz_pickup is the live S443 file and keeps under the scratch store", DP.STORE == STORE)
A = cons("07-01-2031", "AB"); MT = 1925000000
code, j = post(RP, "report", A, "consultation_report_2031-01-07.csv", MT)
r1 = rows("business_date='2031-01-07'")
check("a consultation report: TAKEN, current, 2 rows, its day read from its content",
      code == 200 and j.get("status") == "TAKEN" and j.get("verdict") == "current" and j.get("day") == "2031-01-07" and j.get("rows") == 2
      and len(r1) == 1 and r1[0]["status"] == "current" and r1[0]["drive_id"] == "reception:" + hashlib.md5(A).hexdigest(), (code, j, r1))
check("its bytes are kept on the box only, mode 600", r1 and os.path.isfile(r1[0]["stored"]) and r1[0]["stored"].startswith(STORE)
      and open(r1[0]["stored"], "rb").read() == A and (os.stat(r1[0]["stored"]).st_mode & 0o777) == 0o600)
code, j = post(RP, "report", A, "consultation_report_2031-01-07.csv", MT)
check("the same report again: ALREADY, and no second row", code == 200 and j.get("status") == "ALREADY" and len(rows("business_date='2031-01-07'")) == 1, (code, j))
B = cons("07-01-2031", "ABC")
code, j = post(RP, "report", B, "consultation_report_2031-01-07 (1).csv", MT + 600)
r2 = rows("business_date='2031-01-07'")
check("a newer export of the day with more rows REPLACES it; the old one is kept as superseded",
      j.get("verdict") == "current" and [x["status"] for x in r2] == ["superseded", "current"], (j, [x["status"] for x in r2]))
C = cons("07-01-2031", "A")
code, j = post(RP, "report", C, "consultation_report_2031-01-07 (2).csv", MT + 1200)
r3 = rows("business_date='2031-01-07'")
check("a newer export with FEWER rows is quarantined and never replaces",
      j.get("verdict") == "quarantined" and [x["status"] for x in r3] == ["superseded", "current", "quarantined"], (j, [x["status"] for x in r3]))
D = cons("07-01-2031", "ABCD")
code, j = post(RP, "report", D, "consultation_report_older.csv", MT - 600)
check("an OLDER export of the day does not replace the current one", j.get("verdict") == "superseded"
      and [x["md5"] for x in rows("business_date='2031-01-07' AND status='current'")] == [hashlib.md5(B).hexdigest()], j)
F = b"Appointment ID,Patient Name,Mobile No,Due Date\nW1,W449 TEST A,x,09-01-2031\nW2,W449 TEST B,x,10-01-2031\n"
code, j = post(RP, "report", F, "followup_logs (4).csv", MT)
check("a follow-up log: TAKEN for the day before its earliest due date", j.get("status") == "TAKEN" and j.get("kind") == "followup" and j.get("day") == "2031-01-08", j)
before = len(rows()); nfiles = sum(len(fs) for _d, _s, fs in os.walk(STORE))
code, j = post(RP, "report", b"Name,Phone\nSOMEONE,private\n", "consultation_report_2031-01-09.csv", MT)
check("a file that is NOT one of the two reports: 400 REFUSED, no row, no file kept",
      code == 400 and j.get("status") == "REFUSED" and len(rows()) == before and sum(len(fs) for _d, _s, fs in os.walk(STORE)) == nfiles, (code, j))
code, j = post(RP, "report", b"x" * (RD.MAX_REPORT + 10), "big.csv", MT)
check("an oversized report: 413", code == 413, (code, j))
code, j = post(RP, "report", A, "bad\\name.csv", MT)
check("a name with a path in it: 401, nothing read", code == 401, (code, j))
# the two roads together
E = cons("09-01-2031", "AB")
con = sqlite3.connect(os.environ["FINANCE_DB"]); con.row_factory = sqlite3.Row
DP.take(con, {"id": "W449driveid1", "name": "consultation_report.csv", "modifiedTime": "2031-01-09T15:00:00.000Z"}, E)
code, j = post(RP, "report", E, "consultation_report_2031-01-09.csv", MT)
check("Drive brought it first, then the direct road: ALREADY (counted once)", j.get("status") == "ALREADY" and not rows("business_date='2031-01-09'"), j)
G = cons("10-01-2031", "AB")
post(RP, "report", G, "consultation_report_2031-01-10.csv", MT)
k2, d2, n2, st2, note2 = DP.take(con, {"id": "W449driveid2", "name": "consultation_report.csv", "modifiedTime": "2031-01-10T15:00:00.000Z"}, G)
cur = con.execute("SELECT COUNT(*) FROM docterz_export WHERE business_date='2031-01-10' AND status='current'").fetchone()[0]
con.close()
check("the direct road first, then Drive brings the same file: 'duplicate', still one current export for the day", st2 == "duplicate" and cur == 1, (st2, cur))

# ---- 5. THE AGENT'S OWN CODE over real HTTP
from werkzeug.serving import make_server
srv = make_server("127.0.0.1", 0, fa.app, threaded=True)
threading.Thread(target=srv.serve_forever, daemon=True).start()
home = os.path.join(SCR, "home"); dl = os.path.join(home, "Downloads"); os.makedirs(dl, exist_ok=True)
os.environ["USERPROFILE"] = home
def put(name, raw, age):
    p = os.path.join(dl, name); open(p, "wb").write(raw); t = time.time() - age; os.utime(p, (t, t)); return p
H1 = cons("13-01-2031", "ABC")
put("consultation_report_2031-01-13.csv", H1, 90)
put("followup_logs (9).csv", b"Appointment ID,Patient Name,Mobile No,Due Date\nW9,W449 TEST Z,x,15-01-2031\n", 3600)
put("W449 SOMEONE xray.jpg", b"not ours to read", 90)
put("consultation_report_lookalike.csv", b"Name,Phone\nSOMEONE,private\n", 90)
ra.find_my_drive = lambda: None                                # Google Drive is DOWN on this PC: the case this kit is for
ra.ensure_dirs()
json.dump({"server_url": "http://127.0.0.1:%d" % srv.server_port}, open(os.path.join(AROOT, "config.json"), "w"))
cfg = ra.load_config()
agent_pub = ra.upload_public()
st = ra.new_state()
beat, _p = ra.build_beat(st, cfg)
ra.direct_pass(st, cfg, beat)
check("AGENT, its key NOT enrolled: the server refuses it, no report is tried, the agent says so and lives",
      st["upload"]["ok_at"] is None and st["upload"]["fail_streak"] == 1 and "401" in (st["upload"]["last_error"] or "")
      and not rows("business_date='2031-01-13'"), st["upload"])
open(KEYS, "a").write("%s  reception-pc-walk\n" % agent_pub)
os.remove(BEAT)
beat, _p = ra.build_beat(st, cfg)
ra.direct_pass(st, cfg, beat)
rec = json.load(open(BEAT)) if os.path.exists(BEAT) else {}
check("AGENT, enrolled, WITH GOOGLE DRIVE DOWN: its real heartbeat is on the server",
      st["upload"]["ok_at"] and rec.get("from") == "reception-pc-walk" and rec.get("beat", {}).get("agent_version") == ra.AGENT_VERSION
      and rec["beat"].get("my_drive") is None, (st["upload"], list(rec)))
k, s, d = hrow(time.time() + 5)
check("...and the health row says what Drive's own heartbeat never could: My Drive is not visible", s == "warn" and "My Drive is not visible" in d, (s, d))
ra1 = rows("business_date='2031-01-13'"); ra2 = rows("kind='followup' AND business_date='2031-01-14'")
check("AGENT: both reports went from the Downloads folder to the server, each once",
      len(ra1) == 1 and ra1[0]["status"] == "current" and ra1[0]["rows"] == 3 and len(ra2) == 1 and st["upload"]["reports_sent"] == 2, (ra1, ra2, st["upload"]))
check("AGENT: the look-alike was refused by the agent itself and the photo never opened",
      len(json.load(open(ra.UPLOAD_SENT_FILE))) == 2 and not any("xray" in k[0] for k in st["upload_cache"]))
nrows = len(rows())
ra.direct_pass(st, cfg, ra.build_beat(st, cfg)[0])
st_b = ra.new_state(); ra.direct_pass(st_b, cfg, ra.build_beat(st_b, cfg)[0])
check("AGENT: the next pass, and a restarted agent, send nothing twice", len(rows()) == nrows and st_b["upload"]["reports_sent"] == 0)
os.remove(ra.UPLOAD_SENT_FILE)
st_c = ra.new_state(); ra.direct_pass(st_c, cfg, ra.build_beat(st_c, cfg)[0])
check("AGENT: even with its own ledger lost, the server answers ALREADY and nothing is counted twice",
      len(rows()) == nrows and st_c["upload"]["reports_sent"] == 2
      and all(v["status"] == "ALREADY" for v in json.load(open(ra.UPLOAD_SENT_FILE)).values()))
srv.shutdown()
st_d = ra.new_state()
for _ in range(3):
    ra.direct_pass(st_d, cfg, ra.build_beat(st_d, cfg)[0])
check("AGENT: the server gone -- three quiet failures, then one attention line; no exception",
      st_d["upload"]["fail_streak"] == 3 and any("direct upload" in x for x in ra.build_beat(st_d, cfg)[0]["attention"]))
leak = json.dumps(rec)
check("nothing of a patient is in the heartbeat file the server keeps", "W449" not in leak and ".csv" not in leak and ".jpg" not in leak)
print("WALK_S449 NEW %s (%d checks, %d failed)" % ("GREEN" if not fails else "RED", n, len(fails)))
for f in fails:
    print("   FAILED: " + f)
sys.exit(0 if not fails else 1)
'''

res = {}
for mode, app, db in (("new", a.new, a.db), ("old", a.old, a.db + ".old")):
    scr = os.path.join(os.path.dirname(os.path.abspath(a.db)), "scr_" + mode)
    os.makedirs(scr, exist_ok=True)
    env = dict(os.environ, APPDIR=os.path.abspath(app), SCRATCH=scr, MODE=mode, FINANCE_DB=os.path.abspath(db),
               AGENT=os.path.join(KDIR, "reception", "reception_agent.py"), PYTHONDONTWRITEBYTECODE="1")
    env.pop("FINANCE_MARG_TOKEN", None)
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, capture_output=True, text=True, timeout=900)
    out = [l for l in p.stdout.splitlines() if l.strip()]
    for l in out:
        print(("" if mode == "new" else "-- old: ") + l)
    if p.returncode != 0:
        print("-- %s probe exit %d: %s" % (mode, p.returncode, p.stderr.strip()[-1200:]))
    res[mode] = (p.returncode, out[-1] if out else "")
ok_new = res["new"][0] == 0 and "WALK_S449 NEW GREEN" in " ".join(o for o in [res["new"][1]])
ok_old = res["old"][0] == 0 and "WALK_S449 OLD AS EXPECTED" in res["old"][1]
print("WALK_S449 GREEN" if (ok_new and ok_old) else "WALK_S449 RED (new %s, negative control %s)"
      % ("green" if ok_new else "RED", "as expected" if ok_old else "NOT as expected"))
sys.exit(0 if (ok_new and ok_old) else 1)
