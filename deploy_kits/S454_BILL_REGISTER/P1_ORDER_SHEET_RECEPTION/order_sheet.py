#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  order_sheet.py  ·  v1.0  ·  kit S454_BILL_REGISTER (part 1)  ·  Session 283 (Sanjeevni)  ·  D666 / D668 / D669
#
#  DARPAN'S MARG ORDER SHEET ON THE SERVER, AND WHAT BECOMES OF EACH OF ITS LINES. The owner, 03-Oct-2026: "the orders currently
#  decided by Darpan ... the system capturing Darpan's orders as he makes them in the order sheet". Marg's report PENDING ORDERS
#  (PURCHASE), saved as text, is converted on the medical PC (marg_txt S454) and taken by the one door (marg_take, signature
#  ORDER_PENDING); marg_take calls load_file() at once, and every page read calls load_pending() as the fallback. Same file twice:
#  nothing added.
#
#  A LINE, keyed by (entry number, item as printed):
#    known      -- held from an earlier sheet: nothing is added (Marg prints a line for ever; this record decides its state)
#    new        -- dated less than order.sheet_max_age_days before the sheet's newest date: TO BE ORDERED, under its supplier
#    old        -- older: kept, shown apart, highlighted, never ordered by itself
#  Its state: to_order -> in_line (WhatsApp in the reception phone's line; its draft order) -> ordered (an order of purchase_order,
#  'sent') · closed_marg (never ticked; Marg shows the purchase: "aa chuka, bina order ke") · lapsed (new, never ordered within
#  order.sheet_max_age_days of its date: old pending now, and the owner reads one line) · old · dropped (removed from its order).
#  What an old line says of itself: "aa chuka dd-mm" when Marg has a purchase of that item from that supplier on or after its
#  date, else "nahi aaya". Shown to the staff while (aa chuka) fewer than order.old_done_days since it first read so, or (nahi
#  aaya) no older than order.old_show_days -- then only on the owner's list. "Dobara order karo" makes it a new line of that day.
#
#  ARRIVAL BY THE BILL'S SCAN (D668): a pharmacy scan whose supplier (carried by the intake link, read exactly or by a learnt spelling,
#  or chosen by reception -- never a merely similar spelling) has an order with no bill scan yet, scanned at or after the moment that
#  order was made (bills.submitted_at, IST, to the minute), is tied to that supplier's OLDEST such order (order_scan_tie, its own
#  table). An awaited order has arrived: status received, its lines left open (supplied NULL) so Marg's bill records ordered against
#  supplied by itself (porders.detect_supplies), its quantities in today's in-transit rule. A bill whose read day and month fall
#  before the order's day ties nothing. A supplier never ticked whose bill is scanned after the sheet was loaded gets its order made
#  "by the bill's scan", arrived. An unread paper ties only after reception's "Haan, pharmacy ka bill" (S454 4.7).
#
#  WHAT IT IS: tables (order_sheet, order_sheet_line, order_scan_tie, s454_line_edit, s454_scan_answer, s454_later, s454_paper_missing),
#  additive columns on purchase_order (supplier_norm, ext_ref, order_src, order_via, sheet_id), the loader, the comparison with the
#  system's own plan (order_rules.plan, kept per sheet, shown to the owner only), the suppliers still to be ordered (the sheet's new
#  lines, or on order.source=system the day's proposals; the orthotic shortage card S403 on both), the order book writes, the
#  reception phone's order messages (supplier_msg kind 'order'), the tie, the clearing, and cron_pass() for order_rules' tick.
#  NO phone number, token or patient detail is printed by this file; a phone number goes only into a page a sender opens to call,
#  or into the reception phone's message.
# =============================================================================
import datetime as dt
import json
import os
import re
import sqlite3
import sys

VERSION = "1.0"
KIT = "S454_BILL_REGISTER"
TYPE = "ORDER_PENDING"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
MARG_DIR = os.environ.get("MARG_INGEST_DIR", "/root/marg_ingest")
PAPER_HOUR = (15, 0)                       # S454 3.5: the paper order of the first load was made at 15:00 IST on the sheet's date
SETTINGS = {
    "porders.simple": ("1", "S454: 1 = the one-task reception screens; 0 = everyone back on the old Purchase orders page"),
    "order.source": ("marg_sheet", "S454 (D666): who decides the order -- marg_sheet (Darpan's sheet) or system (the system's own list)"),
    "order.sheet_max_age_days": ("7", "S454: a line of the sheet this old or older, and unknown, is old pending; a new line not ordered this long after its date lapses"),
    "order.sheet_print_old": ("1", "S454: 1 = old pending lines on the printed order sheet, 0 = left off"),
    "order.old_done_days": ("7", "S454: an old line that has since been supplied stays before the staff this many days"),
    "order.old_show_days": ("60", "S454: an old line that never came stays before the staff until it is this many days old"),
    "order.remind_times": ("17:00", "S454: when the one reminder of the day goes (HH:MM, 05:00-21:50, in tens of minutes)"),
    "order.whatsapp_wait_min": ("60", "S454: a WhatsApp not sent within this many minutes is withdrawn and its supplier is pending again"),
    "order.phone_alive_min": ("30", "S454: the reception phone silent this long -- the WhatsApp button is disabled"),
    "supplier_msg.handout_gap_min": ("10", "S454 (F-702): a message handed to the phone is not handed out again within this many minutes"),
    "purchase.register_from": ("2026-10-01", "S454: the first counted month (staff work and alerts start here)"),
    "purchase.parked_months": ("2026-09", "S454: earlier months shown to the staff behind their own link, optional"),
    "purchase.arrival_scan_days": ("7", "S454: how long a received order asks for its bill's scan"),
    "purchase.unread_pair_days": ("7", "S454: how near in date a Marg bill must be for reception to be asked whether an unread paper is that bill"),
}
DDL = (
    "CREATE TABLE IF NOT EXISTS order_sheet (id INTEGER PRIMARY KEY, md5 TEXT UNIQUE NOT NULL, name TEXT, source TEXT, stamp TEXT,"
    " taken_at TEXT NOT NULL, newest_date TEXT, n_lines INTEGER, n_new INTEGER, n_old INTEGER, n_known INTEGER, n_suppliers INTEGER,"
    " units_total INTEGER, value_total INTEGER, as_ordered INTEGER NOT NULL DEFAULT 0, cmp TEXT, cmp_at TEXT, unresolved TEXT,"
    " phones_new TEXT, notice TEXT)",
    "CREATE TABLE IF NOT EXISTS order_sheet_line (id INTEGER PRIMARY KEY, entry_no TEXT NOT NULL, item_printed TEXT NOT NULL,"
    " item TEXT NOT NULL, resolved INTEGER NOT NULL DEFAULT 0, supplier TEXT NOT NULL, supplier_norm TEXT NOT NULL, packing TEXT,"
    " pack_size INTEGER, line_date TEXT NOT NULL, qty_raw TEXT, qty INTEGER, loose INTEGER NOT NULL DEFAULT 0, strip INTEGER NOT NULL DEFAULT 0,"
    " units INTEGER, rate_p INTEGER, value_p INTEGER, kind TEXT NOT NULL, state TEXT NOT NULL, order_id INTEGER, reorder_day TEXT,"
    " marg_date TEXT, marg_bill TEXT, marg_seen_at TEXT, lapsed_at TEXT, first_sheet INTEGER NOT NULL, last_sheet INTEGER NOT NULL,"
    " created_at TEXT NOT NULL, updated_at TEXT, UNIQUE (entry_no, item_printed))",
    "CREATE TABLE IF NOT EXISTS order_scan_tie (order_id INTEGER PRIMARY KEY, asset_bill_id INTEGER UNIQUE NOT NULL, stamp TEXT,"
    " scan_at TEXT, tied_at TEXT NOT NULL, how TEXT NOT NULL, arrived INTEGER NOT NULL DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS s454_line_edit (src TEXT NOT NULL, ref TEXT NOT NULL, item TEXT NOT NULL, qty INTEGER,"
    " removed INTEGER NOT NULL DEFAULT 0, by TEXT, at TEXT, PRIMARY KEY (src, ref, item))",
    "CREATE TABLE IF NOT EXISTS s454_scan_answer (asset_bill_id INTEGER NOT NULL, kind TEXT NOT NULL, answer TEXT, value TEXT, by TEXT,"
    " at TEXT NOT NULL, PRIMARY KEY (asset_bill_id, kind))",
    "CREATE TABLE IF NOT EXISTS s454_later (asset_bill_id INTEGER NOT NULL, kind TEXT NOT NULL, at TEXT NOT NULL, PRIMARY KEY (asset_bill_id, kind))",
    "CREATE TABLE IF NOT EXISTS s454_paper_missing (bill_id INTEGER PRIMARY KEY, by TEXT, at TEXT NOT NULL, accepted_by TEXT, accepted_at TEXT)",
)
ORDER_COLS = (("supplier_norm", "TEXT"), ("ext_ref", "TEXT"), ("order_src", "TEXT"), ("order_via", "TEXT"), ("sheet_id", "INTEGER"))
MSG_COLS = (("handed_at", "TEXT"),)
HEADING_WORDS = re.compile(r"\b(ESTIMATE|CHALLAN|QUOTATION)\b", re.I)


# ------------------------------------------------------------------ small things
def now():
    return dt.datetime.now().replace(microsecond=0)


def now_iso():
    return now().isoformat()


def today():
    v = os.environ.get("ORDER_TODAY", "")
    try:
        return dt.date.fromisoformat(v) if v else dt.date.today()
    except ValueError:
        return dt.date.today()


def _pa():
    import purchase_app                                       # noqa: PLC0415 -- beside this file
    return purchase_app


def _ia():
    import item_alias                                         # noqa: PLC0415
    return item_alias


def _iso_dmy(s):
    """'02-10-2026' -> '2026-10-02'; an ISO date unchanged; else ''."""
    s = str(s or "").strip()
    m = re.match(r"^(\d\d)-(\d\d)-(\d{4})$", s)
    if m:
        return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1))
    return s[:10] if re.match(r"^\d{4}-\d\d-\d\d", s) else ""


def ddmm(iso):
    s = str(iso or "")[:10]
    return ("%s-%s" % (s[8:10], s[5:7])) if len(s) == 10 else s


def dmy(iso):
    s = str(iso or "")[:10]
    return ("%s-%s-%s" % (s[8:10], s[5:7], s[0:4])) if len(s) == 10 else s


def _date(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None


def _dtm(s):
    """An IST moment from '2026-10-02T15:00:00' or '2026-10-02 15:00' -> datetime (minutes), else None."""
    s = str(s or "").strip().replace("T", " ")
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return dt.datetime.strptime(s[:19] if f.endswith("%S") else s[:16], f).replace(second=0)
        except ValueError:
            continue
    return None


def setting(con, key, default=None):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        if r is not None and r[0] is not None and str(r[0]).strip() != "":
            return str(r[0]).strip()
    except sqlite3.Error:
        pass
    return SETTINGS[key][0] if (default is None and key in SETTINGS) else (default if default is not None else "")


def int_setting(con, key):
    try:
        return int(float(setting(con, key)))
    except (TypeError, ValueError):
        return int(SETTINGS[key][0])


def source(con):
    v = setting(con, "order.source")
    return v if v in ("marg_sheet", "system") else "marg_sheet"


def _has_col(con, table, col):
    try:
        return col in {r[1] for r in con.execute("PRAGMA table_info(%s)" % table)}
    except sqlite3.Error:
        return False


def ensure(con):
    for d in DDL:
        con.execute(d)
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for k, (v, note) in SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))
    for col, typ in ORDER_COLS:
        if not _has_col(con, "purchase_order", col):
            try:
                con.execute("ALTER TABLE purchase_order ADD COLUMN %s %s" % (col, typ))
            except sqlite3.Error:
                pass
    for col, typ in MSG_COLS:
        if _has_col(con, "supplier_msg", "id") and not _has_col(con, "supplier_msg", col):
            try:
                con.execute("ALTER TABLE supplier_msg ADD COLUMN %s %s" % (col, typ))
            except sqlite3.Error:
                pass
    con.commit()


def audit(con, who, action, ref="", detail=None):
    try:
        _pa()._audit(con, who, action, ref, detail)
    except Exception:                                         # noqa: BLE001 -- the row itself is the record
        pass


def qty_text(qty_raw):
    """The sheet's quantity in the order's own unit, as the staff were given it: '20:0' -> '20 strip', '20:5' -> '20 strip + 5', '5' -> '5'."""
    q = str(qty_raw or "").strip()
    m = re.match(r"^(\d+):(\d+)$", q)
    if m:
        return "%s strip%s" % (m.group(1), (" + %s" % m.group(2)) if int(m.group(2)) else "")
    return q


def line_qty_text(l):
    """A line's quantity in its own unit -- an edit applied: strips (+ loose) for a strip item, the plain number otherwise."""
    q = int(l.get("qty") or 0)
    if l.get("strip"):
        return "%d strip%s" % (q, (" + %d" % int(l["loose"])) if int(l.get("loose") or 0) else "")
    return "%d" % q


def _pack(packing):
    m = re.match(r"^\s*(\d+)\s*\*\s*(\d+)", str(packing or ""))
    return int(m.group(1)) * int(m.group(2)) if m else 1


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ the item: resolved to Marg's own name
def _snapshot_names(con):
    try:
        rows = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
        if not rows:
            return []
        as_on = max(rows, key=lambda d: (str(d)[6:], str(d)[3:5], str(d)[:2]))
        return [r[0] for r in con.execute("SELECT item FROM stock_snapshot WHERE as_on=?", (as_on,))]
    except sqlite3.Error:
        return []


def resolve_item(printed, names, pn=None):
    """The sheet prints about 21 characters of a name: Marg's own name by the exact name, else the ONE name that begins with it."""
    pn = pn or _ia().pad_norm
    p = pn(printed)
    exact = [n for n in names if pn(n) == p]
    if exact:
        return exact[0], True
    pre = [n for n in names if pn(n).startswith(p)]
    if len(pre) == 1:
        return pre[0], True
    return printed, False


# ------------------------------------------------------------------ the loader
def rows_from_file(path):
    """The converted sheet's rows (xlrd, through the router's own reader)."""
    if MARG_DIR not in sys.path:
        sys.path.insert(0, MARG_DIR)
    import marg_router                                        # noqa: PLC0415
    sh = marg_router.open_sheet(path)
    return [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]


def _lines_of(rows):
    """[{supplier, phones, item, packing, entry, date, qty_raw, rate, value}] from the sheet's rows; the heads must be ours."""
    hi = next((i for i, r in enumerate(rows) if [str(x).strip().upper() for x in r[:3]] == ["SUPPLIER", "PHONES", "ITEM NAME"]), None)
    if hi is None:
        raise ValueError("the order sheet's heads are not where they must be")
    out = []
    for r in rows[hi + 1:]:
        r = list(r) + [""] * (11 - len(r))
        if str(r[0]).strip().upper() == "TOTAL" and not str(r[2]).strip():
            break
        if not str(r[2]).strip():
            continue
        q = r[6]
        q = ("%d" % int(q)) if isinstance(q, float) else str(q).strip()
        out.append(dict(supplier=str(r[0]).strip(), phones=[p.strip() for p in str(r[1] or "").split(",") if p.strip()], item=str(r[2]).strip(),
                        packing=str(r[3]).strip(), entry=str(r[4]).strip(), date=_iso_dmy(r[5]), qty_raw=q,
                        rate=_num(r[9]) or 0.0, value=_num(r[10]) or 0.0))
    return out


def load_file(con, path, md5, name="", src="push", stamp="", as_ordered=False):
    """marg_take's hook (a VERIFIED ORDER_PENDING file), the page's fallback, and the first load. Idempotent by md5."""
    ensure(con)
    if con.execute("SELECT 1 FROM order_sheet WHERE md5=?", (md5,)).fetchone():
        return dict(ok=True, already=True)
    return load_rows(con, rows_from_file(path), md5, name, src, stamp, as_ordered)


def load_rows(con, rows, md5, name="", src="push", stamp="", as_ordered=False, who="order sheet"):
    ensure(con)
    pa = _pa()
    if con.execute("SELECT 1 FROM order_sheet WHERE md5=?", (md5,)).fetchone():
        return dict(ok=True, already=True)
    lines = _lines_of(rows)
    if not lines or any(not l["date"] for l in lines):
        raise ValueError("an order sheet with no lines, or a line with no date")
    newest = max(l["date"] for l in lines)
    nd = _date(newest)
    max_age = int_setting(con, "order.sheet_max_age_days")
    names = _snapshot_names(con)
    t = now_iso()
    cur = con.execute("INSERT INTO order_sheet (md5, name, source, stamp, taken_at, newest_date, as_ordered) VALUES (?,?,?,?,?,?,?)",
                      (md5, name, src, stamp, t, newest, 1 if as_ordered else 0))
    sid = cur.lastrowid
    n_new = n_old = n_known = 0
    unresolved, phones_new, sups, units_total, value_total = [], {}, set(), 0, 0
    new_ids = []
    for l in lines:
        sn = pa.supplier_key(l["supplier"])
        sups.add(sn)
        q = l["qty_raw"]
        m = re.match(r"^(\d+):(\d+)$", q)
        strip = 1 if m else 0
        qty = int(m.group(1)) if m else int(q or 0)
        loose = int(m.group(2)) if m else 0
        ps = _pack(l["packing"])
        units = qty * ps + loose if strip else qty
        units_total += units
        value_total += int(round(l["value"]))
        old = con.execute("SELECT id FROM order_sheet_line WHERE entry_no=? AND item_printed=?", (l["entry"], l["item"])).fetchone()
        if old:
            con.execute("UPDATE order_sheet_line SET last_sheet=?, updated_at=? WHERE id=?", (sid, t, old[0]))
            n_known += 1
            continue
        item, ok = resolve_item(l["item"], names)
        if not ok:
            unresolved.append(dict(item=l["item"], supplier=l["supplier"]))
        ld = _date(l["date"])
        kind = "new" if (nd and ld and (nd - ld).days < max_age) else "old"
        state = "to_order" if kind == "new" else "old"
        cur = con.execute("INSERT INTO order_sheet_line (entry_no, item_printed, item, resolved, supplier, supplier_norm, packing, pack_size, line_date,"
                          " qty_raw, qty, loose, strip, units, rate_p, value_p, kind, state, first_sheet, last_sheet, created_at) VALUES"
                          " (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (l["entry"], l["item"], item, 1 if ok else 0, l["supplier"], sn, l["packing"], ps, l["date"], q, qty, loose, strip,
                           units, int(round(l["rate"] * 100)), int(round(l["value"] * 100)), kind, state, sid, sid, t))
        if kind == "new":
            n_new += 1
            new_ids.append(cur.lastrowid)
        else:
            n_old += 1
        if l["phones"] and sn not in phones_new:
            try:
                have = bool(pa._wa_digits(pa._phone_for(con, l["supplier"])))
            except Exception:                                 # noqa: BLE001
                have = True
            if not have:
                phones_new[sn] = dict(supplier=l["supplier"], phones=l["phones"])
    con.execute("UPDATE order_sheet SET n_lines=?, n_new=?, n_old=?, n_known=?, n_suppliers=?, units_total=?, value_total=?, unresolved=?, phones_new=?"
                " WHERE id=?", (len(lines), n_new, n_old, n_known, len(sups), units_total, value_total * 100,
                                json.dumps(unresolved, ensure_ascii=False), json.dumps(phones_new, ensure_ascii=False), sid))
    con.commit()
    audit(con, who, "order_sheet_loaded", sid, dict(md5=md5, name=name, source=src, newest=newest, lines=len(lines), new=n_new, old=n_old,
                                                     known=n_known, unresolved=len(unresolved), as_ordered=bool(as_ordered)))
    made = []
    if as_ordered and new_ids:
        made = _paper_orders(con, sid, new_ids, newest)
    try:
        compare(con, sid)
    except Exception as e:                                    # noqa: BLE001 -- the comparison never stops a load
        con.execute("UPDATE order_sheet SET cmp=? WHERE id=?", (json.dumps(dict(error=str(e)[:200])), sid))
    con.commit()
    refresh(con)
    if not as_ordered and n_new and source(con) == "marg_sheet":
        _sheet_notice(con, sid)
    con.commit()
    return dict(ok=True, already=False, sheet_id=sid, newest=newest, lines=len(lines), new=n_new, old=n_old, known=n_known,
                unresolved=unresolved, paper_orders=made)


def load_pending(con):
    """The page's fallback: every VERIFIED order sheet the door took that is not loaded yet (its archived copy)."""
    ensure(con)
    out = 0
    try:
        rows = con.execute("SELECT md5, drive_name, server_name, date_from, stamp, source FROM mi_file WHERE type=? AND verdict='VERIFIED' "
                           "ORDER BY received_at", (TYPE,)).fetchall()
    except sqlite3.Error:
        return 0
    for md5, name, server, dfrom, stamp, src in rows:
        if con.execute("SELECT 1 FROM order_sheet WHERE md5=?", (md5,)).fetchone():
            continue
        p = os.path.join(MARG_DIR, "archive", TYPE, str(dfrom or "")[:7], server or "")
        if not (server and os.path.isfile(p)):
            continue
        try:
            load_file(con, p, md5, name or server, src or "push", stamp or "")
            out += 1
        except Exception as e:                                # noqa: BLE001
            print("order_sheet: %s not loaded (%s)" % (server, str(e)[:120]), file=sys.stderr)
    return out


def day_order(con, sid):
    """(medicines, suppliers) of a sheet's own order -- its lines dated its newest date (a reprinted line counts on the sheet that carries it)."""
    r = con.execute("SELECT newest_date FROM order_sheet WHERE id=?", (sid,)).fetchone()
    if not r:
        return 0, 0
    n = con.execute("SELECT COUNT(*), COUNT(DISTINCT supplier_norm) FROM order_sheet_line WHERE last_sheet=? AND line_date=?", (sid, r[0])).fetchone()
    return int(n[0] or 0), int(n[1] or 0)


def newest_sheet(con):
    ensure(con)
    r = con.execute("SELECT * FROM order_sheet ORDER BY taken_at DESC, id DESC LIMIT 1").fetchone()
    return dict(r) if r else None


def refused_sheet(con):
    """The newest order sheet the server refused (mi_file), when it is newer than the newest one taken."""
    try:
        r = con.execute("SELECT received_at, reason, drive_name FROM mi_file WHERE verdict<>'VERIFIED' AND (type=? OR reason LIKE ? OR reason LIKE ?) "
                        "ORDER BY received_at DESC LIMIT 1", (TYPE, "%" + TYPE + "%", "%PENDING ORDERS%")).fetchone()
    except sqlite3.Error:
        return None
    if not r:
        return None
    ns = newest_sheet(con)
    if ns and str(ns["taken_at"])[:19] >= str(r[0]).replace("+05:30", "")[:19]:
        return None
    return dict(at=str(r[0])[:16].replace("T", " "), reason=r[1] or "", name=r[2] or "")


# ------------------------------------------------------------------ the order book
def _phones(con, vendor):
    """(first, second) from the phone book -- a sender's page shows them under the Call button."""
    try:
        r = con.execute("SELECT phone, phone2 FROM purchase_vendor_contact WHERE vendor_norm=?", (_pa().supplier_key(vendor),)).fetchone()
    except sqlite3.Error:
        r = None
    return ((r[0] or "") if r else "", (r[1] or "") if r else "")


def make_order(con, who, vendor, lines, status, via, created_at=None, sheet_id=None, ext_ref="", section="Medicines", note=""):
    """One purchase order, as _staff_send / send_proposal write one (the same tables), made at that moment by that person, saying how
    it went and carrying Marg's entry numbers. lines: [{item, packs, pack_size, rate_p, on_hand}]."""
    ensure(con)
    pa = _pa()
    t = created_at or now_iso()
    cur = con.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, note, total_p, sent_by, section, supplier_norm, ext_ref, "
                      "order_src, order_via, sheet_id) VALUES (?,?,?,?,?,0,?,?,?,?,?,?,?)",
                      (t, who, vendor, status, note or ("S454 %s" % via), who if status != "draft" else None, section, pa.supplier_key(vendor),
                       ext_ref or None, "s454", via, sheet_id))
    oid = cur.lastrowid
    total = 0
    for l in lines:
        packs = int(l["packs"])
        size = max(1, int(l.get("pack_size") or 1))
        rate = int(l.get("rate_p") or 0)
        total += packs * rate
        con.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units, rate_p, value_p, on_hand, per_day, cover_after) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)", (oid, l["item"], packs, size, int(l.get("units") or packs * size), rate, packs * rate,
                                                     l.get("on_hand"), l.get("per_day"), l.get("cover_after")))
    con.execute("UPDATE purchase_order SET total_p=? WHERE id=?", (total, oid))
    audit(con, who, "order_made_s454", oid, dict(vendor=vendor, lines=len(lines), status=status, via=via, sheet=sheet_id, entries=ext_ref))
    return oid


def _sheet_order_lines(rows):
    out = []
    for l in rows:
        packs = int(l["qty"] or 0) + (1 if (l["strip"] and int(l["loose"] or 0)) else 0)
        out.append(dict(item=l["item"], packs=packs, pack_size=(int(l["pack_size"] or 1) if l["strip"] else 1),
                        units=int(l["units"] or 0), rate_p=int(l["rate_p"] or 0), on_hand=None))
    return out


def _paper_orders(con, sid, ids, newest):
    """S454 3.5: the sheet of 02-Oct was ordered by phone from Marg's print -- one order per supplier, made 'on paper' at 15:00 IST on
    the sheet's date, awaiting arrival."""
    made = []
    rows = [dict(r) for r in con.execute("SELECT * FROM order_sheet_line WHERE id IN (%s) ORDER BY supplier_norm, id" % ",".join("?" * len(ids)), ids)]
    by = {}
    for l in rows:
        by.setdefault(l["supplier_norm"], []).append(l)
    t = "%sT%02d:%02d:00" % (newest, PAPER_HOUR[0], PAPER_HOUR[1])
    ortho = _ortho_norm(con)
    for sn, ls in sorted(by.items()):
        oid = make_order(con, "Darpan (Marg sheet, on paper)", ls[0]["supplier"], _sheet_order_lines(ls), "sent", "paper", created_at=t, sheet_id=sid,
                         ext_ref=",".join(sorted({l["entry_no"] for l in ls})), section=("Orthotics" if sn == ortho else "Medicines"),
                         note="S454 3.5: ordered by phone from Marg's print, %s" % dmy(newest))
        con.execute("UPDATE order_sheet_line SET state='ordered', order_id=?, updated_at=? WHERE id IN (%s)" % ",".join("?" * len(ls)),
                    [oid, now_iso()] + [l["id"] for l in ls])
        made.append(dict(order_id=oid, supplier=ls[0]["supplier"], lines=len(ls)))
    con.commit()
    return made


def _ortho_norm(con):
    try:
        import porders                                        # noqa: PLC0415
        return _pa().supplier_key(porders.vendor_of(con))
    except Exception:                                         # noqa: BLE001
        return "YUVIKA SURGICALS"


# ------------------------------------------------------------------ what Marg says of a line: "aa chuka" / "nahi aaya"
def _keys(con, item, printed, resolved):
    ia = _ia()
    ks = {ia.pad_norm(ia.clip(item, ia.PURCHASE_CLIP))}
    try:
        ks |= {ia.pad_norm(ia.clip(f, ia.PURCHASE_CLIP)) for f in ia.aliases_of(con, item)}
    except Exception:                                         # noqa: BLE001
        pass
    return ks, (None if resolved else ia.pad_norm(printed))


def _marg_hit(con, cache, sn, item, printed, resolved, since):
    """(bill_date, bill_no) of the first Marg purchase of the item from the supplier dated on or after `since`, else None."""
    pa = _pa()
    if sn not in cache:
        try:
            cache[sn] = [(r[0], r[1], r[2]) for r in con.execute(
                "SELECT l.item, l.bill_date, l.bill_no FROM purchase_line l WHERE l.supplier_norm=? AND l.direction='PURCHASE' AND " + pa.EFF_LINE +
                " ORDER BY l.bill_date, l.id", (sn,)).fetchall()]
        except sqlite3.Error:
            cache[sn] = []
    ks, prefix = _keys(con, item, printed, resolved)
    ia = _ia()
    for it, bd, bno in cache[sn]:
        if str(bd or "") < since:
            continue
        k = ia.pad_norm(it)
        if k in ks or (prefix and k.startswith(prefix)):
            return str(bd)[:10], str(bno or "")
    return None


def refresh(con, t=None):
    """Every line's word from Marg, the ways out: a never-ticked line Marg has supplied closes ('aa chuka, bina order ke'); a new line
    not ordered within order.sheet_max_age_days of its date lapses into old pending (the owner reads one line). Idempotent."""
    ensure(con)
    t = t or today()
    max_age = int_setting(con, "order.sheet_max_age_days")
    cache = {}
    changed = 0
    rows = [dict(r) for r in con.execute("SELECT * FROM order_sheet_line WHERE state IN ('to_order','old','lapsed')")]
    for l in rows:
        base = l["reorder_day"] or l["line_date"]
        hit = _marg_hit(con, cache, l["supplier_norm"], l["item"], l["item_printed"], l["resolved"], base)
        if l["state"] == "to_order":
            if hit and not l["order_id"]:
                con.execute("UPDATE order_sheet_line SET state='closed_marg', marg_date=?, marg_bill=?, marg_seen_at=?, updated_at=? WHERE id=?",
                            (hit[0], hit[1], now_iso(), now_iso(), l["id"]))
                audit(con, "order sheet", "sheet_line_closed_marg", l["id"], dict(item=l["item"], supplier=l["supplier"], bill=hit[1], date=hit[0]))
                changed += 1
                continue
            bd = _date(base)
            if bd and (t - bd).days >= max_age and not l["order_id"]:
                con.execute("UPDATE order_sheet_line SET state='lapsed', lapsed_at=?, updated_at=? WHERE id=?", (now_iso(), now_iso(), l["id"]))
                audit(con, "order sheet", "sheet_line_lapsed", l["id"], dict(item=l["item"], supplier=l["supplier"], date=base))
                changed += 1
            continue
        if hit and not l["marg_date"]:
            con.execute("UPDATE order_sheet_line SET marg_date=?, marg_bill=?, marg_seen_at=?, updated_at=? WHERE id=?",
                        (hit[0], hit[1], now_iso(), now_iso(), l["id"]))
            changed += 1
    if changed:
        con.commit()
    return changed


def old_visible(con, l, t=None):
    """An old (or lapsed) line before the staff: 'aa chuka' for order.old_done_days from the day it first read so; 'nahi aaya' until it is
    older than order.old_show_days."""
    t = t or today()
    if l["state"] not in ("old", "lapsed"):
        return False
    if l.get("marg_date"):
        seen = _date(l.get("marg_seen_at")) or t
        return (t - seen).days < int_setting(con, "order.old_done_days")
    ld = _date(l["line_date"])
    return bool(ld and (t - ld).days <= int_setting(con, "order.old_show_days"))


def old_lines(con, sn=None, staff=True):
    ensure(con)
    q = "SELECT * FROM order_sheet_line WHERE state IN ('old','lapsed')" + (" AND supplier_norm=?" if sn else "") + " ORDER BY supplier_norm, line_date, id"
    rows = [dict(r) for r in con.execute(q, (sn,) if sn else ())]
    return [l for l in rows if (old_visible(con, l) or not staff)]


def old_word(l, en=False):
    if l.get("marg_date"):
        return ("arrived %s" if en else "aa chuka %s") % ddmm(l["marg_date"])
    return "never came" if en else "nahi aaya"


# ------------------------------------------------------------------ the comparison with the system's own plan (owner only)
def compare(con, sid):
    """At each sheet's load: the system's plan of that moment against the sheet's new lines -- in both (both quantities), only on the
    sheet, only on the system's list. Kept on the sheet's row; the owner reads one line."""
    import order_rules                                        # noqa: PLC0415
    pa = _pa()
    p = order_rules.plan(con, today())
    sys_l = {}
    for v in (p.get("vendors") or {}).values():
        for l in v.get("lines") or []:
            sys_l[pa.norm(l["item"])] = dict(item=l["item"], vendor=v.get("vendor"), qty=int(l.get("qty") or 0), unit=l.get("unit") or "")
    nd = con.execute("SELECT newest_date FROM order_sheet WHERE id=?", (sid,)).fetchone()[0]
    sheet = [dict(r) for r in con.execute("SELECT * FROM order_sheet_line WHERE last_sheet=? AND line_date=? ORDER BY supplier_norm, id", (sid, nd))]
    both, only_sheet = [], []
    seen = set()
    for l in sheet:
        k = pa.norm(l["item"])
        s = sys_l.get(k)
        row = dict(item=l["item"], supplier=l["supplier"], sheet=qty_text(l["qty_raw"]))
        if s:
            seen.add(k)
            row["system"] = ("%d %s" % (s["qty"], "strip" if str(s["unit"]).startswith("strip") else "")).strip()
            both.append(row)
        else:
            only_sheet.append(row)
    only_sys = [dict(item=s["item"], supplier=s["vendor"], system=("%d %s" % (s["qty"], "strip" if str(s["unit"]).startswith("strip") else "")).strip())
                for k, s in sorted(sys_l.items()) if k not in seen]
    out = dict(x=len(both), y=len(sheet), both=both, only_sheet=only_sheet, only_system=only_sys, as_on=p.get("as_on"), at=now_iso())
    con.execute("UPDATE order_sheet SET cmp=?, cmp_at=? WHERE id=?", (json.dumps(out, ensure_ascii=False), now_iso(), sid))
    con.commit()
    return out


def _sheet_notice(con, sid):
    """'Darpan ki order sheet aa gayi: N supplier, M dawa.' -- one push to the ordering team per sheet."""
    n = day_order(con, sid)
    text = "Darpan ki order sheet aa gayi: %d supplier, %d dawa." % (n[1], n[0])
    try:
        import order_rules                                    # noqa: PLC0415
        to = [x.strip().lower() for x in order_rules._setting(con, "order.notice_to").split(",") if x.strip()]
        payload = dict(kind="order", title="Purchase orders", body=text, url="/finance/porders", tag="porders", ttl=3600, renotify=True,
                       ts=int(dt.datetime.now().timestamp() * 1000))
        sent = {}
        for u in to:
            try:
                a, b = order_rules._push(u, payload)
                sent[u] = dict(sent=a, failed=b)
            except Exception as e:                            # noqa: BLE001
                sent[u] = dict(sent=0, failed=1, error=type(e).__name__)
        con.execute("UPDATE order_sheet SET notice=? WHERE id=?", (json.dumps(dict(text=text, sent=sent, at=now_iso())), sid))
    except Exception as e:                                    # noqa: BLE001
        con.execute("UPDATE order_sheet SET notice=? WHERE id=?", (json.dumps(dict(text=text, error=str(e)[:100])), sid))
    con.commit()


# ======================================================================= the suppliers still to be ordered (S454 4.2)
def _edits(con, src, ref):
    return {r[0]: dict(qty=r[1], removed=int(r[2] or 0)) for r in con.execute("SELECT item, qty, removed FROM s454_line_edit WHERE src=? AND ref=?", (src, str(ref)))}


def _drafts(con):
    """{supplier_norm: the newest draft order of the new flow (WhatsApp tapped, not yet ordered)} with its message's state."""
    out = {}
    for o in con.execute("SELECT * FROM purchase_order WHERE status='draft' AND order_src='s454' ORDER BY id"):
        o = dict(o)
        m = None
        try:
            m = con.execute("SELECT id, status, last_error, queued_at, sent_at FROM supplier_msg WHERE kind='order' AND ref=? ORDER BY id DESC LIMIT 1",
                            (o["id"],)).fetchone()
        except sqlite3.Error:
            m = None
        o["msg"] = dict(m) if m else None
        o["lines"] = [dict(l) for l in con.execute("SELECT * FROM purchase_order_line WHERE order_id=? ORDER BY id", (o["id"],))]
        out[o["supplier_norm"] or _pa().supplier_key(o["vendor"])] = o
    return out


def _proposals_today(con, t):
    """order.source = system: the day's proposals that S410's rules let go out (the rules approved, not held, not paused)."""
    import order_rules                                        # noqa: PLC0415
    if not order_rules._rules_ok(con):
        return []
    out = []
    for p in con.execute("SELECT * FROM order_proposal WHERE day=? AND status='open' ORDER BY kind DESC, vendor", (t.isoformat(),)):
        p = dict(p)
        r = order_rules.rule_for(con, p["supplier_norm"])
        if int(r.get("paused") or 0):
            continue
        try:
            p["lines"] = json.loads(p["lines"] or "[]")
        except ValueError:
            p["lines"] = []
        out.append(p)
    return out


def _ortho_short(con):
    try:
        import porders                                        # noqa: PLC0415
        sh = porders.shelf(con)
        return sh["vendor"], [it for it in sh["items"] if it["short"] > 0]
    except Exception:                                         # noqa: BLE001
        return None, []


def entries(con, t=None, with_ortho=True):
    """[{sn, vendor, lines, state, draft, msg_state, called, has_phone, phone, phone2, sources}] -- one card per supplier still to be ordered.
    state: pending | withdrawn (WhatsApp nahi gaya -- call kijiye) | in_line (WhatsApp line mein hai). Frozen: none."""
    ensure(con)
    t = t or today()
    pa = _pa()
    import order_rules                                        # noqa: PLC0415
    if order_rules._frozen(con):
        return []
    drafts = _drafts(con)
    by = {}

    def card(sn, vendor):
        return by.setdefault(sn, dict(sn=sn, vendor=vendor, lines=[], sources=set()))
    if source(con) == "marg_sheet":
        for l in con.execute("SELECT * FROM order_sheet_line WHERE state='to_order' ORDER BY supplier_norm, line_date, id"):
            l = dict(l)
            if l["supplier_norm"] in drafts:
                continue                                      # the draft is this supplier's card until it is ordered
            e = _edits(con, "sheet", l["id"]).get(l["item"]) or {}
            if e.get("removed"):
                continue
            q = int(e["qty"]) if e.get("qty") is not None else int(l["qty"] or 0)
            c = card(l["supplier_norm"], l["supplier"])
            c["lines"].append(dict(src="sheet", ref=str(l["id"]), item=l["item"], qty=q, loose=(l["loose"] if e.get("qty") is None else 0),
                                   strip=l["strip"], pack_size=l["pack_size"], packing=l["packing"], rate_p=l["rate_p"], entry=l["entry_no"],
                                   reordered=bool(l["reorder_day"]), line_date=l["line_date"]))
            c["sources"].add("sheet")
    else:
        for p in _proposals_today(con, t):
            if p["supplier_norm"] in drafts:
                continue
            ed = _edits(con, "proposal", p["id"])
            c = card(p["supplier_norm"], p["vendor"])
            for l in p["lines"]:
                e = ed.get(l["item"]) or {}
                if e.get("removed"):
                    continue
                strip = 1 if str(l.get("unit") or "").startswith("strip") else 0
                c["lines"].append(dict(src="proposal", ref=str(p["id"]), item=l["item"], qty=int(e["qty"]) if e.get("qty") is not None else int(l["qty"] or 0),
                                       loose=0, strip=strip, pack_size=int(l.get("pack_size") or 1), packing=l.get("packing") or "",
                                       rate_p=int(l.get("rate_p") or 0), entry="", reordered=False, on_hand=l.get("on_hand")))
            c["sources"].add("proposal")
    if with_ortho:                                            # S403's orthotic shortage: that supplier's card, on both settings
        vendor, short = _ortho_short(con)
        if vendor and short:
            sn = pa.supplier_key(vendor)
            if sn not in drafts:
                c = card(sn, vendor)
                have = {pa.norm(x["item"]) for x in c["lines"]}
                ed = _edits(con, "ortho", "ortho:" + t.isoformat())
                for it in short:
                    if pa.norm(it["item"]) in have:
                        continue                              # an item on both is shown once, with the sheet's quantity
                    e = ed.get(it["item"]) or {}
                    if e.get("removed"):
                        continue
                    c["lines"].append(dict(src="ortho", ref="ortho:" + t.isoformat(), item=it["item"], qty=int(e["qty"]) if e.get("qty") is not None else int(it["short"]),
                                           loose=0, strip=0, pack_size=1, packing=it.get("packing") or "1*1", rate_p=0, entry="", reordered=False,
                                           on_hand=it.get("shelf")))
                c["sources"].add("ortho")
    for sn, d in drafts.items():                              # a supplier whose WhatsApp was tapped: its draft order is its card
        m = d.get("msg") or {}
        c = card(sn, d["vendor"])
        c["draft"] = d
        c["lines"] = [dict(src="draft", ref=str(d["id"]), item=l["item"], qty=int(l["packs"]), loose=0, strip=1 if int(l["pack_size"] or 1) > 1 else 0,
                           pack_size=int(l["pack_size"] or 1), packing="", rate_p=int(l["rate_p"] or 0), entry="", reordered=False) for l in d["lines"]]
        c["sources"].add("draft")
    out = []
    for sn, c in sorted(by.items(), key=lambda kv: kv[1]["vendor"]):
        if not c["lines"]:
            continue
        d = c.get("draft")
        if d:
            m = d.get("msg") or {}
            c["state"] = "in_line" if m.get("status") in ("queued", "failed") else "withdrawn"
        else:
            c["state"] = "pending"
        p1, p2 = _phones(con, c["vendor"])
        c["has_phone"] = bool(pa._wa_digits(p1))
        c["phone"], c["phone2"] = p1, p2
        c["called"] = _called_since(con, sn, c)
        c["sources"] = sorted(c["sources"])
        out.append(c)
    return out


def _called_since(con, sn, c):
    """When a Call was tapped for this supplier since its lines became due ('call kiya tha, order baaki'), else ''."""
    try:
        r = con.execute("SELECT at, who FROM purchase_audit WHERE action='s454_call' AND ref=? ORDER BY id DESC LIMIT 1", (sn,)).fetchone()
    except sqlite3.Error:
        r = None
    if not r:
        return ""
    since = min([str(x.get("line_date") or "") for x in c["lines"] if x.get("line_date")] or [today().isoformat()])
    return str(r[0]) if str(r[0])[:10] >= since else ""


def entry_of(con, sn):
    return next((e for e in entries(con) if e["sn"] == sn), None)


def order_lines_of(e):
    out = []
    for l in e["lines"]:
        packs = int(l["qty"]) + (1 if (l["strip"] and int(l.get("loose") or 0)) else 0)
        if packs <= 0:
            continue
        size = int(l["pack_size"] or 1) if l["strip"] else 1
        out.append(dict(item=l["item"], packs=packs, pack_size=size, units=packs * size, rate_p=int(l.get("rate_p") or 0), on_hand=l.get("on_hand"),
                        src=l["src"], ref=l["ref"]))
    return out


def _mark_sources(con, e, oid, state, who):
    """The lines of the card now belong to order `oid`: sheet lines in_line / ordered, the proposal sent, the edit store left as it is."""
    t = now_iso()
    for l in e["lines"]:
        if l["src"] == "sheet":
            con.execute("UPDATE order_sheet_line SET state=?, order_id=?, updated_at=? WHERE id=?", (state, oid, t, int(l["ref"])))
        elif l["src"] == "proposal":
            con.execute("UPDATE order_proposal SET status='sent', sent_order_id=?, sent_at=?, sent_by=? WHERE id=? AND status IN ('open','held')",
                        (oid, t, who, int(l["ref"])))
    for pid in {l["ref"] for l in e["lines"] if l["src"] == "proposal"}:
        p = con.execute("SELECT supplier_norm, day FROM order_proposal WHERE id=?", (int(pid),)).fetchone()
        if p:                                                 # S410: the merged ones go with it, as send_proposal does
            con.execute("UPDATE order_proposal SET status='sent', sent_order_id=?, sent_at=?, sent_by=? WHERE supplier_norm=? AND status='merged' AND merged_into<=?",
                        (oid, t, who, p[0], p[1]))


def order_supplier(con, who, sn, via):
    """'Order ho gaya' (via call) or one supplier of 'Sab ko WhatsApp bhejo' (via whatsapp). One order per card, whatever is tapped:
    a draft already made for it is confirmed, never a second. Returns (body, code)."""
    ensure(con)
    pa = _pa()
    e = entry_of(con, sn)
    if not e:
        r = con.execute("SELECT id, created_at, sent_by, created_by, status FROM purchase_order WHERE supplier_norm=? AND order_src='s454' ORDER BY id DESC LIMIT 1",
                        (sn,)).fetchone()
        if r and _within_min(r[1], 10 if via == "call" else 10**6):
            return dict(ok=True, already=True, order_id=r[0], message="Yeh order pehle hi ho chuka hai."), 200
        return dict(ok=False, error="nothing", message="Is supplier ka koi order baaki nahi hai."), 409
    t = now_iso()
    d = e.get("draft")
    if d:
        oid = d["id"]
        if via == "call":
            con.execute("UPDATE purchase_order SET status='sent', sent_by=?, order_via=? WHERE id=? AND status='draft'",
                        (who, "whatsapp+call" if (d.get("msg") or {}).get("status") == "sent" else "call", oid))
            con.execute("UPDATE order_sheet_line SET state='ordered', updated_at=? WHERE order_id=? AND state='in_line'", (t, oid))
            audit(con, who, "s454_ordered", oid, dict(supplier=e["vendor"], via="call", draft=True))
            con.commit()
            return dict(ok=True, order_id=oid, confirmed=True, message="Order ho gaya — %s." % e["vendor"]), 200
        if e["state"] == "withdrawn":
            _queue_message(con, e, oid, who, requeue=True)
            con.commit()
            return dict(ok=True, order_id=oid, queued=True), 200
        return dict(ok=True, already=True, order_id=oid, queued=True), 200
    lines = order_lines_of(e)
    if not lines:
        return dict(ok=False, error="nothing", message="Kuch order karne ko nahi hai."), 409
    if via == "whatsapp" and not e["has_phone"]:
        return dict(ok=False, error="no_phone", message="Is supplier ka phone number yahan nahi hai."), 409
    sids = [int(l["ref"]) for l in e["lines"] if l["src"] == "sheet"]
    sheet_ids = ({int(x[0]) for x in con.execute("SELECT first_sheet FROM order_sheet_line WHERE id IN (%s)" % ",".join("?" * len(sids)), sids)}
                 if sids else set())
    entries_ = sorted({l["entry"] for l in e["lines"] if l.get("entry")})
    section = "Orthotics" if (sn == _ortho_norm(con)) else "Medicines"
    oid = make_order(con, who, e["vendor"], lines, "sent" if via == "call" else "draft", via, sheet_id=(max(sheet_ids) if sheet_ids else None),
                     ext_ref=",".join(entries_), section=section,
                     note="S454 %s · %s" % (via, "Marg sheet " + ",".join(entries_) if entries_ else ("system list" if "proposal" in e["sources"] else "orthotic shortage")))
    _mark_sources(con, e, oid, "ordered" if via == "call" else "in_line", who)
    if via == "whatsapp":
        _queue_message(con, e, oid, who)
    audit(con, who, "s454_ordered" if via == "call" else "s454_whatsapp_queued", oid, dict(supplier=e["vendor"], via=via, lines=len(lines)))
    con.commit()
    return dict(ok=True, order_id=oid, queued=(via == "whatsapp"), message="Order ho gaya — %s." % e["vendor"]), 200


def _within_min(ts, minutes):
    d = _dtm(ts)
    return bool(d and (now() - d) <= dt.timedelta(minutes=minutes))


# ------------------------------------------------------------------ the reception phone (supplier_msg kind 'order')
def wa_body(con, lines, vendor=""):
    """The order's text as built today -- the shop's heading, then one line per medicine with its quantity and unit (qty_words: never
    'units')."""
    pa = _pa()
    try:
        import qty_words as qw                                # noqa: PLC0415
        try:
            raw = setting(con, "stock.whole_unit_items", "[]")
            qw.set_whole_units(json.loads(raw) if raw.startswith("[") else [x for x in raw.split(",") if x.strip()])
        except Exception:                                     # noqa: BLE001
            pass
    except Exception:                                         # noqa: BLE001
        qw = None
    body = []
    for l in lines:
        if qw is not None:
            q = qw.words(int(l["packs"]) * (int(l["pack_size"] or 1) if int(l["pack_size"] or 1) > 1 else 1), pack=int(l["pack_size"] or 1), name=l["item"])
        else:
            q = "%d" % int(l["packs"])
        body.append("%s — %s" % (l["item"], q))
    return pa.WA_HEADER + "\n\n" + "\n".join(body)


def _queue_message(con, e, oid, who, requeue=False):
    import supplier_msg                                       # noqa: PLC0415
    supplier_msg.ensure(con)
    ensure(con)
    pa = _pa()
    lines = [dict(l) for l in con.execute("SELECT item, packs, pack_size FROM purchase_order_line WHERE order_id=? ORDER BY id", (oid,))]
    to = pa._wa_digits(_phones(con, e["vendor"])[0])
    body = wa_body(con, lines, e["vendor"])
    month = today().strftime("%Y-%m")
    if requeue:
        con.execute("UPDATE supplier_msg SET status='queued', attempts=0, last_error=NULL, handed_at=NULL, queued_at=?, to_number=?, body=? "
                    "WHERE kind='order' AND ref=?", (now_iso(), to or None, body, oid))
        audit(con, who, "s454_whatsapp_requeued", oid, dict(supplier=e["vendor"]))
    else:
        supplier_msg._queue_row(con, month, e["sn"], e["vendor"], "order", oid, to, body, None if to else "number nahi")


def phone_state(con):
    """(alive, why): the reception phone has a key and asked the queue door (200) within order.phone_alive_min minutes."""
    tok = setting(con, "supplier_msg.phone_token", "")
    if not tok:
        return False, "no_key"
    at, _sp, code = setting(con, "supplier_msg.phone_last", "").partition(" ")
    d = _dtm(at)
    if not d or code != "200":
        return False, "silent"
    return ((now() - d) <= dt.timedelta(minutes=int_setting(con, "order.phone_alive_min"))), "silent"


def whatsapp_all(con, who):
    """'Sab ko WhatsApp bhejo': every supplier still to be ordered with a number gets its order made and its message queued for the
    reception phone. The phone not set up or silent: nothing is made, the button is disabled, and the owner hears of it once met."""
    alive, why = phone_state(con)
    if not alive:
        con.execute("INSERT INTO setting (key, value, note) VALUES ('s454.phone_off_met', ?, 'S454: when someone last met the disabled WhatsApp button') "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", ("%s %s" % (now_iso(), who),))
        con.commit()
        return dict(ok=False, error="phone_off", why=why, message="Reception phone set nahi hai — call se order kijiye"), 409
    done, skipped = [], []
    for e in entries(con):
        if e["state"] == "in_line":
            continue
        if not e["has_phone"]:
            skipped.append(e["vendor"])
            continue
        body, code = order_supplier(con, who, e["sn"], "whatsapp")
        (done if code == 200 and body.get("ok") else skipped).append(e["vendor"])
    audit(con, who, "s454_whatsapp_all", "", dict(queued=len(done), skipped=len(skipped)))
    con.commit()
    return dict(ok=True, queued=len(done), skipped=skipped, message="%d supplier ka WhatsApp line mein." % len(done)), 200


def on_message_done(con, mid, ok, err=""):
    """supplier_msg's done door: a message of kind 'order' the phone sent makes its supplier ORDERED; one it could not send is withdrawn
    at once and its supplier is pending again ('WhatsApp nahi gaya -- call kijiye'). Fail-soft for the caller."""
    ensure(con)
    r = con.execute("SELECT id, kind, ref, vendor FROM supplier_msg WHERE id=?", (int(mid),)).fetchone()
    if not r or r[1] != "order":
        return None
    oid = int(r[2] or 0)
    o = con.execute("SELECT id, status, order_via, created_by FROM purchase_order WHERE id=?", (oid,)).fetchone()
    if not o:
        return None
    t = now_iso()
    if ok:
        if o[1] == "draft":
            con.execute("UPDATE purchase_order SET status='sent', sent_by=?, order_via='whatsapp' WHERE id=?", ("%s (WhatsApp)" % (o[3] or ""), oid))
            con.execute("UPDATE order_sheet_line SET state='ordered', updated_at=? WHERE order_id=? AND state='in_line'", (t, oid))
        elif o[2] == "call":
            con.execute("UPDATE purchase_order SET order_via='whatsapp+call' WHERE id=?", (oid,))
        audit(con, "reception-phone", "s454_whatsapp_sent", oid, dict(supplier=r[3], message=int(mid)))
    else:
        con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=?", (("withdrawn: phone could not send — %s" % (err or ""))[:200], int(mid)))
        audit(con, "reception-phone", "s454_whatsapp_withdrawn", oid, dict(supplier=r[3], message=int(mid), why="the phone could not send"))
    con.commit()
    return True


def withdraw_late(con):
    """A message not sent within order.whatsapp_wait_min minutes (or one the phone failed) is withdrawn from the queue; its supplier is
    pending again with the same order."""
    ensure(con)
    try:
        import supplier_msg                                   # noqa: PLC0415
        supplier_msg.ensure(con)
    except Exception:                                         # noqa: BLE001
        pass
    wait = int_setting(con, "order.whatsapp_wait_min")
    n = 0
    try:
        rows = con.execute("SELECT id, status, queued_at, ref, vendor FROM supplier_msg WHERE kind='order' AND status IN ('queued','failed')").fetchall()
    except sqlite3.Error:
        return 0
    for mid, st, qa, ref, vendor in rows:
        d = _dtm(qa)
        if st == "failed" or (d and (now() - d) >= dt.timedelta(minutes=wait)):
            o = con.execute("SELECT status FROM purchase_order WHERE id=?", (int(ref or 0),)).fetchone()
            con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=?",
                        ("withdrawn: %s" % ("the phone could not send" if st == "failed" else "not sent within %d minutes" % wait), mid))
            audit(con, "order sheet", "s454_whatsapp_withdrawn", ref, dict(supplier=vendor, message=mid, why=st, order_status=(o[0] if o else None)))
            n += 1
    if n:
        con.commit()
    return n


# ------------------------------------------------------------------ arrival by the bill's scan (D668)
def _assets():
    try:
        return _pa()._assets_con()
    except Exception:                                         # noqa: BLE001
        return None


def pharmacy_scans(days=45):
    """The captured pharmacy scans of the last `days` days from the asset app (READ ONLY): [dict]; None when unreachable."""
    acon = _assets()
    if acon is None:
        return None
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        sel = [c for c in ("id", "stamp_no", "vendor", "bill_no", "bill_date", "total_amount", "submitted_at", "created_at", "ocr_status",
                           "dup_of", "bill_month", "lane", "status", "kind") if c in cols]
        since = (dt.datetime.utcnow() - dt.timedelta(days=days)).strftime("%Y-%m-%d")
        rows = [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' AND COALESCE(status,'')<>'rejected' AND created_at>=? ORDER BY id"
                                              % ", ".join(sel), (since,))]
    except sqlite3.Error:
        rows = []
    finally:
        acon.close()
    for r in rows:
        r["at"] = scan_moment(r)
    return rows


def scan_moment(r):
    """The scan's moment in IST, to the minute: bills.submitted_at (IST) -- else created_at (UTC) + 5:30."""
    d = _dtm(r.get("submitted_at"))
    if d:
        return d
    c = _dtm(r.get("created_at"))
    return (c + dt.timedelta(hours=5, minutes=30)) if c else None


def unread(r):
    """A paper with neither a bill number nor an amount read, or whose reading is headed Estimate / Challan / Quotation (S454 4.7)."""
    no_no = not str(r.get("bill_no") or "").strip()
    no_amt = r.get("total_amount") in (None, "") or _num(r.get("total_amount")) in (None, 0.0)
    head = HEADING_WORDS.search("%s %s" % (r.get("vendor") or "", r.get("bill_no") or ""))
    settled = str(r.get("ocr_status") or "") in ("read", "empty", "failed") or (r.get("at") and (now() - r["at"]) > dt.timedelta(minutes=10))
    return bool(settled and ((no_no and no_amt) or head))


def answers(con, kind=None):
    ensure(con)
    q = "SELECT asset_bill_id, kind, answer, value, by, at FROM s454_scan_answer" + (" WHERE kind=?" if kind else "")
    out = {}
    for r in con.execute(q, (kind,) if kind else ()):
        out.setdefault(int(r[0]), {})[r[1]] = dict(answer=r[2], value=r[3], by=r[4], at=r[5])
    return out


def _resolver(con):
    """A scan's supplier: the intake link's or the reading's EXACT supplier (punctuation apart) or a learnt spelling, or reception's choice.
    The suppliers of the orders awaited and of the sheet are on the list too. A merely similar spelling resolves to nothing."""
    pa = _pa()
    canon = set()
    for q in ("SELECT DISTINCT supplier FROM purchase_bill", "SELECT DISTINCT vendor FROM purchase_order WHERE status IN ('draft','sent','received')",
              "SELECT DISTINCT supplier FROM order_sheet_line"):
        try:
            canon |= {pa.supplier_key(r[0]) for r in con.execute(q) if r[0]}
        except sqlite3.Error:
            pass
    toks = {}
    for k in canon:
        try:
            toks.setdefault(tuple(sorted(set(pa._vendor_tokens_s439(k)))), k)
        except Exception:                                     # noqa: BLE001
            pass
    learned = {}
    try:
        learned = {r[0]: r[1] for r in con.execute("SELECT ocr_norm, supplier_norm FROM purchase_scan_alias")}
    except sqlite3.Error:
        pass
    chosen = {}
    try:
        chosen = {int(r[0]): r[1] for r in con.execute("SELECT asset_bill_id, chosen_vendor FROM purchase_scan_state WHERE COALESCE(chosen_vendor,'') NOT IN ('','-')")}
    except sqlite3.Error:
        pass
    mine = {k: v.get("vendor", {}).get("value") for k, v in answers(con).items() if v.get("vendor")}

    def sup(r):
        sid = int(r["id"])
        if mine.get(sid) and mine[sid] != "-":
            return mine[sid]
        if chosen.get(sid):
            return chosen[sid]
        k = pa.supplier_key(r.get("vendor") or "")
        if not k:
            return None
        if k in canon:
            return k
        if k in learned:
            return learned[k]
        try:
            tk = tuple(sorted(set(pa._vendor_tokens_s439(k))))
            if tk and tk in toks and not pa._is_buyer_s439(list(tk)):
                return toks[tk]
        except Exception:                                     # noqa: BLE001
            pass
        return None
    return sup


def _md(s):
    d = _date(s)
    return (d.month, d.day) if d else None


def _asking(con, o, t, marg_cache):
    """A received order (no tie) still asking for its bill's scan: received on the arrival screen within purchase.arrival_scan_days, and no
    Marg bill of that supplier dated on or after the order's day without a scan has taken its place."""
    rd = _date(o["received_at"])
    if not rd or (t - rd).days >= int_setting(con, "purchase.arrival_scan_days"):
        return False
    sn = o.get("supplier_norm") or _pa().supplier_key(o["vendor"])
    day = str(o["created_at"] or "")[:10]
    key = (sn, day)
    if key not in marg_cache:
        pa = _pa()
        try:
            marg_cache[key] = con.execute("SELECT b.id FROM purchase_bill b WHERE b.supplier_norm=? AND b.bill_date>=? AND " + pa.EFF_BILL +
                                          " AND NOT EXISTS (SELECT 1 FROM purchase_scan_link k WHERE k.bill_id=b.id) LIMIT 1", (sn, day)).fetchone() is not None
        except sqlite3.Error:
            marg_cache[key] = False
    return not marg_cache[key]


def awaiting_scan(con, t=None):
    """{supplier_norm: [orders with no bill scan yet, oldest first]} -- awaited (sent), or received on the arrival screen and still asking."""
    ensure(con)
    t = t or today()
    pa = _pa()
    tied = {r[0] for r in con.execute("SELECT order_id FROM order_scan_tie")}
    out, mc = {}, {}
    for o in con.execute("SELECT * FROM purchase_order WHERE status IN ('sent','received') ORDER BY created_at, id"):
        o = dict(o)
        if o["id"] in tied:
            continue
        if o["status"] == "received" and not _asking(con, o, t, mc):
            continue
        out.setdefault(o.get("supplier_norm") or pa.supplier_key(o["vendor"]), []).append(o)
    return out


def tie_pass(con, who="tie"):
    """Every untied pharmacy scan, oldest first, against its supplier's orders (the rule in the header). Returns the ties made."""
    ensure(con)
    scans = pharmacy_scans()
    if scans is None:
        return []
    t = today()
    sup_of = _resolver(con)
    tied_scans = {r[0] for r in con.execute("SELECT asset_bill_id FROM order_scan_tie")}
    ans = answers(con)
    made = []
    state = {}

    def fresh():
        state["waiting"] = awaiting_scan(con, t)
        state["ents"] = {x["sn"]: x for x in entries(con, with_ortho=False)} if source(con) == "marg_sheet" else {}
    fresh()
    for s in scans:
        sid = int(s["id"])
        if sid in tied_scans or s.get("dup_of") or str(s.get("lane") or "pharmacy") != "pharmacy" or not s.get("at"):
            continue
        if unread(s) and (ans.get(sid, {}).get("pharmacy") or {}).get("answer") != "yes":
            continue                                          # an unread paper is a delivery's paper only after reception's "Haan"
        sn = sup_of(s)
        if not sn:
            continue
        smd = _md(s.get("bill_date"))
        waiting = state["waiting"].get(sn) or []
        cand = [o for o in waiting if _dtm(o["created_at"]) and _dtm(o["created_at"]) <= s["at"]]
        if cand:
            o = cand[0]
            if smd and smd < _md(o["created_at"]):
                continue                                      # a bill older than the order ties nothing
            _tie(con, o, s, "scan", who)
            made.append((o["id"], sid))
            fresh()
            continue
        # a supplier nobody ticked: its bill scanned after the sheet was loaded makes its order, "by the bill's scan"
        e = state["ents"].get(sn)
        if not e:
            continue
        sheet_lines = [l for l in e["lines"] if l["src"] in ("sheet", "draft")]
        if not sheet_lines:
            continue
        ids = [int(l["ref"]) for l in e["lines"] if l["src"] == "sheet"]
        sh = None
        if ids:
            sh = con.execute("SELECT MAX(s.taken_at), MAX(s.newest_date) FROM order_sheet s JOIN order_sheet_line l ON l.first_sheet=s.id WHERE l.id IN (%s)"
                             % ",".join("?" * len(ids)), ids).fetchone()
        elif e.get("draft"):
            sh = (e["draft"]["created_at"], str(e["draft"]["created_at"])[:10])
        if not sh or not _dtm(sh[0]) or _dtm(sh[0]) > s["at"]:
            continue
        if smd and smd < _md(sh[1]):
            continue
        d = e.get("draft")
        if d:
            con.execute("UPDATE purchase_order SET status='sent', order_via='scan', sent_by=? WHERE id=?", ("bill scan %s" % (s.get("stamp_no") or sid), d["id"]))
            con.execute("UPDATE supplier_msg SET status='skipped', last_error='withdrawn: the bill was scanned' WHERE kind='order' AND ref=? AND status IN ('queued','failed')",
                        (d["id"],))
            con.execute("UPDATE order_sheet_line SET state='ordered', updated_at=? WHERE order_id=?", (now_iso(), d["id"]))
            oid = d["id"]
        else:
            lines = order_lines_of(dict(e, lines=sheet_lines))
            ents = sorted({l["entry"] for l in sheet_lines if l.get("entry")})
            oid = make_order(con, "bill scan %s" % (s.get("stamp_no") or sid), e["vendor"], lines, "sent", "scan",
                             created_at=s["at"].isoformat(), ext_ref=",".join(ents), note="S454: made by the bill's scan %s" % (s.get("stamp_no") or sid))
            _mark_sources(con, dict(e, lines=sheet_lines), oid, "ordered", "bill scan")
        o = dict(con.execute("SELECT * FROM purchase_order WHERE id=?", (oid,)).fetchone())
        _tie(con, o, s, "scan_made_order", who)
        made.append((oid, sid))
        fresh()
    if made:
        con.commit()
    return made


def _tie(con, o, s, how, who):
    at = s["at"].isoformat()
    con.execute("INSERT OR IGNORE INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,?)",
                (o["id"], int(s["id"]), s.get("stamp_no") or "", at, now_iso(), how, 1 if o["status"] == "sent" else 0))
    if o["status"] == "sent":
        con.execute("UPDATE purchase_order SET status='received', received_at=?, received_by=? WHERE id=? AND status='sent'",
                    (at, "bill scan %s" % (s.get("stamp_no") or s["id"]), o["id"]))
    audit(con, who, "s454_scan_tie", o["id"], dict(scan=int(s["id"]), stamp=s.get("stamp_no"), how=how, arrived=(o["status"] == "sent"),
                                                    supplier=o["vendor"]))


def ties(con):
    ensure(con)
    return {r[0]: dict(scan=r[1], stamp=r[2], scan_at=r[3], how=r[4]) for r in con.execute("SELECT order_id, asset_bill_id, stamp, scan_at, how FROM order_scan_tie")}


# ------------------------------------------------------------------ the cron (order_rules' tick) and every page read
def cron_pass(con, who="cron"):
    """Neither the tie nor Marg's clearing waits for someone to open the page: order_rules' tick runs this."""
    out = {}
    for name, fn in (("sheets", load_pending), ("withdrawn", withdraw_late), ("refresh", refresh)):
        try:
            out[name] = fn(con)
        except Exception as e:                                # noqa: BLE001
            out[name] = "error: %s" % str(e)[:80]
    try:
        _pa()._rematch_if_changed(con, "S454 %s" % who)
    except Exception as e:                                    # noqa: BLE001
        out["rematch"] = "error: %s" % str(e)[:80]
    try:
        out["ties"] = len(tie_pass(con, who))
    except Exception as e:                                    # noqa: BLE001
        out["ties"] = "error: %s" % str(e)[:80]
    try:
        import porders                                        # noqa: PLC0415
        out["marg_lines"] = porders.detect_supplies(con)
    except Exception as e:                                    # noqa: BLE001
        out["marg_lines"] = "error: %s" % str(e)[:80]
    return out


# ------------------------------------------------------------------ the one reminder of the day; Darpan's line; the owner's lines
def reminder_text(con):
    es = [e for e in entries(con) if e["state"] != "in_line"]
    if not es:
        return None
    return "Order baaki: %s" % ", ".join(e["vendor"] for e in es)


def reminder_due(con, at=None):
    """(key, text) once the day's remind time has come and a supplier is still to be ordered; else (key, None)."""
    at = at or now()
    rt = setting(con, "order.remind_times")
    m = re.match(r"^(\d\d):(\d\d)$", rt)
    if not m:
        return None, None
    key = "R%s%s" % (m.group(1), m.group(2))
    if (at.hour, at.minute) < (int(m.group(1)), int(m.group(2))):
        return key, None
    return key, reminder_text(con)


def day_summary(con):
    """Darpan's old line while the source is the sheet: the sheet's suppliers, ordered and still to be ordered."""
    ns = newest_sheet(con)
    es = [e for e in entries(con, with_ortho=False) if e["state"] != "in_line"]
    if not ns:
        return dict(ok=True, n=0, sent=0, unsent=0, text="", url="/finance/porders")
    tot = day_order(con, ns["id"])[1]
    un = len(es)
    text = ("Order baaki: %d supplier — %s" % (un, ", ".join(e["vendor"] for e in es[:6]))) if un else ""
    return dict(ok=True, n=int(tot or 0), sent=max(0, int(tot or 0) - un), unsent=un, text=text, url="/finance/porders")


def darpan_card(con):
    """His card on Kal ka hisaab: the newest sheet (when it came, how many medicines and suppliers, that reception has it) -- or the
    newest file refused."""
    ensure(con)
    try:
        load_pending(con)
    except Exception:                                         # noqa: BLE001
        pass
    ns = newest_sheet(con)
    rf = refused_sheet(con)
    out = dict(ok=True, refused=bool(rf), refused_at=(rf or {}).get("at", ""), sheet=None)
    if ns:
        n = day_order(con, ns["id"])
        out["sheet"] = dict(date=ddmm(ns["newest_date"]), taken=str(ns["taken_at"])[:16].replace("T", " "), dawa=int(n[0] or 0), suppliers=int(n[1] or 0))
    return out


def owner_lines(con):
    """The owner's Needs-you lines about ordering (S454 7.3)."""
    out = []
    try:
        ensure(con)
        es = entries(con)
        for e in es:
            if e["state"] != "in_line" and not e["has_phone"]:
                out.append(dict(cls="warn", target="porders", text="To order: %s has no phone number in the phone book" % e["vendor"]))
        alive, why = phone_state(con)
        waiting = 0
        try:
            waiting = con.execute("SELECT COUNT(*) FROM supplier_msg WHERE kind='order' AND status IN ('queued','failed')").fetchone()[0]
        except sqlite3.Error:
            pass
        met = setting(con, "s454.phone_off_met", "")
        met_d = _dtm(met.split(" ")[0]) if met else None
        if not alive and (waiting or (met_d and (now() - met_d) <= dt.timedelta(hours=24))):
            out.append(dict(cls="warn", target="porders", text=("The reception phone has no key: WhatsApp orders cannot go" if why == "no_key" else
                                                                 "The reception phone has not asked the server for %d minutes%s" % (
                                                                     int_setting(con, "order.phone_alive_min"),
                                                                     (" -- %d order message(s) wait" % waiting) if waiting else " -- someone met the disabled WhatsApp button"))))
        since = (today() - dt.timedelta(days=7)).isoformat()
        for r in con.execute("SELECT supplier, line_date, COUNT(*) FROM order_sheet_line WHERE state='lapsed' AND lapsed_at>=? GROUP BY supplier_norm, line_date",
                             (since,)):
            out.append(dict(cls="warn", target="porders", text="An order of %s to %s was never placed (%d item%s)" % (dmy(r[1]), r[0], r[2], "" if r[2] == 1 else "s")))
        rf = refused_sheet(con)
        if rf and str(rf["at"])[:10] == today().isoformat():
            out.append(dict(cls="bad", target="porders", text="Darpan's order sheet refused today: %s" % (rf["reason"] or "")[:140]))
        ns = newest_sheet(con)
        if ns:
            un = json.loads(ns.get("unresolved") or "[]")
            if un:
                out.append(dict(cls="info", target="porders", text="Order sheet of %s: %d item name%s not found in Marg's stock list: %s"
                                % (dmy(ns["newest_date"]), len(un), "" if len(un) == 1 else "s", ", ".join(x["item"] for x in un[:6]))))
            for v in (json.loads(ns.get("phones_new") or "{}") or {}).values():
                pa = _pa()
                if not pa._wa_digits(pa._phone_for(con, v["supplier"])):
                    out.append(dict(cls="info", target="porders", text="Order sheet: %s prints a phone number the phone book lacks -- add it in the phone book"
                                    % v["supplier"]))
    except Exception:                                         # noqa: BLE001 -- Needs you never waits on this
        pass
    return out
