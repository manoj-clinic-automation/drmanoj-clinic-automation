#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s633.py -- S633_XRAY_FULL_YEAR (D767): rebuilds xray_costs.py's TO bytes from the pinned FROM bytes by exact, counted edits.

    python3 -B make_s633.py <FROM folder> <TO folder>

Each edit's anchor must occur exactly ONCE in the FROM file; the FROM md5 must equal the pin; the TO md5 is printed.

The owner, 22:11 IST 22-Oct-2026: "the xray page, it lists expenses from july, but all from April needed there, to get the full
picture of xray expenses, and film size wise incremental procurement with dates, so that the xray revenue can be analysed properly,
films are regular consumables. Amc needs to be assessed monthly, fdr battery, xray online ups battery also need to be appropriately
accounted for, for a better assessment of xray costs."
"""
import hashlib
import os
import sys

FROM_PIN = {"xray_costs.py": "22e59f5a275d687bae767da8bf776a6a"}

NEW_FUNCS = r'''# ---------------------------------------------------------------------------------------------- S633 (D767): the year, the films, the spreads
def _span(a, b):
    """Whole months from one day to another (19-07-2026 .. 18-07-2027 -> 12); 0 when either is not read or the end is earlier."""
    f, t = _iso(a), _iso(b)
    if f is None or t is None or t < f:
        return 0
    n = (t.year - f.year) * 12 + t.month - f.month + (1 if t.day >= f.day else 0)
    return max(0, min(n, 240))


def _s633_spread(out, ok, n, why):
    """The last row of `out` spread evenly over n months from its own month (the last share takes the paise left over). A row that
    cannot be spread stays one row. Every share keeps the row's papers; a paper is claimed once per row (month_view)."""
    r = out[-1]
    r["share"] = ""
    if not ok or n < 2 or not r.get("month") or not r["cost"]:
        return
    tot = r["cost"]
    each = round(tot / n, 2)
    out.pop()
    for i in range(n):
        s = dict(r)
        s["month"] = ym_shift(r["month"], i)
        s["cost"] = each if i < n - 1 else round(tot - each * (n - 1), 2)
        s["share"] = "month %d of %d · %s %s" % (i + 1, n, rs(tot), why)
        out.append(s)


def _life_n(f, p):
    """The months a battery's cost is spread over: its place's usual life, or fewer when it was taken out sooner (K1 C6)."""
    n = int(p["life_months"] or 0)
    fm, rm = _iso(f["fitted_on"]), _iso(f["removed_on"])
    if n and fm is not None and rm is not None:
        n = min(n, max(1, (rm.year - fm.year) * 12 + rm.month - fm.month + 1))
    return n


def fy_start(ym):
    """The first month of the financial year (April) that holds `ym`."""
    y, m = int(ym[:4]), int(ym[5:7])
    return "%04d-%02d" % (y if m >= FY_START_MONTH else y - 1, FY_START_MONTH)


def size_of(text):
    """A film size read from words such as 'DHL 8*10 150SH' or '11 x 14' -> '8×10', '11×14'; '' when none is written."""
    m = SIZE.search(text or "")
    if not m:
        return ""
    a, b = sorted((int(m.group(1)), int(m.group(2))))
    return "%d×%d" % (a, b)


def _sup1(v):
    bt = sys.modules.get("batteries")
    if bt is not None and hasattr(bt, "sup1"):
        return bt.sup1(v)
    w = re.sub(r"[^a-z0-9 ]", " ", (v or "").lower()).split()
    return w[0] if w else ""


def _desk_films(db):
    """Every film paper on the desk (the films section's groups), any month: not set aside, not a second scan."""
    sd = _sd()
    sec = _films_section(sd) if sd is not None else None
    subs = tuple(sec[2]) if sec else ("xray_small", "xray_11x14", "xray")
    try:
        return db.execute("SELECT id, stamp_no, vendor, bill_date, total_amount FROM bills WHERE subgroup IN (%s) AND COALESCE(status,'')<>'rejected' "
                          "AND dup_of IS NULL" % ",".join("?" * len(subs)), subs).fetchall()
    except sqlite3.Error:
        return []


def _paid(db, sd, key, subs, ym, cache):
    """The month's own selection (sd._s566_paid_rows), read once per section and month for the whole page (K1 C4)."""
    ck = ("paid", key, ym)
    if ck not in cache:
        cache[ck] = sd._s566_paid_rows(db, key, subs, ym)
    return cache[ck]


def _counted_film(db, b, cache):
    """True when The month counts this desk paper among the films of its own month."""
    sd = _sd()
    sec = _films_section(sd) if sd is not None else None
    cp = sys.modules.get("clinic_papers")
    if sec is None or cp is None:
        return False
    try:
        mo = db.execute("SELECT " + cp.MONTH_OF + " FROM bills b WHERE b.id=?", (b["id"],)).fetchone()[0]
    except (sqlite3.Error, TypeError):
        return False
    if not ym_ok(mo):
        return False
    money, finals = _paid(db, sd, sec[0], sec[2], mo, cache)
    return b["id"] in {x["id"] for x in list(money) + list(finals)}


def _desk_twin(db, desk, r, cache):
    """The desk film paper that IS this machine record's bill AND that The month counts: first the record's own bill link, then
    the same supplier and date with the amount of its typed lines or of its record price (K1 C3). None when there is no such
    paper -- the record's lines then count here."""
    try:
        x = db.execute("SELECT bill_id FROM assets WHERE id=?", (r["aid"],)).fetchone()
        bid = x[0] if x else None
    except sqlite3.Error:
        bid = None
    if bid:
        for b in desk:
            if b["id"] == bid:
                return b if _counted_film(db, b, cache) else None
    k = _sup1(r["vendor"])
    amts = [a for a in (r["amount"], r["price"]) if a is not None]
    for b in desk:
        if (k and _sup1(b["vendor"]) == k and str(b["bill_date"] or "")[:10] == str(r["date"] or "")[:10]
                and b["total_amount"] is not None and any(abs(float(b["total_amount"]) - float(a)) < 1 for a in amts)
                and _counted_film(db, b, cache)):
            return b
    return None


def film_assets(db, cache):
    """Film bills kept on the Machines list (before the sorting desk): every machine record with live film lines -- its date, its
    lines and their sum. A record whose bill is also a film paper on the desk is shown 'also on the desk' and counted there, once."""
    if "film_assets" in cache:
        return cache["film_assets"]
    out, by = [], {}
    try:
        lines = db.execute("SELECT l.*, a.name, a.vendor, a.purchase_date, a.price FROM xray_film_line l JOIN assets a ON a.id=l.asset_id "
                           "AND COALESCE(a.created_at,'')=l.asset_created_at WHERE l.voided_at='' ORDER BY a.purchase_date, a.id, l.id").fetchall()
    except sqlite3.Error:
        lines = []
    for l in lines:
        r = by.get(l["asset_id"])
        if r is None:
            r = by[l["asset_id"]] = {"aid": l["asset_id"], "name": l["name"], "vendor": l["vendor"] or "", "date": l["purchase_date"],
                                     "month": _month_of(l["purchase_date"]), "price": l["price"], "lines": [], "amount": 0.0, "dup": None}
            out.append(r)
        r["lines"].append({"id": l["id"], "size": l["size"], "boxes": l["boxes"], "amount": float(l["amount"] or 0)})
        r["amount"] += float(l["amount"] or 0)
    desk = _desk_films(db) if out else []
    for r in out:
        r["dup"] = _desk_twin(db, desk, r, cache)
    cache["film_assets"] = out
    return out


def film_candidates(db, cache):
    """Machine records that look like film bills (the word film, the supplier Jugnu -- the owner's word, 22-Oct -- or a size such as
    8*10 in the name, supplier or serial) and every record that already has film lines -- never counted until its lines are typed."""
    have = {r["aid"]: r for r in film_assets(db, cache)}
    out = []
    try:
        rows = db.execute("SELECT id, name, vendor, serial_no, purchase_date, price FROM assets ORDER BY purchase_date, id").fetchall()
    except sqlite3.Error:
        rows = []
    for a in rows:
        txt = " ".join(str(a[k] or "") for k in ("name", "vendor", "serial_no"))
        if a["id"] in have or LOOKS_FILM.search(txt):
            r = have.get(a["id"])
            out.append({"id": a["id"], "name": a["name"], "vendor": a["vendor"] or "", "date": a["purchase_date"], "price": a["price"],
                        "hint": size_of(a["serial_no"] or "") or size_of(a["name"] or ""), "lines": r["lines"] if r else [],
                        "amount": r["amount"] if r else 0.0, "dup": r["dup"] if r else None})
    return out


def film_ledger(db, cache, fr, to):
    """Every film purchase from month `fr` to `to`, oldest first, with the running boxes and rupees of its size: the desk's film
    papers by The month's own rule (their read item lines give the size and the boxes; each line takes its share of the paper's
    total by its own amount), then the film bills kept on the Machines list. A paper claimed by a spend, cover or battery row is
    left out (it counts there)."""
    sd = _sd()
    sec = _films_section(sd) if sd is not None else None
    claims = (cache.get("claims") or ([], {}))[1]
    rows, ym, n = [], fr, 0
    while sec is not None and ym <= to and n < 60:
        money, finals = _paid(db, sd, sec[0], sec[2], ym, cache)
        for b in list(money) + list(finals):
            if b["id"] in claims:
                continue
            tot = float(b["total_amount"] or 0)
            parts = []
            try:
                its = db.execute("SELECT item_name, quantity, rate, amount FROM bill_items WHERE bill_id=? ORDER BY id", (b["id"],)).fetchall()
            except sqlite3.Error:
                its = []
            for it in its:
                a = it["amount"] if it["amount"] is not None else (it["quantity"] or 0) * (it["rate"] or 0)
                parts.append((size_of(it["item_name"]), it["quantity"], float(a or 0)))
            base = sum(p[2] for p in parts)
            if not parts or base <= 0:
                parts, base = [({"xray_11x14": "11×14"}.get(b["subgroup"] or "", ""), None, 1.0)], 1.0
            for sz, q, a in parts:
                rows.append({"date": b["bill_date"] or b["created_at"], "month": ym, "size": sz or "size not read", "boxes": q,
                             "amount": round(tot * a / base, 2), "src": _stamp(b), "href": _href(b["id"]), "vendor": b["vendor"] or "",
                             "noamt": a <= 0})                        # K1 C1: a line read with no amount -- its size gets no per-box price
        ym, n = ym_shift(ym, 1), n + 1
    for r in film_assets(db, cache):
        if r["dup"] is not None or not r["month"] or not (fr <= r["month"] <= to):
            continue
        for l in r["lines"]:
            rows.append({"date": r["date"], "month": r["month"], "size": l["size"], "boxes": l["boxes"], "amount": l["amount"],
                         "src": "machine record", "href": url_for("asset_view", aid=r["aid"]), "vendor": r["vendor"]})
    rows.sort(key=lambda x: (str(x["date"] or "")[:10], x["src"]))
    run = {}
    for x in rows:
        s = run.setdefault(x["size"], {"boxes": 0.0, "amount": 0.0, "nobox": 0})
        if x["boxes"] is None or x.get("noamt"):
            s["nobox"] += 1
        if x["boxes"] is None:
            pass
        else:
            s["boxes"] += float(x["boxes"])
        s["amount"] += x["amount"]
        x["run_boxes"], x["run_amount"] = s["boxes"], s["amount"]
    sizes = [{"size": k, "boxes": v["boxes"], "amount": v["amount"], "nobox": v["nobox"],
              "per_box": (v["amount"] / v["boxes"]) if (v["boxes"] and not v["nobox"]) else None} for k, v in sorted(run.items())]
    return {"rows": rows, "sizes": sizes, "total": sum(x["amount"] for x in rows), "from": fr, "to": to}


def fy_rows(db, cache, ym, this):
    """The financial year that holds `ym`, month by month from April to the current month (or March): each month's own view."""
    fr = fy_start(ym)
    to = min(ym_shift(fr, 11), this)
    rows, m, tot = [], fr, 0.0
    while m <= to:
        v = month_view(db, m, cache)
        rows.append({"ym": m, "films": v.films_total, "papers": v.papers_total, "machines": v.machines_total,
                     "batteries": v.batteries_total, "total": v.total})
        tot += v.total
        m = ym_shift(m, 1)
    return {"from": fr, "to": to, "rows": rows, "total": tot}


def _num(v):
    s = str(v or "").replace(",", "").replace("₹", "").strip()
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        raise ValueError("'%s' is not a number." % s[:12])
    if f != f or f in (float("inf"), float("-inf")):
        raise ValueError("'%s' is not a number." % s[:12])
    return f


def post_film():
    """S633 (D767): a film bill kept on the Machines list gets its lines (size, boxes, the amount with tax) -- or loses one (kept,
    voided). Writes ONLY xray_film_line (and the audit); never the machine record. The owner only (the route's gate)."""
    db = AR.get_db()
    f = request.form
    do = (f.get("do") or "").strip()
    ym = f.get("ym") if ym_ok(f.get("ym")) else None
    try:
        if do == "add":
            try:
                aid = int(f.get("asset") or 0)
            except ValueError:
                aid = 0
            a = db.execute("SELECT id, name, created_at FROM assets WHERE id=?", (aid,)).fetchone()
            if a is None:
                raise ValueError("There is no such machine record.")
            sz = size_of(f.get("size") or "") or re.sub(r"\s+", " ", f.get("size") or "").strip()[:20]
            if not sz:
                raise ValueError("Choose the film size.")
            boxes = _num(f.get("boxes"))
            if boxes is not None and boxes < 0:
                raise ValueError("Boxes cannot be below zero.")
            amt = _num(f.get("amount"))
            if amt is None or amt <= 0:
                raise ValueError("Type the line's amount in rupees, as on the bill with tax.")
            db.execute("INSERT INTO xray_film_line(asset_id, asset_created_at, size, boxes, amount, by_whom, at) VALUES(?,?,?,?,?,?,?)",
                       (a["id"], a["created_at"] or "", sz, boxes, amt, _who(), _now()))
            _audit(db, "xray_film_line", {"asset": a["id"], "size": sz})
            db.commit()
            flash("Saved: %s — %s%s, %s." % (a["name"], sz, (" × %g box%s" % (boxes, "" if boxes == 1 else "es")) if boxes is not None else "", rs(amt)))
        elif do == "void":
            try:
                lid = int(f.get("line") or 0)
            except ValueError:
                lid = 0
            n = db.execute("UPDATE xray_film_line SET voided_at=?, voided_by=? WHERE id=? AND voided_at=''", (_now(), _who(), lid)).rowcount
            if n:
                _audit(db, "xray_film_line_voided", {"line": lid})
            db.commit()
            flash("Removed the film line (kept in the records)." if n else "That line was already removed.")
        else:
            abort(400)
    except ValueError as e:
        db.rollback()
        flash(str(e) + " Nothing was saved.")
    return redirect(url_for("s582_xray", ym=ym, _anchor="s633fassets") if ym else url_for("s582_xray", _anchor="s633fassets"))


'''

EDITS = {"xray_costs.py": [
    # Y1 the docstring
    ('''    of that key in the table, live or removed, means "leave it").
"""''',
     '''    of that key in the table, live or removed, means "leave it").

S633_XRAY_FULL_YEAR (D767; the owner, 22:11 IST 22-Oct-2026: "all from April needed there ... film size wise incremental
procurement with dates ... Amc needs to be assessed monthly, fdr battery, xray online ups battery also need to be appropriately
accounted for")
    The page shows the financial year from April, month by month (films, AMC and service, batteries, marked papers, total). An AMC,
    CMC or insurance cover with a cost is spread evenly over its months (from-day to till-day); a battery's price, less the old
    battery's, over its place's usual life; a service or repair spend stays on its date. "Film purchases by size" lists every film
    bill of the year oldest first, with the running boxes and rupees of each size -- the desk's film papers by The month's own rule
    (sizes and boxes from their read item lines), and the film bills kept on the Machines list before the desk, which count once
    their lines are typed on this page (table xray_film_line, additive; a record also on the desk counts there, once).
"""'''),
    # Y2 constants
    ('''VERSION = "S582"
''',
     '''VERSION = "S582"
FULL_YEAR = "S633"            # S633 (D767): the year from April, film purchases by size, the spreads
FY_START_MONTH = 4            # the financial year starts in April
SPREAD_KINDS = ("amc", "cmc", "insurance")                        # a cover of these kinds with a cost is spread over its months
SIZE = re.compile(r"(\\d{1,2})\\s*(?:\\*|x|X|×)\\s*(\\d{1,2})")
FILM_SIZES = ("8×10", "10×12", "11×14", "14×17")
LOOKS_FILM = re.compile(r"\\bfilms?\\b|jugnu|\\b\\d{1,2}\\s*[*x×]\\s*\\d{1,2}\\b", re.I)
'''),
    # Y3 the film-line table
    ('''    "CREATE UNIQUE INDEX IF NOT EXISTS xray_mark_live ON xray_mark(kind, ref_id, ref_created_at) WHERE removed_at=''",
)''',
     '''    "CREATE UNIQUE INDEX IF NOT EXISTS xray_mark_live ON xray_mark(kind, ref_id, ref_created_at) WHERE removed_at=''",
    "CREATE TABLE IF NOT EXISTS xray_film_line(id INTEGER PRIMARY KEY, asset_id INTEGER NOT NULL, asset_created_at TEXT NOT NULL DEFAULT '', "
    "size TEXT NOT NULL, boxes REAL, amount REAL NOT NULL, by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', "
    "voided_by TEXT NOT NULL DEFAULT '')",                                              # S633 (D767)
)'''),
    # Y4 a cover with a cost is spread over its months
    ('''                        "papers": [p] if p is not None else [], "stale": st == "stale", "note": note})''',
     '''                        "papers": [p] if p is not None else [], "stale": st == "stale", "note": note})
            _s633_spread(out, (c["kind"] in SPREAD_KINDS and c["cost"] is not None and bool((c["from_day"] or "").strip())),
                         _span(c["from_day"], c["till_day"]), "spread over its cover months")                    # S633 (D767)
            if c["kind"] in SPREAD_KINDS and c["cost"] and not _span(c["from_day"], c["till_day"]):              # K1 C7
                out[-1]["note"] = (out[-1]["note"] + " · " if out[-1]["note"] else "") + "no till-day — not spread"'''),
    # Y5 a battery's net price is spread over its place's usual life
    ('''                        "cost": float(f["price"] or 0), "nocost": f["price"] is None, "papers": papers, "stale": stale, "note": ""})''',
     '''                        "cost": float(f["price"] or 0) - float(f["old_amount"] or 0), "nocost": f["price"] is None, "papers": papers,
                        "stale": stale, "note": ("price %s less the old battery %s" % (rs(f["price"]), rs(f["old_amount"]))) if f["old_amount"] else ""})
            _s633_spread(out, f["price"] is not None, _life_n(f, p),
                         "spread to the month it was taken out" if f["removed_on"] else "spread over its usual life")   # S633 (D767)'''),
    # Y6 a paper is claimed once per row, not once per share
    ('''                claim.setdefault(p["id"], []).append(r)''',
     '''                lst = claim.setdefault(p["id"], [])
                if all((x["src"], x["id"]) != (r["src"], r["id"]) for x in lst):          # S633: a spread row's shares claim once
                    lst.append(r)'''),
    # Y7 the film bills kept on the Machines list count with the films of their month
    ('''            v.films_total = v.films_month_total - sum(float(r["amount"] or 0) for r in v.films_claimed)''',
     '''            v.films_total = v.films_month_total - sum(float(r["amount"] or 0) for r in v.films_claimed)
    fa = film_assets(db, cache)                                       # S633 (D767): film bills kept on the Machines list, by their date
    v.film_assets = [r for r in fa if r["month"] == ym and r["lines"]]
    v.film_assets_total = sum(r["amount"] for r in v.film_assets if r["dup"] is None)
    v.films_total += v.film_assets_total
    fa_bills = set()                                                  # K1 C2: a film record's own bill, marked for X-ray, counts once
    for r_ in fa:
        try:
            x_ = db.execute("SELECT bill_id FROM assets WHERE id=?", (r_["aid"],)).fetchone()
        except sqlite3.Error:
            x_ = None
        if x_ and x_[0] and r_["dup"] is None and r_["lines"]:
            fa_bills.add(x_[0])'''),
    # K1 C2 / C4: a marked paper that is a film record's bill; the month's selection read once per section and month
    ('''                elif b["id"] in film_ids:''',
     '''                elif b["id"] in fa_bills:
                    row["why"] = "already counted under the film bill kept on the Machines list"
                elif b["id"] in film_ids:'''),
    ('''            money, finals = sd._s566_paid_rows(db, key, subs, ym)''',
     '''            money, finals = _paid(db, sd, key, subs, ym, cache)'''),
    ('''                        money, finals = sd._s566_paid_rows(db, sec[0], sec[2], ym)''',
     '''                        money, finals = _paid(db, sd, sec[0], sec[2], ym, cache)'''),
    # Y8 the new functions
    ('''# ---------------------------------------------------------------------------------------------- the page
CSS = """<style>''',
     NEW_FUNCS + '''# ---------------------------------------------------------------------------------------------- the page
CSS = """<style>'''),
    # Y9 the page's data
    ('''    first, since = since_total(db, cache, this)''',
     '''    first, since = None, 0.0                                          # S633 (D767): the financial year replaces "since <first month>"
    fy = fy_rows(db, cache, ym, this)
    ledger = film_ledger(db, cache, fy["from"], fy["to"])
    fc = film_candidates(db, cache)'''),
    ('''                   has_bt=_bt() is not None, flow=AR._flow("X-ray expenses", back))''',
     '''                   has_bt=_bt() is not None, fy=fy, ledger=ledger, fcands=fc, sizes=FILM_SIZES, fopen=any(not a["lines"] for a in fc),
                   flow=AR._flow("X-ray expenses", back))'''),
    # Y10 the head line and the year
    ('''<b>{{rs(v.total)}}</b> this month{% if first %} · <b>{{rs(since)}}</b> since {{label(first)}}{% else %} · nothing counted for X-ray yet{% endif %}</p>''',
     '''<b>{{rs(v.total)}}</b> this month · <b>{{rs(fy.total)}}</b> this financial year (from {{label(fy.from)}})</p>
<details class=card id=s633fy open data-total="{{'%.2f'|format(fy.total)}}"><summary>This financial year — {{label(fy.from)}} to {{label(fy.to)}} <span class=amt>{{rs(fy.total)}}</span></summary>
<div style="overflow-x:auto"><table style="min-width:620px"><colgroup><col style="width:22%"><col><col><col><col><col></colgroup><tr><th>Month</th><th class=r>Films</th><th class=r>AMC, service</th><th class=r>Batteries</th><th class=r>Papers marked</th><th class=r>Total</th></tr>
{% for r in fy.rows %}<tr data-fy="{{r.ym}}"{% if r.ym == v.ym %} style="font-weight:600"{% endif %}><td><a href="{{url_for('s582_xray', ym=r.ym)}}">{{label(r.ym)}}</a></td><td class=r>{{rs(r.films)}}</td><td class=r>{{rs(r.machines)}}</td><td class=r>{{rs(r.batteries)}}</td><td class=r>{{rs(r.papers)}}</td><td class=r>{{rs(r.total)}}</td></tr>{% endfor %}
<tr style="font-weight:600"><td>Total</td><td class=r>{{rs(fy.rows|sum(attribute='films'))}}</td><td class=r>{{rs(fy.rows|sum(attribute='machines'))}}</td><td class=r>{{rs(fy.rows|sum(attribute='batteries'))}}</td><td class=r>{{rs(fy.rows|sum(attribute='papers'))}}</td><td class=r>{{rs(fy.total)}}</td></tr></table></div>
<p class=sub style="margin:6px 0 0">Films by their bill’s month; an AMC spread evenly over its months; a battery’s cost spread over its usual life.</p></details>'''),
    # Y11 the films fold: the film bills kept on the Machines list
    ('''{% else %}<p class=muted>No X-ray film paper counted this month.</p>{% endif %}{% endif %}</details>''',
     '''{% else %}<p class=muted>No X-ray film paper on the desk this month.</p>{% endif %}{% endif %}
{% if v.film_assets %}<p class=sub style="margin:10px 0 0">Film bills kept on the Machines list:</p><table>{{cols}}<tr><th>Date</th><th>What</th><th>Supplier</th><th class=r>Amount</th><th>Record</th></tr>
{% for r in v.film_assets %}<tr data-fasset="{{r.aid}}"><td>{{dmy(r.date)}}</td><td>{% for l in r.lines %}{{l.size}}{% if l.boxes is not none %} × {{'%g'|format(l.boxes)}}{% endif %}{{', ' if not loop.last}}{% endfor %}{% if r.dup %}<div class=sub>also on the desk as {{r.dup['stamp_no'] or ''}} — counted there</div>{% endif %}</td><td>{{r.vendor}}</td>
<td class=r>{% if r.dup %}<span class=sub>{{rs(r.amount)}}</span>{% else %}{{rs(r.amount)}}{% endif %}</td><td><a href="{{url_for('asset_view', aid=r.aid)}}">machine record</a></td></tr>{% endfor %}</table>{% endif %}</details>'''),
    # Y12 the machines fold: the spread, in words
    ('''<p class=sub style="margin:6px 0 0">Spends by their date, covers by their from-date. A machine’s purchase price is the asset, not an expense here.</p>''',
     '''<p class=sub style="margin:6px 0 0">Spends by their date. An AMC, CMC or insurance with a cost is spread evenly over its months; any other cover counts on its from-date. A machine’s purchase price is the asset, not an expense here.</p>'''),
    ('''<a href="{{url_for('asset_view', aid=r.aid)}}">{{r.what}}</a>{% if r.note %} <span class=flag>{{r.note}}</span>{% endif %}''',
     '''<a href="{{url_for('asset_view', aid=r.aid)}}">{{r.what}}</a>{% if r.note %} <span class=flag>{{r.note}}</span>{% endif %}{% if r.share %}<div class=sub>{{r.share}}</div>{% endif %}'''),
    # Y13 the batteries fold: the spread, in words
    ('''<summary>Batteries of the X-ray places <span class=amt>{{rs(v.batteries_total)}}</span></summary>''',
     '''<summary>Batteries of the X-ray places <span class=amt>{{rs(v.batteries_total)}}</span></summary>
<p class=sub style="margin:6px 0 0">A battery’s price, less what the old battery fetched, is spread evenly over its place’s usual life (set on the battery place).</p>'''),
    ('''<a href="{{url_for('s571_place', pid=r.pid) if has_bt else '#'}}">{{r.what}}</a>''',
     '''<a href="{{url_for('s571_place', pid=r.pid) if has_bt else '#'}}">{{r.what}}</a>{% if r.share %}<div class=sub>{{r.share}}{% if r.note %} · {{r.note}}{% endif %}</div>{% endif %}'''),
    # Y14 the film purchases by size, and the film bills kept on the Machines list
    ('''<details class=card id=s582mmarks>''',
     '''<details class=card id=s633ledger data-total="{{'%.2f'|format(ledger.total)}}"><summary>Film purchases by size — {{label(ledger.from)}} to {{label(ledger.to)}} <span class=amt>{{rs(ledger.total)}}</span></summary>
<p class=sub style="margin:6px 0 0">Every film bill, oldest first, with the running boxes and rupees of its size — to set X-ray revenue against the film bought.</p>
{% if ledger.rows %}<table><colgroup><col><col style="width:120px"><col style="width:150px"><col style="width:130px"></colgroup><tr><th>Size</th><th class=r>Boxes</th><th class=r>Rupees</th><th class=r>Per box</th></tr>
{% for s in ledger.sizes %}<tr data-size="{{s.size}}"><td>{{s.size}}</td><td class=r>{{'%g'|format(s.boxes)}}{% if s.nobox %} <span class=sub>+ {{s.nobox}} not read</span>{% endif %}</td><td class=r>{{rs(s.amount)}}</td><td class=r>{{rs(s.per_box) if s.per_box else '—'}}</td></tr>{% endfor %}</table>
<div style="overflow-x:auto"><table style="min-width:620px"><colgroup><col style="width:105px"><col style="width:80px"><col style="width:70px"><col style="width:110px"><col><col style="width:130px"></colgroup><tr><th>Date</th><th>Size</th><th class=r>Boxes</th><th class=r>Rupees</th><th class=r>So far, this size</th><th>Bill</th></tr>
{% for x in ledger.rows %}<tr data-led="{{x.size}}"><td>{{dmy(x.date)}}</td><td>{{x.size}}</td><td class=r>{{'%g'|format(x.boxes) if x.boxes is not none else '—'}}</td><td class=r>{{rs(x.amount)}}</td><td class=r>{{'%g'|format(x.run_boxes)}} box{{'' if x.run_boxes == 1 else 'es'}} · {{rs(x.run_amount)}}</td><td><a href="{{x.href}}">{{x.src}}</a></td></tr>{% endfor %}</table></div>
{% else %}<p class=muted>No film bought in this period.</p>{% endif %}</details>

<details class=card id=s633fassets{{' open' if fopen}}><summary>Film bills kept on the Machines list <span class=muted style="font-weight:400">({{fcands|selectattr('lines')|list|length}} of {{fcands|length}} entered)</span></summary>
<p class=sub style="margin:6px 0 0">X-ray film bills recorded as machines before the sorting desk. Type each bill’s lines — the size, the boxes and the amount with tax — and the bill counts as film on its date. A record also on the desk counts there, once.</p>
{% for a in fcands %}<div style="border-top:1px solid #ECECE6;padding:8px 0" data-fcand="{{a.id}}"><b><a href="{{url_for('asset_view', aid=a.id)}}">{{a.name}}</a></b> <span class=sub>· {{a.vendor}} · {{dmy(a.date)}} · record price {{rs(a.price)}}{% if a.hint %} · reads {{a.hint}}{% endif %}</span>
{% for l in a.lines %}<div style="font-size:14px">{{l.size}}{% if l.boxes is not none %} × {{'%g'|format(l.boxes)}} box{{'' if l.boxes == 1 else 'es'}}{% endif %} — {{rs(l.amount)}} <form method=post class=inl action="{{url_for('s633_film')}}"><input type=hidden name=do value=void><input type=hidden name=line value="{{l.id}}"><input type=hidden name=ym value="{{v.ym}}"><button class="btn small">remove</button></form></div>{% endfor %}
{% if a.lines and a.price is not none and (a.amount - a.price)|abs >= 1 %}<div class=flag>lines {{rs(a.amount)}}, record price {{rs(a.price)}} — check</div>{% endif %}
{% if a.dup %}<div class=sub>also on the desk as {{a.dup['stamp_no'] or ''}} — counted there</div>{% endif %}
<form method=post action="{{url_for('s633_film')}}" style="display:flex;flex-wrap:wrap;gap:6px;align-items:flex-end;margin-top:4px"><input type=hidden name=do value=add><input type=hidden name=asset value="{{a.id}}"><input type=hidden name=ym value="{{v.ym}}">
<label style="margin:0">Size<select name=size>{% for s in sizes %}<option{{' selected' if s == a.hint}}>{{s}}</option>{% endfor %}</select></label>
<label style="margin:0">Boxes<input name=boxes inputmode=decimal style="max-width:70px;margin:0"></label><label style="margin:0">Amount ₹<input name=amount inputmode=decimal required style="max-width:110px;margin:0"></label><button class="btn small">Add line</button></form></div>
{% else %}<p class=muted>No machine record looks like a film bill.</p>{% endfor %}</details>

<details class=card id=s582mmarks>'''),
    # Y15 the new door
    ('''    app.add_url_rule("/xray/mark", "s582_mark", cr(_owner_gate(post_mark)), methods=["POST"])''',
     '''    app.add_url_rule("/xray/mark", "s582_mark", cr(_owner_gate(post_mark)), methods=["POST"])
    app.add_url_rule("/xray/film", "s633_film", cr(_owner_gate(post_film)), methods=["POST"])              # S633 (D767), the owner only'''),
]}


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    total = 0
    for f, edits in EDITS.items():
        with open(os.path.join(src, f), "rb") as h:
            raw = h.read()
        if md5b(raw) != FROM_PIN[f]:
            out("%s: FROM is %s, not the pin %s -- STOP" % (f, md5b(raw)[:8], FROM_PIN[f][:8]))
            return 1
        t = raw.decode("utf-8")
        for i, (a, b) in enumerate(edits, 1):
            n = t.count(a)
            if n != 1:
                out("%s: edit %d anchor found %d times (must be 1) -- STOP" % (f, i, n))
                return 1
            t = t.replace(a, b)
        data = t.encode("utf-8")
        with open(os.path.join(dst, f), "wb") as h:
            h.write(data)
        total += len(edits)
        out("%s: %d counted edit(s), %s -> %s" % (f, len(edits), FROM_PIN[f][:8], md5b(data)))
    out("make_s633: %d counted edits in all" % total)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
