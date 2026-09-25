#!/usr/bin/env python3
"""walk_s398.py -- kit S398_SLIP_DEAD_CODE. S398 only deletes code nobody can reach, so the proof is sameness:
the kit's slip_log.py and the live one (S392, the control) are mounted side by side, each over ITS OWN scratch copy
of the live finance.db, with the clock pinned; every page a person can open is fetched from both as each role, and
the two answers must be identical byte for byte (status, redirect target and body). The two retired doors are posted
to as well. Prints counts only -- never a page, a name or a number.
Usage: python3 walk_s398.py <kit slip_log.py> <live slip_log.py> <scratch db A> <scratch db B>"""
import datetime as dt, hashlib, importlib.util, os, sqlite3, sys
new_p, live_p, dba, dbb = [os.path.abspath(x) for x in sys.argv[1:5]]
for d in (dba, dbb):
    assert "walk" in d or "scratch" in d or d.startswith("/tmp"), "refusing a non-scratch database"
os.environ["SLIP_NOW"] = os.environ.get("WALK_NOW", dt.datetime.now().replace(microsecond=0).isoformat())
os.environ.setdefault("FINANCE_CRON_TOKEN", "walk-s398-token")
N = [0]


def ok(c, label):
    N[0] += 1
    if not c:
        print("WALK RED %d: %s" % (N[0], label)); sys.exit(1)


from flask import Flask
USER = {"u": None}


def build(path, tag, dbp):
    s = importlib.util.spec_from_file_location("slip_log_" + tag, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    a = Flask("w" + tag)

    def dbg():
        c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row; return c

    def req(*roles, **kw):
        u = USER["u"]
        if not set(u["roles"]) & set(roles):
            from flask import jsonify
            return None, (jsonify(ok=False, error="not_permitted"), 403)
        return u, None
    m.init(a, dbg, req, None, unit="slips")
    return a, m


A, SA = build(new_p, "new", dba)
B, SB = build(live_p, "live", dbb)
ca, cb = A.test_client(), B.test_client()
ok({r.rule for r in A.url_map.iter_rules()} == {r.rule for r in B.url_map.iter_rules()}, "the same doors as S392")
ok(not any(hasattr(SA, n) for n in ("emr_items", "emr_pending_count", "_emr_html", "_BLOOD_ASKING")), "the dead helpers are gone")
today = dt.date.fromisoformat(os.environ["SLIP_NOW"][:10])
con = sqlite3.connect(dba)
ids = [r[0] for r in con.execute("SELECT DISTINCT clinic_id FROM blood_order WHERE clinic_id<>'' ORDER BY id DESC LIMIT 3")]
con.close()
paths = ["/finance/slips", "/finance/slips?tile=1", "/finance/slips/pending", "/finance/slips/blood",
         "/finance/slips/report", "/finance/slips/api/pending-counts", "/finance/slips/emr", "/finance/slips/emr?ok=x"]
paths += ["/finance/slips?s=%s" % k for k in ("opd", "xp", "room", "list", "book", "all")]
paths += ["/finance/slips/report/%s" % (today - dt.timedelta(days=i)).isoformat() for i in range(0, 10)]
paths += ["/finance/slips/api/patient?id=%s" % i for i in ids]
roles = [("sukhveer", ["maker"]), ("manoj", ["checker"]), ("viewer1", ["viewer"]), ("nobody", ["none"])]
pages = 0
for who, rl in roles:
    USER["u"] = {"user": who, "roles": rl}
    for p in paths:
        ra, rb = ca.get(p), cb.get(p)
        same = (ra.status_code, ra.headers.get("Location"), ra.get_data()) == (rb.status_code, rb.headers.get("Location"), rb.get_data())
        ok(same, "GET %s as %s differs (%d vs %d)" % (p.split("?")[0], rl[0], ra.status_code, rb.status_code))
        pages += 1
    for p in ("/finance/slips/emr/mark",):
        ra, rb = ca.post(p, data={"act": "done", "key": "xi:1"}), cb.post(p, data={"act": "done", "key": "xi:1"})
        ok((ra.status_code, ra.headers.get("Location")) == (rb.status_code, rb.headers.get("Location")), "POST %s as %s differs" % (p, rl[0]))
        pages += 1
# the two databases must still be alike in every table the retired code could have written
ta, tb = sqlite3.connect(dba), sqlite3.connect(dbb)
for t in ("emr_upload", "blood_order", "lab_report", "lab_noid", "slip"):
    try:
        ha = hashlib.md5(repr(ta.execute("SELECT * FROM %s ORDER BY rowid" % t).fetchall()).encode()).hexdigest()
        hb = hashlib.md5(repr(tb.execute("SELECT * FROM %s ORDER BY rowid" % t).fetchall()).encode()).hexdigest()
    except sqlite3.OperationalError:
        continue
    ok(ha == hb, "table %s ended different" % t)
print("WALK OK %d/%d checks (%d answers compared byte for byte, %d clinic IDs looked up)" % (N[0], N[0], pages, len(ids)))
