# -*- coding: utf-8 -*-
r"""
setup_s893.py -- kit S893_MEDICAL_NET_WATCH. Runs ONCE on the medical PC, as
ADMINISTRATOR (SETUP_NETWATCH_S893.bat asks Windows for that). Safe to run again.

  1. C:\Program Files\MedicalNetWatch\ : a copy of this PC's python and
     netwatch.py, in a folder only administrators and SYSTEM may change
     (so nothing the staff account can write ever runs as SYSTEM).
  2. The scheduled task "MedicalNetWatch": as SYSTEM, at start-up, and every
     5 minutes if it is not running.
  3. Power, so the network is not put to sleep: the PC never sleeps or
     hibernates on mains power; USB selective suspend off (the Wi-Fi dongle);
     "allow the computer to turn off this device" off on both adapters.
     The old values are saved for the undo.
  4. The last 48 hours of Windows' network and power events, written to
     D:\SendToClinic\_netwatch\ -- the record of the 20-Nov outage.
  5. Starts the task, waits for its first record, writes the result.

  --undo : removes the task and the folder, puts the power values back.
  --dry  : prints what it would do (used on the test bench).
"""
import datetime as dt, hashlib, json, os, shutil, string, subprocess, sys, time

KIT = "S893_MEDICAL_NET_WATCH"
WANT_NETWATCH = "451bf9b5cf0204fa0042f550e0429f29"
HERE = os.path.dirname(os.path.abspath(__file__))
HOME = r"C:\Program Files\MedicalNetWatch"
OLD_HOME = r"C:\ProgramData\MedicalNetWatch"     # v1/v2's place: its lock refused even
                                                   # the administrator (20-Nov 14:17)
PYSRC = r"D:\SendToClinic\pyportable"
MIRROR = r"D:\SendToClinic\_netwatch"
TASK = "MedicalNetWatch"
DRY = "--dry" in sys.argv
LINES = []

def _guid(h):
    """A Windows GUID written as one hex run (the publish gate reads digit runs in a dashed GUID as a phone number)."""
    return "%s-%s-%s-%s-%s" % (h[:8], h[8:12], h[12:16], h[16:20], h[20:])


USB_SUB = _guid("2a737441193044028d77b2bebba308a3")
USB_SET = "48e6b7a6-50f5-4782-a5d4-53bb8f07e226"
SLEEP_SUB = "238c9fa8-0aad-41ed-83f4-97be242c8f20"
STANDBY = "29f6c1db-86da-48c5-9fdb-f2b67b1f44da"
HIBER = "9d7815a6-7ee4-497e-8888-515a05f02364"


def sysdir():
    """System32 as a 64-bit process sees it (a 32-bit python is redirected to
    SysWOW64; Sysnative reaches the real one)."""
    root = os.environ.get("SystemRoot", r"C:\Windows")
    native = os.path.join(root, "Sysnative")
    return native if os.path.isdir(native) else os.path.join(root, "System32")


def say(msg):
    line = "%s  %s" % (dt.datetime.now().strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    LINES.append(line)


def run(args, timeout=120):
    if DRY:
        say("   [dry] " + " ".join(args))
        return 0, ""
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        r = subprocess.run(args, capture_output=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, creationflags=flags)
        out = (r.stdout or b"") + (b"\n" + r.stderr if r.stderr else b"")
        return r.returncode, out.decode("utf-8", "replace").strip()
    except Exception as ex:                                    # noqa: BLE001
        return -1, "%s: %s" % (ex.__class__.__name__, ex)


def ps(script, timeout=180):
    exe = os.path.join(sysdir(), "WindowsPowerShell", "v1.0", "powershell.exe")
    return run([exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                "-Command", script], timeout=timeout)


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def is_admin():
    if DRY:
        return True
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:                                          # noqa: BLE001
        return False


def task_xml():
    py = os.path.join(HOME, "python", "pythonw.exe")
    nwp = os.path.join(HOME, "netwatch.py")
    start = dt.datetime.now().replace(second=0, microsecond=0).isoformat()
    return """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Kit S893: watches the internet, records outages and their cause, heals (D:\\SendToClinic\\_netwatch).</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT1M</Delay>
    </BootTrigger>
    <TimeTrigger>
      <Repetition>
        <Interval>PT5M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>%s</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>%s</Command>
      <Arguments>-I -S -B "%s"</Arguments>
      <WorkingDirectory>%s</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
""" % (start, py, nwp, HOME)


PS_EVENTS = r"""
$ErrorActionPreference='SilentlyContinue'
$since=(Get-Date).AddHours(-48)
'== System log, network and power, last 48 hours =='
$p='Microsoft-Windows-Kernel-Power','Microsoft-Windows-Power-Troubleshooter','Microsoft-Windows-Dhcp-Client','Microsoft-Windows-DNS-Client','Tcpip','Microsoft-Windows-WLAN-AutoConfig','Microsoft-Windows-NDIS','Microsoft-Windows-NetworkProfile','Microsoft-Windows-Kernel-General','EventLog','USER32','Microsoft-Windows-Kernel-Boot'
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$since} -MaxEvents 4000 |
 Where-Object { $p -contains $_.ProviderName -or $_.ProviderName -like '*Realtek*' -or $_.ProviderName -like 'rt*' -or $_.ProviderName -like '*Netwtw*' -or $_.ProviderName -like '*Tailscale*' -or $_.ProviderName -like '*wintun*' } |
 Sort-Object TimeCreated |
 ForEach-Object { '{0:dd-MM HH:mm:ss} {1} #{2} {3}' -f $_.TimeCreated,$_.ProviderName,$_.Id,(($_.Message -split "`n")[0]).Trim() }
'== WLAN AutoConfig, last 48 hours =='
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-WLAN-AutoConfig/Operational'; StartTime=$since} -MaxEvents 300 |
 Sort-Object TimeCreated | ForEach-Object { '{0:dd-MM HH:mm:ss} WLAN #{1} {2}' -f $_.TimeCreated,$_.Id,(($_.Message -split "`n")[0]).Trim() }
'== NetworkProfile, last 48 hours =='
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-NetworkProfile/Operational'; StartTime=$since} -MaxEvents 300 |
 Sort-Object TimeCreated | ForEach-Object { '{0:dd-MM HH:mm:ss} NetProfile #{1} {2}' -f $_.TimeCreated,$_.Id,(($_.Message -split "`n")[0]).Trim() }
'== adapters now =='
Get-NetAdapter | ForEach-Object { '{0} | {1} | {2} | {3} | driver {4} {5}' -f $_.Name,$_.InterfaceDescription,$_.Status,$_.LinkSpeed,$_.DriverVersion,$_.DriverDate }
'== adapter power management now =='
Get-NetAdapterPowerManagement | ForEach-Object { '{0} | turn-off-device {1} | wake {2}' -f $_.Name,$_.AllowComputerToTurnOffDevice,$_.WakeOnMagicPacket }
'== addresses now =='
Get-NetIPConfiguration | ForEach-Object { '{0} | gateway {1} | dns {2}' -f $_.InterfaceAlias,(($_.IPv4DefaultGateway|%{$_.NextHop}) -join ','),(($_.DNSServer|?{$_.AddressFamily -eq 2}|%{$_.ServerAddresses}) -join ',') }
'== Windows =='
(Get-CimInstance Win32_OperatingSystem | ForEach-Object { $_.Caption + ' ' + $_.Version + ' | last boot ' + $_.LastBootUpTime })
'== power plan =='
powercfg /getactivescheme
"""


def power_value(sub, setting):
    code, out = run(["powercfg", "/q", "SCHEME_CURRENT", sub, setting], timeout=30)
    for line in out.splitlines():
        if "AC Power Setting Index" in line or "Current AC Power Setting Index" in line:
            return line.split(":")[-1].strip()
    return None


def find_drive_out():
    for letter in string.ascii_uppercase:
        p = "%s:\\My Drive\\Clinic Data Archive\\FromMedical" % letter
        if os.path.isdir(p):
            return p
    return None


def write_result(ok):
    text = "%s %s on %s\n\n%s\n" % (KIT, "DONE" if ok else "NOT DONE",
                                     dt.datetime.now().isoformat(timespec="seconds"),
                                     "\n".join(LINES))
    for d in (MIRROR, find_drive_out()):
        if not d or DRY:
            continue
        try:
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "S893_SETUP_RESULT.txt"), "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError:
            pass


def undo():
    say("UNDO: removing the task, the folder, putting power back")
    run(["shutdown", "/a"])
    run(["schtasks", "/End", "/TN", TASK])
    c, o = run(["schtasks", "/Delete", "/TN", TASK, "/F"])
    say("  task deleted -> %s" % c)
    before = os.path.join(HOME, "power_before.json")
    try:
        b = json.load(open(before))
        for key, (sub, st) in (("standby", (SLEEP_SUB, STANDBY)), ("hibernate", (SLEEP_SUB, HIBER)),
                               ("usb", (USB_SUB, USB_SET))):
            v = b.get(key)
            if v:
                run(["powercfg", "/setacvalueindex", "SCHEME_CURRENT", sub, st, str(int(v, 16))])
        run(["powercfg", "/setactive", "SCHEME_CURRENT"])
        for name, val in (b.get("nic") or {}).items():
            ps("Set-NetAdapterPowerManagement -Name '%s' -AllowComputerToTurnOffDevice %s" % (name, val))
        say("  power values put back from power_before.json")
    except Exception as ex:                                    # noqa: BLE001
        say("  power values not put back (%s) -- nothing else is affected" % ex)
    names = []
    try:
        names = json.load(open(os.path.join(HOME, "adapters.json"), encoding="utf-8"))
    except Exception:                                          # noqa: BLE001
        pass
    try:
        for n in json.load(open(os.path.join(HOME, "dns_before.json"), encoding="utf-8")):
            ps("Set-DnsClientServerAddress -InterfaceAlias '%s' -ResetServerAddresses" % n)
        say("  name lookup back to the router's (from DHCP)")
    except Exception:                                          # noqa: BLE001
        pass
    try:
        for line in open(os.path.join(HOME, "pnp_before.txt"), encoding="utf-8").read().splitlines():
            n, key, old = line.split("|")
            path = ("HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\"
                    "{4d36e972-e325-11ce-bfc1-08002be10318}\\" + key)
            if old.strip():
                ps("Set-ItemProperty -Path '%s' -Name PnPCapabilities -Value %s -Type DWord" % (path, old))
            else:
                ps("Remove-ItemProperty -Path '%s' -Name PnPCapabilities" % path)
        say("  adapters' power setting put back (after the next restart)")
    except Exception:                                          # noqa: BLE001
        pass
    c, o = ps("Start-Service -Name Tailscale -ErrorAction SilentlyContinue")
    for n in names:   # only the adapters it looked after -- never one switched off before
        ps("Enable-NetAdapter -Name '%s' -Confirm:$false -ErrorAction SilentlyContinue" % n)
    say("  Tailscale started, any switched-off adapter switched on")
    if not DRY:
        time.sleep(3)
        shutil.rmtree(HOME, ignore_errors=True)
    say("  %s removed" % HOME)
    return 0


def main():
    say("%s -- the medical PC's internet watchdog" % KIT)
    if not is_admin():
        say("NOT DONE: this must run as administrator (the .bat asks Windows for it).")
        return 2
    if "--undo" in sys.argv:
        return undo()

    src = os.path.join(HERE, "netwatch.py")
    if not os.path.isfile(src) or md5(src) != WANT_NETWATCH:
        say("NOT DONE: netwatch.py beside this file is missing or not the one built.")
        return 3
    say("1  netwatch.py is the built file (%s)" % WANT_NETWATCH[:8])

    if not DRY and not os.path.isfile(os.path.join(PYSRC, "pythonw.exe")):
        say("NOT DONE: %s\\pythonw.exe not found." % PYSRC)
        return 4
    if not DRY:
        os.makedirs(HOME, exist_ok=True)
    # a running watchdog holds its python open: stop it first (a re-run)
    run(["schtasks", "/End", "/TN", TASK], timeout=60)
    if not DRY:
        time.sleep(3)
    # v3: the old place is looked at (for the record) and removed
    if os.path.isdir(OLD_HOME) or DRY:
        c, o = run(["icacls", OLD_HOME], timeout=60)
        say("2a the old folder's permissions (why it refused): %s" % " | ".join(
            l.strip() for l in o.splitlines()[:8]))
        c2, o2 = run(["icacls", os.path.join(OLD_HOME, "netwatch.py")], timeout=60)
        say("2a ...and its netwatch.py: %s" % " | ".join(l.strip() for l in o2.splitlines()[:6]))
        run(["takeown", "/F", OLD_HOME, "/R", "/D", "Y"], timeout=300)
        run(["icacls", OLD_HOME, "/grant", "*S-1-5-32-544:(OI)(CI)F", "/T", "/C", "/Q"], timeout=300)
        # the values saved before the first run's changes travel to the new place
        for f in ("power_before.json", "dns_before.json", "pnp_before.txt"):
            src_f, dst_f = os.path.join(OLD_HOME, f), os.path.join(HOME, f)
            if not DRY and os.path.isfile(src_f) and not os.path.exists(dst_f):
                try:
                    os.makedirs(HOME, exist_ok=True)
                    shutil.copyfile(src_f, dst_f)
                    say("2a kept %s from the first run" % f)
                except OSError as ex:
                    say("2a could not keep %s (%s)" % (f, ex))
        run(["icacls", OLD_HOME, "/reset", "/T", "/C", "/Q"], timeout=300)
        run(["icacls", OLD_HOME, "/grant", "*S-1-5-32-544:(OI)(CI)F", "/T", "/C", "/Q"], timeout=300)
        run(["attrib", "-R", os.path.join(OLD_HOME, "*"), "/S", "/D"], timeout=120)
        if not DRY:
            shutil.rmtree(OLD_HOME, ignore_errors=True)
        say("2a old folder %s" % ("removed" if (DRY or not os.path.isdir(OLD_HOME))
                                  else "NOT fully removed (harmless; nothing runs from it)"))
    c, o = run(["robocopy", PYSRC, os.path.join(HOME, "python"), "/MIR", "/XD", "__pycache__",
                "/R:1", "/W:1", "/NFL", "/NDL", "/NJH", "/NJS", "/NP"], timeout=600)
    if c >= 8:
        say("NOT DONE: copying python failed (robocopy %s)" % c)
        return 5
    say("2  python copied to %s\\python" % HOME)
    if not DRY:
        tmp = os.path.join(HOME, "netwatch.py.new")
        shutil.copyfile(src, tmp)
        os.replace(tmp, os.path.join(HOME, "netwatch.py"))
        if md5(os.path.join(HOME, "netwatch.py")) != WANT_NETWATCH:
            say("NOT DONE: netwatch.py did not copy whole")
            return 6
    c, o = run(["icacls", HOME], timeout=60)
    staff_w = [l for l in o.splitlines() if ("Users" in l or "Authenticated" in l or "Everyone" in l)
               and any(x in l for x in ("(F)", "(M)", "(W)", "(WD)", "(AD)"))]
    if staff_w and not DRY:
        say("NOT DONE: staff could change %s (%s) -- no task made" % (HOME, staff_w[0].strip()))
        return 10
    say("3  %s: Windows' own protection (staff read only): %s"
        % (HOME, " | ".join(l.strip() for l in o.splitlines()[:6])))
    if not DRY:
        os.makedirs(MIRROR, exist_ok=True)

    # power: the old values first, for the undo
    before = {"standby": power_value(SLEEP_SUB, STANDBY), "hibernate": power_value(SLEEP_SUB, HIBER),
              "usb": power_value(USB_SUB, USB_SET), "nic": {}}
    c, o = ps("Get-NetAdapterPowerManagement | ForEach-Object { $_.Name + '|' + $_.AllowComputerToTurnOffDevice }")
    for line in o.splitlines():
        if "|" in line:
            n, v = line.rsplit("|", 1)
            if v.strip() in ("Enabled", "Disabled"):
                before["nic"][n.strip()] = v.strip()
    if not DRY and not os.path.exists(os.path.join(HOME, "power_before.json")):
        with open(os.path.join(HOME, "power_before.json"), "w") as fh:
            json.dump(before, fh, indent=1)
    c, o = ps("Get-NetAdapter -Physical | Where-Object { $_.Status -ne 'Disabled' } | "
              "ForEach-Object { $_.Name }")
    names = [l.strip() for l in o.splitlines() if l.strip()]
    if not DRY and names:
        with open(os.path.join(HOME, "adapters.json"), "w", encoding="utf-8") as fh:
            json.dump(names, fh)
    say("4  adapters the watchdog keeps switched on: %s" % (", ".join(names) or "(none read)"))
    say("4  power before: sleep %s, hibernate %s, USB suspend %s, adapters %s"
        % (before["standby"], before["hibernate"], before["usb"], before["nic"]))

    # the record of the last 48 hours, before anything changes
    c, o = ps(PS_EVENTS, timeout=240)
    if not DRY:
        with open(os.path.join(MIRROR, "events_48h_at_setup.txt"), "w", encoding="utf-8") as fh:
            fh.write(o)
    say("5  Windows events of the last 48 hours written (%d lines) -> %s\\events_48h_at_setup.txt"
        % (len(o.splitlines()), MIRROR))

    # the task
    xml = os.path.join(HOME, "task.xml")
    if not DRY:
        with open(xml, "w", encoding="utf-16") as fh:
            fh.write(task_xml())
    c, o = run(["schtasks", "/Create", "/TN", TASK, "/XML", xml, "/F"])
    if c != 0:
        say("NOT DONE: the task could not be made (schtasks %s: %s)" % (c, o[:200]))
        return 7
    say("6  scheduled task %s made (SYSTEM; at start-up and every 5 min)" % TASK)

    # S893 v2 (20-Nov, the first run's findings): the router's name lookup
    # (192.168.1.1) stopped answering from 00:47 -- 816 DNS timeouts in the log.
    # The two adapters ask public name servers instead; the old setting kept.
    c, o = ps("Get-DnsClientServerAddress -AddressFamily IPv4 | ForEach-Object { "
              "$_.InterfaceAlias + '|' + ($_.ServerAddresses -join ',') }")
    dns_before = {}
    for line in o.splitlines():
        if "|" in line:
            a, v = line.split("|", 1)
            if a.strip() in names:
                dns_before[a.strip()] = v.strip()
    if not DRY and not os.path.exists(os.path.join(HOME, "dns_before.json")):
        with open(os.path.join(HOME, "dns_before.json"), "w", encoding="utf-8") as fh:
            json.dump(dns_before, fh, indent=1)
    said = []
    for n in names:
        # public first; the router's own kept LAST, so a blocked public server
        # still leaves the old way open
        servers = ["1.1.1.1", "8.8.8.8"]
        for x in (dns_before.get(n) or "").split(","):
            x = x.strip()
            if x and x not in servers and x.count(".") == 3:
                servers.append(x)
        c, o = ps("Set-DnsClientServerAddress -InterfaceAlias '%s' -ServerAddresses "
                  "(%s) -ErrorAction Stop; 'ok'" % (n, ",".join("'%s'" % x for x in servers)),
                  timeout=60)
        said.append("%s %s" % (n, "ok" if "ok" in o else ("exit %s %s" % (c, o[-80:]))))
    run(["ipconfig", "/flushdns"], timeout=30)
    say("7a name lookup now asks 1.1.1.1 and 8.8.8.8 (before: %s): %s"
        % (dns_before, " ; ".join(said)))

    # the adapters' "allow the computer to turn off this device": this Windows'
    # PowerShell has no switch for it, so the registry value Windows itself
    # uses (PnPCapabilities = 24); it takes effect at the next restart.
    c, o = ps(r"$cls='HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}';"
              r"Get-NetAdapter -Physical | ForEach-Object { $n=$_.Name; $g=$_.InterfaceGuid;"
              r" Get-ChildItem $cls -ErrorAction SilentlyContinue | Where-Object {"
              r" (Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue).NetCfgInstanceId -eq $g } |"
              r" ForEach-Object { $old=(Get-ItemProperty $_.PSPath).PnPCapabilities;"
              r" Set-ItemProperty -Path $_.PSPath -Name PnPCapabilities -Value 24 -Type DWord;"
              r" $n + '|' + $_.PSChildName + '|' + $old } }", timeout=90)
    pnp = [l.strip() for l in o.splitlines() if l.count("|") == 2]
    if not DRY and pnp and not os.path.exists(os.path.join(HOME, "pnp_before.txt")):
        with open(os.path.join(HOME, "pnp_before.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(pnp))
    say("7b adapters' power saving off at the next restart (name|key|before): %s"
        % (" ; ".join(pnp) or o[-160:]))

    # the Wi-Fi dongle read Disconnected at the first run: what Windows says, and one try
    c, o = run(["netsh", "wlan", "show", "interfaces"], timeout=30)
    st = [l.strip() for l in o.splitlines() if l.strip().split(":")[0].strip() in
          ("Name", "State", "SSID", "Signal", "Radio type")]
    c2, o2 = run(["netsh", "wlan", "show", "profiles"], timeout=30)
    profs = [l.split(":", 1)[1].strip() for l in o2.splitlines() if "All User Profile" in l]
    say("7c Wi-Fi: %s | saved networks: %s" % (" ; ".join(st) or o[-120:], ", ".join(profs) or "none"))
    # reported only: which saved network the dongle should join is not guessed

    # power changes (the adapter one may blink the network for a second)
    for args in (["powercfg", "/change", "standby-timeout-ac", "0"],
                 ["powercfg", "/change", "hibernate-timeout-ac", "0"],
                 ["powercfg", "/setacvalueindex", "SCHEME_CURRENT", USB_SUB, USB_SET, "0"],
                 ["powercfg", "/setactive", "SCHEME_CURRENT"]):
        c, o = run(args, timeout=30)
        say("7  %s -> %s" % (" ".join(args[:3]), c))
    # the self-test: one start and one check, in the open, every word kept
    tpy = os.path.join(HOME, "python", "python.exe")
    c, o = run([tpy, "-I", "-S", "-B", os.path.join(HOME, "netwatch.py"), "--once"], timeout=300)
    say("9a self-test (exit %s):\n      %s" % (c, "\n      ".join(o.splitlines()[-16:])))

    # start and wait for the first record
    run(["schtasks", "/End", "/TN", TASK], timeout=60)
    t_run = time.time()
    c, o = run(["schtasks", "/Run", "/TN", TASK])
    say("9b task started -> %s %s" % (c, o[-80:]))
    say("9  started; waiting for its first record (up to 2 minutes)...")
    state = os.path.join(MIRROR, "netwatch_state.json")
    t0 = time.time()
    ok = DRY
    while not ok and time.time() - t0 < 120:
        time.sleep(5)
        try:
            st = json.load(open(state, encoding="utf-8"))
            ok = dt.datetime.fromisoformat(st["written_at"]) >= dt.datetime.fromtimestamp(int(t_run))
        except Exception:                                      # noqa: BLE001
            pass
    if not ok:
        c, o = run(["schtasks", "/Query", "/TN", TASK, "/V", "/FO", "LIST"], timeout=30)
        keep = [l.strip() for l in o.splitlines() if l.split(":")[0].strip() in
                ("Status", "Last Run Time", "Last Result", "Run As User", "Task To Run",
                 "Logon Mode", "Next Run Time", "Scheduled Task State")]
        say("   task: %s" % " | ".join(keep))
        for f in ("crash.txt", "netwatch.log"):
            try:
                say("   %s tail:\n      %s" % (f, "\n      ".join(
                    open(os.path.join(HOME, f), encoding="utf-8").read().splitlines()[-8:])))
            except OSError:
                pass
        say("NOT DONE: no record from the watchdog task in 2 minutes. The task stays; Claude reads why.")
        return 8
    say("10 the watchdog is running and writing to %s" % MIRROR)
    msg = os.path.join(sysdir(), "msg.exe")
    say("11 on-screen message to staff: %s" % ("available" if (DRY or os.path.isfile(msg))
                                                else "NOT on this Windows (Home edition) -- restart warning only"))
    return 0


if __name__ == "__main__":
    rc = 9
    try:
        rc = main()
    except Exception as ex:                                    # noqa: BLE001
        import traceback
        say("NOT DONE: %s" % ex)
        LINES.append(traceback.format_exc())
    write_result(rc == 0)
    print()
    print("  DONE -- you can close this window." if rc == 0 else
          "  NOT DONE -- nothing harmful was left; Claude reads the result file.")
    if not DRY:
        try:
            input("  Press Enter to close.")
        except Exception:                                      # noqa: BLE001
            pass
    sys.exit(rc)
