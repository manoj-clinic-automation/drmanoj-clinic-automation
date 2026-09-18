#!/root/wa/venv/bin/python3
# =============================================================================
#  update_proc_s322.py  ·  S322_PROC_SIDE  ·  v1
#
#  HIS INSTRUCTION, 19-Sep-2026: the word FIBRE in every cast and slab; every
#  plaster variant to exist BOTH as a cast and as a slab, because the two carry
#  different charges; right / left asked on the ILI lines, and on the X-rays
#  where it applies.
#
#  WHAT THIS DOES, on the live table, and nothing else:
#
#   * each of the ten plaster sites: the seeded row is RENAMED to the fibre cast
#     (or the fibre slab, for U slab) and its twin is ADDED, with the same
#     consumables copied across, so both forms are priced separately;
#   * every cast-and-slab line and every ILI line is marked "asks R / L";
#   * the limb X-rays are marked the same way -- knee, ankle, foot, shoulder,
#     wrist, elbow, leg, hand, toes, thumb, forearm, clavicle. The spines, the
#     chest and pelvis-both-hips are not, because there is no side to ask.
#
#  PRICES ARE LEFT EMPTY on the procedures: he has not stated them, and a number
#  I invented would be worse than a blank he fills. The page already counts a
#  blank as waiting for him.
#
#  SAFETY, the same as S321: a row he has touched himself (updated_by is not
#  'seed') is never renamed, never re-flagged, never overwritten. Nothing is ever
#  deleted. Idempotent -- the second run says ALREADY.
# =============================================================================
import argparse
import datetime as dt
import os
import sqlite3
import sys

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

#  code, site, which form the SEEDED row becomes, which form is added
PLASTER = (
    ("AK",    "Above knee",        "cast", "slab"),
    ("BK",    "Below knee",        "cast", "slab"),
    ("SBK",   "Short below knee",  "cast", "slab"),
    ("HBK",   "High below knee",   "cast", "slab"),
    ("CYL",   "Cylinder",          "cast", "slab"),
    ("AE",    "Above elbow",       "cast", "slab"),
    ("BE",    "Below elbow",       "cast", "slab"),
    ("SBE",   "Short below elbow", "cast", "slab"),
    ("USLAB", "U",                 "slab", "cast"),      # a U slab is a slab first
    ("SPICA", "Thumb spica",       "cast", "slab"),
)

SIDE_ON_PROC = ("AK", "BK", "SBK", "HBK", "CYL", "AE", "BE", "SBE", "USLAB", "SPICA",
                "ILI-SH", "ILI-EL", "ILI-TH", "ILI-FI", "ILI-HE")
SIDE_ON_XRAY = ("KNEE", "KS", "ANKLE", "FOOT", "SHOULDER", "WRIST", "ELBOW", "LEG",
                "HAND", "TOES", "THUMB", "FOREARM", "CLAVICLE")


def now():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def name_for(site, form):
    return "%s fibre %s" % (site, form)


def twin_code(code, form):
    return "%s-%s" % (code, form.upper())


def open_db(path, write):
    if not os.path.isfile(path):
        print("RED -- no database at %s" % path)
        return None
    con = sqlite3.connect(path if write else "file:%s?mode=ro" % path, uri=not write)
    con.row_factory = sqlite3.Row
    return con


def plan(con):
    renames, adds, sides, skipped, collisions = [], [], [], [], []
    names = {(r["kind"], r["name"]): r["id"] for r in
             con.execute("SELECT id, kind, name FROM owner_service")}
    for code, site, keep_form, add_form in PLASTER:
        row = con.execute("SELECT id, name, updated_by FROM owner_service "
                          "WHERE kind='proc' AND code=?", (code,)).fetchone()
        if row is None:
            skipped.append((code, "not in the table"))
        else:
            want = name_for(site, keep_form)
            if row["name"] == want:
                skipped.append((code, "already named"))
            elif (row["updated_by"] or "") != "seed":
                skipped.append((code, "HIS OWN EDIT -- left alone"))
            elif names.get(("proc", want), row["id"]) != row["id"]:
                collisions.append((code, want))
            else:
                renames.append((row["id"], code, row["name"], want, keep_form))
        tcode = twin_code(code, add_form)
        twant = name_for(site, add_form)
        if con.execute("SELECT 1 FROM owner_service WHERE kind='proc' AND code=?",
                       (tcode,)).fetchone():
            skipped.append((tcode, "already there"))
        elif ("proc", twant) in names:
            collisions.append((tcode, twant))
        else:
            adds.append((code, tcode, twant, add_form))
    for kind, codes in (("proc", SIDE_ON_PROC), ("xray", SIDE_ON_XRAY)):
        for code in codes:
            r = con.execute("SELECT id, side, updated_by, name FROM owner_service "
                            "WHERE kind=? AND code=?", (kind, code)).fetchone()
            if r is None:
                continue
            if (r["side"] or "") == "ask":
                continue
            if (r["updated_by"] or "") != "seed":
                skipped.append((code, "side left alone -- his own edit"))
                continue
            sides.append((r["id"], code, r["name"]))
    return renames, adds, sides, skipped, collisions


def show(renames, adds, sides, skipped, collisions):
    for _id, code, old, new, form in renames:
        print("    %-10s %-26s -> %s" % (code, old[:26], new))
    for _src, tcode, name, form in adds:
        print("    %-10s NEW                        -> %s" % (tcode, name))
    if sides:
        print("    side R / L asked on %d line(s): %s"
              % (len(sides), ", ".join(c for _i, c, _n in sides)))
    for code, why in skipped:
        print("    %-10s %s" % (code, why))
    for code, name in collisions:
        print("    %-10s REFUSED -- '%s' is already another row's name" % (code, name))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/root/finance/finance.db")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv[1:])
    con = open_db(a.db, write=a.apply)
    if con is None:
        return 3
    # The side column. The page's own migration adds it on the first OWNER visit --
    # but a curl from the installer gets the login redirect and never reaches that
    # code, so this script does not wait for a page load: it adds the column
    # itself, with the same declaration, and says so. Idempotent either way.
    have = [r[1] for r in con.execute("PRAGMA table_info(owner_service)")]
    if "side" not in have:
        if not a.apply:
            print("    the side column is not there yet -- --apply adds it (TEXT NOT NULL DEFAULT '')")
        else:
            con.execute("ALTER TABLE owner_service ADD COLUMN side TEXT NOT NULL DEFAULT ''")
            con.commit()
            print("    side column added")
    if "side" not in [r[1] for r in con.execute("PRAGMA table_info(owner_service)")]:
        print("RESULT PENDING -- run with --apply; the side column comes first")
        return 0

    renames, adds, sides, skipped, collisions = plan(con)
    print("    database: %s" % a.db)
    show(renames, adds, sides, skipped, collisions)
    if collisions:
        print("RESULT RED -- a rename would collide; nothing written")
        return 4
    if not (renames or adds or sides):
        print("RESULT ALREADY -- nothing to change")
        return 0
    if not a.apply:
        print("RESULT PENDING -- %d rename(s), %d new row(s), %d side flag(s); --apply writes them"
              % (len(renames), len(adds), len(sides)))
        return 0

    ts = now()
    for sid, code, _old, new, form in renames:
        con.execute("UPDATE owner_service SET name=?, forms=?, updated_by='seed', updated_ts=? "
                    "WHERE id=?", (new, form, ts, sid))
    for src_code, tcode, name, form in adds:
        src = con.execute("SELECT id, grp FROM owner_service WHERE kind='proc' AND code=?",
                          (src_code,)).fetchone()
        grp = src["grp"] if src else "Cast / slab"
        cur = con.execute("INSERT INTO owner_service (kind,name,price_p,code,status,grp,forms,source,"
                          "side,created_by,created_ts,updated_by,updated_ts) "
                          "VALUES ('proc',?,0,?,'pending',?,?,'owner-rule-S322','ask','seed',?,'seed',?)",
                          (name, tcode, grp, form, ts, ts))
        new_id = cur.lastrowid
        if src:            # the consumables are the same for both forms
            for it in con.execute("SELECT item, qty, unit, ask, sizes, note FROM owner_service_item "
                                  "WHERE service_id=?", (src["id"],)).fetchall():
                con.execute("INSERT INTO owner_service_item (service_id,item,qty,unit,ask,sizes,note,"
                            "added_by,added_ts) VALUES (?,?,?,?,?,?,?,'seed',?)",
                            (new_id, it["item"], it["qty"], it["unit"], it["ask"], it["sizes"],
                             it["note"], ts))
    for sid, _code, _name in sides:
        con.execute("UPDATE owner_service SET side='ask', updated_by='seed', updated_ts=? "
                    "WHERE id=?", (ts, sid))
    con.commit()

    # The read-back asks only about what THIS run wrote. A line he renamed himself
    # is not expected to carry the word fibre -- his name is the record, and
    # checking it here is how a green gate turns into a false red.
    touched = [c for _i, c, _o, _n, _f in renames] + [t for _s, t, _n, _f in adds]
    bad = []
    for c in touched:
        r = con.execute("SELECT name FROM owner_service WHERE kind='proc' AND code=?",
                        (c,)).fetchone()
        if r is not None and "fibre" not in (r["name"] or ""):
            bad.append(c)
    if bad:
        print("RESULT RED -- the read-back finds lines without the word fibre: %s" % ", ".join(bad))
        return 5
    print("RESULT APPLIED -- %d renamed, %d added, %d side flag(s), read back"
          % (len(renames), len(adds), len(sides)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
