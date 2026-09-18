#!/root/wa/venv/bin/python3
# =============================================================================
#  update_xray_s321.py  ·  S321_XRAY_VIEWS  ·  v1
#
#  THE OWNER'S WORDS, 19-Sep-2026: "add this part after what you have named in
#  the X-ray, such as knee, then add AP & Lateral view. Similarly, do it for all
#  and then I will be editing it. It will be easy for me and keep the default
#  price as 500 rupees, which I will edit if needed."
#
#  And his price rule, in the same message:
#      a single view                               300
#      two views                                   500
#      on the large 11 x 14 film                   400  and  600
#      wrist AP + lateral + oblique (3 on 11 x 14) 800
#      PBH -- mostly 11 x 14, single view          400 each
#      chest -- AP and PA, both single views       any film size
#
#  So every X-ray row gains its views, every row gets a price, and chest becomes
#  TWO rows (AP and PA) because he described two studies, not one.
#
#  WHAT IT WILL NOT DO. It changes a row ONLY while that row is still the seed's
#  own -- updated_by = 'seed'. The moment he renames, prices, approves or rejects
#  a row, this script leaves it alone for ever: his edit is the record, not mine.
#  It never deletes, never touches a procedure row, and refuses a rename that
#  would collide with a name already in the table (the UNIQUE index on kind+name).
#
#  Idempotent: run it twice and the second run says ALREADY.
# =============================================================================
import argparse
import datetime as dt
import os
import sqlite3
import sys

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

# code -> (name with views, rupees)
PLAN = (
    ("KNEE",     "Knee AP & Lateral view",                        500),
    ("LS",       "Lumbosacral spine AP & Lateral view",           500),
    ("KS",       "Knee studies (K/S) AP & Lateral view",          500),
    ("ANKLE",    "Ankle AP & Lateral view",                       500),
    ("FOOT",     "Foot AP & Lateral view",                        500),
    ("CS",       "Cervical spine AP & Lateral view",              500),
    ("SHOULDER", "Shoulder AP & Lateral view",                    500),
    ("WRIST",    "Wrist AP, Lateral & Oblique view (11 x 14)",     800),
    ("ELBOW",    "Elbow AP & Lateral view",                       500),
    ("LEG",      "Leg (tibia-fibula) AP & Lateral view",          500),
    ("HAND",     "Hand AP & Lateral view",                        500),
    ("CHEST",    "Chest PA view",                                 300),
    ("PBH",      "Pelvis both hips AP view (11 x 14)",            400),
    ("TOES",     "Toes AP & Lateral view",                        500),
    ("DS",       "Dorsal spine AP & Lateral view",                500),
    ("THUMB",    "Thumb AP & Lateral view",                       500),
    ("FOREARM",  "Forearm AP & Lateral view",                     500),
    ("CLAVICLE", "Clavicle AP view",                              300),
    ("DL",       "Dorsolumbar AP & Lateral view",                 500),
)

# the second chest study, which the seed did not have
NEW_ROWS = (("CHEST_AP", "Chest AP view", 300),)


def now():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def open_db(path, write):
    if not os.path.isfile(path):
        print("RED -- no database at %s" % path)
        return None
    con = sqlite3.connect(path if write else "file:%s?mode=ro" % path, uri=not write)
    con.row_factory = sqlite3.Row
    return con


def plan_for(con):
    """(changes, skipped, collisions, missing) -- read-only."""
    changes, skipped, collisions, missing = [], [], [], []
    names = {r["name"]: r["id"] for r in
             con.execute("SELECT id, name FROM owner_service WHERE kind='xray'")}
    for code, name, rupees in PLAN:
        row = con.execute("SELECT id, name, price_p, status, updated_by FROM owner_service "
                          "WHERE kind='xray' AND code=?", (code,)).fetchone()
        if row is None:
            missing.append(code)
            continue
        if row["name"] == name and int(row["price_p"]) == rupees * 100:
            skipped.append((code, "already", row["name"]))
            continue
        if (row["updated_by"] or "") != "seed":
            skipped.append((code, "HIS OWN EDIT -- left alone", row["name"]))
            continue
        other = names.get(name)
        if other is not None and other != row["id"]:
            collisions.append((code, name))
            continue
        changes.append((row["id"], code, row["name"], name, rupees))
    for code, name, rupees in NEW_ROWS:
        if con.execute("SELECT 1 FROM owner_service WHERE kind='xray' AND code=?",
                       (code,)).fetchone():
            skipped.append((code, "already", name))
        elif name in names:
            collisions.append((code, name))
        else:
            changes.append((None, code, "(new row)", name, rupees))
    return changes, skipped, collisions, missing


def show(changes, skipped, collisions, missing):
    for _id, code, old, new, rupees in changes:
        print("    %-9s %-34s -> %-44s %5d" % (code, old[:34], new, rupees))
    for code, why, name in skipped:
        print("    %-9s %-34s    %s" % (code, name[:34], why))
    for code, name in collisions:
        print("    %-9s REFUSED -- '%s' is already another row's name" % (code, name))
    if missing:
        print("    not in the table (nothing done): %s" % ", ".join(missing))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/root/finance/finance.db")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv[1:])

    con = open_db(a.db, write=a.apply)
    if con is None:
        return 3
    try:
        con.execute("SELECT 1 FROM owner_service LIMIT 1")
    except sqlite3.Error as ex:
        print("RED -- owner_service is not readable here: %s" % ex)
        return 3

    changes, skipped, collisions, missing = plan_for(con)
    print("    database: %s" % a.db)
    show(changes, skipped, collisions, missing)
    if collisions:
        print("RESULT RED -- a rename would collide; nothing written")
        return 4
    if not changes:
        print("RESULT ALREADY -- nothing to change")
        return 0
    if not a.apply:
        print("RESULT PENDING -- %d row(s) would change; --apply writes them" % len(changes))
        return 0

    ts = now()
    for sid, code, _old, new, rupees in changes:
        if sid is None:
            con.execute("INSERT INTO owner_service (kind,name,price_p,code,status,seen,grp,source,"
                        "created_by,created_ts,updated_by,updated_ts) "
                        "VALUES ('xray',?,?,?,'pending',0,'X-ray','owner-rule-S321','seed',?,'seed',?)",
                        (new, rupees * 100, code, ts, ts))
        else:
            con.execute("UPDATE owner_service SET name=?, price_p=?, updated_by='seed', updated_ts=? "
                        "WHERE id=? AND kind='xray'", (new, rupees * 100, ts, sid))
    con.commit()

    # read back
    bad = []
    for code, name, rupees in list(PLAN) + list(NEW_ROWS):
        r = con.execute("SELECT name, price_p FROM owner_service WHERE kind='xray' AND code=?",
                        (code,)).fetchone()
        if r is None:
            continue
        if r["name"] != name or int(r["price_p"]) != rupees * 100:
            if code not in [c for c, _w, _n in skipped]:
                bad.append(code)
    if bad:
        print("RESULT RED -- the read-back does not match for: %s" % ", ".join(bad))
        return 5
    print("RESULT APPLIED -- %d row(s) written, read back" % len(changes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
