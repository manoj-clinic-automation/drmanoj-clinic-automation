#!/usr/bin/env python3
"""make_s813.py -- S813_SPINE_PART_EXPORT (13-Nov-2026, Sanjeevni session 444).
Rebuilds /root/finance/spine/spine_build.py from its LIVE bytes by exact anchors (each must occur once) and writes the result.
    python3 make_s813.py <live spine_build.py> <out file>      -> prints the md5 of the result; exit 1 on any anchor not found once.
"""
import hashlib
import sys

FROM_PIN = "67d5693fbd853fca7979fa4763f9f825"

EDITS = [
    # 1. the version
    ('BUILD_VERSION = "S704.1"\n', 'BUILD_VERSION = "S813.1"\n'),
    # 2. the rule, beside supnorm
    ('def supnorm(s):\n    return re.sub(r\'[^A-Z]\', \'\', (s or "").upper())[:8]\n',
     'def supnorm(s):\n    return re.sub(r\'[^A-Z]\', \'\', (s or "").upper())[:8]\n'
     '\n\n'
     'def part_list(r, auth, exports, key):\n'
     '    """S813 (13-Nov-2026; S795\'s rule for the purchase pages, F-1277): a purchase report holding fewer than HALF the rows of an older\n'
     '    report that is today the authority for some of its days -- one whose whole period lies inside this report\'s period -- and more\n'
     '    than two rows short of it, is a PART LIST.  It is set aside whole (r[\'_part\'] names the fuller report) and the fuller report\n'
     '    stays the authority.  On 11-Nov Marg printed November\'s bill list twice, 15 s apart -- 29 bills, then 4 -- and the 4-bill list,\n'
     '    being the later, retired the full one: the gate failed on the item lines of 25 bills and the spine stood still for two days.\n'
     '    key: \'bills\' (bill-wise) or \'lines\' (item-wise).  Only an OLDER authority can make a report a part list; a later, fuller\n'
     '    report simply takes over as before."""\n'
     '    d0, d1 = r["data"]["date_from"], r["data"]["date_to"]\n'
     '    mine = len(r["data"].get(key) or [])\n'
     '    for m in sorted({auth[d] for d in dates(d0, d1) if d in auth}):\n'
     '        o = exports.get(m)\n'
     '        if not o or not o.get("_accepted"):            # only a report that passed its own witness can be the fuller one\n'
     '            continue\n'
     '        od = o["data"]\n'
     '        if not (d0 <= od["date_from"] and od["date_to"] <= d1):\n'
     '            continue\n'
     '        theirs = len(od.get(key) or [])\n'
     '        if mine < 0.5 * theirs and theirs - mine > 2:\n'
     '            r["_part"] = o["name"]\n'
     '            return True\n'
     '    return False\n'),
    # 3. bill-wise authority
    ('    auth_bw = {}\n    for r in BW:                                         # latest stamp covering a day is that day\'s authority\n'
     '        for d in dates(r["data"]["date_from"], r["data"]["date_to"]):\n            auth_bw[d] = r["md5"]\n',
     '    auth_bw = {}\n    for r in BW:                                         # latest stamp covering a day is that day\'s authority\n'
     '        if part_list(r, auth_bw, exports, "bills"):      # S813: ... unless it is a part list of an older, fuller report\n'
     '            continue\n'
     '        for d in dates(r["data"]["date_from"], r["data"]["date_to"]):\n            auth_bw[d] = r["md5"]\n'),
    # 4. item-wise authority
    ('    auth_pl = {}\n    for r in PL:\n        for d in dates(r["data"]["date_from"], r["data"]["date_to"]):\n            auth_pl[d] = r["md5"]\n',
     '    auth_pl = {}\n    for r in PL:\n'
     '        if part_list(r, auth_pl, exports, "lines"):      # S813: the same rule for the item lines (a report rescued later\n'
     '            continue                                   # by the returns witness is judged too -- R1 of the cold review)\n'
     '        for d in dates(r["data"]["date_from"], r["data"]["date_to"]):\n            auth_pl[d] = r["md5"]\n'),
    # 4b. a gate line names every part list set aside (information, never blocking)
    ('              len(hard), hard[:6], len(undated) - len(hard), [u[:4] for u in undated if not u[4]][:6]))\n',
     '              len(hard), hard[:6], len(undated) - len(hard), [u[:4] for u in undated if not u[4]][:6]))\n'
     '    parts = [(r["name"], r["_part"]) for r in BW + PL if r.get("_part")]\n'
     '    G.add("purchase reports set aside as a part list of a fuller one (S813, information)", True,\n'
     '          "%d: %s" % (len(parts), parts), blocking=False)\n'),
    # 5. sp_export says so, and a part list is not counted as cover (ok=0)
    ('            int(bool(r.get("_accepted"))), json.dumps(r.get("_real_fail", [])), "READ" if r.get("family") else "NOT_USED",\n'
     '            ("waived: " + "; ".join(r["_waived"])) if r.get("_waived") else ""))\n',
     '            int(bool(r.get("_accepted")) and not r.get("_part")),\n'
     '            json.dumps(r.get("_real_fail", []) + (["part list of " + r["_part"] + " (S813)"] if r.get("_part") else [])),\n'
     '            ("PART_LIST" if r.get("_part") else "READ") if r.get("family") else "NOT_USED",\n'
     '            ("waived: " + "; ".join(r["_waived"])) if r.get("_waived") else ""))\n'),
]


def main(a):
    src, out = a[1], a[2]
    b = open(src, "rb").read()
    if hashlib.md5(b).hexdigest() != FROM_PIN:
        print("STOP: the live file is not the pinned one (%s)" % hashlib.md5(b).hexdigest())
        return 1
    t = b.decode("utf-8")
    for old, new in EDITS:
        n = t.count(old)
        if n != 1:
            print("STOP: an anchor occurs %d times: %r" % (n, old[:80]))
            return 1
        t = t.replace(old, new)
    open(out, "wb").write(t.encode("utf-8"))
    print(hashlib.md5(t.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
