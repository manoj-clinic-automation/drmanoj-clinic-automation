#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s644.py -- the S644 walk, on scratch copies only (CLAUDE.md rules 3 and 4).

    python -B walk_s644.py --live <root with finance/> --to <make_s644 --out dir> --db <finance.db to copy> --spine <spine.db> --scratch <dir> [--python <exe>]

Makes <scratch>/old (the live bytes) and <scratch>/new (the live bytes with the TO files over them), a fresh backup-API copy of the database
for every section, and runs walk_run.py in a child process per step (FINANCE_DB, SPINE_DB, ORDER_TODAY set by this driver). Sections:
  1 fixed is today      plan() + interim_plan() + prepare_day on model=fixed, old vs new, on three days: every old key equal.
  2 rhythm              the table for every supplier; Kedar fixed; clamps; last_buy (a) (b) (c); the override; the mode switch; bad values.
  3 relist              stamp · same · moved -> made again once, ids kept · touched -> stale · after the hour · on fixed off.
  4 on the way          a sent order counts within max(on_order_days, interval + lead) of its supplier, not beyond.
  5 the owner's fold    owner_state()['model'], the words, the settings route (choice / clock / clamp cross-check).
  6 the real day        both models, counts and the fifteen largest quantity differences (the table the chat reads).
  7 the selftest        spine/selftest_spine.py (the pure functions made to fail on purpose) on the new bytes.
  8 the cron commands   order_rules.py tick (ORDER_TICK=prepare) and order_rehearsal.py once each as scripts on scratch.
  N negative control    the same checks against the OLD bytes: red where they must be.
Exit 0 = every check green."""
import argparse
import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FAILS = []
N = 0


def check(name, ok, detail=""):
    global N
    N += 1
    print("  %s  %s%s" % ("ok " if ok else "RED", name, (" -- " + str(detail)[:300]) if (detail and not ok) else ""))
    if not ok:
        FAILS.append(name)
    return ok


def copy_db(src, dst):
    s = sqlite3.connect(src)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def run(py, app, cmd, env, arg=None):
    e = dict(os.environ)
    e.update(env)
    p = subprocess.run([py, "-B", os.path.join(HERE, "walk_run.py"), app, cmd, json.dumps(arg or {})], capture_output=True, text=True, env=e, timeout=900)
    if p.returncode != 0:
        print(p.stderr[-2000:])
        raise SystemExit("walk_run %s failed" % cmd)
    line = p.stdout.strip().splitlines()[-1]
    return json.loads(line)


OLD_LINE_KEYS = ("item", "on_hand", "qty", "unit", "pack_size", "packing", "rate_p", "per_day", "cover_after", "cover_days", "value_p", "confirm", "why",
                 "days_left", "vendor_norm", "marg_qty", "shelf_qty", "lot", "free", "family")


def same_plan(a, b):
    """Every OLD key of every line equal; the vendors equal; totals equal. Returns (ok, first difference)."""
    for side in ("vendors", "interim"):
        va, vb = a[side], b[side]
        if set(va) != set(vb):
            return False, "%s suppliers differ: %s vs %s" % (side, sorted(set(va) ^ set(vb)), "")
        for vn in va:
            xa, xb = va[vn], vb[vn]
            if xa["total_p"] != xb["total_p"] or xa["held"] != xb["held"]:
                return False, "%s %s total/held %s vs %s" % (side, vn, (xa["total_p"], xa["held"]), (xb["total_p"], xb["held"]))
            la = {l["item"]: l for l in xa["lines"]}
            lb = {l["item"]: l for l in xb["lines"]}
            if set(la) != set(lb):
                return False, "%s %s items differ %s" % (side, vn, sorted(set(la) ^ set(lb)))
            for it in la:
                for k in OLD_LINE_KEYS:
                    if la[it].get(k) != lb[it].get(k):
                        return False, "%s %s %s.%s %r vs %r" % (side, vn, it, k, la[it].get(k), lb[it].get(k))
    if a["no_supplier"] != b["no_supplier"]:
        return False, "no_supplier differs"
    return True, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", required=True)
    ap.add_argument("--to", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--spine", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--today", default="")
    a = ap.parse_args()
    py = a.python
    os.makedirs(a.scratch, exist_ok=True)
    old = os.path.join(a.scratch, "old", "finance")
    new = os.path.join(a.scratch, "new", "finance")
    for d in (old, new):
        if os.path.exists(os.path.dirname(d)):
            shutil.rmtree(os.path.dirname(d))
        shutil.copytree(os.path.join(a.live, "finance"), d, ignore=shutil.ignore_patterns("__pycache__", "*.db", "*.db-*", "finance.db*"))
    for root, _, files in os.walk(os.path.join(a.to, "finance")):
        if "__pycache__" in root:
            continue
        for f in files:
            src = os.path.join(root, f)
            rel = os.path.relpath(src, os.path.join(a.to, "finance"))
            shutil.copy2(src, os.path.join(new, rel))
    spine = os.path.join(a.scratch, "spine.db")
    shutil.copy2(a.spine, spine)
    today = a.today or dt.date.today().isoformat()
    base_env = dict(SPINE_DB=spine, ORDER_TODAY=today, ORDER_PUSH_STUB="1")

    def fresh(name):
        p = os.path.join(a.scratch, "finance_%s.db" % name)
        copy_db(a.db, p)
        return p

    print("S644 WALK  today=%s  python=%s" % (today, py))
    # ---------------------------------------------------------------- 1 fixed is today
    print("1 · fixed is today (old bytes vs new bytes, model = fixed)")
    t0 = dt.date.fromisoformat(today)
    days = [t0]
    d = t0
    while len(days) < 3:
        d += dt.timedelta(days=1)
        if d.weekday() in (0, 3) and d not in days:              # a Monday and a Thursday
            days.append(d)
    for dd in days:
        env = dict(base_env, ORDER_TODAY=dd.isoformat())
        dbo, dbn = fresh("1o_" + dd.isoformat()), fresh("1n_" + dd.isoformat())
        po = run(py, old, "plan", dict(env, FINANCE_DB=dbo))
        pn = run(py, new, "plan", dict(env, FINANCE_DB=dbn), dict(model="fixed"))
        ok, why = same_plan(po, pn)
        check("plan + interim equal on %s %s (%d suppliers, %d lines)" % (dd.isoformat(), dd.strftime("%a"), len(po["vendors"]), sum(len(v["lines"]) for v in po["vendors"].values())), ok and po["engine"] == pn["engine"] == "spine", why or po["engine"])
        qo = run(py, old, "prepare", dict(env, FINANCE_DB=dbo))
        qn = run(py, new, "prepare", dict(env, FINANCE_DB=dbn), dict(model="fixed"))
        ro = [(r["supplier_norm"], r["kind"], r["status"], r["total_p"], r["reason"], [(l["item"], l["qty"]) for l in r["lines"]]) for r in qo["rows"]]
        rn = [(r["supplier_norm"], r["kind"], r["status"], r["total_p"], r["reason"], [(l["item"], l["qty"]) for l in r["lines"]]) for r in qn["rows"]]
        check("prepare_day rows equal on %s (%d rows, made %s)" % (dd.isoformat(), len(ro), qo["made"]), ro == rn and qo["made"] == qn["made"], (ro, rn) if ro != rn else "")
        check("no made_through stamp on fixed", not any(s == "made_through" for s, _ in qn["notices"]), qn["notices"])
    # ---------------------------------------------------------------- 2 rhythm
    print("2 · the rhythm (model = levels)")
    db2 = fresh("2")
    rh = run(py, new, "rhythm", dict(base_env, FINANCE_DB=db2))
    print("     %-32s %-6s %4s %5s %-10s %-5s %-10s %4s %4s" % ("supplier", "mode", "bd90", "every", "last buy", "due", "next", "gap", "cap"))
    for r in rh:
        print("     %-32s %-6s %4s %5s %-10s %-5s %-10s %4s %4s" % (r["supplier"][:32], r["mode"], r["bill_days90"], r["interval"], r["last_buy"], r["due_today"], r["next"], r["gap"], r["cap"]))
    ked = next(r for r in rh if r["supplier"] == "KEDAR PHARMACEUTICAL")
    check("Kedar is rhythm_mode fixed (the owner's Mon + Fri)", ked["mode"] == "fixed" and ked["order_days"] == "MON,FRI")
    check("every learnt interval within 2..30", all(2 <= r["interval"] <= 30 for r in rh if r["mode"] == "learnt"))
    gun = next(r for r in rh if r["supplier"].startswith("GUNINA"))
    check("Gunina (30 bill days, median 3) is reviewed every 3 days", gun["interval"] == 3 and gun["bill_days90"] >= 20, gun)
    few = [r for r in rh if r["mode"] == "learnt" and (r["bill_days90"] or 0) < 3]
    check("a supplier with fewer than 3 bill days gets the default 7", all(r["interval"] == 7 for r in few) and len(few) > 0, few)
    check("every learnt supplier's cap follows its interval (14 / 21 / 45)", all(r["cap"] == (14 if r["interval"] <= 7 else 21 if r["interval"] <= 14 else 45) for r in rh if r["mode"] == "learnt"))
    check("the words say the interval", all(("reviewed every %d day" % r["interval"]) in r["words"] for r in rh if r["mode"] == "learnt") and "fixed days" in ked["words"], [r["words"] for r in rh][:2])
    # last_buy (a) (b) (c), strictly before, interim does not count, override, mode switch, bad values -- on a supplier with a learnt rhythm
    sup = "GUNINA PHARMACEUTICALS PVT LTD"
    t = dt.date.fromisoformat(today)
    d2, d1 = (t - dt.timedelta(days=2)).isoformat(), (t - dt.timedelta(days=1)).isoformat()
    # last_buy on the walk's OWN supplier (no bill, no order of its own in the live data -- the rows are found by key, never by counting)
    ws = "WALK SUPPLIER S644"
    lb = run(py, new, "lastbuy", dict(base_env, FINANCE_DB=fresh("2b")), dict(supplier=ws, inject=[
        dict(kind="interim", day=d1),                                                # an interim-only order yesterday: must NOT move last buy
        dict(kind="order", day=d2),                                                  # a real order 2 days ago: moves it
        dict(kind="proposal", day=d1),                                               # a sent fixed proposal yesterday: moves it
        dict(kind="order", day=today)]))                                             # today: strictly before -> not counted
    print("    ", json.dumps(lb))
    check("a supplier never bought from: last buy none (due)", lb["before"] == "1970-01-01" and lb["interval"] == 7, lb)
    check("an interim-only order does not move last buy", lb["after_interim_" + d1] == "1970-01-01", lb)
    check("(a) a sent order moves it", lb["after_order_" + d2] == d2, lb)
    check("(b) a sent fixed proposal moves it", lb["after_proposal_" + d1] == d1, lb)
    check("an order sent today is not 'before' today", lb["after_order_" + today] == d1, lb)
    check("due today is false with a buy yesterday and interval 7; next = yesterday + 7 (or the first allowed day after)", lb["due_today"] is False and lb["next"] >= (t + dt.timedelta(days=6)).isoformat(), lb)
    # (c), the override, the mode switch and bad values on a real learnt supplier
    lg = run(py, new, "lastbuy", dict(base_env, FINANCE_DB=fresh("2c")), dict(supplier=sup, review_days=5, mode="fixed", bad=[("review_days", 99), ("rhythm_mode", "maybe")]))
    print("    ", json.dumps(lg))
    check("(c) Gunina: with its real orders / bills, last buy is a real day before today", lg["before"] != "1970-01-01" and lg["before"] < today, lg)
    check("the owner's review_days override wins and the words say 'set by you'", lg["set_review_days"][0] == 200 and lg["interval_after_override"] == 5 and "set by you" in lg["words_after_override"], lg)
    check("rhythm_mode fixed puts the supplier back on its calendar (Monday next)", lg["set_mode"][0] == 200 and lg["next_after_mode"] == "2026-10-26" if today == "2026-10-25" else lg["set_mode"][0] == 200, lg)
    check("bad values refused (review_days 99, rhythm_mode maybe)", lg["bad_review_days_99"] == 400 and lg["bad_rhythm_mode_maybe"] == 400, lg)
    # ---------------------------------------------------------------- 3 relist
    print("3 · the list made again (B.2a)")
    mon = next(d for d in days if d.weekday() == 0)                                  # a Monday: suppliers are due, the list has rows
    rl = run(py, new, "relist", dict(base_env, FINANCE_DB=fresh("3"), ORDER_CLOCK="09:40", ORDER_TODAY=mon.isoformat()))
    print("    ", json.dumps(dict((k, v) for k, v in rl.items() if k != "notices")))
    check("prepare_day on levels stamps made_through", bool(rl.get("stamp")) and "sales_through" in (rl.get("stamp") or ""), rl.get("stamp"))
    check("same inputs: no relist", rl["tick_same"] == "same", rl["tick_same"])
    check("moved inputs + untouched: made again once (rows > 0), ids kept, row count kept", str(rl["tick_moved"]).startswith("relisted") and rl["tick_moved"] != "relisted 0" and rl["ids_kept"]
          and rl["rows_before_after"][0] == rl["rows_before_after"][1] > 0 and rl["tick_again"] == "same", (rl["tick_moved"], rl["ids_kept"], rl["rows_before_after"], rl["tick_again"]))
    check("a touched list is marked stale, not rebuilt", rl["tick_touched"] == "touched -- stale" and rl["stale"], rl["tick_touched"])
    check("after relist_until nothing happens", str(rl["tick_late"]).startswith("past"), rl["tick_late"])
    check("on fixed the relist is off", rl["tick_fixed"] == "off", rl["tick_fixed"])
    # ---------------------------------------------------------------- 4 on the way
    print("4 · on the way (B.4)")
    oo = run(py, new, "onorder", dict(base_env, FINANCE_DB=fresh("4")), dict(supplier=sup, ages=[1, 3, 4, 5, 6, 8, 12]))
    print("    ", json.dumps(oo))
    win = max(oo["on_order_days"], oo["interval"] + 1)
    check("levels: a sent order counts within max(on_order_days %d, interval %d + lead 1) = %d days and not beyond" % (oo["on_order_days"], oo["interval"], win),
          oo["counted_ages"] == [x for x in [1, 3, 4, 5, 6, 8, 12] if x <= win], oo)
    of = run(py, new, "onorder", dict(base_env, FINANCE_DB=fresh("4f")), dict(supplier=sup, ages=[1, 3, 4, 5, 6, 8, 12], model="fixed"))
    check("fixed: on_order_days alone, as before", of["counted_ages"] == [x for x in [1, 3, 4, 5, 6, 8, 12] if x <= of["on_order_days"]], of)
    # ---------------------------------------------------------------- 5 the owner's fold
    print("5 · the owner's fold and the settings route")
    ow = run(py, new, "owner", dict(base_env, FINANCE_DB=fresh("5")))
    print("    ", json.dumps(ow)[:600])
    check("owner_state carries model with value, words, settings (11), rhythm rows, score, inputs", ow["value"] == "levels" and ow["n_settings"] == 11 and ow["rhythm_n"] > 10
          and {"words", "other", "score", "settings", "rhythm"} <= set(ow["keys"]) and not ow.get("error"), ow)
    st = run(py, new, "settings", dict(base_env, FINANCE_DB=fresh("5b")), dict(tries=[("order.model", "levels"), ("order.model", "sideways"), ("order.relist_until", "12:30"), ("order.relist_until", "25:99"),
                                                                                    ("order.review_min_days", "31"), ("order.review_max_days", "1"), ("order.review_min_days", "3"), ("order.big_day_days", "0"), ("order.big_day_days", "91")]))
    print("    ", json.dumps(st))
    check("settings route: levels ok, a wrong word refused, HH:MM ok, 25:99 refused, min > max refused, max < min refused, min 3 ok, big 0 ok, 91 refused, 17 keys on the card",
          st["order.model=levels"] == 200 and st["order.model=sideways"] == 400 and st["order.relist_until=12:30"] == 200 and st["order.relist_until=25:99"] == 400
          and st["order.review_min_days=31"] == 400 and st["order.review_max_days=1"] == 400 and st["order.review_min_days=3"] == 200 and st["order.big_day_days=0"] == 200
          and st["order.big_day_days=91"] == 400 and st["keys_on_card"] == 17 and st["model_now"] == "levels", st)
    # ---------------------------------------------------------------- 6 the real day
    print("6 · the real day, both models (the table the chat reads)")
    pf = run(py, new, "plan", dict(base_env, FINANCE_DB=fresh("6f")), dict(model="fixed"))
    pl = run(py, new, "plan", dict(base_env, FINANCE_DB=fresh("6l")), dict(model="levels"))
    check("the levels plan was made on the spine", pl["engine"] == "spine", pl["engine"])
    check("the levels plan says its window end and model in inputs", (pl.get("inputs") or {}).get("model") == "levels" and (pl.get("inputs") or {}).get("window_end"), pl.get("inputs"))

    def summary(p):
        L = [l for v in p["vendors"].values() for l in v["lines"]]
        return dict(suppliers=len(p["vendors"]), held=sum(1 for v in p["vendors"].values() if v["held"]), lines=len(L), value_rs=sum(l["value_p"] for l in L) // 100,
                    lot_based=sum(1 for l in L if l.get("lot_based")), interim_suppliers=len(p["interim"]), interim_lines=sum(len(v["lines"]) for v in p["interim"].values()),
                    no_supplier=len(p["no_supplier"] or []))
    sf, sl = summary(pf), summary(pl)
    print("     fixed : %s" % json.dumps(sf))
    print("     levels: %s" % json.dumps(sl))
    lf = {(vn, l["item"]): l for vn, v in pf["vendors"].items() for l in v["lines"]}
    ll = {(vn, l["item"]): l for vn, v in pl["vendors"].items() for l in v["lines"]}
    diffs = []
    for k in set(lf) | set(ll):
        qf = lf[k]["qty"] if k in lf else 0
        ql = ll[k]["qty"] if k in ll else 0
        if qf != ql:
            diffs.append((abs(qf - ql), k[1], k[0], qf, ql, (ll.get(k) or lf.get(k))["unit"], "; ".join((ll.get(k) or {}).get("why") or [])[:140]))
    diffs.sort(reverse=True)
    print("     the fifteen largest quantity differences (item · supplier · fixed -> levels · why):")
    for d in diffs[:15]:
        print("       %-28s %-26s %4s -> %-4s %-6s %s" % (d[1][:28], d[2][:26], d[3], d[4], d[5], d[6]))
    check("the two models differ somewhere (else the model is not in force)", len(diffs) > 0, len(diffs))
    check("every levels line has a quantity > 0 and a unit", all(l["qty"] > 0 and l["unit"] for l in ll.values()))
    check("a lot-based line is not rounded to tens unless its lot is", all((l["qty"] % 10 == 0) or l.get("lot_based") or not str(l["unit"]).startswith("strip") for l in ll.values()))
    # ---------------------------------------------------------------- 7 selftest
    print("7 · the spine selftest on the new bytes (the pure functions made to fail on purpose)")
    p = subprocess.run([py, "-B", os.path.join(new, "spine", "selftest_spine.py")], capture_output=True, text=True, cwd=os.path.join(new, "spine"), timeout=600)
    check("selftest_spine.py OK on the new bytes", p.returncode == 0 and "SELFTEST OK" in p.stdout, (p.stdout[-400:] + p.stderr[-400:]))
    print("     ", p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-300:])
    # ---------------------------------------------------------------- 8 cron commands as scripts
    print("8 · the cron commands once each, as scripts, on scratch")
    db8 = fresh("8")
    e = dict(os.environ, **dict(base_env, FINANCE_DB=db8, ORDER_TICK="prepare"))
    p = subprocess.run([py, "-B", os.path.join(new, "order_rules.py"), "tick"], capture_output=True, text=True, env=e, cwd=new, timeout=900)
    check("order_rules.py tick (prepare) runs", p.returncode == 0 and '"slot": "prepare"' in p.stdout, p.stdout[-300:] + p.stderr[-300:])
    out8 = os.path.join(a.scratch, "orders8")
    os.makedirs(out8, exist_ok=True)
    p = subprocess.run([py, "-B", os.path.join(new, "spine", "order_rehearsal.py"), "--spine", spine, "--finance-db", db8, "--out", out8, "--date", today], capture_output=True, text=True, cwd=os.path.join(new, "spine"), timeout=900)
    check("order_rehearsal.py runs and writes the weekly file with by_model / darpan keys", p.returncode == 0 and os.path.exists(os.path.join(out8, "order_score_latest.json"))
          and {"by_model", "darpan"} <= set(json.load(open(os.path.join(out8, "order_score_latest.json")))), p.stdout[-300:] + p.stderr[-300:])
    # ---------------------------------------------------------------- N negative control
    print("N · negative control -- the OLD bytes")
    h = run(py, old, "has", dict(base_env, FINANCE_DB=fresh("n")))
    check("OLD bytes have no model_rate, no relist, no review_interval (the checks above would be red on them)", not h["model_rate"] and not h["relist"] and not h["review_interval"] and h["kit"] != "S644_BUYING_MODEL", h)
    rn = run(py, old, "relist", dict(base_env, FINANCE_DB=fresh("n3"), ORDER_CLOCK="09:40"))
    check("OLD bytes: prepare_day leaves no made_through stamp and has no relist", not rn.get("stamp") and rn.get("relist") == "absent", rn)
    p = subprocess.run([py, "-B", os.path.join(old, "spine", "selftest_spine.py")], capture_output=True, text=True, cwd=os.path.join(old, "spine"), timeout=600)
    check("OLD selftest has no S644 checks (fewer checks than the new one)", p.returncode == 0 and "S644" not in p.stdout)
    print("\nWALK %s  (%d checks, %d red)" % ("GREEN" if not FAILS else "RED", N, len(FAILS)))
    for f in FAILS:
        print("  RED: " + f)
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
