#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s943.py -- kit S943: builds owner_console.py (TO) from the live bytes (FROM cf7f8b09, S911's) by two exact anchors, and
freshness_legs.json (TO) from the live bytes (FROM f2ade687, S897's) by one added leg. Nothing else moves.
    python3 make_s943.py <owner_console.py FROM> <owner_console.py TO> <freshness_legs.json FROM> <freshness_legs.json TO>
"""
import ast
import hashlib
import json
import sys

OC_FROM = "cf7f8b09122306a893b229a4158449a1"
LEGS_FROM = "f2ade68779b94c6b99cf3c3b0e00e7d6"

A1 = "def sec_system(con, cx):\n"
NEW1 = '''SREC = _env("CONSOLE_SERVER_RECORD", os.path.join(FIN, "server_record", "LATEST.json"))   # S943 (A1): the nightly server record


def _s943_server_lines(cx):
    """S943 (roadmap S510 A1, plan L1): one line from the nightly server record -- disk, RAM, load, when it was taken -- and its
    warnings under it (disk 80 %, RAM under 1 GB, load at or above the CPUs). Read only; the record is server_record.py's."""
    if not os.path.exists(SREC):
        return [L("n", "Server record: not written yet -- the first comes at 02:50 tonight (disk, RAM, load, the biggest processes)")]
    with open(SREC, encoding="utf-8") as fh:
        r = json.load(fh)
    when_s = str(r.get("when_iso") or "")
    try:
        hours = (cx["now"].replace(tzinfo=None) - dt.datetime.fromisoformat(when_s[:19])).total_seconds() / 3600.0
    except (ValueError, TypeError):
        hours = None
    if hours is None or hours > 30:
        return [L("w", "The server record has not been written since %s -- server_record.py (02:50) did not run" % (when(when_s, cx["today"]) or "never"))]
    disks = r.get("disks") or []
    root = next((d for d in disks if d.get("mount") == "/"), disks[0] if disks else None)
    ram = (r.get("ram") or {}).get("available_b")
    load = (r.get("load") or {}).get("l1")
    parts = []
    if root:
        parts.append("disk %s%% used (%.0f GB free)" % (root.get("pct"), (root.get("avail_b") or 0) / 1e9))
    if ram is not None:
        parts.append("RAM %.1f GB available" % (ram / 1e9))
    if load is not None:
        parts.append("load %.2f" % load)
    warn = [str(w) for w in (r.get("warn") or [])]
    procs = ", ".join(str(p.get("comm") or "?") for p in (r.get("procs") or [])[:5])
    out = [L("w" if warn else "g", "Server: %s -- recorded %s" % (" · ".join(parts) or "no figures", when(when_s, cx["today"])),
             why=("the five biggest processes: %s" % procs) if procs else None)]
    for w in warn[:4]:
        out.append(L("w", w, sub=True))
    return out


'''
A2 = '''    piece(lines, "The reception PC's heartbeat", beat)\n'''
NEW2 = A2 + '''    piece(lines, "The server record", lambda: _s943_server_lines(cx))     # S943 (A1): one health line from the nightly record\n'''

LEG = {"name": "server record", "group": "Watchdog", "kind": "file_mtime", "target": "/root/finance/server_record/LATEST.json",
       "max_age_h": 26,
       "note": "S943 (roadmap A1, plan L1) · server_record.py nightly 02:50 · disk by folder, RAM, load, the five biggest processes, 90 days kept · red when a night was missed"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    oc_from, oc_to, lg_from, lg_to = sys.argv[1:5]
    raw = open(oc_from, "rb").read()
    if md5(raw) != OC_FROM:
        sys.exit("owner_console.py FROM is %s, not %s (F-472: read the live bytes first)" % (md5(raw)[:8], OC_FROM[:8]))
    t = raw.decode("utf-8")
    for a in (A1, A2):
        if t.count(a) != 1:
            sys.exit("anchor not exactly once: %r" % a[:50])
    if "_s943_" in t:
        sys.exit("already carries S943")
    t = t.replace(A1, NEW1 + A1).replace(A2, NEW2)
    ast.parse(t)
    out = t.encode("utf-8")
    open(oc_to, "wb").write(out)
    print("owner_console.py TO %s (%d bytes)" % (md5(out), len(out)))
    rawl = open(lg_from, "rb").read()
    if md5(rawl) != LEGS_FROM:
        sys.exit("freshness_legs.json FROM is %s, not %s" % (md5(rawl)[:8], LEGS_FROM[:8]))
    d = json.loads(rawl.decode("utf-8"))
    if any(l.get("name") == LEG["name"] for l in d["legs"]):
        sys.exit("the leg is already there")
    d["legs"].append(LEG)
    outl = json.dumps(d, indent=1, ensure_ascii=False).encode("utf-8")   # the live file ends without a newline
    # the file as it stands: check its own formatting so the diff is one leg, not a re-indent
    back = json.loads(rawl.decode("utf-8"))
    back["legs"] = d["legs"][:-1]
    if json.dumps(back, indent=1, ensure_ascii=False).encode("utf-8") != rawl:
        print("note: the live legs file is not in this exact formatting -- the TO re-serialises it; every leg kept, one added")
    open(lg_to, "wb").write(outl)
    print("freshness_legs.json TO %s (%d legs)" % (md5(outl), len(d["legs"])))


if __name__ == "__main__":
    main()
