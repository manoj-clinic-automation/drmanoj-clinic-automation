#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s450.py -- kit S450_CLINIC_PCS_TILE. THE REAL finance_app.py and THE REAL portal.py (copies of /root/finance and
/root/portal) over a SCRATCH COPY of finance.db; the kit files of deploy_kits/PC_KITS exactly as the page will serve them;
the code store, its log, the reception key file and heartbeat all in the scratch folder.

  * Flask's test client through the finance app's own gate: the page as the owner and as anyone else, the button, the
    two doors with good, wrong and expired codes, a kit that is not whole;
  * THE CHAIN A SETUP FILE RUNS, over real HTTP: press the button, fetch both parts with the code, check them against
    the md5s written into the setup file, unpack the kit, hold every file to the kit's own MD5SUMS.txt, then run THE
    KIT'S OWN AGENT with `--enroll <code>` -- and read the reception key file, the door and the page afterwards.
    (The .cmd itself is Windows; it is rehearsed on the reception PC after the install.)
  * the portal: who is shown the tile.

  --new NEW --old OLD            copies of /root/finance: the kit's files / the box as it is (the negative control)
  --por-new P --por-old P        copies of /root/portal, likewise
  --db PATH                      the scratch finance.db; PATH.old is made for the old app
  --kits PATH                    deploy_kits/PC_KITS
  --vpy PATH                     the portal's interpreter (the venv python)
"""
import argparse
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--new", "--old", "--por-new", "--por-old", "--db", "--kits", "--vpy"):
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

FIN = r'''
import hashlib, importlib.util, io, json, os, re, shutil, sqlite3, subprocess, sys, threading, time, urllib.request, urllib.error, zipfile
APP = os.environ["APPDIR"]; SCR = os.environ["SCRATCH"]; NEW = os.environ["MODE"] == "new"; KITS = os.environ["KITS"]
sys.path.insert(0, APP); os.chdir(APP)
KEYS = os.path.join(SCR, "keys.txt"); BEAT = os.path.join(SCR, "beat.json")
os.environ.update(RECEPTION_KEYS=KEYS, RECEPTION_BEAT=BEAT, DOCTERZ_EXPORT_STORE=os.path.join(SCR, "store"),
                  PC_KITS_ROOT=KITS, PC_KIT_CODES=os.path.join(SCR, "codes.json"), PC_KIT_LOG=os.path.join(SCR, "log.txt"),
                  FINANCE_ALLOW_HEADER_AUTH="1")
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if (got is not None and not cond) else ""))
    if not cond:
        fails.append(label)
con = sqlite3.connect(os.environ["FINANCE_DB"])
OWNER = [r[0] for r in con.execute("SELECT username FROM unit_role WHERE unit='medical' AND role='checker' AND active=1")]
OTHER = [r[0] for r in con.execute("SELECT username FROM unit_role WHERE unit='medical' AND active=1 AND role<>'checker' "
                                   "AND lower(username) NOT IN (SELECT lower(username) FROM unit_role WHERE unit='medical' AND role='checker' AND active=1)")]
con.close()
import finance_app as fa
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
check("the finance app loads with every part mounted", not fa._MOUNT_FAILED, fa._MOUNT_FAILED)
check("the medical unit has exactly one checker -- the owner", len(OWNER) == 1, len(OWNER))
ME = OWNER[0] if OWNER else "nobody"
PK = sys.modules.get("pc_kits"); RD = sys.modules.get("reception_door")
if not NEW:
    r = c.get("/finance/pcs", headers=H(ME))
    check("OLD APP: no Clinic PCs page (404)", r.status_code == 404, r.status_code)
    r = c.get("/finance/api/pc-kit/fetch?part=kit", headers={"X-Kit-Code": "x" * 32})
    check("OLD APP: the kit door is shut by the gate (401 not_signed_in)", r.status_code == 401 and (r.get_json(silent=True) or {}).get("error") == "not_signed_in", r.status_code)
    check("OLD APP: no pc_kits module", PK is None)
    print("WALK_S450 FIN OLD %s (%d checks, %d failed)" % ("AS EXPECTED" if not fails else "UNEXPECTED", n, len(fails)))
    sys.exit(0 if not fails else 1)

# ---- 1. the page
open(KEYS, "w").write("# walk\n%s  receptionpc (the key before the reinstall)\n" % ("ab" * 32))
with fa.app.app_context():
    h = fa._health_state(fa.db())
mr = [x for x in h["checks"] if x["key"] == "mounts"]
check("the mounts row counts 27 parts, all loaded", mr and mr[0]["state"] == "ok" and "all 27 parts" in mr[0]["detail"], mr)
r = c.get("/finance/pcs", headers=H(ME)); page = r.get_data(as_text=True)
check("the owner opens the page: every PC of the mock is on it", r.status_code == 200 and all(w in page for w in (
    "Clinic PCs", "Reception PC", "Medical PC (Sanjeevni)", "Dr Manoj", "Shavez", "Pathology lab PC", "Not set up yet")), r.status_code)
check("the Reception PC has its button; the PCs whose kit is not packed have none -- and say so",
      page.count("<form method=post") == 1 and "/finance/pcs/setup/reception" in page and page.count("not on the server yet") == 2)
check("each working PC's line is the health page's own row, in its words",
      all((x["detail"][:40] in page.replace("&#x27;", "'").replace("&amp;", "&")) or (__import__("html").escape(x["detail"])[:40] in page)
          for x in h["checks"] if x["key"] in ("watcher", "pipeline")))
check("no identity: the gate sends the page to the login", c.get("/finance/pcs").status_code in (302, 401))
check("a login with no role in the medical unit: the gate sends it away", c.get("/finance/pcs", headers=H("w450nobody")).status_code in (302, 401))
if OTHER:
    r2 = c.get("/finance/pcs", headers=H(OTHER[0]))
    check("a medical login that is not the checker: 403 'not permitted', no button", r2.status_code == 403 and "<form" not in r2.get_data(as_text=True), r2.status_code)
    check("...and cannot press the button", c.post("/finance/pcs/setup/reception", headers=H(OTHER[0])).status_code == 403)

# ---- 2. the button
r = c.post("/finance/pcs/setup/reception", headers=H(ME)); cmd = r.get_data()
m = re.search(rb'set "CODE=([A-Za-z0-9_-]+)"', cmd); CODE = m.group(1).decode() if m else ""
info = PK.kit_info("reception")
check("the button hands over ONE file, ClinicSetup_Reception.cmd, as a download that is never cached",
      r.status_code == 200 and 'filename="ClinicSetup_Reception.cmd"' in r.headers.get("Content-Disposition", "")
      and r.headers.get("Cache-Control") == "no-store", (r.status_code, dict(r.headers)))
check("the file is plain ASCII with Windows line endings only, and nothing left unfilled",
      cmd.count(b"\n") == cmd.count(b"\r\n") > 60 and b"__" not in cmd and max(cmd) < 128)
check("it carries the code, this server's address and the two md5s the kit must match",
      len(CODE) >= 20 and b"https://followup.dr-manoj.in" in cmd and info["kit_md5"].encode() in cmd and info["python_md5"].encode() in cmd)
codes_raw = open(os.environ["PC_KIT_CODES"]).read()
check("the server keeps only the code's SHA-256, in a file root alone can read",
      CODE not in codes_raw and (os.stat(os.environ["PC_KIT_CODES"]).st_mode & 0o777) == 0o600 and CODE not in open(os.environ["PC_KIT_LOG"]).read())
check("a second press gives a different code", re.search(rb'set "CODE=([A-Za-z0-9_-]+)"', c.post("/finance/pcs/setup/reception", headers=H(ME)).get_data()).group(1).decode() != CODE)
check("a press from another site's page is refused (Origin)", c.post("/finance/pcs/setup/reception", headers=dict(H(ME), Origin="https://elsewhere.example")).status_code == 403)
check("a PC with no kit has no setup file (404)", c.post("/finance/pcs/setup/medical", headers=H(ME)).status_code == 404)
check("no identity cannot press the button", c.post("/finance/pcs/setup/reception").status_code in (302, 401))

# ---- 3. the two doors, by test client
F = "/finance/api/pc-kit/fetch"; E = "/finance/api/pc-kit/enroll"
check("fetch with no code: the DOOR's own 401", c.get(F + "?part=kit").status_code == 401 and "code" in (c.get(F + "?part=kit").get_json(silent=True) or {}).get("message", ""))
check("fetch with a code nobody was given: 401", c.get(F + "?part=kit", headers={"X-Kit-Code": "A" * 32}).status_code == 401)
r = c.get(F + "?part=kit", headers={"X-Kit-Code": CODE})
check("fetch with the code: the kit, byte for byte what KIT_INFO.txt says", r.status_code == 200 and hashlib.md5(r.get_data()).hexdigest() == info["kit_md5"])
r = c.get(F + "?part=python", headers={"X-Kit-Code": CODE})
check("...and the Python part", r.status_code == 200 and hashlib.md5(r.get_data()).hexdigest() == info["python_md5"])
check("a part that does not exist: 404", c.get(F + "?part=secrets", headers={"X-Kit-Code": CODE}).status_code == 404)
check("the code in the address bar opens nothing (it is read from the header only)", c.get(F + "?part=kit&code=" + CODE).status_code == 401)
OLDCODE = PK.mint("reception", "walk")
d = json.load(open(os.environ["PC_KIT_CODES"])); d[PK._h(OLDCODE)]["at"] = time.time() - 61 * 60; json.dump(d, open(os.environ["PC_KIT_CODES"], "w"))
check("a code 61 minutes old: 401 at both doors", c.get(F + "?part=kit", headers={"X-Kit-Code": OLDCODE}).status_code == 401
      and c.post(E, json={"pc_key": "cd" * 32}, headers={"X-Kit-Code": OLDCODE}).status_code == 401)
check("enrol: something that is not a public key: 400", c.post(E, json={"pc_key": "zz" * 32}, headers={"X-Kit-Code": CODE}).status_code == 400)
check("enrol: a good key with no code: 401, the key file untouched",
      c.post(E, json={"pc_key": "ab" * 32}).status_code in (400, 401) and open(KEYS).read().count("receptionpc") == 1)
real = PK.KIT_ROOT; bad = os.path.join(SCR, "badkits"); shutil.copytree(real, bad)
open(os.path.join(bad, "reception", "kit.zip"), "ab").write(b"x"); PK.KIT_ROOT = bad
pg = c.get("/finance/pcs", headers=H(ME)).get_data(as_text=True)
check("a kit that is not exactly what KIT_INFO.txt says: no button, no setup file, nothing served",
      "<form" not in pg and c.post("/finance/pcs/setup/reception", headers=H(ME)).status_code == 404
      and c.get(F + "?part=kit", headers={"X-Kit-Code": CODE}).status_code == 503)
PK.KIT_ROOT = real

# ---- 4. THE CHAIN A SETUP FILE RUNS, over real HTTP, ending with the kit's own agent
from werkzeug.serving import make_server
srv = make_server("127.0.0.1", 0, fa.app, threaded=True)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d" % srv.server_port
cmd = c.post("/finance/pcs/setup/reception", headers=H(ME)).get_data()
CODE2 = re.search(rb'set "CODE=([A-Za-z0-9_-]+)"', cmd).group(1).decode()
KITMD5 = re.search(rb'set "KITMD5=([0-9a-f]{32})"', cmd).group(1).decode(); PYMD5 = re.search(rb'set "PYMD5=([0-9a-f]{32})"', cmd).group(1).decode()
def get(part):
    return urllib.request.urlopen(urllib.request.Request(BASE + F + "?part=" + part, headers={"X-Kit-Code": CODE2}), timeout=60).read()
kit, py = get("kit"), get("python")
check("CHAIN: both parts arrive over HTTP and match the md5s written into the setup file", hashlib.md5(kit).hexdigest() == KITMD5 and hashlib.md5(py).hexdigest() == PYMD5)
PCROOT = os.path.join(SCR, "pc"); os.makedirs(PCROOT)
zipfile.ZipFile(io.BytesIO(kit)).extractall(os.path.join(PCROOT, "kit"))
sums = [l.split(None, 1) for l in open(os.path.join(PCROOT, "kit", "MD5SUMS.txt")).read().splitlines() if l.strip()]
okf = [(f.strip(), hashlib.md5(open(os.path.join(PCROOT, "kit", f.strip()), "rb").read()).hexdigest() == h) for h, f in sums if f.strip() != "pyportable.zip"]
check("CHAIN: every file in the kit is what the kit's own MD5SUMS.txt says (%d files)" % len(okf), len(okf) >= 9 and all(v for _f, v in okf), okf)
check("CHAIN: the Python part is the one MD5SUMS.txt names", any(f.strip() == "pyportable.zip" and h == hashlib.md5(py).hexdigest() for h, f in sums))
bat = open(os.path.join(PCROOT, "kit", "INSTALL_RECEPTION_AGENT.bat"), "rb").read()
check("CHAIN: the installer reached the PC with its Windows line endings (git would have stripped them)", bat.count(b"\r\n") > 100 and bat.count(b"\n") == bat.count(b"\r\n"))
zf = zipfile.ZipFile(io.BytesIO(py))
check("CHAIN: the Python part unpacks to pyportable/python.exe and pythonw.exe", "pyportable/python.exe" in zf.namelist() and "pyportable/pythonw.exe" in zf.namelist())
AG = os.path.join(PCROOT, "ClinicAgent"); os.makedirs(AG)
shutil.copy(os.path.join(PCROOT, "kit", "reception_agent.py"), AG)
json.dump({"server_url": BASE}, open(os.path.join(AG, "config.json"), "w"))
env = dict(os.environ, USERPROFILE=os.path.join(PCROOT, "home"), COMPUTERNAME="RECEPTIONPC"); os.makedirs(os.path.join(PCROOT, "home", "Downloads"))
before = open(KEYS).read()
p = subprocess.run([sys.executable, "-B", os.path.join(AG, "reception_agent.py"), "--enroll", "A" * 32], env=env, capture_output=True, text=True, timeout=120)
check("CHAIN: the kit's agent with a WRONG code -- refused, exit 1, the key file untouched", p.returncode == 1 and "did not take" in p.stdout and open(KEYS).read() == before, (p.returncode, p.stdout, p.stderr[-300:]))
p = subprocess.run([sys.executable, "-B", os.path.join(AG, "reception_agent.py"), "--enroll", CODE2], env=env, capture_output=True, text=True, timeout=120)
check("CHAIN: the kit's own agent, `--enroll <the code>`: exit 0 -- the server knows this PC and accepted its first report",
      p.returncode == 0 and "accepted its first report" in p.stdout, (p.returncode, p.stdout, p.stderr[-300:]))
newpub = None
try:
    spec = importlib.util.spec_from_file_location("ra_w450", os.path.join(AG, "reception_agent.py")); ra = importlib.util.module_from_spec(spec); spec.loader.exec_module(ra)
    newpub = ra.upload_public()
except Exception as ex:
    print("-- could not load the agent: %s" % ex)
keys_now = open(KEYS).read(); klines = [l for l in keys_now.splitlines() if "receptionpc" in l and not l.startswith("#")]
check("the key file now holds ONE key for the reception PC -- the new one; the old one is gone; the old file is kept as .prev",
      len(klines) == 1 and newpub and klines[0].startswith(newpub) and ("ab" * 32) not in keys_now and open(KEYS + ".prev").read() == before, klines)
check("...and the line says where it came from and who pressed the button", "Clinic PCs page" in klines[0] and ME in klines[0])
rec = json.load(open(BEAT)) if os.path.exists(BEAT) else {}
check("the door took the new PC's signed heartbeat (agent %s)" % rec.get("beat", {}).get("agent_version"),
      rec.get("beat", {}).get("computer") == "RECEPTIONPC" and rec.get("from", "").startswith("receptionpc"))
def signed_beat(sk):
    body = json.dumps({"agent_version": "walk", "attention": []}).encode(); ts = int(time.time())
    r = c.post("/finance/api/reception/heartbeat", data=body, headers={"X-Rx-Time": str(ts), "X-Rx-Name": "", "X-Rx-Mtime": "",
               "X-Rx-Sig": ra.ed_sign(sk, ra.upload_message("heartbeat", ts, "", "", body)).hex()})
    return r.status_code
check("the key of the old Windows no longer opens the door (401); the new PC's does (200)",
      signed_beat(bytes(range(1, 33))) == 401 and signed_beat(ra.upload_secret()) == 200)
r = c.post(E, json={"pc_key": newpub}, headers={"X-Kit-Code": CODE2})
check("the same file run twice: the same key again is 'already', and the key file does not grow", r.status_code == 200 and r.get_json().get("already") is True and open(KEYS).read().count("receptionpc") == 1)
check("...but the code cannot enrol a DIFFERENT key", c.post(E, json={"pc_key": ra.ed_public(bytes(range(3, 35))).hex()}, headers={"X-Kit-Code": CODE2}).status_code == 401)
srv.shutdown()

# ---- 5. the ticks and the trail
def beat(**ov):
    body = json.dumps(dict({"agent_version": "walk", "attention": [], "google_drive_running": ov.pop("drive", False), "my_drive": "G:\\My Drive" if ov.get("d2", True) else None}, owner_view=ov)).encode()
    ts = int(time.time())
    c.post("/finance/api/reception/heartbeat", data=body, headers={"X-Rx-Time": str(ts), "X-Rx-Name": "", "X-Rx-Mtime": "",
           "X-Rx-Sig": ra.ed_sign(ra.upload_secret(), ra.upload_message("heartbeat", ts, "", "", body)).hex()})
    return c.get("/finance/pcs", headers=H(ME)).get_data(as_text=True)
check("ticks: a PC that reports nothing done shows none", beat(drive=False, tailscale_running=False, share_ready=False).count("<li class=y>") == 0)
check("ticks: Drive signed in, Tailscale running, the share there -> three ticks", beat(drive=True, tailscale_running=True, share_ready=True).count("<li class=y>") == 3)
pg = c.get("/finance/pcs", headers=H(ME)).get_data(as_text=True)
check("the card says what kit the server holds and what last happened", info["version"] in pg and "agent S449" in info["version"] and "ENROLLED" in pg)
log = open(os.environ["PC_KIT_LOG"]).read()
check("the trail: made, fetched, enrolled -- and no code in it", all(w in log for w in ("setup file was made", "kit was fetched", "ENROLLED")) and CODE2 not in log and CODE not in log)
print("WALK_S450 FIN NEW %s (%d checks, %d failed)" % ("GREEN" if not fails else "RED", n, len(fails)))
for f in fails:
    print("   FAILED: " + f)
sys.exit(0 if not fails else 1)
'''

POR = r'''
import os, sys
APP = os.environ["APPDIR"]; NEW = os.environ["MODE"] == "new"
sys.path.insert(0, APP); os.chdir(APP)
os.environ["TILE_GRANTS_FILE"] = os.path.join(APP, "tile_grants.json")
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if (got is not None and not cond) else ""))
    if not cond:
        fails.append(label)
import portal
def sees(role, user, pc=False):
    return {t["name"]: g for g, items in portal._visible_sections(role, pc, user) for t in items}
m = sees("doctor", "manoj")
if not NEW:
    check("OLD PORTAL: no Clinic PCs tile for anyone", "Clinic PCs" not in m and not any(t["name"] == "Clinic PCs" for t in portal.TILES))
    print("WALK_S450 POR OLD %s (%d checks, %d failed)" % ("AS EXPECTED" if not fails else "UNEXPECTED", n, len(fails)))
    sys.exit(0 if not fails else 1)
check("the portal loads; the owner sees the tile, in Admin, beside Manage Users", m.get("Clinic PCs") == "Admin" and m.get("Manage Users") == "Admin", m.get("Clinic PCs"))
t = [x for x in portal.TILES if x["name"] == "Clinic PCs"][0]
check("the tile opens /finance/pcs and carries the approved words", t["url"] == "/finance/pcs" and t["live"] and "set one up again after a Windows reinstall" in t["desc"])
check("Dr Bhawna, also a doctor, is not shown it", "Clinic PCs" not in sees("doctor", "bhawna"))
check("no staff login is shown it", not any("Clinic PCs" in sees(r, u) for r, u in (("staff", "shavez"), ("staff", "reception"), ("manager", "shivani"), ("staff", "amir"), ("staff", "darpan"))))
check("every tile the owner had before is still there", len(m) >= 2 and all(k in m for k in ("System Board", "Manage Users", "Procedures & prices")))
os.environ["TILE_GRANTS_FILE"] = os.path.join(APP, "no_such_file.json"); portal.TILE_GRANTS_FILE = os.environ["TILE_GRANTS_FILE"]; portal._GRANTS_CACHE.update(mtime=None, data=None)
check("with the grants file lost, the owner still has the tile (the code's own fallback) and nobody else gains it",
      "Clinic PCs" in sees("doctor", "manoj") and "Clinic PCs" not in sees("doctor", "bhawna") and "Clinic PCs" not in sees("staff", "shavez"))
print("WALK_S450 POR NEW %s (%d checks, %d failed)" % ("GREEN" if not fails else "RED", n, len(fails)))
for f in fails:
    print("   FAILED: " + f)
sys.exit(0 if not fails else 1)
'''

res = {}
base = os.path.dirname(os.path.abspath(a.db))
runs = [("fin", "new", FIN, sys.executable, a.new, a.db), ("fin", "old", FIN, sys.executable, a.old, a.db + ".old"),
        ("por", "new", POR, a.vpy, a.por_new, ""), ("por", "old", POR, a.vpy, a.por_old, "")]
for part, mode, probe, exe, app, db in runs:
    scr = os.path.join(base, "scr_%s_%s" % (part, mode))
    os.makedirs(scr, exist_ok=True)
    env = dict(os.environ, APPDIR=os.path.abspath(app), SCRATCH=scr, MODE=mode, KITS=os.path.abspath(a.kits), PYTHONDONTWRITEBYTECODE="1")
    if db:
        env["FINANCE_DB"] = os.path.abspath(db)
    env.pop("FINANCE_MARG_TOKEN", None)
    p = subprocess.run([exe, "-B", "-c", probe], env=env, capture_output=True, text=True, timeout=900)
    out = [l for l in p.stdout.splitlines() if l.strip()]
    for l in out:
        if l.startswith(("  ok", "  FAIL", "   FAILED", "WALK_S450", "--")):
            print(("" if mode == "new" else "-- old: ") + l)
    if p.returncode != 0:
        print("-- %s %s probe exit %d: %s" % (part, mode, p.returncode, p.stderr.strip()[-1500:]))
    res[(part, mode)] = (p.returncode, " ".join(o for o in out if o.startswith("WALK_S450")))
good = (res[("fin", "new")][0] == 0 and "FIN NEW GREEN" in res[("fin", "new")][1] and res[("fin", "old")][0] == 0 and "FIN OLD AS EXPECTED" in res[("fin", "old")][1]
        and res[("por", "new")][0] == 0 and "POR NEW GREEN" in res[("por", "new")][1] and res[("por", "old")][0] == 0 and "POR OLD AS EXPECTED" in res[("por", "old")][1])
print("WALK_S450 GREEN" if good else "WALK_S450 RED: %s" % {"%s %s" % k: v[1] or ("exit %d" % v[0]) for k, v in res.items()})
sys.exit(0 if good else 1)
