#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
order_rehearsal.py -- S274 / kit S341_ORDER_REHEARSAL (Sanjeevni).  D567 item 5:
"Ordering prepared offline against the live spine, rehearsed every night -- NOT switched."

    /root/wa/venv/bin/python3 -B /root/finance/spine/order_rehearsal.py            (tonight's rehearsal)
    ... order_rehearsal.py --date 2026-09-19 --spine /root/finance/spine/spine.db --out /root/finance/spine/orders

WHAT IT IS.  Every night, after the compare, this prepares the order the S225 engine WOULD make tomorrow --
but from the spine (kit S331, the one corrected store) instead of the unverified tables the live engine
reads -- and writes it to a file.  Nobody sees it on a screen; nothing is sent; nothing in finance.db is
touched.  Each later night it SCORES its own proposal of seven nights ago against what was actually bought
since (the spine's purchase lines): proposed and bought · proposed and not bought · bought though not
proposed.  That score is the two-week trial S270 asked for, run by the machine before any person's day
includes "make today's order".

THE RULES ARE THE ENGINE'S DEFAULTS, COPIED, NOT THE OWNER'S RULINGS.  purchase_app.py's plan_line /
cadence_for / confidence (S207_PO, S225) are reproduced here byte-for-meaning -- 2 days lead, 3 safety, +3
single-source, cover capped at 45 days, weekly / fortnightly / monthly cadence by the vendor's monthly value,
box rounding, the dead / thin / spike / small-line rails -- because that is exactly what the owner has not yet
seen or approved (S270_WHAT_IS_LEFT s1 item 2).  The rehearsal exists so he can see what those rules would
have bought, night after night, before ruling on them.  Copied, not imported: kits do not import across each
other on the box.

THE LISTS THAT DO NOT EXIST YET.  order_rules.json beside this file holds the four lists S270 named as
missing -- never_reorder · on_demand · internal_use · orthotics_cycle -- empty except internal_use, seeded
with the three items the owner's 09-Sep ruling (S235) calls internal consumption: BLADE, ZIG ZAG COTTON
500GM, GLOVES SURGICAL 7.  An item on a list is never on the order; it is listed under "held back" with
its reason so the owner sees what the lists do.  Editing the file is the owner's sitting, when it comes.

READS: spine.db (read-only URI), order_rules.json, its own earlier files.  WRITES: orders/order_rehearsal_<date>.json
and orders/order_rehearsal_latest.txt, under /root/finance/spine/.  OFF: the spine's own switches.
"""
import argparse
import datetime as dt
import json
import math
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPINE_DEFAULT = os.path.join(HERE, "spine.db")
OUT_DEFAULT = os.path.join(HERE, "orders")
RULES_DEFAULT = os.path.join(HERE, "order_rules.json")
OFF_FLAGS = (os.path.join(HERE, "OFF"), "/root/finance/_off/ALL_OFF")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
KIT = "S341_ORDER_REHEARSAL"

# ---- the engine's rails, COPIED from purchase_app.py (S207_PO / S225) -- the owner's sitting will change these
TIER_WEEKLY_P = 2000000
TIER_FORTNIGHT_P = 400000
CADENCE_DAYS = {"weekly": 7, "fortnightly": 14, "monthly": 30}
LEAD_DAYS = 2
SAFETY_DAYS = 3
SINGLE_SOURCE_EXTRA_DAYS = 3
MAX_COVER_DAYS = 45
PEAK_SHARE_SPIKE = 0.40
THIN_SELL_DAYS = 5
LOW_CONF_DAYS = 20
DEAD_AFTER_DAYS = 60
MIN_LINE_P = 5000
DEFAULT_BOX = 10
BOX_STRETCH_ASK = 2.0
CONFIRM_LINE_P = 500000
PACE_DAYS = 28
SCORE_AFTER_DAYS = 7

DEFAULT_RULES = {
    "version": 1, "_about": "S341: the four lists S270 s1 item 3 named as missing. Names as Marg prints them; matched on the "
                            "spine's 20-character key. The owner's sitting fills these; until then only internal_use is seeded "
                            "(his 09-Sep ruling, S235).",
    "never_reorder": [], "on_demand": [], "internal_use": ["BLADE", "ZIG ZAG COTTON 500GM", "GLOVES SURGICAL 7"],
    "orthotics_cycle": []}


def K(n):
    return re.sub(r'\s+', ' ', (n or "").strip())[:20].strip()


def ceil_div(a, b):
    return -(-a // b) if b else 0


def cadence_for(monthly_p, observed_per_month):
    if monthly_p >= TIER_WEEKLY_P:
        want = "weekly"
    elif monthly_p >= TIER_FORTNIGHT_P:
        want = "fortnightly"
    else:
        want = "monthly"
    if observed_per_month and observed_per_month > 0:
        observed_days = 30.0 / observed_per_month
        for name in ("weekly", "fortnightly", "monthly"):
            if CADENCE_DAYS[name] >= observed_days - 0.01:
                break
        if CADENCE_DAYS[name] > CADENCE_DAYS[want]:
            return name, want
    return want, want


def confidence(sell_days):
    if sell_days >= LOW_CONF_DAYS:
        return "high"
    if sell_days >= THIN_SELL_DAYS:
        return "medium"
    return "thin"


def plan_line(it, cad_days):
    cover = cad_days + LEAD_DAYS + SAFETY_DAYS
    if it["single_source"]:
        cover += SINGLE_SOURCE_EXTRA_DAYS
    capped = min(cover, MAX_COVER_DAYS)
    rate = it["rate_per_day"]
    target = rate * capped
    need = target - it["on_hand"]
    size = max(1, int(it["pack_size"] or 1))
    strips = 0 if need <= 0 else ceil_div(int(math.ceil(need)), size)
    reasons, confirm = [], False
    box = int(it.get("box") or 0)
    if size == 1:
        box = box if box > 1 else 1
    elif box <= 1:
        box = DEFAULT_BOX
    if strips and box > 1:
        rounded = ceil_div(strips, box) * box
        if rounded != strips:
            reasons.append("rounded up from %d to a box of %d" % (strips, box))
            if rounded >= BOX_STRETCH_ASK * strips:
                confirm = True
                reasons.append("the box is %.0fx what is actually needed" % (float(rounded) / strips))
        strips = rounded
    value_p = int(strips * size * (it["cost_p"] or 0))
    conf = confidence(it["sell_days"])
    peak = it.get("peak_share") or 0.0
    if strips and peak >= PEAK_SHARE_SPIKE:
        confirm = True
        reasons.append("one day was %d%% of the window's sales -- a spike, not a rate" % round(peak * 100))
    if strips and conf == "thin":
        confirm = True
        reasons.append("sold on only %d day%s in %d -- the daily rate is a guess"
                       % (it["sell_days"], "" if it["sell_days"] == 1 else "s", PACE_DAYS))
    if strips and value_p >= CONFIRM_LINE_P:
        confirm = True
        reasons.append("one line over Rs %d" % (CONFIRM_LINE_P // 100))
    if strips and it["days_since_sale"] > DEAD_AFTER_DAYS:
        strips, value_p = 0, 0
        reasons.append("nothing sold for %d days -- not reordered" % it["days_since_sale"])
    if strips and value_p < MIN_LINE_P and it["on_hand"] > 0:
        strips, value_p = 0, 0
        reasons.append("under Rs %d and not out of stock -- waits for the next run" % (MIN_LINE_P // 100))
    if cover > MAX_COVER_DAYS:
        reasons.append("cover capped at %d days" % MAX_COVER_DAYS)
    return {"item": it["item"], "key": it["key"], "vendor": it["vendor"], "on_hand": it["on_hand"], "marg_on_hand": it.get("marg_on_hand"),
            "rate_per_day": round(rate, 2), "sell_days": it["sell_days"], "confidence": conf,
            "cover_days": capped, "pack_size": size, "box": box, "order_strips": strips,
            "order_units": strips * size, "value_p": value_p, "confirm": confirm,
            "single_source": it["single_source"], "days_since_sale": it["days_since_sale"],
            "peak_share": round(peak, 3), "why": reasons}


# ---------------------------------------------------------------- the spine's inputs
def pack_size(packing):
    m = re.match(r'^\s*(\d+)\s*\*\s*(\d+)', packing or "")
    if m:
        n = int(m.group(2))
        return n if n > 0 else 1
    return 1


def load_rules(path):
    try:
        with open(path, encoding="utf-8") as fh:
            r = json.load(fh)
    except (OSError, ValueError):
        r = dict(DEFAULT_RULES)
    out = {}
    for lst in ("never_reorder", "on_demand", "internal_use", "orthotics_cycle"):
        out[lst] = {K(x) for x in (r.get(lst) or [])}
    out["version"] = r.get("version", 0)
    return out


def gather(con, today):
    """Per k20: everything plan_line needs, from the spine alone."""
    since = (today - dt.timedelta(days=PACE_DAYS - 1)).isoformat()
    t_iso = today.isoformat()
    items = {}
    for r in con.execute("SELECT k20, name, packing, unit_kind FROM sp_item ORDER BY name"):
        e = items.setdefault(r["k20"], dict(key=r["k20"], item=r["name"], packs=set(), unit_kind=r["unit_kind"]))
        if len(r["name"]) > len(e["item"]):
            e["item"] = r["name"]
        e["packs"].add(pack_size(r["packing"]))
    on_hand = {r["k20"]: r["u"] for r in con.execute("SELECT k20, COALESCE(SUM(units),0) AS u FROM sp_move WHERE date<=? GROUP BY k20", (t_iso,))}
    marg = {}
    for r in con.execute("SELECT k20, as_on, units FROM sp_close WHERE as_on<=? ORDER BY as_on", (t_iso,)):
        marg[r["k20"]] = (r["as_on"], r["units"])
    per = {}
    for r in con.execute("SELECT k20, date, COALESCE(SUM(units),0) AS u FROM sp_sale_line WHERE date BETWEEN ? AND ? GROUP BY k20, date", (since, t_iso)):
        per.setdefault(r["k20"], {})[r["date"]] = r["u"]
    last_sale = {r["k20"]: r["d"] for r in con.execute("SELECT k20, MAX(date) AS d FROM sp_sale_line WHERE date<=? GROUP BY k20", (t_iso,))}
    sup = {}
    for r in con.execute("SELECT l.k20, l.supkey, l.date, l.qty, l.units, l.amount_p, b.supplier FROM sp_purchase_line l "
                         "LEFT JOIN sp_purchase_bill b ON b.supkey=l.supkey AND b.bill=l.bill AND b.date=l.date "
                         "WHERE l.direction='PURCHASE' AND l.date<=? ORDER BY l.date", (t_iso,)):
        e = sup.setdefault(r["k20"], dict(vendor=None, vendor_key=None, suppliers=set(), qtys=[], cost_p=None, last=""))
        if r["supkey"]:
            e["suppliers"].add(r["supkey"])
            e["vendor"], e["vendor_key"] = (r["supplier"] or r["supkey"]), r["supkey"]
        if r["units"] and r["amount_p"]:
            e["cost_p"] = float(r["amount_p"]) / float(r["units"])
        if r["qty"]:
            e["qtys"].append(int(r["qty"]))
        e["last"] = r["date"]
    # vendor cadence: the last 90 days of purchase bills per supplier
    since90 = (today - dt.timedelta(days=90)).isoformat()
    cad = {}
    for r in con.execute("SELECT supkey, COALESCE(SUM(amount_p),0) AS a, COUNT(*) AS n FROM sp_purchase_bill "
                         "WHERE direction='PURCHASE' AND date BETWEEN ? AND ? GROUP BY supkey", (since90, t_iso)):
        name, _want = cadence_for(r["a"] / 3.0, (r["n"] or 0) / 3.0)
        cad[r["supkey"]] = CADENCE_DAYS[name]
    out = []
    for k, e in items.items():
        days = per.get(k, {})
        total = max(0.0, sum(days.values()))
        peak = max(days.values()) if days else 0.0
        ls = last_sale.get(k)
        dsl = (today - dt.date.fromisoformat(ls)).days if ls else 999
        s = sup.get(k, {})
        g = 0
        for q in s.get("qtys", []):
            g = math.gcd(g, q)
        size = max(e["packs"]) if e["packs"] else 1
        out.append(dict(key=k, item=e["item"], pack_size=size, on_hand=float(on_hand.get(k, 0.0)),
                        marg_on_hand=(marg.get(k) or (None, None))[1], marg_as_on=(marg.get(k) or (None, None))[0],
                        rate_per_day=total / PACE_DAYS, sell_days=sum(1 for v in days.values() if v > 0),
                        peak_share=(peak / total) if total > 0 else 0.0, days_since_sale=dsl,
                        vendor=s.get("vendor"), vendor_key=s.get("vendor_key"), single_source=len(s.get("suppliers", ())) <= 1,
                        cost_p=(s.get("cost_p") or 0.0), box=(g if g > 1 else 0),
                        cadence_days=cad.get(s.get("vendor_key"), CADENCE_DAYS["monthly"])))
    return out


def rehearse(con, today, rules):
    lines, held = [], []
    for it in gather(con, today):
        why = None
        for lst, word in (("never_reorder", "never re-ordered (owner's list)"), ("internal_use", "internal use, not sold (S235 ruling)"),
                          ("on_demand", "ordered only against a patient's need (owner's list)"), ("orthotics_cycle", "orthotics: its own cycle (owner's list)")):
            if it["key"] in rules[lst]:
                why = word
                break
        p = plan_line(it, it["cadence_days"])
        p["cadence_days"] = it["cadence_days"]
        if why:
            if p["order_strips"]:
                held.append(dict(p, held=why))
            continue
        if p["order_strips"]:
            lines.append(p)
    lines.sort(key=lambda x: (x["vendor"] or "~", x["item"]))
    return lines, held


def score(out_dir, con, today):
    """The proposal of SCORE_AFTER_DAYS nights ago against the spine's purchases since."""
    d0 = today - dt.timedelta(days=SCORE_AFTER_DAYS)
    p = os.path.join(out_dir, "order_rehearsal_%s.json" % d0.isoformat())
    if not os.path.exists(p):
        return None
    try:
        with open(p) as fh:
            old = json.load(fh)
    except (OSError, ValueError):
        return None
    bought = {r["k20"]: r["u"] for r in con.execute("SELECT k20, COALESCE(SUM(units),0) AS u FROM sp_purchase_line "
                                                    "WHERE direction='PURCHASE' AND date>? AND date<=? GROUP BY k20", (d0.isoformat(), today.isoformat()))}
    proposed = {l["key"]: l for l in old.get("lines", [])}
    hit = [(k, l["order_units"], bought[k]) for k, l in proposed.items() if bought.get(k, 0) > 0]
    miss = [(k, l["order_units"]) for k, l in proposed.items() if bought.get(k, 0) <= 0]
    extra = [(k, u) for k, u in bought.items() if k not in proposed and u > 0]
    return dict(proposal_date=d0.isoformat(), proposed=len(proposed), bought_as_proposed=len(hit), proposed_not_bought=len(miss),
                bought_not_proposed=len(extra), hits=hit[:40], misses=miss[:40], extras=extra[:40])


def render(today, meta, lines, held, sc, rules):
    v = sum(l["value_p"] for l in lines)
    o = ["ORDER REHEARSAL -- %s -- prepared %s from the spine built %s (%s)" % (today.isoformat(), dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M"), meta.get("built", "?")[:16], KIT),
         "NOT AN ORDER. Nobody acts on this file. The rules are the S225 engine's defaults, which the owner has not approved.",
         "lines %d · value Rs %s · confirm-flagged %d · held back by the lists %d · rules v%s" % (len(lines), "{:,}".format(v // 100), sum(1 for l in lines if l["confirm"]), len(held), rules.get("version")),
         ""]
    vendor = None
    for l in lines:
        if l["vendor"] != vendor:
            vendor = l["vendor"]
            o.append("== %s  (cadence %s d)" % (vendor or "(no supplier known)", l["cadence_days"]))
        o.append("  %-30s on hand %6.0f (Marg %s) · %5.2f/day · cover %2d d · ORDER %3d x %-3d = %5d u · Rs %7s%s%s"
                 % (l["item"][:30], l["on_hand"], ("%.0f" % l["marg_on_hand"]) if l["marg_on_hand"] is not None else "-", l["rate_per_day"], l["cover_days"],
                    l["order_strips"], l["pack_size"], l["order_units"], "{:,}".format(l["value_p"] // 100),
                    "  CONFIRM" if l["confirm"] else "", ("  [" + "; ".join(l["why"]) + "]") if l["why"] else ""))
    if held:
        o.append("")
        o.append("-- held back by the lists (would have ordered):")
        for l in held:
            o.append("  %-30s %3d x %-3d -- %s" % (l["item"][:30], l["order_strips"], l["pack_size"], l["held"]))
    o.append("")
    if sc:
        o.append("-- SCORE of the proposal of %s against the purchases since: proposed %d · bought as proposed %d · proposed not bought %d · bought not proposed %d"
                 % (sc["proposal_date"], sc["proposed"], sc["bought_as_proposed"], sc["proposed_not_bought"], sc["bought_not_proposed"]))
    else:
        o.append("-- SCORE: no proposal from %d nights ago yet" % SCORE_AFTER_DAYS)
    return "\n".join(o) + "\n"


def run(spine, out_dir, rules_path, today, log=print):
    for f in OFF_FLAGS:
        if os.path.exists(f):
            log("order_rehearsal: switched off (%s)" % f)
            return 0
    if not os.path.exists(spine):
        log("order_rehearsal: no spine at %s" % spine)
        return 2
    os.makedirs(out_dir, exist_ok=True)
    if not os.path.exists(rules_path):
        with open(rules_path + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(DEFAULT_RULES, fh, indent=1)
        os.replace(rules_path + ".tmp", rules_path)
        log("order_rehearsal: wrote the default order_rules.json (internal_use seeded from the S235 ruling)")
    rules = load_rules(rules_path)
    con = sqlite3.connect("file:%s?mode=ro" % spine, uri=True)
    con.row_factory = sqlite3.Row
    try:
        meta = {r["key"]: r["value"] for r in con.execute("SELECT key, value FROM sp_meta")}
        lines, held = rehearse(con, today, rules)
        sc = score(out_dir, con, today)
    finally:
        con.close()
    rec = dict(kit=KIT, date=today.isoformat(), prepared_at=dt.datetime.now(IST).isoformat(timespec="seconds"), spine_built=meta.get("built", ""),
               rules_version=rules.get("version"), lines=lines, held=held, score=sc,
               totals=dict(lines=len(lines), value_p=sum(l["value_p"] for l in lines), confirm=sum(1 for l in lines if l["confirm"]), held=len(held)))
    p = os.path.join(out_dir, "order_rehearsal_%s.json" % today.isoformat())
    with open(p + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    os.replace(p + ".tmp", p)
    txt = render(today, meta, lines, held, sc, rules)
    lp = os.path.join(out_dir, "order_rehearsal_latest.txt")
    with open(lp + ".tmp", "w", encoding="utf-8") as fh:
        fh.write(txt)
    os.replace(lp + ".tmp", lp)
    log(txt.splitlines()[0])
    log(txt.splitlines()[2])
    log(txt.splitlines()[-1])
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", default=SPINE_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--rules", default=RULES_DEFAULT)
    ap.add_argument("--date", default="")
    a = ap.parse_args(argv)
    today = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(IST).date()
    return run(a.spine, a.out, a.rules, today)


if __name__ == "__main__":
    sys.exit(main())
