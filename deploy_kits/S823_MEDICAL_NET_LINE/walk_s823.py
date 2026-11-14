# -*- coding: utf-8 -*-
"""walk_s823.py -- proves medical_agent.py S823.1's NETWORK line on made-up Windows answers.
python walk_s823.py <medical_agent.py>   (the control: run it on S499.1 -- it must go red)"""
import importlib.util, json, subprocess, sys, types
spec = importlib.util.spec_from_file_location("ag", sys.argv[1])
ag = importlib.util.module_from_spec(spec); spec.loader.exec_module(ag)
R = []
def ck(name, cond):
    R.append((name, bool(cond))); print(("ok   " if cond else "RED  ") + name)

def run(name, fn):
    try:
        fn()
    except Exception as ex:
        ck(name + " (raised %s)" % ex.__class__.__name__, False)

ETH = {"Name": "Ethernet", "InterfaceDescription": "Realtek PCIe GbE Family Controller", "Status": "Up",
       "MediaType": "802.3", "PhysicalMediaType": "802.3", "LinkSpeed": "100 Mbps", "ifIndex": 12}
WIFI = {"Name": "Wi-Fi 2", "InterfaceDescription": "Realtek RTL8188FTV Wireless LAN 802.11n USB 2.0 Network Adapter",
        "Status": "Up", "MediaType": "Native 802.11", "PhysicalMediaType": "Native 802.11", "LinkSpeed": "72.2 Mbps", "ifIndex": 18}
TS = {"Name": "Tailscale", "InterfaceDescription": "Tailscale Tunnel", "Status": "Up", "MediaType": "802.3",
      "PhysicalMediaType": "Unspecified", "LinkSpeed": "100 Gbps", "ifIndex": 7}
WIFI_DOWN = dict(WIFI, Status="Disconnected", LinkSpeed="0 bps")

def t1():
    j = json.dumps({"adapters": [ETH, WIFI, TS], "route": [{"InterfaceAlias": "Wi-Fi 2", "ifIndex": 18},
                                                           {"InterfaceAlias": "Wi-Fi 2", "ifIndex": 18}]})
    n = ag.net_parse(j)
    ck("both up, route by the dongle -> via Wi-Fi 2, kind Wi-Fi", n["via"] == "Wi-Fi 2" and n["via_kind"] == "Wi-Fi")
    ck("kinds: Ethernet cable, Tailscale other", [a["kind"] for a in n["adapters"]] == ["cable", "Wi-Fi", "other"])
    L = ag.net_lines(n)
    ck("line says the Wi-Fi dongle", "through Wi-Fi 2 (the Wi-Fi dongle)" in L[0])
    ck("Tailscale (other, Up) listed, both real adapters listed", sum(1 for l in L[1:]) == 3)
run("t1", t1)

def t2():
    j = json.dumps({"adapters": ETH, "route": {"InterfaceAlias": "Ethernet", "ifIndex": 12}})
    n = ag.net_parse(j)
    ck("one adapter as a dict, route as a dict -> via Ethernet (the cable)", n["via"] == "Ethernet" and n["via_kind"] == "cable")
    ck("line says the cable", "(the cable)" in ag.net_lines(n)[0])
run("t2", t2)

def t3():
    n = ag.net_parse(json.dumps({"adapters": [ETH, WIFI_DOWN], "route": []}))
    ck("no route -> says NO ROUTE", n["via"] is None and "NO ROUTE" in ag.net_lines(n)[0])
    ck("a disconnected real adapter is still listed", any("Disconnected" in l for l in ag.net_lines(n)))
run("t3", t3)

def fake_run(out=b"", exc=None, rc=0):
    def f(*a, **k):
        if exc: raise exc
        return types.SimpleNamespace(stdout=out, returncode=rc)
    return f

def t4():
    real = subprocess.run
    try:
        ag._NET["data"] = None
        subprocess.run = fake_run(exc=subprocess.TimeoutExpired("ps", 25))
        n = ag.net_state(); ck("PowerShell timeout -> one error line, no raise", "did not answer" in ag.net_lines(n)[0])
        ag._NET["data"] = None
        subprocess.run = fake_run(out=b"", rc=1)
        n = ag.net_state(); ck("empty answer -> error line", "no answer" in ag.net_lines(n)[0])
        ag._NET["data"] = None
        subprocess.run = fake_run(out=b"<garbage>")
        n = ag.net_state(); ck("garbage -> error line, no raise", n["error"] and "could not be read" in ag.net_lines(n)[0])
        ag._NET["data"] = None
        subprocess.run = fake_run(exc=FileNotFoundError("powershell.exe"))
        n = ag.net_state(); ck("no PowerShell -> error line, no raise", "FileNotFoundError" in n["error"])
        ag._NET["data"] = None
        calls = []
        def counting(*a, **k):
            calls.append(1); return types.SimpleNamespace(
                stdout=json.dumps({"adapters": [ETH], "route": [{"InterfaceAlias": "Ethernet"}]}).encode(), returncode=0)
        subprocess.run = counting
        ag.net_state(); ag.net_state(); ag.net_state()
        ck("cached: PowerShell asked once in three beats", len(calls) == 1)
        ck("read_at stamped", bool(ag.net_state().get("read_at")))
    finally:
        subprocess.run = real
run("t4", t4)

def t5():
    # the whole heartbeat, with the PC's own readers stood in
    for name, val in (("kit_status", (None, {})), ("captures_today", (0, None, None)), ("ignored_files", []),
                      ("agent_drift", {"checked": True, "differs": False}), ("marg_slots", []),
                      ("backup_count", 0), ("kit_backup_state", {}), ("backup_state_read", {})):
        setattr(ag, name, (lambda v: (lambda *a, **k: v))(val))
    ag._md5 = lambda p: None
    ag._NET["data"] = {"via": "Ethernet", "via_kind": "cable", "adapters": [], "error": None, "read_at": "x"}
    ag._NET["at"] = 10 ** 12
    beat = ag.build_beat(True, 1234, "2026-11-14T06:00:00", 0, {})
    ck("beat carries network", beat.get("network", {}).get("via") == "Ethernet")
    txt = ag.human(beat)
    ck("heartbeat text ends with the NETWORK line after DISK",
       "DISK    :" in txt and txt.rstrip().splitlines()[-1].startswith("NETWORK : the internet goes through Ethernet"))
    ck("heartbeat names S823.1", "agent S823.1" in txt)
    ck("json of the beat still serialises", bool(json.dumps(beat)))
run("t5", t5)

def t6():
    src = open(sys.argv[1], encoding="utf-8").read()
    ck("FIX line names INSTALL_AGENT_S823.bat", 'INSTALL_AGENT_S823.bat' in src and 'INSTALL_AGENT_S499.bat")' not in src)
    ck("medical_agent.py still never in the kit's reach", 'KIT_NEVER = ("medical_agent.py",)' in src)
run("t6", t6)

def t7():
    n = ag.net_parse(json.dumps({"adapters": {"value": [ETH, WIFI], "Count": 2}, "route": {"value": [{"InterfaceAlias": "Ethernet"}], "Count": 1}}))
    ck("PowerShell's {value:[..]} wrapping unwrapped -> via Ethernet", n["via"] == "Ethernet" and len(n["adapters"]) == 2)
    ck("a malformed state shows one line, no raise", ag.net_lines({"via": 5, "adapters": [None]})[0].startswith("NETWORK :"))
    real = subprocess.run
    try:
        ag._NET["data"] = None
        subprocess.run = fake_run(out=b"\xef\xbb\xbf" + json.dumps({"adapters": [ETH], "route": [{"InterfaceAlias": "Ethernet"}]}).encode())
        ck("a UTF-8 BOM before the JSON is read", ag.net_state().get("via") == "Ethernet")
    finally:
        subprocess.run = real
run("t7", t7)

bad = [n for n, ok in R if not ok]
print("WALK %d/%d %s" % (len(R) - len(bad), len(R), "GREEN" if not bad else "RED"))
sys.exit(1 if bad else 0)
