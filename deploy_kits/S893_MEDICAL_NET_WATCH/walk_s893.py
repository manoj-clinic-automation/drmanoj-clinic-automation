# walk_s893.py -- netwatch.py on a made-up PC: a fake clock, fake probes, fake
# Windows commands. Usage: python walk_s893.py <path to netwatch.py>
import datetime as dt, importlib.util, json, os, shutil, sys, tempfile

SRC = sys.argv[1]
spec = importlib.util.spec_from_file_location("nw", SRC)
nw = importlib.util.module_from_spec(spec); spec.loader.exec_module(nw)

class Fake:
    def __init__(s, start, ok_fn, uptime=600.0, marg=False, files=None):
        s.t = start; s.m = 1000.0; s.ok_fn = ok_fn; s.calls = []; s.up = uptime
        s.marg = marg; s.files = dict(files or {}); s.steps = []; s.disabled = set(); s.ts_fail = False
    def now(s): return s.t
    def mono(s): return s.m
    def sleep(s, sec): s.t += dt.timedelta(seconds=sec); s.m += sec
    def jump(s, sec, mono=True):
        s.t += dt.timedelta(seconds=sec)
        if mono: s.m += sec
    def exists(s, p): return p in s.files
    def run(s, args, timeout=60):
        s.calls.append(("run", list(args)))
        if args[0] == "ipconfig" and args[1] == "/flushdns": s.steps.append("flush")
        return 0, "ok"
    def ps(s, script, timeout=60):
        s.calls.append(("ps", script[:60]))
        if "Get-NetAdapter -Physical | ForEach-Object { $_.Name }" in script:
            return 0, "Ethernet\nWi-Fi 2"
        if "Disable-NetAdapter" in script:
            s.steps.append("bounce"); return 0, "bounced"
        if "Enable-NetAdapter" in script and "Get-NetAdapter -Name" in script:
            for n in list(s.disabled):
                if "'%s'" % n in script:
                    s.disabled.discard(n); s.steps.append("enable:" + n); return 0, "ENABLED again " + n
            return 0, "enabled"
        if "Set-DnsClientServerAddress" in script:
            if "pdns" not in s.steps: s.steps.append("pdns")
            return 0, "set"
        if "Restart-Service -Name Tailscale" in script: s.steps.append("tsrestart")
        if "Stop-Service -Name Tailscale" in script: s.steps.append("tsstop")
        if "Start-Service -Name Tailscale" in script:
            s.steps.append("tsstart"); return 0, ("Stopped" if s.ts_fail else "Running")
        return 0, "ok"
    def ok(s): return s.ok_fn(s)
    def tcp(s, h, p, timeout=3.0): return s.ok()
    def resolve(s, n, timeout=6.0): return s.ok()
    def web(s, u, timeout=8.0): return s.ok()
    def uptime_min(s): return s.up
    def process_running(s, exe): return s.marg
    def write(s, path, text, mode="w"):
        s.files[path] = (s.files.get(path, "") + text) if mode == "a" else text
    def read(s, path):
        if path not in s.files: raise OSError("no")
        return s.files[path]
    def size(s, path): return len(s.files.get(path, ""))
    def copy(s, src, dst): s.files[dst] = s.files[src]

H = r"C:\ProgramData\MedicalNetWatch"; M = r"D:\SendToClinic\_netwatch"
LOG = os.path.join(H, "netwatch.log"); ST = os.path.join(H, "state.json")
def mk(fake):
    w = nw.Watch(w=fake, home=H, mirror=M, off_files=(r"D:\SendToClinic\_off\NETWATCH_OFF.txt",))
    w.start(); return w
def run_for(w, fake, minutes):
    end = fake.t + dt.timedelta(minutes=minutes)
    while fake.t < end:
        w.tick(); w.last_end = fake.mono(); w.do_mirror(); fake.sleep(w.cfg["check_every_s"])
def shut(fake): return [c for c in fake.calls if c[0]=="run" and c[1][0]=="shutdown"]
def msgs(fake): return [c for c in fake.calls if c[0]=="run" and c[1][0].lower().endswith("msg.exe")]
def state(fake): return json.loads(fake.files[ST])

R = []
def check(name, cond):
    R.append((name, bool(cond))); print(("PASS " if cond else "FAIL ") + name)

NIGHT = dt.datetime(2026, 11, 20, 0, 40)
DAY = dt.datetime(2026, 11, 20, 11, 0)

# W1 healthy
f = Fake(DAY, lambda s: True); w = mk(f); run_for(w, f, 10)
check("W1 healthy: an ok line, no step, no restart", "ok: internet OK" in f.files[LOG] and not f.steps and not shut(f))

# W2 fixed by the name-cache clear
f = Fake(DAY, lambda s: "flush" in s.steps); w = mk(f); run_for(w, f, 10)
L = f.files[LOG]
check("W2 DOWN recorded with a picture", "DOWN: NO INTERNET" in L and "PICTURE" in L)
check("W2 BACK fixed by flush_dns", "Fixed by: flush_dns" in L and (state(f).get("outages") or [{}])[-1].get("fixed_by") == "flush_dns")
check("W2 no Tailscale or adapter step after the fix", f.steps == ["pdns", "flush"])

# W3 fixed by the adapters, steps in their order
f = Fake(DAY, lambda s: "bounce" in s.steps); w = mk(f); run_for(w, f, 15)
L = f.files[LOG]
check("W3 steps in order flush, Tailscale, adapters", f.steps[:4] == ["pdns", "flush", "tsrestart", "bounce"])
check("W3 BACK fixed by restart_adapters", "Fixed by: restart_adapters" in L)
o = (state(f).get("outages") or [{"min": -1}])[-1]
check("W3 outage minutes between 5 and 9", 5 <= o["min"] <= 9)

# W4 never back, night, no Marg -> restart at >=15 min with 60 s
f = Fake(NIGHT, lambda s: False); w = mk(f); run_for(w, f, 25)
S = shut(f)
check("W4 one restart, /t 60", len(S) == 1 and S[0][1][2:4] == ["/t", "60"])
check("W4 restart only after every step", f.steps[:9] == ["pdns","flush","tsrestart","bounce","bounce","tsstop","tsstart","bounce","bounce"])
check("W4 restart recorded", len(state(f)["reboots"]) == 1 and "restart_pending" in state(f))
first_shut_min = None

# W5 shop hours with Marg open: message at 15, restart (180 s) only at 30
f = Fake(DAY, lambda s: False, marg=True); w = mk(f); run_for(w, f, 20)
check("W5 at 20 min: staff warned once, no restart yet", len(msgs(f)) == 1 and not shut(f))
run_for(w, f, 12)
S = shut(f)
check("W5 at 32 min: restart with /t 180", len(S) == 1 and S[0][1][2:4] == ["/t", "180"])

# W6 a restart one hour ago -> none now, said once
f = Fake(NIGHT, lambda s: False)
f.files[ST] = json.dumps({"reboots": [(NIGHT - dt.timedelta(hours=1)).isoformat()]})
w = mk(f); run_for(w, f, 25)
check("W6 no restart within 4 h of the last", not shut(f))
check("W6 'RESTART NOT DONE' said once", f.files[LOG].count("RESTART NOT DONE") == 1)

# W7 just started -> no restart
f = Fake(NIGHT, lambda s: False, uptime=10.0); w = mk(f); run_for(w, f, 25)
check("W7 no restart within 30 min of start-up", not shut(f))

# W8 switched off -> no step at all
f = Fake(DAY, lambda s: False, files={r"D:\SendToClinic\_off\NETWATCH_OFF.txt": "x"}); w = mk(f); run_for(w, f, 25)
check("W8 switch: no step, no restart, said so", not f.steps and not shut(f) and "SWITCHED OFF" in f.files[LOG])

# W9 asleep while down: on waking, steps start again from zero; no instant restart
f = Fake(NIGHT, lambda s: False); w = mk(f); run_for(w, f, 2)
f.jump(8 * 3600)                  # 8 hours asleep
f.marg = True; f.t = f.t.replace(hour=9); n0 = len(f.steps)
run_for(w, f, 20)
check("W9 GAP recorded", "GAP: no check for" in f.files[LOG])
check("W9 no restart in the first 20 min after waking", not shut(f))
check("W9 the steps run again after waking", f.steps[n0:n0+2] == ["flush", "tsrestart"])

# W10 Tailscale the cause
f = Fake(DAY, lambda s: s.steps and s.steps[-1] == "tsstop"); w = mk(f); run_for(w, f, 10)
check("W10 'CAME BACK WITHOUT Tailscale' recorded", "CAME BACK WITHOUT Tailscale" in f.files[LOG])

# W11 after its own restart: BACK names the restart
f = Fake(NIGHT, lambda s: True)
f.files[ST] = json.dumps({"down": {"since": (NIGHT - dt.timedelta(minutes=20)).isoformat(), "done": [], "kind": "x", "last_step": "restart_adapters"},
                          "restart_pending": {"at": NIGHT.isoformat()}, "reboots": [NIGHT.isoformat()]})
w = mk(f); run_for(w, f, 2)
check("W11 BACK fixed by: restart of the PC", "Fixed by: restart of the PC" in f.files[LOG])

# W12 the mirror
check("W12 log and state mirrored to D:\\SendToClinic\\_netwatch", os.path.join(M, "netwatch.log") in f.files and os.path.join(M, "netwatch_state.json") in f.files)

# W13 settings honoured (no restart, earlier flush)
f = Fake(NIGHT, lambda s: False)
f.files[os.path.join(H, "settings.json")] = json.dumps({"reboot": False, "steps": [[0.5, "flush_dns"]]})
w = mk(f); run_for(w, f, 25)
check("W13 settings: restart off, one step", not shut(f) and f.steps == ["flush"])

# W14 a step that raises does not stop the watch
class Boom(Fake):
    def ps(s, script, timeout=60):
        if "Restart-Service" in script: raise RuntimeError("boom")
        return Fake.ps(s, script, timeout)
f = Boom(DAY, lambda s: "bounce" in s.steps); w = mk(f); run_for(w, f, 12)
check("W14 a failing step is logged and the next step still runs", "failed: RuntimeError" in f.files[LOG] and "Fixed by: restart_adapters" in f.files[LOG])

# W16 still down after a restart by hand, shop hours, Marg open: no instant restart, steps again
f = Fake(DAY.replace(hour=8, minute=31), lambda s: False, uptime=40.0, marg=True)
f.files[ST] = json.dumps({"down": {"since": (f.t - dt.timedelta(hours=2)).isoformat(), "kind": "x",
     "done": ["0:flush_dns","1:restart_tailscale","2:restart_adapters","3:tailscale_pause","4:restart_adapters"],
     "last_step": "restart_adapters"}, "warned": True, "reboots": []})
w = mk(f); run_for(w, f, 20)
check("W16 restart by hand: no restart within 20 min", not shut(f))
check("W16 restart by hand: steps from the first again", f.steps[:3] == ["pdns", "flush", "tsrestart"])
check("W16 restart by hand: staff warned again at 15 min", len(msgs(f)) == 1)

# W17 shop hours, Marg not seen: still the 30-minute path
f = Fake(DAY, lambda s: False, marg=False); w = mk(f); run_for(w, f, 20)
check("W17 shop hours without Marg: no restart at 20 min", not shut(f))
run_for(w, f, 12)
S = shut(f)
check("W17 shop hours without Marg: restart at 30 min with /t 180", len(S) == 1 and S[0][1][2:4] == ["/t", "180"])

# W18 Tailscale left paused by a crash: started at start-up
f = Fake(DAY, lambda s: True); f.files[ST] = json.dumps({"ts_paused": True})
w = mk(f)
check("W18 Tailscale left paused is started at start-up", "tsstart" in f.steps and "ts_paused" not in state(f))

# W19 an adapter left switched off is switched on at DOWN, and named as the fix
f = Fake(DAY, lambda s: "enable:Wi-Fi 2" in s.steps); f.disabled = {"Wi-Fi 2"}
w = mk(f); run_for(w, f, 3)
check("W19 a switched-off adapter switched on, named as the fix", "Fixed by: an adapter found switched off" in f.files[LOG])

# W20 Tailscale will not start: said, flag kept, tried again on the next good check
f = Fake(DAY, lambda s: s.steps.count("tsstop") > 0); f.ts_fail = True
w = mk(f); run_for(w, f, 11)
check("W20 Tailscale not starting is said and kept for retry", "did NOT start again" in f.files[LOG] and state(f).get("ts_paused"))
f.ts_fail = False; run_for(w, f, 1)
check("W20 ...and started on a later good check", "ts_paused" not in state(f))

# W21 the restart counter across midnight: one at 23:50, none again at 00:30
f = Fake(dt.datetime(2026, 11, 21, 0, 10), lambda s: False)
f.files[ST] = json.dumps({"reboots": [dt.datetime(2026, 11, 20, 23, 50).isoformat()]})
w = mk(f); run_for(w, f, 25)
check("W21 4-hour gap holds across midnight", not shut(f))

# W22 the router's name lookup dead (20-Nov's fault): fixed by the public name servers
f = Fake(DAY, lambda s: "pdns" in s.steps); w = mk(f); run_for(w, f, 4)
check("W22 fixed by public_dns", "Fixed by: public_dns" in f.files[LOG] and "flush" not in f.steps)

# W15 no patient number or secret pattern can come from the code's own text
src = open(SRC, encoding="utf-8").read()
import re
check("W15 no 10-digit number in the file", not re.search(r"\d{10}", src))

bad = [n for n, ok in R if not ok]
print("\n%d/%d %s" % (len(R) - len(bad), len(R), "GREEN" if not bad else "RED"))
sys.exit(1 if bad else 0)
