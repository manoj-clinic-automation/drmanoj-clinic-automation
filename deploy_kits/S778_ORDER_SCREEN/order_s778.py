#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  order_s778.py  ·  v1.0  ·  kit S778_ORDER_SCREEN  ·  Session 425 (Sanjeevni)  ·  D890 (the owner's mock approved 10-Nov 15:08 IST)
#
#  THE ORDER SCREEN, THREE THINGS (the logic; porders_s454.py's S778 block mounts it and draws it):
#   (a) OLD ORDERS AT THE TOP of 'Order karna hai' -- every medicine ordered and not come 3 days after (Sundays not counted), in a red
#       box, its age big (orange under 7, red from 7), item · quantity · dealer · order date, 'Dobara order karo' / 'Ab nahi milta'.
#       Sources: the open carries (order_carry), the late orders' open lines (order_track.late_orders), Marg's old group
#       (order_sheet.open_order). One line per dealer + medicine. It leaves the box when its bill comes, it is ordered again, or
#       'Ab nahi milta' is tapped. On the dealer's card the line says 'PURANA · N din'.
#   (b) 'AB NAHI MILTA' (staff): the medicine leaves today's list at once; the doctor's Needs-you line '<staff> says <ITEM> is no longer
#       available (last bought <date>)' opens /finance/porders/s454/abnahi: 'Stop it everywhere' (an order_item_rule 'never' marked
#       'S778 until a bill brings it' -- off the order list, the system's plan and its proposals, Darpan's list and the comparison;
#       cleared by itself by the first Marg purchase line of the medicine after it) / 'Keep ordering'; Undo in one tap.
#   (c) THE WRONG-DEALER CHECK: a line to a dealer who has NEVER billed the medicine (purchase_line) while another dealer has -> a
#       warning on the card before sending ('<X> ke card par bhejo' / '<dealer> hi sahi', remembered) and in the red box
#       ('<X> ko order karo'); every catch listed for the doctor for a week.
#
#  Tables (its own): order_s778_again (a line put on a dealer's card by 'Dobara order karo' / a move) · order_s778_na (each
#  'Ab nahi milta' and the doctor's answer) · order_s778_dealer_ok ('<dealer> hi sahi') · order_s778_wd (the wrong-dealer catches).
#  It writes order_item_rule (rule 'never', note 'S778 ...') only on the doctor's 'Stop it everywhere', and order_carry's
#  dropped_at / dropped_by ('s778_na', 's778_moved') -- never Marg, purchase_line, or the rules' JSON lists.
#  Every wrapper is fail-soft: an error here leaves the screen exactly as it was before this kit.
# =============================================================================
import datetime as dt
import html as _html
import re
import sqlite3

VERSION = "1.0"
KIT = "S778_ORDER_SCREEN"
P = "/finance/porders"
OLD_AFTER = 3                                                  # working days after the order (Sundays not counted)
RED_FROM = 7
NOTE = "S778 until a bill brings it"

DDL = (
    "CREATE TABLE IF NOT EXISTS order_s778_again (id INTEGER PRIMARY KEY, supplier_norm TEXT NOT NULL, vendor TEXT NOT NULL, item TEXT NOT NULL,"
    " qty INTEGER NOT NULL, pack_size INTEGER NOT NULL DEFAULT 1, packing TEXT, rate_p INTEGER NOT NULL DEFAULT 0, kind TEXT NOT NULL, ref TEXT NOT NULL,"
    " src_day TEXT, from_sn TEXT, at TEXT NOT NULL, by TEXT, done_order_id INTEGER, done_at TEXT, cleared_at TEXT, cleared_by TEXT)",
    "CREATE TABLE IF NOT EXISTS order_s778_na (id INTEGER PRIMARY KEY, item_norm TEXT NOT NULL, item TEXT NOT NULL, supplier_norm TEXT, vendor TEXT,"
    " kind TEXT, ref TEXT, qty TEXT, by TEXT, at TEXT NOT NULL, last_bought TEXT, max_line INTEGER NOT NULL DEFAULT 0,"
    " status TEXT NOT NULL DEFAULT 'asked' CHECK (status IN ('asked','stop','keep','came')), answered_by TEXT, answered_at TEXT,"
    " prev_rule TEXT, prev_value INTEGER, prev_note TEXT, cleared_at TEXT, cleared_why TEXT)",
    "CREATE TABLE IF NOT EXISTS order_s778_dealer_ok (supplier_norm TEXT NOT NULL, item_norm TEXT NOT NULL, item TEXT, by TEXT, at TEXT,"
    " PRIMARY KEY (supplier_norm, item_norm))",
    "CREATE TABLE IF NOT EXISTS order_s778_wd (supplier_norm TEXT NOT NULL, item_norm TEXT NOT NULL, item TEXT NOT NULL, vendor TEXT, other_sn TEXT,"
    " other_vendor TEXT, first_at TEXT NOT NULL, outcome TEXT, outcome_at TEXT, outcome_by TEXT, PRIMARY KEY (supplier_norm, item_norm))",
)

# (staff Roman Hindi, the owner's English)
W = {
    "box": ("⚠ Purane order — maal abhi tak nahi aaya", "⚠ Old orders — the goods have not come"),
    "din": ("din", "days"),
    "orderd": ("order %s", "ordered %s"),
    "again": ("Dobara order karo", "Order again"),
    "na": ("Ab nahi milta", "No longer available"),
    "oncard": ("Aaj ke %s card par hai", "On today's %s card"),
    "wd_box": ("⚠ Galat dealer? %s hamesha %s se aaya hai (%d bill, aakhri %s). %s ne kabhi nahi diya.",
               "⚠ Wrong dealer? %s has always come from %s (%d bill%s, last %s). %s never supplied it."),
    "wd_card": ("⚠ Yeh dealer is dawa ko pehle kabhi nahi laya — %s laata hai (%d bill, aakhri %s).",
                "⚠ This dealer has never brought this medicine — %s does (%d bill%s, last %s)."),
    "to_x": ("%s ko order karo", "Order from %s"),
    "move": ("%s ke card par bhejo", "Move to %s's card"),
    "ok": ("%s hi sahi", "%s is right"),
    "purana": ("PURANA · %d din", "OLD · %d days"),
    "na_done": ("%s — dealer ke paas nahi (doctor sahab ko bheja)", "%s — no longer available (sent to you to decide)"),
    "moved": ("%s — %s ke card par gaya", "%s — moved to %s's card"),
    "againd": ("%s — %s ke aaj ke card par", "%s — on %s's card today"),
    "wd_top": ("⚠ %d dawa galat dealer par ho sakti hai — neeche card dekhiye", "⚠ %d medicine%s may be on the wrong dealer — see the cards below"),
    "carry": ("pichhle order se baaki", "left from an earlier order"),
    "oncard_n": ("%d aur purani dawa aaj ke dealer card par hai — wahan PURANA likha hai", "%d more old medicine(s) are on today's dealer cards — marked OLD there"),
}


def T(en, k, *a):
    s = W[k][1 if en else 0]
    return s % a if a else s


def esc(s):
    return _html.escape(str(s if s is not None else ""), quote=True)


def _os():
    import order_sheet                                         # noqa: PLC0415
    return order_sheet


def _ot():
    import order_track                                         # noqa: PLC0415
    return order_track


def _or():
    import order_rules                                         # noqa: PLC0415
    return order_rules


def _pa():
    return _os()._pa()


def ensure(con):
    for s in DDL:
        con.execute(s)


def norm(item):
    return _pa().norm(item)


def forms(con, item, sn=None):
    gg = _g()
    memo = None
    if gg is not None:
        memo = getattr(gg, "s778_forms", None)
        if memo is None:
            memo = {}
            setattr(gg, "s778_forms", memo)
        if (item, sn) in memo:
            return memo[(item, sn)]
    out = forms_raw(con, item, sn)
    if memo is not None:
        memo[(item, sn)] = out
    return out


def forms_raw(con, item, sn=None):
    out = {norm(item)}
    try:
        for f in _ot()._names(con, item, sn):
            out.add(norm(f))
    except Exception:                                          # noqa: BLE001
        pass
    return out


def now_iso():
    return _os().now_iso()


def today():
    return _os().today()


def _date(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None


def workdays(day, t=None):
    """Days after `day` up to today, Sundays not counted (the owner's rule for 'old')."""
    d0 = _date(day)
    t = t or today()
    if not d0 or d0 >= t:
        return 0
    n = 0
    d = d0 + dt.timedelta(days=1)
    while d <= t:
        if d.weekday() != 6:
            n += 1
        d += dt.timedelta(days=1)
    return n


def ddmon(iso):
    d = _date(iso)
    return d.strftime("%d-%b") if d else ""


def short(v):
    try:
        return _ot().short_name(v)
    except Exception:                                          # noqa: BLE001
        return str(v or "").split(" ")[0].title()


def who_name(s):
    try:
        return _ot().who_name(s) or "Staff"
    except Exception:                                          # noqa: BLE001
        return str(s or "Staff")


# ------------------------------------------------------------------ who has billed what (purchase_line, read only)
_IDX = {"cur": (None, {}, {})}                                 # (key, by, names) -- replaced whole, never updated in place


def bill_index(con):
    """{item_norm: {supplier_norm: [bills set, last date]}} of every Marg purchase line, cached until purchase_line changes."""
    try:
        k = con.execute("SELECT COALESCE(MAX(rowid),0) FROM purchase_line").fetchone()[0]
    except sqlite3.Error:
        return {}
    cur = _IDX["cur"]
    if cur[0] == k:
        return cur[1]
    by = {}
    for sn, item, bill, day, d in con.execute("SELECT supplier_norm, item, bill_no, bill_date, direction FROM purchase_line"):
        if str(d or "PURCHASE").upper() != "PURCHASE" or not sn or not str(bill or "").strip():
            continue
        r = by.setdefault(norm(item), {}).setdefault(sn, [set(), ""])
        r[0].add(str(bill).strip())
        if day and str(day) > r[1]:
            r[1] = str(day)
    names = {}
    try:
        for sn, s in con.execute("SELECT supplier_norm, supplier FROM purchase_bill GROUP BY supplier_norm"):
            names[sn] = s
    except sqlite3.Error:
        pass
    _IDX["cur"] = (k, by, names)
    return by


def billed_by(con, item, fs=None):
    idx = bill_index(con)
    out = {}
    for f in (fs or forms(con, item)):
        for sn, (bills, last) in (idx.get(f) or {}).items():
            o = out.setdefault(sn, [set(), ""])
            o[0] |= bills
            o[1] = max(o[1], last)
    return {sn: (len(b), last) for sn, (b, last) in out.items()}


def last_bought(con, item):
    b = billed_by(con, item)
    return max([v[1] for v in b.values()] or [""])


def vendor_of(con, sn):
    bill_index(con)
    v = _IDX["cur"][2].get(sn)
    if not v:
        r = con.execute("SELECT vendor FROM purchase_order WHERE supplier_norm=? ORDER BY id DESC LIMIT 1", (sn,)).fetchone()
        v = r[0] if r else sn
    return v


def wrong_dealer(con, sn, item, vendor="", fs=None):
    """None, or the dealer who does bring it: a line to `sn`, who has NEVER billed the medicine, while another dealer has."""
    fs = fs or forms(con, item, sn)
    if con.execute("SELECT 1 FROM order_s778_dealer_ok WHERE supplier_norm=? AND item_norm=?", (sn, norm(item))).fetchone():
        return None
    b = billed_by(con, item, fs)
    if not b or sn in b:
        return None
    osn, (n, last) = sorted(b.items(), key=lambda kv: (kv[1][0], kv[1][1]), reverse=True)[0]
    ov = vendor_of(con, osn)
    try:
        wk = (today() - dt.timedelta(days=7)).isoformat()
        cur = con.execute("INSERT INTO order_s778_wd (supplier_norm, item_norm, item, vendor, other_sn, other_vendor, first_at) VALUES (?,?,?,?,?,?,?) "
                          "ON CONFLICT(supplier_norm, item_norm) DO UPDATE SET first_at=excluded.first_at, other_sn=excluded.other_sn, "
                          "other_vendor=excluded.other_vendor, outcome=NULL, outcome_at=NULL, outcome_by=NULL WHERE order_s778_wd.first_at<?",
                          (sn, norm(item), item, vendor or vendor_of(con, sn), osn, ov, now_iso(), wk))
        if cur.rowcount:
            con.commit()                                       # the doctor's week keeps every catch, from any screen
    except sqlite3.Error:
        pass
    return dict(other_sn=osn, other_vendor=ov, other=short(ov), n=n, last=last, dealer=short(vendor or vendor_of(con, sn)))


# ------------------------------------------------------------------ 'Ab nahi milta' -- what is held
def na_rows(con, statuses=("asked", "stop")):
    return [dict(r) for r in con.execute("SELECT * FROM order_s778_na WHERE cleared_at IS NULL AND status IN (%s) ORDER BY id"
                                         % ",".join("?" * len(statuses)), statuses)]


def hidden(con):
    """{item_norm} held off today's list: asked (waiting for the doctor) or stopped."""
    return {r["item_norm"] for r in na_rows(con)}


def na_since(con, fs, day):
    for r in con.execute("SELECT item_norm, at FROM order_s778_na WHERE status IN ('asked','stop','keep') AND cleared_at IS NULL"):
        if r[0] in fs and str(r[1])[:10] >= str(day or "")[:10]:
            return True
    return False


def clear_by_bills(con):
    """A Marg purchase line of the medicine, newer than the tap (a line added after it, dated on or after its day), ends the hold:
    an 'asked' row becomes 'came'; a stopped one's rule is lifted (the rule it replaced put back)."""
    n = 0
    for r in na_rows(con):
        fs = forms(con, r["item"])
        hit = None
        for lid, item, bill, day in con.execute(
                "SELECT p.id, p.item, p.bill_no, p.bill_date FROM purchase_line p WHERE p.id>? AND p.bill_date>=? AND UPPER(COALESCE(p.direction,'PURCHASE'))='PURCHASE' "
                "AND NOT EXISTS (SELECT 1 FROM purchase_line q WHERE q.id<=? AND q.supplier_norm=p.supplier_norm AND q.bill_no=p.bill_no) ORDER BY p.id",
                (int(r["max_line"] or 0), str(r["at"])[:10], int(r["max_line"] or 0))):
            if norm(item) in fs:
                hit = (bill, day)
                break
        if not hit:
            continue
        why = "bill %s %s" % (hit[0], ddmon(hit[1]))
        if r["status"] == "stop":
            _lift(con, r, "bill")
        _unhold_sheet(con, r)
        con.execute("UPDATE order_s778_na SET status=CASE WHEN status='asked' THEN 'came' ELSE status END, cleared_at=?, cleared_why=? WHERE id=?",
                    (now_iso(), why, r["id"]))
        _os().audit(con, "s778", "s778_na_cleared", r["id"], dict(item=r["item"], why=why, kit=KIT))
        n += 1
    if n:
        con.commit()
    return n


def _hold_sheet(con, who, kind, ref, item):
    """A Marg sheet line held by 'Ab nahi milta' is also taken off Marg's open order as the papers read it (sheet.pdf, marg.pdf, the
    tick's process): a removal edit with the reason 's778_na', taken back on Keep ordering, Undo or a bill."""
    if kind == "sheet" and ref:
        con.execute("INSERT INTO s454_line_edit (src, ref, item, qty, removed, by, at, reason) VALUES ('sheet',?,?,NULL,1,?,?,'s778_na') "
                    "ON CONFLICT(src, ref, item) DO UPDATE SET removed=1, by=excluded.by, at=excluded.at, reason=excluded.reason", (str(ref), item, who, now_iso()))


def _unhold_sheet(con, r):
    if r.get("kind") == "sheet" and r.get("ref"):
        con.execute("DELETE FROM s454_line_edit WHERE src='sheet' AND ref=? AND item=? AND reason='s778_na'", (str(r["ref"]), r["item"]))


def _lift(con, r, who):
    """Take the 'never' rule off -- only while it is still this kit's -- and put back the rule it replaced."""
    row = con.execute("SELECT rule, note FROM order_item_rule WHERE item_norm=?", (r["item_norm"],)).fetchone()
    if not row or row[0] != "never" or not str(row[1] or "").startswith("S778"):
        return False
    if r.get("prev_rule"):
        con.execute("UPDATE order_item_rule SET rule=?, value=?, note=?, set_by=?, set_at=? WHERE item_norm=?",
                    (r["prev_rule"], r.get("prev_value"), r.get("prev_note"), who, now_iso(), r["item_norm"]))
    else:
        con.execute("DELETE FROM order_item_rule WHERE item_norm=?", (r["item_norm"],))
    try:
        _or()._audit(con, who, None, "item:never", "never (S778)", r.get("prev_rule") or "off")
    except Exception:                                          # noqa: BLE001
        pass
    return True


# ------------------------------------------------------------------ (a) the red box: the old lines
def red_lines(con, en=False, cards=None):
    """[line] -- every medicine ordered and not come, OLD_AFTER working days or more after its order, one per dealer + medicine,
    oldest first. Writes only the wrong-dealer catch (order_s778_wd)."""
    OS, OT = _os(), _ot()
    gg, key = _g(), "s778_red_%d" % (1 if en else 0)
    if gg is not None and getattr(gg, key, None) is not None:
        return getattr(gg, key)                                # one reading per page: the box, the cards' tags and their count
    ensure(con)
    t = today()
    now = OS.now()
    cards = OS.entries(con) if cards is None else cards
    on_card = {}
    for e in cards:
        for l in e["lines"]:
            on_card[(e["sn"], norm(l["item"]))] = e["vendor"]
    cand = []
    for c in OT.open_carries(con):
        ps = int(c.get("pack_size") or 1)
        cand.append(dict(kind="carry", ref=str(c["id"]), sn=c["supplier_norm"], vendor=c["vendor"], item=c["item"], packs=int(c["qty"]), pack_size=ps,
                         qty_text=_qty(con, en, c["item"], int(c["qty"]), ps), at=str(c.get("from_at") or c["at"]), from_order=c["from_order_id"]))
    try:
        late = OT.late_orders(con, now)
    except Exception:                                          # noqa: BLE001
        late = []
    for s in late:
        for x in s["lines"]:
            if x["state"] not in ("open", "part"):
                continue
            packs = max(int(x["packs"]) - int(x.get("came") or 0), 0) or int(x["packs"])
            cand.append(dict(kind="late", ref="%d:%d" % (s["id"], x["id"]), sn=s["sn"], vendor=s["vendor"], item=x["item"], packs=packs,
                             pack_size=int(x["pack_size"] or 1), qty_text=_qty(con, en, x["item"], packs, int(x["pack_size"] or 1)),
                             at=str(s["created_at"]), from_order=s["id"]))
    show = OS.int_setting(con, "order.old_show_days") or 60
    for l in OS.open_order(con)["groups"]["old"]:
        if l.get("removed") or l.get("dealer_no"):
            continue
        day = str(OS.old_day(l) or "")
        if not day or (t - (_date(day) or t)).days > show:
            continue
        cand.append(dict(kind="old", ref=str(l["id"]), sn=l["supplier_norm"], vendor=l["supplier"], item=l["item"], packs=int(l["qty"] or 0),
                         pack_size=int(l.get("pack_size") or 1), qty_text=OS.qty_of(l, en, pend=True, con=con), at=day,
                         from_order=(l.get("order_id") if l.get("state") == "ordered" else None), marg_line=(l["id"] if OS.can_reorder(l) else None),
                         note=OS.old_word(l, en), packing=l.get("packing") or "", rate_p=int(l.get("rate_p") or 0)))
    seen, out = set(), []
    for c in cand:
        fs = forms(con, c["item"], c["sn"])
        dk = (c["sn"], norm(c["item"]))
        if dk in seen:
            continue
        seen.add(dk)
        day = c["at"][:10]
        age = workdays(day, t)
        if age < OLD_AFTER:
            continue
        if na_since(con, fs, day):
            continue                                           # 'Ab nahi milta' was tapped for it
        if con.execute("SELECT 1 FROM order_s778_again WHERE kind=? AND ref=? AND cleared_at IS NULL", (c["kind"], c["ref"])).fetchone():
            continue                                           # already put on a card by Dobara / '<X> ko order karo' (open or ordered)
        try:
            if OT._ordered_since(con, c["sn"], c["item"], c["at"], exclude=c.get("from_order")):
                continue                                       # ordered again
        except Exception:                                      # noqa: BLE001
            pass
        c.update(day=day, age=age, red=(age >= RED_FROM), fs=sorted(fs),
                 on_card=next((on_card[(c["sn"], f)] for f in fs if (c["sn"], f) in on_card), ""))
        c["wrong"] = wrong_dealer(con, c["sn"], c["item"], c["vendor"], fs)
        out.append(c)
    out.sort(key=lambda c: (-c["age"], c["vendor"], c["item"]))
    try:
        con.commit()
    except sqlite3.Error:
        pass
    if gg is not None:
        setattr(gg, key, out)
    return out


def _g():
    try:
        from flask import g, has_app_context                  # noqa: PLC0415
        return g if has_app_context() else None
    except Exception:                                          # noqa: BLE001
        return None


def _qty(con, en, item, packs, ps):
    """The shop's one quantity text (order_sheet.qty_of: '10 patte' to the staff, '10 strips' to the owner)."""
    try:
        return _os().qty_of(dict(item=item, qty=int(packs), loose=0, strip=(1 if ps > 1 else 0), pack_size=ps), en, con=con)
    except Exception:                                          # noqa: BLE001
        return str(packs)


def old_of(con, sn):
    """{item_norm: age} of the dealer's red-box lines and its open again rows -- the 'PURANA · N din' tags on its card."""
    out = {}
    for c in red_lines(con):
        if c["sn"] == sn:
            for f in c["fs"]:
                out[f] = c["age"]
    for r in con.execute("SELECT item, src_day FROM order_s778_again WHERE supplier_norm=? AND done_at IS NULL AND cleared_at IS NULL", (sn,)):
        a = workdays(r[1])
        if a:
            out.setdefault(norm(r[0]), a)
    return out


def find_line(con, kind, ref, en=False):
    return next((c for c in red_lines(con, en) if c["kind"] == kind and c["ref"] == str(ref)), None)


# ------------------------------------------------------------------ the doors' work (each returns (dict, status))
def again(con, who, kind, ref, to_sn=""):
    """'Dobara order karo' (to_sn empty) / '<X> ko order karo' (to_sn): the line goes on the dealer's card today."""
    ensure(con)
    if con.execute("SELECT 1 FROM order_s778_again WHERE kind=? AND ref=? AND cleared_at IS NULL", (kind, str(ref))).fetchone():
        return dict(ok=True, already=True, item="", vendor=""), 200
    c = find_line(con, kind, ref)
    if not c:
        return dict(ok=False, error="gone", message="Yeh line ab purane order mein nahi hai."), 409
    sn = to_sn or c["sn"]
    if to_sn and (not c.get("wrong") or c["wrong"]["other_sn"] != to_sn):
        return dict(ok=False, error="bad_dealer", message="Yeh dealer is line ke liye nahi hai."), 409
    if not to_sn and c.get("on_card"):
        return dict(ok=True, already=True, item=c["item"], vendor=c["on_card"]), 200
    vendor = vendor_of(con, sn) if to_sn else c["vendor"]
    pk, rate = c.get("packing") or "", int(c.get("rate_p") or 0)
    if kind == "carry":
        try:
            cr = next(x for x in _ot().open_carries(con) if str(x["id"]) == str(ref))
            pk, rate = _os()._s619_line(con, cr)
        except Exception:                                      # noqa: BLE001
            pass
    t = now_iso()
    cur = con.execute("INSERT INTO order_s778_again (supplier_norm, vendor, item, qty, pack_size, packing, rate_p, kind, ref, src_day, from_sn, at, by) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (sn, vendor, c["item"], max(int(c["packs"]), 1), int(c["pack_size"] or 1), pk, rate if not to_sn else 0, kind, str(ref), c["day"],
                       c["sn"], t, who))
    if to_sn:
        if kind == "carry":
            con.execute("UPDATE order_carry SET dropped_at=?, dropped_by='s778_moved' WHERE id=? AND done_at IS NULL AND dropped_at IS NULL", (t, int(ref)))
        con.execute("UPDATE order_s778_wd SET outcome='moved', outcome_at=?, outcome_by=? WHERE supplier_norm=? AND item_norm=?", (t, who, c["sn"], norm(c["item"])))
    _os().audit(con, who, "s778_again", cur.lastrowid, dict(kind=kind, ref=str(ref), item=c["item"], to=sn, kit=KIT))
    con.commit()
    return dict(ok=True, id=cur.lastrowid, item=c["item"], vendor=short(vendor)), 200


def _card_line(con, sn, src, ref, item):
    e = _os().entry_of(con, sn)
    if not e:
        return None, None
    return e, next((l for l in e["lines"] if l["src"] == src and str(l["ref"]) == str(ref) and l["item"] == item), None)


def na(con, who, b):
    """'Ab nahi milta' -- from a red-box line (kind, ref) or a card line (sn, src, ref, item)."""
    ensure(con)
    kind, ref = str(b.get("kind") or ""), str(b.get("ref") or "")
    if kind in ("carry", "late", "old"):
        c = find_line(con, kind, ref)
        if not c:
            return dict(ok=False, error="gone", message="Yeh line ab purane order mein nahi hai."), 409
        item, sn, vendor, qty = c["item"], c["sn"], c["vendor"], c["qty_text"]
    else:
        sn, src, item = str(b.get("sn") or ""), str(b.get("src") or ""), str(b.get("item") or "")
        if src not in ("sheet", "proposal", "ortho", "carry", "s778"):
            return dict(ok=False, error="bad_line"), 400
        e, l = _card_line(con, sn, src, ref, item)
        if not l:
            return dict(ok=False, error="gone", message="Yeh line ab order mein nahi hai."), 409
        if e.get("draft") or e.get("state") != "pending":
            return dict(ok=False, error="has_draft", message="Is supplier ka order ban chuka hai — ab line nahi hat sakti."), 409
        kind, vendor, qty = src, e["vendor"], str(l.get("qty") or "")
    k = norm(item)
    if con.execute("SELECT 1 FROM order_s778_na WHERE item_norm=? AND status IN ('asked','stop') AND cleared_at IS NULL", (k,)).fetchone():
        return dict(ok=True, already=True, item=item), 200
    t = now_iso()
    mx = con.execute("SELECT COALESCE(MAX(id),0) FROM purchase_line").fetchone()[0]
    cur = con.execute("INSERT INTO order_s778_na (item_norm, item, supplier_norm, vendor, kind, ref, qty, by, at, last_bought, max_line) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (k, item, sn, vendor, kind, ref, qty, who, t, last_bought(con, item), int(mx or 0)))
    if kind == "carry":
        con.execute("UPDATE order_carry SET dropped_at=?, dropped_by='s778_na' WHERE id=? AND done_at IS NULL AND dropped_at IS NULL", (t, int(ref)))
    _hold_sheet(con, who, kind, ref, item)
    if kind == "s778":
        con.execute("UPDATE order_s778_again SET cleared_at=?, cleared_by=? WHERE id=? AND done_at IS NULL", (t, "na:" + who, int(ref)))
    _os().audit(con, who, "s778_na", cur.lastrowid, dict(item=item, kind=kind, ref=ref, supplier=vendor, kit=KIT))
    con.commit()
    return dict(ok=True, id=cur.lastrowid, item=item), 200


def na_answer(con, who, nid, answer):
    """The doctor: stop (Stop it everywhere) · keep (Keep ordering) · undo (a stop taken back)."""
    ensure(con)
    r = con.execute("SELECT * FROM order_s778_na WHERE id=?", (int(nid),)).fetchone()
    if not r:
        return dict(ok=False, error="gone"), 404
    r = dict(r)
    t = now_iso()
    if answer == "stop":
        if r["status"] != "asked" or r["cleared_at"]:
            return dict(ok=False, error="answered", message="Already answered."), 409
        cur = con.execute("SELECT rule, value, note FROM order_item_rule WHERE item_norm=?", (r["item_norm"],)).fetchone()
        prev = (cur[0], cur[1], cur[2]) if cur and not (cur[0] == "never" and str(cur[2] or "").startswith("S778")) else (None, None, None)
        if not (cur and cur[0] == "never"):
            con.execute("INSERT INTO order_item_rule (item_norm, item, rule, value, set_by, set_at, note) VALUES (?,?,?,?,?,?,?) ON CONFLICT(item_norm) DO UPDATE SET "
                        "rule='never', value=NULL, set_by=excluded.set_by, set_at=excluded.set_at, note=excluded.note",
                        (r["item_norm"], r["item"], "never", None, who, t, "%s · since %s" % (NOTE, ddmon(t))))
            try:
                _or()._audit(con, who, None, "item:never", ("%s %s" % (prev[0], prev[1])) if prev[0] else None, "never (S778, until a bill brings it)")
            except Exception:                                  # noqa: BLE001
                pass
        con.execute("UPDATE order_s778_na SET status='stop', answered_by=?, answered_at=?, prev_rule=?, prev_value=?, prev_note=? WHERE id=?",
                    (who, t, prev[0], prev[1], prev[2], r["id"]))
    elif answer == "keep":
        if r["status"] != "asked" or r["cleared_at"]:
            return dict(ok=False, error="answered", message="Already answered."), 409
        con.execute("UPDATE order_s778_na SET status='keep', answered_by=?, answered_at=? WHERE id=?", (who, t, r["id"]))
        _unhold_sheet(con, r)
    elif answer == "undo":
        if r["status"] != "stop" or r["cleared_at"]:
            return dict(ok=False, error="not_stopped", message="Not stopped."), 409
        _lift(con, r, who)
        _unhold_sheet(con, r)
        con.execute("UPDATE order_s778_na SET status='keep', answered_by=?, answered_at=? WHERE id=?", (who, t, r["id"]))
    else:
        return dict(ok=False, error="bad_answer"), 400
    _os().audit(con, who, "s778_na_" + answer, r["id"], dict(item=r["item"], kit=KIT))
    con.commit()
    return dict(ok=True, item=r["item"], status=answer), 200


def dealer_ok(con, who, sn, item):
    """'<dealer> hi sahi' -- remembered: this dealer is not asked about this medicine again."""
    ensure(con)
    if not sn or not item:
        return dict(ok=False, error="bad_line"), 400
    t = now_iso()
    con.execute("INSERT OR IGNORE INTO order_s778_dealer_ok (supplier_norm, item_norm, item, by, at) VALUES (?,?,?,?,?)", (sn, norm(item), item, who, t))
    con.execute("INSERT INTO order_s778_wd (supplier_norm, item_norm, item, vendor, first_at, outcome, outcome_at, outcome_by) VALUES (?,?,?,?,?,'kept',?,?) "
                "ON CONFLICT(supplier_norm, item_norm) DO UPDATE SET outcome='kept', outcome_at=excluded.outcome_at, outcome_by=excluded.outcome_by",
                (sn, norm(item), item, vendor_of(con, sn), t, t, who))
    _os().audit(con, who, "s778_dealer_ok", sn, dict(item=item, kit=KIT))
    con.commit()
    return dict(ok=True), 200


def move(con, who, b):
    """'<X> ke card par bhejo' -- a card line goes to the dealer who brings it."""
    ensure(con)
    sn, src, ref, item, to = (str(b.get(k) or "") for k in ("sn", "src", "ref", "item", "to"))
    if src not in ("sheet", "proposal", "ortho", "carry", "s778"):
        return dict(ok=False, error="bad_line"), 400
    e, l = _card_line(con, sn, src, ref, item)
    if not l:
        return dict(ok=False, error="gone", message="Yeh line ab order mein nahi hai."), 409
    if e.get("draft") or e.get("state") != "pending":
        return dict(ok=False, error="has_draft", message="Is supplier ka order ban chuka hai — ab line nahi hat sakti."), 409
    w = wrong_dealer(con, sn, item, e["vendor"])
    if not w or w["other_sn"] != to:
        return dict(ok=False, error="bad_dealer", message="Yeh dealer is line ke liye nahi hai."), 409
    t = now_iso()
    vendor = vendor_of(con, to)
    if src == "s778":
        con.execute("UPDATE order_s778_again SET supplier_norm=?, vendor=?, rate_p=0, from_sn=? WHERE id=? AND done_at IS NULL", (to, vendor, sn, int(ref)))
    else:
        con.execute("INSERT INTO s454_line_edit (src, ref, item, qty, removed, by, at, reason) VALUES (?,?,?,?,1,?,?,?) ON CONFLICT(src, ref, item) DO UPDATE SET "
                    "removed=1, by=excluded.by, at=excluded.at, reason=excluded.reason", (src, ref, item, None, who, t, "s778_moved"))
        if src == "carry":
            con.execute("UPDATE order_carry SET dropped_at=?, dropped_by='s778_moved' WHERE id=? AND done_at IS NULL AND dropped_at IS NULL", (t, int(ref)))
        ps = int(l.get("pack_size") or 1) if l.get("strip") else 1
        con.execute("INSERT INTO order_s778_again (supplier_norm, vendor, item, qty, pack_size, packing, rate_p, kind, ref, src_day, from_sn, at, by) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (to, vendor, item, max(int(l.get("qty") or 0), 1), ps, l.get("packing") or "", 0, "moved",
                                                          "%s:%s" % (src, ref), today().isoformat(), sn, t, who))
    con.execute("UPDATE order_s778_wd SET outcome='moved', outcome_at=?, outcome_by=? WHERE supplier_norm=? AND item_norm=?", (t, who, sn, norm(item)))
    _os().audit(con, who, "s778_move", ref, dict(src=src, item=item, frm=sn, to=to, kit=KIT))
    con.commit()
    return dict(ok=True, item=item, vendor=short(vendor)), 200


# ------------------------------------------------------------------ the wrappers (installed by porders_s454's S778 block)
def adjust_entries(con, out):
    """Today's cards, as order_sheet.entries made them, with (b) a held medicine taken off and (a) the again rows put on their
    dealer's card (a card made for a dealer that had none) -- never on a card whose WhatsApp is already in line (its draft)."""
    OS, OT = _os(), _ot()
    if _or()._frozen(con):
        return out                                             # ordering frozen: no card at all, as order_sheet.entries says
    ensure(con)
    hid = hidden(con)
    if hid:
        for e in out:
            e["lines"] = [l for l in e["lines"] if l.get("src") == "draft" or not (forms(con, l["item"], e["sn"]) & hid)]
    rows = [dict(r) for r in con.execute("SELECT * FROM order_s778_again WHERE done_at IS NULL AND cleared_at IS NULL ORDER BY id")]
    if rows:
        by = {e["sn"]: e for e in out}
        drafts = OS._drafts(con)
        t = now_iso()
        for r in rows:
            hit = None
            try:
                hit = OT._ordered_since(con, r["supplier_norm"], r["item"], r["at"])
            except Exception:                                  # noqa: BLE001
                pass
            if hit:
                con.execute("UPDATE order_s778_again SET done_order_id=?, done_at=? WHERE id=? AND done_at IS NULL", (hit[0], t, r["id"]))
                continue
            if r["supplier_norm"] in drafts or (forms(con, r["item"]) & hid):
                continue
            ed = OS._edits(con, "s778", r["id"]).get(r["item"]) or {}
            if ed.get("removed"):
                con.execute("UPDATE order_s778_again SET cleared_at=?, cleared_by='removed' WHERE id=? AND cleared_at IS NULL", (t, r["id"]))
                continue                                       # taken off the card by S454's remove door: not put back tomorrow
            e = by.get(r["supplier_norm"])
            if e is None:
                e = dict(sn=r["supplier_norm"], vendor=r["vendor"], lines=[], sources=[], state="pending")
                call, wa, shown, on = OS.book_card(con, r["vendor"])
                e.update(has_phone=bool(_pa()._wa_digits(wa)), phone=call, wa=wa, shown=shown, book_on=on, called="")
                by[r["supplier_norm"]] = e
                out.append(e)
            if e.get("draft"):
                continue
            if norm(r["item"]) in {norm(x["item"]) for x in e["lines"]}:
                continue                                       # on the card already: shown once
            ps = int(r["pack_size"] or 1)
            e["lines"].append(dict(src="s778", ref=str(r["id"]), item=r["item"], qty=int(ed["qty"]) if ed.get("qty") is not None else int(r["qty"]),
                                   loose=0, strip=(1 if ps > 1 else 0), pack_size=ps, packing=r["packing"] or "", rate_p=int(r["rate_p"] or 0), entry="",
                                   reordered=True, on_hand=None, s778_day=r["src_day"]))
            src = set(e.get("sources") or [])
            src.add("s778")
            e["sources"] = sorted(src)
            try:
                e["called"] = OS._called_since(con, e["sn"], e) if not e.get("called") else e["called"]
            except Exception:                                  # noqa: BLE001
                pass
        con.commit()
    out = [e for e in out if e["lines"]]
    out.sort(key=lambda e: e["vendor"])
    return out


def mark_done(con, sn, oid):
    """An order just made for `sn`: its lines that came from this kit's again rows are done; a card made only of them is noted as such."""
    ensure(con)
    items = {norm(r[0]) for r in con.execute("SELECT item FROM purchase_order_line WHERE order_id=?", (int(oid),))}
    rows = [dict(r) for r in con.execute("SELECT id, item FROM order_s778_again WHERE supplier_norm=? AND done_at IS NULL AND cleared_at IS NULL", (sn,))]
    hit = [r["id"] for r in rows if norm(r["item"]) in items]
    if hit:
        con.execute("UPDATE order_s778_again SET done_order_id=?, done_at=? WHERE id IN (%s)" % ",".join("?" * len(hit)), [int(oid), now_iso()] + hit)
        if items and items <= {norm(r["item"]) for r in rows}:
            con.execute("UPDATE purchase_order SET note=replace(note, 'orthotic shortage', 'old orders (S778)') WHERE id=?", (int(oid),))
        con.commit()
    return len(hit)


def owner_lines(con):
    """The doctor's Needs-you lines: each 'Ab nahi milta' waiting for him; the week's wrong-dealer catches (information)."""
    ensure(con)
    try:
        clear_by_bills(con)
    except Exception:                                          # noqa: BLE001
        pass
    out = []
    for r in na_rows(con, ("asked",)):
        lb = ddmon(r["last_bought"]) if r["last_bought"] else "never"
        out.append(dict(cls="warn", target="porders", href=P + "/s454/abnahi",
                        text="%s says %s is no longer available (last bought %s)" % (who_name(r["by"]), r["item"], lb)))
    wk = (today() - dt.timedelta(days=7)).isoformat()
    rows = [dict(r) for r in con.execute("SELECT * FROM order_s778_wd WHERE first_at>=? ORDER BY first_at", (wk,))]
    if rows:
        out.append(dict(cls="info", target="porders", href=P + "/s454/abnahi",
                        text="Wrong dealer caught this week: %s" % "; ".join("%s (%s, %s brings it)" % (r["item"], short(r["vendor"]), short(r["other_vendor"]))
                                                                             for r in rows[:4]) + (" and %d more" % (len(rows) - 4) if len(rows) > 4 else "")))
    return out


# ------------------------------------------------------------------ the HTML pieces
CSS = """
.s778box{border:2px solid #b3261e;background:#fbe7e5;border-radius:14px;padding:12px 12px 6px}
.s778box .hd{display:flex;align-items:center;gap:10px;font-weight:800;color:#8c1d18;font-size:17px}
.s778box .hd .n{background:#b3261e;color:#fff;border-radius:999px;padding:1px 10px;font-size:14px}
.s778l{display:grid;grid-template-columns:auto minmax(0,1fr);gap:10px;align-items:start;background:#fff;border-radius:10px;padding:9px 10px;margin:8px 0}
.s778age{font-weight:800;font-size:22px;color:#fff;background:#b3261e;border-radius:8px;padding:6px 8px;text-align:center;min-width:58px;line-height:1.05}
.s778age small{display:block;font-size:12px;font-weight:600}
.s778age.mid{background:#b4580e}
.s778l .it{font-weight:700;font-size:17px}.s778l .dl{font-size:14px;color:#3d4b48}.s778l .nt{font-size:13px;color:#5b5b5b}
.s778btn{grid-column:1/-1;display:flex;gap:8px;flex-wrap:wrap}
.s778btn button{flex:1 1 140px;min-height:46px;border-radius:10px;font:700 15px system-ui,sans-serif;cursor:pointer;padding:8px 10px}
.s778btn .go{background:#2e6b34;border:1px solid #2e6b34;color:#fff}
.s778btn .gh{background:#fff;border:1px solid #5b5b5b;color:#1c1c1c}
.s778wd{margin-top:6px;font-size:14px;font-weight:700;color:#8a5300;background:#fdf1dc;border-radius:8px;padding:7px 9px}
.s778tag{display:inline-block;font-size:12px;font-weight:800;color:#fff;background:#b3261e;border-radius:6px;padding:1px 7px;margin-left:6px;white-space:nowrap}
.s778tag.mid{background:#b4580e}
.s778cw{font-size:14px;font-weight:700;color:#8a5300;background:#fdf1dc;border-radius:8px;padding:7px 9px;display:flex;flex-direction:column;gap:6px}
.s778cw .s778btn button{min-height:44px}
.s778na{min-height:44px;margin-left:10px;border:1px solid #5b5b5b;border-radius:9px;padding:6px 9px;background:#fff;font:600 14px system-ui,sans-serif;cursor:pointer;white-space:nowrap}
.s778ok{background:#e4f2e6;border:2px solid #2e6b34;border-radius:12px;padding:12px 14px;font-weight:700;color:#1f4d25}
"""


def js_call(url, body, then="null"):
    import json                                                # noqa: PLC0415
    return "s454(%s,%s,%s)" % (esc(json.dumps(url)), esc(json.dumps(body, ensure_ascii=False)), then)


def _done_then(word_key, en):
    return ("function(j){location.href=location.pathname+'?s778=%s&i='+encodeURIComponent(j.item||'')+'&v='+encodeURIComponent(j.vendor||'')}" % word_key)


def ok_html(en, args):
    k = str(args.get("s778") or "")
    if k not in ("na_done", "moved", "againd"):
        return ""
    i, v = str(args.get("i") or "")[:80], str(args.get("v") or "")[:60]
    return '<div class="s778ok" id="s778ok">%s</div>' % esc(T(en, k, i, v) if k != "na_done" else T(en, k, i))


def age_box(en, c):
    return '<div class="s778age%s">%d<small>%s</small></div>' % ("" if c["red"] else " mid", c["age"], T(en, "din"))


def red_box(con, en, cards=None):
    al = red_lines(con, en, cards)
    ls = [c for c in al if not c.get("on_card")]               # an old line already on today's card is named on that card instead
    n_card = len(al) - len(ls)
    if not ls:
        return ('<div class="mut" id="s778oncard">%s</div>' % esc(T(en, "oncard_n", n_card))) if n_card else ""
    h = ['<div class="s778box" id="s778box"><div class="hd">%s <span class="n">%d</span></div>' % (esc(T(en, "box")), len(ls))]
    for c in ls:
        w = c.get("wrong")
        sub = '%s · <span style="white-space:nowrap">%s</span>' % (esc(c["vendor"]), esc(T(en, "orderd", ddmon(c["day"]))))
        nt = ""
        if c["kind"] == "old" and c.get("note"):
            nt = '<div class="nt">%s</div>' % esc(c["note"])
        btns = []
        if w and not c.get("on_card"):
            nt += '<div class="s778wd">%s</div>' % esc(T(en, "wd_box", c["item"], w["other"], w["n"], "" if w["n"] == 1 else "s", ddmon(w["last"]), w["dealer"])
                                                     if en else T(en, "wd_box", c["item"], w["other"], w["n"], ddmon(w["last"]), w["dealer"]))
            btns.append('<button class="go" onclick="%s">%s</button>' % (js_call(P + "/api/s778/again", dict(kind=c["kind"], ref=c["ref"], to=w["other_sn"]),
                                                                                 _done_then("againd", en)), esc(T(en, "to_x", w["other"]))))
            btns.append('<button class="gh" onclick="%s">%s</button>' % (js_call(P + "/api/s778/dealer_ok", dict(sn=c["sn"], item=c["item"])), esc(T(en, "ok", w["dealer"]))))
        else:
            if c.get("on_card"):
                nt += '<div class="nt"><b>%s</b></div>' % esc(T(en, "oncard", short(c["on_card"])))
            elif c.get("marg_line"):
                btns.append('<button class="go" onclick="%s">%s</button>' % (js_call(P + "/api/s454/reorder", dict(line=int(c["marg_line"]))), esc(T(en, "again"))))
            else:
                btns.append('<button class="go" onclick="%s">%s</button>' % (js_call(P + "/api/s778/again", dict(kind=c["kind"], ref=c["ref"]), _done_then("againd", en)),
                                                                           esc(T(en, "again"))))
            btns.append('<button class="gh" onclick="%s">%s</button>' % (js_call(P + "/api/s778/na", dict(kind=c["kind"], ref=c["ref"]), _done_then("na_done", en)),
                                                                       esc(T(en, "na"))))
        h.append('<div class="s778l" data-kind="%s" data-ref="%s">%s<div><div class="it">%s · %s</div><div class="dl">%s</div>%s</div>'
                 '<div class="s778btn">%s</div></div>' % (esc(c["kind"]), esc(c["ref"]), age_box(en, c), esc(c["item"]), esc(c["qty_text"]), sub, nt, "".join(btns)))
    if n_card:
        h.append('<div class="nt" id="s778oncard" style="padding:2px 4px 6px">%s</div>' % esc(T(en, "oncard_n", n_card)))
    h.append("</div>")
    return "".join(h)


def line_wrong_html(con, en, e, l):
    """The card's warning under a line to a dealer who never brought it (only while the card can still change)."""
    if l.get("src") == "draft" or e.get("draft") or e.get("state") != "pending":
        return ""
    w = wrong_dealer(con, e["sn"], l["item"], e["vendor"])
    if not w:
        return ""
    body = dict(sn=e["sn"], src=l["src"], ref=str(l["ref"]), item=l["item"], to=w["other_sn"])
    words = (T(en, "wd_card", w["other"], w["n"], "" if w["n"] == 1 else "s", ddmon(w["last"])) if en
             else T(en, "wd_card", w["other"], w["n"], ddmon(w["last"])))
    return ('<div class="s778cw" data-item="%s"><div>%s · %s</div><div class="s778btn"><button class="go" onclick="%s">%s</button>'
            '<button class="gh" onclick="%s">%s</button></div></div>'
            % (esc(l["item"]), esc(l["item"]), esc(words), js_call(P + "/api/s778/move", body, _done_then("moved", en)), esc(T(en, "move", w["other"])),
               js_call(P + "/api/s778/dealer_ok", dict(sn=e["sn"], item=l["item"])), esc(T(en, "ok", w["dealer"]))))


def tag_html(en, age):
    if not age:
        return ""
    return ' <span class="s778tag%s">%s</span>' % ("" if age >= RED_FROM else " mid", esc(T(en, "purana", age)))


def na_button(en, e, l):
    if l.get("src") == "draft" or e.get("draft") or e.get("state") != "pending":
        return ""
    body = dict(sn=e["sn"], src=l["src"], ref=str(l["ref"]), item=l["item"])
    return '<button class="s778na" onclick="%s">%s</button>' % (js_call(P + "/api/s778/na", body, _done_then("na_done", en)), esc(T(en, "na")))


def card_extra(con, en, e):
    """On a dealer's card of 'Order karna hai': its old lines named with their age, and the wrong-dealer warnings."""
    h = []
    ages = old_of(con, e["sn"])
    old = []
    for l in e["lines"]:
        a = next((ages[f] for f in forms(con, l["item"], e["sn"]) if f in ages), 0)
        if a:
            old.append('%s%s' % (esc(l["item"]), tag_html(en, a)))
    if old:
        h.append('<div class="sb">%s</div>' % " · ".join(old))
    for l in e["lines"]:
        h.append(line_wrong_html(con, en, e, l))
    return "".join(h)


def wrong_count(con, cards):
    n = 0
    for e in cards:
        if e.get("draft") or e.get("state") != "pending":
            continue
        for l in e["lines"]:
            if wrong_dealer(con, e["sn"], l["item"], e["vendor"]):
                n += 1
    return n


OWNER_OK = {"stop": "%s is stopped everywhere — until a Marg bill brings it again.", "keep": "%s stays on the order list.",
            "undo": "%s is back on the order list."}


def _owner_then(k):
    return "function(j){location.href=location.pathname+'?done=%s&i='+encodeURIComponent(j.item||'')}" % k


def owner_ok_html(args):
    k = str(args.get("done") or "")
    if k not in OWNER_OK:
        return ""
    return '<div class="s778ok" id="s778ok">%s</div>' % esc(OWNER_OK[k] % str(args.get("i") or "")[:80])


def owner_page_body(con):
    """/finance/porders/s454/abnahi -- the doctor's answers (English)."""
    ensure(con)
    clear_by_bills(con)
    h = ['<div class="mut">Staff say these medicines are no longer available; until you answer, each is off today\'s order list. '
         '<b>Stop it everywhere</b> keeps it off every list until a Marg bill brings it again; Undo takes it back.</div>']
    asked = na_rows(con, ("asked",))
    for r in asked:
        lb = ddmon(r["last_bought"]) if r["last_bought"] else "never"
        h.append('<div class="card" data-na="%d"><div class="nm">%s</div><div class="sb">%s says it is no longer available (last bought %s) · tapped %s · %s</div>'
                 '<div class="s778btn"><button class="go" onclick="%s">Stop it everywhere</button><button class="gh" onclick="%s">Keep ordering</button></div></div>'
                 % (r["id"], esc(r["item"]), esc(who_name(r["by"])), esc(lb), esc(ddmon(r["at"])), esc(r["vendor"] or ""),
                    js_call(P + "/api/s778/na_answer", dict(id=r["id"], answer="stop"), _owner_then("stop")),
                    js_call(P + "/api/s778/na_answer", dict(id=r["id"], answer="keep"), _owner_then("keep"))))
    if not asked:
        h.append('<div class="ok"><div class="t">Nothing waiting for your answer.</div></div>')
    stopped = na_rows(con, ("stop",))
    if stopped:
        h.append('<div class="grp">Stopped — until a bill brings it</div>')
        for r in stopped:
            h.append('<div class="card" data-stop="%d"><div class="nm">%s</div><div class="sb">stopped %s by you · %s tapped it %s</div>'
                     '<div class="s778btn"><button class="gh" onclick="%s">Undo — order it again</button></div></div>'
                     % (r["id"], esc(r["item"]), esc(ddmon(r["answered_at"])), esc(who_name(r["by"])), esc(ddmon(r["at"])),
                        js_call(P + "/api/s778/na_answer", dict(id=r["id"], answer="undo"), _owner_then("undo"))))
    wk = (today() - dt.timedelta(days=7)).isoformat()
    rows = [dict(r) for r in con.execute("SELECT * FROM order_s778_wd WHERE first_at>=? ORDER BY first_at DESC", (wk,))]
    h.append('<div class="grp">Wrong dealer — caught in the last 7 days</div>')
    if rows:
        word = {"moved": "moved to %s", "kept": "kept with %s"}
        for r in rows:
            oc = (word.get(r["outcome"] or "", "") % (short(r["other_vendor"]) if r["outcome"] == "moved" else short(r["vendor"]))) if r["outcome"] else "no answer yet"
            h.append('<div class="ln" data-wd="1"><div class="t"><div class="a">%s</div><div class="s">ordered to %s · %s brings it · %s · %s</div></div></div>'
                     % (esc(r["item"]), esc(short(r["vendor"])), esc(short(r["other_vendor"])), esc(ddmon(r["first_at"])), esc(oc)))
    else:
        h.append('<div class="mut">None.</div>')
    return "".join(h)


def lift_all(con, who="kit undone"):
    """The kit's undo: every stop of this kit lifted (the rule it replaced put back), every sheet line it held or moved given back, every
    carry it dropped (and not ordered since) open again. Its own tables stay; nothing reads them without the kit."""
    ensure(con)
    n = 0
    for r in na_rows(con):
        if r["status"] == "stop":
            _lift(con, r, who)
        _unhold_sheet(con, r)
        con.execute("UPDATE order_s778_na SET cleared_at=?, cleared_why=? WHERE id=?", (now_iso(), who, r["id"]))
        n += 1
    m = con.execute("DELETE FROM s454_line_edit WHERE reason IN ('s778_na','s778_moved')").rowcount
    c = con.execute("UPDATE order_carry SET dropped_at=NULL, dropped_by=NULL WHERE dropped_by IN ('s778_na','s778_moved') AND done_at IS NULL").rowcount
    con.commit()
    return "LIFTED: %d hold(s), %d line edit(s), %d carry(ies)" % (n, m, c)


if __name__ == "__main__":
    import sys                                                 # noqa: PLC0415
    if len(sys.argv) == 3 and sys.argv[2] == "--lift-all":
        sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
        _c = sqlite3.connect(sys.argv[1], timeout=30)
        _c.row_factory = sqlite3.Row
        print(lift_all(_c))
    else:
        print("usage: order_s778.py FINANCE_DB --lift-all")
