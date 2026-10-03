#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_s454p3b.py -- kit S454_BILL_REGISTER, P3B (S454 18.3, 18.4, 18.5): what the changes do to TODAY's data, read on SCRATCH copies
(backup API) before anything is placed. One process per side: NEW = the box + P3B's built files, OLD = the box as it is (the control).

  18.3  September's Sarvam counter (supplier misreads should fall 4 -> 3), every register row whose state moves, and the matcher's links
        re-run on each side (a pair made or lost is listed -- a wrong pair would stop the install)
  18.4  the system's plan on order.stock_basis = marg: the lines that change
  18.5  F-713: every item whose sales reading (90 days) or expected stock (stock_watch.expected_units) moves when a credit note is a return

    --fin-new DIR --fin-old DIR --db PATH --adb PATH --spine PATH --work DIR
"""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
import sys

TAG = "R454P3BJSON "
TODAY = dt.date.today()


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def probe():
    FIN = os.environ["FINDIR"]
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    import purchase_app as pa                                          # noqa: E402
    import order_rules as orr                                          # noqa: E402
    import scan_register as SR                                         # noqa: E402
    import stock_watch as SW                                           # noqa: E402
    assert SR.__file__.startswith(FIN), SR.__file__
    pa._assets_db = os.environ["ASSETS_DB"]
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    db.row_factory = sqlite3.Row
    out = {}
    # ---- 18.3
    out["gunina"] = SR.sup_norm("GUNINA PHARMACEUTICALS P.L. LTD.")
    links0 = {str(k): v.get("scan") for k, v in SR.links(db).items()}
    pa._rematch(db, "S454P3B report")
    links1 = {str(k): v.get("scan") for k, v in SR.links(db).items()}
    out["links_before"], out["links_after"] = len(links0), len(links1)
    out["links_made"] = sorted((k, links1[k]) for k in links1 if links0.get(k) != links1[k])
    out["links_lost"] = sorted((k, links0[k]) for k in links0 if links1.get(k) != links0[k])
    out["sarvam"] = SR.sarvam(db, "2026-09")
    reg = {}
    for m in ("2026-09", "2026-10"):
        r = SR.register(db, m)
        for row in r.get("rows") or []:
            reg["%s|%s" % (m, row.get("bill_id") or row.get("id"))] = dict(state=row.get("state"), supplier=row.get("supplier"), bill_no=row.get("bill_no"),
                                                                          note=str(row.get("note") or "")[:120])
        out["reg_head_" + m] = {k: v for k, v in (r.get("counts") or {}).items()}
    out["reg"] = reg
    bills = {str(r[0]): dict(supplier=r[1], bill_no=r[2], amount_p=r[3]) for r in db.execute("SELECT id, supplier, bill_no, amount_p FROM purchase_bill")}
    out["bills"] = {k: bills.get(k) for k in set([x[0] for x in out["links_made"] + out["links_lost"]])}
    # ---- 18.4 the plan on marg
    db.execute("INSERT INTO setting (key, value) VALUES ('order.stock_basis','marg') ON CONFLICT(key) DO UPDATE SET value='marg'")
    db.commit()
    p = orr.plan(db, TODAY)
    out["plan_marg"] = sorted([v.get("vendor") or "", l["item"], l["qty"], l.get("unit") or ""] for v in (p.get("vendors") or {}).values() for l in v["lines"])
    tr = orr._snapshot_inputs(db, TODAY)[4]
    out["way_marg"] = {k: v.get("units") for k, v in tr.items()}
    # ---- 18.5 the spine's sales reading
    sp = SW.Spine(os.environ["SPINE_DB"])
    d90 = (TODAY - dt.timedelta(days=90)).isoformat()
    exp, s90 = {}, {}
    for it in sp.items():
        nm = it["name"]
        try:
            e = SW.expected_units(db, sp, nm)
            if e.get("expected") is not None:
                exp[nm] = round(float(e["expected"]), 2)
        except Exception as ex:                                        # noqa: BLE001
            exp[nm] = "ERR " + str(ex)[:60]
        s90[nm] = round(float(sp.sales(nm, d90, TODAY.isoformat(), incl_from=True)["u"] or 0), 2)
    out["exp"], out["s90"] = exp, s90
    out["pack"] = {it["name"]: SW.pack_of(it["packing"]) for it in sp.items()}
    print(TAG + json.dumps(out, default=str))


def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--db", "--adb", "--spine", "--work"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    assert a.work.startswith("/tmp/"), "refusing a non-scratch work folder"
    os.makedirs(a.work, exist_ok=True)

    def copydb(src, dst):
        s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
        d = sqlite3.connect(dst)
        s.backup(d)
        d.close()
        s.close()

    def run(side, fin):
        dbp, adbp, spp = [os.path.join(a.work, "r_%s_%s.db" % (side, x)) for x in ("fin", "ast", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, FINDIR=fin, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, PORDERS_SOURCE="tables")
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=3000)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s side did not finish (exit %s):" % (side, p.returncode))
            for l in p.stdout.splitlines()[-25:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    N, O = run("new", a.fin_new), run("old", a.fin_old)
    if N is None or O is None:
        print("REPORT_S454P3B NOT DONE")
        return 1
    print("-- 18.3  'P.L.' dropped like PVT and LTD: sup_norm('GUNINA PHARMACEUTICALS P.L. LTD.') NEW %r · OLD %r" % (N["gunina"], O["gunina"]))
    sn, so = N["sarvam"], O["sarvam"]
    print("   September's Sarvam counter (%d linked bills): misread supplier NEW %d / OLD %d · bill no. %d / %d · date %d / %d · total %d / %d"
          % (sn["n"], sn["misses"]["supplier"], so["misses"]["supplier"], sn["misses"]["billno"], so["misses"]["billno"], sn["misses"]["date"],
             so["misses"]["date"], sn["misses"]["total"], so["misses"]["total"]))
    print("   the matcher re-run on each side: NEW links %d (made %s, lost %s) · OLD links %d (made %s, lost %s)"
          % (N["links_after"], N["links_made"], N["links_lost"], O["links_after"], O["links_made"], O["links_lost"]))
    extra_made = [x for x in N["links_made"] if x not in O["links_made"]]
    extra_lost = [x for x in N["links_lost"] if x not in O["links_lost"]]
    for k, s in extra_made:
        print("   PAIR MADE by NEW only: bill %s %s -> scan #%s" % (k, mask(N["bills"].get(k)), s))
    for k, s in extra_lost:
        print("   PAIR LOST by NEW only: bill %s %s (scan #%s)" % (k, mask(N["bills"].get(k)), s))
    moved = sorted(k for k in set(N["reg"]) | set(O["reg"]) if (N["reg"].get(k) or {}).get("state") != (O["reg"].get(k) or {}).get("state"))
    print("   register rows whose state moves (September, October): %d" % len(moved))
    for k in moved:
        n_, o_ = N["reg"].get(k) or {}, O["reg"].get(k) or {}
        print("     %s %s %s: %s -> %s" % (k.split("|")[0], n_.get("supplier") or o_.get("supplier"), n_.get("bill_no") or o_.get("bill_no"), o_.get("state"), n_.get("state")))
    print("   register heads NEW: %s · OLD: %s" % (N.get("reg_head_2026-09"), O.get("reg_head_2026-09")))
    print("-- 18.4  the plan on order.stock_basis = marg (today's data): NEW %d lines · OLD %d lines" % (len(N["plan_marg"]), len(O["plan_marg"])))
    pn, po = {(x[0], x[1]): x for x in N["plan_marg"]}, {(x[0], x[1]): x for x in O["plan_marg"]}
    for k in sorted(set(pn) | set(po)):
        if pn.get(k) != po.get(k):
            print("     %s · %s: OLD %s -> NEW %s" % (k[0], k[1], (po.get(k) or [None, None, "—"])[2:], (pn.get(k) or [None, None, "—"])[2:]))
    wch = sorted(k for k in set(N["way_marg"]) | set(O["way_marg"]) if N["way_marg"].get(k) != O["way_marg"].get(k))
    print("   goods on the way / in transit that change on marg: %d item(s)%s" % (len(wch), "".join("\n     %s: OLD %s -> NEW %s" % (k, O["way_marg"].get(k), N["way_marg"].get(k)) for k in wch[:40])))
    print("-- 18.5  F-713 (a credit note is a return): items whose 90-day sales or expected stock move")
    ch_s = sorted((k, O["s90"].get(k), N["s90"].get(k)) for k in N["s90"] if N["s90"].get(k) != O["s90"].get(k))
    ch_e = sorted((k, O["exp"].get(k), N["exp"].get(k)) for k in N["exp"] if N["exp"].get(k) != O["exp"].get(k))
    print("   90-day sales (the pace): %d item(s) move; expected stock (the spot count's comparison): %d item(s) move" % (len(ch_s), len(ch_e)))
    def packs(k, v):
        p = int(N["pack"].get(k) or 1)
        return ("%g" % v) if p <= 1 else ("%g (%.1f strips)" % (v, v / p))
    big = sorted(ch_e, key=lambda x: -abs(float(x[2] or 0) - float(x[1] or 0)) if not isinstance(x[1], str) and not isinstance(x[2], str) else 0)
    for k, o, n in big[:25]:
        d = (float(n) - float(o)) if not isinstance(o, str) and not isinstance(n, str) and o is not None and n is not None else None
        print("     expected %-28s OLD %-12s NEW %-12s %s" % (k, o, n, ("+" + packs(k, d)) if d and d > 0 else (packs(k, d) if d is not None else "")))
    for k, o, n in sorted(ch_s, key=lambda x: -abs(float(x[1] or 0) - float(x[2] or 0)))[:15]:
        print("     90-day sales %-24s OLD %-10s NEW %s" % (k, o, n))
    tot = sum(abs(float(o) - float(n)) for _k, o, n in ch_s if o is not None and n is not None)
    print("   in all: %d units of credit notes no longer counted as sales over 90 days (twice their units move: out of sales, into returns)" % int(round(tot / 2)))
    print("REPORT_S454P3B DONE")
    return 0


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        sys.exit(main())
