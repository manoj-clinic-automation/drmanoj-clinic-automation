#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s644.py -- S644_BUYING_MODEL: builds the TO files from the FROM (live) bytes with anchored edits (each anchor exactly once; a miss
stops the build) and one appended block (s644_block.py). Usage:

    python -B make_s644.py --src <live root, e.g. /root or a bundle's root> --out <dir>      (writes <out>/<relative path> + SUMS_TO.md5)
    python -B make_s644.py --check <live root>                                                (pins only: FROM md5s, exit 1 on a mismatch)

FROM pins (the 25-Oct-2026 01:35 IST bundle = the live box after the S642 / S641 installs):"""
import argparse
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {
    "finance/order_rules.py": "8d078dbe",
    "finance/porders_s454.py": "673883e8",
    "finance/spine/spine_read.py": "10697b38",
    "finance/spine/order_rehearsal.py": "104d366d",
    "finance/spine/selftest_spine.py": "7d0edb4a",
    "finance/finance_ui/finance_approvals.html": "a7016a4e",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def rd(p):
    with io.open(p, "rb") as fh:
        return fh.read()


def edit(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit("ANCHOR %s: found %d times, need exactly 1" % (label, n))
    return text.replace(old, new)


# ------------------------------------------------------------------------------------------------------------------------ order_rules.py
def build_order_rules(t):
    t = edit(t, 'KIT = "S593_ORDER_ENGINE_ONE_SOURCE"                            # the kit that last changed this file; v1.0 was S410_MEDICINE_ORDERING',
             'KIT = "S644_BUYING_MODEL"                                       # the kit that last changed this file (S593 before it); v1.0 was S410_MEDICINE_ORDERING',
             "OR kit")
    t = edit(t, '''        ds = sorted(set(e["dates"]))
        gaps = []
        for i in range(len(ds) - 1):
            try:
                gaps.append((dt.date.fromisoformat(ds[i + 1]) - dt.date.fromisoformat(ds[i])).days)
            except ValueError:
                pass
        e["avg_month_p"] = int(e["amount90_p"] / 3.0)
        e["gap"] = statistics.median(gaps) if gaps else None
        if len(ds) >= minb and gaps:
''', '''        ds = sorted(set(e["dates"]))
        dds = []
        for x in ds:
            try:
                dds.append(dt.date.fromisoformat(x))
            except ValueError:
                pass
        e["avg_month_p"] = int(e["amount90_p"] / 3.0)
        e["interval"], e["gap"], e["bill_days90"] = model_interval(dds, today, minb, _s470_days(con, "order.review_default_days"),   # S644: THE one median
                                                                 _s470_days(con, "order.review_min_days"), _s470_days(con, "order.review_max_days"))
        if len(ds) >= minb and e["gap"] is not None:
''', "OR rhythm")
    t = edit(t, '''        line = pa.plan_line(it, cad, dead_after)               # S470 (B.8)
        line["cover_days"] = cov
''', '''        line = pa.plan_line(it, cad, dead_after)               # S470 (B.8)
        line["cover_days"] = cov
        _s644_shape(con, s, it, p, lp, r, line, cov, dead_after, cost_unit)   # S644: on levels the floor, the need, the lot; on fixed nothing
''', "OR plan hook")
    t = edit(t, '''        cover = on_hand / p["rate_per_day"]
        horizon = (F - today).days + lead + safety
        if cover >= horizon:
            continue
        need = p["rate_per_day"] * horizon - on_hand
        strips = int(math.ceil(need / float(s["pack_size"])))
        if strips <= 0:
            continue
''', '''        cover = on_hand / p["rate_per_day"]
        horizon, strips = _s644_interim(con, r, s, p, on_hand, F, today, lead, safety)   # S644: fixed = today's test and arithmetic, line for line
        if strips <= 0:
            continue
''', "OR interim hook")
    t = edit(t, '''        line = dict(order_strips=strips, cover_days=horizon, confirm=False, why=why)
        lo = _line_out(pa, s, dict(on_hand=s["qty"]), line, cost_unit, p)
''', '''        line = dict(order_strips=strips, cover_days=horizon, confirm=False, why=why)
        _s644_interim_keys(con, line, s, p)                    # S644: the model keys on the interim row (owner's eyes only)
        lo = _line_out(pa, s, dict(on_hand=s["qty"]), line, cost_unit, p)
''', "OR interim keys")
    t = edit(t, '''        made["interim"] += 1
    con.commit()
    _ = pa
    return made
''', '''        made["interim"] += 1
    con.commit()
    _s644_stamp_day(con, today)                               # S644 (B.2a): what the list was made from, in order_notice
    _ = pa
    return made
''', "OR prepare stamp")
    t = edit(t, '''    _s500_reports(con, s454)                                  # S500: the morning reports' watch (reports_watch.tick)
''', '''    _s500_reports(con, s454)                                  # S500: the morning reports' watch (reports_watch.tick)
    try:
        _s644_relist(con, today, now)                         # S644 (B.2a): on levels, the untouched list made again when an input moved
    except Exception:                                         # noqa: BLE001 -- never stops the tick
        pass
''', "OR tick relist")
    block = rd(os.path.join(HERE, "s644_block.py")).decode("utf-8")
    t = edit(t, '''

if __name__ == "__main__":                                   # S454 P1D: last in the file''', block + '''

if __name__ == "__main__":                                   # S454 P1D: last in the file''', "OR tail")
    return t


# ------------------------------------------------------------------------------------------------------------------------ spine_read.py
def build_spine_read(t):
    t = edit(t, '''    def last_sale(self, name):
        """{date} of the latest sale line of the key over all history, or None."""
        d = self.q("SELECT MAX(date) AS d FROM sp_sale_line WHERE k20=?", self.key(name))[0]["d"]
        return dict(date=d) if d else None
''', '''    def last_sale(self, name):
        """{date} of the latest sale line of the key over all history, or None."""
        d = self.q("SELECT MAX(date) AS d FROM sp_sale_line WHERE k20=?", self.key(name))[0]["d"]
        return dict(date=d) if d else None

    def last_sale_day(self):
        """ISO day of the newest sale line the spine holds, any item, or None. S644: the day the levels model's rate windows end on
        (never today -- a list made with yesterday's sales in it)."""
        return self.q("SELECT MAX(date) AS d FROM sp_sale_line")[0]["d"]
''', "SR last_sale_day")
    return t


# ------------------------------------------------------------------------------------------------------------------------ porders_s454.py
def build_porders_s454(t):
    t = edit(t, '''S470_LIMITS = {"order.pace_days": (7, 90), "order.dead_after_days": (1, 365), "order.on_order_days": (1, 30), "order.in_transit_days": (1, 60),
               "order.lot_history_days": (30, 730)}
''', '''S470_LIMITS = {"order.pace_days": (7, 90), "order.dead_after_days": (1, 365), "order.on_order_days": (1, 30), "order.in_transit_days": (1, 60),
               "order.lot_history_days": (30, 730),
               # S644 (the levels model's numbers; order.model and order.relist_until are word / clock settings, validated below)
               "order.rate_short_days": (3, 14), "order.rate_short_cap_pct": (100, 400), "order.rate_short_min_sell_days": (1, 7), "order.big_day_days": (0, 90),
               "order.interim_margin_days": (0, 7), "order.new_item_days": (7, 90), "order.review_min_days": (1, 7), "order.review_max_days": (3, 45),
               "order.review_default_days": (2, 30)}
S644_CHOICE = {"order.model": ("fixed", "levels")}
''', "PS limits")
    t = edit(t, '''    v = str(v or "").strip()
    if key == "order.engine_source":
        return v in ("spine", "tables"), v
    lim = S470_LIMITS.get(key)
''', '''    v = str(v or "").strip()
    if key == "order.engine_source":
        return v in ("spine", "tables"), v
    if key in S644_CHOICE:                                     # S644: a word setting
        return v in S644_CHOICE[key], v
    if key == "order.relist_until":                            # S644: a clock, HH:MM
        m = re.match(r"^([01]\\d|2[0-3]):([0-5]\\d)$", v)
        return bool(m), v
    lim = S470_LIMITS.get(key)
''', "PS valid")
    t = edit(t, '''    ok, v = _s470_valid(key, value)
    if not ok:
        lim = S470_LIMITS.get(key)
        return jsonify(ok=False, error="bad_value", message="%s: not a valid value (%s)" % (key, ("%d to %d" % lim) if lim else "spine or tables")), 400
    old = _s470_or()._setting(con, key)
''', '''    ok, v = _s470_valid(key, value)
    if not ok:
        lim = S470_LIMITS.get(key)
        hint = ("%d to %d" % lim) if lim else (" or ".join(S644_CHOICE[key]) if key in S644_CHOICE else ("HH:MM" if key == "order.relist_until" else "spine or tables"))
        return jsonify(ok=False, error="bad_value", message="%s: not a valid value (%s)" % (key, hint)), 400
    if key in ("order.review_min_days", "order.review_max_days"):   # S644: the two clamps must stay in order
        other = "order.review_max_days" if key == "order.review_min_days" else "order.review_min_days"
        ov = int(_s470_or()._setting(con, other) or 0)
        if (key == "order.review_min_days" and int(v) > ov) or (key == "order.review_max_days" and int(v) < ov):
            return jsonify(ok=False, error="bad_value", message="%s: review_min_days must stay at or below review_max_days (now %d)" % (key, ov)), 400
    old = _s470_or()._setting(con, key)
''', "PS set")
    t = edit(t, '''    pct = lambda x, late: ("%d%%" % int(round(float(x)))) if x is not None else late       # noqa: E731
    m, k = int(j.get("stockouts") or 0), int(j.get("stockouts_listed_in_time") or 0)
    return ("Last week: of what was bought, %s was on the list beforehand · of what was listed, %s was bought within 14 days · "
            "%d medicine%s ran out, %d of them listed in time."
            % (pct(j.get("bought_on_list_pct"), "nothing yet"), pct(j.get("listed_bought_pct"), "not known yet (14 days are needed)"),
               m, "" if m == 1 else "s", k))
''', '''    pct = lambda x, late: ("%d%%" % int(round(float(x)))) if x is not None else late       # noqa: E731
    m, k = int(j.get("stockouts") or 0), int(j.get("stockouts_listed_in_time") or 0)
    s = ("Last week: of what was bought, %s was on the list beforehand · of what was listed, %s was bought within 14 days · "
         "%d medicine%s ran out, %d of them listed in time."
         % (pct(j.get("bought_on_list_pct"), "nothing yet"), pct(j.get("listed_bought_pct"), "not known yet (14 days are needed)"),
            m, "" if m == 1 else "s", k))
    bm = j.get("by_model") or {}                               # S644 (B.8): the same figures per model, when a week carried more than one
    if bm:
        s += " " + " · ".join("%s list: %s of the list bought within 14 days (%d day%s)" % (("new" if mk == "levels" else "old"), pct(v.get("listed_bought_pct"), "n/a"),
                                                                                             int(v.get("days") or 0), "" if int(v.get("days") or 0) == 1 else "s")
                              for mk, v in sorted(bm.items()))
    return s
''', "PS score line")
    t = edit(t, '''def _s470_card(con, st):
    h = ['<div %s id="s470"><div id="s470score">%s</div>' % (st, esc(_s470_score_line()))]
''', '''def _s644_model_line(con):
    """S644 (B.0): How the list is made -- one line and one button for the other value, on the owner's old page (the approvals fold draws its own)."""
    cur = _s470_or()._setting(con, "order.model", "fixed")
    words = {"levels": "Levels -- each supplier's own rhythm, the shop's lots, yesterday's sales", "fixed": "Fixed days -- as before"}
    other = "fixed" if cur == "levels" else "levels"
    return ('<div id="s644model"><b>How the list is made</b> · %s <button onclick="s454set(\\'order.model\\',\\'%s\\')" style="min-height:40px">Change to %s</button>'
            '<div style="color:#666;font-size:13px">The list is made and scored in the background; no staff screen changes with this setting.</div></div>'
            % (esc(words.get(cur, cur)), other, esc(words[other])))


def _s470_card(con, st):
    h = ['<div %s id="s470">%s<div id="s470score">%s</div>' % (st, _s644_model_line(con), esc(_s470_score_line()))]
''', "PS card")
    if "import re" not in t.split("\n\n")[0] and "\nimport re\n" not in t:
        t = edit(t, "\nimport os\n", "\nimport os\nimport re\n", "PS import re")
    return t


# ------------------------------------------------------------------------------------------------------------------------ order_rehearsal.py
def build_rehearsal(t):
    t = edit(t, 'KIT = "S470_ORDER_ON_SPINE"\n', 'KIT = "S644_BUYING_MODEL"                                    # S470_ORDER_ON_SPINE built it; S644 keeps model / held / added / qty_engine and scores per model\n', "RH kit")
    t = edit(t, '''            lines.append(dict(key=sp.key(l.get("item")), item=l.get("item"), vendor=vendor, vendor_norm=sn, kind=kind, source=SOURCE, qty=qty,
                              unit=l.get("unit"), pack_size=size, order_units=qty * size, value_p=int(l.get("value_p") or 0), proposal_id=pid,
                              lot=l.get("lot"), free=l.get("free"), family=l.get("family")))
''', '''            qe = l.get("qty_engine")                             # S644 (B.8): Darpan's changed quantity keeps the engine's beside it
            lines.append(dict(key=sp.key(l.get("item")), item=l.get("item"), vendor=vendor, vendor_norm=sn, kind=kind, source=SOURCE, qty=qty,
                              unit=l.get("unit"), pack_size=size, order_units=qty * size, value_p=int(l.get("value_p") or 0), proposal_id=pid,
                              lot=l.get("lot"), free=l.get("free"), family=l.get("family"),
                              model=l.get("model") or "fixed", held=bool(l.get("held")), added=bool(l.get("added")),
                              qty_engine=(int(qe) if qe not in (None, "") else None), made_through=l.get("window_end")))
''', "RH keep")
    t = edit(t, '''def proposed(rec):
    """{key: dict(units, value_p)} -- a key proposed twice on one day is ONE proposed key, its units and value summed."""
    out = {}
    for l in (rec or {}).get("lines") or []:
        e = out.setdefault(l["key"], dict(units=0, value_p=0))
        e["units"] += l.get("order_units") or 0
        e["value_p"] += l.get("value_p") or 0
    return out
''', '''def proposed(rec, model=None):
    """{key: dict(units, value_p)} -- a key proposed twice on one day is ONE proposed key, its units and value summed. S644 (B.8): a line
    Darpan ADDED is not the engine's and is not scored; a HELD line is scored as listed; the units scored are the engine's (qty_engine)
    when Darpan changed the quantity. model: only that model's lines."""
    out = {}
    for l in (rec or {}).get("lines") or []:
        if l.get("added"):
            continue
        if model is not None and (l.get("model") or "fixed") != model:
            continue
        e = out.setdefault(l["key"], dict(units=0, value_p=0))
        qe = l.get("qty_engine")
        e["units"] += (int(qe) * max(1, int(l.get("pack_size") or 1))) if qe not in (None, "") else (l.get("order_units") or 0)
        e["value_p"] += l.get("value_p") or 0
    return out
''', "RH proposed")
    t = edit(t, '''    first = None
    if not scored7:                                               # nothing old enough yet: when does the first week fall due
''', '''    by_model, darpan = {}, dict(held=0, added=0, changed=0)   # S644 (B.8): the listed-and-bought score per model; Darpan's taps as kept
    for d in w14:
        rec = load(out_dir, d)
        if not rec:
            continue
        for l in rec.get("lines") or []:
            darpan["held"] += 1 if l.get("held") else 0
            darpan["added"] += 1 if l.get("added") else 0
            darpan["changed"] += 1 if l.get("qty_engine") not in (None, "") else 0
        for mk in {(l.get("model") or "fixed") for l in rec.get("lines") or []}:
            P = proposed(rec, mk)
            if not P:
                continue
            B = bought(sp, d, D(dt.date.fromisoformat(d), LATE_DAYS))
            e = by_model.setdefault(mk, dict(days=0, listed=0, listed_bought=0))
            e["days"] += 1
            e["listed"] += len(P)
            e["listed_bought"] += sum(1 for k in P if B.get(k, 0) > 0)
    for e in by_model.values():
        e["listed_bought_pct"] = round(100.0 * e["listed_bought"] / e["listed"], 1) if e["listed"] else None
    first = None
    if not scored7:                                               # nothing old enough yet: when does the first week fall due
''', "RH weekly")
    t = edit(t, '''                stockout_items=outs[:60], first_score_on=first)
''', '''                stockout_items=outs[:60], first_score_on=first,
                by_model=(by_model if len(by_model) > 1 else {}), darpan=darpan)   # S644: by_model only when a week carried two models
''', "RH weekly out")
    return t


# ------------------------------------------------------------------------------------------------------------------------ selftest_spine.py
def build_selftest(t):
    t = edit(t, '''if __name__ == "__main__":
    test_readers()
    test_evidence()
    test_builder()
    test_s470()
    test_s577()
    print("SELFTEST OK  %d checks" % N)
''', '''def test_s644():
    """S644 (B.0a): the pure arithmetic of the levels model, made to fail on purpose; and the rehearsal's B.8 rules."""
    import datetime as dt
    sys.path.insert(0, os.path.dirname(HERE))
    import order_rules as OR                                 # noqa: E402  (the venv has flask; the service's python too)
    import order_rehearsal as RH                             # noqa: E402
    end = dt.date(2026, 10, 20)
    flat = {end - dt.timedelta(days=n): 2.0 for n in range(28)}                       # 2 a day for 28 days
    r, rl, rs, sl, ss, pk = OR.model_rate(flat, end, 28, 7, 3, 200)
    check("S644 rate: a flat 2 a day reads 2.0 long and short", abs(rl - 2.0) < 1e-9 and abs(rs - 2.0) < 1e-9 and abs(r - 2.0) < 1e-9 and sl == 28 and ss == 7)
    spike = dict(flat)
    for n in range(7):
        spike[end - dt.timedelta(days=n)] = 10.0                                      # 5x last week on 7 selling days
    r, rl, rs, _, ss, _ = OR.model_rate(spike, end, 28, 7, 3, 200)
    check("S644 rate: 5x last week is bounded at 2x the long rate", abs(rs - 10.0) < 1e-9 and abs(r - 2 * rl) < 1e-9 and r < rs)
    one = {end - dt.timedelta(days=3): 6.0}
    r, rl, rs, _, ss, _ = OR.model_rate(one, end, 28, 7, 3, 200)
    check("S644 rate: one sale in the week keeps the long rate", ss == 1 and abs(r - rl) < 1e-9)
    check("S644 rate: a day after the window end is not counted", OR.model_rate({end + dt.timedelta(days=1): 99.0}, end, 28, 7, 3, 200)[0] == 0.0)
    bd, on = OR.model_big_day(spike, end, 28)
    check("S644 big day: the largest day and its date", bd == 10.0 and on == end)
    check("S644 big day: 0 days = off", OR.model_big_day(spike, end, 0) == (0.0, None))
    check("S644 big day: 90 days reaches past 28", OR.model_big_day({end - dt.timedelta(days=60): 50.0}, end, 90)[0] == 50.0 and OR.model_big_day({end - dt.timedelta(days=60): 50.0}, end, 28)[0] == 0.0)
    pl = [(end - dt.timedelta(days=10), 100.0), (end - dt.timedelta(days=40), 100.0), (end - dt.timedelta(days=70), 50.0), (end - dt.timedelta(days=400), 1000.0)]
    check("S644 lot: the median of the window's lots, the old one left out", OR.model_lot(pl, end, 180) == 100.0 and OR.model_lot(pl, end, 20) == 100.0 and OR.model_lot([], end, 180) is None)
    ds = [end - dt.timedelta(days=n) for n in (1, 4, 7, 10, 13, 16)]
    iv, med, nb = OR.model_interval(ds, end, 3, 7, 2, 30)
    check("S644 interval: six bill days 3 apart -> 3", iv == 3 and med == 3 and nb == 6)
    check("S644 interval: two bill days -> the default", OR.model_interval(ds[:2], end, 3, 7, 2, 30)[0] == 7)
    check("S644 interval: clamped both ways", OR.model_interval([end - dt.timedelta(days=n) for n in (0, 1, 2, 3)], end, 3, 7, 2, 30)[0] == 2
          and OR.model_interval([end - dt.timedelta(days=n) for n in (0, 40, 80)], end, 3, 7, 2, 30)[0] == 30)
    check("S644 interval: a day after as_of is not a bill day", OR.model_interval(ds + [end + dt.timedelta(days=5)], end, 3, 7, 2, 30)[2] == 6)
    check("S644 cap: by the interval", OR.model_cap_days(3, 14, 21, 45) == 14 and OR.model_cap_days(10, 14, 21, 45) == 21 and OR.model_cap_days(20, 14, 21, 45) == 45)
    check("S644 level: never below the big day", OR.model_level(2.0, 10, 30.0) == 30.0 and OR.model_level(2.0, 10, 5.0) == 20.0)
    q, notes = OR.model_qty(140.0, 100.0, 10.0, 2.0, 200, False)
    check("S644 qty: need 140 with a lot of 100 -> 200", q == 200.0 and not notes)
    q, notes = OR.model_qty(140.0, 100.0, 10.0, 2.0, 60, False)
    check("S644 qty: the cap stops the second lot", q == 100.0 and "cut to the cover cap" in notes)
    q, notes = OR.model_qty(5.0, 100.0, 0.0, 1.0, 30, False)
    check("S644 qty: one lot above the cap is still one lot, and says so", q == 100.0 and "one lot is more than the cover cap" in notes)
    check("S644 qty: a new item is one lot", OR.model_qty(900.0, 100.0, 0.0, 2.0, 200, True)[0] == 100.0)
    check("S644 interim: fires only when the stock will not last to the next review + lead + margin",
          OR.model_interim_due(10.0, 2.0, 5, 1, 1) is True and OR.model_interim_due(14.0, 2.0, 5, 1, 1) is False and OR.model_interim_due(0.0, 0.0, 5, 1, 1) is False)
    rec = dict(lines=[dict(key="A", order_units=10, value_p=100, pack_size=10, model="levels"),
                      dict(key="B", order_units=20, value_p=200, pack_size=10, model="levels", added=True),
                      dict(key="C", order_units=30, value_p=300, pack_size=10, model="fixed", qty_engine=5),
                      dict(key="D", order_units=40, value_p=400, pack_size=10, model="levels", held=True)])
    P = RH.proposed(rec)
    check("S644 B.8: an added line is not scored, a held one is, qty_engine is the units scored", set(P) == {"A", "C", "D"} and P["C"]["units"] == 50 and P["D"]["units"] == 40)
    check("S644 B.8: per model", set(RH.proposed(rec, "levels")) == {"A", "D"} and set(RH.proposed(rec, "fixed")) == {"C"})


if __name__ == "__main__":
    test_readers()
    test_evidence()
    test_builder()
    test_s470()
    test_s577()
    test_s644()
    print("SELFTEST OK  %d checks" % N)
''', "ST main")
    return t


# ------------------------------------------------------------------------------------------------------------------------ finance_approvals.html
def build_approvals(t):
    t = edit(t, '''  var h=poApproveHTML("Top");
  h+='<div id="poFreezeLine">'+poFreezeHTML()+'</div>';
''', '''  var h=poApproveHTML("Top");
  h+='<div id="poFreezeLine">'+poFreezeHTML()+'</div>';
  h+=poModelHTML(j.model||{});
''', "UI model block call")
    t = edit(t, '''function loadPORules(){
''', '''/* ---- S644: how the list is made (the levels model) -- one line, one button, the score, the inputs, the settings ---- */
function poModelHTML(m){
  if(!m||!m.value) return "";
  var h='<div class="alert" id="poModel" style="margin:6px 0"><b>How the list is made:</b> '+esc(m.words||m.value)+' <button onclick="poModelSet(\\''+esc(m.other||"")+'\\')">Change to '+esc(m.other_words||m.other||"")+'</button>';
  h+='<div class="mut">Made and scored in the background; no staff screen changes with this setting.'+(m.score?' · '+esc(m.score):'')+'</div>';
  var inp=m.inputs||null;
  if(inp){ var c=inp.capture||{}; h+='<div class="mut">The last list stood on: sales to '+esc(inp.sales_through||"?")+' · Marg\\'s closing of '+esc(c.end_day||c.as_on||"?")+' · spine built '+esc(String(inp.spine_built||"").slice(0,16))+' · '+esc(inp.counted)+' counted / '+esc(inp.marg)+' on Marg\\'s figure / '+esc(inp.absent)+' absent'+(inp.window_end?' · rate windows end '+esc(inp.window_end):'')+'</div>'; }
  if(m.relist) h+='<div class="mut">'+esc(m.relist.text)+'</div>';
  if(m.stale) h+='<div class="mut" style="color:#8c1d18">'+esc(m.stale.text)+'</div>';
  if(m.rhythm&&m.rhythm.length){ h+='<details class="fold"><summary>Each supplier\\'s rhythm ('+m.rhythm.length+')</summary><div class="tblwrap"><table><tr><th>supplier</th><th>mode</th><th>every</th><th>bill days / 90</th><th>last buy</th><th>next</th><th>cap</th></tr>';
    m.rhythm.forEach(function(r){ h+='<tr><td>'+esc(r.supplier)+'</td><td>'+esc(r.mode)+'</td><td>'+esc(r.interval)+' d</td><td>'+esc(r.bill_days90==null?"":r.bill_days90)+'</td><td>'+esc(r.last_buy==="1970-01-01"?"never":(r.last_buy||"—"))+'</td><td>'+esc(r.next)+'</td><td>'+esc(r.cap)+' d</td></tr>'; });
    h+='</table></div></details>'; }
  if(m.settings&&m.settings.length){ h+='<details class="fold"><summary>The model\\'s settings ('+m.settings.length+')</summary><div class="tblwrap"><table>';
    m.settings.forEach(function(s){ var id="poMs_"+s.key.replace(/\\./g,"_"); h+='<tr><td><code>'+esc(s.key)+'</code><div class="mut">'+esc(s.note)+'</div></td><td><input id="'+id+'" value="'+esc(s.value)+'" style="width:110px"> <button onclick="poModelSave(\\''+esc(s.key)+'\\',\\''+id+'\\')">Save</button></td></tr>'; });
    h+='</table></div></details>'; }
  return h+'</div>';
}
function poModelSet(v){ return poModelSave("order.model",null,v); }
function poModelSave(key,id,v){
  if(id){ var e=$(id); v=e?e.value:""; }
  return fetch("/finance/porders/api/s454/setting",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:key,value:v})}).then(srvJSON).then(function(x){
    var j=x.j||{}; if(!j.ok){ alert(j.message||j.error||"not saved"); return; } loadPORules();
  }).catch(function(){ alert("could not reach the server"); });
}
function loadPORules(){
''', "UI model fns")
    t = edit(t, '''    num("cap",r.cover_cap_days,["Cover cap (days)","never order more than this many days of cover in one go (weekly 14 · fortnightly 21 · monthly 45 by default)"])+
''', '''    num("cap",r.cover_cap_days,["Cover cap (days)","never order more than this many days of cover in one go (weekly 14 · fortnightly 21 · monthly 45 by default)"])+
    '<label>Rhythm '+sel("rhythm_mode",r.rhythm_mode||"learnt",[["learnt","learnt from its bills"],["fixed","fixed days (the days ticked above)"]])+'<small>S644 · read only while the list is made by levels: learnt = reviewed every N days as its own bills show · fixed = the order days above, as before</small></label>'+
    '<label>Review every <input type="number" id="'+p+'review_days" min="1" max="45" value="'+esc(r.review_days==null?"":r.review_days)+'" placeholder="learnt"> days<small>blank = learnt from its bills; a number overrides it (within the model\\'s min / max)</small></label>'+
''', "UI edit form")
    t = edit(t, '''            ["review_on",v("review_on")],["review_target",v("review_target")],["note",v("note")]];
  var cur={cadence:r.cadence,order_days:r.order_days,blocked_days:r.blocked_days,lead_days:r.lead_days,safety_days:r.safety_days,cover_cap_days:r.cover_cap_days,single_source_extra:Number(r.single_source_extra)?1:0,review_on:r.review_on||"",review_target:r.review_target||"",note:r.note||""};
''', '''            ["review_on",v("review_on")],["review_target",v("review_target")],["note",v("note")],["rhythm_mode",v("rhythm_mode")],["review_days",v("review_days")]];
  var cur={cadence:r.cadence,order_days:r.order_days,blocked_days:r.blocked_days,lead_days:r.lead_days,safety_days:r.safety_days,cover_cap_days:r.cover_cap_days,single_source_extra:Number(r.single_source_extra)?1:0,review_on:r.review_on||"",review_target:r.review_target||"",note:r.note||"",rhythm_mode:r.rhythm_mode||"learnt",review_days:(r.review_days==null?"":r.review_days)};
''', "UI edit save")
    return t


BUILDERS = {
    "finance/order_rules.py": build_order_rules,
    "finance/porders_s454.py": build_porders_s454,
    "finance/spine/spine_read.py": build_spine_read,
    "finance/spine/order_rehearsal.py": build_rehearsal,
    "finance/spine/selftest_spine.py": build_selftest,
    "finance/finance_ui/finance_approvals.html": build_approvals,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", help="the live root: <src>/finance/order_rules.py ...")
    ap.add_argument("--out", help="where the TO files go, same relative paths")
    ap.add_argument("--check", help="pins only, against this live root")
    a = ap.parse_args()
    root = a.check or a.src
    if not root:
        ap.error("--src/--out or --check")
    bad = 0
    for rel, pin in FROM.items():
        p = os.path.join(root, rel)
        h = md5(rd(p))[:8] if os.path.exists(p) else "MISSING"
        print("FROM %-45s %s %s" % (rel, h, "ok" if h == pin else "!= %s" % pin))
        bad += h != pin
    if bad:
        print("PIN MISMATCH -- stop")
        return 1
    if a.check:
        return 0
    sums = []
    for rel, fn in BUILDERS.items():
        src = rd(os.path.join(root, rel)).decode("utf-8")
        out = fn(src)
        op = os.path.join(a.out, rel)
        os.makedirs(os.path.dirname(op), exist_ok=True)
        with io.open(op, "w", encoding="utf-8", newline="") as fh:
            fh.write(out)
        h = md5(out.encode("utf-8"))
        sums.append("%s  %s" % (h, rel))
        print("TO   %-45s %s" % (rel, h[:8]))
    with io.open(os.path.join(a.out, "SUMS_TO.md5"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(sums) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
