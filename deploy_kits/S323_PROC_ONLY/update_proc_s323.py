#!/root/wa/venv/bin/python3
# =============================================================================
#  update_proc_s323.py  ·  S323_PROC_ONLY  ·  v1
#
#  TWO DATA CHANGES HE ASKED FOR, 19-Sep-2026.
#
#  1. THE DISPLAY HE WANTS: "each one has a display with its abbreviation first,
#     and name in brackets as in A/E (Above elbow)". So every cast, slab and ILI
#     line is renamed to the clinic's own shorthand with the words in brackets:
#
#         A/K (Above knee) fibre cast      A/K (Above knee) fibre slab
#         A/E (Above elbow) fibre cast     A/E (Above elbow) fibre slab
#         ILI (shoulder) ...
#
#     U slab and the dressing keep their plain names: their shorthand IS the word.
#
#  2. THE SIDE FLAG, WHICH DID NOT TAKE. S322 reported "X-rays that now ask a
#     side: 0", and the reason is in its own safety rule: it only flagged rows
#     still marked as the seed's own, and by then he had approved the X-ray list,
#     so every row was marked as HIS. The flag is additive -- it changes no name,
#     no price and no approval -- so here it is set wherever it is relevant
#     regardless of who last touched the row. That is the one thing this script
#     does not ask permission for, and the reason is written here.
#
#  A NAME he has typed himself is still never overwritten: a rename happens only
#  when the row still carries the exact text the previous kit wrote.
# =============================================================================
import argparse
import datetime as dt
import os
import sqlite3
import sys

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

#  code, the S322 name (what we may replace), the new display name
CAST = (
    ("AK",         "Above knee fibre cast",        "A/K (Above knee) fibre cast"),
    ("AK-SLAB",    "Above knee fibre slab",        "A/K (Above knee) fibre slab"),
    ("BK",         "Below knee fibre cast",        "B/K (Below knee) fibre cast"),
    ("BK-SLAB",    "Below knee fibre slab",        "B/K (Below knee) fibre slab"),
    ("SBK",        "Short below knee fibre cast",  "S/BK (Short below knee) fibre cast"),
    ("SBK-SLAB",   "Short below knee fibre slab",  "S/BK (Short below knee) fibre slab"),
    ("HBK",        "High below knee fibre cast",   "H/BK (High below knee) fibre cast"),
    ("HBK-SLAB",   "High below knee fibre slab",   "H/BK (High below knee) fibre slab"),
    ("CYL",        "Cylinder fibre cast",          "CYL (Cylinder) fibre cast"),
    ("CYL-SLAB",   "Cylinder fibre slab",          "CYL (Cylinder) fibre slab"),
    ("AE",         "Above elbow fibre cast",       "A/E (Above elbow) fibre cast"),
    ("AE-SLAB",    "Above elbow fibre slab",       "A/E (Above elbow) fibre slab"),
    ("BE",         "Below elbow fibre cast",       "B/E (Below elbow) fibre cast"),
    ("BE-SLAB",    "Below elbow fibre slab",       "B/E (Below elbow) fibre slab"),
    ("SBE",        "Short below elbow fibre cast", "S/BE (Short below elbow) fibre cast"),
    ("SBE-SLAB",   "Short below elbow fibre slab", "S/BE (Short below elbow) fibre slab"),
    ("USLAB",      "U fibre slab",                 "U fibre slab"),
    ("USLAB-CAST", "U fibre cast",                 "U fibre cast"),
    ("SPICA",      "Thumb spica fibre cast",       "SPICA (Thumb spica) fibre cast"),
    ("SPICA-SLAB", "Thumb spica fibre slab",       "SPICA (Thumb spica) fibre slab"),
    ("ILI-SH",     "ILI shoulder",                 "ILI (shoulder)"),
    ("ILI-EL",     "ILI elbow",                    "ILI (elbow)"),
    ("ILI-TH",     "ILI thumb",                    "ILI (thumb)"),
    ("ILI-FI",     "ILI finger (trigger finger)",  "ILI (trigger finger)"),
    ("ILI-HE",     "ILI heel (plantar fasciitis)", "ILI (heel, plantar fasciitis)"),
)

SIDE_PROC = ("AK", "AK-SLAB", "BK", "BK-SLAB", "SBK", "SBK-SLAB", "HBK", "HBK-SLAB",
             "CYL", "CYL-SLAB", "AE", "AE-SLAB", "BE", "BE-SLAB", "SBE", "SBE-SLAB",
             "USLAB", "USLAB-CAST", "SPICA", "SPICA-SLAB",
             "ILI-SH", "ILI-EL", "ILI-TH", "ILI-FI", "ILI-HE")
SIDE_XRAY = ("KNEE", "KS", "ANKLE", "FOOT", "SHOULDER", "WRIST", "ELBOW", "LEG",
             "HAND", "TOES", "THUMB", "FOREARM", "CLAVICLE")


def now():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def open_db(path, write):
    if not os.path.isfile(path):
        print("RED -- no database at %s" % path)
        return None
    con = sqlite3.connect(path if write else "file:%s?mode=ro" % path, uri=not write)
    con.row_factory = sqlite3.Row
    return con


def plan(con):
    renames, sides, kept, collisions = [], [], [], []
    names = {(r["kind"], r["name"]): r["id"] for r in
             con.execute("SELECT id, kind, name FROM owner_service")}
    for code, was, new in CAST:
        r = con.execute("SELECT id, name FROM owner_service WHERE kind='proc' AND code=?",
                        (code,)).fetchone()
        if r is None:
            continue
        if r["name"] == new:
            continue
        if r["name"] != was:                       # he has typed his own words here
            kept.append((code, r["name"]))
            continue
        if names.get(("proc", new), r["id"]) != r["id"]:
            collisions.append((code, new))
            continue
        renames.append((r["id"], code, r["name"], new))
    for kind, codes in (("proc", SIDE_PROC), ("xray", SIDE_XRAY)):
        for code in codes:
            r = con.execute("SELECT id, side, name FROM owner_service WHERE kind=? AND code=?",
                            (kind, code)).fetchone()
            if r is not None and (r["side"] or "") != "ask":
                sides.append((r["id"], code, r["name"]))
    return renames, sides, kept, collisions


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/root/finance/finance.db")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv[1:])
    con = open_db(a.db, write=a.apply)
    if con is None:
        return 3
    have = [r[1] for r in con.execute("PRAGMA table_info(owner_service)")]
    if "side" not in have:
        print("RED -- the side column is missing; install S322 first")
        return 3

    renames, sides, kept, collisions = plan(con)
    print("    database: %s" % a.db)
    for _i, code, old, new in renames:
        print("    %-11s %-30s -> %s" % (code, old[:30], new))
    if sides:
        print("    side R / L set on %d line(s): %s"
              % (len(sides), ", ".join(c for _i, c, _n in sides)))
    for code, name in kept:
        print("    %-11s YOUR OWN WORDING KEPT: %s" % (code, name))
    for code, name in collisions:
        print("    %-11s REFUSED -- '%s' is already another row's name" % (code, name))
    if collisions:
        print("RESULT RED -- a rename would collide; nothing written")
        return 4
    if not (renames or sides):
        print("RESULT ALREADY -- nothing to change")
        return 0
    if not a.apply:
        print("RESULT PENDING -- %d rename(s) and %d side flag(s); --apply writes them"
              % (len(renames), len(sides)))
        return 0

    ts = now()
    for sid, _code, _old, new in renames:
        con.execute("UPDATE owner_service SET name=?, updated_ts=? WHERE id=?", (new, ts, sid))
    for sid, _code, _name in sides:
        con.execute("UPDATE owner_service SET side='ask', updated_ts=? WHERE id=?", (ts, sid))
    con.commit()

    bad = [c for _i, c, _o, n in renames
           if (con.execute("SELECT name FROM owner_service WHERE id=?",
                           (_i,)).fetchone()["name"] != n)]
    off = [c for _i, c, _n in sides
           if (con.execute("SELECT side FROM owner_service WHERE id=?",
                           (_i,)).fetchone()["side"] != "ask")]
    if bad or off:
        print("RESULT RED -- the read-back disagrees: names %s · sides %s"
              % (", ".join(bad) or "-", ", ".join(off) or "-"))
        return 5
    print("RESULT APPLIED -- %d renamed, %d side flag(s), read back" % (len(renames), len(sides)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
