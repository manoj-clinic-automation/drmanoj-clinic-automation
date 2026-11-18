#!/usr/bin/env python3
"""shape_s878.py <code_dir> <db_copy> [n] -- the new page on real IDs of a COPY of the live database: every page 200, timings,
counts only (no name, number or diagnosis printed). Last line: SHAPE ok=<n> fail=<n> max_ms=<n> avg_ms=<n>."""
import os, sqlite3, sys, time, random, re
code, dbp = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 40
sys.path.insert(0, code)
import records as rc, patient_events as pe
import flask
def getdb():
    c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True); c.row_factory = sqlite3.Row; return c
app = flask.Flask("s878shape")
rc.init(app, getdb, lambda *a, **kw: ({"user": "manoj"}, None)); pe.init(app, getdb, lambda *a, **kw: ({"user": "manoj"}, None))
cl = app.test_client()
con = getdb()
ids = [r[0] for r in con.execute("SELECT DISTINCT clinic_id FROM clinic_day_line WHERE clinic_id<>'' ORDER BY business_date DESC LIMIT 400")]
ids = [i for i in ids if pe.is_patient_id(i)]
random.Random(7).shuffle(ids)
ids = ids[:N]
ok = fail = 0; times = []; with_dx = with_mob = with_bills = with_dz = 0
for cid in ids:
    t0 = time.time(); r = cl.get("/finance/records/p/" + cid); ms = int((time.time() - t0) * 1000); times.append(ms)
    page = r.get_data(as_text=True)
    good = r.status_code == 200 and '<details class="money">' in page and "rvAll(true)" in page and "confirm(" not in page
    ok += bool(good); fail += (not good)
    with_dx += "Diagnosis:</b>" in page; with_bills += "<table class=\"bl\">" in page; with_dz += "Docterz: " in page
    with_mob += bool(re.search(r"ID [A-Za-z0-9\-]+ · <b>\d{10}", page))
print("SHAPE %s ok=%d fail=%d max_ms=%d avg_ms=%d ids=%d with_diagnosis=%d with_bill_tables=%d with_docterz_line=%d with_full_mobile=%d" % (
    "OK" if (ok >= 1 and fail == 0) else "BAD", ok, fail, max(times) if times else 0, (sum(times) // len(times)) if times else 0, len(ids), with_dx, with_bills, with_dz, with_mob))
