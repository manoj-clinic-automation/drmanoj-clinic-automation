#!/usr/bin/env python3
"""make_s688.py -- kit S688_XRAY_FILM_LOG (31-Oct-2026, the parent, session 372). The X-ray film log.

Builds the four TO files from the box's OWN live bytes (S687's TO files are this kit's FROM):
    python3 -B make_s688.py <root> <outdir>     -> <outdir>/finance/{finance_app.py, aaj_duties.json, aaj_seed.py, xray_film.py}
    python3 -B make_s688.py --duties            prints the four duties as JSON (the walk reads them)
    python3 -B make_s688.py --lines             prints the panel lines as JSON ({person: [lines]})
<root> holds finance/... (on the box: /root). Refuses (exit 1, nothing written) unless every FROM pin is exact (S687's
month_jobs.py too: read, never changed) and finance/xray_film.py is NOT there yet. Every edit is anchored on text found
EXACTLY ONCE in the real bytes, and counted:
  finance_app.py   1 edit  -- the xray_film mount block, after the S687_DARPAN_MONTH_JOBS block (nothing else)
  aaj_duties.json  2 edits -- four 'extra' duties after the last one (kind sql; one read-only SELECT each, xf_* tables only);
                             the weekly tick reception.week_film_stock RETIRED (the owner, 20:20 IST 31-Oct-2026: the machine
                             shows the films loaded) -- its duty taken out; its duty_tick history rows are never touched
  aaj_seed.py      3 edits -- Shavez's three lines at the end of his panel; Reception's one line at the end of hers; all on;
                             the retired weekly line taken off Reception's panel
  xray_film.py     NEW     -- copied from the kit beside this script
No .json file is shipped (the repository's .gitignore drops *.json): aaj_duties.json is BUILT here from the box's live bytes."""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {"finance/finance_app.py": "9ce1b67f622ae0172422c2a38c5a57b5",
        "finance/aaj_duties.json": "0adf1a84042e7efc198a3f39ad44d032",
        "finance/aaj_seed.py": "73b8556afcb5f3b1cd0826e038abd797"}
KEEP = {"finance/month_jobs.py": "33fa557f44dc4fbd53cf45b198cf5c2e"}     # S687's module: must be there, never changed
NEW = "finance/xray_film.py"
NOW = "datetime('now','localtime')"      # each duty's clock, written exactly once (the walk moves it)


def _set(key, default):
    return ("COALESCE((SELECT s.value FROM xf_setting s WHERE s.key = '%s' AND s.value <> '' ORDER BY s.id DESC LIMIT 1), '%s')"
            % (key, default))


# ------------------------------------------------------------------------------------------------ the four duties
def count_sql(standin):
    """Today's morning count not saved (both sizes), from setting count.from, never on a Sunday; the stand-in from a time."""
    return ("WITH t(ts) AS (SELECT " + NOW + "), d(day) AS (SELECT date((SELECT ts FROM t))) "
            "SELECT CASE WHEN (SELECT day FROM d) >= " + _set("count.from", "2026-11-01") + " "
            "AND strftime('%w', (SELECT day FROM d)) <> '0' "
            + ("AND time((SELECT ts FROM t)) >= " + _set("standin.after", "11:00") + " " if standin else "") +
            "AND (SELECT COUNT(DISTINCT c.size) FROM xf_count c WHERE c.day = (SELECT day FROM d) AND c.void = 0 "
            "AND c.id = (SELECT MAX(q.id) FROM xf_count q WHERE q.size = c.size AND q.day = c.day)) < 2 THEN 1 ELSE 0 END AS n, "
            "(SELECT day FROM d) AS since")


def order_sql(size):
    """The size's films left (the newest figure typed from the machine's screen) under the set days of use (the 30-day average)
    AND no SPARE box of that size (spare <= 0): from setting spare.from -- the opening boxes, + every box billed, - one per box
    load the figures show (a figure HIGHER than the one before); NOT floored (boxes loaded before their bills are owed); a bill
    HELD for its quantity (read above bill.max_boxes, not yet confirmed by the owner) never counts.
    Used between two figures: previous - today, or on a box load previous + (box films - today), never below 0. The same rule as
    xray_film.size_state()."""
    return ("WITH t(ts) AS (SELECT " + NOW + "), d(day) AS (SELECT date((SELECT ts FROM t))), "
            "cfg(nd, pb) AS (SELECT CAST(" + _set("order.days", "10") + " AS REAL), CAST(" + _set("box.films", "150") + " AS INTEGER)), "
            "cur(day, r) AS (SELECT c.day, c.remaining FROM xf_count c WHERE c.size = '" + size + "' AND c.day <= (SELECT day FROM d) "
            "AND c.void = 0 AND c.id = (SELECT MAX(q.id) FROM xf_count q WHERE q.size = c.size AND q.day = c.day)), "
            "u(day, used, ld) AS (SELECT day, CASE WHEN LAG(r) OVER (ORDER BY day) IS NULL THEN NULL "
            "WHEN r <= LAG(r) OVER (ORDER BY day) THEN LAG(r) OVER (ORDER BY day) - r "
            "ELSE MAX(0, LAG(r) OVER (ORDER BY day) + (SELECT pb FROM cfg) - r) END, "
            "CASE WHEN LAG(r) OVER (ORDER BY day) IS NOT NULL AND r > LAG(r) OVER (ORDER BY day) THEN 1 ELSE 0 END FROM cur), "
            "lt(r) AS (SELECT r FROM cur ORDER BY day DESC LIMIT 1), "
            "w(d0) AS (SELECT MIN(day) FROM cur WHERE day >= date((SELECT day FROM d), '-30 days')), "
            "av(a) AS (SELECT CASE WHEN COUNT(used) > 0 AND julianday(MAX(day)) - julianday((SELECT d0 FROM w)) >= 3 "
            "THEN SUM(used) * 1.0 / (julianday(MAX(day)) - julianday((SELECT d0 FROM w))) END FROM u WHERE day > (SELECT d0 FROM w)), "
            "st0(d0, op) AS (SELECT " + _set("spare.from", "2026-11-01") + ", CAST(" + _set("spare.open." + size, "0") + " AS REAL)), "
            "sp(n) AS (SELECT (SELECT op FROM st0) + COALESCE((SELECT SUM(COALESCE(p.boxes, 1)) FROM xf_purchase p WHERE p.size = '" + size + "' "
            "AND p.gone_at = '' AND p.held = 0 AND p.bill_day >= (SELECT d0 FROM st0) AND p.bill_day <= (SELECT day FROM d)), 0) "
            "- (SELECT COUNT(*) FROM u WHERE u.ld = 1 AND u.day >= (SELECT d0 FROM st0))) "
            "SELECT CASE WHEN EXISTS (SELECT 1 FROM lt) AND (SELECT a FROM av) > 0 AND (SELECT r FROM lt) < (SELECT a FROM av) * (SELECT nd FROM cfg) "
            "AND (SELECT n FROM sp) <= 0 THEN 1 ELSE 0 END AS n, (SELECT MAX(day) FROM cur) AS since")


DOOR_COUNT = "/finance/slips/film/subah"
DOOR_LOG = "/finance/slips/film/log"
DUTIES = [
    {"id": "reception.xray_film_count", "person": "alisha", "kind": "sql", "group": "first", "allowed_days": 0,
     "single": True, "hi": "X-ray film: machine mein kitni film bachi hain, likhiye (dono size)",
     "how_hi": "Machine ki screen par jitni film bachi dikh rahi hain, wahi likhiye — 8×10 aur 11×14 dono, phir Save. Farq ka koi kaaran nahi poochha jaata.",
     "en": "Reception: the X-ray film count of {since} is not saved yet", "tile": "X-ray film", "door": DOOR_COUNT,
     "sql": count_sql(False), "ok_hi": "X-ray film: aaj ki bachi film likh di gayi"},
    {"id": "shavez.xray_film_count", "person": "shavez", "kind": "sql", "group": "day", "allowed_days": 0, "single": True,
     "hi": "X-ray film ginti: reception nahi hai to aap likhiye",
     "how_hi": "Reception ne abhi tak bachi film nahi likhi. Machine ki screen par dono size ki bachi film dekh kar likhiye.",
     "en": "Shavez (stand-in): the X-ray film count of {since} is still not saved", "tile": "X-ray film", "door": DOOR_COUNT,
     "sql": count_sql(True), "ok_hi": "X-ray film: aaj ki bachi film likh di gayi"},
    {"id": "shavez.xray_film_order_8x10", "person": "shavez", "kind": "sql", "group": "comeup", "allowed_days": 0, "single": True,
     "hi": "8×10 film mangwaiye — 1 box",
     "how_hi": "Kholiye: 8×10 ka haal wahin likha hai — supplier ka WhatsApp button, aur koi bill abhi scan hona baaki ho to woh bhi.",
     "en": "Order 8×10 X-ray film — 1 box: the films left on the machine last under the set days and no spare box (Shavez; count of {since})",
     "tile": "X-ray film log", "door": DOOR_LOG, "sql": order_sql("8x10"), "ok_hi": "8×10 film: box mein kaafi film hai"},
    {"id": "shavez.xray_film_order_11x14", "person": "shavez", "kind": "sql", "group": "comeup", "allowed_days": 0, "single": True,
     "hi": "11×14 film mangwaiye — 1 box",
     "how_hi": "Kholiye: 11×14 ka haal wahin likha hai — supplier ka WhatsApp button, aur koi bill abhi scan hona baaki ho to woh bhi.",
     "en": "Order 11×14 X-ray film — 1 box: the films left on the machine last under the set days and no spare box (Shavez; count of {since})",
     "tile": "X-ray film log", "door": DOOR_LOG, "sql": order_sql("11x14"), "ok_hi": "11×14 film: box mein kaafi film hai"},
]
IDS = tuple(d["id"] for d in DUTIES)
LINES = {
    "shavez": [
        {"id": "shavez.xray_film_count", "hi": "X-ray film ginti: reception nahi hai to aap likhiye", "when": "day", "on": True,
         "opens": "X-ray film", "en": "Stand-in: the morning film count, when reception has not saved it by 11:00."},
        {"id": "shavez.xray_film_order_8x10", "hi": "8×10 film mangwaiye — 1 box", "when": "comeup", "on": True, "opens": "X-ray film log",
         "en": "The 8×10 films left last under 10 days and no spare box: order one box. The page it opens says if a bill is still to be scanned."},
        {"id": "shavez.xray_film_order_11x14", "hi": "11×14 film mangwaiye — 1 box", "when": "comeup", "on": True, "opens": "X-ray film log",
         "en": "The 11×14 films left last under 10 days and no spare box: order one box. The page it opens says if a bill is still to be scanned."},
    ],
    "reception": [
        {"id": "reception.xray_film_count", "hi": "X-ray film: machine mein kitni film bachi hain, likhiye (dono size)", "when": "first", "on": True,
         "opens": "X-ray film", "en": "Each morning: the films left on the Fuji machine's screen for 8×10 and 11×14, one Save."},
    ],
}

MOUNT_ANCHOR = "# --- S687_DARPAN_MONTH_JOBS end ---\n"
MOUNT = MOUNT_ANCHOR + '''
# --- S688_XRAY_FILM_LOG begin -- the X-ray film log: the morning count, the boxes, the gap, the order line, the X-ray list (owner, 31-Oct-2026) ---
# PARENT. Paths /finance/slips/film/... -- unit 'slips' by _unit_for_path (shavez, alisha, shivani makers; the doctors checkers;
# other slips logins refused inside the module). Its own xf_* tables, made on the first request (F-303) and by the kit's data
# step; reads slip / slip_item / owner_service and the Scan App's assets.db READ ONLY. GUARDED (S209): a fault inside the
# module is printed and every other page keeps serving.
try:
    import xray_film                                           # noqa: E402
    xray_film.init(app, db, require, audit, unit="slips")
except Exception as _ex_xf:                                    # noqa: BLE001
    _MOUNT_FAILED.append(('xray_film', repr(_ex_xf)[:200]))
    print("xray_film NOT mounted: %s" % _ex_xf, file=sys.stderr)
# --- S688_XRAY_FILM_LOG end ---
'''
DUTIES_ANCHOR = '"ok_hi": "Kaagaz ki yaad: koi kaagaz khatm nahin ho raha"\n  }\n ]\n}'
SHAVEZ_ANCHOR = "             'opens': 'Kal ke procedures'}]},\n {'key': 'amir',\n"
RECEPTION_ANCHOR = "             'opens': 'Day check'}]},\n {'key': 'darpan',\n"
RETIRED = "reception.week_film_stock"           # the owner's ruling, 20:20 IST 31-Oct-2026
RETIRE_DUTY = ('  {\n   "id": "reception.week_film_stock",\n   "person": "alisha",\n   "kind": "tick",\n   "period": "week",\n'
               '   "group": "week",\n   "hi": "X-ray film ka stock gina (dono size)",\n   "en": "Reception: X-ray film stock counted, both sizes '
               '(weekly)",\n   "tile": null,\n   "door": null\n  },\n')
RETIRE_LINE = ("            {'id': 'reception.week_film_stock',\n             'hi': 'X-ray film ka stock giniye (dono size)',\n"
               "             'en': 'X-ray film stock counted, both sizes.',\n             'when': 'week',\n             'on': True,\n"
               "             'opens': ''},\n")


def rep(s, a, b, what, counter):
    n = s.count(a)
    if n != 1:
        raise SystemExit("make_s688: %s: anchor found %d times (must be exactly once) -- STOP, nothing written" % (what, n))
    counter.append(what)
    return s.replace(a, b)


def seed_lines_text(person):
    out = []
    for ln in LINES[person]:
        out.append("            {'id': %r,                       # S688 (31-Oct-2026): the owner's X-ray film log (films left)\n"
                   "             'hi': %r,\n             'en': %r,\n             'when': %r,\n             'on': True,\n"
                   "             'opens': %r}" % (ln["id"], ln["hi"], ln["en"], ln["when"], ln["opens"]))
    return ",\n".join(out)


def seed_edit(anchor, person):
    head, tail = anchor.split("}]},\n", 1)
    return anchor, head + "},\n" + seed_lines_text(person) + "]},\n" + tail


def build(root, out):
    got = {}
    for f, pin in list(FROM.items()) + list(KEEP.items()):
        p = os.path.join(root, f)
        if not os.path.isfile(p):
            raise SystemExit("make_s688: %s is missing -- STOP, nothing written" % p)
        b = open(p, "rb").read()
        h = hashlib.md5(b).hexdigest()
        if h != pin:
            raise SystemExit("make_s688: %s is %s, not its FROM %s -- STOP, nothing written" % (f, h[:8], pin[:8]))
        got[f] = b.decode("utf-8")
    if os.path.exists(os.path.join(root, NEW)):
        raise SystemExit("make_s688: %s is already there -- STOP, nothing written" % os.path.join(root, NEW))
    xf = open(os.path.join(HERE, "xray_film.py"), "rb").read()
    edits = []

    a = got["finance/finance_app.py"]
    if "S688_XRAY_FILM_LOG" in a or "import xray_film" in a:
        raise SystemExit("make_s688: finance_app.py already names xray_film -- STOP")
    a = rep(a, MOUNT_ANCHOR, MOUNT, "finance_app.py: the mount block after S687", edits)
    compile(a, "finance_app.py", "exec")

    j = got["finance/aaj_duties.json"]
    for d in DUTIES:
        if '"id": "%s"' % d["id"] in j:
            raise SystemExit("make_s688: aaj_duties.json already holds %s -- STOP" % d["id"])
    blocks = ",\n".join("\n".join("  " + ln for ln in json.dumps(d, indent=1, ensure_ascii=False).splitlines()) for d in DUTIES)
    j = rep(j, DUTIES_ANCHOR, DUTIES_ANCHOR[:-len("\n ]\n}")] + ",\n" + blocks + "\n ]\n}", "aaj_duties.json: the duties at the end", edits)
    j = rep(j, RETIRE_DUTY, "", "aaj_duties.json: the weekly film-stock tick retired", edits)
    dj = json.loads(j)
    ids = [x.get("id") for x in dj["extra"]]
    assert len(ids) == len(set(ids)), "duties: ids not unique"
    for d in DUTIES:
        assert [x for x in dj["extra"] if x.get("id") == d["id"]] == [d], "duties: %s did not read back" % d["id"]
        assert d["sql"].count(NOW) == 1 and ";" not in d["sql"], "duties: %s clock" % d["id"]

    t = got["finance/aaj_seed.py"]
    for d in DUTIES:
        if d["id"] in t:
            raise SystemExit("make_s688: aaj_seed.py already names %s -- STOP" % d["id"])
    t = rep(t, *seed_edit(SHAVEZ_ANCHOR, "shavez"), "aaj_seed.py: Shavez's three lines, on", edits)
    t = rep(t, *seed_edit(RECEPTION_ANCHOR, "reception"), "aaj_seed.py: Reception's line, on", edits)
    t = rep(t, RETIRE_LINE, "", "aaj_seed.py: the weekly film-stock line off Reception's panel", edits)
    compile(t, "aaj_seed.py", "exec")
    ns = {}
    exec(compile(t, "aaj_seed.py", "exec"), ns)                       # noqa: S102 -- our own built seed, read back
    for person, lines in LINES.items():
        pp = [p for p in ns["PEOPLE"] if p["key"] == person][0]
        for ln in lines:
            assert [x for x in pp["lines"] if x["id"] == ln["id"]] == [ln], "seed: %s did not read back" % ln["id"]
        assert pp["lines"][-len(lines):] == lines, "seed: %s's lines not at the end" % person
    assert not [x for p in ns["PEOPLE"] for x in p["lines"] if x["id"] == RETIRED], "seed: the retired line is still on a panel"
    assert not [x for x in dj["extra"] if x.get("id") == RETIRED] and RETIRED not in j, "duties: the retired tick is still there"
    compile(xf.decode("utf-8"), "xray_film.py", "exec")
    if len(edits) != 6:
        raise SystemExit("make_s688: %d edits, expected 6 -- STOP" % len(edits))

    outs = {"finance/finance_app.py": a.encode("utf-8"), "finance/aaj_duties.json": j.encode("utf-8"),
            "finance/aaj_seed.py": t.encode("utf-8"), NEW: xf}
    for f, b in outs.items():
        p = os.path.join(out, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(b)
    for e in edits:
        print("edit ok: %s" % e)
    for f, b in sorted(outs.items()):
        print("built %s %s" % (f, hashlib.md5(b).hexdigest()))
    print("make_s688: 6 counted edits, each anchor found exactly once; 4 files written")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--duties"]:
        print(json.dumps(DUTIES, ensure_ascii=False))
    elif sys.argv[1:2] == ["--lines"]:
        print(json.dumps(LINES, ensure_ascii=False))
    elif len(sys.argv) == 3:
        build(sys.argv[1], sys.argv[2])
    else:
        raise SystemExit(__doc__)
