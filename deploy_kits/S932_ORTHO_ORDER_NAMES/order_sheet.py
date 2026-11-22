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
#  (History, retired by S543: an old line once said "aa chuka dd-mm" / "nahi aaya" of itself and stayed before the staff for a number
#  of days set by two day settings.) "Dobara order karo" makes an old line a new line of that day.
#
#  S543_ORDER_SHEET_MARG (13-Oct-2026, D716) -- ONE RULE: MARG'S OWN OPEN ORDER. A line is on the ordering pages and on the printed
#  sheet exactly while Marg's newest PENDING ORDERS export prints it: open_order() reads the lines whose last_sheet is the newest sheet
#  (RANK: the export's own capture stamp decides), on every order.source, and puts each in ONE group -- to_order · in_line · ordered
#  (its order under "Maal aaya?", or made less than order.sheet_max_age_days ago) · old (everything else: "Marg mein baaki"; a line
#  ordered here is never re-ordered from the old block). Nothing the system guesses closes a line Marg carries; only an export ranking
#  at or after a line's own moves it; Marg's RECEIVE / PENDING are kept on the line (marg_recv_raw / marg_pend_raw, healed from the
#  archived file by heal_marg_cols); every quantity is qty_of() through qty_words; an order none of whose sheet lines Marg still
#  carries has been closed by Marg (marg_closed_order) and leaves "Maal aaya?".
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
#
#  S605_ORDER_FIXES (20-Oct-2026; D749, F-959, F-960, F-702, F-961):
#    * DARPAN SAYS YES FIRST (D749). The orthotic card is THE LINES DARPAN KEPT (ortho_kept: his newest answer for the item is 'yes' and no
#      order to the orthotic vendor has carried it since) -- never porders' shortage itself, on every order.source. What is put to him is
#      ortho_offer: the shortage (_ortho_short, the one reader) less a line whose shelf or family figure is below zero (never offered, never
#      ordered: the owner's line), less a kept line, less a line answered no / removed while its shortage has not changed. His taps are rows
#      of ortho_yes (one per tap and line; never updated, never deleted) through ortho_answer, the one door (darpan_kal's POST).
#    * ONE HAND-OUT (F-960). withdraw_late withdraws only a message the phone was never handed; one handed and not confirmed within
#      order.whatsapp_wait_min makes its order 'sent' by WhatsApp, marked unconfirmed (audit s454_whatsapp_unconfirmed; the message
#      'skipped' with last_error 'unconfirmed: ...' -- supplier_msg's CHECK admits no new status), and the owner reads one line.
#      order_supplier never queues again a message once handed.
#    * ASK ONCE (F-961). wa_plan is the one list 'Sab ko WhatsApp bhejo' queues; the confirm screen shows it and whatsapp_all refuses (409,
#      nothing queued) when the list the screen showed is not the list now.
#
#  S613_S605_FOLLOWUP (22-Oct-2026; F-960, three loose ends):
#    * THE WAIT STARTS AT THE HAND-OUT. withdraw_late: a handed message becomes unconfirmed when its handed_at is order.whatsapp_wait_min old
#      and is never withdrawn by queued_at; a never-handed message is withdrawn from queued_at, its UPDATE guarded (handed_at NULL, queued).
#    * A LATE "COULD NOT SEND" on an order unconfirmed in this cycle (on_message_done): nothing arrived on it -> the order is a draft again
#      (sent_by NULL, its ordered lines in_line, the message skipped, audit s454_whatsapp_unconfirmed_no) and reception's card reads
#      'WhatsApp nahi gaya -- call kijiye'; something arrived -> the order unchanged, the message skipped, audit
#      s454_whatsapp_unconfirmed_no_arrived, and the owner reads one line that day.
#    * MAY IT BE SENT AGAIN -- ONE RULE (_s613_phone_said_no), read by order_supplier's withdrawn branch and wa_plan: the order's newest
#      audit row of the message's cycle is the phone's own no, and the message is skipped, never sent, handed. Once per no, never after
#      a silence.
#
#  S619_ORDER_TRACKER (22-Oct-2026; the owner's rulings of 22-Oct: two days, the delivery line, the automatic carry, "either to do"):
#    * SETTINGS order.deliver_days / deliver_skip / deliver_window / wa_delivery_line / track_since (order_track reads them: late = two days).
#    * ensure(): table order_carry (order_track.CARRY_DDL, the one DDL) and s454_line_edit.reason (guarded ALTER).
#    * THE TIE: an order whose every line was tapped 'Nahi mila' never asks for a scan; a received order whose every line is answered, Marg
#      having billed one, stops asking (_s619_may_ask, in _asking and awaiting_scan); two or more orders of the dealer waiting -> the scan's
#      reading picks (after it is in, ten minutes at most), else the oldest (_s619_pick). Existing ties are never moved.
#    * THE CARRY: entries() puts a dealer's open carries (order_track) on that dealer's NEXT card as lines src 'carry' (never a card by
#      themselves); order_supplier marks them done on the order made; wa_body says 'pichhle order se baaki (dd-mm)' on them and ends every
#      order with order.wa_delivery_line; cron_pass runs order_track.carry_pass after Marg's detection.
#    * THE REASON: a removal 'Dealer ke paas nahi hai' (s454_line_edit.reason dealer_no) lives while its sheet is Marg's newest (a sheet line;
#      the line returns on a newer sheet that still carries it) or for its day (any other line) -- _s619_live, read by _edits and open_order;
#      open_order marks such a line dealer_no (the paper prints 'dealer ke paas nahi'; old_word says so).
#    * owner_lines: 'Orders: N late, M medicines came short (back on the next order) -- the order list' (order_track.owner_line).
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
    "order.source": ("marg_sheet", "S454 (D666): who decides the order -- marg_sheet (Darpan's sheet), system (the system's own list) or, "
                                   "S485 (D677), darpan (the system's list once Darpan has made it pakka on his own page)"),
    "order.sheet_max_age_days": ("7", "S454: a line of the sheet this old or older, and unknown, is old pending; a new line not ordered this long after its date lapses"),
    "order.sheet_print_old": ("1", "S454: 1 = old pending lines on the printed order sheet, 0 = left off"),
    "order.remind_times": ("17:00", "S454: when the one reminder of the day goes (HH:MM, 05:00-21:50, in tens of minutes)"),
    "order.whatsapp_wait_min": ("60", "S454: a WhatsApp not sent within this many minutes is withdrawn and its supplier is pending again"),
    "order.phone_alive_min": ("720", "S454: the reception phone silent this long -- the WhatsApp button is disabled (17.10: it asks only while "
                                      "awake and unlocked, so a dark phone is normal)"),
    "supplier_msg.handout_gap_min": ("10", "S454 (F-702); S605 (F-960): only the owner's test message is handed to the phone again, after this "
                                           "many minutes -- every other message is handed once"),
    "purchase.register_from": ("2026-10-01", "S454: the first counted month (staff work and alerts start here)"),
    "purchase.parked_months": ("2026-09", "S454: earlier months shown to the staff behind their own link, optional"),
    "purchase.arrival_scan_days": ("7", "S454: how long a received order asks for its bill's scan"),
    "purchase.unread_pair_days": ("7", "S454: how near in date a Marg bill must be for reception to be asked whether an unread paper is that bill"),
    "purchase.entry_mode": ("paper", "S454 P2 (6): paper = Amir enters from the paper bill and his register, the scans only offered; both = S452's words "
                                     "and its grey line; digital is not built"),
    "purchase.total_noise_rs": ("10", "S454 P2 (5): a scan's total within this many rupees of Marg's agrees (the difference shown); more is a question"),
    "purchase.scan_wait_days": ("3", "S454 P2 (7.3): you hear of a bill waiting to be scanned only after this many days"),
    "purchase.entry_wait_days": ("7", "S454 P2 (7.3): you see a read scan not yet entered in Marg after this many days (Amir is not told)"),
    "order.stock_basis": ("count", "S454 P3 (9.2): count = the system's own list works from the shelf figure (the 6 Sep count carried forward); "
                                   "marg = from Marg's closing stock, line for line as before"),
    "stock.gap_min_packs": ("1", "S454 P3 (9.3): a change of the gap between the shelf figure and Marg smaller than this many packs of the item "
                                 "is not counted"),
    "order.sheet_notice_max_min": ("60", "Order sheet arrived: minutes after which the arrival notice is no longer sent"),   # S494 (F-767)
    "order.deliver_days": ("2", "S619 (the owner, 22-Oct): an order is late this many days after it was made, at 18:00 -- the days in order.deliver_skip not counted"),
    "order.deliver_skip": ("SUN", "S619: days not counted towards order.deliver_days (MON..SUN, comma-separated)"),
    "order.deliver_window": ("15:00-18:00,-11:00", "S619: the delivery hours asked of the dealers; a 'Maal aaya' tap outside them shows its time on the order list"),
    "order.wa_delivery_line": ("Kripya maal dopahar 3 se shaam 6 baje ke beech, ya subah 11 baje tak bhejein.",
                               "S619 (the owner, 22-Oct): the last line of every WhatsApp order, and once on the printed sheets"),
    "order.track_since": ("2026-10-12", "S619: the order list, the late rule and the carry count the orders made on or after this day"),
    "order.carry_on_card": ("0", "S820 (the owner, 13-Nov): 0 = a medicine that did not come waits in the red Purane order box and goes to the dealer only on Dobara order karo; 1 = it rides on the dealer's next order by itself (S619, as before)"),
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
    "CREATE TABLE IF NOT EXISTS ortho_yes (id INTEGER PRIMARY KEY, tap INTEGER NOT NULL, at TEXT NOT NULL, by TEXT, answer TEXT NOT NULL "
    "CHECK (answer IN ('yes','no','remove')), item TEXT NOT NULL, qty INTEGER, short_at_answer INTEGER)",      # S605 (D749): never updated, never deleted
    "CREATE TABLE IF NOT EXISTS scan_rescan_ask (id INTEGER PRIMARY KEY, asset_bill_id INTEGER NOT NULL, stamp TEXT, reason TEXT NOT NULL,"
    " asked_by TEXT NOT NULL, asked_at TEXT NOT NULL, done_bill_id INTEGER, done_at TEXT, withdrawn_at TEXT, withdrawn_by TEXT)",   # S618: people's act; only done_* / withdrawn_* set; never deleted
)
ORDER_COLS = (("supplier_norm", "TEXT"), ("ext_ref", "TEXT"), ("order_src", "TEXT"), ("order_via", "TEXT"), ("sheet_id", "INTEGER"))
MSG_COLS = (("handed_at", "TEXT"),)
SHEET_LINE_COLS = (("marg_recv_raw", "TEXT"), ("marg_pend_raw", "TEXT"))   # S543: Marg's RECEIVE / PENDING on the newest export carrying it
RANK = "COALESCE(NULLIF(stamp,''),'0') DESC, taken_at DESC, id DESC"        # S543: which export is Marg's word -- its own capture stamp
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


def _ot():
    import order_track                                        # noqa: PLC0415 -- S619, beside this file
    return order_track


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
    return v if v in ("marg_sheet", "system", "darpan") else "marg_sheet"


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
    for col, typ in SHEET_LINE_COLS:                          # S543: additive; NULL until an export (or heal_marg_cols) gives them
        if not _has_col(con, "order_sheet_line", col):
            try:
                con.execute("ALTER TABLE order_sheet_line ADD COLUMN %s %s" % (col, typ))
            except sqlite3.Error:
                pass
    try:                                                      # S619: the carry's table -- order_track.CARRY_DDL, the one DDL
        con.execute(_ot().CARRY_DDL)
    except Exception:                                         # noqa: BLE001
        pass
    if _has_col(con, "s454_line_edit", "src") and not _has_col(con, "s454_line_edit", "reason"):
        try:                                                  # S619: a removal's reason (dealer_no | not_now)
            con.execute("ALTER TABLE s454_line_edit ADD COLUMN reason TEXT")
        except sqlite3.Error:
            pass
    con.commit()


def audit(con, who, action, ref="", detail=None):
    try:
        _pa()._audit(con, who, action, ref, detail)
    except Exception:                                         # noqa: BLE001 -- the row itself is the record
        pass


def whole_units(con):
    """S543: the ONE loader of the shop's whole-unit list (setting stock.whole_unit_items, loss_piles' home) into qty_words -- called by
    wa_body and by qty_of's readers. Returns the qty_words module, or None when it cannot be imported."""
    try:
        import qty_words as qw                                # noqa: PLC0415
    except Exception:                                         # noqa: BLE001
        return None
    if con is not None:
        try:
            raw = setting(con, "stock.whole_unit_items", "[]")
            qw.set_whole_units(json.loads(raw) if raw.startswith("[") else [x for x in raw.split(",") if x.strip()])
        except Exception:                                     # noqa: BLE001
            pass
    return qw


def _raw_qty(raw):
    """Marg's quantity text as qty_raw keeps it ('10:0', '6', '-') -> (qty, loose, strip); None for '' and Marg's '-'."""
    q = str(raw if raw is not None else "").strip()
    if q in ("", "-"):
        return None
    m = re.match(r"^(\d+):(\d+)$", q)
    if m:
        return int(m.group(1)), int(m.group(2)), 1
    try:
        return int(round(float(q))), 0, 0
    except ValueError:
        return None


def qty_of(l, en=False, pend=False, recv=False, con=None):
    """S543 (charter 8): ONE quantity text for every line -- a sheet line, a card line (an edit applied), a draft or an order line --
    through qty_words, in the shop's one nomenclature ('10 patte', '10 botal', '30 vial', '6 nag'; English on the owner's pages).
    n = packs for an item on the whole-unit list, else units (qty x pack size + loose for a strip line, qty otherwise); the packing is the
    line's own, else 1*<pack size>. pend=True: Marg's PENDING when Marg printed one, else the order quantity; recv=True: Marg's RECEIVE,
    '' when Marg printed none. con (optional) reloads the whole-unit list first."""
    qw = whole_units(con)
    item = l.get("item") or l.get("item_printed") or ""
    ps = max(1, int(l.get("pack_size") or 1))
    packing = l.get("packing") or (("1*%d" % ps) if ps > 1 else "")
    got = None
    if recv or pend:
        got = _raw_qty(l.get("marg_recv_raw" if recv else "marg_pend_raw"))
        if got is None and recv:
            return ""
    if got is None:
        got = (int(l.get("qty") or 0), int(l.get("loose") or 0), 1 if l.get("strip") else 0)
    q, loose, strip = got
    if qw is None:
        return "%d" % q
    n = q if qw.whole_unit_of(item) else ((q * ps + loose) if strip else q)
    return qw.words(n, packing, lang=("en" if en else "hi"), pack=ps, name=item)


def unit_word(l, en=False, con=None):
    """S543: the word for one whole piece of the line's item ('patte', 'botal', 'vial'; English on the owner's pages) -- qty_words."""
    qw = whole_units(con)
    if qw is None:
        return ""
    ps = max(1, int(l.get("pack_size") or 1))
    return qw.whole_word(l.get("packing") or (("1*%d" % ps) if ps > 1 else ""), name=l.get("item") or "", pack=ps, lang=("en" if en else "hi"))


def marg_received(l):
    """S543: Marg's RECEIVE on the line is more than nothing."""
    got = _raw_qty(l.get("marg_recv_raw"))
    return bool(got and (got[0] or got[1]))


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
        q = _raw_text(r[6])
        out.append(dict(supplier=str(r[0]).strip(), phones=[p.strip() for p in str(r[1] or "").split(",") if p.strip()], item=str(r[2]).strip(),
                        packing=str(r[3]).strip(), entry=str(r[4]).strip(), date=_iso_dmy(r[5]), qty_raw=q,
                        rate=_num(r[9]) or 0.0, value=_num(r[10]) or 0.0,
                        recv_raw=_raw_text(r[7]), pend_raw=_raw_text(r[8])))      # S543: Marg's RECEIVE and PENDING, shaped as qty_raw
    return out


def _raw_text(v):
    """A quantity cell as qty_raw keeps it: a number -> its integer text, text ('10:0', Marg's '-') as it is."""
    return ("%d" % int(v)) if isinstance(v, float) else str(v).strip()


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
        old = con.execute("SELECT id, last_sheet FROM order_sheet_line WHERE entry_no=? AND item_printed=?", (l["entry"], l["item"])).fetchone()
        if old:
            if _ranks_at_or_after(con, sid, old[1]):          # S543 (R1-1, R2-1): only an export at or after the line's own moves it
                con.execute("UPDATE order_sheet_line SET last_sheet=?, marg_recv_raw=?, marg_pend_raw=?, updated_at=? WHERE id=?",
                            (sid, l["recv_raw"], l["pend_raw"], t, old[0]))
            n_known += 1
            continue
        item, ok = resolve_item(l["item"], names)
        if not ok:
            unresolved.append(dict(item=l["item"], supplier=l["supplier"]))
        ld = _date(l["date"])
        kind = "new" if (nd and ld and (nd - ld).days < max_age) else "old"
        state = "to_order" if kind == "new" else "old"
        cur = con.execute("INSERT INTO order_sheet_line (entry_no, item_printed, item, resolved, supplier, supplier_norm, packing, pack_size, line_date,"
                          " qty_raw, qty, loose, strip, units, rate_p, value_p, kind, state, first_sheet, last_sheet, created_at, marg_recv_raw, marg_pend_raw)"
                          " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (l["entry"], l["item"], item, 1 if ok else 0, l["supplier"], sn, l["packing"], ps, l["date"], q, qty, loose, strip,
                           units, int(round(l["rate"] * 100)), int(round(l["value"] * 100)), kind, state, sid, sid, t, l["recv_raw"], l["pend_raw"]))
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
    try:                                                      # S454 P1B: compared BEFORE the sheet's own paper orders -- else S410's
        compare(con, sid)                                     # plan counts them as on the way and drops their items (0 of 21)
    except Exception as e:                                    # noqa: BLE001 -- the comparison never stops a load
        con.execute("UPDATE order_sheet SET cmp=? WHERE id=?", (json.dumps(dict(error=str(e)[:200])), sid))
    con.commit()
    made = []
    if as_ordered and new_ids:
        made = _paper_orders(con, sid, new_ids, newest)
    refresh(con)
    if not as_ordered and n_new and source(con) == "marg_sheet" and (newest_sheet(con) or {}).get("id") == sid:   # S543 (R3-8): newest only
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
        p = _archive_path(dfrom, server)
        if not (server and os.path.isfile(p)):
            continue
        try:
            load_file(con, p, md5, name or server, src or "push", stamp or "")
            out += 1
        except Exception as e:                                # noqa: BLE001
            try:                                              # S593 (F-717): a half-loaded sheet never rides into the next one
                con.rollback()
            except sqlite3.Error:
                pass
            print("order_sheet: %s not loaded (%s)" % (server, str(e)[:120]), file=sys.stderr)
    return out


def _archive_path(dfrom, server):
    """The door's archived copy of a taken file (marg_take's archive: archive/ORDER_PENDING/<yyyy-mm>/<server name>)."""
    return os.path.join(MARG_DIR, "archive", TYPE, str(dfrom or "")[:7], server or "")


def sheet_file(con, sheet):
    """S543: the archived file of an order sheet (the door's mi_file row of that md5), or '' when there is none on disk."""
    if not sheet:
        return ""
    try:
        r = con.execute("SELECT server_name, date_from FROM mi_file WHERE md5=? AND type=? ORDER BY received_at DESC LIMIT 1",
                        (sheet["md5"], TYPE)).fetchone()
    except sqlite3.Error:
        return ""
    if not r or not r[0]:
        return ""
    p = _archive_path(r[1], r[0])
    return p if os.path.isfile(p) else ""


def heal_marg_cols(con):
    """S543 (BUILD_NORM 1): the newest sheet's lines with no Marg RECEIVE / PENDING yet get them from that sheet's archived file, by
    (entry number, item as printed). Keyed and idempotent -- a second run writes nothing. Returns the lines filled."""
    ensure(con)
    ns = newest_sheet(con)
    if not ns or not con.execute("SELECT 1 FROM order_sheet_line WHERE last_sheet=? AND marg_pend_raw IS NULL LIMIT 1", (ns["id"],)).fetchone():
        return 0
    p = sheet_file(con, ns)
    if not p:
        return 0
    got = {(x["entry"], x["item"]): x for x in _lines_of(rows_from_file(p))}
    n = 0
    for lid, e, ip in con.execute("SELECT id, entry_no, item_printed FROM order_sheet_line WHERE last_sheet=? AND marg_pend_raw IS NULL",
                                  (ns["id"],)).fetchall():
        x = got.get((e, ip))
        if x is None:
            continue
        con.execute("UPDATE order_sheet_line SET marg_recv_raw=?, marg_pend_raw=? WHERE id=? AND marg_pend_raw IS NULL", (x["recv_raw"], x["pend_raw"], lid))
        n += 1
    if n:
        con.commit()
    return n


def day_order(con, sid):
    """(medicines, suppliers) of a sheet's own order -- its lines dated its newest date (a reprinted line counts on the sheet that carries it)."""
    r = con.execute("SELECT newest_date FROM order_sheet WHERE id=?", (sid,)).fetchone()
    if not r:
        return 0, 0
    n = con.execute("SELECT COUNT(*), COUNT(DISTINCT supplier_norm) FROM order_sheet_line WHERE last_sheet=? AND line_date=?", (sid, r[0])).fetchone()
    return int(n[0] or 0), int(n[1] or 0)


def newest_sheet(con):
    ensure(con)
    r = con.execute("SELECT * FROM order_sheet ORDER BY " + RANK + " LIMIT 1").fetchone()     # S543: the export's own stamp decides
    return dict(r) if r else None


def _ranks_at_or_after(con, a, b):
    """S543: sheet a ranks at or after sheet b by RANK (the one rank: newest_sheet, the loader, the duty map's NEWEST)."""
    if a == b:
        return True
    r = con.execute("SELECT id FROM order_sheet WHERE id IN (?,?) ORDER BY " + RANK + " LIMIT 1", (a, b)).fetchone()
    return bool(r) and r[0] == a


def _s556_ts(s):
    """S556: a stamp of either ISO shape ('T' or ' ', '+05:30', microseconds) -> 'YYYY-MM-DD HH:MM:SS', the one shape compared."""
    return str(s or "").replace("T", " ")[:19]


def _s556_reader_stop(reason):
    """S556: reports_tile.reader_stop -- the ONE rule (the medical PC's reader stopped at a line). Not importable: not a stop (shown, as before)."""
    try:
        import reports_tile                                   # noqa: PLC0415
        return bool(reports_tile.reader_stop(str(reason or "")))
    except Exception:                                         # noqa: BLE001
        return False


def refused_sheet(con, staff=False):
    """The newest order sheet the server refused (mi_file), when it is newer than the newest one taken.
    S556 (F-893): both sides in one time shape; with staff=True (Darpan's card) the newest refused sheet is shown only when it is not a
    reader stop -- an older refusal is never brought back by skipping one. The owner's lines (staff=False) name every refusal."""
    try:
        r = con.execute("SELECT received_at, reason, drive_name FROM mi_file WHERE verdict<>'VERIFIED' AND (type=? OR reason LIKE ? OR reason LIKE ?) "
                        "ORDER BY substr(replace(received_at,'T',' '),1,19) DESC LIMIT 1", (TYPE, "%" + TYPE + "%", "%PENDING ORDERS%")).fetchone()
    except sqlite3.Error:
        return None
    if not r:
        return None
    ns = newest_sheet(con)
    if ns and _s556_ts(ns["taken_at"]) >= _s556_ts(r[0]):
        return None
    if staff and _s556_reader_stop(r[1]):
        return None
    return dict(at=str(r[0])[:16].replace("T", " "), reason=r[1] or "", name=r[2] or "")


# ------------------------------------------------------------------ the order book
def book_card(con, vendor):
    """S574 (charter 2): the numbers a sender's page and paper show, from the phone book's one reader (purchase_app.book_number /
    book_shown) -- (call, wa, shown, on): call rings (Call karo, tel:), wa is where a WhatsApp order goes, shown is printed under the name,
    on = the switch purchase.book_one_record.on. Switch OFF: call = wa = number 1, shown = numbers 1-2 -- as _phones gave them."""
    pa = _pa()
    try:
        return pa.book_number(con, vendor, "call"), pa.book_number(con, vendor, "order"), pa.book_shown(con, vendor), pa.book_on(con)
    except sqlite3.Error:
        return "", "", [], False


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
    """The ways out of 'to be ordered': a never-ticked line Marg no longer carries and has supplied closes ('aa chuka, bina order ke');
    a new line not ordered within order.sheet_max_age_days of its date lapses into old pending (the owner reads one line). S543 (D716):
    a line on Marg's open order is never closed by a guess, and nothing is written for an old line. Idempotent."""
    ensure(con)
    t = t or today()
    max_age = int_setting(con, "order.sheet_max_age_days")
    ns = newest_sheet(con)
    cache = {}
    changed = 0
    rows = [dict(r) for r in con.execute("SELECT * FROM order_sheet_line WHERE state='to_order'")]
    for l in rows:
        base = l["reorder_day"] or l["line_date"]
        if not l["order_id"] and not (ns and l["last_sheet"] == ns["id"]):
            hit = _marg_hit(con, cache, l["supplier_norm"], l["item"], l["item_printed"], l["resolved"], base)
            if hit:
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
    if changed:
        con.commit()
    return changed


# ------------------------------------------------------------------ S543: Marg's own open order -- one reading, four groups
def _stamp_text(ns, full=False):
    """The export's own capture stamp '20261012-143518' -> '12-10 14:35' (full: '12-10-2026 14:35'); a sheet with no stamp -> its date."""
    m = re.match(r"^(\d{4})(\d\d)(\d\d)-(\d\d)(\d\d)", str(ns.get("stamp") or ""))
    if m:
        return ("%s-%s-%s %s:%s" if full else "%s-%s %s:%s") % ((m.group(3), m.group(2), m.group(1), m.group(4), m.group(5)) if full
                                                                 else (m.group(3), m.group(2), m.group(4), m.group(5)))
    return dmy(ns.get("newest_date")) if full else ddmm(ns.get("newest_date"))


def marg_lines(con):
    """The lines Marg's newest export prints (M), on every order.source; [] when no sheet has come."""
    ns = newest_sheet(con)
    if not ns:
        return []
    return [dict(r) for r in con.execute("SELECT * FROM order_sheet_line WHERE last_sheet=? ORDER BY supplier_norm, line_date, id", (ns["id"],))]


def open_order(con, t=None):
    """S543 (charter 2): THE ONE READING of Marg's open order. Writes nothing; never calls entries().
    {sheet, stamp_text, stamp_full, lines (M), suppliers, count, groups: {to_order, in_line, ordered, old}} -- every line of M in exactly
    one group: to_order (not removed by an edit) · in_line · ordered (its order under 'Maal aaya?' -- sent, no bill scan tied -- or made
    less than order.sheet_max_age_days days before today) · old (all else). Each line carries its order's facts (o_status, o_created,
    o_tied, o_via) and whether an edit removed it."""
    ensure(con)
    t = t or today()
    groups = dict(to_order=[], in_line=[], ordered=[], old=[])
    ns = newest_sheet(con)
    if not ns:
        return dict(sheet=None, stamp_text="", stamp_full="", lines=[], suppliers=0, count=0, groups=groups)
    whole_units(con)
    M = marg_lines(con)
    removed, dealer_no = _s619_removed(con, ns)                # S619: a 'Dealer ke paas nahi hai' removal lifts on a newer sheet
    tied = {r[0] for r in con.execute("SELECT order_id FROM order_scan_tie")}
    max_age = int_setting(con, "order.sheet_max_age_days")
    oids = sorted({int(l["order_id"]) for l in M if l.get("order_id")})
    orders = {}
    if oids:
        for r in con.execute("SELECT id, status, created_at, order_via FROM purchase_order WHERE id IN (%s)" % ",".join("?" * len(oids)), oids):
            orders[r[0]] = dict(status=r[1] or "", created_at=r[2] or "", via=r[3] or "", tied=(r[0] in tied))
    for l in M:
        o = orders.get(l.get("order_id")) or {}
        l.update(o_status=o.get("status", ""), o_created=o.get("created_at", ""), o_tied=bool(o.get("tied")), o_via=o.get("via", ""),
                 removed=((str(l["id"]), l["item"]) in removed), dealer_no=((str(l["id"]), l["item"]) in dealer_no))
        st = l["state"]
        od = _date(l["o_created"])
        if st == "to_order" and not l["removed"]:
            groups["to_order"].append(l)
        elif st == "in_line":
            groups["in_line"].append(l)
        elif st == "ordered" and o and ((o["status"] == "sent" and not o["tied"]) or (od is not None and (t - od).days < max_age)):
            groups["ordered"].append(l)
        else:
            groups["old"].append(l)
    return dict(sheet=ns, stamp_text=_stamp_text(ns), stamp_full=_stamp_text(ns, True), lines=M, suppliers=len({l["supplier_norm"] for l in M}),
                count=len(M), groups=groups)


def old_lines(con, sn=None):
    """S543: the old group of Marg's open order (open_order) -- one supplier's when sn is given."""
    return [l for l in open_order(con)["groups"]["old"] if not sn or l["supplier_norm"] == sn]


def old_word(l, en=False):
    """S543: what an old line of Marg's open order says of itself -- 'Marg mein baaki' ('Marg: <recv> aaya, <pend> baaki' once Marg
    records a part), after 'maal aa gaya · ' for a line ordered here whose order has come (by the bill's scan or the arrival tap)."""
    if l.get("dealer_no"):                                    # S619: removed 'Dealer ke paas nahi hai'
        return "the dealer does not have it" if en else "dealer ke paas nahi"
    if marg_received(l):
        w = ("Marg: %s came, %s open" if en else "Marg: %s aaya, %s baaki") % (qty_of(l, en, recv=True), qty_of(l, en, pend=True))
    else:
        w = "still open in Marg" if en else "Marg mein baaki"
    if l.get("state") == "ordered" and l.get("o_status") == "received":
        w = ("goods came · " if en else "maal aa gaya · ") + w
    return w


def old_day(l):
    """S543: the day an old line names -- its order's day for a line ordered here, else the day Marg dates it."""
    return (l.get("o_created") if l.get("state") == "ordered" and l.get("o_created") else (l.get("reorder_day") or l.get("line_date")))


def can_reorder(l):
    """S543 (charter 13): 'Dobara order karo' shows, and its door accepts, only an old line never ordered here and not removed by an edit
    -- state old, lapsed, closed_marg or dropped (a line of open_order)."""
    return l.get("state") in ("old", "lapsed", "closed_marg", "dropped") and not l.get("removed")


def marg_closed_order(con, o, M=None):
    """S543 (2.8): an order made from Marg's sheet -- its ext_ref names entry numbers -- none of whose lines Marg's newest export still
    prints under one of those entry numbers for its supplier has been closed by Marg. An order with no ext_ref: never (judged as before).
    The duty map's reception.order_arrival reads the same rule."""
    ents = {x.strip() for x in str(o.get("ext_ref") or "").split(",") if x.strip()}
    if not ents:
        return False
    M = marg_lines(con) if M is None else M
    items = {r[0] for r in con.execute("SELECT item FROM purchase_order_line WHERE order_id=?", (o["id"],))}
    sn = o.get("supplier_norm")
    return not any(x["supplier_norm"] == sn and x["entry_no"] in ents and x["item"] in items for x in M)


def sheet_lines_of_order(con, oid):
    """{item: order_sheet_line} of the sheet lines an order carries -- their packing and Marg's quantities."""
    try:
        return {r["item"]: dict(r) for r in con.execute("SELECT * FROM order_sheet_line WHERE order_id=?", (oid,))}
    except Exception:                                         # noqa: BLE001
        return {}


def edited(con, l):
    """A to_order sheet line as its card shows it: a quantity edit applied (the edit store, as entries() reads it)."""
    e = _edits(con, "sheet", l["id"]).get(l["item"]) or {}
    return dict(l, qty=int(e["qty"]), loose=0) if e.get("qty") is not None else l


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
        row = dict(item=l["item"], supplier=l["supplier"], sheet=qty_of(l, en=True, con=con))       # S543: qty_words, the owner's English
        if s:
            seen.add(k)
            row["system"] = ("%d %s" % (s["qty"], "strip" if str(s["unit"]).startswith("strip") else "")).strip()
            both.append(row)
        else:
            only_sheet.append(row)
    only_sys = [dict(item=s["item"], supplier=s["vendor"], system=("%d %s" % (s["qty"], "strip" if str(s["unit"]).startswith("strip") else "")).strip())
                for k, s in sorted(sys_l.items()) if k not in seen]
    out = dict(x=len(both), y=len(sheet), both=both, only_sheet=only_sheet, only_system=only_sys, as_on=p.get("as_on"), at=now_iso(),
               basis=("marg" if setting(con, "order.stock_basis") == "marg" else "count"))   # S454 P3B (18.6): the stock the plan was taken on
    con.execute("UPDATE order_sheet SET cmp=?, cmp_at=? WHERE id=?", (json.dumps(out, ensure_ascii=False), now_iso(), sid))
    con.commit()
    return out


def _sheet_notice(con, sid):
    """'Darpan ki order sheet aa gayi: N supplier, M dawa.' -- one push to the ordering team per sheet."""
    n = day_order(con, sid)
    text = "Darpan ki order sheet aa gayi: %d supplier, %d dawa." % (n[1], n[0])
    if not _can_push():                                       # S494 (F-767): the web process cannot push -- the tick sends it
        con.execute("UPDATE order_sheet SET notice=? WHERE id=?", (json.dumps(dict(text=text, pending=True, at=now_iso())), sid))
        con.commit()
        return
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


# ==========================================================================================================================================
# S494_AMIR_JOBS_NOTICE_FLAGS (07-Oct-2026, F-767) -- THE ARRIVAL NOTICE IS SENT BY A PROCESS THAT CAN SEND IT.
#   The web service runs /usr/bin/python3, which has no pywebpush: ring_common.send_push imports it inside its try, so in the web process
#   every phone answered 'failed' with no exception (06-Oct 15:40:43: 0 sent everywhere). _sheet_notice now keeps the text as
#   'pending' when this process cannot push, and order_rules' ten-minute tick (the venv, 05:00-21:50) sends it through cron_pass:
#   never on a later day, never once order.sheet_notice_max_min minutes have passed since the sheet was taken, never on another
#   order.source, and never more than twice (a send that failed everywhere is tried once more, and carries 'retried').
#   ORDER_PUSH_NONE (a walk's "web process") / ORDER_PUSH_STUB (the walk's file) serve the walk; the service never sets them.
# ==========================================================================================================================================
def _can_push():
    """Can THIS process send a Web Push? False under ORDER_PUSH_NONE; True under ORDER_PUSH_STUB; else only if pywebpush imports."""
    if os.environ.get("ORDER_PUSH_NONE"):
        return False
    if os.environ.get("ORDER_PUSH_STUB"):
        return True
    try:
        import pywebpush                                      # noqa: F401,PLC0415 -- the venv has it; /usr/bin/python3 does not
        return True
    except Exception:                                         # noqa: BLE001
        return False


def _s494_notice_shape(nt):
    """'pending', 'failed' (every login 0 sent, one failed at least, never retried / lapsed / dropped) or None."""
    if not isinstance(nt, dict) or any(k in nt for k in ("retried", "lapsed", "dropped")):
        return None
    if nt.get("pending") is True:
        return "pending"
    s = nt.get("sent")
    if not isinstance(s, dict) or not s:
        return None
    try:
        if all(int((v or {}).get("sent") or 0) == 0 for v in s.values()) and any(int((v or {}).get("failed") or 0) > 0 for v in s.values()):
            return "failed"
    except (AttributeError, TypeError, ValueError):
        return None
    return None


def send_pending_notices(con):
    """The tick's sender (S494 A.3): each order sheet whose arrival notice is pending, or failed everywhere once -- lapsed when it was
    taken on an earlier day or more than order.sheet_notice_max_min minutes ago; dropped on another order.source; left for the tick when
    this process cannot push; else the STORED text sent to order.notice_to. Returns the number of rows sent. Fail-soft per row."""
    out = 0
    try:
        rows = con.execute("SELECT id, taken_at, notice FROM order_sheet WHERE notice IS NOT NULL AND notice <> '' ORDER BY id").fetchall()
    except sqlite3.Error:
        return 0
    for sid, taken, raw in rows:
        try:
            try:
                nt = json.loads(raw)
            except (TypeError, ValueError):
                continue
            shape = _s494_notice_shape(nt)
            if not shape:
                continue

            def put(d):
                con.execute("UPDATE order_sheet SET notice=? WHERE id=?", (json.dumps(d), sid))
                con.commit()
            t0 = _dtm(taken)
            if str(taken or "")[:10] != today().isoformat() or t0 is None \
                    or (now() - t0).total_seconds() / 60.0 > int_setting(con, "order.sheet_notice_max_min"):
                nt.update(lapsed=True, pending=False)
                put(nt)
                continue
            if source(con) != "marg_sheet":
                nt.update(dropped="source", pending=False)
                put(nt)
                continue
            if not _can_push():
                continue                                      # this process cannot: the tick will
            text = nt.get("text") or ""
            if not text:
                continue
            import order_rules                                # noqa: PLC0415
            to = [x.strip().lower() for x in order_rules._setting(con, "order.notice_to").split(",") if x.strip()]
            payload = dict(kind="order", title="Purchase orders", body=text, url="/finance/porders", tag="porders", ttl=3600, renotify=True,
                           ts=int(dt.datetime.now().timestamp() * 1000))
            sent = {}
            for u in to:
                try:
                    a, b = order_rules._push(u, payload)
                    sent[u] = dict(sent=a, failed=b)
                except Exception as e:                        # noqa: BLE001
                    sent[u] = dict(sent=0, failed=1, error=type(e).__name__)
            new = dict(text=text, sent=sent, at=now_iso(), first_at=nt.get("first_at") or nt.get("at"), pending=False)
            if shape == "failed":
                new["retried"] = True
            put(new)
            out += 1
        except Exception as e:                                # noqa: BLE001 -- one row never stops the others
            print("order_sheet: notice of sheet %s not sent (%s)" % (sid, str(e)[:120]), file=sys.stderr)
    return out
# ---- S494 (Part A) end -------------------------------------------------------------------------------------------------------------------


# ======================================================================= the suppliers still to be ordered (S454 4.2)
def _edits(con, src, ref):
    """S619: a removal 'Dealer ke paas nahi hai' counts only while it lives (_s619_live): a sheet line's until a newer Marg sheet, any other's for its day."""
    has = _has_col(con, "s454_line_edit", "reason")
    taken = _s619_taken(con) if src == "sheet" else ""
    out = {}
    for r in con.execute("SELECT item, qty, removed, %s, at FROM s454_line_edit WHERE src=? AND ref=?" % ("reason" if has else "NULL"), (src, str(ref))):
        out[r[0]] = dict(qty=r[1], removed=(int(r[2] or 0) if _s619_live(r[3], r[4], src, taken) else 0), reason=r[3])
    return out


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


def _proposals_today(con, t, status="open"):
    """order.source = system: the day's proposals that S410's rules let go out (the rules approved, not held, not paused).
    S485 (D677): order.source = darpan asks for status darpan_ok -- the ones Darpan has made pakka."""
    import order_rules                                        # noqa: PLC0415
    if not order_rules._rules_ok(con):
        return []
    out = []
    for p in con.execute("SELECT * FROM order_proposal WHERE day=? AND status=? ORDER BY kind DESC, vendor", (t.isoformat(), status)):
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


# ---- S605 (D749, F-959): Darpan says yes to the orthotic list first ------------------------------------------------------------------
S605_ANSWERS = ("yes", "no", "remove")


def _s605_vendor(con):
    try:
        import porders                                        # noqa: PLC0415
        return porders.vendor_of(con) or None
    except Exception:                                         # noqa: BLE001
        return None


def _s605_answers(con):
    """{item: Darpan's newest ortho_yes row for it}."""
    out = {}
    for r in con.execute("SELECT id, tap, at, by, answer, item, qty, short_at_answer FROM ortho_yes ORDER BY id"):
        out[r[5]] = dict(id=r[0], tap=r[1], at=r[2], by=r[3], answer=r[4], item=r[5], qty=r[6], short=r[7])
    return out



# ---- S932 (F-1579, 22-Nov-2026): an orthotic ORDER LINE carries Marg's CURRENT name -------------------------------------------------
#  The orthotic lane keys its rows by the count's names (the 06-Sep spellings): for the 22 renamed sizes Amir ticked (item_alias), that is
#  a name Marg no longer prints -- ANKLE BINDER BAMBOO M was ordered under it thrice. The lane's own keys stay as they are (porder_keep, the
#  section map, Darpan's yes rows); only what LEAVES the lane -- the order line reception sends, the dealer's sheet, Darpan's and his
#  flow rows -- carries the ticked NEW name, and the lane's lookups read both names (_s932_forms; porders._on_order folds a new name back).
def _s932_map(con):
    """{OLD name: NEW name} of the ticked renames, EXACT names only (never a clip: orthotic sizes differ only at the tail, so a 20-letter clip
    is shared by siblings). A chain (X->Y ticked and Y->Z ticked) folds nothing on Y: Y is also a lane key of its own. Fail-soft: {}."""
    try:
        rows = [r for r in _ia().done_rows(con) if r.get("old_name") and r.get("new_name")]
        olds = {str(r["old_name"]) for r in rows}
        return {str(r["old_name"]): str(r["new_name"]) for r in rows if str(r["new_name"]) not in olds}
    except Exception:                                         # noqa: BLE001
        return {}


def _s932_marg_name(con, name, m=None):
    """The ticked rename's NEW name for a count name (exact; a spacing/case difference is matched by item_alias.pad_norm); the name itself
    when no rename is ticked. Fail-soft."""
    m = _s932_map(con) if m is None else m
    if name in m:
        return m[name]
    try:
        pn = _ia().pad_norm(name)
        for o, n in m.items():
            if _ia().pad_norm(o) == pn:
                return n
    except Exception:                                         # noqa: BLE001
        pass
    return name


def _s932_forms(con, name, m=None):
    """[name, its ticked NEW name] -- the exact spellings an order line of this item may carry (never a clip: see _s932_map)."""
    mn = _s932_marg_name(con, name, m)
    return [name] if mn == name else [name, mn]


def _s605_ordered_since(con, sn, item, at, m=None):
    """An order of the new flow to the orthotic vendor (draft, sent or received), made at or after `at`, carries the item -- under the count's
    name or Marg's current name (S932; m = _s932_map(con) built once by the caller)."""
    forms = _s932_forms(con, item, m)
    return con.execute("SELECT 1 FROM purchase_order o JOIN purchase_order_line l ON l.order_id=o.id WHERE o.order_src='s454' AND o.supplier_norm=? "
                       "AND o.status IN ('draft','sent','received') AND o.created_at>=? AND l.item IN (%s) LIMIT 1" % ",".join("?" * len(forms)),
                       tuple([sn, at] + forms)).fetchone() is not None


def ortho_kept(con):
    """(vendor, [rows]) -- THE ONE RULE of the orthotic card (entries() reads it, nothing else): the lines whose newest answer is Darpan's
    'yes' and that no order to the orthotic vendor has carried since. Reads his rows and the order book only; writes nothing."""
    ensure(con)
    vendor = _s605_vendor(con)
    if not vendor:
        return None, []
    sn = _pa().supplier_key(vendor)
    m = _s932_map(con)                                        # S932: the ticked renames read once for the whole list
    out = [a for a in _s605_answers(con).values() if a["answer"] == "yes" and not _s605_ordered_since(con, sn, a["item"], a["at"], m)]
    return vendor, sorted(out, key=lambda a: a["id"])


def _s605_impossible(it):
    """A line whose shelf figure, or its family's, is below zero: never put to Darpan, never ordered -- the owner's line instead."""
    fam = it.get("family_shelf")
    return int(it.get("shelf") or 0) < 0 or (fam is not None and int(fam) < 0)


def ortho_offer(con):
    """(vendor, offer, impossible) -- the lines put to Darpan on Kal ka hisaab: porders' shortage (_ortho_short) less an impossible line,
    less a kept line not yet ordered (it is on the card), less a line whose newest answer (no, remove, or a yes already ordered) was given at
    the shortage it has now. A new sale or arrival that moves the shortage offers it again."""
    ensure(con)
    vendor, short = _ortho_short(con)
    if not vendor:
        return None, [], []
    ans = _s605_answers(con)
    kept = {a["item"] for a in ortho_kept(con)[1]}
    offer, bad = [], []
    for it in short:
        if _s605_impossible(it):
            bad.append(it)
            continue
        if it["item"] in kept:
            continue
        a = ans.get(it["item"])
        if a and a["short"] is not None and int(a["short"]) == int(it["short"]):
            continue
        offer.append(it)
    return vendor, offer, bad


def darpan_ortho(con):
    """Darpan's section 'Orthotic kam hai' (charter 14: only what it reads): the lines put to him, the vendor's first word, his newest yes /
    no of today (HH:MM)."""
    vendor, offer, _bad = ortho_offer(con)
    if not vendor:
        return dict(ok=False, n=0, items=[])
    last = dict(con.execute("SELECT answer, MAX(at) FROM ortho_yes WHERE substr(at,1,10)=? AND answer IN ('yes','no') GROUP BY answer",
                            (now().date().isoformat(),)).fetchall())
    return dict(ok=True, n=len(offer), who=vendor.split()[0].title(), url="/finance/porders",
                items=[dict(item=it["item"], short=int(it["short"]), approx=bool(it.get("approx"))) for it in offer],
                yes_at=str(last.get("yes") or "")[11:16], no_at=str(last.get("no") or "")[11:16])


def ortho_answer(con, who, action, items):
    """Darpan's tap -- the one door (D749): 'remove' one line, 'yes' the lines shown (kept, with the quantities shown), 'no' every line
    shown. One ortho_yes row per line, one tap number per tap. The lines the screen showed must be the offer now (and for yes / no all of
    it), else 409 and nothing is written. Returns (body, code)."""
    ensure(con)
    if action not in S605_ANSWERS:
        return dict(ok=False, error="bad_action"), 400
    try:
        shown = [(str(x.get("item") or ""), int(x.get("qty"))) for x in (items or [])]
    except (TypeError, ValueError, AttributeError):
        return dict(ok=False, error="bad_items"), 400
    vendor, offer, _bad = ortho_offer(con)
    cur = {it["item"]: int(it["short"]) for it in offer}
    if (not shown or any(cur.get(i) != q for i, q in shown) or (action == "remove" and len(shown) != 1)
            or (action != "remove" and sorted(i for i, _q in shown) != sorted(cur))):
        return dict(ok=False, error="list_changed", message="सूची बदल गई — फिर से देखिए"), 409
    tap = int(con.execute("SELECT COALESCE(MAX(tap), 0) + 1 FROM ortho_yes").fetchone()[0])
    t = now_iso()
    for i, q in shown:
        con.execute("INSERT INTO ortho_yes (tap, at, by, answer, item, qty, short_at_answer) VALUES (?,?,?,?,?,?,?)", (tap, t, who, action, i, q, cur[i]))
    audit(con, who, "s605_ortho_" + action, tap, dict(vendor=vendor, items=[i for i, _q in shown]))
    con.commit()
    return dict(ok=True, tap=tap, at=t[11:16], n=len(shown)), 200


def entries(con, t=None, with_ortho=True):
    """[{sn, vendor, lines, state, draft, msg_state, called, has_phone, phone, wa, shown, book_on, sources}] -- one card per supplier still to be
    ordered (S574: phone = the Calls number, wa = the Order WhatsApp number, shown = the numbers printed, from book_card).
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
        for l in open_order(con, t)["groups"]["to_order"]:     # S543: Marg's open order -- its to_order group, in its order
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
        for p in _proposals_today(con, t, "darpan_ok" if source(con) == "darpan" else "open"):   # S485 (D677)
            if p["supplier_norm"] in drafts:
                continue
            ed = _edits(con, "proposal", p["id"])
            c = card(p["supplier_norm"], p["vendor"])
            for l in p["lines"]:
                e = ed.get(l["item"]) or {}
                if e.get("removed") or l.get("held"):             # S485: a line Darpan held ("is baar nahi") is not on the card
                    continue
                strip = 1 if str(l.get("unit") or "").startswith("strip") else 0
                c["lines"].append(dict(src="proposal", ref=str(p["id"]), item=l["item"], qty=int(e["qty"]) if e.get("qty") is not None else int(l["qty"] or 0),
                                       loose=0, strip=strip, pack_size=int(l.get("pack_size") or 1), packing=l.get("packing") or "",
                                       rate_p=int(l.get("rate_p") or 0), entry="", reordered=False, on_hand=l.get("on_hand")))
            c["sources"].add("proposal")
    if with_ortho:                                            # S605 (D749): the lines Darpan kept, not yet ordered -- never the shortage itself
        vendor, kept = ortho_kept(con)
        if vendor and kept:
            sn = pa.supplier_key(vendor)
            if sn not in drafts:
                c = card(sn, vendor)
                have = {pa.norm(x["item"]) for x in c["lines"]}
                m932 = _s932_map(con)                         # S932: once for the card
                for a in kept:
                    mn = _s932_marg_name(con, a["item"], m932)   # S932 (F-1579): the order line carries Marg's CURRENT name
                    if pa.norm(a["item"]) in have or pa.norm(mn) in have:
                        continue                              # an item on both is shown once, with the sheet's quantity
                    ref = "ortho:%d" % a["id"]                # his yes row: reception's quantity edit keeps to the line
                    ed = _edits(con, "ortho", ref)
                    e = ed.get(mn) or ed.get(a["item"]) or {}
                    if e.get("removed"):
                        continue
                    c["lines"].append(dict(src="ortho", ref=ref, item=mn, qty=int(e["qty"]) if e.get("qty") is not None else int(a["qty"] or 0),
                                           loose=0, strip=0, pack_size=1, packing="1*1", rate_p=0, entry="", reordered=False, on_hand=None))
                c["sources"].add("ortho")
    try:                                                      # S619 (3.4): a medicine that did not come rides on its dealer's NEXT card
        for cr in (_ot().open_carries(con) if setting(con, "order.carry_on_card") == "1" else []):   # S820: only when the owner says 1; else it waits in the Purane order box for Dobara order karo
            c = by.get(cr["supplier_norm"])
            if cr["supplier_norm"] in drafts or not c or not c["lines"]:
                continue                                      # never a card by itself: it goes on the dealer's next order
            if pa.norm(cr["item"]) in {pa.norm(x["item"]) for x in c["lines"]}:
                continue                                      # the item is on the card already: shown once
            e = _edits(con, "carry", cr["id"]).get(cr["item"]) or {}
            if e.get("removed"):
                continue
            ps = int(cr.get("pack_size") or 1)
            pk, rate = _s619_line(con, cr)
            c["lines"].append(dict(src="carry", ref=str(cr["id"]), item=cr["item"], qty=(int(e["qty"]) if e.get("qty") is not None else int(cr["qty"])),
                                   loose=0, strip=(1 if ps > 1 else 0), pack_size=ps, packing=pk, rate_p=rate, entry="", reordered=False,
                                   carry_from=str(cr.get("from_at") or cr["at"])[:10], on_hand=None))
            c["sources"].add("carry")
    except Exception:                                         # noqa: BLE001 -- the cards never wait on the carry
        pass
    for sn, d in drafts.items():                              # a supplier whose WhatsApp was tapped: its draft order is its card
        m = d.get("msg") or {}
        c = card(sn, d["vendor"])
        c["draft"] = d
        sl = sheet_lines_of_order(con, d["id"])               # S543 (R1-9, R2-5): a draft line reads its sheet line's packing
        c["lines"] = [dict(src="draft", ref=str(d["id"]), item=l["item"], qty=int(l["packs"]), loose=0, strip=1 if int(l["pack_size"] or 1) > 1 else 0,
                           pack_size=int(l["pack_size"] or 1), packing=((sl.get(l["item"]) or {}).get("packing") or ""), rate_p=int(l["rate_p"] or 0),
                           entry="", reordered=False) for l in d["lines"]]
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
        call, wa, shown, on = book_card(con, c["vendor"])        # S574: the one reader
        c["has_phone"] = bool(pa._wa_digits(wa))
        c["phone"], c["wa"], c["shown"], c["book_on"] = call, wa, shown, on
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
            con.execute("UPDATE order_proposal SET status='sent', sent_order_id=?, sent_at=?, sent_by=? WHERE id=? AND status IN ('open','held','darpan_ok')",
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
            if _s605_handed(con, oid) and not _s613_phone_said_no(con, oid):   # S605 (F-960): handed -> call; S613: unless the phone said no
                return dict(ok=False, error="handed", message="WhatsApp nahi gaya — call kijiye"), 409
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
    _s619_carry_done(con, e, oid)                             # S619: the carried lines ride on this order (never carried again)
    if via == "whatsapp":
        _queue_message(con, e, oid, who)
    audit(con, who, "s454_ordered" if via == "call" else "s454_whatsapp_queued", oid, dict(supplier=e["vendor"], via=via, lines=len(lines)))
    con.commit()
    return dict(ok=True, order_id=oid, queued=(via == "whatsapp"), message="Order ho gaya — %s." % e["vendor"]), 200


def _within_min(ts, minutes):
    d = _dtm(ts)
    return bool(d and (now() - d) <= dt.timedelta(minutes=minutes))


# ------------------------------------------------------------------ the reception phone (supplier_msg kind 'order')
def wa_body(con, lines, vendor="", carried=None):
    """The order's text as built today -- the shop's heading, then one line per medicine with its quantity and unit (qty_words: never
    'units'). S619: a carried line says 'pichhle order se baaki (dd-mm)' (carried = {item: 'dd-mm'}); order.wa_delivery_line ends the order, once."""
    pa = _pa()
    qw = whole_units(con)                                     # S543: the one loader of the whole-unit list
    carried = carried or {}
    body = []
    for l in lines:
        if qw is not None:
            q = qw.words(int(l["packs"]) * (int(l["pack_size"] or 1) if int(l["pack_size"] or 1) > 1 else 1), pack=int(l["pack_size"] or 1), name=l["item"])
        else:
            q = "%d" % int(l["packs"])
        t = "%s — %s" % (l["item"], q)
        if l["item"] in carried:
            t += " · pichhle order se baaki (%s)" % carried[l["item"]]
        body.append(t)
    dl = setting(con, "order.wa_delivery_line") if con is not None else ""
    return pa.WA_HEADER + "\n\n" + "\n".join(body) + (("\n\n" + dl) if dl else "")


def _queue_message(con, e, oid, who, requeue=False):
    import supplier_msg                                       # noqa: PLC0415
    supplier_msg.ensure(con)
    ensure(con)
    pa = _pa()
    lines = [dict(l) for l in con.execute("SELECT item, packs, pack_size FROM purchase_order_line WHERE order_id=? ORDER BY id", (oid,))]
    to = pa._wa_digits(pa.book_number(con, e["vendor"], "order"))     # S574: the Order WhatsApp number
    body = wa_body(con, lines, e["vendor"], carried=_s619_carried(con, oid))   # S619: both queue paths
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


def _s605_handed(con, oid):
    """S605 (F-960): the order's message was handed to the reception phone (handed_at, never reset by the server)."""
    return con.execute("SELECT 1 FROM supplier_msg WHERE kind='order' AND ref=? AND handed_at IS NOT NULL LIMIT 1", (int(oid),)).fetchone() is not None


S613_CYCLE = ("s454_whatsapp_queued", "s454_whatsapp_requeued", "s454_whatsapp_withdrawn", "s454_whatsapp_unconfirmed",
              "s454_whatsapp_unconfirmed_no", "s454_whatsapp_sent")


def _s613_phone_said_no(con, oid):
    """S613 (F-960): THE ONE RULE 'may this order's message be queued again', read by order_supplier's withdrawn branch and by wa_plan.
    True only when the NEWEST of the order's audit rows of the message's cycle (S613_CYCLE) is the phone's own no -- s454_whatsapp_withdrawn
    with why 'the phone could not send', or s454_whatsapp_unconfirmed_no -- AND the message is skipped, never sent (sent_at NULL) and was
    handed (handed_at set). The history of answers lives only in purchase_audit (api_done overwrites status and last_error). Once per no;
    a handed message the phone never answered is never queued again (call instead)."""
    try:
        m = con.execute("SELECT status, sent_at, handed_at FROM supplier_msg WHERE kind='order' AND ref=? ORDER BY id DESC LIMIT 1", (int(oid),)).fetchone()
        if not m or m[0] != "skipped" or m[1] or not m[2]:
            return False
        r = con.execute("SELECT action, detail FROM purchase_audit WHERE ref=? AND action IN (%s) ORDER BY id DESC LIMIT 1" % ",".join("?" * len(S613_CYCLE)),
                        (str(int(oid)),) + S613_CYCLE).fetchone()
    except (sqlite3.Error, TypeError, ValueError):
        return False
    if not r:
        return False
    if r[0] == "s454_whatsapp_unconfirmed_no":
        return True
    if r[0] == "s454_whatsapp_withdrawn":
        try:
            d = json.loads(r[1] or "{}")
        except ValueError:
            d = {}
        return isinstance(d, dict) and d.get("why") == "the phone could not send"
    return False


def wa_plan(con):
    """S605 (F-961): (queue, nonum, call) -- THE ONE LIST of 'Sab ko WhatsApp bhejo': every card not in the phone's line with an Order
    WhatsApp number (queue), without one (nonum), and withdrawn after the phone was handed its message (call: never sent again). The
    confirm screen shows it; whatsapp_all queues it. Writes nothing."""
    q, nonum, call = [], [], []
    for e in entries(con):
        if e["state"] == "in_line":
            continue
        did = (e.get("draft") or {}).get("id") or 0
        if e["state"] == "withdrawn" and _s605_handed(con, did) and not _s613_phone_said_no(con, did):   # S613: after the phone's no, queued again
            call.append(e)
            continue
        (q if e["has_phone"] else nonum).append(e)
    return q, nonum, call


def whatsapp_all(con, who, expect=None):
    """'Sab ko WhatsApp bhejo': every supplier of wa_plan's queue gets its order made and its message queued for the reception phone.
    S605 (F-961): expect = the supplier keys the confirm screen showed; a different list now -> 409, nothing queued. The phone not set up
    or silent: nothing is made, the button is disabled, and the owner hears of it once met."""
    alive, why = phone_state(con)
    if not alive:
        con.execute("INSERT INTO setting (key, value, note) VALUES ('s454.phone_off_met', ?, 'S454: when someone last met the disabled WhatsApp button') "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", ("%s %s" % (now_iso(), who),))
        con.commit()
        return dict(ok=False, error="phone_off", why=why, message="Reception phone set nahi hai — call se order kijiye"), 409
    q, nonum, call = wa_plan(con)
    if expect is not None and sorted(set(str(x) for x in expect)) != sorted(e["sn"] for e in q):
        return dict(ok=False, error="list_changed", message="List badal gayi — dobara dekhiye"), 409
    done, skipped = [], [e["vendor"] for e in nonum + call]
    for e in q:
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
    elif _s613_unconfirmed_now(con, oid, int(mid), o):        # S613 (F-960): the phone's no after the unconfirmed hour
        _s613_late_no(con, oid, int(mid), r[3], err, t)
    else:
        con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=?", (("withdrawn: phone could not send — %s" % (err or ""))[:200], int(mid)))
        audit(con, "reception-phone", "s454_whatsapp_withdrawn", oid, dict(supplier=r[3], message=int(mid), why="the phone could not send"))
    con.commit()
    return True


def _s613_unconfirmed_now(con, oid, mid, o):
    """S613 (F-960): the order was made 'sent' by the unconfirmed step in THIS cycle -- an audit row s454_whatsapp_unconfirmed newer than its
    newest s454_whatsapp_requeued -- cross-checked structurally: the order sent (or received) by WhatsApp, the message never sent."""
    try:
        if not o or o[1] not in ("sent", "received") or o[2] != "whatsapp":
            return False
        m = con.execute("SELECT sent_at FROM supplier_msg WHERE id=?", (int(mid),)).fetchone()
        if not m or m[0]:
            return False
        un = con.execute("SELECT MAX(id) FROM purchase_audit WHERE ref=? AND action='s454_whatsapp_unconfirmed'", (str(int(oid)),)).fetchone()[0]
        rq = con.execute("SELECT MAX(id) FROM purchase_audit WHERE ref=? AND action='s454_whatsapp_requeued'", (str(int(oid)),)).fetchone()[0]
    except sqlite3.Error:
        return False
    return bool(un) and (rq is None or int(un) > int(rq))


def _s613_late_no(con, oid, mid, vendor, err, t):
    """S613 (F-960): the phone said it could not send an order already marked sent-unconfirmed. Nothing arrived on it (no line supplied, billed
    or arrived, no bill-scan tie) -> the order is a draft again, sent_by NULL, the lines the unconfirmed step made ordered back in_line, the
    message skipped with the phone's error, audit s454_whatsapp_unconfirmed_no: reception's card reads 'WhatsApp nahi gaya -- call kijiye'.
    Something arrived -> the order unchanged, the message skipped, audit s454_whatsapp_unconfirmed_no_arrived (the owner's line, today)."""
    n = con.execute("SELECT COUNT(*) FROM purchase_order_line WHERE order_id=? AND (supplied IS NOT NULL OR COALESCE(billed_bill_no,'')<>'' "
                    "OR arrived_at IS NOT NULL)", (oid,)).fetchone()[0]
    try:
        tie = con.execute("SELECT 1 FROM order_scan_tie WHERE order_id=?", (oid,)).fetchone() is not None
    except sqlite3.Error:
        tie = False
    oa = con.execute("SELECT created_at FROM purchase_order WHERE id=?", (oid,)).fetchone()
    od = _dtm(oa[0]) if oa else None
    if not n and not tie:
        con.execute("UPDATE purchase_order SET status='draft', sent_by=NULL WHERE id=? AND status='sent'", (oid,))
        con.execute("UPDATE order_sheet_line SET state='in_line', updated_at=? WHERE order_id=? AND state='ordered'", (t, oid))
        con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=?",
                    (("withdrawn: phone could not send (after the unconfirmed hour) — %s" % (err or ""))[:200], mid))
        audit(con, "reception-phone", "s454_whatsapp_unconfirmed_no", oid, dict(supplier=vendor, message=mid, why="the phone could not send",
                                                                                error=(err or "")[:120]))
    else:
        con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=?",
                    (("could not send, but goods already came in on the order -- nothing changed — %s" % (err or ""))[:200], mid))
        audit(con, "reception-phone", "s454_whatsapp_unconfirmed_no_arrived", oid, dict(supplier=vendor, message=mid, error=(err or "")[:120],
                                                                                        order_hm=(od.strftime("%H:%M") if od else "")))


def withdraw_late(con):
    """A message the phone failed, or one NEVER HANDED to it within order.whatsapp_wait_min minutes, is withdrawn from the queue; its
    supplier is pending again with the same order. S605 (F-960): one HANDED and not confirmed within the wait is never withdrawn (it may
    have gone): its order becomes 'sent' by WhatsApp, marked unconfirmed, and the owner reads one line -- nothing is sent again."""
    ensure(con)
    try:
        import supplier_msg                                   # noqa: PLC0415
        supplier_msg.ensure(con)
    except Exception:                                         # noqa: BLE001
        pass
    wait = int_setting(con, "order.whatsapp_wait_min")
    n = 0
    try:
        rows = con.execute("SELECT id, status, queued_at, ref, vendor, handed_at FROM supplier_msg WHERE kind='order' AND status IN ('queued','failed')").fetchall()
    except sqlite3.Error:
        return 0
    for mid, st, qa, ref, vendor, handed in rows:
        d = _dtm(qa)
        if st != "failed" and handed:                         # S613 (F-960): a handed message waits from its hand-out -- never withdrawn by queued_at
            h = _dtm(handed)
            if h and (now() - h) >= dt.timedelta(minutes=wait):
                _s605_unconfirmed(con, mid, ref, vendor, handed, wait)
                n += 1
            continue
        if st == "failed" or (d and (now() - d) >= dt.timedelta(minutes=wait)):
            o = con.execute("SELECT status FROM purchase_order WHERE id=?", (int(ref or 0),)).fetchone()
            cur = con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=? AND " +
                              ("status='failed'" if st == "failed" else "handed_at IS NULL AND status='queued'"),   # S613: never a message handed meanwhile
                              ("withdrawn: %s" % ("the phone could not send" if st == "failed" else "not sent within %d minutes" % wait), mid))
            if cur.rowcount == 1:
                audit(con, "order sheet", "s454_whatsapp_withdrawn", ref, dict(supplier=vendor, message=mid, why=st, order_status=(o[0] if o else None)))
                n += 1
    if n:
        con.commit()
    return n


def _s605_unconfirmed(con, mid, ref, vendor, handed, wait):
    """S605 (F-960): the phone was handed the order and never said done -- the order is sent by WhatsApp (marked unconfirmed by its audit row
    and the message's last_error), its lines ordered; the message is never handed again."""
    oid = int(ref or 0)
    o = con.execute("SELECT status, created_by FROM purchase_order WHERE id=?", (oid,)).fetchone()
    con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=? AND status IN ('queued','failed')",
                ("unconfirmed: handed to the reception phone %s, no done within %d minutes -- not sent again" % (str(handed)[:16].replace("T", " "), wait), mid))
    if o and o[0] == "draft":
        con.execute("UPDATE purchase_order SET status='sent', sent_by=?, order_via='whatsapp' WHERE id=? AND status='draft'",
                    ("%s (WhatsApp, unconfirmed)" % (o[1] or ""), oid))
        con.execute("UPDATE order_sheet_line SET state='ordered', updated_at=? WHERE order_id=? AND state='in_line'", (now_iso(), oid))
    audit(con, "order sheet", "s454_whatsapp_unconfirmed", oid, dict(supplier=vendor, message=int(mid), handed_at=handed, order_status=(o[0] if o else None)))


def _s605_minus(v):
    """-1 -> '−1' (the owner's English line)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    s = ("%d" % f) if f == int(f) else ("%.1f" % f)
    return s.replace("-", "−")


def _s605_owner_lines(con):
    """S605: an orthotic line never offered (its figure is below zero), and an order the phone took but never confirmed (today, yesterday)."""
    out = []
    try:
        _v, _offer, bad = ortho_offer(con)
        for it in bad:
            own = int(it.get("shelf") or 0) < 0
            out.append(dict(cls="warn", target="porders", text="%s — the system's %s is %s (Marg %s): not offered for ordering; the count or a sale needs a look"
                            % (it["item"], "stock figure" if own else "family figure", _s605_minus(it["shelf"] if own else it.get("family_shelf")),
                               _s605_minus(it.get("marg")) if it.get("marg") is not None else "—")))
    except Exception:                                         # noqa: BLE001 -- Needs you never waits on this
        pass
    try:
        since = (now().date() - dt.timedelta(days=1)).isoformat()
        for vendor, handed in con.execute("SELECT vendor, handed_at FROM supplier_msg WHERE kind='order' AND status='skipped' AND last_error LIKE 'unconfirmed:%' "
                                          "AND substr(handed_at,1,10)>=? ORDER BY handed_at, id", (since,)).fetchall():
            h = _dtm(handed)
            at = (h.strftime("%H:%M") if h.date() == now().date() else h.strftime("%d-%m %H:%M")) if h else ""
            out.append(dict(cls="warn", target="porders", text="%s — the reception phone took the order at %s but never confirmed it. It was not sent again. "
                            "Check the reception phone's WhatsApp chat with %s." % (vendor, at, vendor)))
    except Exception:                                         # noqa: BLE001
        pass
    try:                                                      # S613 (F-960): the phone's late no on an order goods already came in on (today)
        for (detail,) in con.execute("SELECT detail FROM purchase_audit WHERE action='s454_whatsapp_unconfirmed_no_arrived' AND substr(at,1,10)=? ORDER BY id",
                                     (now().date().isoformat(),)).fetchall():
            try:
                d = json.loads(detail or "{}")
            except ValueError:
                d = {}
            out.append(dict(cls="warn", target="porders", text="%s — the reception phone said it could not send the order of %s, but goods have already "
                            "come in on it. Nothing was changed." % (d.get("supplier") or "", d.get("order_hm") or "")))
    except Exception:                                         # noqa: BLE001
        pass
    return out


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
                           "dup_of", "bill_month", "lane", "status", "kind", "rescan_of") if c in cols]      # S618: + rescan_of
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
    if not _s619_may_ask(con, o["id"]):                       # S619 (3.3): nothing came, or every line answered with Marg in
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
        if o["status"] == "sent" and not _s619_may_ask(con, o["id"]):
            continue                                          # S619: an order where nothing came never asks
        out.setdefault(o.get("supplier_norm") or pa.supplier_key(o["vendor"]), []).append(o)
    return out


def tie_pass(con, who="tie"):
    """Every untied pharmacy scan, oldest first, against its supplier's orders (the rule in the header). Returns the ties made."""
    ensure(con)
    scans = pharmacy_scans()
    if scans is None:
        return []
    t = today()
    _s618_follow(con, scans, who)                             # S618: a rescan's re-point and its ask closed -- BEFORE the loop (R1-B4)
    sup_of = _resolver(con)
    tied_scans = {r[0] for r in con.execute("SELECT asset_bill_id FROM order_scan_tie")}
    try:                                                      # S711 (F-1120): a scan picked as the copy (S708's "This one is right") ties nothing
        copies = {int(r[0]) for r in con.execute("SELECT drop_id FROM s708_scan_pick WHERE undone_at IS NULL")}
    except sqlite3.Error:
        copies = set()
    ans = answers(con)
    made = []
    state = {}

    def fresh():
        state["waiting"] = awaiting_scan(con, t)
        state["ents"] = {x["sn"]: x for x in entries(con, with_ortho=False)} if source(con) == "marg_sheet" else {}
    fresh()
    for s in scans:
        sid = int(s["id"])
        if sid in tied_scans or sid in copies or s.get("dup_of") or str(s.get("lane") or "pharmacy") != "pharmacy" or not s.get("at"):
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
            if len(cand) >= 2:                                # S619 (3.3): two or more orders waiting -- the reading picks, once it is in
                if not (str(s.get("ocr_status") or "") in ("read", "empty", "failed") or (now() - s["at"]) > dt.timedelta(minutes=10)):
                    continue                                  # (ten minutes at most), else the oldest
                o = _s619_pick(con, cand, s, sn) or o
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
    for name, fn in (("sheets", load_pending), ("heal", heal_marg_cols), ("notices", send_pending_notices), ("withdrawn", withdraw_late),
                     ("refresh", refresh)):                   # S494: notices; S543: Marg's RECEIVE / PENDING healed, fail-soft
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
    try:                                                      # S619 (3.4): a short line goes on its dealer's next order by itself
        out["carry"] = _ot().carry_pass(con, now())
    except Exception as e:                                    # noqa: BLE001
        out["carry"] = "error: %s" % str(e)[:80]
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
    rf = refused_sheet(con, staff=True)                       # S556: a sheet the medical PC's reader stopped on is not his to redo
    out = dict(ok=True, refused=bool(rf), refused_at=(rf or {}).get("at", ""), sheet=None)
    if ns:
        oo = open_order(con)                                  # S543 (R3-12): the figure reception's heading and the printed sheet give
        n = (oo["count"], oo["suppliers"]) if (oo["sheet"] or {}).get("id") == ns["id"] else day_order(con, ns["id"])
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
                                                                 "The reception phone has not asked the server for %s%s" % (
                                                                     _span(int_setting(con, "order.phone_alive_min")),
                                                                     (" -- %d order message(s) wait" % waiting) if waiting else " -- someone met the disabled WhatsApp button"))))
        since = (today() - dt.timedelta(days=7)).isoformat()
        out.extend(_s605_owner_lines(con))                   # S605: the orthotic line never offered; the order the phone never confirmed
        try:                                                  # S619: late orders and medicines short (what the other two voices do not say)
            _ol = _ot().owner_line(con, now())
            if _ol:
                out.append(_ol)
        except Exception:                                     # noqa: BLE001
            pass
        for r in con.execute("SELECT supplier, line_date, COUNT(*) FROM order_sheet_line WHERE state='lapsed' AND lapsed_at>=? GROUP BY supplier_norm, line_date",
                             (since,)):
            out.append(dict(cls="warn", target="porders", text="An order of %s to %s was never placed (%d item%s)" % (dmy(r[1]), r[0], r[2], "" if r[2] == 1 else "s")))
        try:                                                  # S454 P3 (9.3): one line, the count of such items and their names
            import shelf_figure                               # noqa: PLC0415
            gl = shelf_figure.gap_line(con)
            if gl:
                out.append(gl)
        except Exception:                                     # noqa: BLE001
            pass
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



def _span(minutes):
    """S454 P1C: 720 -> '12 hours', 90 -> '90 minutes' (the owner's line)."""
    m = int(minutes or 0)
    if m >= 120 and m % 60 == 0:
        return "%d hours" % (m // 60)
    return "%d minute%s" % (m, "" if m == 1 else "s")


# ------------------------------------------------------------------ S618 (22-Oct-2026): a rescan takes over its old scan (kit S618_SCAN_QUALITY)
S618_DECIDED = ("likely_bill", "confirmed_by", "confirmed_at", "paper_amount", "chosen_vendor", "hint_no", "amount_state", "dup_ok")


def _s618_carry(con, old, new, who):
    """The people's decisions on the old scan COPIED to its rescan (the old rows stay as they are): purchase_scan_state's decided fields,
    s454_scan_answer, and reception's CONFIRMED pairing. A link is one per bill (purchase_scan_link's key is the bill): the copy is made
    once the bill is free -- the matcher lets the set-aside old scan go by itself. Keyed: each copy is written once. True when it wrote."""
    wrote = False
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(purchase_scan_state)")]
        r = con.execute("SELECT * FROM purchase_scan_state WHERE asset_bill_id=?", (old,)).fetchone()
        if r is not None and not con.execute("SELECT 1 FROM purchase_scan_state WHERE asset_bill_id=?", (new,)).fetchone():
            row = dict(zip(cols, r))
            dec = {k: row.get(k) for k in S618_DECIDED if k in cols and row.get(k) not in (None, "")}
            if dec:
                ks = ["asset_bill_id", "why", "detail", "checked_at"] + sorted(dec)
                con.execute("INSERT INTO purchase_scan_state (%s) VALUES (%s)" % (", ".join(ks), ",".join("?" * len(ks))),
                            [new, row.get("why") or "no_bill_yet", "S618: carried from the rescanned scan %d" % old, now_iso()] + [dec[k] for k in sorted(dec)])
                wrote = True
    except sqlite3.Error:
        pass
    try:
        cur = con.execute("INSERT OR IGNORE INTO s454_scan_answer (asset_bill_id, kind, answer, value, by, at) "
                          "SELECT ?, kind, answer, value, by, at FROM s454_scan_answer WHERE asset_bill_id=?", (new, old))
        wrote = wrote or cur.rowcount > 0
        for (bid,) in con.execute("SELECT bill_id FROM purchase_scan_link WHERE asset_bill_id=? AND grade='CONFIRMED'", (old,)).fetchall():
            cur = con.execute("INSERT OR IGNORE INTO s454_scan_answer (asset_bill_id, kind, answer, value, by, at) VALUES (?,?,?,?,?,?)",
                              (new, "pair", "yes", str(bid), "S618 (the pairing of scan %d carried)" % old, now_iso()))
            wrote = wrote or cur.rowcount > 0
        a = con.execute("SELECT value FROM s454_scan_answer WHERE asset_bill_id=? AND kind='pair' AND answer='yes'", (new,)).fetchone()
        if a and str(a[0] or "").isdigit():
            bid = int(a[0])
            if (not con.execute("SELECT 1 FROM purchase_scan_link WHERE bill_id=? OR asset_bill_id=?", (bid, new)).fetchone()
                    and con.execute("SELECT 1 FROM purchase_bill WHERE id=?", (bid,)).fetchone()):
                con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                            (bid, new, "CONFIRMED", "S618: reception's pairing of the rescanned scan %d, carried" % old, now_iso()))
                con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (new, bid))
                audit(con, who, "scan_link", bid, dict(scan=new, grade="CONFIRMED", rule="carried from the rescanned scan %d" % old, kit="S618"))
                wrote = True
    except sqlite3.Error:
        pass
    return wrote


def _s618_follow(con, scans, who="tie"):
    """S618, BEFORE tie_pass's loop (R1-B4). (a) Re-point: each captured pharmacy scan that is a rescan (bills.rescan_of) takes over its old
    scan's order tie -- the tie's asset_bill_id and stamp become the rescan's, scan_at stays (the delivery moment did not change); never a new
    tie (the rescan is untied until this step, so the loop below sees it tied). The people's decisions are copied (_s618_carry).
    (b) Every open ask whose scan has a rescan in assets.db -- any lane, any kind, tie or no tie -- is closed (done_bill_id, done_at).
    Keyed and idempotent; commits what it wrote. Returns (re-pointed, closed)."""
    wrote, rp, cl = False, 0, 0
    for s in scans or []:
        old = s.get("rescan_of")
        if not old:
            continue
        new, old = int(s["id"]), int(old)
        t = con.execute("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", (old,)).fetchone()
        if t and not con.execute("SELECT 1 FROM order_scan_tie WHERE asset_bill_id=?", (new,)).fetchone():
            con.execute("UPDATE order_scan_tie SET asset_bill_id=?, stamp=? WHERE asset_bill_id=?", (new, s.get("stamp_no") or "", old))
            audit(con, who, "s454_scan_retie", t[0], dict(old=old, new=new, stamp=s.get("stamp_no"), kit="S618"))
            rp += 1
            wrote = True
        wrote = _s618_carry(con, old, new, who) or wrote
    pairs = []
    acon = _assets()
    if acon is not None:
        try:
            if "rescan_of" in {r[1] for r in acon.execute("PRAGMA table_info(bills)")}:
                pairs = [(int(r[0]), int(r[1])) for r in acon.execute("SELECT id, rescan_of FROM bills WHERE rescan_of IS NOT NULL ORDER BY id")]
        except sqlite3.Error:
            pairs = []
        finally:
            acon.close()
    for new, old in pairs:
        try:
            for (aid,) in con.execute("SELECT id FROM scan_rescan_ask WHERE asset_bill_id=? AND done_at IS NULL AND withdrawn_at IS NULL", (old,)).fetchall():
                con.execute("UPDATE scan_rescan_ask SET done_bill_id=?, done_at=? WHERE id=? AND done_at IS NULL AND withdrawn_at IS NULL", (new, now_iso(), aid))
                audit(con, who, "s618_rescan_done", aid, dict(old=old, new=new, kit="S618"))
                cl += 1
                wrote = True
        except sqlite3.Error:
            pass
    if wrote:
        con.commit()
    return rp, cl


# ------------------------------------------------------------------ S619 (22-Oct-2026, kit S619_ORDER_TRACKER): the tie's asking, the carry, the reason
#  _s619_may_ask: an order whose every line was tapped 'Nahi mila' never asks for a scan; an order whose every line is answered, Marg having
#  billed one of them, stops asking (order 45). _s619_pick: two or more orders of the dealer waiting -- the reading's best line match among them
#  (order_track.match_lines), else the oldest. _s619_live: a removal 'Dealer ke paas nahi hai' counts while its sheet is Marg's newest (a sheet
#  line) or for its day (any other line); 'Abhi nahi chahiye' as before. The carry's lines: their packing and rate from the order they came from.
def _s619_may_ask(con, oid):
    try:
        ls = con.execute("SELECT billed_qty, billed_bill_no, supplied, missing, arrived_by FROM purchase_order_line WHERE order_id=?", (int(oid),)).fetchall()
    except sqlite3.Error:
        return True
    if not ls:
        return True
    if all(int(l[3] or 0) == 1 and str(l[4] or "") != "marg" for l in ls):
        return False
    if any(l[0] is not None and str(l[1] or "").strip() for l in ls) and all(l[0] is not None or l[2] is not None or int(l[3] or 0) == 1 for l in ls):
        return False
    return True


def _s619_reads(sid):
    """The read item names of one scan (assets.db claude_reading, READ ONLY): [(name, stamp)]."""
    acon = _assets()
    if acon is None:
        return []
    try:
        st = acon.execute("SELECT stamp_no FROM bills WHERE id=?", (int(sid),)).fetchone()
        r = acon.execute("SELECT data FROM claude_reading WHERE bill_id=? AND ok=1 ORDER BY at DESC LIMIT 1", (int(sid),)).fetchone()
    except sqlite3.Error:
        return []
    finally:
        acon.close()
    try:
        d = json.loads(r[0]) if r and r[0] else {}
    except ValueError:
        d = {}
    stamp = (st[0] if st else "") or "#%d" % int(sid)
    return [(str(i.get("name") or ""), stamp) for i in (d.get("items") or []) if isinstance(i, dict) and i.get("name")]


def _s619_pick(con, cand, s, sn):
    """The waiting order whose lines the scan's reading names best (one-to-one, by name, never quantities); None when no line matches."""
    reads = _s619_reads(s["id"])
    if not reads:
        return None
    best, score = None, 0
    for o in cand:
        items = [r[0] for r in con.execute("SELECT item FROM purchase_order_line WHERE order_id=?", (o["id"],))]
        n = len(_ot().match_lines(con, sn, items, reads))
        if n > score:
            best, score = o, n
    return best


def _s619_live(reason, at, src, taken):
    if str(reason or "") != "dealer_no":
        return True
    if src == "sheet":
        return str(at or "") >= str(taken or "")
    return str(at or "")[:10] == today().isoformat()


def _s619_taken(con):
    try:
        r = con.execute("SELECT taken_at FROM order_sheet ORDER BY " + RANK + " LIMIT 1").fetchone()
        return (r[0] or "") if r else ""
    except sqlite3.Error:
        return ""


def _s619_removed(con, ns=None):
    """(removed, dealer_no): the sheet lines (ref, item) a live removal takes off -- and those of them removed as 'Dealer ke paas nahi hai'."""
    taken = (ns or {}).get("taken_at") if ns else _s619_taken(con)
    has = _has_col(con, "s454_line_edit", "reason")
    rem, dn = set(), set()
    for r in con.execute("SELECT ref, item, %s, at FROM s454_line_edit WHERE src='sheet' AND removed=1" % ("reason" if has else "NULL")):
        if _s619_live(r[2], r[3], "sheet", taken):
            rem.add((r[0], r[1]))
            if r[2] == "dealer_no":
                dn.add((r[0], r[1]))
    return rem, dn


def _s619_line(con, cr):
    """(packing, rate_p) of a carried line -- its sheet line's packing and its order line's rate."""
    pk, rate = "", 0
    try:
        r = con.execute("SELECT rate_p FROM purchase_order_line WHERE id=?", (int(cr["from_line_id"]),)).fetchone()
        rate = int((r[0] if r else 0) or 0)
        pk = (sheet_lines_of_order(con, int(cr["from_order_id"])).get(cr["item"]) or {}).get("packing") or ""
    except (sqlite3.Error, TypeError, ValueError):
        pass
    return pk, rate


def _s619_carry_done(con, e, oid):
    """The carried lines of the card now ride on order `oid` (done_order_id): never carried again."""
    ids = [int(l["ref"]) for l in e.get("lines") or [] if l.get("src") == "carry"]
    if not ids:
        return 0
    cur = con.execute("UPDATE order_carry SET done_order_id=?, done_at=? WHERE id IN (%s) AND done_at IS NULL AND dropped_at IS NULL" % ",".join("?" * len(ids)),
                      [int(oid), now_iso()] + ids)
    return cur.rowcount


def _s619_carried(con, oid):
    """{item: 'dd-mm'} of the carried lines an order carries (the WhatsApp body's 'pichhle order se baaki (dd-mm)')."""
    try:
        return {r[0]: ddmm(r[1] or r[2]) for r in con.execute("SELECT c.item, o.created_at, c.at FROM order_carry c LEFT JOIN purchase_order o ON o.id=c.from_order_id "
                                                              "WHERE c.done_order_id=?", (int(oid),))}
    except sqlite3.Error:
        return {}
# ---- S619 end ---------------------------------------------------------------------------------------------------------------------------
