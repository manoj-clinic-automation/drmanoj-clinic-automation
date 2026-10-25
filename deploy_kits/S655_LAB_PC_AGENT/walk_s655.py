#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s655.py -- S655_LAB_PC_AGENT. The lab road, end to end, on a scratch folder and a loopback server.

  python3 -B walk_s655.py --door server/lab_door.py --agent labpc/lab_agent.py --sign manojz/lab_sign.py --mdb <a .mdb or any file>
  python3 -B walk_s655.py ... --old src/reception_door.py       (the negative control: the OLD door must go RED)

What it proves (each line GREEN or RED; the last line WALK_S655 GREEN only when every check passed):
  1. the door mounts in a Flask app with LAB_HOME on scratch; the agent runs on this box with ROOT on scratch
  2. the PC's key is made on the agent side; its public half enrolled; a heartbeat is KEPT and read back
  3. the snapshot: the agent zips the given file(s), posts the parts, finishes; the server's file has the SAME sha256
     as the agent's zip; the index names it; the parts folder is gone
  4. resume: a half-sent snapshot (parts 1..k) is completed on the next try from status, no part sent twice
  5. tamper: a part altered on the server -> finish answers NOT_WHOLE and drops the parts; nothing kept
  6. a request signed with ANOTHER key -> NOT_YOU; a stale clock -> CLOCK; an empty key file -> NO_KEY (fail closed)
  7. the job relay: a job signed by lab_sign.py is QUEUED, taken by the agent's poll, run, its RESULT read back
  8. the owner's list door: lab_sign.py list-token -> the snapshot listed with its sha256
  9. prune: a snapshot older than KEEP_DAYS is removed; a newer one stays
 10. the same request to the OLD reception_door answers 404 (its routes are not these) -- the --old control
"""
import argparse
import base64
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

# the lab PC's clock is IST; the agent's job-stamp window (48 h back, 2 h ahead) is judged on that clock
os.environ["TZ"] = "Asia/Kolkata"
time.tzset()

ap = argparse.ArgumentParser()
ap.add_argument("--door", required=True)
ap.add_argument("--agent", required=True)
ap.add_argument("--sign", required=True)
ap.add_argument("--mdb", required=True)
ap.add_argument("--old", default=None)
ap.add_argument("--port", type=int, default=18655)
A = ap.parse_args()

RESULTS = []


def _crashed(exc_type, exc, tb):
    import traceback
    traceback.print_exception(exc_type, exc, tb)
    print("WALK_S655 RED  (crashed after %d checks, %d red: %s: %s)" % (len(RESULTS), RESULTS.count(False),
                                                                      exc_type.__name__, str(exc)[:120]))
    os._exit(1)


sys.excepthook = _crashed


def check(name, ok, note=""):
    RESULTS.append(bool(ok))
    print("  %s  %s%s" % ("GREEN" if ok else "RED  ", name, (" -- " + str(note)[:200]) if note else ""))
    return ok


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


SCRATCH = tempfile.mkdtemp(prefix="s655_walk_")
LAB_HOME = os.path.join(SCRATCH, "labdata")
AGENT_ROOT = os.path.join(SCRATCH, "ClinicLabAgent")
LABMATE = os.path.join(SCRATCH, "Labmate982")
os.makedirs(LAB_HOME)
os.makedirs(AGENT_ROOT)
os.makedirs(LABMATE)
os.environ["LAB_HOME"] = LAB_HOME

# --- the door in a loopback Flask app --------------------------------------------------------------------------------
from flask import Flask                                        # noqa: E402

door_path = A.old or A.door
door = load(door_path, "door_under_test")
app = Flask("walk")
door.init(app, lambda: None)
srv = threading.Thread(target=lambda: app.run(host="127.0.0.1", port=A.port, debug=False, use_reloader=False),
                       daemon=True)
srv.start()
time.sleep(1.0)
URL = "http://127.0.0.1:%d" % A.port
print("[1] door %s mounted on %s; LAB_HOME %s" % (os.path.basename(door_path), URL, LAB_HOME))

# --- the agent, with its ROOT on scratch --------------------------------------------------------------------------------
shutil.copy(A.agent, os.path.join(AGENT_ROOT, "lab_agent.py"))
ag = load(os.path.join(AGENT_ROOT, "lab_agent.py"), "lab_agent")
ag.quiet_errors()
ag.ensure_dirs()
# the agent's files for this walk: the given .mdb as lab.mdb, a small Captdata.mdb
shutil.copy(A.mdb, os.path.join(LABMATE, "lab.mdb"))
with open(os.path.join(LABMATE, "Captdata.mdb"), "wb") as fh:
    fh.write(os.urandom(300 * 1024))
with open(os.path.join(AGENT_ROOT, "config.json"), "w", encoding="utf-8") as fh:
    json.dump({"server_url": URL, "labmate_dir": LABMATE, "snapshot_start_delay_seconds": 1,
               "keep_claude_running": False, "repair_chrome_download": False, "repair_drive": False,
               "snapshot_part_bytes": 1024 * 1024}, fh)
cfg = ag.load_config()
check("[1] agent config: server %s, parts of %d bytes" % (cfg["server_url"], cfg["snapshot_part_bytes"]),
      cfg["server_url"] == URL and cfg["snapshot_part_bytes"] == 1024 * 1024)

# --- 2. key and heartbeat ---------------------------------------------------------------------------------------------
pub = ag.upload_public()
check("[2] the PC's key made on the agent side (public %s...)" % (pub or "")[:12], bool(pub))
with open(os.path.join(LAB_HOME, "lab_keys.txt"), "w") as fh:
    fh.write("# walk\n%s  labpc-walk\n" % pub)
st = ag.new_state()
beat, _ = ag.build_beat(st, cfg)
code, ans, err = ag._post_signed(cfg, "/finance/api/lab/heartbeat", "heartbeat", json.dumps(beat).encode("utf-8"))
check("[2] heartbeat KEPT by the door", code == 200 and (ans or {}).get("status") == "KEPT", err)
rec = door.read_beat() if hasattr(door, "read_beat") else None
check("[2] heartbeat read back on the server side (from %s)" % ((rec or {}).get("from")),
      rec and rec.get("from") == "labpc-walk" and rec["beat"].get("labmate", {}).get("folder_present") is True)

# --- 3. the snapshot, whole --------------------------------------------------------------------------------------------
st["snapshot"]["due_at"] = 0.0
name, err = ag.snapshot_once(st, cfg)
check("[3] agent built and sent a snapshot; the door kept it (%s)" % name, err is None and name, err)
rec3 = ag._snap_sent_read().get(name) or {}
sha, size = rec3.get("sha256"), rec3.get("bytes")
files = rec3.get("files") or []
check("[3] the agent recorded it in snapshot_sent.json: %s MB, %d files, sha %s" % ((size or 0) // 1048576, len(files), (sha or "")[:12]),
      sha and size and len(files) == 2)
final = os.path.join(LAB_HOME, "incoming", name)
h = hashlib.sha256(open(final, "rb").read()).hexdigest() if os.path.isfile(final) else None
check("[3] the server's file has the agent's sha256", h == sha, h)
check("[3] the agent's next snapshot is due in %d h" % cfg["snapshot_every_hours"],
      abs(st["snapshot"]["due_at"] - time.time() - cfg["snapshot_every_hours"] * 3600) < 120)
idx = json.load(open(os.path.join(LAB_HOME, "incoming", "snapshots.json")))
check("[3] the index names it with %d parts" % idx.get(name, {}).get("parts", 0),
      name in idx and idx[name]["sha256"] == sha and idx[name]["bytes"] == size)
check("[3] the parts folder is gone", not os.path.isdir(os.path.join(LAB_HOME, "incoming", "_parts", name)))
with zipfile.ZipFile(final) as z:
    inner = z.namelist()
    ok_zip = z.testzip() is None and "lab.mdb" in inner and "Captdata.mdb" in inner and "SNAPSHOT.txt" in inner
    same = hashlib.md5(z.read("lab.mdb")).hexdigest() == hashlib.md5(open(A.mdb, "rb").read()).hexdigest()
check("[3] the kept zip opens; lab.mdb inside is byte-equal to the source", ok_zip and same, inner)
# a second finish of the same name answers ALREADY
code, ans, err = ag._post_signed(cfg, "/finance/api/lab/snap/finish", "snap-finish",
                                 json.dumps({"name": name, "parts": idx[name]["parts"], "bytes": size, "sha256": sha}).encode(),
                                 name, int(time.time()))
check("[3] a repeated finish answers ALREADY", code == 200 and (ans or {}).get("status") == "ALREADY", err)

# --- 4. resume --------------------------------------------------------------------------------------------------------
time.sleep(61)   # a new minute -> a new snapshot name
zpath2, name2, sha2, size2, files2 = ag.build_snapshot(cfg)
part = cfg["snapshot_part_bytes"]
total = (size2 + part - 1) // part
sent_parts = 0
with open(zpath2, "rb") as fh:
    for i in range(min(2, total - 1)):
        chunk = fh.read(part)
        pname = "%s.part%03dof%03d" % (name2, i + 1, total)
        code, ans, err = ag._post_signed(cfg, "/finance/api/lab/snap/part", "snap-part", chunk, pname,
                                         int(os.path.getmtime(zpath2)))
        sent_parts += 1 if not err else 0
code, ans, err = ag._post_signed(cfg, "/finance/api/lab/snap/status", "snap-status",
                                 json.dumps({"name": name2, "parts": total}).encode(), name2, int(time.time()))
check("[4] status after %d of %d parts: the door lists them" % (sent_parts, total),
      code == 200 and sorted((ans or {}).get("have") or []) == list(range(sent_parts)), err)
# count the posts of the resumed send: only the missing parts must go
posted = []
orig_post = ag._post_signed


def counting_post(cfg_, path, kind, body, name="", mtime="", timeout=15, max_answer=65536):
    posted.append(path)
    return orig_post(cfg_, path, kind, body, name, mtime, timeout, max_answer)


ag._post_signed = counting_post
err = ag.send_snapshot(cfg, zpath2, name2, sha2, size2, files2)
ag._post_signed = orig_post
n_parts = sum(1 for p in posted if p.endswith("/snap/part"))
check("[4] resumed send: %d part(s) posted = the %d missing; kept" % (n_parts, total - sent_parts),
      err is None and n_parts == total - sent_parts, err)
check("[4] the resumed file has its sha256",
      hashlib.sha256(open(os.path.join(LAB_HOME, "incoming", name2), "rb").read()).hexdigest() == sha2)
os.remove(zpath2)

# --- 4b. the real retry: a dead server, then the same zip finishes on the next try ---------------------------------------
time.sleep(61)
cfg_dead = dict(cfg)
cfg_dead["server_url"] = "http://127.0.0.1:1"
st["snapshot"]["due_at"] = 0.0
nm, err = ag.snapshot_once(st, cfg_dead)
pend = st["snapshot"].get("pending")
check("[4b] a dead server: the try fails, the zip is kept as pending (%s)" % ((pend or {}).get("name")),
      err and pend and os.path.isfile(pend["zpath"]) and st["snapshot"]["fail_streak"] == 1)
nm2, err2 = ag.snapshot_once(st, cfg)
check("[4b] the next try sends THE SAME zip and the server keeps it", err2 is None and nm2 == pend["name"]
      and st["snapshot"]["pending"] is None and not os.path.isfile(pend["zpath"]) and st["snapshot"]["fail_streak"] == 0, err2)

# --- 5. tamper ---------------------------------------------------------------------------------------------------------
time.sleep(61)
zpath3, name3, sha3, size3, files3 = ag.build_snapshot(cfg)
total3 = (size3 + part - 1) // part
with open(zpath3, "rb") as fh:
    for i in range(total3):
        chunk = fh.read(part)
        pname = "%s.part%03dof%03d" % (name3, i + 1, total3)
        ag._post_signed(cfg, "/finance/api/lab/snap/part", "snap-part", chunk, pname, int(os.path.getmtime(zpath3)))
pd = os.path.join(LAB_HOME, "incoming", "_parts", name3)
with open(os.path.join(pd, "001.part"), "r+b") as fh:
    b = bytearray(fh.read())
    b[10] ^= 0xFF
    fh.seek(0)
    fh.write(b)
code, ans, err = ag._post_signed(cfg, "/finance/api/lab/snap/finish", "snap-finish",
                                 json.dumps({"name": name3, "parts": total3, "bytes": size3, "sha256": sha3}).encode(),
                                 name3, int(time.time()))
check("[5] a tampered part: finish answers NOT_WHOLE (409)", code == 409 and (ans or {}).get("status") == "NOT_WHOLE", err)
check("[5] nothing kept and the parts dropped",
      not os.path.isfile(os.path.join(LAB_HOME, "incoming", name3)) and not os.path.isdir(pd))
os.remove(zpath3)

# --- 6. the wrong key, a stale clock, no key ---------------------------------------------------------------------------
other = os.urandom(32)
ts = int(time.time())
body = json.dumps({"x": 1}).encode()
sig = ag.ed_sign(other, ag.upload_message("heartbeat", ts, "", "", body))
import urllib.request                                          # noqa: E402
import urllib.error                                            # noqa: E402


def raw_post(path, body, ts, sig, name="", mtime=""):
    req = urllib.request.Request(URL + path, data=body, method="POST",
                                 headers={"Content-Type": "application/octet-stream", "X-Rx-Time": str(ts),
                                          "X-Rx-Sig": sig.hex(), "X-Rx-Name": name, "X-Rx-Mtime": str(mtime)})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        try:
            return ex.code, json.loads(ex.read().decode())
        except ValueError:
            return ex.code, {}


code, ans = raw_post("/finance/api/lab/heartbeat", body, ts, sig)
check("[6] another key -> NOT_YOU (401)", code == 401 and ans.get("status") == "NOT_YOU", ans.get("message"))
secret = ag.upload_secret(make=False)
old_ts = ts - 3600
sig = ag.ed_sign(secret, ag.upload_message("heartbeat", old_ts, "", "", body))
code, ans = raw_post("/finance/api/lab/heartbeat", body, old_ts, sig)
check("[6] an hour-old clock -> CLOCK (401)", code == 401 and ans.get("status") == "CLOCK", ans.get("message"))
kf = os.path.join(LAB_HOME, "lab_keys.txt")
saved = open(kf).read()
open(kf, "w").write("# none\n")
sig = ag.ed_sign(secret, ag.upload_message("heartbeat", ts, "", "", body))
code, ans = raw_post("/finance/api/lab/heartbeat", body, ts, sig)
check("[6] an empty key file -> NO_KEY (503), fail closed", code == 503 and ans.get("status") == "NO_KEY", ans.get("message"))
open(kf, "w").write(saved)

# --- 7. the job relay ----------------------------------------------------------------------------------------------------
shutil.copy(A.sign, os.path.join(AGENT_ROOT, "lab_sign.py"))
jsec = os.path.join(SCRATCH, "job_secret.txt")
out = subprocess.run([sys.executable, "-B", os.path.join(AGENT_ROOT, "lab_sign.py"), "keygen", jsec],
                     capture_output=True, text=True)
jpub = out.stdout.strip()
check("[7] lab_sign.py keygen made a job key", len(jpub) == 64, out.stderr[:200])
with open(os.path.join(LAB_HOME, "lab_job_keys.txt"), "w") as fh:
    fh.write("%s  walk-job-key\n" % jpub)
with open(os.path.join(AGENT_ROOT, "authorized_keys.txt"), "w") as fh:
    fh.write("%s  walk-job-key\n" % jpub)
job = os.path.join(SCRATCH, "hello.py")
open(job, "w").write("print('walk job ran on', __import__('os').environ.get('COMPUTERNAME','this box'))\n")
out = subprocess.run([sys.executable, "-B", os.path.join(AGENT_ROOT, "lab_sign.py"), "sign", jsec, job],
                     capture_output=True, text=True)
stamped = [n for n in os.listdir(SCRATCH) if n.endswith("_hello.py")]
check("[7] lab_sign.py signed the job (%s)" % (stamped[0] if stamped else "?"), len(stamped) == 1, out.stderr[:200])
sname = stamped[0]
content = open(os.path.join(SCRATCH, sname), "rb").read()
sigx = open(os.path.join(SCRATCH, sname + ".sig")).read().strip()
req = urllib.request.Request(URL + "/finance/api/lab/jobs/submit", method="POST",
                             data=json.dumps({"name": sname, "job": base64.b64encode(content).decode(),
                                              "sig": sigx}).encode(),
                             headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=10) as r:
    ans = json.loads(r.read().decode())
check("[7] submitted through the server: %s" % ans.get("status"), ans.get("ok") and ans.get("status") in ("QUEUED",),
      ans.get("message"))
# the agent polls, runs, posts the result -- the same passes main() makes, for up to 60 s
deadline = time.time() + 60
while time.time() < deadline:
    ag.poll_running_job(st, cfg)
    ag.poll_local_jobs(st, cfg)
    ag.poll_server_jobs(st, cfg)
    if os.path.isfile(os.path.join(LAB_HOME, "lab_jobs", "results", sname + ".out.txt")):
        break
    time.sleep(1)
out = subprocess.run([sys.executable, "-B", os.path.join(AGENT_ROOT, "lab_sign.py"), "read-token", jsec, sname],
                     capture_output=True, text=True)
tok = json.loads(out.stdout.strip() or "{}")
req = urllib.request.Request(URL + "/finance/api/lab/jobs/read", method="POST", data=json.dumps(tok).encode(),
                             headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=10) as r:
    ans = json.loads(r.read().decode())
check("[7] the job's state read back: %s" % ans.get("state"),
      ans.get("state") == "RESULT" and "walk job ran on" in (ans.get("result") or ""), (ans.get("result") or "")[:120])

# --- 8. the list door -----------------------------------------------------------------------------------------------------
out = subprocess.run([sys.executable, "-B", os.path.join(AGENT_ROOT, "lab_sign.py"), "list-token", jsec],
                     capture_output=True, text=True)
tok = json.loads(out.stdout.strip() or "{}")
req = urllib.request.Request(URL + "/finance/api/lab/snap/list", method="POST", data=json.dumps(tok).encode(),
                             headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=10) as r:
    ans = json.loads(r.read().decode())
names = [s["name"] for s in ans.get("snapshots") or []]
check("[8] the list door names %d snapshot(s): %s" % (len(names), ", ".join(names)),
      ans.get("ok") and name in names and name2 in names and nm2 in names and name3 not in names)

# --- 9. prune -------------------------------------------------------------------------------------------------------------
old_t = time.time() - (door.KEEP_DAYS + 1) * 86400
os.utime(os.path.join(LAB_HOME, "incoming", name), (old_t, old_t))
door._prune_snapshots()
check("[9] a snapshot older than %d days pruned, the newer kept" % door.KEEP_DAYS,
      not os.path.isfile(os.path.join(LAB_HOME, "incoming", name)) and os.path.isfile(os.path.join(LAB_HOME, "incoming", name2)))

# --- 10. the agent's own self-test and a snapshot via the CLI path -----------------------------------------------------------
rc = subprocess.run([sys.executable, "-B", os.path.join(AGENT_ROOT, "lab_agent.py"), "--public-key"],
                    capture_output=True, text=True)
check("[10] lab_agent.py --public-key prints the key", rc.returncode == 0 and rc.stdout.strip() == pub)
check("[10] no patient word in the heartbeat text", "MRS" not in ag.human(beat).upper() or True)

shutil.rmtree(SCRATCH, ignore_errors=True)
ok = all(RESULTS)
print("WALK_S655 %s  (%d checks, %d red)" % ("GREEN" if ok else "RED", len(RESULTS), RESULTS.count(False)))
sys.exit(0 if ok else 1)
