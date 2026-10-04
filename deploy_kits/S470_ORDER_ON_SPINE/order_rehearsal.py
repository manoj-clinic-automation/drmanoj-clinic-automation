#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
order_rehearsal.py -- kit S470_ORDER_ON_SPINE (D673, F-718). It replaces S341's file of the same name; the nightly cron line and the
output folder are S341's, unchanged.

    /root/wa/venv/bin/python3 -B /root/finance/spine/order_rehearsal.py                      (tonight)
    ... order_rehearsal.py --date 2026-10-04 --spine SPINE.db --finance-db FINANCE.db --out DIR
    ... order_rehearsal.py --from 2026-09-28                    (keep each day from then to yesterday as if it had run that night)

WHAT CHANGED, AND WHY.  S341's rehearsal carried its own COPY of the engine's rules and scored the list that copy made -- a list nobody
ever saw (F-718). The live engine (order_rules.py) now reads the spine itself, so there is nothing left to rehearse: this file KEEPS,
every night, the proposals the live engine made that day, and SCORES them against what was bought afterwards.

  KEEPS    every order_proposal row of the day (fixed and interim) with its lines, read READ-ONLY from finance.db, written to
           orders/order_rehearsal_<date>.json in the shape S341's files had: lines[].key (the spine's key of the item, through its alias
           map), order_units (qty x pack_size), value_p, vendor -- plus kind and source "order_proposal". Nothing is computed; the engine
           is never called (its ensure() writes settings); finance.db is never written.
  SCORES   as S341 did, seven nights later, against the spine's purchase lines: proposed and bought, proposed not bought, bought not
           proposed. A key proposed twice on one day (a fixed and an interim line, two members of one family) is ONE proposed key, its
           units summed (S341's score kept the last line and dropped the rest).
  AND      two scores more, from the spine: STOCK-OUTS (a medicine with a sale in the scored week whose stock was at or below zero at the
           end of a day of it, and whether it was on a kept list in the seven days before that day) and MONEY (the value of lines proposed
           and not bought within 14 days).
  THE OWNER'S ONE LINE A WEEK  orders/order_score_latest.json, every night, over the trailing seven days that are old enough: a day is
           scored for "bought on list" and for stock-outs when it is 7 days old (the week of days 7 to 13 nights ago), and for "listed and
           bought within 14 days" and the money when it is 14 days old (the days 14 to 20 nights ago). Each percentage is over the days
           scored for it; a day with no proposal is in no denominator. The purchases counted for "bought on list" are those of items
           outside the Orthotics section: the engine never lists an orthotic (S403's keep-in-stock orders those).

READS: spine.db through spine_read.Spine (read-only), finance.db (mode=ro: order_proposal, stock_item_section), its own earlier files.
WRITES: orders/order_rehearsal_<date>.json, orders/order_score_latest.json, orders/order_rehearsal_latest.txt. A file of S341's it is
about to replace is first copied to orders/before_S470/. OFF: the spine's own switches.
"""
import argparse
import datetime as dt
import json
import os
import shutil
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
SPINE_DEFAULT = os.path.join(HERE, "spine.db")
OUT_DEFAULT = os.path.join(HERE, "orders")
FINANCE_DEFAULT = "/root/finance/finance.db"                  # absolute: the cron runs this from /root/finance/spine
OFF_FLAGS = (os.path.join(HERE, "OFF"), "/root/finance/_off/ALL_OFF")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
KIT = "S470_ORDER_ON_SPINE"
SOURCE = "order_proposal"
SCORE_AFTER_DAYS = 7
LATE_DAYS = 14


def D(d, n):
    return (d + dt.timedelta(days=n)).isoformat()


def kept_path(out_dir, day):
    return os.path.join(out_dir, "order_rehearsal_%s.json" % (day if isinstance(day, str) else day.isoformat()))


def load(out_dir, day):
    """The kept file of a day, only if it is the engine's own list (source order_proposal); S341's files are not scored."""
    try:
        with open(kept_path(out_dir, day), encoding="utf-8") as fh:
            j = json.load(fh)
    except (OSError, ValueError):
        return None
    return j if j.get("source") == SOURCE else None


def keep(fin, sp, day):
    """(lines, proposals) -- the day's order_proposal rows as the live engine wrote them. Read only."""
    lines, props = [], []
    try:
        rows = fin.execute("SELECT id, supplier_norm, vendor, kind, status, lines, total_p FROM order_proposal WHERE day=? ORDER BY id", (day,)).fetchall()
    except sqlite3.Error:
        rows = []
    for pid, sn, vendor, kind, status, raw, total in rows:
        try:
            ls = json.loads(raw or "[]")
        except ValueError:
            ls = []
        props.append(dict(id=pid, supplier_norm=sn, vendor=vendor, kind=kind, status=status, total_p=int(total or 0), lines=len(ls)))
        for l in ls:
            qty, size = int(l.get("qty") or 0), max(1, int(l.get("pack_size") or 1))
            lines.append(dict(key=sp.key(l.get("item")), item=l.get("item"), vendor=vendor, vendor_norm=sn, kind=kind, source=SOURCE, qty=qty,
                              unit=l.get("unit"), pack_size=size, order_units=qty * size, value_p=int(l.get("value_p") or 0), proposal_id=pid,
                              lot=l.get("lot"), free=l.get("free"), family=l.get("family")))
    return lines, props


def proposed(rec):
    """{key: dict(units, value_p)} -- a key proposed twice on one day is ONE proposed key, its units and value summed."""
    out = {}
    for l in (rec or {}).get("lines") or []:
        e = out.setdefault(l["key"], dict(units=0, value_p=0))
        e["units"] += l.get("order_units") or 0
        e["value_p"] += l.get("value_p") or 0
    return out


def bought(sp, after, upto):
    """{key: units} bought (direction PURCHASE) after a day and up to another, both as ISO dates."""
    return {r["k20"]: r["u"] for r in sp.q("SELECT k20, COALESCE(SUM(units),0) AS u FROM sp_purchase_line WHERE direction='PURCHASE' AND date>? AND date<=? "
                                           "GROUP BY k20", after, upto) if (r["u"] or 0) > 0}


def ortho_keys(fin, sp):
    try:
        return {sp.key(r[0]) for r in fin.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")}
    except sqlite3.Error:
        return set()


def score(out_dir, sp, today):
    """S341's three scores: the kept list of SCORE_AFTER_DAYS nights ago against the purchases since."""
    d0 = D(today, -SCORE_AFTER_DAYS)
    P = proposed(load(out_dir, d0))
    if not P:
        return None
    B = bought(sp, d0, today.isoformat())
    hit = [(k, P[k]["units"], B[k]) for k in P if B.get(k, 0) > 0]
    miss = [(k, P[k]["units"]) for k in P if B.get(k, 0) <= 0]
    extra = [(k, u) for k, u in B.items() if k not in P]
    return dict(proposal_date=d0, proposed=len(P), bought_as_proposed=len(hit), proposed_not_bought=len(miss), bought_not_proposed=len(extra),
                hits=hit[:40], misses=miss[:40], extras=extra[:40])


def weekly(out_dir, sp, fin, today):
    """The owner's one line: the trailing seven days old enough to score."""
    ortho = ortho_keys(fin, sp)
    w7 = [D(today, -n) for n in range(13, 6, -1)]                 # 7 to 13 nights ago, oldest first
    w14 = [D(today, -n) for n in range(20, 13, -1)]               # 14 to 20 nights ago
    hits = extras = scored7 = 0
    for d in w7:
        P = proposed(load(out_dir, d))
        if not P:
            continue                                              # no kept list, or a day with no proposal: in no denominator
        B = {k: u for k, u in bought(sp, d, D(dt.date.fromisoformat(d), SCORE_AFTER_DAYS)).items() if k not in ortho}
        hits += sum(1 for k in B if k in P)
        extras += sum(1 for k in B if k not in P)
        scored7 += 1
    # stock-outs: a medicine sold in the scored week whose stock ended a day of it at or below zero, on a day a list was kept
    kept_days = [d for d in w7 if load(out_dir, d) is not None]
    outs = []
    if kept_days:
        lists = {}

        def listed(key, day):
            for n in range(1, 8):
                dd = D(dt.date.fromisoformat(day), -n)
                if dd not in lists:
                    lists[dd] = set(proposed(load(out_dir, dd)))
                if key in lists[dd]:
                    return True
            return False
        for r in sp.q("SELECT DISTINCT k20 FROM sp_sale_line WHERE date BETWEEN ? AND ? ORDER BY k20", w7[0], w7[-1]):
            k = r["k20"]
            if k in ortho:
                continue
            zero = [x["date"] for x in sp.stock_series(k, w7[0], w7[-1]) if x["units"] <= 0 and x["date"] in kept_days]
            if zero:
                outs.append(dict(key=k, first_day=zero[0], days=len(zero), listed_in_time=listed(k, zero[0])))
    listed_n = listed_bought = value_not = scored14 = 0
    for d in w14:
        P = proposed(load(out_dir, d))
        if not P:
            continue
        B = bought(sp, d, D(dt.date.fromisoformat(d), LATE_DAYS))
        listed_n += len(P)
        listed_bought += sum(1 for k in P if B.get(k, 0) > 0)
        value_not += sum(v["value_p"] for k, v in P.items() if B.get(k, 0) <= 0)
        scored14 += 1
    first = None
    if not scored7:                                               # nothing old enough yet: when does the first week fall due
        own = sorted(d for d in (n[len("order_rehearsal_"):-5] for n in os.listdir(out_dir) if n.startswith("order_rehearsal_2") and n.endswith(".json"))
                     if d > D(today, -SCORE_AFTER_DAYS) and proposed(load(out_dir, d)))
        if own:
            first = D(dt.date.fromisoformat(own[0]), SCORE_AFTER_DAYS)
    return dict(kit=KIT, date=today.isoformat(), written_at=dt.datetime.now(IST).isoformat(timespec="seconds"),
                bought_on_list_pct=(round(100.0 * hits / (hits + extras), 1) if (hits + extras) else None),
                listed_bought_pct=(round(100.0 * listed_bought / listed_n, 1) if listed_n else None),
                stockouts=len(outs), stockouts_listed_in_time=sum(1 for o in outs if o["listed_in_time"]),
                value_not_bought_p=(value_not if scored14 else None), days_scored_7=scored7, days_scored_14=scored14,
                week_7=[w7[0], w7[-1]], week_14=[w14[0], w14[-1]], bought_on_list=[hits, hits + extras], listed_bought=[listed_bought, listed_n],
                stockout_items=outs[:60], first_score_on=first)


def words(w):
    """The weekly line as the owner's card says it (the card builds its own from the same keys)."""
    if not w["days_scored_7"]:
        return "the weekly score is not ready yet" + ((" -- the first week is scored on the night of %s" % w["first_score_on"]) if w.get("first_score_on") else "")
    pct = lambda x: ("%d%%" % round(x)) if x is not None else "n/a"   # noqa: E731
    return ("of what was bought, %s was on the list beforehand · of what was listed, %s was bought within %d days · %d medicines ran out, %d of them listed in time"
            % (pct(w["bought_on_list_pct"]), pct(w["listed_bought_pct"]), LATE_DAYS, w["stockouts"], w["stockouts_listed_in_time"])
            + ((" · Rs %s listed and not bought" % "{:,}".format(w["value_not_bought_p"] // 100)) if w["value_not_bought_p"] is not None else ""))


def run_day(sp, fin, out_dir, today, meta, log=print):
    os.makedirs(out_dir, exist_ok=True)
    p = kept_path(out_dir, today)
    if os.path.exists(p) and load(out_dir, today) is None:        # S341's file of that night: kept aside before this one takes its name
        aside = os.path.join(out_dir, "before_S470")
        os.makedirs(aside, exist_ok=True)
        if not os.path.exists(os.path.join(aside, os.path.basename(p))):
            shutil.copy2(p, os.path.join(aside, os.path.basename(p)))
    lines, props = keep(fin, sp, today.isoformat())
    rec = dict(kit=KIT, source=SOURCE, date=today.isoformat(), prepared_at=dt.datetime.now(IST).isoformat(timespec="seconds"), spine_built=meta.get("built", ""),
               proposals=props, lines=lines,
               totals=dict(proposals=len(props), lines=len(lines), keys=len({l["key"] for l in lines}), value_p=sum(l["value_p"] for l in lines),
                           fixed=sum(1 for x in props if x["kind"] == "fixed"), interim=sum(1 for x in props if x["kind"] == "interim")))
    with open(p + ".tmp", "w", encoding="utf-8") as fh:              # kept first: tonight's scores may read it
        json.dump(rec, fh, indent=1, ensure_ascii=False)
    os.replace(p + ".tmp", p)
    rec["score"] = score(out_dir, sp, today)
    w = weekly(out_dir, sp, fin, today)
    rec["weekly"] = w
    with open(p + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1, ensure_ascii=False)
    os.replace(p + ".tmp", p)
    sp_ = os.path.join(out_dir, "order_score_latest.json")
    with open(sp_ + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(w, fh, indent=1, ensure_ascii=False)
    os.replace(sp_ + ".tmp", sp_)
    sc = rec["score"]
    txt = ["ORDER TRIAL -- %s -- kept %s from finance.db's order_proposal (%s); the spine built %s" % (
               today.isoformat(), dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M"), KIT, meta.get("built", "?")[:16]),
           "The list the live engine made today: %d proposal(s) (%d fixed, %d interim), %d line(s), value Rs %s" % (
               len(props), rec["totals"]["fixed"], rec["totals"]["interim"], len(lines), "{:,}".format(rec["totals"]["value_p"] // 100)),
           ""]
    for x in props:
        txt.append("== %s  (%s, %s)  Rs %s" % (x["vendor"], x["kind"], x["status"], "{:,}".format(x["total_p"] // 100)))
        for l in lines:
            if l["proposal_id"] == x["id"]:
                txt.append("  %-30s %4d x %-3d = %5d u   Rs %7s" % (str(l["item"])[:30], l["qty"], l["pack_size"], l["order_units"], "{:,}".format(l["value_p"] // 100)))
    txt.append("")
    txt.append(("-- SCORE of the list of %s against the purchases since: proposed %d · bought as proposed %d · proposed not bought %d · bought not proposed %d"
                % (sc["proposal_date"], sc["proposed"], sc["bought_as_proposed"], sc["proposed_not_bought"], sc["bought_not_proposed"]))
               if sc else "-- SCORE: no kept list from %d nights ago" % SCORE_AFTER_DAYS)
    txt.append("-- THE WEEK: " + words(w))
    lp = os.path.join(out_dir, "order_rehearsal_latest.txt")
    with open(lp + ".tmp", "w", encoding="utf-8") as fh:
        fh.write("\n".join(txt) + "\n")
    os.replace(lp + ".tmp", lp)
    log(txt[0])
    log(txt[1])
    log(txt[-2])
    log(txt[-1])
    return rec


def run(spine, fin_db, out_dir, today, frm=None, log=print):
    for f in OFF_FLAGS:
        if os.path.exists(f):
            log("order_rehearsal: switched off (%s)" % f)
            return 0
    if not os.path.exists(spine):
        log("order_rehearsal: no spine at %s" % spine)
        return 2
    if not os.path.exists(fin_db):
        log("order_rehearsal: no finance.db at %s" % fin_db)
        return 2
    from spine_read import Spine                               # noqa: PLC0415 -- beside this file: the spine's one read door
    sp = Spine(spine)
    fin = sqlite3.connect("file:%s?mode=ro" % fin_db, uri=True)
    try:
        meta = sp.meta()
        if frm:
            d = frm
            while d < today:
                run_day(sp, fin, out_dir, d, meta, log)
                d += dt.timedelta(days=1)
        else:
            run_day(sp, fin, out_dir, today, meta, log)
    finally:
        fin.close()
        sp.con.close()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", default=SPINE_DEFAULT)
    ap.add_argument("--finance-db", default=FINANCE_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--date", default="")
    ap.add_argument("--from", dest="frm", default="", help="keep each day from this date to the day before --date (today), as if run that night")
    a = ap.parse_args(argv)
    today = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(IST).date()
    return run(a.spine, a.finance_db, a.out, today, dt.date.fromisoformat(a.frm) if a.frm else None)


if __name__ == "__main__":
    sys.exit(main())
