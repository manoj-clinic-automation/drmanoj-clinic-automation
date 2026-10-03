#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  item_check.py  ·  v1.0  ·  kit S454_BILL_REGISTER (part 5)  ·  Session 283 (Sanjeevni)  ·  S454 section 11
#
#  THE ITEMS -- two things, read only of the bills (they change no stock, no order and no bill):
#  11.1 The items check (the owner's page /finance/purchase/page/items?month=): each Marg purchase bill of the month whose lines' own value
#       -- quantity x rate, less the discount, plus the tax, from purchase_line -- does not come to the bill's amount within the noise setting
#       (purchase.total_noise_rs): the bill, the difference and its lines. Marg prints each line twice (item-wise and bill-item-wise): one
#       copy is read (the bill-item-wise one when it is there), from the newest export that carries it. Marg's own net figure of each line is
#       shown beside the line's value: where they differ, something reached the bill that the line's columns do not show.
#  11.2 Learning the suppliers' item names: from a VERIFIED pair (scan_register's rule) whose scan has as many item lines as Marg's entry, a
#       scan line is paired with the Marg line whose quantity and rate agree when no other line of that bill does -- the name that supplier
#       printed is learnt against Marg's item, once (s454_item_name). The Sarvam check then judges a scan's item name by the learnt names
#       first (purchase_app._s446_compare_one). Two names that share nothing are never learnt as one (names_akin: quantity and rate can
#       agree by chance -- found on 03-Oct's data).
#  READ ONLY of the asset app's database. Nothing here prints a phone number, an account number or a key.
# =============================================================================
import datetime as dt
import re
import sqlite3

VERSION = "1.0"
KIT = "S454_BILL_REGISTER"
DDL = ("CREATE TABLE IF NOT EXISTS s454_item_name (supplier_norm TEXT NOT NULL, scan_norm TEXT NOT NULL, scan_name TEXT, marg_item TEXT NOT NULL, "
       "bill_id INTEGER, asset_bill_id INTEGER, learnt_at TEXT NOT NULL, PRIMARY KEY (supplier_norm, scan_norm))")


def _pa():
    import purchase_app                                       # noqa: PLC0415 -- beside this file
    return purchase_app


def _sr():
    import scan_register                                      # noqa: PLC0415
    return scan_register


def ensure(con):
    con.execute(DDL)


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _rows(con, sql, args=()):
    """[dict] whatever the connection's own row factory is."""
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    return [dict(r) for r in cur.execute(sql, args).fetchall()]


def name_norm(s):
    return re.sub(r"[^A-Z0-9]+", " ", str(s or "").upper()).strip()


def marg_lines(con, bill):
    """Marg's lines of one bill, one copy: the bill-item-wise lines when there are any, else the item-wise ones, from the newest export
    of that kind that is still in force."""
    pa = _pa()
    ls = _rows(con, "SELECT l.* FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_no=? AND l.bill_date=? AND " + pa.EFF_LINE + " ORDER BY l.id",
               (bill["supplier_norm"], bill["bill_no"], bill["bill_date"]))
    if not ls:
        return []
    typ = "BILLITEMWISE" if any(l.get("line_type") == "BILLITEMWISE" for l in ls) else ls[0].get("line_type")
    ls = [l for l in ls if l.get("line_type") == typ]
    newest = ls[-1]["source_md5"]
    return [l for l in ls if l["source_md5"] == newest]


def line_value_p(l):
    """quantity x rate, less the discount, plus the tax (paise); a purchase return counts against the bill."""
    v = float(l.get("qty") or 0) * float(l.get("rate_p") or 0) * (1 - float(l.get("discount_pct") or 0) / 100.0) * (1 + float(l.get("tax") or 0) / 100.0)
    return -v if str(l.get("direction") or "").upper() == "RETURN" else v


# ------------------------------------------------------------------ 11.1 the items check
def items_check(con, month):
    """dict(month, n, adds, differs, nolines, noise_p, rows=[{bill, diff_p, value_p, lines}] for the bills that do not add up)."""
    pa = _pa()
    noise = _sr().noise_p(con)
    bills = _rows(con, "SELECT b.* FROM purchase_bill b WHERE " + pa.EFF_BILL + " AND COALESCE(b.month, substr(b.bill_date,1,7))=? ORDER BY b.bill_date, b.id",
                  (month,))
    out = dict(month=month, n=len(bills), adds=0, differs=0, nolines=0, noise_p=noise, rows=[], nolines_rows=[])
    for b in bills:
        ls = marg_lines(con, b)
        if not ls:
            out["nolines"] += 1
            out["nolines_rows"].append(dict(id=b["id"], supplier=b["supplier"], bill_no=b["bill_no"], date=b["bill_date"], amount_p=int(b["amount_p"] or 0)))
            continue
        val = sum(line_value_p(l) for l in ls)
        diff = int(round(val)) - int(b["amount_p"] or 0)
        if abs(diff) <= noise:
            out["adds"] += 1
            continue
        out["differs"] += 1
        out["rows"].append(dict(id=b["id"], supplier=b["supplier"], bill_no=b["bill_no"], date=b["bill_date"], amount_p=int(b["amount_p"] or 0),
                                value_p=int(round(val)), diff_p=diff,
                                lines=[dict(item=l["item"], packing=l.get("packing") or "", qty=l.get("qty"), free=l.get("free"), rate_p=l.get("rate_p"),
                                            disc=l.get("discount_pct"), tax=l.get("tax"), value_p=int(round(line_value_p(l))),
                                            marg_net_p=(int(l["net_amount_p"]) if l.get("net_amount_p") is not None else None), direction=l.get("direction"))
                                       for l in ls]))
    out["rows"].sort(key=lambda r: -abs(r["diff_p"]))
    return out


# ------------------------------------------------------------------ 11.2 learning the suppliers' item names
def _same_qty(a, b):
    try:
        return a not in (None, "") and b not in (None, "") and abs(float(a) - float(b)) <= 0.001
    except (TypeError, ValueError):
        return False


def _same_rate(scan_rate, marg_rate_p):
    """The Sarvam check's own tolerance: within 1 paisa or 1%."""
    try:
        if scan_rate in (None, "") or marg_rate_p is None:
            return False
        r1, r2 = float(scan_rate), float(marg_rate_p) / 100.0
        return abs(r1 - r2) <= max(0.01, 0.01 * r2)
    except (TypeError, ValueError):
        return False


FORM_WORDS = frozenset(("TAB", "TABS", "TABLET", "TABLETS", "CAP", "CAPS", "CAPSULE", "GEL", "SYP", "SYRUP", "INJ", "CREAM", "OINT", "DROP", "DROPS",
                        "SPRAY", "SACH", "SACHET", "STRIP", "SUSP", "LOTION", "POWDER"))
AKIN_RATIO = 0.4


def names_akin(a, b):
    """S454 P5 (a guard on 11.2, found on 03-Oct's data): two names that share nothing are never learnt as one -- quantity and rate can agree by
    chance ("BARBELLY Junction only," read off an address line was paired with CHYMORAL AP; "CCM TAB" with DFO 4X GEL). Akin: at least 0.4
    alike as strings, or a word (not a form word such as TAB or CAP) whose first three letters both carry."""
    import difflib                                            # noqa: PLC0415
    A, B = name_norm(a), name_norm(b)
    if not A or not B:
        return False
    if difflib.SequenceMatcher(None, A, B).ratio() >= AKIN_RATIO:
        return True
    ta = {w[:3] for w in A.split() if len(w) >= 3 and not w.isdigit() and w not in FORM_WORDS}
    tb = {w[:3] for w in B.split() if len(w) >= 3 and not w.isdigit() and w not in FORM_WORDS}
    return bool(ta & tb)


def pairs_of(scan_items, ml):
    """[(scan line, Marg line)] -- each scan line whose quantity and rate agree with exactly one Marg line, when no other scan line agrees
    with that Marg line (and that scan line agrees with no other Marg line)."""
    m = [[j for j, x in enumerate(ml) if _same_qty(it.get("quantity"), x.get("qty")) and _same_rate(it.get("rate"), x.get("rate_p"))] for it in scan_items]
    out = []
    for i, js in enumerate(m):
        if len(js) != 1:
            continue
        j = js[0]
        if sum(1 for k in m if j in k) != 1:
            continue
        out.append((scan_items[i], ml[j]))
    return out


def learn(con, only_bills=None):
    """Learns from every VERIFIED link whose scan has as many item lines as Marg's entry. Returns the names newly learnt ([dict])."""
    pa = _pa()
    SR = _sr()
    ensure(con)
    acon = pa._assets_con()
    if acon is None:
        return []
    new = []
    try:
        scans = SR.asset_scans(con) or {}
        cx = SR.Ctx(con)
        for bid, l in sorted(SR.links(con).items()):
            if only_bills is not None and bid not in only_bills:
                continue
            s = scans.get(l["scan"])
            bb = _rows(con, "SELECT * FROM purchase_bill WHERE id=?", (bid,))
            if s is None or not bb:
                continue
            b = bb[0]
            if not SR.verified(SR.agree(cx, dict(s), b)):
                continue
            items = _rows(acon, "SELECT item_name, quantity, rate FROM bill_items WHERE bill_id=? ORDER BY id", (l["scan"],))
            ml = marg_lines(con, b)
            if not items or len(items) != len(ml):
                continue
            for it, x in pairs_of(items, ml):
                sn = name_norm(it.get("item_name"))
                if not sn or sn == name_norm(x["item"]) or not names_akin(sn, x["item"]):
                    continue
                cur = con.execute("INSERT OR IGNORE INTO s454_item_name (supplier_norm, scan_norm, scan_name, marg_item, bill_id, asset_bill_id, learnt_at) "
                                  "VALUES (?,?,?,?,?,?,?)", (b["supplier_norm"], sn, it.get("item_name"), x["item"], bid, l["scan"], now_iso()))
                if cur.rowcount:
                    new.append(dict(supplier_norm=b["supplier_norm"], scan_name=it.get("item_name"), marg_item=x["item"], bill_id=bid, scan=l["scan"]))
        con.commit()
    finally:
        acon.close()
    return new


def learnt_line(con, bill, nm, ml):
    """(Marg line, 1.0) when this supplier's printed name `nm` (already normalised) was learnt and its Marg item is on this bill; else (None, 0.0)."""
    try:
        r = con.execute("SELECT marg_item FROM s454_item_name WHERE supplier_norm=? AND scan_norm=?", (bill["supplier_norm"], nm)).fetchone()
    except sqlite3.Error:
        return None, 0.0
    if not r:
        return None, 0.0
    hit = [x for x in ml if x.get("item") == r[0]]
    return (hit[0], 1.0) if hit else (None, 0.0)


def learnt(con):
    ensure(con)
    return [dict(supplier_norm=r[0], scan_name=r[1], marg_item=r[2], learnt_at=r[3]) for r in
            con.execute("SELECT supplier_norm, scan_name, marg_item, learnt_at FROM s454_item_name ORDER BY supplier_norm, scan_norm")]
