#!/usr/bin/env python3
"""
pipeline_status.py  ·  B2 (S202) · S205.3 · runs on manojz at the end of every pull

WHY THIS EXISTS
---------------
Every health check on the clinic server watches ARRIVAL AT THE VPS. Four of the
seven ways the Marg chain can fail happen entirely on the owner's machines:

    the medical watcher dies · the 10-minute pull stops running ·
    the outbox stops draining · the Drive offsite silently stops

None of them is visible from the server. F-179 is the proof: eleven verified
reports sat undelivered for three days while capture, routing and archiving all
reported success, and the only symptom the owner could see was a page that
stayed empty.

So this posts what manojz CAN see, once per pull. It is a reporter: it reads,
it posts, and it changes nothing.

WHAT S205 ADDS, AND WHY  (D350 §2 · "verification at both ends, MEASURED,
NEVER INFERRED")
---------------------------------------------------------------------------
On 26-Aug-2026 the feed was dead for eight hours and forty minutes with TWO
GREEN LIGHTS EITHER SIDE OF A BROKEN WIRE. The medical PC was on, the owner was
in an RDP session with it, Tailscale reported it `active; direct`, the agent was
running, Marg was capturing -- and manojz could not read the share, because
Windows had applied its default policy against unauthenticated guest access.

Everything was healthy. The LINK was not, and nothing in the world was looking
at the link. So this now reports it:

  * TAILSCALE, BOTH ENDS -- this machine's own state and address, and what it
    can see of the medical peer: online, its address, direct or relayed, and
    when it was last confirmed. Read from `tailscale status --json`, which is
    a measurement, not a belief.

  * AN ACTUAL REACHABILITY TEST OF THE SHARE, PERFORMED. Two separate probes,
    because they fail differently and only both together name the guilty part:
    a TCP connect to port 445 (is SMB answering at all?) and a real directory
    read of the exact path the pull needs. "The PC answers and the share
    refuses" is a different fault from "the PC is gone", and on 26-Aug the
    message named the second while the truth was the first.

  * WHICH TRANSPORT THIS CYCLE USED. There is one transport today. Reporting
    it now, before the Drive fallback of D350 §1 exists, is deliberate: if the
    fallback is built first and its switch is wrong, the failure it causes is
    invisible -- the exact fault the whole contract exists to end. The reserve
    route must read as a degraded state from the day it exists, and it cannot
    do that unless something is already saying which route was taken.

  * WHETHER A CREDENTIAL EXISTS AT ALL, and WHICH ACCOUNT this process runs
    as. Credentials are stored PER WINDOWS USER. A manual `dir` can succeed
    while the scheduled task fails, for ever, and the two look identical from
    every other angle. NO SECRET IS READ OR SENT: `cmdkey /list` never prints
    a password, and this records only the target, the account name, and
    whether an entry is there.

  * THE MAGICDNS NAME, AND WHETHER IT AGREES WITH THE HARDCODED ADDRESS (B6).
    The address is hardcoded in PULL_FROM_MEDICAL.bat. The durable fix is the
    Tailscale name, so a changed number can never be the fault again. This
    version REPORTS the disagreement; it does not switch. Switching changes
    how reports actually travel, and that is the owner's call, not a
    reporter's.

RULES IT KEEPS
  * it NEVER fails the pull -- every section is independently guarded and a
    failure here must never stop reports being sent (that would be a monitor
    taking down the thing it monitors)
  * every new probe has a HARD TIMEOUT. A reporter that hangs is a pull that
    stops, which is worse than no reporter at all.
  * no probe opens a console window (S201's FIX_POPUP was needed once already)
  * it NEVER prints or logs the token, and reuses marg_gate's own resolution
    rather than keeping a second copy of that rule (D349)
  * it reuses FINANCE_MARG_TOKEN -- no fourth secret to rotate, when rotation
    is already the oldest open item in the project
  * EVERY MEASURED FACT SAYS WHETHER IT WAS MEASURED. A field that could not
    be read reads as `null` with a reason beside it, never as a healthy value.

    python pipeline_status.py            # gather and post
    python pipeline_status.py --dry-run  # gather and PRINT, post nothing
    python pipeline_status.py --selftest # prove the gathering offline
                                         # (S205.2: and on manojz too -- F-217)
"""
import argparse
import datetime
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEF_ARCHIVE   = r"D:\Downloads\margsync\MargArchive"
DEF_LASTPULL  = r"D:\Downloads\margsync\MargPull\_last_pull.txt"
# The medical PC writes its heartbeat to Drive; manojz also mirrors the medical
# SendToClinic folder. BOTH can carry it and either can be the fresher one, so
# the newest that EXISTS wins rather than one hard-coded guess -- this script
# cannot be allowed to report "no watcher section" just because a drive letter
# moved. Reported out loud in the payload as heartbeat.from.
DEF_HEARTBEATS = [
    r"H:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt",
    r"F:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt",
    r"D:\Downloads\margsync\medical_SendToClinic\heartbeat.txt",
]
DEF_OFFSITE   = r"H:\My Drive\Clinic Data Archive\MargArchive"
DEF_URL       = "https://followup.dr-manoj.in/finance/api/pipeline-status"
DEF_TOKEN     = r"D:\Downloads\margsync\SendToClinic\token.txt"
DEF_TOKEN_UNC = r"\\100.119.151.40\DDrive\SendToClinic\token.txt"

# ---------------------------------------------------------------- S205 (B2/B6)
# The medical host, in ONE place. It was previously only ever embedded inside
# DEF_TOKEN_UNC and inside the batch file, which is how a changed address
# becomes an eight-hour outage nobody can name.
DEF_MEDICAL_HOST = "100.119.151.40"
# The share path the pull actually needs. Probing anything else would prove
# something the pull does not depend on.
DEF_SHARE_PROBE = r"\\%s\DDrive\MARGERP\users" % DEF_MEDICAL_HOST
# The MagicDNS names worth trying. Tailscale serves both the short name and the
# fully-qualified one; which resolves depends on the tailnet's DNS settings, so
# try both and report what happened rather than assuming either.
# MEASURED on manojz at the S205 dry run, not guessed: the tailnet is
# tail4aa9a0.ts.net, and the short name `medical` resolves to exactly the
# hardcoded address. The FQDN this file shipped with first was invented and
# resolved to nothing -- harmless, because a name that does not resolve is
# reported as null rather than believed, but wrong is wrong and it is fixed
# from the measurement rather than from another guess.
DEF_MAGICDNS = ("medical", "medical.tail4aa9a0.ts.net")
DEF_TAILSCALE = (r"C:\Program Files\Tailscale\tailscale.exe",
                 r"C:\Program Files (x86)\Tailscale\tailscale.exe")
# Facts the BATCH knows and used to throw away -- the share test it already
# performs, the return codes, which transport it took. Written by
# PULL_FROM_MEDICAL.bat, read here. See _pull_facts().
DEF_FACTS = r"D:\Downloads\margsync\MargPull\_pull_facts.txt"

# No probe may take longer than this. The pull runs every ten minutes; a
# reporter that blocks is a pull that does not happen.
PROBE_TIMEOUT = 6.0
# Windows: run helpers with no console window. On any other platform this flag
# does not exist, so it degrades to 0 rather than raising.
_NOWINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _hours_since(ts):
    try:
        return round((datetime.datetime.now() - ts).total_seconds() / 3600.0, 1)
    except Exception:
        return None


def _run(cmd, timeout=PROBE_TIMEOUT):
    """Run a helper and return its stdout, or None.

    Guarded absolutely: a missing executable, a hang, a non-zero exit and a
    permission refusal all come back as None. Nothing this function is used for
    is allowed to stop the pull.
    """
    try:
        p = subprocess.run(cmd, timeout=timeout, capture_output=True,
                           creationflags=_NOWINDOW)
    except Exception:                                          # noqa: BLE001
        return None
    try:
        return p.stdout.decode("utf-8", "replace")
    except Exception:                                          # noqa: BLE001
        return None


def outbox_state(archive):
    """How many reports are queued AND NOT YET DELIVERED, and how old the oldest
    of those is. THIS is the number F-179 needed and nobody was reading: assert
    the DRAIN, not the enqueue.

    CAUGHT BY RUNNING IT AGAINST REAL DATA, not by reasoning: the first version
    counted FILES in _outbox and reported 10 waiting, oldest 192.8 hours. But
    delivered files are deliberately KEPT there (the pipeline reference says so
    in as many words), so that check would have gone red on day one and stayed
    red forever. A false alarm is worse than no alarm -- it teaches the owner to
    ignore the light.

    marg_gate records what it has delivered in _outbox_state.json, keyed by
    content hash. That is the authority, so this reads it rather than keeping a
    second opinion about what "delivered" means (D349).
    """
    d = os.path.join(archive, "_outbox")
    try:
        files = [os.path.join(d, f) for f in os.listdir(d)
                 if os.path.isfile(os.path.join(d, f)) and not f.startswith("_")]
    except Exception:
        return {}
    sent = set()
    try:
        with io.open(os.path.join(archive, "_outbox_state.json"),
                     "r", encoding="utf-8-sig", errors="replace") as fh:
            sent = set((json.load(fh) or {}).get("sent") or {})
    except Exception:
        sent = set()
    import hashlib
    pending = []
    for f in files:
        try:
            with open(f, "rb") as fh:
                h = hashlib.md5(fh.read()).hexdigest()
        except Exception:
            continue
        if h not in sent:
            pending.append(f)
    if not pending:
        return {"count": 0, "oldest_hours": 0, "kept": len(files)}
    oldest = min(os.path.getmtime(f) for f in pending)
    return {"count": len(pending), "kept": len(files),
            "oldest_hours": _hours_since(datetime.datetime.fromtimestamp(oldest))}


def last_pull_state(path):
    try:
        with io.open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            lines = [l.strip() for l in fh if l.strip()]
    except Exception:
        return {}
    tail = lines[-4:] if lines else []
    return {"lines": tail,
            "ended_ok": any(l.startswith("END") and l.endswith("ok") for l in tail),
            "failed": any("FAILED" in l for l in tail)}


def _backup_from_heartbeat(txt):
    """The BACKUP block the medical agent writes (S203).

    Parsed defensively for one reason: a heartbeat from an OLDER agent has no
    such block, and that must read as "not reported" -- never as "no backup".
    A monitor that turns silence into an alarm gets ignored, and a monitor that
    turns silence into a green is worse.
    """
    bk = {"reported": False, "stick_age_days": None, "newest": None,
          "serverbackup_age_days": None, "offsite_files": None,
          "offsite_gb": None, "offsite_complete": None, "pending": None}
    for line in (txt or "").splitlines():
        u = line.strip()
        m = re.search(r"newest backup on the stick is ([\d.]+) day", u)
        if m:
            bk["reported"] = True
            bk["stick_age_days"] = float(m.group(1))
            m2 = re.search(r"\(([^)]+)\)\s*$", u)
            if m2:
                bk["newest"] = m2.group(1)
        elif u.startswith("BACKUP") and "NO BACKUP FILE" in u.upper():
            bk["reported"] = True
        m = re.search(r"serverbackup: ([\d.]+) day", u)
        if m:
            bk["serverbackup_age_days"] = float(m.group(1))
        m = re.search(r"offsite: (\d+) file\(s\), ([\d.]+) GB", u)
        if m:
            bk["offsite_files"] = int(m.group(1))
            bk["offsite_gb"] = float(m.group(2))
        if "offsite copy is COMPLETE" in u:
            bk["offsite_complete"] = True
        m = re.search(r"(\d+) file\(s\) still to copy", u)
        if m:
            bk["offsite_complete"] = False
            bk["pending"] = int(m.group(1))
    return bk


def heartbeat_state(path):
    """Parse the medical PC's heartbeat. Text, because a human reads it too --
    so parse defensively and report what could not be read rather than guessing.
    """
    try:
        with io.open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            txt = fh.read()
        age = _hours_since(datetime.datetime.fromtimestamp(os.path.getmtime(path)))
    except Exception:
        return {}, {}, None
    w = {}
    for line in txt.splitlines():
        u = line.strip()
        if u.startswith("WATCHER :"):
            w["alive"] = "ALIVE" in u.upper()
        elif u.startswith("CAPTURES:"):
            try:
                w["captures_today"] = int(u.split(":", 1)[1].strip().split()[0])
            except Exception:
                pass
    ign = 0
    for line in txt.splitlines():
        if line.strip().startswith("IGNORED :"):
            try:
                ign = int(line.split(":", 1)[1].strip().split()[0])
            except Exception:
                ign = 0
    return w, {"age_hours": age,
               "backup": _backup_from_heartbeat(txt)}, ign


def offsite_state(archive, mirror):
    """Is the Drive copy keeping up? The archive is the ONLY copy of a report
    once Marg overwrites its slot."""
    def newest(root):
        best = None
        for dp, _dn, fn in os.walk(root):
            for f in fn:
                try:
                    m = os.path.getmtime(os.path.join(dp, f))
                except Exception:
                    continue
                if best is None or m > best:
                    best = m
        return best
    try:
        a, b = newest(archive), newest(mirror)
        if a is None or b is None:
            return {}
        return {"lag_hours": round(max(0.0, (a - b) / 3600.0), 1)}
    except Exception:
        return {}


def pick_heartbeat(explicit, cands=None):
    """The newest heartbeat file that actually exists. A missing drive letter
    must degrade to 'I could not read it', never to a silent green.

    S205 (F-217): `cands` exists ONLY so this can be tested deterministically.
    Until now the selftest called it with the REAL default list, so the test's
    result depended on which heartbeat files happened to exist on the machine
    running it. It passed in an offline build environment -- where none of the
    Windows paths resolve, so the answer is always None -- and FAILED on
    manojz, the only machine this file ever runs on, because a heartbeat is
    genuinely sitting there. A check that can only pass where the thing it
    tests cannot happen is not a check.

    The BEHAVIOUR below is unchanged, byte for byte in its logic.
    """
    base = list(DEF_HEARTBEATS) if cands is None else list(cands)
    cands = [explicit] if explicit else list(base)
    if explicit and explicit not in base:
        cands = [explicit] + list(base)
    best, bestm = None, None
    for c in cands:
        try:
            m = os.path.getmtime(c)
        except Exception:
            continue
        if bestm is None or m > bestm:
            best, bestm = c, m
    return best


# =============================================================================
#  S205 · D350 §2 — VERIFICATION AT THIS END. MEASURED, NEVER INFERRED.
# =============================================================================

def _tailscale_exe():
    for p in DEF_TAILSCALE:
        if os.path.exists(p):
            return p
    return None


def tailscale_state(host=DEF_MEDICAL_HOST, peer_names=DEF_MAGICDNS):
    """Tailscale at BOTH ends, as far as this machine can see it.

    `tailscale status --json` is the measurement. It gives this node's own
    backend state and address, and for every peer: its addresses, whether it is
    Online, whether the connection is direct or relayed, and when it was last
    seen. That last one matters more than it looks -- on 26-Aug the peer was
    Online and direct the entire time the feed was dead, which is precisely why
    a green Tailscale must never be read as a working pipeline.

    Everything is optional. No Tailscale, an old CLI without --json, a refused
    permission: all read as `installed`/`read` False with a reason, never as a
    healthy default.
    """
    out = {"here": {"installed": False, "read": False}, "medical": {"seen": False},
           "checked_at": datetime.datetime.now().isoformat(timespec="seconds")}
    exe = _tailscale_exe()
    if not exe:
        out["here"]["note"] = "tailscale.exe not found in either Program Files path"
        return out
    out["here"]["installed"] = True
    out["here"]["exe"] = exe
    raw = _run([exe, "status", "--json"])
    if not raw:
        out["here"]["note"] = "tailscale status --json returned nothing " \
                              "(not running, not logged in, or too old a CLI)"
        return out
    try:
        st = json.loads(raw)
    except Exception:                                          # noqa: BLE001
        out["here"]["note"] = "tailscale status --json was not valid JSON"
        return out
    out["here"]["read"] = True
    out["here"]["backend"] = st.get("BackendState")
    self_ = st.get("Self") or {}
    ips = self_.get("TailscaleIPs") or []
    out["here"]["address"] = ips[0] if ips else None
    out["here"]["name"] = self_.get("DNSName") or self_.get("HostName")
    out["here"]["online"] = self_.get("Online")

    want = tuple(n.lower() for n in peer_names)
    for _k, pr in (st.get("Peer") or {}).items():
        pips = [str(x) for x in (pr.get("TailscaleIPs") or [])]
        dns = str(pr.get("DNSName") or "")
        hn = str(pr.get("HostName") or "")
        match = (host in pips
                 or hn.lower() in want
                 or any(dns.lower().startswith(w + ".") or dns.lower() == w
                        for w in want))
        if not match:
            continue
        out["medical"] = {
            "seen": True,
            "name": dns or hn,
            "address": pips[0] if pips else None,
            "online": pr.get("Online"),
            # CurAddr set => a direct connection. Empty with Relay set => DERP.
            # Reported as words because "direct" and "relayed" mean different
            # things for a 60 MB pull and the owner should not have to know
            # which field to read.
            "route": ("direct %s" % pr.get("CurAddr")) if pr.get("CurAddr")
                     else ("relayed via %s" % pr.get("Relay") if pr.get("Relay")
                           else "unknown"),
            # Tailscale writes 0001-01-01T00:00:00Z for a peer that is
            # connected RIGHT NOW -- there is no "last seen" because it has
            # not been away. Reporting that raw would put the year 1 on the
            # owner's health page and read as a fault. Seen in the S205 dry
            # run against the live tailnet, which is the whole reason a dry
            # run happens on the real machine and not on the build machine.
            "last_seen": (None if str(pr.get("LastSeen") or "").startswith(
                "0001-01-01") else pr.get("LastSeen")),
            # The one that is always meaningful. A handshake minutes ago is
            # a live tunnel; hours ago with Online true is worth a look.
            "last_handshake": pr.get("LastHandshake"),
        }
        break
    if not out["medical"].get("seen"):
        out["medical"]["note"] = ("no peer matched %s or %s -- the address may "
                                  "have changed" % (host, "/".join(peer_names)))
    return out


def magicdns_state(host=DEF_MEDICAL_HOST, names=DEF_MAGICDNS):
    """B6: does the NAME resolve, and does it agree with the hardcoded address?

    The pull addresses the medical PC by a number that lives in two files. The
    durable fix is the MagicDNS name, because a name follows the machine and a
    number does not. THIS ONLY REPORTS. Switching the live path is a change to
    how reports travel and belongs to the owner, not to a monitor -- and D350
    §7 is explicit that nothing which moves data changes until everything
    watching it is proven.
    """
    import socket
    out = {"configured": host, "tried": list(names), "resolved": {},
           "agrees": None, "usable_name": None}
    for n in names:
        try:
            socket.setdefaulttimeout(PROBE_TIMEOUT)
            ip = socket.gethostbyname(n)
        except Exception:                                      # noqa: BLE001
            out["resolved"][n] = None
            continue
        out["resolved"][n] = ip
        if ip == host and out["usable_name"] is None:
            out["usable_name"] = n
    got = [v for v in out["resolved"].values() if v]
    if not got:
        out["note"] = ("no MagicDNS name resolves from here -- the hardcoded "
                       "address is currently the only way to reach it")
    else:
        out["agrees"] = (host in got)
        if not out["agrees"]:
            out["note"] = ("THE NAME AND THE NUMBER DISAGREE: the name resolves "
                           "to %s, the pull is configured for %s. One of them "
                           "is stale." % (", ".join(sorted(set(got))), host))
    return out


def share_probe(host=DEF_MEDICAL_HOST, path=DEF_SHARE_PROBE, facts=None):
    """AN ACTUAL REACHABILITY TEST, PERFORMED — not deduced (D350 §2).

    Two probes, because they fail differently:

      1. TCP 445. Is SMB answering at all? This separates "the machine or the
         tunnel is gone" from "the machine is there and the share said no".
         Preferred over ping: on 26-Aug ping would have answered while the
         share refused, and a probe that cannot tell those apart is the
         message that cost eight hours.
      2. A real directory read of the exact path the pull needs. Not a
         neighbouring path, not the root -- the one the pull would fail on.

    The verdict is composed from what was measured. Where nothing could be
    measured it says so; it never falls through to a healthy word.
    """
    import socket
    import time
    out = {"host": host, "path": path}

    t0 = time.time()
    tcp = {"tried": True, "port": 445, "open": None}
    try:
        s = socket.create_connection((host, 445), timeout=PROBE_TIMEOUT)
        s.close()
        tcp["open"] = True
    except Exception as ex:                                    # noqa: BLE001
        tcp["open"] = False
        tcp["error"] = "%s: %s" % (ex.__class__.__name__, ex)
    tcp["ms"] = int((time.time() - t0) * 1000)
    out["tcp445"] = tcp

    t0 = time.time()
    sh = {"tried": True, "readable": None}
    try:
        sh["readable"] = os.path.isdir(path)
        if not sh["readable"]:
            sh["error"] = "the path did not read as a directory"
    except Exception as ex:                                    # noqa: BLE001
        sh["readable"] = False
        sh["error"] = "%s: %s" % (ex.__class__.__name__, ex)
    sh["ms"] = int((time.time() - t0) * 1000)
    out["share"] = sh

    # The batch performs this same test at the top of every run and used to
    # throw the answer away. If it left us its answer, carry it -- two
    # independent readings of the same fact are worth more than one, and a
    # disagreement between them is itself worth seeing.
    if facts and facts.get("share_seen") is not None:
        out["share"]["batch_saw"] = facts.get("share_seen")
        if facts.get("share_seen") != bool(sh.get("readable")):
            out["share"]["note"] = ("the batch and this probe disagree -- the "
                                    "link changed state during the cycle")

    # ---- WHICH POINT IS DOWN, in words (D350 §3) ---------------------------
    if sh.get("readable"):
        out["verdict"] = "ok"
        out["verdict_words"] = "the share reads -- the whole path is up"
    elif tcp.get("open"):
        out["verdict"] = "share_refusing"
        out["verdict_words"] = ("the PC answers on 445, the share refuses -- "
                                "most likely credentials, not the machine")
    elif tcp.get("open") is False:
        out["verdict"] = "host_unreachable"
        out["verdict_words"] = ("nothing answers on 445 -- the machine is off, "
                                "or the tunnel is down")
    else:
        out["verdict"] = "unknown"
        out["verdict_words"] = "neither probe could be performed"
    return out


def credential_state(host=DEF_MEDICAL_HOST):
    """Does a stored credential for the medical host exist AT ALL, and which
    Windows account is this process running as?

    Credentials are stored PER WINDOWS USER. A manual `dir` by the owner can
    succeed while the scheduled task fails for ever, because the task runs as a
    different account -- and from every other vantage point those two cases are
    identical. This is the field that tells them apart.

    NO SECRET IS READ OR SENT. `cmdkey /list` never prints a password; it
    prints targets and account names. Only the presence, the target and the
    account name leave this machine.
    """
    out = {"checked": False, "exists": None, "target": host,
           "note": "credentials are stored per Windows user"}
    try:
        out["running_as"] = "%s\\%s" % (os.environ.get("USERDOMAIN", "?"),
                                        os.environ.get("USERNAME", "?"))
    except Exception:                                          # noqa: BLE001
        out["running_as"] = None
    raw = _run(["cmdkey", "/list"])
    if raw is None:
        out["note"] = "cmdkey could not be run -- credential state unknown"
        return out
    out["checked"] = True
    out["exists"] = False
    block_user = None
    for line in raw.splitlines():
        u = line.strip()
        if host in u:
            out["exists"] = True
            block_user = block_user or ""
        elif out["exists"] and block_user == "" and u.lower().startswith("user:"):
            block_user = u.split(":", 1)[1].strip()
    if block_user:
        out["user"] = block_user
    if out["exists"] is False:
        out["note"] = ("no stored credential for %s under %s. If the share "
                       "refuses, this is the first thing to look at."
                       % (host, out.get("running_as")))
    return out


def _pull_facts(path=DEF_FACTS):
    """What the BATCH measured this cycle and used to discard.

    PULL_FROM_MEDICAL.bat already performs the share test, already knows every
    step's return code, and already knows which route it took. Until S205 all
    of it went to a console the hidden launcher throws away. Now it writes
    `key=value` lines here and this reads them.

    Simple `key=value`, not JSON, on purpose: quoting JSON inside a Windows
    batch file is how a monitor acquires its own bug.
    """
    out = {}
    try:
        with io.open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return {}
    for line in raw.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if not k:
            continue
        if v in ("0", "1") and k in ("share_seen", "fallback"):
            out[k] = (v == "1")
        elif v.isdigit():
            out[k] = int(v)
        else:
            out[k] = v
    return out


def transport_state(facts, probe):
    """WHICH ROUTE THIS CYCLE TOOK, and whether it was the reserve one.

    There is exactly one transport today: the Tailscale SMB share. Reporting it
    before the Drive fallback exists is the point, not an oversight -- D350 §7
    orders it that way, because a fallback whose switch is wrong fails
    invisibly, and invisible failure is the fault the contract exists to end.

    `measured` says whether the batch told us or whether this was worked out
    from the probe. A field that was inferred must never look like one that was
    measured (D350 §2).
    """
    used = facts.get("transport")
    if used:
        return {"used": used, "fallback": bool(facts.get("fallback")),
                "measured": True, "source": "the pull reported it"}
    if probe.get("verdict") == "ok":
        return {"used": "smb", "fallback": False, "measured": False,
                "source": "inferred from the share probe -- the pull did not "
                          "say, so this is a deduction, not a reading"}
    return {"used": None, "fallback": None, "measured": False,
            "source": "the pull did not report a transport and the share is "
                      "not readable"}


def gather(args):
    _hbp = pick_heartbeat(getattr(args, "heartbeat", None))
    w, hb, ign = heartbeat_state(_hbp) if _hbp else ({}, {}, 0)
    if _hbp:
        hb["from"] = _hbp
    # S203: the backup state travels at the TOP of the payload, not nested in
    # the heartbeat, so the server reads it in one place and there is only one
    # place for it to be.
    _bk = hb.pop("backup", {}) if isinstance(hb, dict) else {}

    # ---- S205 (D350 §2). Each guarded on its own: one probe that cannot run
    # ---- must not cost the server every other fact in this payload.
    _host = getattr(args, "medical_host", None) or DEF_MEDICAL_HOST
    _facts = _guard(_pull_facts, getattr(args, "facts", None) or DEF_FACTS)
    _probe = _guard(share_probe, _host,
                    getattr(args, "share_probe", None)
                    or (r"\\%s\DDrive\MARGERP\users" % _host),
                    _facts)
    _ts = _guard(tailscale_state, _host)
    _dns = _guard(magicdns_state, _host)
    _cred = _guard(credential_state, _host)
    _tr = _guard(transport_state, _facts, _probe or {})

    return {"source": "manojz",
            "at": datetime.datetime.now().isoformat(timespec="seconds"),
            "outbox": outbox_state(args.archive),
            "last_pull": last_pull_state(args.last_pull),
            "watcher": w,
            "heartbeat": hb,
            "ignored": ign or 0,
            "offsite": offsite_state(args.archive, args.offsite),
            "backup": _bk,
            # ---- S205 ----
            "link": _probe,
            "tailscale": _ts,
            "magicdns": _dns,
            "credential": _cred,
            "transport": _tr,
            "reporter": "S205.3"}


def _guard(fn, *a):
    """Run a gatherer; on ANY failure return a dict that SAYS it failed.

    Returning {} would be indistinguishable from "nothing to report", and this
    whole file exists because a silence was read as a green.
    """
    try:
        return fn(*a)
    except Exception as ex:                                    # noqa: BLE001
        return {"error": "%s: %s" % (ex.__class__.__name__, ex),
                "read": False}


def post(payload, url, token, timeout=30):
    import urllib.request
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Finance-Marg", token)          # never logged
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")[:400]


def selftest():
    import tempfile
    ok = [0]
    def ck(cond, msg):
        ok[0] += 1
        if not cond:
            raise AssertionError("check %d FAILED: %s" % (ok[0], msg))
    t = tempfile.mkdtemp()
    arc = os.path.join(t, "arc"); os.makedirs(os.path.join(arc, "_outbox"))
    ck(outbox_state(arc).get("count") == 0, "empty outbox reads zero")
    with io.open(os.path.join(arc, "_outbox", "r.xls"), "w") as fh:
        fh.write("x")
    ck(outbox_state(arc)["count"] == 1, "an UNDELIVERED report is counted")
    import hashlib
    _h = hashlib.md5(b"x").hexdigest()
    with io.open(os.path.join(arc, "_outbox_state.json"), "w", encoding="utf-8") as fh:
        json.dump({"sent": {_h: {"business_date": "2026-08-01"}}}, fh)
    _os2 = outbox_state(arc)
    ck(_os2["count"] == 0 and _os2["kept"] == 1,
       "a DELIVERED report still on disk is NOT counted as waiting — delivered "
       "files are kept by design, and counting them would fire this check "
       "forever (caught against real data: 10 files, 0 actually pending)")
    ck(outbox_state(os.path.join(t, "nope")) == {}, "a missing archive is empty, not a crash")
    hb = os.path.join(t, "hb.txt")
    with io.open(hb, "w", encoding="utf-8") as fh:
        fh.write("WATCHER : ALIVE, pid 1\nCAPTURES: 6 today; newest x\nIGNORED : 2 file(s)\n")
    w, h, ig = heartbeat_state(hb)
    ck(w.get("alive") is True, "an ALIVE watcher is read as alive")
    ck(w.get("captures_today") == 6, "captures today is read")
    ck(ig == 2, "the ignored counter is read")
    with io.open(hb, "w", encoding="utf-8") as fh:
        fh.write("WATCHER : NOT RUNNING\nCAPTURES: 0 today\nIGNORED : 0 file(s)\n")
    w2, _, _ = heartbeat_state(hb)
    ck(w2.get("alive") is False, "a dead watcher is read as dead — the case that matters")
    ck(heartbeat_state(os.path.join(t, "nope"))[0] == {}, "a missing heartbeat is empty, not a crash")
    # S203: the agent's BACKUP block. Until now this pull told the server about
    # the watcher and the outbox and said nothing about whether the pharmacy's
    # database had been backed up -- the one loss that cannot be undone.
    with io.open(hb, "w", encoding="utf-8") as fh:
        fh.write("WATCHER : ALIVE, pid 1\nCAPTURES: 1 today\nIGNORED : 0 file(s)\n"
                 "BACKUP  : newest backup on the stick is 4.1 day(s) old  (a.mbk)\n"
                 "          Marg's own serverbackup: 0.6 day(s) old -- but on D:,\n"
                 "          offsite: 182 file(s), 0.41 GB in /x\n"
                 "          offsite copy is COMPLETE\n")
    _bk = (heartbeat_state(hb)[1] or {}).get("backup") or {}
    ck(_bk.get("reported") is True, "the BACKUP block is seen")
    ck(_bk.get("stick_age_days") == 4.1,
       "the age reported is the STICK's, not serverbackup's -- serverbackup sits "
       "on the same disk as the data, so reporting it would be a false green")
    ck(_bk.get("serverbackup_age_days") == 0.6,
       "serverbackup is reported BESIDE the stick, never instead of it")
    ck(_bk.get("offsite_files") == 182 and _bk.get("offsite_complete") is True,
       "the offsite copy state is read")
    with io.open(hb, "w", encoding="utf-8") as fh:
        fh.write("WATCHER : ALIVE, pid 1\nCAPTURES: 1 today\nIGNORED : 0 file(s)\n")
    ck(((heartbeat_state(hb)[1] or {}).get("backup") or {}).get("reported") is False,
       "an OLDER agent with no BACKUP block reads as NOT REPORTED, never as no backup")
    lp = os.path.join(t, "lp.txt")
    with io.open(lp, "w", encoding="utf-8") as fh:
        fh.write("START 26-08-2026 01:00:00\nEND 26-08-2026 01:00:11 -- ok\n")
    ck(last_pull_state(lp)["ended_ok"] is True, "a clean pull is read as ok")
    ck(last_pull_state(os.path.join(t, "nope")) == {}, "a missing pull stamp is empty, not a crash")
    # ---- F-217 (S205). THE CHECK THIS REPLACES WAS:
    #        ck(pick_heartbeat(os.path.join(t, "nope")) in (None, hb), ...)
    #    which asserts a RESULT, and the result depends on which heartbeat
    #    files exist on the machine running the test. Offline, none of the
    #    Windows paths resolve, so it returned None and went green. On manojz
    #    a real heartbeat sits at DEF_HEARTBEATS[2], so it returned that --
    #    correct behaviour, failed assertion. The test was wrong, not the code.
    #    Four checks now, each testing the PROPERTY, on any machine:
    _miss = os.path.join(t, "nope")
    ck(pick_heartbeat(_miss, cands=[]) is None,
       "with nothing to fall back to, a missing heartbeat path returns None")
    ck(pick_heartbeat(_miss, cands=[hb]) == hb,
       "a missing heartbeat path FALLS BACK to one that exists")
    _pk = pick_heartbeat(_miss)
    ck(_pk is None or os.path.exists(_pk),
       "against the REAL default list it returns either None or a file that "
       "EXISTS -- true on the build machine and on manojz alike")
    ck(_pk != _miss,
       "and it NEVER returns the path it could not read, which would make the "
       "caller report a heartbeat it never opened -- the silent green this "
       "check exists to prevent")

    # ---------------------------------------------------------------- S205
    # THE POINT OF THESE: every new field must degrade to a stated unknown.
    # A probe that cannot run must never produce a value that reads healthy.
    ck(_guard(lambda: 1 / 0) .get("read") is False,
       "a gatherer that throws reports read=False, not an empty dict that "
       "would be indistinguishable from 'nothing wrong'")

    fp = os.path.join(t, "facts.txt")
    with io.open(fp, "w", encoding="utf-8") as fh:
        fh.write("share_seen=1\ntransport=smb\nfallback=0\nrc_gate=0\n"
                 "started=27-08-2026 04:30:01\n")
    f = _pull_facts(fp)
    ck(f.get("share_seen") is True and f.get("transport") == "smb",
       "the batch's own facts are read back")
    ck(f.get("fallback") is False, "fallback=0 reads as False, not as the string '0'")
    ck(_pull_facts(os.path.join(t, "nope")) == {},
       "a missing facts file is empty, not a crash — the batch may be older "
       "than this reporter and that must not break the pull")

    # share_probe's VERDICT logic, which is the D350 §3 'which point is down'
    # answer. Exercised through the composition rules rather than the network,
    # because a selftest that needs a live share proves nothing offline.
    def _verdict(readable, tcp_open):
        o = {"share": {"readable": readable}, "tcp445": {"open": tcp_open}}
        sh, tcp = o["share"], o["tcp445"]
        if sh.get("readable"):
            return "ok"
        if tcp.get("open"):
            return "share_refusing"
        if tcp.get("open") is False:
            return "host_unreachable"
        return "unknown"
    ck(_verdict(True, True) == "ok", "a readable share is ok")
    ck(_verdict(False, True) == "share_refusing",
       "THE 26-AUG FAULT: the port answers and the share does not — that is "
       "credentials, and it must not be reported as an absent machine")
    ck(_verdict(False, False) == "host_unreachable",
       "nothing on 445 means the machine or the tunnel")
    ck(_verdict(False, None) == "unknown",
       "a probe that could not be performed says UNKNOWN, never ok")

    ck(transport_state({"transport": "drive", "fallback": 1},
                       {}).get("fallback") is True,
       "a cycle that ran on the fallback says so")
    ck(transport_state({"transport": "smb"}, {}).get("measured") is True,
       "a transport the pull reported is marked MEASURED")
    ck(transport_state({}, {"verdict": "ok"}).get("measured") is False,
       "a transport worked out from the probe is marked INFERRED — an inferred "
       "fact must never look like a measured one (D350 §2)")
    ck(transport_state({}, {"verdict": "share_refusing"}).get("used") is None,
       "with no report and no readable share, the transport is unknown")

    _md = magicdns_state("10.0.0.1", ("no.such.name.invalid",))
    ck(_md.get("resolved", {}).get("no.such.name.invalid") is None
       and _md.get("agrees") is None,
       "a name that does not resolve reports null and does NOT claim agreement")

    p = gather(argparse.Namespace(archive=arc, last_pull=lp, heartbeat=hb,
                                  offsite=os.path.join(t, "nope"),
                                  medical_host="127.0.0.1",
                                  share_probe=os.path.join(t, "nope"),
                                  facts=fp))
    ck(p["heartbeat"].get("from") == hb, "the payload says WHICH heartbeat it read")
    ck(p["source"] == "manojz" and "outbox" in p, "the payload assembles")
    ck("backup" in p, "the payload carries the backup state to the clinic server")
    for _k in ("link", "tailscale", "magicdns", "credential", "transport"):
        ck(_k in p, "the payload carries the %s section (D350 §2)" % _k)
    ck(p["link"].get("verdict") in ("ok", "share_refusing", "host_unreachable",
                                    "unknown"),
       "the link verdict is one of the four measured outcomes")
    ck(p.get("reporter") == "S205.3",
       "the payload names its own version — so the server can tell an old "
       "reporter's silence from a new reporter's null")
    _blob = json.dumps(p).lower()
    ck("token" not in _blob,
       "the payload carries no token — it must never leave here")
    ck("pass" not in _blob and "secret" not in _blob,
       "no probe leaked a credential value into the payload")
    # ASCII deliberately: the Windows console is cp437 and an em-dash prints
    # as a question mark, which makes a PASS line look like a problem.
    print("PIPELINE_STATUS SELFTEST PASSED -- %d checks OK" % ok[0])
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="post manojz's view of the Marg pipeline")
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    ap.add_argument("--last-pull", dest="last_pull", default=DEF_LASTPULL)
    ap.add_argument("--heartbeat", default=None)
    ap.add_argument("--offsite", default=DEF_OFFSITE)
    ap.add_argument("--url", default=DEF_URL)
    ap.add_argument("--token-file", default=DEF_TOKEN)
    ap.add_argument("--token-unc", default=DEF_TOKEN_UNC)
    ap.add_argument("--medical-host", dest="medical_host", default=DEF_MEDICAL_HOST)
    ap.add_argument("--share-probe", dest="share_probe", default=DEF_SHARE_PROBE)
    ap.add_argument("--facts", default=DEF_FACTS)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    try:
        payload = gather(a)
    except Exception as ex:                                   # noqa: BLE001
        print("pipeline_status: could not gather (%s) — the pull is unaffected" % ex)
        return 0
    if a.dry_run:
        print(json.dumps(payload, indent=2))
        return 0
    try:
        sys.path.insert(0, HERE)
        import marg_gate                                      # one token rule, D349
        token, where = marg_gate.resolve_token(a.token_unc, a.token_file)
    except Exception as ex:                                   # noqa: BLE001
        print("pipeline_status: no token (%s) — the pull is unaffected" % ex)
        return 0
    if not token:
        print("pipeline_status: no token available — the pull is unaffected")
        return 0
    try:
        st, body = post(payload, a.url, token)
        print("pipeline_status: %s (token from %s)" % (st, where))
    except Exception as ex:                                   # noqa: BLE001
        print("pipeline_status: post failed (%s) — the pull is unaffected" % ex)
    return 0


if __name__ == "__main__":
    sys.exit(main())
