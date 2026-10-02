#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s451.py -- kit S451_CLINIC_PCS_BUTTON. THE REAL finance_app.py (a copy of /root/finance) over a SCRATCH COPY of
finance.db; the kit files of deploy_kits/PC_KITS exactly as the page serves them; the code store, its log, the reception
key file and heartbeat all in the scratch folder. Everything walk_s450 walked is walked again, and on top of it:

  * F-684 -- THE PRESS, IN THE SHAPES A REAL BROWSER BEHIND THE REAL FRONT SERVER SENDS IT: the browser's own word
    (Sec-Fetch-Site) with Origin as sent, altered, "null" and missing; a browser that does not say; another site.
    Each refusal must say why, on the page and in the trail. THE BOX AS IT IS (S450) must show the defect.
  * F-685 -- the setup file names the computer, stops on the clinic's other PCs, asks when the name is new; the enrol
    door refuses another clinic PC's name -- by test client and by the kit's own agent -- and takes a brand-new name.

  --new NEW --old OLD            copies of /root/finance: with the kit's pc_kits.py / the box as it is (S450)
  --sso PATH                     a copy of /root/portal's *.py WITHOUT portal_config.py (the app imports its sso module)
  --db PATH                      the scratch finance.db; PATH.old is made for the old app
  --kits PATH                    deploy_kits/PC_KITS
"""
import argparse
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--new", "--old", "--sso", "--db", "--kits"):
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
SITE = "https://followup.dr-manoj.in"
def press(pc="reception", who=None, **hdr):
    h = dict(H(who or ME)); h.update({k.replace("_", "-"): v for k, v in hdr.items()})
    return c.post("/finance/pcs/setup/" + pc, headers=h)
if not NEW:
    check("OLD APP (S450, the box as it is): the page is there", c.get("/finance/pcs", headers=H(ME)).status_code == 200)
    r = press(Sec_Fetch_Site="same-origin", Origin="http://followup.dr-manoj.in")
    check("OLD APP, THE DEFECT (F-684): the owner's own press from the page itself, Origin altered on the way -- refused 403, and the page does not say why",
          r.status_code == 403 and "Not permitted" in r.get_data(as_text=True) and "did not come from this page" not in r.get_data(as_text=True), r.status_code)
    r = press(Sec_Fetch_Site="same-origin", Origin="https://127.0.0.1:8106")
    check("OLD APP: ...and again with Origin rewritten to the app's own address", r.status_code == 403, r.status_code)
    cmd = press().get_data()
    check("OLD APP (F-685): its setup file never asks which computer it is on", b"KITMD5" in cmd and b"COMPUTERNAME" not in cmd)
    print("WALK_S451 FIN OLD %s (%d checks, %d failed)" % ("AS EXPECTED" if not fails else "UNEXPECTED", n, len(fails)))
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
check("a login with no role in the medical unit: the gate sends it away", c.get("/finance/pcs", headers=H("w451nobody")).status_code in (302, 401))
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
      cmd.count(b"\n") == cmd.count(b"\r\n") > 60 and max(cmd) < 128
      and not any(w in cmd for w in (b"__CODE__", b"__SRV__", b"__KITMD5__", b"__PYMD5__", b"__OTHERS__", b"__EXPECT__")))   # not b"__": a code may hold two underscores
check("it carries the code, this server's address and the two md5s the kit must match",
      len(CODE) >= 20 and b"https://followup.dr-manoj.in" in cmd and info["kit_md5"].encode() in cmd and info["python_md5"].encode() in cmd)
codes_raw = open(os.environ["PC_KIT_CODES"]).read()
check("the server keeps only the code's SHA-256, in a file root alone can read",
      CODE not in codes_raw and (os.stat(os.environ["PC_KIT_CODES"]).st_mode & 0o777) == 0o600 and CODE not in open(os.environ["PC_KIT_LOG"]).read())
check("a second press gives a different code", re.search(rb'set "CODE=([A-Za-z0-9_-]+)"', c.post("/finance/pcs/setup/reception", headers=H(ME)).get_data()).group(1).decode() != CODE)
ok200 = lambda r: r.status_code == 200 and b'set "CODE=' in r.get_data()
check("F-684: a real browser's press from the page -- Sec-Fetch-Site same-origin, Origin this site -- is taken", ok200(press(Sec_Fetch_Site="same-origin", Origin=SITE)))
check("F-684: the browser says same-origin and the front server altered Origin (http, a port, the app's own address, another name): taken every time",
      all(ok200(press(Sec_Fetch_Site="same-origin", Origin=o)) for o in ("http://followup.dr-manoj.in", SITE + ":443", "http://127.0.0.1:8106", "https://127.0.0.1:8106", "https://localhost", "https://vps.internal.example")))
check("F-684: the browser says same-origin and Origin is 'null' or was stripped: taken", ok200(press(Sec_Fetch_Site="same-origin", Origin="null")) and ok200(press(Sec_Fetch_Site="same-origin")))
check("F-684: typed address / bookmark (Sec-Fetch-Site none) and a sister site of the clinic (same-site): taken", ok200(press(Sec_Fetch_Site="none")) and ok200(press(Sec_Fetch_Site="same-site", Origin="https://assets.dr-manoj.in")))
check("F-684: a browser that does not say -- Origin this site, with a slash, in capitals, http, 'null', or none at all: taken",
      all(ok200(press(Origin=o)) for o in (SITE, SITE + "/", "HTTPS://FOLLOWUP.DR-MANOJ.IN", "http://followup.dr-manoj.in", "null")) and ok200(press()))
r = press(Sec_Fetch_Site="cross-site", Origin=SITE); t = r.get_data(as_text=True)
check("ANOTHER SITE's page, the browser saying so (cross-site) even with this site's Origin: refused 403, and the page says why",
      r.status_code == 403 and "did not come from this page" in t and "the browser says cross-site" in t and b'set "CODE=' not in r.get_data(), r.status_code)
r = press(Origin="https://elsewhere.example"); t = r.get_data(as_text=True)
check("ANOTHER SITE's page from a browser that does not say: refused 403, and the page names where it came from",
      r.status_code == 403 and "it came from elsewhere.example" in t and b'set "CODE=' not in r.get_data(), r.status_code)
check("...a look-alike name is another site too", press(Origin="https://followup.dr-manoj.in.evil.example").status_code == 403 and press(Origin="https://evil-followup.dr-manoj.in").status_code == 403)
r = press(Origin="https://x.example/<script>alert(1)</script>")
check("...and what it says is escaped", r.status_code == 403 and "<script>" not in r.get_data(as_text=True))
log = open(os.environ["PC_KIT_LOG"]).read()
check("the trail has each refusal with what was seen -- and the card will show it", log.count("a press was REFUSED") == 5 and "the browser says cross-site [origin=https://followup.dr-manoj.in" in log and "it came from elsewhere.example [origin=https://elsewhere.example" in log, log[-600:])
n_codes = len(json.load(open(os.environ["PC_KIT_CODES"])))
press(Sec_Fetch_Site="cross-site"); press(Origin="https://elsewhere.example")
check("a refused press makes no code", len(json.load(open(os.environ["PC_KIT_CODES"]))) == n_codes)
if OTHER:
    check("the owner-only rule comes first: another medical login with a perfect browser press is still 403 'Not permitted'",
          press(who=OTHER[0], Sec_Fetch_Site="same-origin", Origin=SITE).status_code == 403 and "Not permitted" in press(who=OTHER[0], Sec_Fetch_Site="same-origin", Origin=SITE).get_data(as_text=True))
# ---- F-685: the setup file asks which computer it is on
lines = cmd.decode("ascii").split("\r\n")
iname = [i for i, l in enumerate(lines) if l.startswith('set "PCNAME=%COMPUTERNAME%"')]
ifirst = [i for i, l in enumerate(lines) if "curl.exe" in l or "mkdir" in l or "INSTALL_RECEPTION_AGENT" in l or "--enroll" in l]
check("F-685: the setup file reads the computer's name BEFORE it makes a folder, fetches, installs or enrols anything", len(iname) == 1 and ifirst and iname[0] < min(ifirst), (iname, ifirst[:3]))
stopline = [l for l in lines if l.startswith("for %%N in (")]
check("F-685: it stops on the clinic's other PCs by name -- MEDICAL and MANOJZ -- and never on the Reception PC's own",
      len(stopline) == 1 and stopline[0].startswith('for %%N in (MEDICAL MANOJZ) do if /i "%PCNAME%"=="%%N" set "WHY=') and stopline[0].endswith("& goto :stop") and "RECEPTIONPC" not in stopline[0], stopline)
igo = lines.index(":go") if ":go" in lines else -1
between = lines[iname[0]:igo] if iname and igo > 0 else []
check("F-685: named RECEPTIONPC it goes straight on; any other name it says so and asks Y/N, and N (or no answer) stops",
      'if /i "%PCNAME%"=="RECEPTIONPC" goto :go' in between and any(l.startswith("choice /c YN") for l in between)
      and any(l.startswith("if errorlevel 2 set \"WHY=") and l.endswith("& goto :stop") for l in between) and "echo   This computer is %PCNAME%." in between, between)
check("F-685: the labels the file jumps to are each there exactly once", all(lines.count(x) == 1 for x in (":go", ":stop", ":failed", ":fetched", ":unpack", ":done", ":cleanup", ":md5of", ":noenroll")))
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
for other in ("MEDICAL", "manojz"):
    p = subprocess.run([sys.executable, "-B", os.path.join(AG, "reception_agent.py"), "--enroll", CODE2], env=dict(env, COMPUTERNAME=other), capture_output=True, text=True, timeout=120)
    check("F-685 CHAIN: the kit's own agent run on %s with a GOOD code -- refused by name, exit 1, the key file untouched" % other.upper(),
          p.returncode == 1 and "did not take" in p.stdout and other.upper() in p.stdout and "other PCs" in p.stdout and open(KEYS).read() == before, (p.returncode, p.stdout, p.stderr[-300:]))
check("F-685: the trail says so, and the code is still good for the right PC", open(os.environ["PC_KIT_LOG"]).read().count("enrolment REFUSED: the computer says it is") == 2)
p = subprocess.run([sys.executable, "-B", os.path.join(AG, "reception_agent.py"), "--enroll", CODE2], env=env, capture_output=True, text=True, timeout=120)
check("CHAIN: the kit's own agent, `--enroll <the code>`: exit 0 -- the server knows this PC and accepted its first report",
      p.returncode == 0 and "accepted its first report" in p.stdout, (p.returncode, p.stdout, p.stderr[-300:]))
newpub = None
try:
    spec = importlib.util.spec_from_file_location("ra_w451", os.path.join(AG, "reception_agent.py")); ra = importlib.util.module_from_spec(spec); spec.loader.exec_module(ra)
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
r = c.post(E, json={"pc_key": newpub, "computer": "DESKTOP-7Q2K9A"}, headers={"X-Kit-Code": CODE2})
check("F-685: a name nobody knows -- a reinstalled Windows -- is taken (the setup file asked the person)", r.status_code == 200 and r.get_json().get("ok") is True)
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
print("WALK_S451 FIN NEW %s (%d checks, %d failed)" % ("GREEN" if not fails else "RED", n, len(fails)))
for f in fails:
    print("   FAILED: " + f)
sys.exit(0 if not fails else 1)
'''

res = {}
base = os.path.dirname(os.path.abspath(a.db))
runs = [("fin", "new", FIN, sys.executable, a.new, a.db), ("fin", "old", FIN, sys.executable, a.old, a.db + ".old")]
for part, mode, probe, exe, app, db in runs:
    scr = os.path.join(base, "scr_%s_%s" % (part, mode))
    os.makedirs(scr, exist_ok=True)
    env = dict(os.environ, APPDIR=os.path.abspath(app), SCRATCH=scr, MODE=mode, KITS=os.path.abspath(a.kits), PYTHONDONTWRITEBYTECODE="1",
               FINANCE_SSO_DIR=os.path.abspath(a.sso))
    if db:
        env["FINANCE_DB"] = os.path.abspath(db)
    env.pop("FINANCE_MARG_TOKEN", None)
    p = subprocess.run([exe, "-B", "-c", probe], env=env, capture_output=True, text=True, timeout=900)
    out = [l for l in p.stdout.splitlines() if l.strip()]
    for l in out:
        if l.startswith(("  ok", "  FAIL", "   FAILED", "WALK_S451", "--")):
            print(("" if mode == "new" else "-- old: ") + l)
    if p.returncode != 0:
        print("-- %s %s probe exit %d: %s" % (part, mode, p.returncode, p.stderr.strip()[-1500:]))
    res[(part, mode)] = (p.returncode, " ".join(o for o in out if o.startswith("WALK_S451")))
good = (res[("fin", "new")][0] == 0 and "FIN NEW GREEN" in res[("fin", "new")][1] and res[("fin", "old")][0] == 0 and "FIN OLD AS EXPECTED" in res[("fin", "old")][1])
print("WALK_S451 GREEN" if good else "WALK_S451 RED: %s" % {"%s %s" % k: v[1] or ("exit %d" % v[0]) for k, v in res.items()})
sys.exit(0 if good else 1)
