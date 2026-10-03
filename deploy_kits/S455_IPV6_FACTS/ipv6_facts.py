#!/usr/bin/env python3
"""ipv6_facts.py -- kit S455_IPV6_FACTS (session 291, 03-Oct-2026). PARENT. READ-ONLY.

F-692: followup.dr-manoj.in has one IPv4 address and no IPv6 address, so a PC on an IPv6-only connection (the owner's
phone hotspot on 02-Oct) cannot reach this server at all. Before anything is changed, this reads what the box has:
its IPv6 addresses and route, what listens on the web ports, the web server's own listener lines, the firewall's
IPv6 side, and whether the site already answers on the box's own IPv6 address. It changes no setting, opens no port,
restarts nothing. It writes ONE file, argv[1], and prints a short summary. Standard library only.
"""
import hashlib, json, os, re, socket, subprocess, sys, time

SITE = "followup.dr-manoj.in"
PORTS = ("80", "443", "7080", "8088")
LSWS = os.environ.get("LSWS_ROOT", "/usr/local/lsws")


def run(cmd, t=15):
    """(rc, text). Never raises; a missing program is rc 127."""
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=t,
                           stdin=subprocess.DEVNULL, universal_newlines=True)
        return p.returncode, (p.stdout or "").strip()
    except FileNotFoundError:
        return 127, "not installed"
    except subprocess.TimeoutExpired:
        return 124, "timed out"
    except Exception as ex:                                    # noqa: BLE001
        return 1, "%s: %s" % (ex.__class__.__name__, ex)


def lines(text, n=40):
    return [l.rstrip() for l in text.splitlines() if l.strip()][:n]


def addr6_global():
    rc, out = run(["ip", "-6", "-o", "addr", "show", "scope", "global"])
    got = []
    for l in lines(out):
        m = re.search(r"^\d+:\s+(\S+)\s+inet6\s+([0-9a-fA-F:]+)/(\d+)(.*)$", l)
        if m:
            got.append({"dev": m.group(1), "addr": m.group(2), "prefix": int(m.group(3)),
                        "flags": " ".join(w for w in m.group(4).split() if w in ("temporary", "deprecated", "dynamic", "tentative", "dadfailed"))})
    return rc, got, (out if rc else "")


def lsws_listeners():
    conf = os.path.join(LSWS, "conf", "httpd_config.conf")
    out = {"conf": conf, "present": os.path.isfile(conf), "listeners": []}
    try:
        with open(conf, "rb") as fh:
            raw = fh.read()
    except OSError as ex:
        out["error"] = str(ex)
        return out
    out["conf_md5"] = hashlib.md5(raw).hexdigest()
    out["conf_bytes"] = len(raw)
    text = raw.decode("utf-8", "replace")
    for m in re.finditer(r"(?m)^listener\s+(\S+)\s*\{(.*?)^\}", text, re.S):
        body = m.group(2)
        one = {"name": m.group(1), "line": text.count("\n", 0, m.start()) + 1}
        for key in ("address", "secure"):
            k = re.search(r"(?m)^\s*%s\s+(\S+)" % key, body)
            one[key] = k.group(1) if k else None
        one["maps"] = len(re.findall(r"(?m)^\s*map\s+", body))
        out["listeners"].append(one)
    try:
        with open(os.path.join(LSWS, "VERSION"), "r") as fh:
            out["version"] = fh.read().strip()[:40]
    except OSError:
        out["version"] = None
    return out


def main():
    dest = sys.argv[1]
    f = {"kit": "S455_IPV6_FACTS", "read_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "host": socket.gethostname(),
         "site": SITE, "changed_on_this_server": "nothing"}
    rc, addrs, err = addr6_global()
    f["addr6_global"] = addrs
    if err:
        f["addr6_error"] = err[:300]
    rc, out = run(["ip", "-6", "route", "show", "default"])
    f["route6_default"] = lines(out, 6) if rc == 0 else []
    if rc:
        f["route6_error"] = out[:200]
    f["disable_ipv6"] = {}
    for k in ("all", "default"):
        try:
            with open("/proc/sys/net/ipv6/conf/%s/disable_ipv6" % k) as fh:
                f["disable_ipv6"][k] = fh.read().strip()
        except OSError:
            f["disable_ipv6"][k] = None
    rc, out = run(["ss", "-H", "-ltn"])
    if rc:
        f["listening_error"], out = out[:200], ""
    f["listening"] = sorted({l.split()[3] for l in lines(out, 400) if len(l.split()) > 3 and l.split()[3].rsplit(":", 1)[-1] in PORTS})
    f["web_server"] = lsws_listeners()
    rc, out = run(["ufw", "status"])
    f["ufw_status"] = lines(out, 40) if rc == 0 else out[:200]
    try:
        with open("/etc/default/ufw") as fh:
            f["ufw_ipv6_line"] = next((l.strip() for l in fh if l.strip().upper().startswith("IPV6=")), None)
    except OSError:
        f["ufw_ipv6_line"] = None
    rc, out = run(["ip6tables", "-S", "INPUT"])
    f["ip6tables_input"] = lines(out, 30) if rc == 0 else out[:200]
    f["dns"] = {}
    for name, fam in (("A", socket.AF_INET), ("AAAA", socket.AF_INET6)):
        try:
            f["dns"][name] = sorted({a[4][0] for a in socket.getaddrinfo(SITE, 443, fam, socket.SOCK_STREAM)})
        except socket.gaierror as ex:
            f["dns"][name] = []
            f["dns"][name + "_note"] = str(ex)
    rc, out = run(["curl", "-6", "-sS", "-m", "10", "-o", "/dev/null", "-w", "%{http_code}", "https://ipv6.google.com/"], t=20)
    f["outbound_ipv6_test"] = out[:200]
    f["site_on_own_ipv6"] = []
    for a in [x["addr"] for x in addrs if "temporary" not in x["flags"] and "deprecated" not in x["flags"]][:4]:
        rc, out = run(["curl", "-6", "-sS", "-m", "10", "-o", "/dev/null", "-w", "%{http_code}",
                       "--resolve", "%s:443:[%s]" % (SITE, a), "https://%s/finance/healthz" % SITE], t=20)
        f["site_on_own_ipv6"].append({"addr": a, "answer": out[:200]})
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(f, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, dest)
    has_addr = bool(addrs)
    v6_listen = any(l.startswith("[::]:") or l.startswith("*:") or (l.startswith("[") and not l.startswith("[::1]")) for l in f["listening"])
    answers = [s["answer"] for s in f["site_on_own_ipv6"]]
    print("   this server has its own IPv6 address : %s" % ("YES (%d)" % len(addrs) if has_addr else "NO"))
    print("   a way out over IPv6                   : %s" % ("YES" if f["route6_default"] else "NO"))
    print("   the web server listens on IPv6        : %s" % ("YES" if v6_listen else "NO"))
    print("   the site answers on that address      : %s" % (", ".join(answers) if answers else "not tried (no address)"))
    print("   the name has an IPv6 address in DNS   : %s" % ("YES" if f["dns"].get("AAAA") else "NO"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
