# -*- coding: utf-8 -*-
"""make_s823.py -- kit S823_MEDICAL_NET_LINE (session 454, the Sanjeevni chat, 14-Nov-2026).
Makes medical_agent.py S823.1 from S499.1 (d91fa79a) by exact anchors (each must occur once).
python make_s823.py <S499.1 medical_agent.py> <out path>"""
import hashlib, sys
FROM_MD5 = "d91fa79ad972c39e531c70afb1a1c758"
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
if hashlib.md5(b).hexdigest() != FROM_MD5:
    sys.exit("STOP: the source is not S499.1 (%s)" % hashlib.md5(b).hexdigest())
t = b.decode("utf-8")

NET = r'''
# ---------------------------------------------------------------------------
# S823 (14-Nov-2026, F-1133, D966): WHICH CONNECTION CARRIES THIS PC.
# Since 13-Nov the PC has a Wi-Fi USB dongle beside the network cable, both on
# the same Airtel line. Nothing could say which of the two the PC actually uses.
# Windows answers that itself: Find-NetRoute names the adapter it would send a
# packet to the internet through; Get-NetAdapter lists every adapter it sees.
# Read at most every NET_EVERY seconds (PowerShell takes a second or two), never
# allowed to stop the agent: any failure becomes one line in the heartbeat.
# ---------------------------------------------------------------------------
NET_EVERY = 1800              # s: how often the adapters are read again
NET_TIMEOUT = 25              # s: PowerShell gets this long, then the line says so
_NET = {"at": 0.0, "data": None}
_NET_PS = (
    "$ErrorActionPreference='SilentlyContinue';"
    "$a=@(Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,"
    "MediaType,PhysicalMediaType,LinkSpeed,ifIndex);"
    "$r=@(Find-NetRoute -RemoteIPAddress 8.8.8.8 | "
    "Where-Object {$_.InterfaceAlias} | Select-Object InterfaceAlias,ifIndex);"
    "@{adapters=$a;route=$r} | ConvertTo-Json -Depth 3 -Compress")
_WIFI_WORDS = ("wi-fi", "wifi", "wireless", "wlan", "802.11")
_CABLE_WORDS = ("ethernet", "802.3", "gbe", "lan ", "family controller")


def _net_kind(ad):
    """'Wi-Fi', 'cable' or 'other' for one adapter row from Get-NetAdapter."""
    words = " ".join(str(ad.get(k) or "") for k in
                     ("Name", "InterfaceDescription", "PhysicalMediaType",
                      "MediaType")).lower()
    if any(w in words for w in ("tailscale", "virtual", "vpn", "loopback",
                                "hyper-v", "bluetooth", "tap-", "wan miniport")):
        return "other"
    if any(w in words for w in _WIFI_WORDS):
        return "Wi-Fi"
    if any(w in words for w in _CABLE_WORDS):
        return "cable"
    return "other"


def _as_list(x):
    if x is None:
        return []
    if isinstance(x, dict) and isinstance(x.get("value"), list):
        x = x["value"]          # PowerShell 5.1 sometimes wraps an array this way
    return x if isinstance(x, list) else [x]


def net_parse(text):
    """The PowerShell JSON -> {"via": alias|None, "via_kind": ..., "adapters": [...]}.
    A pure function, so the walk can feed it what Windows prints."""
    d = json.loads(text)
    ads = []
    for ad in _as_list(d.get("adapters")):
        if not isinstance(ad, dict):
            continue
        ads.append({"name": str(ad.get("Name") or "?"),
                    "desc": str(ad.get("InterfaceDescription") or ""),
                    "status": str(ad.get("Status") or "?"),
                    "speed": str(ad.get("LinkSpeed") or ""),
                    "index": ad.get("ifIndex"),
                    "kind": _net_kind(ad)})
    via = None
    for r in _as_list(d.get("route")):
        if isinstance(r, dict) and r.get("InterfaceAlias"):
            via = str(r.get("InterfaceAlias"))
    kind = None
    if via:
        for ad in ads:
            if ad["name"] == via:
                kind = ad["kind"]
        if kind is None:
            kind = _net_kind({"Name": via})
    return {"via": via, "via_kind": kind, "adapters": ads, "error": None}


def net_state():
    """Cached; never raises. {"via", "via_kind", "adapters", "error", "read_at"}."""
    if _NET["data"] is not None and time.time() - _NET["at"] < NET_EVERY:
        return _NET["data"]
    data = {"via": None, "via_kind": None, "adapters": [], "error": None,
            "read_at": now().isoformat(timespec="seconds")}
    try:
        ps = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32",
                          "WindowsPowerShell", "v1.0", "powershell.exe")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        r = subprocess.run([ps, "-NoProfile", "-NonInteractive", "-Command", _NET_PS],
                           capture_output=True, timeout=NET_TIMEOUT,
                           creationflags=flags)
        out = (r.stdout or b"").decode("utf-8-sig", "replace").strip()
        if not out:
            data["error"] = "PowerShell gave no answer (exit %s)" % r.returncode
        else:
            got = net_parse(out)
            got["read_at"] = data["read_at"]
            data = got
    except subprocess.TimeoutExpired:
        data["error"] = "PowerShell did not answer in %d s" % NET_TIMEOUT
    except Exception as ex:                                    # noqa: BLE001
        data["error"] = "%s: %s" % (ex.__class__.__name__, str(ex)[:80])
    _NET["data"], _NET["at"] = data, time.time()
    return data


def net_lines(n):
    """The heartbeat's NETWORK lines for one net_state() result. Never raises."""
    try:
        return _net_lines(n)
    except Exception as ex:                                    # noqa: BLE001
        return ["NETWORK : could not be shown -- %s" % ex.__class__.__name__]


def _net_lines(n):
    L = []
    if not n:
        return ["NETWORK : not read yet"]
    if n.get("error"):
        return ["NETWORK : could not be read -- %s" % n["error"]]
    if n.get("via"):
        L.append("NETWORK : the internet goes through %s (%s)"
                 % (n["via"], {"Wi-Fi": "the Wi-Fi dongle", "cable": "the cable"}
                    .get(n.get("via_kind"), "another adapter")))
    else:
        L.append("NETWORK : NO ROUTE TO THE INTERNET found by Windows")
    for ad in n.get("adapters") or []:
        if ad.get("kind") == "other" and ad.get("status") != "Up":
            continue
        L.append("          %-14s %-6s %-12s %s" % (ad["name"][:14], ad["kind"],
                                                  ad["status"][:12], ad["speed"]))
    return L

'''

def once(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit("STOP: anchor '%s' occurs %d times" % (what, n))
    return t.replace(old, new)

t = once(t, 'AGENT_VERSION = "S499.1"', 'AGENT_VERSION = "S823.1"', "version")
t = once(t, 'out["installer"] = os.path.join(inn, "INSTALL_AGENT_S499.bat")',
         'out["installer"] = os.path.join(inn, "INSTALL_AGENT_S823.bat")', "installer")
t = once(t, '"INSTALL_AGENT_S499.bat in ToMedical of the clinic Drive"',
         '"INSTALL_AGENT_S823.bat in ToMedical of the clinic Drive"', "installer words")
t = once(t, "\ndef build_beat(", NET + "\ndef build_beat(", "build_beat")
t = once(t, '        "disk_free_gb_D": free,\n',
         '        "disk_free_gb_D": free,\n        "network": net_state(),\n', "beat field")
t = once(t, '    a("DISK    : %s GB free on D:" % beat["disk_free_gb_D"])\n',
         '    a("DISK    : %s GB free on D:" % beat["disk_free_gb_D"])\n'
         '    for _l in net_lines(beat.get("network")):\n        a(_l)\n', "human line")
open(dst, "wb").write(t.encode("utf-8"))
print("made", dst, hashlib.md5(t.encode("utf-8")).hexdigest())
