"""s929_load.py -- S929 one-off (the parent, S498, 22-Nov-2026), staff_register.db, ONE transaction, audited.
The owner's word 14:34: the JAN 2027 tab of Shavez's 'DRESS UNIFORM DETAILS' sheet is the set each staff member has NOW;
mobiles with Shavez, Darpan, Surendra, Ranjeet; a cycle with Sandip.
  1. each listed staff member's CURRENT uniform set -> an approved issue (size, pieces), dated today (the hand-over date was
     not recorded); the earlier issues on the sheet's 2025 and 2026 tabs -> approved issues with their own dates;
  2. that staff member's open uniform pause windows close the day before (the fine resumes today) -- S929's own rule;
  3. uniform entries still waiting for approval, older than the current set, -> 'superseded' (they never counted);
  4. the mobiles and the cycle -> 'Issued assets' (number / IMEI and date not yet recorded).
Usage: s929_load.py DB [--apply]  (without --apply: says what it would do). A second --apply says ALREADY DONE."""
import datetime as dt, sqlite3, sys
DB = sys.argv[1]
APPLY = "--apply" in sys.argv[2:]
WHO = "manoj (S929, owner's word 22-Nov)"
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).date().isoformat()
NOW = (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
TAG = "(S929)"
CURRENT = [  # name, size, blazer, shirts, hoodie, white T, blue T  -- the JAN 2027 tab
    ("Ranjeet", "M 36", 0, 0, 0, 0, 2), ("Sukhveer", "XXL 42", 0, 0, 1, 0, 2), ("Surendra", "L 38", 0, 0, 1, 0, 2),
    ("Vikki", "M 36", 0, 0, 1, 0, 2), ("Sandip", "XL 40", 0, 0, 1, 0, 2), ("Awdhesh", "L 38", 1, 2, 0, 2, 0),
    ("Shivani", "XL 40", 1, 2, 0, 2, 0), ("Darpan", "XL 40", 1, 2, 0, 2, 0), ("Shavez", "L 38", 1, 2, 0, 2, 0),
    ("Alisha", "XL 40", 1, 2, 0, 2, 0)]
HISTORY = [  # name, date, size, pieces -- the 2025 and 2026 tabs
    ("Surendra", "2025-10-09", "XL", "Blue/black T 1"), ("Sandip", "2025-09-11", "XL", "Blue/black T 2"),
    ("Ranjeet", "2025-09-11", "M", "Blue/black T 2"), ("Shivani", "2025-09-12", "XL", "White T 2"),
    ("Awdhesh", "2025-09-11", "M", "White T 2"), ("Shavez", "2025-09-11", "XL", "White T 2"),
    ("Alisha", "2025-09-11", "XL", "White T 2"), ("Darpan", "2025-09-12", "L", "White T 2"),
    ("Vikki", "2026-06-21", "M", "Blue T 2"), ("Awdhesh", "2026-06-21", "M", "White T 2"),
    ("Shivani", "2026-06-22", "42", "White T 2"), ("Darpan", "2026-06-21", "L", "White T 2"),
    ("Sukhveer", "2026-06-22", "XL", "Blue T 2")]
ASSETS = [("Shavez", "mobile_phone", "Clinic mobile"), ("Darpan", "mobile_phone", "Clinic mobile"),
          ("Surendra", "mobile_phone", "Clinic mobile"), ("Ranjeet", "mobile_phone", "Clinic mobile"),
          ("Sandip", "bicycle", "Clinic cycle")]
def pieces(b, sh, h, w, bl):
    parts = [("Blazer", b), ("Shirts", sh), ("Hoodie", h), ("White T", w), ("Blue T", bl)]
    return " · ".join("%s %d" % (n, q) for n, q in parts if q)
con = sqlite3.connect(DB, timeout=30)
con.row_factory = sqlite3.Row
if APPLY:                                                # the S929 columns (the app adds them at its start too; harmless twice)
    have = {r["name"] for r in con.execute("PRAGMA table_info(issuance)")}
    for col in ("size", "pieces", "note"):
        if col not in have:
            con.execute("ALTER TABLE issuance ADD COLUMN %s TEXT" % col)
    con.commit()
elif not {"size", "pieces", "note"} <= {r["name"] for r in con.execute("PRAGMA table_info(issuance)")}:
    print("S929_LOAD: WOULD add the size / pieces / note columns first, then the load (dry)"); sys.exit(0)
ids = {}
for r in con.execute("SELECT staff_id, name FROM staff WHERE active=1"):
    ids.setdefault(r["name"].strip().lower(), r["staff_id"])
names = {n for n, *_ in CURRENT} | {n for n, *_ in HISTORY} | {n for n, *_ in ASSETS}
missing = sorted(n for n in names if n.lower() not in ids)
if missing:
    print("S929_LOAD: NOT AS FOUND -- no active staff named %s; nothing changed" % ", ".join(missing)); sys.exit(2)
done = con.execute("SELECT COUNT(*) FROM issuance WHERE note LIKE ?", ("%" + TAG + "%",)).fetchone()[0]
if done:
    print("S929_LOAD: ALREADY DONE (%d issues carry %s)" % (done, TAG)); sys.exit(0)
openp = con.execute("SELECT COUNT(*) FROM issuance_pause WHERE item_type='uniform' AND to_date IS NULL AND staff_id IN (%s)"
                    % ",".join(str(ids[n.lower()]) for n, *_ in CURRENT)).fetchone()[0]
if not APPLY:
    print("S929_LOAD: WOULD add %d current sets + %d earlier issues, close %d open uniform pauses, add %d assets (dry)"
          % (len(CURRENT), len(HISTORY), openp, len(ASSETS))); sys.exit(0)
try:
    con.execute("BEGIN IMMEDIATE")
    def audit(entity, ref, action, old, new):
        con.execute("INSERT INTO audit_log(entity,entity_ref,action,old_value,new_value,actor,ts,note) VALUES(?,?,?,?,?,?,?,?)",
                    (entity, str(ref), action, str(old), str(new), WHO, NOW, "S929 one-off"))
    for n, d, size, pc in HISTORY:
        sid = ids[n.lower()]
        c = con.execute("INSERT INTO issuance(staff_id,item_type,season,issued_date,maker_user,maker_ts,checker_user,checker_ts,"
                        "status,size,pieces,note) VALUES(?,?,?,?,?,?,?,?, 'approved',?,?,?)",
                        (sid, "uniform", None, d, WHO, NOW, WHO, NOW, size, pc, "Shavez's sheet " + TAG))
        audit("issuance", c.lastrowid, "add+approve", "", "uniform %s %s" % (d, pc))
    closed = superseded = 0
    for n, size, b, sh, h, w, bl in CURRENT:
        sid = ids[n.lower()]
        c = con.execute("INSERT INTO issuance(staff_id,item_type,season,issued_date,maker_user,maker_ts,checker_user,checker_ts,"
                        "status,size,pieces,note) VALUES(?,?,?,?,?,?,?,?, 'approved',?,?,?)",
                        (sid, "uniform", None, TODAY, WHO, NOW, WHO, NOW, size, pieces(b, sh, h, w, bl),
                         "current set with staff, hand-over date not recorded -- sheet tab JAN 2027 " + TAG))
        audit("issuance", c.lastrowid, "add+approve", "", "uniform current set %s" % TODAY)
        before = (dt.date.fromisoformat(TODAY) - dt.timedelta(days=1)).isoformat()
        for p in con.execute("SELECT id, from_date FROM issuance_pause WHERE staff_id=? AND item_type='uniform' AND to_date IS NULL "
                             "AND from_date<=?", (sid, TODAY)).fetchall():
            to = max(before, p["from_date"])
            con.execute("UPDATE issuance_pause SET to_date=?, checker_user=?, checker_ts=?, status='closed' WHERE id=? AND to_date IS NULL",
                        (to, WHO, NOW, p["id"]))
            audit("pause", p["id"], "close", "open", "closed %s (current set recorded, S929)" % to)
            closed += 1
        for q in con.execute("SELECT id FROM issuance WHERE staff_id=? AND item_type='uniform' AND status='draft' AND issued_date<?",
                             (sid, TODAY)).fetchall():
            con.execute("UPDATE issuance SET status='superseded', checker_user=?, checker_ts=?, note=COALESCE(note,'') || ? WHERE id=?",
                        (WHO, NOW, " superseded by the current set " + TAG, q["id"]))
            audit("issuance", q["id"], "supersede", "draft", "superseded")
            superseded += 1
    added = 0
    for n, typ, descr in ASSETS:
        sid = ids[n.lower()]
        if con.execute("SELECT 1 FROM asset_issue WHERE staff_id=? AND asset_type=? AND status='issued'", (sid, typ)).fetchone():
            continue
        c = con.execute("INSERT INTO asset_issue(staff_id,asset_type,identifier,descr,issued_date,issued_by,status,note) "
                        "VALUES(?,?,NULL,?,NULL,?,'issued',?)", (sid, typ, descr, WHO, "number / IMEI and date not recorded yet " + TAG))
        con.execute("INSERT INTO audit_log(entity,entity_ref,action,old_value,new_value,actor,ts,note) VALUES('asset',?,'issue',?,'',?,?,'S929 one-off')",
                    (str(sid), typ, WHO, NOW))
        added += 1
    con.commit()
except Exception as ex:                                  # noqa: BLE001
    con.rollback()
    print("S929_LOAD: FAILED, rolled back -- nothing changed: %s" % ex); sys.exit(3)
print("S929_LOAD: APPLIED -- %d current sets + %d earlier issues; %d pauses closed (fine resumes %s); %d pending entries superseded; %d assets"
      % (len(CURRENT), len(HISTORY), closed, TODAY, superseded, added))
