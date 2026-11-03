#!/usr/bin/env python3
"""walk_swap_s701.py -- kit S701_WA_KEY_SWAP's walk of swap_key_s701.py. Nothing real is read or written: a made-up server
tree in a temp folder (made-up keys, made-up services), a stand-in systemctl and crontab, a fake /proc, and a stand-in
MyOperator on 127.0.0.1 that accepts or refuses each key as the step orders.
  python3 walk_swap_s701.py <swap_key_s701.py> <dir holding portal/portal_inbox.py + inbox_retry.py>
Prints one line per check and 'N of N green' last."""
import hashlib, http.server, json, os, shutil, stat, subprocess, sys, tempfile, threading

TOOL = os.path.abspath(sys.argv[1])
PORTAL_SRC = os.path.abspath(os.path.join(sys.argv[2], "portal"))
OLD = "wALKoldKEYxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx1"          # 42 characters, made up
NEW = "wALKnewKEYyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy2"          # same shape
NEW_LONG = "wALKnewKEYzz" + "z" * 50
OTHER = "wALKotherKEYqqqqqqqqqqqqqqqqqqqqqqqqqqqqq3"
assert len(OLD) == len(NEW) == 42
MODE = {"m": "new_ok"}
ASKED = []


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        tok = (self.headers.get("Authorization") or "").replace("Bearer ", "")
        ASKED.append(tok[:8])
        ok = (MODE["m"] == "new_ok" and tok in (NEW, NEW_LONG)) or (MODE["m"] == "old_ok" and tok == OLD)
        code = 200 if ok else (401 if MODE["m"] == "new_401" and tok == NEW else 500)
        body = b'{"status":"success","data":[]}' if ok else (b'{"message":"Unauthorized"}' if code == 401 else b'{"message":null}')
        self.send_response(code)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
RES, OUTS = [], []


def check(name, fn):
    try:
        ok, note = fn()
    except Exception as e:                                              # noqa: BLE001
        ok, note = False, "%s: %s" % (type(e).__name__, e)
    RES.append(bool(ok))
    print("%s  %s%s" % ("GREEN" if ok else "RED  ", name, ("  -- " + str(note)[:240]) if (note and not ok) else ""), flush=True)


def w(path, text, mode=0o600):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    os.chmod(path, mode)


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def build(T, approve_key=OLD, extras=False):
    R = os.path.join(T, "root")
    w(R + "/wa/.env", "MYOP_WABA_ID=2101222617483538\nMYOP_AUTH_TOKEN=%s\nWATCHDOG_SMTP_USER=walk@example.invalid\n" % OLD)
    w(R + "/wa/wa_approve.env", "MYOP_AUTH_TOKEN=\"%s\"\n" % approve_key, 0o640)
    w(R + "/portal/portal_config.py", "PORTAL_WA_DRYRUN = '0'\nMYOP_AUTH_TOKEN = '%s'   # S599\n" % OLD, 0o600)
    w(R + "/wa/other_tool.py", "TOKEN = '%s'  # a holder nobody listed\n" % OLD, 0o700)
    w(R + "/s599_backup/config.json.before_s599", '{"k": "%s"}' % OLD)
    w(R + "/portal/portal_config.py.bak_S599", "MYOP_AUTH_TOKEN = '%s'\n" % OLD)
    if extras:                                         # a log and the repository copy holding the key: Claude must look first
        w(R + "/wa/wa_logs/2026-11-02.jsonl", '{"auth": "%s"}\n' % OLD)
        w(R + "/deploy/repo/leak.txt", OLD)
    w(R + "/state_backup/clinic_state_backup.py", "K = '%s'  # live code in a folder named state_backup\n" % OLD, 0o700)
    w(R + "/wa/notifier_x.py", "import os\nTOK = os.environ.get('MYOP_AUTH_TOKEN')  # reads the key at start\n", 0o700)
    w(R + "/wa/venv/lib/site.py", OLD)
    w(R + "/wa/recordings-archive/call.mp3", "ID3" + OLD)
    w(R + "/wa/nothing.py", "print('no key here')\n")
    U = os.path.join(T, "etc/systemd/system")
    w(U + "/wa-approve.service.d/override.conf", "[Service]\nEnvironment=MYOP_AUTH_TOKEN=%s\n" % OLD, 0o644)
    w(U + "/wa-approve.service", "[Service]\nEnvironmentFile=%s/wa/wa_approve.env\nExecStart=/x/wa_approve.py\n" % R, 0o644)
    w(U + "/clinic-portal.service", "[Service]\nExecStart=/x/gunicorn portal:app\n", 0o644)
    w(U + "/wa-send-api.service", "[Service]\nExecStart=/x/wa_send_api.py\n", 0o644)
    w(U + "/call-hook.service", "[Service]\nExecStart=/x/call_hook_capture.py\n", 0o644)
    w(U + "/crond.service", "[Service]\nExecStart=/usr/sbin/crond\n", 0o644)
    w(U + "/oneshot-report.service", "[Service]\nType=oneshot\nRemainAfterExit=yes\nExecStart=/x/python3 %s/wa/notifier_x.py\n" % R, 0o644)
    w(U + "/wa-notifier.service", "[Service]\nExecStart=/x/python3 %s/wa/notifier_x.py\n" % R, 0o644)
    P = os.path.join(T, "proc")
    w(P + "/101/environ", "PATH=/bin\0MYOP_AUTH_TOKEN=%s\0" % OLD)
    w(P + "/101/cgroup", "0::/system.slice/wa-approve.service\n")
    w(P + "/102/environ", "MYOP_AUTH_TOKEN=%s\0" % OLD)
    w(P + "/102/cgroup", "0::/system.slice/crond.service\n")
    w(P + "/103/environ", "PATH=/bin\0")
    w(P + "/103/cgroup", "0::/system.slice/call-hook.service\n")
    w(os.path.join(T, "crontab.txt"), "*/2 * * * * MYOP_AUTH_TOKEN=%s /x/job.py\n0 1 * * * /x/other.py\n" % OLD)
    w(os.path.join(T, "store/config.json"), json.dumps({"token_source": "env:%s/wa/.env:MYOP_AUTH_TOKEN" % R}))
    os.makedirs(os.path.join(T, "portal"))
    for f in ("portal_inbox.py", "inbox_retry.py"):
        shutil.copy(os.path.join(PORTAL_SRC, f), os.path.join(T, "portal", f))
    # the stand-in systemctl: logs every call; restart of wa-approve re-reads its override into process 101's environment
    w(os.path.join(T, "bin/systemctl"), r'''#!%s
import os, re, sys
T = %r
open(os.path.join(T, "systemctl.log"), "a").write(" ".join(sys.argv[1:]) + "\n")
a = sys.argv[1:]
U = os.path.join(T, "etc/systemd/system")
units = sorted(f for f in os.listdir(U) if f.endswith(".service"))
if a[0] == "is-active":
    print("active"); sys.exit(0)
if a[0] == "show":
    print("0" if a[-1] == "oneshot-report" else "4242"); sys.exit(0)
if a[0] == "list-units":
    for u in units: print(u + " loaded active running x")
    sys.exit(0)
if a[0] == "cat":
    p = os.path.join(U, a[1]); print(open(p).read() if os.path.exists(p) else "")
    d = p + ".d"
    if os.path.isdir(d):
        for f in os.listdir(d): print(open(os.path.join(d, f)).read())
    sys.exit(0)
if a[0] == "restart" and a[1] == "wa-approve":
    o = open(os.path.join(U, "wa-approve.service.d/override.conf")).read()
    k = re.search(r"MYOP_AUTH_TOKEN=(\S+)", o).group(1)
    open(os.path.join(T, "proc/101/environ"), "w").write("PATH=/bin\0MYOP_AUTH_TOKEN=%%s\0" %% k)
sys.exit(0)
''' % (sys.executable, T), 0o755)
    w(os.path.join(T, "bin/crontab"), r'''#!%s
import os, shutil, sys
T = %r
c = os.path.join(T, "crontab.txt")
if sys.argv[1] == "-l":
    sys.stdout.write(open(c).read()); sys.exit(0)
if os.path.exists(os.path.join(T, "CRONTAB_FAIL")):
    sys.exit(1)
shutil.copy(sys.argv[1], c); sys.exit(0)
''' % (sys.executable, T), 0o755)
    return R


def env_for(T, R):
    e = dict(os.environ)
    e.update({"S701_WALK": "1", "S701_ROOTS": "%s:%s" % (R, os.path.join(T, "etc/systemd/system")), "S701_REPORT_ROOTS": os.path.join(T, "etc/nginx"),
              "S701_PROC": os.path.join(T, "proc"), "S701_SYSTEMCTL": os.path.join(T, "bin/systemctl"),
              "S701_CRONTAB": os.path.join(T, "bin/crontab"), "S701_BACKUP": os.path.join(R, "s701_backup"),
              "S701_WA_ENV": R + "/wa/.env", "S701_APPROVE_ENV": R + "/wa/wa_approve.env", "S701_SEND_ENV": R + "/wa/wa_send.env",
              "S701_PORTAL_CFG": R + "/portal/portal_config.py", "S701_REPO": R + "/deploy/repo",
              "S701_CHECK_URL": "http://127.0.0.1:%d/chat/templates" % srv.server_address[1], "S701_GAP_S": "0",
              "S701_RESTART_WAIT": "0", "S701_UNIT_DIRS": os.path.join(T, "etc/systemd/"),
              "S701_VPY": sys.executable, "S701_PORTAL_DIR": os.path.join(T, "portal"),
              "INBOX_STORE": os.path.join(T, "store"), "INBOX_WA_ENV": R + "/wa/.env", "INBOX_RAW_DIR": os.path.join(T, "raw")})
    return e


def run(T, R, mode, paste=None, m="new_ok"):
    MODE["m"] = m
    p = subprocess.run([sys.executable, "-B", TOOL, mode] + (["--stdin"] if paste is not None else []), input=(paste or "") + "\n",
                       capture_output=True, text=True, env=env_for(T, R), timeout=300, cwd=T)
    out = p.stdout + p.stderr
    OUTS.append(out)
    return p.returncode, out


def snapshot(T):
    s = {}
    for d, _dirs, files in os.walk(T):
        if "/bin" in d[len(T):] or d.endswith("/proc") or "systemctl.log" in files and False:
            pass
        for f in files:
            p = os.path.join(d, f)
            if f in ("systemctl.log",) or "/s701_backup" in p or "/store/" in p:
                continue
            s[p] = md5(p)
    return s


LIVE = ["wa/.env", "wa/wa_approve.env", "portal/portal_config.py", "wa/other_tool.py", "state_backup/clinic_state_backup.py"]
LEFT = ["s599_backup/config.json.before_s599", "portal/portal_config.py.bak_S599", "wa/venv/lib/site.py", "wa/recordings-archive/call.mp3"]

# ================================================================ 1: find, refusals that change nothing
T = tempfile.mkdtemp(prefix="s701swap.")
R = build(T)
OVR = os.path.join(T, "etc/systemd/system/wa-approve.service.d/override.conf")
rc, out = run(T, R, "find")
check("find: the live holders are named (the two env files, the portal settings, a holder nobody listed, a unit override)",
      lambda: (rc == 0 and all((R + "/" + x) in out.split("WILL change")[1].split("LEFT")[0] for x in LIVE) and OVR in out, out[-900:]))
check("find: backup copies are named as LEFT; media and venv are not read; live code in /root/state_backup is NOT a backup",
      lambda: (all((R + "/" + x) in out.split("LEFT")[1] for x in LEFT[:2]) and (R + "/wa/venv/lib/site.py") not in out
               and (R + "/wa/recordings-archive/call.mp3") not in out and (R + "/state_backup/clinic_state_backup.py") in out.split("WILL change")[1].split("LEFT")[0], out[-900:]))
check("find: the crontab counted; the service started with the key (wa-approve) named; crond's job not counted as a service",
      lambda: ("the crontab  (1 place)" in out and "environment: wa-approve" in out, out[-600:]))
check("find: services the swap would restart = the three readers + wa-approve's unit + a service whose script reads the key (call-hook not)",
      lambda: ("restart: clinic-portal, oneshot-report, wa-approve, wa-notifier, wa-send-api" in out and "call-hook" not in out.split("restart:")[1], out[-300:]))
before = snapshot(T)
rc, out = run(T, R, "apply", "abc def ghi")
check("apply: a paste with spaces is refused, nothing changed", lambda: (rc == 1 and "does not look like a key" in out and snapshot(T) == before, out[-300:]))
rc, out = run(T, R, "apply", OLD)
check("apply: the SAME key as now is refused (Regenerate first), nothing changed", lambda: (rc == 1 and "Regenerate" in out and snapshot(T) == before, out[-300:]))
rc, out = run(T, R, "apply", "")
check("apply: Enter alone = skip, nothing changed (exit 2)", lambda: (rc == 2 and "left as it is" in out and snapshot(T) == before, out[-300:]))
rc, out = run(T, R, "apply", NEW, m="old_ok")
check("apply: MyOperator still takes the OLD key and never the new -> STOPPED, nothing changed",
      lambda: (rc == 1 and "still accepts the OLD key" in out and snapshot(T) == before, out[-300:]))
rc, out = run(T, R, "apply", NEW_LONG, m="none")
check("apply: MyOperator takes neither and the new one has another shape -> STOPPED, nothing changed",
      lambda: (rc == 1 and "different shape" in out and snapshot(T) == before, out[-300:]))
rc, out = run(T, R, "apply", NEW, m="new_401")
check("apply: MyOperator answers 401 to the new key (a clear 'wrong key') -> STOPPED at once, nothing changed",
      lambda: (rc == 1 and "WRONG" in out and snapshot(T) == before, out[-300:]))
check("the owner is told to press Regenerate only AFTER every check is green (the line comes after the holders and the services)",
      lambda: (out.index("press Regenerate") > out.index("services that will restart") > out.index("WILL change"), ""))
# ================================================================ 2: the swap, proven
rc, out = run(T, R, "apply", NEW, m="new_ok")
check("apply (MyOperator takes the new key): exit 0, 'THE KEY IS SWAPPED (PROVEN)'", lambda: (rc == 0 and "THE KEY IS SWAPPED (PROVEN)" in out, out[-1200:]))
check("every live holder now has the NEW key and not the old (env files, portal settings, the unlisted holder, the unit override)",
      lambda: (all(NEW in open(R + "/" + x).read() and OLD not in open(R + "/" + x).read() for x in LIVE)
               and NEW in open(OVR).read() and OLD not in open(OVR).read(), ""))
check("the rest of each file is byte-for-byte the same (only the key changed)",
      lambda: (all(open(R + "/" + x).read().replace(NEW, OLD) == open(os.path.join(R, "s701_backup", (R + "/" + x).strip("/").replace("/", "__") + ".before")).read()
                   for x in LIVE), ""))
check("file modes kept (600, 640, 700)", lambda: (stat.S_IMODE(os.stat(R + "/wa/wa_approve.env").st_mode) == 0o640
                                                  and stat.S_IMODE(os.stat(R + "/wa/other_tool.py").st_mode) == 0o700, ""))
check("the crontab: the new key in, the old out, the other line untouched",
      lambda: (lambda c: (NEW in c and OLD not in c and "0 1 * * * /x/other.py" in c, c))(open(os.path.join(T, "crontab.txt")).read()))
check("backups, mode 600 in a 700 folder, hold the OLD key; a manifest without any key",
      lambda: (lambda B: (stat.S_IMODE(os.stat(B).st_mode) == 0o700 and all(stat.S_IMODE(os.stat(os.path.join(B, f)).st_mode) == 0o600 for f in os.listdir(B))
                          and OLD in open(os.path.join(B, "wa__.env".join([(R + "/").strip("/").replace("/", "__"), ".before"]) if False else os.path.join(B, (R + "/wa/.env").strip("/").replace("/", "__") + ".before"))).read()
                          and OLD not in open(os.path.join(B, "manifest_latest.json")).read() and NEW not in open(os.path.join(B, "manifest_latest.json")).read(), sorted(os.listdir(B))))(os.path.join(R, "s701_backup")))
check("backups, logs and the repository copy left as they were", lambda: (all(OLD in open(R + "/" + x, errors="replace").read() for x in LEFT), ""))
SL = open(os.path.join(T, "systemctl.log")).read()
check("systemd reloaded (a unit file changed) BEFORE the restarts",
      lambda: ("daemon-reload" in SL and SL.index("daemon-reload") < SL.index("restart "), SL[-400:]))
check("restarted: clinic-portal, wa-approve, wa-send-api, wa-notifier; NOT crond, NOT call-hook, NOT a finished one-shot that reads the key",
      lambda: (all(("restart " + u) in SL for u in ("clinic-portal", "wa-approve", "wa-send-api", "wa-notifier")) and "restart oneshot-report" not in SL and "restart crond" not in SL and "restart call-hook" not in SL, SL[-400:]))
check("after: no live file and no service holds the old key; the inbox reads the NEW key",
      lambda: ("still holding the OLD key: none; services still started with it: none" in out and "the inbox reads the NEW key: yes" in out, out[-700:]))
rc2, out2 = run(T, R, "find")
check("find after the swap: the known places all hold one key, the new one", lambda: (out2.count(hashlib.sha256(NEW.encode()).hexdigest()[:8]) >= 4 and OLD[:12] not in out2, out2[:500]))
rc3, out3 = run(T, R, "apply", "")
check("the same line again after a good swap: 'ALREADY', Enter alone leaves it, exit 0, nothing changed",
      lambda: (rc3 == 0 and "ALREADY SWAPPED" in out3 and all(NEW in open(R + "/" + x).read() for x in LIVE), out3[-400:]))
# ================================================================ 3: undo
ORIG = {x: open(os.path.join(R, "s701_backup", (R + "/" + x).strip("/").replace("/", "__") + ".before"), "rb").read() for x in LIVE}
open(os.path.join(T, "systemctl.log"), "w").close()
rc, out = run(T, R, "undo")
check("undo: every file back byte-identical, the crontab back (unchanged since the swap), the services restarted",
      lambda: (rc == 0 and all(open(R + "/" + x, "rb").read() == ORIG[x] for x in LIVE) and OLD in open(OVR).read()
               and OLD in open(os.path.join(T, "crontab.txt")).read() and "restart clinic-portal" in open(os.path.join(T, "systemctl.log")).read(), out[-500:]))
shutil.rmtree(T, ignore_errors=True)
# ================================================================ 4: not yet proven; disagreement; a failed write
T = tempfile.mkdtemp(prefix="s701swap.")
R = build(T)
rc, out = run(T, R, "apply", NEW, m="none")
check("MyOperator takes neither key, the new has the old one's shape: written, 'NOT YET PROVEN', exit 3, every holder swapped",
      lambda: (rc == 3 and "NOT YET PROVEN" in out and all(NEW in open(R + "/" + x).read() for x in LIVE), out[-600:]))
with open(os.path.join(T, "crontab.txt"), "a") as fh:
    fh.write("5 5 * * * /x/added_after.py\n")             # someone edits the crontab after the swap
rc, out = run(T, R, "undo")
check("undo when the crontab was edited after the swap: the crontab is LEFT (the edit kept) and said so; the files go back",
      lambda: (rc == 1 and "the crontab changed since the swap" in out and "added_after" in open(os.path.join(T, "crontab.txt")).read()
               and all(OLD in open(R + "/" + x).read() for x in LIVE), out[-500:]))
shutil.rmtree(T, ignore_errors=True)
T = tempfile.mkdtemp(prefix="s701swap.")
R = build(T, approve_key=OTHER)
before = snapshot(T)
rc, out = run(T, R, "apply", NEW)
check("the known places hold DIFFERENT keys: STOPPED before asking for anything, nothing changed",
      lambda: (rc == 1 and "DIFFERENT keys" in out and snapshot(T) == before, out[-400:]))
shutil.rmtree(T, ignore_errors=True)
T = tempfile.mkdtemp(prefix="s701swap.")
R = build(T)
open(os.path.join(T, "CRONTAB_FAIL"), "w").close()
before = snapshot(T)
rc, out = run(T, R, "apply", NEW)
check("a write that fails half way (the crontab refuses): every file put back as it was, STOPPED",
      lambda: (rc == 1 and "putting everything back" in out and snapshot(T) == before, out[-600:]))
shutil.rmtree(T, ignore_errors=True)
T = tempfile.mkdtemp(prefix="s701swap.")
R = build(T, extras=True)
before = snapshot(T)
rc, out = run(T, R, "apply", NEW)
check("a log and the repository copy hold the key: STOPPED before the owner is asked to press Regenerate, nothing changed",
      lambda: (rc == 1 and "Do NOT press Regenerate" in out and "NOW, on MyOperator" not in out and snapshot(T) == before, out[-500:]))
rc, out = run(T, R, "find")
check("find says the same (exit 1, 'Claude looks first')", lambda: (rc == 1 and "Claude looks first" in out, out[-300:]))
shutil.rmtree(T, ignore_errors=True)
# ================================================================ 5: no key is ever printed
check("no run printed either key (old, new, other)", lambda: (not any(k in o for o in OUTS for k in (OLD, NEW, NEW_LONG, OTHER)), ""))
srv.shutdown()
print("%d of %d green" % (sum(RES), len(RES)))
