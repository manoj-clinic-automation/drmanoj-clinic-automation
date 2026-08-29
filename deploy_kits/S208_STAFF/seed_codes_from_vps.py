#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""seed_codes_from_vps.py -- load every employee code ever used onto the register.

RUN THIS ONCE, ON THE VPS, BEFORE ANYBODY ELSE IS ENROLLED.

    /root/wa/venv/bin/python3 seed_codes_from_vps.py --dry
    /root/wa/venv/bin/python3 seed_codes_from_vps.py

WHY IT READS punches.csv AND NOT JUST THE ROSTER
    The roster only holds people who are still here. punches.csv is append-only
    and keyed on (user_id, datetime), so it is the ONLY place a departed
    person's code survives -- and those are exactly the codes that must never
    come back. A register seeded from the roster alone would look complete and
    would still hand out a leaver's number.

    Codes found only in punches get the name "(left -- name not recorded)" and
    are marked retired. We cannot recover who they were, and we do not need to:
    what matters is that the number is spoken for, permanently.

Reads. Never writes to punches.csv or staff_master.csv.
"""
import argparse
import csv
import io
import json
import os
import sys
import urllib.request

PUNCHES = os.environ.get("ATT_PUNCH_CSV", "/root/punches.csv")
MASTER = os.environ.get("ATT_STAFF_MASTER", "/root/staff_master.csv")
API = os.environ.get("JOINER_API", "http://127.0.0.1:8000/joiner/api/seed_codes")


def codes_from_punches(path):
    """{code} -- every user_id that has ever punched."""
    out = set()
    if not os.path.exists(path):
        return out, "not found"
    with io.open(path, encoding="utf-8", errors="ignore") as fh:
        for i, line in enumerate(fh):
            if i == 0 and line.startswith("user_id"):
                continue
            head = line.split(",", 1)[0].strip()
            if head.isdigit():
                out.add(int(head))
    return out, "ok"


def codes_from_master(path):
    """{code: name} -- the people still on the roster."""
    out = {}
    if not os.path.exists(path):
        return out, "not found"
    with io.open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            c = str(r.get("user_id", "")).strip()
            if c.isdigit():
                out[int(c)] = (r.get("name") or "").strip() or "(name blank)"
    return out, "ok"


def main():
    ap = argparse.ArgumentParser(description="seed the employee-code register")
    ap.add_argument("--dry", action="store_true", help="show what would be sent")
    ap.add_argument("--punches", default=PUNCHES)
    ap.add_argument("--master", default=MASTER)
    ap.add_argument("--api", default=API)
    a = ap.parse_args()

    punched, p_ok = codes_from_punches(a.punches)
    roster, m_ok = codes_from_master(a.master)
    print("punches.csv     : %-9s %d distinct codes" % (p_ok, len(punched)))
    print("staff_master.csv: %-9s %d people" % (m_ok, len(roster)))
    if p_ok != "ok" and m_ok != "ok":
        print("\nNeither file is readable. Nothing to seed, and NOT a code failure --")
        print("check ATT_PUNCH_CSV and ATT_STAFF_MASTER.")
        return 2

    rows = []
    for code, name in sorted(roster.items()):
        rows.append({"code": code, "person": name, "retired": False,
                     "note": "on the roster at seeding"})
    ghosts = sorted(punched - set(roster))
    for code in ghosts:
        rows.append({"code": code, "person": "(left -- name not recorded)",
                     "retired": True,
                     "note": "found only in punches.csv; the person is gone, the "
                             "number is spoken for"})

    print("\nto seed: %d on the roster, %d retired ghosts from punches" %
          (len(roster), len(ghosts)))
    if ghosts:
        print("  ghost codes: %s" % ", ".join(str(c) for c in ghosts[:20]) +
              (" ..." if len(ghosts) > 20 else ""))
        print("  ^ THESE are the ones that would otherwise be handed out again.")
    highest = max(punched | set(roster)) if (punched or roster) else 0
    print("\nhighest code ever seen: %s   -> next to issue: %d" % (highest or "none", highest + 1))

    if a.dry:
        print("\n--dry: nothing sent.")
        return 0
    body = json.dumps({"source": "punches+roster", "codes": rows}).encode("utf-8")
    req = urllib.request.Request(a.api, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print("\nserver:", resp.read().decode("utf-8")[:400])
    except Exception as e:
        print("\ncould not reach %s -- %s" % (a.api, e))
        print("Run the app first, or pass --api. Nothing was changed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
