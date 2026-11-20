# -*- coding: utf-8 -*-
r"""
netwatch.py -- kit S893_MEDICAL_NET_WATCH (session 490, the Sanjeevni chat, 20-Nov-2026)

Runs ON THE MEDICAL PC as the SYSTEM account, started by the scheduled task
"MedicalNetWatch" (at start-up, and every 5 minutes if it is not running).
It lives in C:\Program Files\MedicalNetWatch\ -- a folder only administrators
can change -- and runs with that folder's own copy of python.

WHY: on 20-Nov-2026 the PC lost the internet on the cable AND the Wi-Fi in
the same minute (~00:45 IST) and stayed off for about 9.5 hours, until the
owner restarted it. Nothing on the PC noticed, nothing tried to fix it, and
nothing recorded why.

WHAT IT DOES, every 30 seconds:
  1. CHECKS the internet three ways: a direct connection to two public
     addresses (no name lookup), a name lookup, and one web page.
  2. WRITES what it sees: every change (down / back) with the time, the
     sleep/wake of the PC, and -- when the internet is down -- one picture of
     the adapters, their addresses and gateways, Tailscale, and the Windows
     events of the last hour about the network and power.
  3. HEALS, one step at a time, re-checking after each, and records WHICH
     step brought the internet back (that is the cause, found):
        1.5 min down : clear the name-lookup cache
        3 min        : restart the Tailscale service
        5 min        : restart the network adapters (cable and Wi-Fi), renew
        8 min        : Tailscale stopped for a minute (does the internet come
                       back without it?), then started again
        11 min       : restart the adapters once more
        15 min       : restart the PC -- with limits (see REBOOT below)
  4. MIRRORS its log and state into D:\SendToClinic\_netwatch\ -- the folder
     manojz copies every 10 minutes -- so the record reaches the clinic.

REBOOT: never within 30 minutes of start-up; at most once in 4 hours and twice
a day. In shop hours (08:00-22:00) with Marg open, the staff are shown a
message at 15 minutes and the PC restarts at 30 minutes with a 3-minute
on-screen warning; otherwise it restarts at 15 minutes with a 1-minute warning.

SWITCHES (any one present = watch and record only, never heal):
  D:\SendToClinic\_off\NETWATCH_OFF.txt
  D:\SendToClinic\_off\ALL_OFF.txt
Settings may be changed in C:\Program Files\MedicalNetWatch\settings.json.

Stdlib only. Never stops on an error: an error becomes one line in the log.
"""

import datetime as dt
import json
import os
import socket
import subprocess
import sys
import threading
import time

VERSION = "S893.5"

HOME = r"C:\Program Files\MedicalNetWatch"
MIRROR = r"D:\SendToClinic\_netwatch"
OFF_FILES = (r"D:\SendToClinic\_off\NETWATCH_OFF.txt",
             r"D:\SendToClinic\_off\ALL_OFF.txt")
LOCK_PORT = 47893            # one copy only: the port is held while it runs

DEFAULTS = {
    "check_every_s": 30,
    "heal": True,
    "public_dns": ["1.1.1.1", "8.8.8.8"],
    "steps": [                # [minutes down, step name]
        [1, "public_dns"],
        [1.5, "flush_dns"],
        [3, "restart_tailscale"],
        [5, "restart_adapters"],
        [8, "tailscale_pause"],
        [11, "restart_adapters"],
    ],
    "reboot": True,
    "reboot_after_min": 15,
    "reboot_shop_after_min": 30,
    "shop_hours": [8, 22],
    "reboot_min_uptime_min": 30,
    "reboot_gap_h": 4,
    "reboot_max_per_day": 2,
    "marg_process": "margwin.exe",
    "warn_text": ("Internet band hai. Computer {sec} second mein RESTART hoga. "
                  "Marg mein bill SAVE kar lijiye."),
    "warn_shop_text": ("Internet {min} minute se band hai. Bill poora karke "
                       "SAVE kijiye -- {left} minute mein computer apne aap "
                       "RESTART hoga."),
    "probe_ips": [["1.1.1.1", 443], ["8.8.8.8", 443], ["208.67.222.222", 443]],
    "probe_names": ["www.google.com", "www.microsoft.com"],
    "probe_url": "http://www.msftconnecttest.com/connecttest.txt",
    "ok_line_every_min": 60,
    "sleep_gap_s": 150,
    "log_keep_bytes": 3000000,
}


def sysdir():
    """System32 as a 64-bit process sees it (a 32-bit python is redirected to
    SysWOW64; Sysnative reaches the real one)."""
    root = os.environ.get("SystemRoot", r"C:\Windows")
    native = os.path.join(root, "Sysnative")
    return native if os.path.isdir(native) else os.path.join(root, "System32")


# --------------------------------------------------------------------------
# the outside world -- one object, so the walk can replace every part of it
# --------------------------------------------------------------------------
class Win:
    """Everything that touches Windows. The walk passes a fake instead."""

    def now(self):
        return dt.datetime.now()

    def mono(self):
        return time.monotonic()

    def sleep(self, s):
        time.sleep(s)

    def exists(self, p):
        return os.path.exists(p)

    def run(self, args, timeout=60):
        """(exit code, text). Never raises."""
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            r = subprocess.run(args, capture_output=True, timeout=timeout,
                               stdin=subprocess.DEVNULL, creationflags=flags)
            out = (r.stdout or b"") + (b"\n" + r.stderr if r.stderr else b"")
            return r.returncode, out.decode("utf-8", "replace").strip()
        except subprocess.TimeoutExpired:
            return -9, "timed out after %d s" % timeout
        except Exception as ex:                                # noqa: BLE001
            return -1, "%s: %s" % (ex.__class__.__name__, ex)

    def ps(self, script, timeout=60):
        exe = os.path.join(sysdir(), "WindowsPowerShell", "v1.0", "powershell.exe")
        return self.run([exe, "-NoProfile", "-NonInteractive",
                         "-ExecutionPolicy", "Bypass", "-Command", script],
                        timeout=timeout)

    def tcp(self, host, port, timeout=3.0):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def resolve(self, name, timeout=6.0):
        box = {}

        def go():
            try:
                box["ok"] = bool(socket.getaddrinfo(name, 443))
            except Exception:                                  # noqa: BLE001
                box["ok"] = False
        t = threading.Thread(target=go, daemon=True)
        t.start()
        t.join(timeout)
        return bool(box.get("ok"))

    def web(self, url, timeout=8.0):
        import urllib.request
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "netwatch"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return 200 <= r.status < 400
        except Exception:                                      # noqa: BLE001
            return False

    def uptime_min(self):
        try:
            import ctypes
            f = ctypes.windll.kernel32.GetTickCount64
            f.restype = ctypes.c_ulonglong       # the default (int) wraps at 24.8 days
            return f() / 60000.0
        except Exception:                                      # noqa: BLE001
            return 9999.0

    def process_running(self, exe):
        code, out = self.run(["tasklist", "/FI", "IMAGENAME eq %s" % exe,
                              "/NH"], timeout=30)
        return exe.lower() in out.lower()

    def write(self, path, text, mode="w"):
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        with open(path, mode, encoding="utf-8") as fh:
            fh.write(text)

    def read(self, path):
        with open(path, "r", encoding="utf-8-sig") as fh:
            return fh.read()

    def size(self, path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    def copy(self, src, dst):
        import shutil
        d = os.path.dirname(dst)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        shutil.copyfile(src, dst)


# --------------------------------------------------------------------------
# the PowerShell pictures -- fixed text, read-only, never a secret
# --------------------------------------------------------------------------
PS_PICTURE = r"""
$ErrorActionPreference='SilentlyContinue'
'-- adapters --'
Get-NetAdapter | Sort-Object Name | ForEach-Object { '{0} | {1} | {2} | {3} | media {4}' -f $_.Name,$_.InterfaceDescription,$_.Status,$_.LinkSpeed,$_.MediaConnectionState }
'-- addresses, gateways, name servers --'
Get-NetIPConfiguration | ForEach-Object {
  $gw = ($_.IPv4DefaultGateway | ForEach-Object { $_.NextHop }) -join ','
  $ip = ($_.IPv4Address | ForEach-Object { $_.IPAddress }) -join ','
  $dns = ($_.DNSServer | Where-Object { $_.AddressFamily -eq 2 } | ForEach-Object { $_.ServerAddresses }) -join ','
  '{0} | ip {1} | gateway {2} | dns {3} | profile {4}' -f $_.InterfaceAlias,$ip,$gw,$dns,$_.NetProfile.IPv4Connectivity
}
'-- gateways answer? --'
Get-NetIPConfiguration | ForEach-Object { foreach ($g in $_.IPv4DefaultGateway) { $ok = Test-Connection -ComputerName $g.NextHop -Count 1 -Quiet; '{0} gateway {1}: {2}' -f $_.InterfaceAlias,$g.NextHop,$ok } }
'-- route Windows picks for the internet --'
Find-NetRoute -RemoteIPAddress 8.8.8.8 | Where-Object { $_.InterfaceAlias } | ForEach-Object { 'via ' + $_.InterfaceAlias + ' next hop ' + $_.NextHop }
'-- Tailscale --'
$s = Get-Service -Name Tailscale; if ($s) { 'service: ' + $s.Status } else { 'service: not installed' }
$t = Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
if (Test-Path $t) { & $t status 2>&1 | Select-Object -First 6 | ForEach-Object { '  ' + $_ } }
'-- Windows events, last {MIN} minutes (network and power) --'
$p = 'Microsoft-Windows-Kernel-Power','Microsoft-Windows-Power-Troubleshooter','Microsoft-Windows-Dhcp-Client','Microsoft-Windows-DNS-Client','Tcpip','e1dexpress','rt640x64','rtwlanu','Microsoft-Windows-WLAN-AutoConfig','Microsoft-Windows-NDIS','Microsoft-Windows-NetworkProfile','Microsoft-Windows-Kernel-PnP','Microsoft-Windows-Kernel-General','EventLog','USER32'
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=(Get-Date).AddMinutes(-{MIN})} -MaxEvents 400 |
  Where-Object { $p -contains $_.ProviderName -or $_.ProviderName -like '*Realtek*' -or $_.ProviderName -like 'rt*' -or $_.ProviderName -like '*Netwtw*' } |
  Sort-Object TimeCreated | Select-Object -Last 60 |
  ForEach-Object { '{0:dd-MM HH:mm:ss} {1} #{2} {3}' -f $_.TimeCreated,$_.ProviderName,$_.Id,(($_.Message -split "`n")[0]).Trim() }
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-WLAN-AutoConfig/Operational'; StartTime=(Get-Date).AddMinutes(-{MIN})} -MaxEvents 20 |
  Sort-Object TimeCreated | ForEach-Object { '{0:dd-MM HH:mm:ss} WLAN #{1} {2}' -f $_.TimeCreated,$_.Id,(($_.Message -split "`n")[0]).Trim() }
"""

PS_ENABLE_ONE = r"""
$ErrorActionPreference='SilentlyContinue'
$a = Get-NetAdapter -Name '{NAME}'
if (-not $a) { 'not found {NAME}' } elseif ($a.Status -eq 'Disabled') { Enable-NetAdapter -Name '{NAME}' -Confirm:$false; 'ENABLED again {NAME}' } else { 'enabled {NAME}' }
"""

PS_BOUNCE_ONE = r"""
$ErrorActionPreference='Continue'
try { Disable-NetAdapter -Name '{NAME}' -Confirm:$false -ErrorAction Stop; Start-Sleep -Seconds 5; 'bounced {NAME}' }
catch { 'could not disable {NAME}: ' + $_.Exception.Message }
finally { Enable-NetAdapter -Name '{NAME}' -Confirm:$false -ErrorAction SilentlyContinue }
"""

PS_LIST_PHYSICAL = "Get-NetAdapter -Physical | ForEach-Object { $_.Name }"


# --------------------------------------------------------------------------
class Watch:
    def __init__(self, w=None, home=HOME, mirror=MIRROR, off_files=OFF_FILES):
        self.w = w or Win()
        self.home = home
        self.mirror = mirror
        self.off_files = off_files
        self.log_path = os.path.join(home, "netwatch.log")
        self.state_path = os.path.join(home, "state.json")
        self.cfg = dict(DEFAULTS)
        self.state = {}
        self.last_end = None      # monotonic time the previous check ended
        self.last_ok_line = None
        self.mirror_dirty = True

    # ---- records --------------------------------------------------------
    def stamp(self):
        return self.w.now().strftime("%d-%b-%Y %H:%M:%S")

    def log(self, msg):
        line = "%s  %s\n" % (self.stamp(), msg)
        try:
            if self.w.size(self.log_path) > self.cfg["log_keep_bytes"]:
                old = self.log_path + ".old"
                try:
                    self.w.copy(self.log_path, old)
                except Exception:                              # noqa: BLE001
                    pass
                self.w.write(self.log_path, "")
            self.w.write(self.log_path, line, mode="a")
        except Exception:                                      # noqa: BLE001
            pass
        self.mirror_dirty = True

    def save_state(self):
        try:
            self.state["version"] = VERSION
            self.state["written_at"] = self.w.now().isoformat(timespec="seconds")
            self.w.write(self.state_path, json.dumps(self.state, indent=1))
        except Exception as ex:                                # noqa: BLE001
            self.log("could not save state: %s" % ex)
        self.mirror_dirty = True

    def do_mirror(self, force=False):
        if not (self.mirror_dirty or force):
            return
        for src, name in ((self.log_path, "netwatch.log"),
                          (self.state_path, "netwatch_state.json")):
            try:
                if self.w.exists(src):
                    self.w.copy(src, os.path.join(self.mirror, name))
            except Exception:                                  # noqa: BLE001
                pass
        self.mirror_dirty = False

    def load(self):
        try:
            got = json.loads(self.w.read(os.path.join(self.home, "settings.json")))
            if isinstance(got, dict):
                for k, v in got.items():
                    if k in DEFAULTS:
                        self.cfg[k] = v
        except Exception:                                      # noqa: BLE001
            pass
        try:
            st = json.loads(self.w.read(self.state_path))
            if isinstance(st, dict):
                self.state = st
        except Exception:                                      # noqa: BLE001
            self.state = {}
        self.state.setdefault("reboots", [])
        self.state.setdefault("outages", [])

    # ---- checks ---------------------------------------------------------
    def probe(self):
        ip = any(self.w.tcp(h, p) for h, p in self.cfg["probe_ips"])
        dns = any(self.w.resolve(n) for n in self.cfg["probe_names"])
        web = self.w.web(self.cfg["probe_url"]) if (ip and dns) else False
        return {"ip": ip, "dns": dns, "web": web, "ok": ip and dns}

    @staticmethod
    def words(p):
        if p["ok"]:
            return "internet OK" + ("" if p["web"] else " (web page did not load)")
        if p["ip"] and not p["dns"]:
            return "NAME LOOKUP FAILS (addresses reachable) -- a DNS fault"
        if not p["ip"] and p["dns"]:
            return "public addresses unreachable, names resolve (cached?)"
        return "NO INTERNET -- public addresses unreachable"

    def fresh_start_of_trying(self, now):
        """After sleep or a restart the PC did not do itself: the steps run again
        from the first, and the minutes count from now (review MUST 1)."""
        d = self.state.get("down")
        if not d:
            return
        d["heal_from"] = now.isoformat(timespec="seconds")
        d["done"] = []
        d.pop("picture2", None)
        for k in ("warned", "reboot_refused_said"):
            self.state.pop(k, None)

    def healing_off(self):
        return any(self.w.exists(p) for p in self.off_files) or not self.cfg["heal"]

    def picture(self, minutes=60):
        code, out = self.w.ps(PS_PICTURE.replace("{MIN}", str(int(minutes))),
                              timeout=90)
        lines = [l.rstrip() for l in out.splitlines() if l.strip()][:160]
        self.log("PICTURE (exit %s):\n        %s" % (code, "\n        ".join(lines)))

    # ---- healing steps ---------------------------------------------------
    def step(self, name):
        w = self.w
        if name == "public_dns":
            said = []
            try:
                before = json.loads(w.read(os.path.join(self.home, "dns_before.json")))
            except Exception:                                  # noqa: BLE001
                before = {}
            for n in self.adapters():
                lst = list(self.cfg["public_dns"])
                for x in str((before or {}).get(n) or "").split(","):
                    x = x.strip()
                    if x and x not in lst and x.count(".") == 3:
                        lst.append(x)           # the router's own kept last
                servers = ",".join("'%s'" % x for x in lst)
                c, out = w.ps("Set-DnsClientServerAddress -InterfaceAlias '%s' "
                              "-ServerAddresses (%s); 'set %s'" % (n, servers, n), timeout=60)
                said.append(out.strip()[-40:] or "exit %s" % c)
            return "public name servers %s on: %s" % (self.cfg["public_dns"], " ; ".join(said))
        if name == "flush_dns":
            code, out = w.run(["ipconfig", "/flushdns"], timeout=30)
            return "ipconfig /flushdns -> %s" % code
        if name == "restart_tailscale":
            code, out = w.ps("Restart-Service -Name Tailscale -Force; "
                             "(Get-Service Tailscale).Status", timeout=90)
            return "Tailscale restarted -> %s %s" % (code, out[-60:])
        if name == "restart_adapters":
            said = []
            for n in self.adapters():
                c, out = w.ps(PS_BOUNCE_ONE.replace("{NAME}", n), timeout=60)
                said.append(out.splitlines()[0] if out else "%s: exit %s" % (n, c))
            said.append(self.ensure_adapters())
            w.sleep(20)
            c2, _ = w.run(["ipconfig", "/renew"], timeout=90)
            return "adapters: %s | renew -> %s" % (" ; ".join(said)[:240], c2)
        if name == "tailscale_pause":
            self.state["ts_paused"] = True
            self.save_state()
            w.ps("Stop-Service -Name Tailscale -Force", timeout=90)
            w.sleep(45)
            p = self.probe()
            back = self.ensure_tailscale()
            return ("Tailscale stopped 45 s: internet %s WITHOUT Tailscale; %s"
                    % ("CAME BACK" if p["ok"] else "still down", back))
        return "unknown step %s" % name

    def adapters(self):
        """The physical adapters set-up found enabled (adapters.json), else
        those Windows lists now. Never the empty list by accident."""
        try:
            got = json.loads(self.w.read(os.path.join(self.home, "adapters.json")))
            if isinstance(got, list) and got:
                return [str(x) for x in got if str(x).strip()]
        except Exception:                                      # noqa: BLE001
            pass
        c, out = self.w.ps(PS_LIST_PHYSICAL, timeout=60)
        return [l.strip() for l in out.splitlines() if l.strip()]

    def ensure_adapters(self):
        """Every adapter set-up found enabled is enabled again if it is not."""
        said = []
        for n in self.adapters():
            c, out = self.w.ps(PS_ENABLE_ONE.replace("{NAME}", n), timeout=60)
            if "ENABLED again" in out or "not found" in out:
                said.append(out.strip()[:80])
        return ("; ".join(said)) or "all adapters enabled"

    def ensure_tailscale(self):
        """Started again after a pause, checked, three tries. Clears ts_paused
        only when Windows says Running (or Tailscale is not installed)."""
        for i in range(3):
            c, out = self.w.ps("Start-Service -Name Tailscale -ErrorAction SilentlyContinue; "
                               "Start-Sleep -Seconds 3; $s = Get-Service -Name Tailscale "
                               "-ErrorAction SilentlyContinue; if ($s) { $s.Status } "
                               "else { 'absent' }", timeout=90)
            if "Running" in out or "absent" in out:
                self.state.pop("ts_paused", None)
                self.save_state()
                return "Tailscale running again"
            self.w.sleep(10)
        self.log("Tailscale did NOT start again after the pause (%s) -- tried 3 times; "
                 "tried again every check" % out[-40:])
        return "Tailscale NOT running yet"

    # ---- restart ------------------------------------------------------------
    def reboot_allowed(self, now):
        cfg = self.cfg
        if not cfg["reboot"] or self.healing_off():
            return False, "restart switched off"
        if self.w.uptime_min() < cfg["reboot_min_uptime_min"]:
            return False, "the PC started less than %s min ago" % cfg["reboot_min_uptime_min"]
        times = []
        for r in self.state.get("reboots", []):
            try:
                times.append(dt.datetime.fromisoformat(r))
            except Exception:                                  # noqa: BLE001
                pass
        if any((now - t).total_seconds() < cfg["reboot_gap_h"] * 3600 for t in times):
            return False, "already restarted in the last %s h" % cfg["reboot_gap_h"]
        if sum(1 for t in times if t.date() == now.date()) >= cfg["reboot_max_per_day"]:
            return False, "already %s restarts today" % cfg["reboot_max_per_day"]
        return True, ""

    def maybe_reboot(self, down_min, now):
        cfg = self.cfg
        if down_min < cfg["reboot_after_min"]:
            return
        ok, why = self.reboot_allowed(now)
        if not ok:
            if not self.state.get("reboot_refused_said"):
                self.log("RESTART NOT DONE: %s" % why)
                self.state["reboot_refused_said"] = True
            return
        shop = cfg["shop_hours"][0] <= now.hour < cfg["shop_hours"][1]
        marg = self.w.process_running(cfg["marg_process"])
        if shop:
            if down_min < cfg["reboot_shop_after_min"]:
                if not self.state.get("warned"):
                    left = int(cfg["reboot_shop_after_min"] - down_min + 0.5)
                    txt = cfg["warn_shop_text"].format(min=int(down_min), left=left)
                    code, out = self.w.run([os.path.join(sysdir(), "msg.exe"), "*", "/TIME:600", txt],
                                           timeout=30)
                    self.log("staff warned on screen (shop hours; Marg open: %s): msg -> %s"
                             % (marg, code))
                    self.state["warned"] = True
                return
            secs = 180
        else:
            secs = 60
        txt = cfg["warn_text"].format(sec=secs)
        self.state["reboots"] = (self.state.get("reboots", []) +
                                 [now.isoformat(timespec="seconds")])[-10:]
        self.state["restart_pending"] = {"at": now.isoformat(timespec="seconds"),
                                         "down_min": round(down_min, 1)}
        self.save_state()
        self.log("RESTARTING THE PC in %d s (down %.0f min; every step tried; "
                 "Marg open: %s; shop hours: %s)" % (secs, down_min, marg, shop))
        self.do_mirror(force=True)
        code, out = self.w.run(["shutdown", "/r", "/t", str(secs), "/c", txt],
                               timeout=30)
        self.log("shutdown /r -> %s %s" % (code, out[:120]))

    # ---- one tick ---------------------------------------------------------
    def tick(self):
        now = self.w.now()
        mono = self.w.mono()
        gap = 0.0
        if self.last_end is not None:
            gap = mono - self.last_end - self.cfg["check_every_s"]
            if gap > self.cfg["sleep_gap_s"]:
                self.log("GAP: no check for %.0f min -- the PC was asleep, or "
                         "stopped" % (gap / 60.0))
                if self.state.get("down"):
                    # minutes asleep are not minutes of trying: the steps and
                    # the restart count from the moment the PC is awake again
                    self.fresh_start_of_trying(now)
                    self.state["down"]["slept"] = True

        p = self.probe()
        st = self.state
        down = st.get("down")
        if p["ok"]:
            if down:
                since = dt.datetime.fromisoformat(down["since"])
                mins = (now - since).total_seconds() / 60.0
                fixed = down.get("last_step") or "nothing -- it came back by itself"
                self.log("BACK: internet returned after %.1f min. Fixed by: %s"
                         % (mins, fixed))
                st["outages"] = (st.get("outages", []) + [{
                    "from": down["since"], "to": now.isoformat(timespec="seconds"),
                    "min": round(mins, 1), "fixed_by": fixed,
                    "kind": down.get("kind")}])[-60:]
                st["down"] = None
                st.pop("warned", None)
                st.pop("reboot_refused_said", None)
                self.save_state()
                self.last_ok_line = now
            elif (self.last_ok_line is None or
                  (now - self.last_ok_line).total_seconds() >=
                  self.cfg["ok_line_every_min"] * 60):
                self.log("ok: %s" % self.words(p))
                self.last_ok_line = now
                self.state["last_ok"] = now.isoformat(timespec="seconds")
                self.save_state()
            if st.get("ts_paused"):
                self.log("Tailscale was left paused -- %s" % self.ensure_tailscale())
            st["last_ok"] = now.isoformat(timespec="seconds")
            return p

        # -- down --
        if not down:
            down = {"since": now.isoformat(timespec="seconds"), "done": [],
                    "kind": self.words(p), "last_step": None}
            st["down"] = down
            self.log("DOWN: %s" % self.words(p))
            if not self.healing_off():
                said = self.ensure_adapters()
                self.log("adapters: %s" % said)
                if "ENABLED again" in said:
                    down["last_step"] = "an adapter found switched off, switched on again"
            self.picture(60)
            self.save_state()
            return p

        since = dt.datetime.fromisoformat(down.get("heal_from") or down["since"])
        mins = (now - since).total_seconds() / 60.0
        if self.healing_off():
            if not down.get("off_said"):
                self.log("healing is SWITCHED OFF -- only recording")
                down["off_said"] = True
                self.save_state()
            return p
        for i, (at_min, name) in enumerate(self.cfg["steps"]):
            key = "%d:%s" % (i, name)
            if mins >= at_min and key not in down["done"]:
                down["done"].append(key)
                down["last_step"] = name
                self.save_state()
                self.log("HEAL step %s (down %.1f min): ..." % (name, mins))
                try:
                    said = self.step(name)
                except Exception as ex:                        # noqa: BLE001
                    said = "failed: %s: %s" % (ex.__class__.__name__, ex)
                self.log("        %s" % said)
                if name == "tailscale_pause" and "CAME BACK" in said:
                    down["tailscale_suspect"] = True
                self.save_state()
                return p          # one step per tick; the next tick re-checks
        if mins >= 20 and not down.get("picture2"):
            down["picture2"] = True
            self.picture(30)
            self.save_state()
        self.maybe_reboot(mins, now)
        return p

    # ---- the loop ------------------------------------------------------------
    def start(self):
        self.load()
        rp = self.state.pop("restart_pending", None)
        self.log("=" * 50)
        self.log("netwatch %s started (uptime %.0f min)%s" % (
            VERSION, self.w.uptime_min(),
            ("; after its own restart of %s" % rp["at"]) if rp else ""))
        if self.state.get("down"):
            if rp:
                self.state["down"]["last_step"] = "restart of the PC"
            else:
                self.state["down"]["last_step"] = "a restart by hand (or power off/on)"
            self.fresh_start_of_trying(self.w.now())
        if self.state.get("ts_paused"):
            self.log("Tailscale was left paused -- starting it: %s" % self.ensure_tailscale())
        self.save_state()
        self.do_mirror(force=True)

    def run_forever(self):
        self.start()
        while True:
            try:
                self.tick()
            except Exception as ex:                            # noqa: BLE001
                self.log("tick error: %s: %s" % (ex.__class__.__name__, ex))
            self.last_end = self.w.mono()
            self.do_mirror()
            self.w.sleep(self.cfg["check_every_s"])


def take_lock():
    """One copy only. A file lock (a port can sit in Windows' excluded range)."""
    try:
        import msvcrt
    except ImportError:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", LOCK_PORT))
            return s
        except OSError:
            return None
    try:
        os.makedirs(HOME, exist_ok=True)
        fh = open(os.path.join(HOME, "netwatch.lock"), "a+")
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        return fh
    except OSError:
        return None


def main():
    if "--once" in sys.argv:
        # the set-up's self-test: one start and one check, printed, then out
        w = Watch()
        w.start()
        p = w.tick()
        w.do_mirror(force=True)
        print("netwatch %s self-test: %s" % (VERSION, Watch.words(p)))
        try:
            print("".join(open(w.log_path, encoding="utf-8").readlines()[-12:]))
        except OSError as ex:
            print("log not readable: %s" % ex)
        return 0
    lock = take_lock()
    if lock is None:
        return 0                 # another copy is running -- the task's 5-minute
                                 # repeat lands here and leaves quietly
    Watch().run_forever()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:                                      # noqa: BLE001
        import traceback
        for p in (os.path.join(HOME, "crash.txt"),
                  os.path.join(MIRROR, "netwatch_crash.txt")):
            try:
                with open(p, "a", encoding="utf-8") as fh:
                    fh.write("%s\n%s\n" % (dt.datetime.now().isoformat(),
                                           traceback.format_exc()))
            except Exception:                                  # noqa: BLE001
                pass
        raise
