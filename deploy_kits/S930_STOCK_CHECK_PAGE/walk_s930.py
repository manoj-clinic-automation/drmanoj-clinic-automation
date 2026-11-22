#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s930.py -- kit S930_STOCK_CHECK_PAGE (22-Nov-2026, Sanjeevni session 503). MADE-UP data only, in a scratch folder.
    python3 -B walk_s930.py <dir with the files under test> <schema-from: a COPY of finance.db> <kit928 dir holding synth_s928.py> [--control]
The S928 synth's fixtures (a scratch finance.db with the copy's schema, a made-up spine, made-up scans and orders of 'W928 PHARMA') and the
Stock check module mounted on a bare Flask app with a header-free stub login (doctor). Checks the page, its doors, the retired addresses'
redirect, the Needs-you href, the Hub's Go to line. --control runs on the OLD files and must go red. No patient data; no long number printed.
Prints 'RESULT: ALL PASS' | 'RESULT: n FAIL'."""
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

RUN, FAILS = [0], []


def say(s):
    print(re.sub(r"\d{8,}", lambda m: "#" * len(m.group(0)), str(s)), flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("ok   " if cond else "FAIL ") + label + (("  [%s]" % str(got)[:300]) if (got is not None and not cond) else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def main():
    fin, copy, k928 = (os.path.abspath(x) for x in sys.argv[1:4])
    control = "--control" in sys.argv
    scratch = tempfile.mkdtemp(prefix="s930_", dir=os.environ.get("TMPDIR") or "/tmp")
    try:
        run(fin, copy, k928, control, scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    say("RESULT: %s" % ("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS)))
    sys.exit(0 if not FAILS else 1)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(fin, copy, k928, control, scratch):
    SY = load("synth_s928_fixtures", os.path.join(k928, "synth_s928.py"))
    dbp, spp, adb = os.path.join(scratch, "fin.db"), os.path.join(scratch, "spine.db"), os.path.join(scratch, "assets.db")
    con = SY.schema_from(copy, dbp)
    SY.make_spine(fin, spp)
    SY.make_assets(adb)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=adb, SPINE_DB=spp, PYTHONDONTWRITEBYTECODE="1")
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != here]
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import purchase_app as PA                                 # noqa: E402
    assert SW.__file__.startswith(fin) and SF.__file__.startswith(fin)
    PA._assets_db = adb
    say("-- S930 walk on the %s files: %s" % ("OLD (control)" if control else "new", fin))
    SW.ensure(con)
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('order.track_since','2026-10-12')")
    con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, supplier_norm) VALUES (1,'2026-11-19T09:00:00','walk','W928 PHARMA','sent','W928 PHARMA')")
    L = "INSERT INTO purchase_order_line (id, order_id, item, packs, pack_size, units, supplied, arrived_at, arrived_by) VALUES (?,?,?,?,?,?,?,?,?)"
    con.execute(L, (11, 1, "W928 ALFA 10", 30, 10, 300, 30, "2026-11-21T11:00:00", "reception"))
    con.execute(L, (12, 1, "W928 BETA 10", 10, 10, 100, 10, "2026-11-21T11:00:00", "reception"))
    con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (1,501,'B-9501','2026-11-21T10:30:00','2026-11-21T10:31:00','walk',1)")
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES ('W928 ALFA 10','W928 ALFA 10','2026-11-20T10:00:00',100,'spot','darpan','settled')")
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES ('W928 EPS 10','W928 EPS 10','2026-11-21T19:49:00',90,'spot','darpan','settled')")
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES ('W928 MOR 10','W928 MOR 10','2026-11-21T10:40:00',70,'spot','darpan','settled')")
    con.execute("INSERT INTO stock_count (id, unit, marg_as_on, bill_no, bill_date, started_at, submitted_at, submitted_by, items_total, items_counted, status) VALUES (7,'medical','2026-09-06','W','06-09-2026','2026-09-06T10:00:00','2026-09-06T18:00:00','walk',1,1,'submitted')")
    con.execute("INSERT INTO stock_count_item (count_id, item, pack_size, marg_qty, counted_qty, at) VALUES (7,'W928 OLDNAME 10',10,10,12,'2026-09-06T12:00:00')")   # a count name Marg no longer prints
    con.commit()
    con.close()

    try:
        import flask                                          # noqa: E402
    except ImportError:
        check("flask importable", False)
        return
    app = flask.Flask("w929")
    app.config["TESTING"] = True

    def dbg():
        c = sqlite3.connect(dbp, timeout=30)
        return c

    ASKED = {}

    def require(*roles):
        from flask import request as _rq                     # noqa: PLC0415
        ASKED[_rq.path] = tuple(roles)
        return dict(user="manoj", role="doctor"), None

    @app.route("/finance/stock/page/drift")
    def _old_drift():
        return "OLD DRIFT PAGE", 200

    try:
        import stock_check as SC                              # noqa: E402
        ok_mod = SC.__file__.startswith(fin)
    except ImportError:
        SC, ok_mod = None, False
    check("C: stock_check.py is beside the finance code and imports", ok_mod)
    if SC is None:
        # the control's remaining checks
        check("C: the Needs-you count line carries an href to the page", False)
        check("C: the Hub's Go to names the Stock check page", "/finance/stockcheck/" in open(os.path.join(fin, "finance_ui", "finance_approvals.html"), encoding="utf-8").read())
        return
    SC.init(app, dbg, require)
    cl = app.test_client()
    r = cl.get("/finance/stockcheck/")
    r_page_text = r.get_data(as_text=True)
    check("C: the page answers 200 with its title and no dialog", r.status_code == 200 and "Stock check" in r.get_data(as_text=True) and "confirm(" not in r.get_data(as_text=True) and "alert(" not in r.get_data(as_text=True), r.status_code)
    r = cl.get("/finance/stock/page/drift", follow_redirects=False)
    check("C: the retired Stock drift address sends to the page (302)", r.status_code == 302 and r.headers.get("Location", "").endswith("/finance/stockcheck/"), (r.status_code, r.headers.get("Location")))
    r = cl.get("/finance/stock/page/now", follow_redirects=False)
    check("C: the retired Stock now address sends to the page (302)", r.status_code == 302, r.status_code)
    r = cl.get("/finance/stockcheck/api/healthz")
    check("C: healthz names the kit and finds the page file", r.status_code == 200 and r.get_json().get("kit") == "S930_STOCK_CHECK_PAGE" and r.get_json().get("page") is True, r.get_data(as_text=True)[:200])
    r = cl.get("/finance/stockcheck/api/rows")
    J = r.get_json() or {}
    check("C: api/rows answers ok with the made-up items", r.status_code == 200 and J.get("ok") and len(J.get("rows") or []) == 10, (r.status_code, J.get("reason"), len(J.get("rows") or [])))
    rows = {x["item"]: x for x in (J.get("rows") or [])}
    A = rows.get("W928 ALFA 10") or {}
    check("C: ALFA -- Marg 30:0, shelf (the count carried forward) 10:0, waiting +20:0 by the bill, real difference -20:0",
          A.get("marg_t") == "30:0" and A.get("core_t") == "10:0" and A.get("arrived_t") == "+20:0" and A.get("gap_t") == "−20:0", {k: A.get(k) for k in ("marg_t", "core_t", "arrived_t", "gap_t")})
    L1 = (A.get("lines") or [])
    check("C: ALFA's delivery line reads the tap against the bill: '10:0 short, back on W928's next order'", len(L1) == 1 and "10:0 short" in L1[0]["word"] and L1[0]["short"] == -100.0, L1)
    B = rows.get("W928 BETA 10") or {}
    check("C: BETA (tapped, not on the bill): no shelf figure (never counted), nothing waiting", B.get("shelf") is None and not B.get("arrived"), {k: B.get(k) for k in ("shelf", "arrived")})
    E = rows.get("W928 EPS 10") or {}
    check("C: EPS -- the evening count is marked, shelf 8:5 (90 - 5), Marg 8:5 -> gap 0, agrees", E.get("evening") is True and E.get("core_t") == "8:5" and E.get("gap") == 0, {k: E.get(k) for k in ("evening", "core_t", "marg_t", "gap")})
    Mo = rows.get("W928 MOR 10") or {}
    check("C: MOR -- morning count 70, 70-10-5 = 55 against Marg 8:5 -> -3:0 (need a look)", Mo.get("core_t") == "5:5" and Mo.get("gap_t") == "−3:0", {k: Mo.get(k) for k in ("core_t", "gap_t")})
    T = J.get("totals") or {}
    check("C: the totals -- 10 items, look 2 (ALFA, MOR), arrived 1, no shelf 7 (never counted), agree 1 (EPS), counts 3",
          (T.get("items"), T.get("look"), T.get("arrived"), T.get("noshelf"), T.get("agree"), T.get("counts")) == (10, 2, 1, 7, 1, 3), T)
    C = J.get("counts") or []
    check("C: Darpan's counts newest first with the evening tag on the 19:49 one", [c["item"] for c in C][:3] == ["W928 EPS 10", "W928 MOR 10", "W928 ALFA 10"] and C[0].get("evening") is True, [(c["item"], c.get("evening")) for c in C])
    co = J.get("count_only") or []
    check("C: the count name Marg no longer prints is listed apart (W928 OLDNAME 10, counted 1:2 on 06-09-2026)", len(co) == 1 and co[0]["item"] == "W928 OLDNAME 10" and co[0]["counted_t"] == "1:2" and co[0]["day"] == "06-09-2026", co)
    check("C: the reports line -- closing as on 20-11-2026 taken 21-11-2026 09:37 IST; sale to 21-11, purchases to 19-11",
          (J.get("reports") or {}).get("closing_as_on") == "20-11-2026" and (J.get("reports") or {}).get("closing_at") == "21-11-2026 09:37 IST"
          and (J.get("reports") or {}).get("sale_to") == "21-11-2026" and (J.get("reports") or {}).get("purchase_to") == "19-11-2026", J.get("reports"))
    # the cold review's points (v1.1)
    check("C: the page builds every Count button from data-item (no name inside a JS string -- an apostrophe in a Marg name cannot break it)",
          "this.dataset.item" in r_page_text and "this.dataset.n" in r_page_text and ".replace(/'/g" not in r_page_text)
    check("C: a first read is built fresh, a second within two minutes is the cached one, ?fresh=1 rebuilds",
          J.get("cached") is False and (cl.get("/finance/stockcheck/api/rows").get_json() or {}).get("cached") is True
          and (cl.get("/finance/stockcheck/api/rows?fresh=1").get_json() or {}).get("cached") is False)
    check("C: the page and its rows admit a viewer (as the retired Stock now did)", "viewer" in ASKED.get("/finance/stockcheck/api/rows", ()) and "viewer" in ASKED.get("/finance/stockcheck/", ()), ASKED)
    check("C: a point's gadbad note reaches the owner as 'Darpan flagged something', never his free text; a long note is cut",
          SC._note_word("gadbad: kuch gadbad hai bhai") == "Darpan flagged something -- see the trace" and len(SC._note_word("x" * 500)) == 120 and SC._note_word(None) == "")
    bz = [x for x in (J.get("rows") or []) if x.get("named") == "below_zero"]
    check("C: a shelf clamped at zero (below_zero) carries no core figure (%d such rows here)" % len(bz), all(x.get("core") is None for x in bz))
    r3 = cl.get("/finance/stock/page/drift/", follow_redirects=False)
    check("C: the retired address with a trailing slash is sent to the page too", r3.status_code == 302, r3.status_code)
    r = cl.post("/finance/stockcheck/api/count", json=dict(item="W928 GAMA 10"))
    j = r.get_json() or {}
    c2 = sqlite3.connect(dbp)
    n_ask = c2.execute("SELECT COUNT(*) FROM stock_watch_ask WHERE item='W928 GAMA 10' AND done_at IS NULL").fetchone()[0]
    check("C: a Count drops the cache (the next read is built fresh)", (cl.get("/finance/stockcheck/api/rows").get_json() or {}).get("cached") is False)
    check("C: Count this -> one open ask for GAMA, the owner's words back", r.status_code == 200 and j.get("ok") and n_ask == 1 and "next" in (j.get("message") or ""), (r.status_code, j, n_ask))
    r = cl.post("/finance/stockcheck/api/count", json=dict(item="W928 GAMA 10"))
    check("C: a second Count this says it is already on the list (no second ask)", (r.get_json() or {}).get("ok") and "already" in ((r.get_json() or {}).get("message") or "")
          and c2.execute("SELECT COUNT(*) FROM stock_watch_ask WHERE item='W928 GAMA 10' AND done_at IS NULL").fetchone()[0] == 1, r.get_json())
    r = cl.post("/finance/stockcheck/api/count", json=dict(item=""))
    check("C: Count this with no item is refused (400)", r.status_code == 400, r.status_code)
    r = cl.get("/finance/stockcheck/api/rows")
    J2 = r.get_json() or {}
    check("C: the open ask shows under 'waiting for his next list' and at the head of the next list", any(a["item"] == "W928 GAMA 10" for a in (J2.get("asks") or [])) and (J2.get("next_list") or [{}])[0].get("item") == "W928 GAMA 10", (J2.get("asks"), J2.get("next_list")))
    r = cl.get("/finance/stockcheck/api/find?q=W928")
    check("C: find answers the ten made-up names", len((r.get_json() or {}).get("items") or []) == 10, r.get_json())
    c2.close()
    # the Needs-you count line opens the page
    c3 = sqlite3.connect(dbp)
    SW.ensure(c3)
    ok1, msg1, code1, P1 = SW.darpan_point(c3, "W928 DELTA 10", 20.0, "darpan", sp=SW.Spine(spp))
    lines = SW.needs_you_lines(c3)
    cd = [l for l in lines if re.search(r"counted \d+ items? on", l.get("text") or "")]
    check("C: the Needs-you count line carries an href to the page", len(cd) == 1 and cd[0].get("href") == "/finance/stockcheck/", cd)
    c3.close()
    html = open(os.path.join(fin, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
    check("C: the Hub's Go to names the Stock check page and no longer 'Stock now'", "/finance/stockcheck/" in html and 'page/now">Stock now' not in html)
    page = open(os.path.join(fin, "stock_check.html"), encoding="utf-8").read()
    routes = set(re.findall(r"/finance/stockcheck/api/\w+", page))
    check("C: every door the page calls exists in the module", routes <= {"/finance/stockcheck/api/rows", "/finance/stockcheck/api/count", "/finance/stockcheck/api/find"}, routes)
    out = json.dumps(J)
    check("no run of 8 or more digits in the page's answer", not re.search(r"\d{8,}", out))
    say("INFO %d checks, %d fail" % (RUN[0], len(FAILS)))


if __name__ == "__main__":
    main()
