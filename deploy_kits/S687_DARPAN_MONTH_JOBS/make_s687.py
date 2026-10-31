#!/usr/bin/env python3
"""make_s687.py -- kit S687_DARPAN_MONTH_JOBS (31-Oct-2026, the parent, session 372). Darpan's monthly jobs.

Builds the four TO files from the box's OWN live bytes:
    python3 -B make_s687.py <root> <outdir>     -> <outdir>/finance/{finance_app.py, aaj_duties.json, aaj_seed.py, month_jobs.py}
    python3 -B make_s687.py --duties            prints the four duties as JSON (the walk reads them)
    python3 -B make_s687.py --lines             prints Darpan's four panel lines as JSON (the walk compares cfg_s687's)
<root> holds finance/... (on the box: /root). Refuses (exit 2, nothing written) unless every FROM pin is exact and
finance/month_jobs.py is NOT there yet. Every edit is anchored on text found EXACTLY ONCE in the real bytes, and counted:
  finance_app.py   1 edit  -- the month_jobs mount block, after the S579_SURGERY_CASES block (nothing else)
  aaj_duties.json  1 edit  -- four 'extra' duties after the last one (kind sql; one read-only SELECT each)
  aaj_seed.py      2 edits -- darpan.paper_renewal joins NO_HOLD; Darpan's four lines at the end of his panel, switched on
  month_jobs.py    NEW     -- copied from the kit beside this script
No .json file is shipped (the repository's .gitignore drops *.json): aaj_duties.json is BUILT here from the box's live bytes."""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {"finance/finance_app.py": "1dd66af3dee7f5724b360e8737c74f0a",
        "finance/aaj_duties.json": "1d085d5873d97beff138b01e15e11577",
        "finance/aaj_seed.py": "2121947f27ce6c5e024b30b0926a898d"}
NEW = "finance/month_jobs.py"
NOW = "date('now','localtime')"          # each duty's clock, written exactly once (the walk moves it)

# ------------------------------------------------------------------------------------------------ the four duties
HOME_SQL = ("WITH t(d) AS (SELECT " + NOW + "), "
            "x(m) AS (SELECT strftime('%Y-%m', date((SELECT d FROM t), '+7 days'))), "
            "f(m) AS (SELECT COALESCE((SELECT s.value FROM mj_setting s WHERE s.key = 'home.floor' AND s.value <> '' ORDER BY s.id DESC LIMIT 1), '2026-11')) "
            "SELECT CASE WHEN (SELECT m FROM x) >= (SELECT m FROM f) AND EXISTS (SELECT 1 FROM mj_home_item i WHERE i.active = 1) "
            "AND NOT EXISTS (SELECT 1 FROM mj_home_count c WHERE c.month = (SELECT m FROM x)) THEN 1 ELSE 0 END AS n, "
            "date((SELECT m FROM x) || '-01', '-7 days') AS since")
VEH_SQL = ("WITH t(d) AS (SELECT " + NOW + "), "
           "x(m) AS (SELECT strftime('%Y-%m', date((SELECT d FROM t), '+1 day', 'start of month', '-1 day'))), "
           "f(m) AS (SELECT COALESCE((SELECT s.value FROM mj_setting s WHERE s.key = 'vehicle.floor' AND s.value <> '' ORDER BY s.id DESC LIMIT 1), '2026-10')) "
           "SELECT CASE WHEN (SELECT m FROM x) >= (SELECT m FROM f) AND EXISTS (SELECT 1 FROM mj_vehicle v WHERE v.active = 1) "
           "AND NOT EXISTS (SELECT 1 FROM mj_vehicle_check c WHERE c.month = (SELECT m FROM x)) THEN 1 ELSE 0 END AS n, "
           "date((SELECT m FROM x) || '-01', '+1 month', '-1 day') AS since")
EXP_SQL = ("WITH t(d) AS (SELECT " + NOW + "), "
           "x(m) AS (SELECT strftime('%Y-%m', date((SELECT d FROM t), '+1 day', 'start of month', '-1 day'))), "
           "f(m) AS (SELECT COALESCE((SELECT s.value FROM mj_setting s WHERE s.key = 'expiry.floor' AND s.value <> '' ORDER BY s.id DESC LIMIT 1), '2026-10')), "
           "r(id) AS (SELECT MAX(id) FROM stock_expiry_run WHERE ok = 1) "
           "SELECT CASE WHEN (SELECT m FROM x) >= (SELECT m FROM f) THEN (SELECT COUNT(*) FROM stock_expiry_line l "
           "WHERE l.run_id = (SELECT id FROM r) AND l.section = 'expired' AND COALESCE(l.units, 0) > 0 "
           "AND substr(COALESCE(l.expiry, ''), 1, 7) <= (SELECT m FROM x) AND NOT EXISTS (SELECT 1 FROM mj_expiry_outcome o "
           "WHERE o.k20 = COALESCE(l.k20, '') AND o.batch = COALESCE(l.batch, '') AND o.expiry = COALESCE(l.expiry, ''))) ELSE 0 END AS n, "
           "date((SELECT m FROM x) || '-01', '+1 month', '-1 day') AS since")
PAPER_SQL = ("WITH t(d) AS (SELECT " + NOW + "), "
             "ld(paper, md) AS (SELECT 'pollution', COALESCE((SELECT s.value FROM mj_setting s WHERE s.key = 'lead.pollution' AND s.value <> '' ORDER BY s.id DESC LIMIT 1), '-7 days') "
             "UNION ALL SELECT 'insurance', COALESCE((SELECT s.value FROM mj_setting s WHERE s.key = 'lead.insurance' AND s.value <> '' ORDER BY s.id DESC LIMIT 1), '-1 month') "
             "UNION ALL SELECT 'rc', COALESCE((SELECT s.value FROM mj_setting s WHERE s.key = 'lead.rc' AND s.value <> '' ORDER BY s.id DESC LIMIT 1), '-45 days')), "
             "cur(rd) AS (SELECT CASE WHEN ld.md LIKE '%month%' THEN MIN(date(p.expiry, ld.md), "
             "date(p.expiry, 'start of month', ld.md, '+1 month', '-1 day')) ELSE date(p.expiry, ld.md) END FROM mj_paper p "
             "JOIN ld ON ld.paper = p.paper JOIN mj_vehicle v ON v.id = p.vehicle_id AND v.active = 1 "
             "WHERE p.id = (SELECT MAX(q.id) FROM mj_paper q WHERE q.vehicle_id = p.vehicle_id AND q.paper = p.paper) AND p.expiry <> '') "
             "SELECT COUNT(*) AS n, MIN(rd) AS since FROM cur WHERE rd IS NOT NULL AND rd <= (SELECT d FROM t)")

DUTIES = [
    {"id": "darpan.home_meds", "person": "darpan", "kind": "sql", "group": "month", "allowed_days": 7, "single": True,
     "hi": "Home medicines — ginti",
     "how_hi": "Mahine ke aakhri hafte se: ghar mein kitni bachi hai, likhiye. Kitni mangwani hai, system bata dega.",
     "en": "Darpan: the home medicines count for the coming month is not saved yet (due since {since})",
     "tile": "Home medicines", "door": "/finance/monthjobs/home", "sql": HOME_SQL,
     "ok_hi": "Home medicines: is mahine ki ginti ho gayi"},
    {"id": "darpan.vehicle_check", "person": "darpan", "kind": "sql", "group": "month", "allowed_days": 3, "single": True,
     "hi": "Gaadi ki jaanch — kaagaz, stepney, jack aur paana",
     "how_hi": "Har gaadi mein dekhiye: kaagaz hain? Stepney, jack aur paana? Jo nahi mila, us par Nahi dabaiye, phir Save.",
     "en": "Darpan: the vehicle check of the month ending {since} is not saved yet",
     "tile": "Gaadi ki jaanch", "door": "/finance/monthjobs/gaadi", "sql": VEH_SQL,
     "ok_hi": "Gaadi ki jaanch: is mahine ki ho gayi"},
    {"id": "darpan.expiry_clear", "person": "darpan", "kind": "sql", "group": "month", "allowed_days": 7,
     "hi": "Expiry ki safai",
     "how_hi": "Expiry wali dawai shelf se hataiye — har ek par likhiye: supplier ko wapas, ya nasht kiya (shelf par na mile to woh bhi).",
     "en": "Darpan: {n} expired medicine line(s) of the newest expiry list without an outcome (month end {since})",
     "tile": "Expiry ki safai", "door": "/finance/monthjobs/expiry", "sql": EXP_SQL,
     "ok_hi": "Expiry ki safai: har dawai ka faisla likha hai"},
    {"id": "darpan.paper_renewal", "person": "darpan", "kind": "sql", "group": "comeup", "allowed_days": 0,
     "hi": "Kaagaz ki yaad",
     "how_hi": "Kholiye: kis gaadi ka kaun sa kaagaz kab khatm ho raha hai. Naya kaagaz banwa kar Dr Manoj ko dijiye — nayi date likhne tak yeh line rahegi.",
     "en": "Vehicle papers to renew: {n} (the first reminder from {since})",
     "tile": "Kaagaz ki yaad", "door": "/finance/monthjobs/kaagaz", "sql": PAPER_SQL,
     "ok_hi": "Kaagaz ki yaad: koi kaagaz khatm nahin ho raha"},
]
# Darpan's panel lines (aaj_seed.PEOPLE['darpan']), on. 'hi' is what he reads, shown as written (aaj_kaam.py fills nothing
# into a panel line); the vehicle and paper of a reminder are on the page the line opens.
LINES = [
    {"id": "darpan.home_meds", "hi": "Home medicines — ginti", "when": "month", "on": True, "opens": "Home medicines",
     "en": "From the last 7 days of the month: what is left at home of each medicine on your list; the page works out what to order."},
    {"id": "darpan.vehicle_check", "hi": "Gaadi ki jaanch — kaagaz, stepney, jack aur paana", "when": "month", "on": True, "opens": "Gaadi ki jaanch",
     "en": "Month end: each vehicle's papers, and the stepney and jack on Wagon R and Vento -- Hai / Nahi."},
    {"id": "darpan.expiry_clear", "hi": "Expiry ki safai", "when": "month", "on": True, "opens": "Expiry ki safai",
     "en": "Month end: each expired line of Sanjeevni's newest expiry list -- returned to the supplier, destroyed, or not found."},
    {"id": "darpan.paper_renewal", "hi": "Kaagaz ki yaad", "when": "comeup", "on": True, "opens": "Kaagaz ki yaad",
     "en": "A vehicle paper inside its reminder time (pollution 7 days, insurance 1 month, RC 45 days) until you enter the new date."},
]

MOUNT_ANCHOR = "# --- S579_SURGERY_CASES end ---\n"
MOUNT = MOUNT_ANCHOR + '''
# --- S687_DARPAN_MONTH_JOBS begin -- Darpan's monthly jobs: home medicines, the vehicle check, the expiry clear-out (owner, 31-Oct-2026) ---
# PARENT. Paths /finance/monthjobs/... -- unit 'medical' by _unit_for_path (darpan maker, the doctor checker); its viewers are refused
# inside the module. Its own mj_* tables, made on the first request (F-303) and by the kit's data step; reads Sanjeevni's
# stock_expiry_run / stock_expiry_line READ ONLY. No rupee amount. GUARDED (S209): a fault inside the module is printed and every
# other page keeps serving.
try:
    import month_jobs                                          # noqa: E402
    month_jobs.init(app, db, require, audit, unit=UNIT)
except Exception as _ex_mj:                                    # noqa: BLE001
    _MOUNT_FAILED.append(('month_jobs', repr(_ex_mj)[:200]))
    print("month_jobs NOT mounted: %s" % _ex_mj, file=sys.stderr)
# --- S687_DARPAN_MONTH_JOBS end ---
'''
DUTIES_ANCHOR = '"fetch": {"url": "/scanapp/procroom/morning/api/open", "field": "open", "text_field": "text"}\n  }\n ]\n}'
NOHOLD_OLD = 'NO_HOLD = ("shavez.sale_report", "shavez.closing_stock", "bhati.availability", "shavez.month_reports")\n'
NOHOLD_NEW = ('NO_HOLD = ("shavez.sale_report", "shavez.closing_stock", "bhati.availability", "shavez.month_reports",\n'
              '           "darpan.paper_renewal")   # S687: a paper is due NOW, however early its reminder day fell\n')
LINES_ANCHOR = ("             'why': 'Held off for now: the Vaapsi Desk page it opens still shows September. Switch it on when that page "
                "starts from 1 October.'}]}]\n\nSEPT = [\n")


def rep(s, a, b, what, counter):
    n = s.count(a)
    if n != 1:
        raise SystemExit("make_s687: %s: anchor found %d times (must be exactly once) -- STOP, nothing written" % (what, n))
    counter.append(what)
    return s.replace(a, b)


def seed_lines_text():
    out = []
    for ln in LINES:
        out.append("            {'id': %r,                       # S687 (31-Oct-2026): the owner's monthly jobs for Darpan\n"
                   "             'hi': %r,\n             'en': %r,\n             'when': %r,\n             'on': True,\n"
                   "             'opens': %r}" % (ln["id"], ln["hi"], ln["en"], ln["when"], ln["opens"]))
    return ",\n".join(out)


def build(root, out):
    got = {}
    for f, pin in FROM.items():
        p = os.path.join(root, f)
        if not os.path.isfile(p):
            raise SystemExit("make_s687: %s is missing -- STOP, nothing written" % p)
        b = open(p, "rb").read()
        h = hashlib.md5(b).hexdigest()
        if h != pin:
            raise SystemExit("make_s687: %s is %s, not its FROM %s -- STOP, nothing written" % (f, h[:8], pin[:8]))
        got[f] = b.decode("utf-8")
    if os.path.exists(os.path.join(root, NEW)):
        raise SystemExit("make_s687: %s is already there -- STOP, nothing written" % os.path.join(root, NEW))
    kit_mj = os.path.join(HERE, "month_jobs.py")
    mj = open(kit_mj, "rb").read()
    edits = []

    a = got["finance/finance_app.py"]
    if "S687_DARPAN_MONTH_JOBS" in a or "import month_jobs" in a:
        raise SystemExit("make_s687: finance_app.py already names month_jobs -- STOP")
    a = rep(a, MOUNT_ANCHOR, MOUNT, "finance_app.py: the mount block after S579", edits)
    compile(a, "finance_app.py", "exec")

    j = got["finance/aaj_duties.json"]
    for d in DUTIES:
        if '"id": "%s"' % d["id"] in j:
            raise SystemExit("make_s687: aaj_duties.json already holds %s -- STOP" % d["id"])
    blocks = ",\n".join("\n".join("  " + ln for ln in json.dumps(d, indent=1, ensure_ascii=False).splitlines()) for d in DUTIES)
    j = rep(j, DUTIES_ANCHOR, DUTIES_ANCHOR[:-len("\n ]\n}")] + ",\n" + blocks + "\n ]\n}", "aaj_duties.json: four duties at the end", edits)
    dj = json.loads(j)
    ids = [x.get("id") for x in dj["extra"]]
    assert len(ids) == len(set(ids)), "duties: ids not unique"
    for d in DUTIES:
        assert [x for x in dj["extra"] if x.get("id") == d["id"]] == [d], "duties: %s did not read back" % d["id"]
        assert d["sql"].count(NOW) == 1 and ";" not in d["sql"], "duties: %s clock" % d["id"]

    t = got["finance/aaj_seed.py"]
    for d in DUTIES:
        if d["id"] in t:
            raise SystemExit("make_s687: aaj_seed.py already names %s -- STOP" % d["id"])
    t = rep(t, NOHOLD_OLD, NOHOLD_NEW, "aaj_seed.py: darpan.paper_renewal joins NO_HOLD", edits)
    t = rep(t, LINES_ANCHOR, LINES_ANCHOR.replace("}]}]\n\nSEPT", "},\n" + seed_lines_text() + "]}]\n\nSEPT"),
            "aaj_seed.py: Darpan's four lines, on", edits)
    compile(t, "aaj_seed.py", "exec")
    ns = {}
    exec(compile(t, "aaj_seed.py", "exec"), ns)                       # noqa: S102 -- our own built seed, read back
    dp = [p for p in ns["PEOPLE"] if p["key"] == "darpan"][0]
    for ln in LINES:
        assert [x for x in dp["lines"] if x["id"] == ln["id"]] == [ln], "seed: %s did not read back" % ln["id"]
    assert "darpan.paper_renewal" in ns["NO_HOLD"]
    compile(mj.decode("utf-8"), "month_jobs.py", "exec")
    if len(edits) != 4:
        raise SystemExit("make_s687: %d edits, expected 4 -- STOP" % len(edits))

    outs = {"finance/finance_app.py": a.encode("utf-8"), "finance/aaj_duties.json": j.encode("utf-8"),
            "finance/aaj_seed.py": t.encode("utf-8"), NEW: mj}
    for f, b in outs.items():
        p = os.path.join(out, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(b)
    for e in edits:
        print("edit ok: %s" % e)
    for f, b in sorted(outs.items()):
        print("built %s %s" % (f, hashlib.md5(b).hexdigest()))
    print("make_s687: 4 counted edits, each anchor found exactly once; 4 files written")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--duties"]:
        print(json.dumps(DUTIES, ensure_ascii=False))
    elif sys.argv[1:2] == ["--lines"]:
        print(json.dumps(LINES, ensure_ascii=False))
    elif len(sys.argv) == 3:
        build(sys.argv[1], sys.argv[2])
    else:
        raise SystemExit(__doc__)
