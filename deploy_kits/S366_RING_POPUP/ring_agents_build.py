#!/usr/bin/env python3
"""
ring_agents_build.py -- kit S366_RING_POPUP (session 279, 22-Sep-2026)
Builds /root/portal/ring_agents.json -- which Clinic-app login owns each staff phone MyOperator rings.

  default        ask MyOperator "Get Users" (token MYOP_LOGS_TOKEN from /root/wa/.env, never printed), match each
                 user's NAME to a portal login with the table below, keep the phone MyOperator holds for them.
                 Prints names and whether a phone was found -- NEVER the numbers (F-185 applies to the terminal too).
  --set LOGIN PHONE   add or change one entry by hand (for a phone MyOperator does not list, e.g. the reception
                 mobile). The number goes into the 0600 file only.
  --show         list logins and names in the file (no numbers).
Existing entries are kept; the API adds or refreshes, never deletes.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

OUT = os.environ.get("RING_AGENTS_FILE", "/root/portal/ring_agents.json")
WA_ENV = os.environ.get("WA_ENV", "/root/wa/.env")
HOST = "https://developers.myoperator.co"

# MyOperator user name (as the Tracker's WebApp.gs AGENT_NAME_BY_EXT spells them) -> Clinic-app login.
# First token of the name decides, so "Shavez Ahmed" and "Shavez" both land on shavez.
NAME_TO_LOGIN = {
    "shavez": "shavez", "shivani": "shivani", "alisha": "alisha", "darpan": "darpan",
    "bhati": "bhati", "manoj bhati": "bhati",
    "dr manoj": "manoj", "manoj agarwal": "manoj", "dr manoj agarwal": "manoj",
}
PHONE_KEYS = ("phone", "mobile", "phone_number", "mobile_number", "number", "contact", "contact_number", "msisdn")


def _load_env(path):
    out = {}
    try:
        for line in open(path, "r", encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def m10(raw):
    d = re.sub(r"\D+", "", str(raw or ""))
    if len(d) > 10:
        d = d[2:] if (d.startswith("91") and len(d) == 12) else (d[1:] if (d.startswith("0") and len(d) == 11) else d[-10:])
    return d if len(d) == 10 else ""


def _read():
    try:
        d = json.load(open(OUT, "r", encoding="utf-8"))
        return d if isinstance(d, dict) and isinstance(d.get("agents"), dict) else {"agents": {}}
    except Exception:
        return {"agents": {}}


def _write(d):
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    os.chmod(tmp, 0o600)
    os.replace(tmp, OUT)


def login_for(name):
    n = re.sub(r"[^a-z ]+", " ", str(name or "").lower()).strip()
    n = re.sub(r"\s+", " ", n)
    if n in NAME_TO_LOGIN:
        return NAME_TO_LOGIN[n]
    toks = n.split(" ")
    if len(toks) >= 2 and toks[0] == "dr" and toks[1] == "manoj":
        return "manoj"
    if toks and toks[0] in NAME_TO_LOGIN:
        return NAME_TO_LOGIN[toks[0]]
    if len(toks) >= 2 and toks[1] in ("bhati",):
        return "bhati"
    return ""


def _phone_of(u):
    for k in PHONE_KEYS:
        v = u.get(k)
        if isinstance(v, (str, int)) and m10(v):
            return m10(v)
    for v in u.values():                          # one level down (e.g. {"contact": {"mobile": ...}})
        if isinstance(v, dict):
            for k in PHONE_KEYS:
                if m10(v.get(k)):
                    return m10(v.get(k))
    return ""


def fetch_users(token):
    url = "%s/search/user?token=%s&_all=1" % (HOST, urllib.parse.quote(token, safe=""))
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    rows = data.get("data") if isinstance(data, dict) else data
    if isinstance(rows, dict):
        rows = rows.get("users") or rows.get("data") or list(rows.values())
    return [r for r in (rows or []) if isinstance(r, dict)]


def main(argv):
    d = _read()
    if "--show" in argv:
        for ph, a in sorted(d["agents"].items(), key=lambda x: x[1].get("user", "")):
            print("  %-10s %s" % (a.get("user", "?"), a.get("name", "")))
        print("%d phone(s) linked" % len(d["agents"]))
        return 0
    if "--set" in argv:
        i = argv.index("--set")
        login, phone = argv[i + 1], m10(argv[i + 2])
        if not phone:
            print("!! that is not a 10-digit mobile"); return 1
        d["agents"][phone] = {"user": login, "name": d["agents"].get(phone, {}).get("name") or login}
        _write(d)
        print("linked: %s (one phone)" % login)
        return 0
    token = (os.environ.get("MYOP_LOGS_TOKEN") or _load_env(WA_ENV).get("MYOP_LOGS_TOKEN") or "").strip()
    if not token:
        print("!! MYOP_LOGS_TOKEN not found in %s -- the map stays as it is (%d linked)" % (WA_ENV, len(d["agents"])))
        return 2
    try:
        users = fetch_users(token)
    except Exception as e:  # noqa: BLE001
        print("!! MyOperator Get Users failed: %s -- the map stays as it is (%d linked)" % (type(e).__name__, len(d["agents"])))
        return 2
    linked = unlinked = nophone = 0
    for u in users:
        name = str(u.get("name") or u.get("user_name") or "").strip()
        login = login_for(name)
        phone = _phone_of(u)
        if not login:
            print("  %-26s -> not a Clinic-app login (skipped)" % (name[:26] or "?")); unlinked += 1; continue
        if not phone:
            print("  %-26s -> %-8s NO phone in MyOperator's record" % (name[:26], login)); nophone += 1; continue
        d["agents"][phone] = {"user": login, "name": name}
        print("  %-26s -> %-8s phone linked" % (name[:26], login)); linked += 1
    _write(d)
    print("ring_agents.json: %d phone(s) linked in all · this run: %d linked, %d without a phone, %d not a login" % (len(d["agents"]), linked, nophone, unlinked))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
