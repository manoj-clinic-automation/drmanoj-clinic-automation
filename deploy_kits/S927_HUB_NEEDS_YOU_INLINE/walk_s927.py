#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s927.py -- S927 on a COPY of finance.db (never the live file). Usage: walk_s927.py <code_dir_with_TO_files> <finance.db copy> [--control]
ok/RED per check; last line 'RESULT: ALL PASS' | 'RESULT: n FAIL'; exit 1 on any RED. State-aware (F-1465): targets are picked from the copy.
The control (the FROM files) must go red. Writes only into the copy. No patient data printed."""
import datetime as dt
import os
import re
import shutil
import sqlite3
import sys
import tempfile

RED = []


def ck(name, ok, note=""):
    print("%-4s %s%s" % ("ok" if ok else "RED", name, (" -- " + str(note)) if note else ""))
    if not ok:
        RED.append(name)


def finish():
    print("---- %d RED" % len(RED))
    for r in RED:
        print("     RED:", r)
    print("RESULT: ALL PASS" if not RED else "RESULT: %d FAIL" % len(RED))
    sys.exit(1 if RED else 0)


def main():
    code, dbp = sys.argv[1], sys.argv[2]
    work = tempfile.mkdtemp(prefix="s927_", dir=os.environ.get("TMPDIR") or "/tmp")
    db = os.path.join(work, "finance.db")
    shutil.copy(dbp, db)
    sys.path.insert(0, code)
    os.environ.setdefault("PYTHONPYCACHEPREFIX", os.path.join(work, "pyc"))
    try:
        run(code, db)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run(code, db):
    html = open(os.path.join(code, "finance_approvals.html"), encoding="utf-8").read()
    ck("page: open-here button, the panel loader, the tiers, the age chip", all(x in html for x in ("s927Toggle", "s927-pan", "s927-tier", "s927-age")))
    ck("page: the arrived group draws one line per item (s761Li)", "S927: one line per item" in html)
    ck("page: the S927 JS adds no confirm()/alert()", "confirm(" not in "".join(l for l in html.splitlines() if "s927" in l.lower()) and "alert(" not in "".join(l for l in html.splitlines() if "s927" in l.lower()))
    day = open(os.path.join(code, "sanjeevni_day.py"), encoding="utf-8").read()
    ck("sanjeevni_day mounts hub_panels beside hub_cash", "hub_panels.init(app, db_getter, require_fn, unit)" in day)
    try:
        import hub_panels as HP                                   # noqa: E402
    except Exception as e:                                        # noqa: BLE001
        ck("hub_panels imports", False, e)
        return finish()
    ck("hub_panels imports; version 1.0", HP.VERSION == "1.0")
    import sanjeevni_approvals as SA                              # noqa: E402
    import stock_watch as SW                                      # noqa: E402
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    ck("stock_watch's arrival line carries panel/ref/since", 'panel="arrived"' in open(os.path.join(code, "stock_watch.py"), encoding="utf-8").read())
    ck("sanjeevni_approvals wraps the lines with hub_panels.decorate", "_hp927.decorate(con, r)" in open(os.path.join(code, "sanjeevni_approvals.py"), encoding="utf-8").read())
    # decorate on a made-up answer (the live builder needs the spine and the whole app; its shape is lines + count)
    r0 = dict(count=6, lines=[
        dict(cls="warn", target="porders", text="Orthotic shortages: 11 items -- an order is out, more still short"),
        dict(cls="warn", target="porders", href="/finance/porders/flow", text="Purchase orders: 3 a dealer keeps not sending — your grouped page"),
        dict(cls="info", target="porders", text="Goods tapped as arrived on 02-11 from KEDAR PHARMACEUTICAL: no bill scanned, nothing in Marg (20 days) -- for your eyes only"),
        dict(cls="warn", target="stock", text="Voucher 9 (STOCK ISSUE): KT ROS DT — by Marg's closing of 20-11-2026 Marg moved 0 strips, the voucher said -6 strips + 11 tabs"),
        dict(cls="warn", target="porders", text="X: counted as arrived when the Y bill was scanned 29-09 19:06 -- not in Marg's purchases up to 22-11", panel="arrived", ref=5, since="2026-09-29"),
        dict(cls="info", target="bank", text="the Yes Bank statement runs to 31-Oct (22 days ago) -- deposits since then are unproven"),
        dict(cls="warn", target="expiry", href="/finance/sanjeevni/expiry", text="Expiry watch: 1 expired batch"),
    ])
    d = HP.decorate(con, r0)
    L = {l["text"][:20]: l for l in d["lines"]}
    ck("decorate: the Orthotic line retired while the purchase-flow line stands", not any(t.startswith("Orthotic") for t in L) and d["count"] == len(d["lines"]) == 6, d["count"])
    ck("decorate: purchase line -> panel porders", L["Purchase orders: 3 a"]["panel"] == "porders")
    ck("decorate: tapped line -> panel tapped, ref vendor|day, since", L["Goods tapped as arri"]["panel"] == "tapped" and L["Goods tapped as arri"]["ref"] == "KEDAR PHARMACEUTICAL|02-11" and L["Goods tapped as arri"]["since"].endswith("-11-02"), L["Goods tapped as arri"].get("since"))
    ck("decorate: voucher line -> panel voucher, ref item", L["Voucher 9 (STOCK ISS"]["panel"] == "voucher" and L["Voucher 9 (STOCK ISS"]["ref"] == "KT ROS DT", L["Voucher 9 (STOCK ISS"].get("ref"))
    ck("decorate: arrival line keeps its panel and gets its age", L["X: counted as arrive"]["panel"] == "arrived" and (L["X: counted as arrive"].get("age_days") or 0) >= 50)
    ck("decorate: info line -> panel seen; expiry -> expiry", L["the Yes Bank stateme"]["panel"] == "seen" and L["Expiry watch: 1 expi"]["panel"] == "expiry")
    G = SA.s761_groups(d["lines"])
    gk = {g["key"]: g for g in G}
    ck("S761 grouping on decorated lines: the information lines still land in the info group (the panel fields are plain)", "info" in gk and gk["info"]["n"] >= 2 and sum(g["n"] for g in G) == len(d["lines"]), {k: g["n"] for k, g in gk.items()})
    ck("S761 grouping: the arrival line is in the arrived group, the voucher in stock", any(l.get("panel") == "arrived" for l in (gk.get("arrived") or {}).get("lines", [])) and any(l.get("panel") == "voucher" for l in (gk.get("stock") or {}).get("lines", [])))
    ck("Seen key ignores the moving figures", HP._key("the Yes Bank statement runs to 31-Oct (22 days ago) -- deposits since then are unproven") == HP._key("the Yes Bank statement runs to 31-Oct (23 days ago) -- deposits since then are unproven"))
    r1 = HP.decorate(con, dict(count=1, lines=[dict(cls="warn", target="porders", text="Orthotic shortages: 11 items -- an order is out, more still short")]))
    ck("decorate: the Orthotic line STAYS when no purchase-flow line stands", len(r1["lines"]) == 1)
    # Seen
    res, st = HP.act(con, "walk", dict(do="seen", text="the Yes Bank statement runs to 31-Oct (22 days ago) -- deposits since then are unproven"))
    d2 = HP.decorate(con, r0)
    ck("door seen: the line is left out for 30 days", st == 200 and res["ok"] and not any(l["text"].startswith("the Yes Bank") for l in d2["lines"]), res)
    # the arrival panel on a real open arrival of the copy
    rows = [dict(x) for x in con.execute("SELECT l.id, l.item, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.arrived_at IS NOT NULL AND l.supplied>0 AND COALESCE(l.billed_bill_no,'')='' ORDER BY l.id DESC LIMIT 3")]
    ck("the copy holds open arrivals to exercise", len(rows) >= 1, len(rows))
    if rows:
        lid = rows[0]["id"]
        p = HP._panel_arrived(con, lid)
        ck("panel arrived: the order line, Marg's purchases since, the stock, the three doors", all(x in p for x in (rows[0]["item"], "Marg's purchases from", "Marg stock today", "Ask Amir to enter it", "It is this Marg line", "Never came")))
        ck("panel arrived: no 10-digit run", not re.search(r"\d{10,}", p))
        res, st = HP.act(con, "walk", dict(do="amir_ask", lid=lid))
        ck("door amir_ask: a job on Amir's card, once", st == 200 and con.execute("SELECT count(*) FROM amir_job WHERE key=?", ("S927:arr:%d" % lid,)).fetchone()[0] == 1, res)
        res2, st2 = HP.act(con, "walk", dict(do="amir_ask", lid=lid))
        ck("door amir_ask again: no second job", st2 == 200 and con.execute("SELECT count(*) FROM amir_job WHERE key=?", ("S927:arr:%d" % lid,)).fetchone()[0] == 1 and "already" in res2.get("said", ""))
        # marg_line: pick a Marg line of the same dealer if any, else expect the other-dealer refusal
        sn = con.execute("SELECT supplier_norm FROM purchase_order o JOIN purchase_order_line l ON l.order_id=o.id WHERE l.id=?", (lid,)).fetchone()[0]
        pl = con.execute("SELECT id, bill_no FROM purchase_line WHERE supplier_norm=? ORDER BY bill_date DESC LIMIT 1", (sn,)).fetchone()
        other = con.execute("SELECT id FROM purchase_line WHERE supplier_norm<>? ORDER BY id DESC LIMIT 1", (sn,)).fetchone()
        res, st = HP.act(con, "walk", dict(do="marg_line", lid=lid, pl=int(other[0])))
        ck("door marg_line: another dealer's line is refused 409", st == 409)
        res, st = HP.act(con, "walk", dict(do="marg_line", lid=lid))
        ck("door marg_line: no line picked is refused 400", st == 400)
        if pl:
            res, st = HP.act(con, "walk", dict(do="marg_line", lid=lid, pl=int(pl[0])))
            b = con.execute("SELECT billed_bill_no, billed_qty FROM purchase_order_line WHERE id=?", (lid,)).fetchone()
            ck("door marg_line: the order line marked billed on the picked bill", st == 200 and b[0] == str(pl[1]) and b[1] is not None, (dict(res), tuple(b)))
            ck("panel arrived afterwards says settled", "Settled: Marg bill" in HP._panel_arrived(con, lid))
            res, st = HP.act(con, "walk", dict(do="never_came", lid=lid))
            ck("a settled line refuses never_came (409)", st == 409)
        if len(rows) > 1:
            lid2 = rows[1]["id"]
            res, st = HP.act(con, "walk", dict(do="never_came", lid=lid2))
            s = con.execute("SELECT supplied, short FROM purchase_order_line WHERE id=?", (lid2,)).fetchone()
            ck("door never_came: supplied 0, short 1", st == 200 and int(s[0]) == 0 and int(s[1]) == 1, tuple(s))
    pp = HP._panel_porders(con)
    ck("panel porders: the S926 groups with their CSS and doors", ("Dealer says out of stock" in pp or "Dealer keeps not sending" in pp or "Nothing waits for your word" in pp) and "ofTwo(" in pp, len(pp))
    ck("panel porders: carries ofTwo (its doors) and hpTwo", "function ofTwo" in pp and "function hpTwo" in pp)
    # tapped, voucher, expiry, seen panels render
    t = HP._panel_tapped(con, "KEDAR PHARMACEUTICAL|02-11")
    ck("panel tapped renders (lines or 'none left')", "KEDAR" in t and ("Tapped came" in t or "is left" in t))
    v = HP._panel_voucher(con, "KT ROS DT")
    ck("panel voucher: Amir's job state and the Ask again door", "KT ROS DT" in v and "Ask Amir again" in v and ("tapped done" in v or "open" in v or "No job" in v))
    res, st = HP.act(con, "walk", dict(do="voucher_again", item="KT ROS DT"))
    ck("door voucher_again: a job on Amir's card, once a day", st == 200 and con.execute("SELECT count(*) FROM amir_job WHERE key LIKE 'S927:voucher:%'").fetchone()[0] == 1)
    e = HP._panel_expiry(con)
    ck("panel expiry renders", "Expiry watch" in e or "No expiry run" in e)
    ck("panel seen renders its door", "Seen — not shown again" in HP._panel_seen("x"))
    ck("act: a bad door is 400", HP.act(con, "walk", dict(do="nonsense"))[1] == 400)
    ck("no walk row carries a 10-digit number", not any(re.search(r"\d{10,}", " ".join(str(x) for x in r)) for r in con.execute("SELECT text_hi, sub_hi FROM amir_job WHERE created_by LIKE 'S927%'")))
    return finish()


if __name__ == "__main__":
    main()
