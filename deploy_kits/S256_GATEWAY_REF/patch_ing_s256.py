#!/usr/bin/env python3
"""S256_GATEWAY_REF -- docterz_ingest.py. Store the reference the parser now keeps.
Additive only: one new column with a default, an idempotent migration for the existing database,
and the column carried through the insert. No existing column, row or figure changes.
"""
import io, sys
SRC, DST = sys.argv[1], sys.argv[2]
s = io.open(SRC, encoding="utf-8").read(); n = 0
def sub(old, new):
    global s, n
    c = s.count(old)
    if c != 1: raise SystemExit("ANCHOR COUNT %d (expected 1):\n%s" % (c, old[:140]))
    s = s.replace(old, new); n += 1

sub("""  mode          TEXT    NOT NULL DEFAULT '',
  shift         TEXT    NOT NULL DEFAULT '',
  PRIMARY KEY (business_date, section, sn)
""",
    """  mode          TEXT    NOT NULL DEFAULT '',
  gateway_ref   TEXT    NOT NULL DEFAULT '',
  shift         TEXT    NOT NULL DEFAULT '',
  PRIMARY KEY (business_date, section, sn)
""")

sub('''def upsert_lines(con, d):''',
    '''def _ensure_gateway_ref(con):
    """S256: add clinic_day_line.gateway_ref to a database created before this kit. Idempotent,
    additive, and silent when the column is already there."""
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(clinic_day_line)")]
        if "gateway_ref" not in cols:
            con.execute("ALTER TABLE clinic_day_line ADD COLUMN gateway_ref TEXT NOT NULL DEFAULT ''")
    except Exception:                                      # noqa: BLE001
        pass


def upsert_lines(con, d):''')

sub('''    con.execute("DELETE FROM clinic_day_line WHERE business_date=?", (d["business_date"],))
    con.executemany(
        "INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, "
        "mode, shift) VALUES (?,?,?,?,?,?,?,?)",
        [(d["business_date"], l["section"], l["sn"], l["patient"], l["clinic_id"],
          l["amount_p"], l["mode"], l["shift"]) for l in d.get("lines", [])])
''',
    '''    _ensure_gateway_ref(con)
    con.execute("DELETE FROM clinic_day_line WHERE business_date=?", (d["business_date"],))
    con.executemany(
        "INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, "
        "mode, gateway_ref, shift) VALUES (?,?,?,?,?,?,?,?,?)",
        [(d["business_date"], l["section"], l["sn"], l["patient"], l["clinic_id"],
          l["amount_p"], l["mode"], l.get("gateway_ref", ""), l["shift"])
         for l in d.get("lines", [])])
''')
io.open(DST, "w", encoding="utf-8", newline="").write(s)
print("anchors applied:", n)
