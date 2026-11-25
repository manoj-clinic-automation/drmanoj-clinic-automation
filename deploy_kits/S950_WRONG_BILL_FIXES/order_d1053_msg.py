#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  order_d1053_msg.py  ·  v1.0  ·  kit S940_ORDER_MESSAGES  ·  Session 509 (Sanjeevni)  ·  D1053 (mock-up "Mockup okay" 23-Nov 18:52 IST)
#
#  THE PURCHASE ORDER FLOW, PART 2 -- THE MESSAGES AND HIS FOUR STEPS (order_d1053.py is part 1; it must be beside this file):
#   A  the Marg sheet came in   -> Darpan (आज का ऑर्डर: N पुरानी दवा पर फ़ैसला) and the ordering staff (Order list aa gayi -- Darpan ka
#                                  intezaar). The doctor already has "Darpan's order sheet ✓" (owner_notice) -- not sent twice.
#   B  Darpan made it final     -> the ordering staff (WhatsApp bhejiye) and the doctor (what Darpan added, what went to his word).
#   C  the WhatsApps went       -> the doctor and Darpan (WhatsApp n · call n · failed n, the failed named), once every order message of
#                                  the batch has been answered by the phone.
#   D  each delivery entered    -> Darpan (<dealer> का माल आया -- what came, what did not), by the arrival tap or the bill scan.
#  Each opens its own page. All are made and sent by order_rules' ten-minute tick (the web process cannot push, F-767): a message
#  lands within ten minutes of its moment. The old sheet notice ("Darpan ki order sheet aa gayi") is not sent while the flow is on.
#  His Purchase orders page opens with the day in four steps: sheet in · final · sent · arriving.
#  Switch: order_d1053.live (setting order.d1053). Recipients: settings order.d1053_msg_darpan (darpan), order.d1053_msg_staff
#  (order.notice_to less Darpan), order.d1053_msg_owner (manoj). Table (its own): order_d1053_msg. Every step fail-soft.
#
#  v1.1 · kit S941_ORDER_ADDINS · the owner's "YES FOR ALL" 23-Nov 20:01 IST on the four add-ins of the mock-up:
#   E  LATE        -> Darpan and the staff, once, the morning after an order's due evening (from order.d1053_late_hour, 09).
#   F  NUDGES      -> Darpan when the sheet is not final order.d1053_nudge_final_min (45) after it came; the staff when it is final but
#                     nothing has gone order.d1053_nudge_send_min (30) after; the doctor only if still stuck order.d1053_nudge_owner_min
#                     (30) after the nudge.
#   G  SUMMARY     -> the doctor and Darpan once a day at order.d1053_summary_at (20:00): ordered · arrived · short · late · his word.
#   H  WRONG BILL  -> Darpan and the doctor: a scanned bill tied to an order of the flow names a medicine the order did not carry, or
#                     more of one than ordered (read from the bill scan, one to one by name as order_track.match_lines). The message
#                     opens /finance/porders/d1053/bill/<scan>: each such line Keep / Send back (two taps); a Send back is reception's
#                     line "Wapas bhejna hai" on the order screen until she taps "Wapas kar diya". Table: order_d1053_billq.
#   Every add-in announces nothing from before order.d1053_msg_since. His four steps: step 1 counts Marg's open order (the same
#   numbers as reception's screen); a sheet made final by the install counts today's orders as sent.
#
#  v1.2 · kit S950_WRONG_BILL_FIXES · Sanjeevni session 518 · 25-Nov-2026 · the two repairs he asked for at the S509 close ("fresh chat"):
#   F-1657 THE NAME MATCH -> a bill line is on the order when it carries the ordered Marg item (as before), or when every word of an
#                     ordered line's name (this order, or the same dealer's orders of the last 30 days) is in the bill's name --
#                     "UPRISE D3 6L INJ" carries "UPRISE 6L INJ". Three words at least, two of them not a form word (TAB, INJ ...),
#                     the same first word; never when the bill adds a variant word (PLUS, FORTE, XT, D, MR, SR ...), and for an
#                     orthotic never with a size clash -- a doubt stays his line. Only an ordered line the bill's other lines have not
#                     already taken; one of THIS order goes through the quantity check as before. An open line that the rule, judged
#                     again on its whole bill, no longer finds is cleared by the tick (status 'cleared', by S950) and leaves every list.
#   F-1658 WRONG BILLS WAITING -> on his flow page, each open line (dealer · bill no. · medicine) opening /finance/porders/d1053/bill/<scan>;
#                     the same lines on Darpan's tab (darpan_payload 'wrong', drawn by darpan_kal.html).
#   MESSAGES TODAY  -> on his flow page, read only and folded: each message of the flow made today -- time, what, to whom, sent / failed /
#                     waiting -- from order_d1053_msg (no server line is ever needed to see it).
# =============================================================================
import datetime as dt
import html as _html
import json
import sqlite3
import sys

VERSION = "1.2"
KIT = "S950_WRONG_BILL_FIXES"

DDL = ("CREATE TABLE IF NOT EXISTS order_d1053_msg (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, ref TEXT NOT NULL, to_user TEXT NOT NULL,"
       " title TEXT, body TEXT, url TEXT, made_at TEXT NOT NULL, sent_at TEXT, result TEXT, UNIQUE (kind, ref, to_user))",
       "CREATE TABLE IF NOT EXISTS order_d1053_billq (id INTEGER PRIMARY KEY, scan INTEGER NOT NULL, order_id INTEGER, stamp TEXT, vendor TEXT,"
       " item TEXT NOT NULL, kind TEXT NOT NULL, read_qty TEXT, ordered TEXT, unit TEXT, status TEXT NOT NULL DEFAULT 'open', by TEXT, at TEXT, done_by TEXT,"
       " done_at TEXT, made_at TEXT NOT NULL, UNIQUE (scan, item, kind))",
       "CREATE TABLE IF NOT EXISTS order_d1053_billseen (scan INTEGER PRIMARY KEY, order_id INTEGER, at TEXT NOT NULL, n INTEGER)")


def esc(s):
    return _html.escape(str(s if s is not None else ""), quote=True)


def _d():
    import order_d1053                                         # noqa: PLC0415 -- beside this file
    return order_d1053


def _os():
    import order_sheet                                         # noqa: PLC0415
    return order_sheet


def _ot():
    import order_track                                         # noqa: PLC0415
    return order_track


def _or():
    import order_rules                                         # noqa: PLC0415
    return order_rules


def log(where, e):
    print("S940 %s failed: %r" % (where, e), file=sys.stderr)


def ensure(con):
    for s in DDL:
        con.execute(s)


def _setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return str(r[0]) if r and r[0] is not None else default
    except sqlite3.Error:
        return default


def _list(v):
    return [x.strip().lower() for x in str(v or "").split(",") if x.strip()]


def to_darpan(con):
    return _list(_setting(con, "order.d1053_msg_darpan", "darpan"))


def to_owner(con):
    return _list(_setting(con, "order.d1053_msg_owner", "manoj"))


def to_staff(con):
    v = _setting(con, "order.d1053_msg_staff", "")
    if v.strip():
        return _list(v)
    dp = set(to_darpan(con))
    return [x for x in _list(_setting(con, "order.notice_to", "")) if x not in dp]


URL_DARPAN = "/finance/darpan/kal#order"
URL_STAFF = "/finance/porders/s454/order"
URL_OWNER = "/finance/porders/flow"


def _queue(con, kind, ref, users, title, body, url):
    t = _os().now_iso()
    n = 0
    for u in users:
        n += con.execute("INSERT OR IGNORE INTO order_d1053_msg (kind, ref, to_user, title, body, url, made_at) VALUES (?,?,?,?,?,?,?)",
                         (kind, str(ref), u, title, body, url, t)).rowcount
    return n


def _done(con, kind, ref):
    return con.execute("SELECT 1 FROM order_d1053_msg WHERE kind=? AND ref=? LIMIT 1", (kind, str(ref))).fetchone() is not None


def _since(con):
    """The moment the messages began (the install): nothing before it is announced."""
    return _setting(con, "order.d1053_msg_since", "") or _os().now_iso()


# ------------------------------------------------------------------ the old sheet notice gives way while the flow is on
_W = {"done": False}


def install(OS=None):
    """Rebinds order_sheet._sheet_notice and send_pending_notices (once per process): while the flow is live the sheet's notice is kept
    as 'replaced by D1053' and not pushed (message A replaces it). Otherwise both as before."""
    if _W["done"]:
        return
    OS = OS or _os()
    before_notice, before_send = OS._sheet_notice, OS.send_pending_notices

    def _sheet_notice(con, sid):
        try:
            if _d().live(con):
                n = OS.day_order(con, sid)
                con.execute("UPDATE order_sheet SET notice=? WHERE id=?",
                            (json.dumps(dict(text="Darpan ki order sheet aa gayi: %d supplier, %d dawa." % (n[1], n[0]), replaced="d1053", at=OS.now_iso())), sid))
                con.commit()
                return
        except Exception as e:                                 # noqa: BLE001 -- the notice as before
            log("sheet notice", e)
        return before_notice(con, sid)

    def _send_pending(con):
        try:
            if _d().live(con):
                for sid, raw in con.execute("SELECT id, notice FROM order_sheet WHERE notice LIKE '%\"pending\": true%'").fetchall():
                    try:
                        nt = json.loads(raw)
                    except (TypeError, ValueError):
                        continue
                    nt.update(pending=False, replaced="d1053")
                    con.execute("UPDATE order_sheet SET notice=? WHERE id=?", (json.dumps(nt), sid))
                con.commit()
                return 0
        except Exception as e:                                 # noqa: BLE001
            log("pending notices", e)
        return before_send(con)

    OS._sheet_notice = _sheet_notice
    OS.send_pending_notices = _send_pending
    _W["done"] = True


# ------------------------------------------------------------------ the four producers
def _make_a(con):
    D = _d()
    key, ns = D.sheet_now(con)
    if not ns or _done(con, "A", key) or D.final_row(con, key):
        return 0
    if str(ns.get("taken_at") or "")[:10] != _os().today().isoformat() or str(ns.get("taken_at") or "") < _since(con):
        return 0
    q = D.questions(con)
    n = len(q["old"]) + len(q["raised"])
    nmed, nsup = _os().day_order(con, ns["id"])
    body_d = ("आज की ऑर्डर सूची आ गई — %d पुरानी दवा पर फ़ैसला" % n) if n else "आज की ऑर्डर सूची आ गई — सूची पक्की कीजिए"
    k = _queue(con, "A", key, to_darpan(con), "आज का ऑर्डर", body_d, URL_DARPAN)
    k += _queue(con, "A", key, to_staff(con), "Order karna hai", "Order list aa gayi (%d supplier, %d dawa) — Darpan ke pakka karne ka intezaar" % (nsup, nmed), URL_STAFF)
    return k


def _make_b(con):
    D = _d()
    key, ns = D.sheet_now(con)
    fr = D.final_row(con, key)
    if not ns or not fr or fr.get("by") == "install" or _done(con, "B", key) or str(fr.get("at") or "") < _since(con):
        return 0
    at = D.hm(fr["at"])
    rows = [dict(r) for r in con.execute("SELECT kind, item, answer FROM order_d1053_q WHERE sheet_key=? AND answer IS NOT NULL AND raised_at IS NULL", (key,))]
    added = [r["item"] for r in rows if r["answer"] == "add"]
    nas = [r["item"] for r in con.execute("SELECT item FROM order_d1053_q WHERE sheet_key=? AND answer='na'", (key,))]
    bits = []
    if added:
        bits.append("%s added" % ", ".join(added[:3]) + (" +%d" % (len(added) - 3) if len(added) > 3 else ""))
    if nas:
        bits.append("%s out of stock → your word" % ", ".join(nas[:3]) + (" +%d" % (len(nas) - 3) if len(nas) > 3 else ""))
    k = _queue(con, "B", key, to_staff(con), "Order karna hai", "Order list pakki (%s %s) — WhatsApp bhejiye" % (D.who_name(fr["by"]), at), URL_STAFF)
    k += _queue(con, "B", key, to_owner(con), "Purchase orders", "%s made the sheet final · %s%s" % (D.who_name(fr["by"]), at, (" · " + " · ".join(bits)) if bits else ""),
                URL_OWNER)
    return k


def _batch(con, since):
    """The order messages queued since `since` and the orders made since then (the flow's, not paper)."""
    try:
        msgs = [dict(r) for r in con.execute("SELECT m.status, o.vendor FROM supplier_msg m LEFT JOIN purchase_order o ON o.id=m.ref "
                                              "WHERE m.kind='order' AND m.queued_at>=?", (since,))]
    except sqlite3.Error:
        msgs = []
    orders = [dict(r) for r in con.execute("SELECT id, vendor, order_via FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') "
                                           "AND COALESCE(order_via,'')<>'paper' AND created_at>=?", (since,))]
    return msgs, orders


def _make_c(con):
    D = _d()
    key, ns = D.sheet_now(con)
    fr = D.final_row(con, key)
    if not ns or not fr or fr.get("by") == "install" or _done(con, "C", key):
        return 0
    msgs, orders = _batch(con, fr["at"])
    if not msgs or any(m["status"] == "queued" for m in msgs):
        return 0                                               # no WhatsApp yet, or the phone has not answered every one
    sent = [m for m in msgs if m["status"] == "sent"]
    failed = [m for m in msgs if m["status"] != "sent"]
    calls = [o for o in orders if not str(o.get("order_via") or "").startswith("whatsapp")]
    fn = ", ".join(D.short(m["vendor"]) for m in failed[:3] if m.get("vendor"))
    en = "Orders sent — WhatsApp %d · call %d%s" % (len(sent), len(calls), (" · %d failed (%s) — reception to call" % (len(failed), fn)) if failed else "")
    dv = "ऑर्डर गए — WhatsApp %d · कॉल %d%s" % (len(sent), len(calls), (" · %d नहीं गए (%s) — रिसेप्शन फ़ोन करेगी" % (len(failed), fn)) if failed else "")
    return (_queue(con, "C", key, to_owner(con), "Purchase orders", en, URL_OWNER) +
            _queue(con, "C", key, to_darpan(con), "आज का ऑर्डर", dv, URL_DARPAN))


def _make_d(con):
    """Each order of the flow (the last 7 days) that has arrived since the messages began, once: Darpan hears what came."""
    OS, OT, D = _os(), _ot(), _d()
    since = _since(con)
    t0 = (OS.today() - dt.timedelta(days=7)).isoformat()
    oids = [r[0] for r in con.execute("SELECT id FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') AND COALESCE(order_via,'')<>'paper' "
                                      "AND created_at>=?", (t0,))]
    if not oids:
        return 0
    k = 0
    for s in OT.light_all(con, OS.now(), oids=oids):
        if not s.get("arrived") or _done(con, "D", s["id"]):
            continue
        at = s.get("arrived_at")
        if at is None or at.replace(microsecond=0).isoformat() < since:
            continue
        nl = len(s["lines"])
        missing = [x["item"] for x in s["lines"] if x["state"] in ("short", "part") or (x["state"] == "open" and s.get("tap_at"))]
        how = "बिल स्कैन" if s.get("arrived_how") == "scan" else ("Marg" if s.get("arrived_how") == "marg" else "रिसेप्शन")
        if missing:
            body = "%s का माल आया — %d में से %d · %s नहीं आया" % (D.short(s["vendor"]), nl, nl - len(missing), ", ".join(missing[:3]))
        else:
            body = "%s का माल आया — %d दवा (%s %s)" % (D.short(s["vendor"]), nl, how, at.strftime("%H:%M"))
        k += _queue(con, "D", s["id"], to_darpan(con), "माल आया", body, URL_DARPAN)
    return k


def _send(con):
    """Every message made today and not yet sent, through order_rules._push (portal_push's store)."""
    OR = _or()
    since = (_os().now() - dt.timedelta(hours=24)).replace(microsecond=0).isoformat()
    n = 0
    for r in [dict(x) for x in con.execute("SELECT * FROM order_d1053_msg WHERE sent_at IS NULL AND made_at>=? ORDER BY id", (since,))]:
        payload = dict(kind="order", title=r["title"] or "Purchase orders", body=r["body"] or "", url=r["url"] or "/finance/porders",
                       tag="d1053-%s" % r["kind"], ttl=3600, renotify=True, ts=int(dt.datetime.now().timestamp() * 1000))
        try:
            a, b = OR._push(r["to_user"], payload)
            res = dict(sent=a, failed=b)
        except Exception as e:                                 # noqa: BLE001
            res = dict(sent=0, failed=1, error=type(e).__name__)
        con.execute("UPDATE order_d1053_msg SET sent_at=?, result=? WHERE id=?", (_os().now_iso(), json.dumps(res), r["id"]))
        n += 1
    con.commit()
    return n


def tick(con):
    """order_rules' ten-minute tick: make A-D where due, then send. Fail-soft per step; nothing while the flow is off."""
    out = {}
    try:
        if not _d().live(con):
            return dict(off=True)
        ensure(con)
        _d().ensure(con)
    except Exception as e:                                     # noqa: BLE001
        return dict(error=str(e)[:80])
    for name, fn in (("A", _make_a), ("B", _make_b), ("C", _make_c), ("D", _make_d), ("E", _make_e), ("F", _make_f), ("G", _make_g),
                     ("H", _make_h)):
        try:
            out[name] = fn(con)
            con.commit()
        except Exception as e:                                 # noqa: BLE001
            out[name] = "error: %s" % str(e)[:80]
    try:
        out["sent"] = _send(con)
    except Exception as e:                                     # noqa: BLE001
        out["sent"] = "error: %s" % str(e)[:80]
    return out


# ------------------------------------------------------------------ his page: the day in four steps
def _step(done, n, title, sub):
    return ('<div style="display:flex;gap:10px;align-items:center;padding:4px 0"><div style="width:28px;height:28px;border-radius:14px;background:%s;color:#fff;'
            'font-size:14px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none">%s</div><div><div style="font-size:15px;font-weight:700">%s</div>'
            '<div style="font-size:13px;color:#4a5563">%s</div></div></div>' % ("#2f6b45" if done else "#b8c1cb", "✓" if done else n, esc(title), esc(sub)))


def owner_card(con):
    """The four steps at the top of his Purchase orders page (English). '' while the flow is off."""
    D, OS = _d(), _os()
    if not D.live(con):
        return ""
    key, ns = D.sheet_now(con)
    fr = D.final_row(con, key)
    h = ['<div id="d1053steps" style="max-width:1080px;margin:8px auto 0;padding:0 12px"><div style="background:#fff;border:1px solid #dde3e9;border-radius:14px;'
         'padding:12px 16px;font:15px/1.5 \'Segoe UI\',system-ui,sans-serif;color:#16202a"><div style="font-size:18px;font-weight:700;margin-bottom:4px">Today\'s order · %s</div>'
         % esc(OS.today().strftime("%d-%b"))]
    if ns:
        oo = OS.open_order(con)                               # S941: the same figures as reception's screen (Marg's open order)
        h.append(_step(True, 1, "Marg sheet in · %s" % (oo.get("stamp_text") or D.hm(ns.get("taken_at"))),
                       "%d suppliers · %d medicines" % (int(oo.get("suppliers") or 0), int(oo.get("count") or 0))))
    else:
        h.append(_step(False, 1, "Marg sheet not in yet", "Darpan saves Marg's order as text; it comes in by itself"))
    if fr:
        rows = [dict(r) for r in con.execute("SELECT answer, item FROM order_d1053_q WHERE sheet_key=? AND answer IS NOT NULL", (key,))]
        bits = []
        for a, w in (("add", "added"), ("na", "out of stock → to you"), ("later", "not now"), ("remove", "taken off this time")):
            n = sum(1 for r in rows if r["answer"] == a)
            if n:
                bits.append("%d %s" % (n, w))
        h.append(_step(True, 2, ("Final · %s (%s)" % (D.hm(fr["at"]), "before this flow" if fr.get("by") == "install" else D.who_name(fr["by"]))),
                       ("Old lines: " + ", ".join(bits)) if bits else "No old line to decide"))
    elif ns:
        q = D.questions(con)
        n = q["pending"]
        h.append(_step(False, 2, "Waiting for Darpan to make it final", ("%d decision%s left on his tab" % (n, "" if n == 1 else "s")) if n else "Only his tap is left"))
        h.append('<div style="margin:0 0 4px 38px;font-size:13px"><a href="/finance/darpan/kal#order">Darpan\'s tab — you can decide and make it final there yourself</a></div>')
    else:
        h.append(_step(False, 2, "Final", "after the sheet comes in"))
    since = (OS.today().isoformat() if fr.get("by") == "install" else fr["at"]) if fr else OS.today().isoformat()
    msgs, orders = _batch(con, since) if fr else ([], [])     # S941: a sheet final by the install counts the day's orders
    if orders:
        sent = sum(1 for m in msgs if m["status"] == "sent")
        failed = sum(1 for m in msgs if m["status"] not in ("sent", "queued"))
        queued = sum(1 for m in msgs if m["status"] == "queued")
        calls = sum(1 for o in orders if not str(o.get("order_via") or "").startswith("whatsapp"))
        h.append(_step(queued == 0, 3, "Sent · %d dealer%s" % (len(orders), "" if len(orders) == 1 else "s"),
                       "WhatsApp %d · call %d%s%s" % (sent, calls, (" · %d failed → called" % failed) if failed else "", (" · %d waiting for the phone" % queued) if queued else "")))
        try:
            light = _ot().light_all(con, OS.now(), oids=[o["id"] for o in orders])
        except Exception as e:                                 # noqa: BLE001
            log("owner light", e)
            light = []
        arr = sum(1 for s in light if s.get("arrived"))
        dues = [s["due_at"] for s in light if s.get("due_at")]
        due = max(dues).strftime("%d-%m") if dues else ""
        h.append(_step(bool(light) and arr == len(light), 4, "Arriving%s" % (" · due %s evening" % due if due else ""), "%d of %d arrived yet" % (arr, len(light))))
    else:
        h.append(_step(False, 3, "Sent", "nothing sent yet" if fr else "after the final"))
        h.append(_step(False, 4, "Arriving", ""))
    try:
        S7 = D._s7()
        na = [r for r in S7.na_rows(con, ("asked",))]
        if na:
            h.append('<div style="margin-top:8px;background:#fff6e0;border:2px solid #8a5a00;border-radius:12px;padding:8px 12px;font-size:14px">'
                     '<b>Your word — out of stock (%d):</b> %s · <a href="/finance/porders/s454/abnahi">decide</a> (they never hold the order)</div>'
                     % (len(na), esc(", ".join(r["item"] for r in na[:5]) + (" +%d" % (len(na) - 5) if len(na) > 5 else ""))))
    except Exception as e:                                     # noqa: BLE001
        log("owner na", e)
    for part in (wrong_bills_html, messages_today_html):      # S950: wrong bills waiting · messages today
        try:
            h.append(part(con))
        except Exception as e:                                 # noqa: BLE001 -- the card as before
            log("S950 " + part.__name__, e)
    h.append("</div></div>")
    return "".join(h)


# ------------------------------------------------------------------ S950: wrong bills waiting · messages today (his page, read only)
def open_wrong(con):
    """The open wrong-bill lines, oldest first."""
    ensure(con)
    return [dict(r) for r in con.execute("SELECT * FROM order_d1053_billq WHERE status='open' ORDER BY made_at, id")]


def _what(r, en):
    if r.get("kind") == "extra":
        return "not on the order" if en else "ऑर्डर में नहीं थी"
    return ("%s %s came, %s ordered" % (r.get("read_qty"), _uw(r.get("unit"), True), r.get("ordered"))) if en else \
        ("%s %s आए, %s मंगाए" % (r.get("read_qty"), _uw(r.get("unit"), False), r.get("ordered")))


def wrong_bills_html(con):
    """F-1658: each open line on his page, grouped by bill, opening the bill's page (Keep / Send back there). '' when none."""
    rows = open_wrong(con)
    back = con.execute("SELECT COUNT(*) FROM order_d1053_billq WHERE status='back'").fetchone()[0]
    if not rows and not back:
        return ""
    by = {}
    for r in rows:
        by.setdefault(int(r["scan"]), []).append(r)
    h = ['<div id="d950wrong" style="margin-top:8px;background:#fff6e0;border:2px solid #8a5a00;border-radius:12px;padding:8px 12px;font-size:14px">']
    if rows:
        h.append('<div style="font-weight:700;color:#6b4500;font-size:15px">Wrong bills waiting (%d) — open a bill to Keep or Send back</div>' % len(rows))
        for scan, rs in by.items():
            h.append('<div style="padding:4px 0;border-top:1px solid #eadfc6"><a href="/finance/porders/d1053/bill/%d"><b>%s · bill %s</b></a> — %s</div>'
                     % (scan, esc(short(rs[0].get("vendor") or "")), esc(rs[0].get("stamp") or ""),
                        esc(", ".join("%s (%s)" % (r["item"], _what(r, True)) for r in rs))))
    if back:
        h.append('<div style="padding:4px 0;color:#4a5563">%d line%s with reception to send back to the dealer</div>' % (back, "" if back == 1 else "s"))
    h.append("</div>")
    return "".join(h)


_KIND = {"A": "Sheet in", "B": "Final", "C": "WhatsApps gone", "D": "Delivery", "E": "Late", "F1": "Reminder · not final",
         "F1o": "Reminder to you · not final", "F2": "Reminder · not sent", "F2o": "Reminder to you · not sent", "G": "20:00 summary",
         "H": "Wrong bill"}


def _state(r):
    if not r.get("sent_at"):
        return "waiting", "#8a5a00"
    try:
        j = json.loads(r.get("result") or "{}")
    except (TypeError, ValueError):
        j = {}
    s, f = int(j.get("sent") or 0), int(j.get("failed") or 0)
    if s > 0:
        return ("sent" + (" · %d failed" % f if f else "")), "#2f6b45"
    return "not delivered (that phone needs notifications allowed)", "#a3271f"


def messages_today_html(con):
    """Every message of the flow made today -- time, what, to whom, sent / failed / waiting; folded."""
    ensure(con)
    today = _os().today().isoformat()
    rows = [dict(r) for r in con.execute("SELECT kind, to_user, title, body, made_at, sent_at, result FROM order_d1053_msg WHERE substr(made_at,1,10)=? "
                                          "ORDER BY made_at, id", (today,))]
    if not rows:
        return '<div id="d950msgs" style="margin-top:8px;font-size:13px;color:#4a5563">Messages today: none yet</div>'
    st = [_state(r)[0] for r in rows]
    ns = sum(1 for x in st if x.startswith("sent"))
    nw = sum(1 for x in st if x == "waiting")
    nf = len(rows) - ns - nw
    h = ['<details id="d950msgs" style="margin-top:8px;font-size:14px"><summary style="cursor:pointer"><b>Messages today (%d)</b> · sent %d%s%s</summary>'
         % (len(rows), ns, (" · <b style=\"color:#a3271f\">not delivered %d</b>" % nf) if nf else "", (" · waiting %d" % nw) if nw else ""),
         '<table style="border-collapse:collapse;margin-top:4px;font-size:13px">']
    for r in rows:
        s, col = _state(r)
        h.append('<tr><td style="padding:3px 10px 3px 0">%s</td><td style="padding:3px 10px 3px 0">%s</td><td style="padding:3px 10px 3px 0">%s</td>'
                 '<td style="padding:3px 0;color:%s">%s</td></tr>'
                 % (esc(_d().hm(r.get("sent_at") or r.get("made_at"))), esc(_KIND.get(r["kind"], r["kind"])), esc(_d().who_name(r["to_user"])), col, esc(s)))
    h.append("</table></details>")
    return "".join(h)


def darpan_wrong(con):
    """S950 (F-1658): the open wrong-bill lines for Darpan's tab -- [dict(item, vendor, stamp, what, url)]."""
    return [dict(item=r["item"], vendor=short(r.get("vendor") or ""), stamp=r.get("stamp") or "", what=_what(r, False),
                 url="/finance/porders/d1053/bill/%d" % int(r["scan"])) for r in open_wrong(con)]



# ==========================================================================================================================================
# S941 -- the four add-ins (E late · F nudges · G 20:00 summary · H wrong bill)
# ==========================================================================================================================================
def _int_setting(con, key, default):
    try:
        return int(float(_setting(con, key, str(default))))
    except (TypeError, ValueError):
        return default


def _hhmm_setting(con, key, default):
    v = _setting(con, key, default).strip()
    try:
        h, m = v.split(":", 1)
        return int(h), int(m)
    except (TypeError, ValueError):
        h, m = default.split(":", 1)
        return int(h), int(m)


def _iso(d):
    return d.replace(microsecond=0).isoformat() if d is not None else ""


def _flow_orders(con, days=14):
    OS = _os()
    t0 = (OS.today() - dt.timedelta(days=days)).isoformat()
    return [r[0] for r in con.execute("SELECT id FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') AND COALESCE(order_via,'')<>'paper' "
                                      "AND created_at>=?", (t0,))]


def _make_e(con):
    """E: an order of the flow late past its due evening -- once, from order.d1053_late_hour the next morning; only orders due after the
    messages began."""
    OS, OT, D = _os(), _ot(), _d()
    now = OS.now()
    if now.hour < _int_setting(con, "order.d1053_late_hour", 9):
        return 0
    oids = _flow_orders(con)
    if not oids:
        return 0
    since = _since(con)
    k = 0
    for s in OT.light_all(con, now, oids=oids):
        due = s.get("due_at")
        if not s.get("late") or due is None or _iso(due) < since or due.date() >= now.date() or _done(con, "E", s["id"]):
            continue
        miss = [x["item"] for x in s["lines"] if x["state"] in ("open", "part")]
        days = (now.date() - due.date()).days + 1
        who = D.short(s["vendor"])
        names = ", ".join(miss[:3]) + (" +%d" % (len(miss) - 3) if len(miss) > 3 else "")
        k += _queue(con, "E", s["id"], to_darpan(con), "माल लेट", "%s का माल %s शाम तक आना था — नहीं आया (%s). रिसेप्शन फ़ोन करे" % (who, due.strftime("%d-%m"), names),
                    URL_DARPAN)
        k += _queue(con, "E", s["id"], to_staff(con), "Maal late", "%s ka maal %s shaam tak aana tha — nahi aaya (%s). Call kijiye" % (who, due.strftime("%d-%m"), names),
                    "/finance/porders/s454/late")
        _ = days
    return k


def _make_f(con):
    """F: the nudges -- the sheet not final, or final and nothing sent; the doctor only if still stuck after the nudge."""
    OS, D = _os(), _d()
    now = OS.now()
    key, ns = D.sheet_now(con)
    if not ns or str(ns.get("taken_at") or "")[:10] != OS.today().isoformat() or str(ns.get("taken_at") or "") < _since(con):
        return 0
    fr = D.final_row(con, key)
    k = 0
    if not fr:
        t0 = OS._dtm(ns.get("taken_at"))
        if t0 is None:
            return 0
        if (now - t0).total_seconds() / 60.0 >= _int_setting(con, "order.d1053_nudge_final_min", 45):
            q = D.questions(con)
            n = q["pending"]
            k += _queue(con, "F1", key, to_darpan(con), "आज का ऑर्डर",
                        ("ऑर्डर सूची अभी पक्की नहीं हुई — %d फ़ैसले बाकी. रिसेप्शन इंतज़ार कर रही है" % n) if n else "ऑर्डर सूची अभी पक्की नहीं हुई — सिर्फ़ 'सूची पक्की करो' दबाना बाकी",
                        URL_DARPAN)
        r = con.execute("SELECT MIN(sent_at) FROM order_d1053_msg WHERE kind='F1' AND ref=? AND sent_at IS NOT NULL", (key,)).fetchone()
        t1 = OS._dtm(r[0]) if r and r[0] else None
        if t1 is not None and (now - t1).total_seconds() / 60.0 >= _int_setting(con, "order.d1053_nudge_owner_min", 30):
            k += _queue(con, "F1o", key, to_owner(con), "Purchase orders",
                        "The order sheet is still not final — Darpan was reminded at %s. You can decide and make it final on his tab." % t1.strftime("%H:%M"),
                        "/finance/darpan/kal#order")
        return k
    if fr.get("by") == "install":
        return 0
    tf = OS._dtm(fr["at"])
    if tf is None:
        return 0
    msgs, orders = _batch(con, fr["at"])
    try:
        pend = [e for e in OS.entries(con) if e.get("state") == "pending" and e.get("lines")]
    except Exception as e:                                     # noqa: BLE001
        log("F entries", e)
        pend = []
    if msgs or not pend:
        return 0                                               # WhatsApp went (or nothing is left to order)
    if (now - tf).total_seconds() / 60.0 >= _int_setting(con, "order.d1053_nudge_send_min", 30):
        k += _queue(con, "F2", key, to_staff(con), "Order karna hai",
                    "Order list pakki hai (%s) — %d supplier ko abhi order nahi gaya. WhatsApp sab ko dabaiye" % (fr["at"][11:16], len(pend)), URL_STAFF)
    r = con.execute("SELECT MIN(sent_at) FROM order_d1053_msg WHERE kind='F2' AND ref=? AND sent_at IS NOT NULL", (key,)).fetchone()
    t2 = OS._dtm(r[0]) if r and r[0] else None
    if t2 is not None and (now - t2).total_seconds() / 60.0 >= _int_setting(con, "order.d1053_nudge_owner_min", 30):
        k += _queue(con, "F2o", key, to_owner(con), "Purchase orders",
                    "The final list has not gone to the dealers — %d still to order; reception was reminded at %s." % (len(pend), t2.strftime("%H:%M")),
                    URL_STAFF)
    return k


def day_figures(con):
    """(ordered, arrived, short, late, word) of today -- G's figures."""
    OS, OT, S7 = _os(), _ot(), _d()._s7()
    now = OS.now()
    today = OS.today().isoformat()
    ordered = con.execute("SELECT COUNT(*) FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') AND COALESCE(order_via,'')<>'paper' "
                          "AND substr(created_at,1,10)=?", (today,)).fetchone()[0]
    arrived = short = late = 0
    oids = _flow_orders(con)
    if oids:
        for s in OT.light_all(con, now, oids=oids):
            at = s.get("arrived_at")
            if s.get("arrived") and at is not None and at.date().isoformat() == today:
                arrived += 1
                if any(x["state"] in ("short", "part") for x in s["lines"]):
                    short += 1
            if s.get("late"):
                late += 1
    word = len(S7.na_rows(con, ("asked",)))
    return int(ordered or 0), arrived, short, late, word


def _make_g(con):
    """G: one summary a day at order.d1053_summary_at -- the doctor and Darpan."""
    OS = _os()
    now = OS.now()
    h, m = _hhmm_setting(con, "order.d1053_summary_at", "20:00")
    if (now.hour, now.minute) < (h, m) or _done(con, "G", OS.today().isoformat()):
        return 0
    o, a, sh, lt, w = day_figures(con)
    k = _queue(con, "G", OS.today().isoformat(), to_owner(con), "Purchase orders",
               "Today: %d ordered · %d arrived · %d short · %d late · %d for your word" % (o, a, sh, lt, w), URL_OWNER)
    k += _queue(con, "G", OS.today().isoformat(), to_darpan(con), "आज का ऑर्डर",
                "आज: %d ऑर्डर · %d आए · %d कम आए · %d लेट · %d डॉक्टर साहब के फ़ैसले पर" % (o, a, sh, lt, w), URL_DARPAN)
    return k


def _reading(scan):
    """[(name, qty)] of one scan's latest good reading (assets.db, READ ONLY); None when there is no good reading (or no assets db) --
    judged again later; [] when a good reading names no line (judged: nothing to say)."""
    acon = _os()._assets()
    if acon is None:
        return None
    try:
        r = acon.execute("SELECT data FROM claude_reading WHERE bill_id=? AND ok=1 ORDER BY at DESC LIMIT 1", (int(scan),)).fetchone()
    except sqlite3.Error:
        r = None
    finally:
        acon.close()
    if not r:
        return None
    try:
        d = json.loads(r[0]) if r[0] else {}
    except (TypeError, ValueError):
        d = {}
    out = []
    for i in d.get("items") or []:
        nm = (i.get("name") or i.get("item")) if isinstance(i, dict) else None
        if nm:
            out.append((str(nm), i.get("qty")))
    return out


# S950 (F-1657): the words of a name -- letters and digits, upper case ("UPRISE-D3 6L INJ." -> UPRISE D3 6L INJ)
def _toks(s):
    import re                                                  # noqa: PLC0415
    return re.findall(r"[A-Z0-9]+", str(s or "").upper())


_FORM = {"TAB", "TABS", "TABLET", "TABLETS", "CAP", "CAPS", "CAPSULE", "INJ", "INJECTION", "SYP", "SYRUP", "SUSP", "GEL", "CREAM", "OINT",
         "OINTMENT", "DROP", "DROPS", "SOL", "LOTION", "SPRAY", "POWDER", "SACHET", "VIAL", "AMP", "KIT", "LIQ", "LIQUID"}
_VARIANT = {"TH4", "TH8", "K27", "K2"}          # variant words with a digit; any added word of letters only (PLUS, FORTE, XT, D, TH ...) refuses too


def _added_refuses(added):
    """S950: a word the bill adds that makes it another medicine -- letters only and not a form word, a strength or size starting with a
    digit (60K, 10ML, 500), or a known variant with a digit. A letter-first digit word (D3) may be added."""
    return any((w.isalpha() and w not in _FORM) or w[:1].isdigit() or w in _VARIANT for w in added)


def token_on_order(con, bill_name, ordered):
    """S950 (F-1657): the ordered item whose every word is in the bill's name, else None -- three words at least and two of them not a
    form word, the same first word, no word of letters or digit-first word added by the bill (a letter-first word like D3 may be added), and an orthotic never
    with a size clash. The first wins."""
    bt = _toks(bill_name)
    if not bt:
        return None
    bs = set(bt)
    ortho = None
    for it in ordered:
        ot = _toks(it)
        os_ = set(ot)
        if len(ot) < 3 or len(os_ - _FORM) < 2 or ot[0] != bt[0] or not os_ <= bs or _added_refuses(bs - os_):
            continue
        try:
            if ortho is None:
                ortho = _ot()._s825_ortho(con)
            if _os()._pa().norm(it) in ortho and _ot().size_clash(it, bill_name, True):
                continue
        except Exception as e:                                 # noqa: BLE001 -- no orthotic test: the words decide
            log("S950 ortho", e)
        return it
    return None


def rejudge_open(con):
    """S950: each open 'not on the order' line's bill is judged again (judge_bill, with the word rule); a line it no longer names is
    cleared (by S950) -- it leaves his page, Darpan's tab and the bill page's buttons. Returns how many were cleared."""
    ensure(con)
    k = 0
    t = _os().now_iso()
    rows = [dict(x) for x in con.execute("SELECT id, item, order_id, scan, stamp, made_at FROM order_d1053_billq WHERE status='open' AND kind='extra'")]
    seen = {}
    for r in rows:
        if not r.get("order_id") or not con.execute("SELECT 1 FROM purchase_order WHERE id=?", (int(r["order_id"]),)).fetchone():
            continue                                           # no order to judge against: stays his line
        key = (int(r["scan"]), int(r["order_id"]))
        if key not in seen:
            reads = _reading(r["scan"])
            if not reads:
                seen[key] = None                               # not read now, or read with no lines: stays his line
            else:
                tie = con.execute("SELECT MIN(tied_at) FROM order_scan_tie WHERE asset_bill_id=? AND order_id=?", (int(r["scan"]), int(r["order_id"]))).fetchone()
                until = (tie[0] if tie and tie[0] else "") or r.get("made_at") or ""
                seen[key] = judge_bill(con, r["order_id"], r["scan"], r.get("stamp") or "", until=until)   # the whole bill, orders up to the tie
        got = seen[key]
        if got is None or any(g[0] == r["item"] for g in got):
            continue                                           # still not on the order: stays his line
        if any(g[1] == "more" for g in got):
            continue                                           # the bill came more than ordered somewhere: every line of it stays his
        con.execute("UPDATE order_d1053_billq SET status='cleared', by='S950', at=? WHERE id=? AND status='open'", (t, r["id"]))
        _os().audit(con, "S950", "d1053_bill_cleared", r["id"], dict(item=r["item"], scan=r["scan"], kit=KIT))
        k += 1
    return k


def judge_bill(con, oid, scan, stamp="", until=None):
    """S950: `until` (an ISO time) keeps the dealer's other orders to those made by then (a later order never excuses an old bill).
    The lines of a scan tied to an order of the flow that the order did not carry, or carried less of: [(item, kind, read, ordered)].
    One to one by name (order_track.match_lines); a quantity is compared only when the bill reads a number and the order carries packs."""
    OT = _ot()
    reads = _reading(scan)
    if reads is None:
        return None                                            # not read (yet): judged later
    if not reads:
        return []                                              # a good reading with no lines: nothing to say
    o = con.execute("SELECT vendor, supplier_norm FROM purchase_order WHERE id=?", (int(oid),)).fetchone()
    if not o:
        return []
    sn = o[1] or _os()._pa().supplier_key(o[0])
    lines = [dict(r) for r in con.execute("SELECT item, packs, pack_size FROM purchase_order_line WHERE order_id=?", (int(oid),))]
    rd = [(n, stamp) for n, _q in reads]
    m = OT.match_lines(con, sn, [l["item"] for l in lines], rd)
    used = {}
    for it, (rn, _st) in m.items():
        used[rn] = it
    # a medicine of the dealer's OTHER orders of the last 30 days (an old line delivered now) is not 'not ordered'
    t0 = (_os().today() - dt.timedelta(days=30)).isoformat()
    other = sorted({r[0] for r in con.execute("SELECT l.item FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE o.supplier_norm=? "
                                               "AND o.id<>? AND o.created_at>=? AND o.created_at<=?", (sn, int(oid), t0, until or "9999"))})
    known = set()
    if other:
        for it, (rn, _st) in OT.match_lines(con, sn, other, rd).items():
            known.add(rn)                                      # also on another order of the dealer: never 'extra', never 'more'

    # S950 (F-1657): a bill name that carries every word of an ordered line's name is on the order too -- never 'extra'. Only an
    # ordered line the bill's other lines have not taken; one of THIS order then goes through the quantity check below.
    mine = [l["item"] for l in lines]
    for n, _q in reads:
        if n in used or n in known:
            continue
        taken = set(used.values())
        it = token_on_order(con, n, [x for x in mine if x not in taken])
        if it is not None:
            used[n] = it
            continue
        if token_on_order(con, n, [x for x in other if x not in mine]) is not None:
            known.add(n)

    out = []
    for n, q in reads:
        it = used.get(n)
        if it is None or n in known:
            if it is None and n not in known:
                try:
                    rq = "" if q is None else ("%g" % float(q))
                except (TypeError, ValueError):
                    rq = str(q)
                out.append((n, "extra", rq, "", ""))
            continue
        ol = next((l for l in lines if l["item"] == it), {})
        packs, ps = int(ol.get("packs") or 0), int(ol.get("pack_size") or 1)
        try:
            qq = float(q)
        except (TypeError, ValueError):
            qq = None
        # a bill may print tablets where the order counts strips: a reading that is a whole multiple of the strip size up to the
        # order's own tablets is not 'more' -- only a reading above the ordered strips and below one strip's worth of them is
        if qq is not None and packs > 0 and qq > packs and (ps <= 1 or qq < packs * ps) and not (ps > 1 and qq % ps == 0 and qq <= packs * ps):
            out.append((it, "more", "%g" % qq, str(packs), "strip" if ps > 1 else "pc"))
    return out


def _make_h(con):
    """H: each scan tied to an order of the flow after the messages began is judged once its reading is in; a bill with a line not ordered
    or more than ordered becomes his and Darpan's message, opening the bill's page."""
    OS, D = _os(), _d()
    since = _since(con)
    k = 0
    try:
        rejudge_open(con)                                      # S950: an open line the word rule now matches leaves the lists
    except Exception as e:                                     # noqa: BLE001 -- judged again next tick
        log("S950 rejudge", e)
    rows = [dict(r) for r in con.execute("SELECT t.order_id, t.asset_bill_id, t.stamp, o.vendor FROM order_scan_tie t JOIN purchase_order o ON o.id=t.order_id "
                                          "WHERE t.tied_at>=? AND o.order_src='s454' AND t.asset_bill_id NOT IN (SELECT scan FROM order_d1053_billseen)", (since,))]
    t = OS.now_iso()
    for r in rows:
        try:
            got = judge_bill(con, r["order_id"], r["asset_bill_id"], r["stamp"] or "")
        except Exception as e:                                 # noqa: BLE001 -- judged again next tick
            log("H judge", e)
            continue
        if got is None:
            continue
        con.execute("INSERT OR IGNORE INTO order_d1053_billseen (scan, order_id, at, n) VALUES (?,?,?,?)", (r["asset_bill_id"], r["order_id"], t, len(got)))
        for item, kind, rq, od, un in got:
            con.execute("INSERT OR IGNORE INTO order_d1053_billq (scan, order_id, stamp, vendor, item, kind, read_qty, ordered, unit, made_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (r["asset_bill_id"], r["order_id"], r["stamp"], r["vendor"], item, kind, rq, od, un, t))
        if got:
            who = D.short(r["vendor"])
            names = ", ".join(("%s (%s)" % (i, "not ordered" if kd == "extra" else "%s %s came, %s ordered" % (rq, _uw(un, True), od))) for i, kd, rq, od, un in got[:3])
            dnames = ", ".join(("%s (%s)" % (i, "मंगाई नहीं थी" if kd == "extra" else "%s %s आए, %s मंगाए" % (rq, _uw(un, False), od))) for i, kd, rq, od, un in got[:3])
            url = "/finance/porders/d1053/bill/%d" % int(r["asset_bill_id"])
            k += _queue(con, "H", r["asset_bill_id"], to_owner(con), "Wrong bill", "%s's bill %s: %s — keep or send back" % (who, r["stamp"] or "", names), url)
            k += _queue(con, "H", r["asset_bill_id"], to_darpan(con), "गलत बिल", "%s का बिल %s: %s — रखें या वापस" % (who, r["stamp"] or "", dnames), url)
    return k


# ------------------------------------------------------------------ H's page and reception's returns
def bill_lines(con, scan):
    ensure(con)
    return [dict(r) for r in con.execute("SELECT * FROM order_d1053_billq WHERE scan=? ORDER BY id", (int(scan),))]


def bill_answer(con, who, qid, act):
    """keep | back (Darpan or the doctor) · returned (reception, a 'back' line)."""
    ensure(con)
    r = con.execute("SELECT * FROM order_d1053_billq WHERE id=?", (int(qid),)).fetchone()
    if not r:
        return dict(ok=False, error="gone"), 404
    r = dict(r)
    t = _os().now_iso()
    if act in ("keep", "back"):
        if r["status"] != "open":
            return dict(ok=True, already=True), 200
        con.execute("UPDATE order_d1053_billq SET status=?, by=?, at=? WHERE id=?", ("kept" if act == "keep" else "back", who, t, r["id"]))
    elif act == "returned":
        if r["status"] != "back":
            return dict(ok=False, error="not_back", message="Yeh line wapas bhejni nahi hai."), 409
        con.execute("UPDATE order_d1053_billq SET status='returned', done_by=?, done_at=? WHERE id=?", (who, t, r["id"]))
    else:
        return dict(ok=False, error="bad_act"), 400
    _os().audit(con, who, "d1053_bill_" + act, r["id"], dict(item=r["item"], scan=r["scan"], kit=KIT))
    con.commit()
    return dict(ok=True, item=r["item"], act=act), 200


def returns_open(con):
    ensure(con)
    return [dict(r) for r in con.execute("SELECT * FROM order_d1053_billq WHERE status='back' ORDER BY at")]


_TWO_JS = """<script>
function d941(b,body){if(b.dataset.busy)return;if(!b.classList.contains('arm')){b.dataset.t=b.dataset.t||b.textContent;b.classList.add('arm');
b.textContent=b.dataset.t+' %s';setTimeout(function(){if(b.classList.contains('arm')){b.classList.remove('arm');b.textContent=b.dataset.t;}},4000);return;}
b.classList.remove('arm');b.dataset.busy='1';b.textContent='…';
fetch('/finance/porders/api/d1053/bill',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
.then(function(r){return r.json();}).then(function(j){if(j&&j.ok){location.reload();}else{delete b.dataset.busy;b.textContent=b.dataset.t+' — '+((j&&(j.message||j.error))||'?');}})
.catch(function(){delete b.dataset.busy;b.textContent=b.dataset.t+' — ?';});}
</script><style>.d941{min-height:44px;padding:0 12px;border-radius:8px;border:1px solid #b8c1cb;background:#fff;font:inherit;font-size:14px;margin:6px 6px 0 0;cursor:pointer}
.d941.arm{background:#fff3d6;border-color:#e3a008;color:#6b4500}.d941l{background:#fff;border-radius:10px;padding:10px;margin:8px 0;border:1px solid #e4e0da}</style>"""


def bill_page_body(con, scan, en):
    """The bill's page: its scan, each line not ordered / more than ordered with Keep / Send back (two taps)."""
    rows = bill_lines(con, scan)
    js = _TWO_JS % ("— tap again" if en else "— दोबारा दबाइए")
    if not rows:
        return js + '<div class="mut">%s</div>' % esc("Nothing to decide on this bill." if en else "इस बिल पर कुछ तय करना नहीं है।")
    r0 = rows[0]
    h = [js, '<div style="font-size:18px;font-weight:700">%s · %s</div>' % (esc(r0["vendor"] or ""), esc(r0["stamp"] or "")),
         '<div><a href="/scanapp/bills/%d/file" target="_blank" rel="noopener"><img loading="lazy" src="/scanapp/bills/%d/thumb" alt="" style="max-width:240px;border-radius:6px"></a>'
         ' <a href="/scanapp/bills/%d/file" target="_blank" rel="noopener">%s</a></div>' % (int(scan), int(scan), int(scan), esc("open full size" if en else "पूरा बिल खोलें"))]
    for r in rows:
        what = ("not on the order" if en else "ऑर्डर में नहीं थी") if r["kind"] == "extra" else \
               (("%s %s came, %s ordered" % (r["read_qty"], _uw(r.get("unit"), True), r["ordered"])) if en else
                ("%s %s आए, %s मंगाए" % (r["read_qty"], _uw(r.get("unit"), False), r["ordered"])))
        st = {"kept": ("Kept" if en else "रख ली"), "back": ("Send back — with reception" if en else "वापस — रिसेप्शन के पास"),
              "returned": ("Sent back" if en else "वापस गई"),
              "cleared": ("On the order — matched by name" if en else "ऑर्डर में थी — नाम से मिली")}.get(r["status"], "")
        h.append('<div class="d941l"><b>%s</b> <span class="mut">%s</span>%s' % (esc(r["item"]), esc(what), (' · <b>%s</b>' % esc(st)) if st else ""))
        if r["status"] == "open":
            for act, w in (("keep", "Keep" if en else "रख लो"), ("back", "Send back" if en else "वापस भेजो")):
                h.append("<button class=\"d941\" onclick='d941(this,%s)'>%s</button>" % (esc(json.dumps(dict(id=r["id"], act=act))), esc(w)))
        h.append("</div>")
    return "".join(h)


def returns_html(con, en):
    """Reception's line on the order screen: each 'send back' until she taps Wapas kar diya."""
    rows = returns_open(con)
    if not rows:
        return ""
    h = [_TWO_JS % ("— dobara dabaiye" if not en else "— tap again"),
         '<div id="d941back" style="background:#fff6e0;border:2px solid #8a5a00;border-radius:14px;padding:10px 12px;margin:8px 0">'
         '<div style="font-weight:700;color:#6b4500">%s</div>' % esc("To send back to the dealer" if en else "Wapas bhejna hai")]
    for r in rows:
        h.append('<div style="padding:6px 0;border-top:1px solid #eee"><b>%s</b> — %s · %s<br>' % (esc(r["item"]), esc(short(r["vendor"])), esc(r["stamp"] or "")))
        h.append("<button class=\"d941\" onclick='d941(this,%s)'>%s</button></div>" % (esc(json.dumps(dict(id=r["id"], act="returned"))),
                                                                                    esc("Sent back" if en else "Wapas kar diya")))
    h.append("</div>")
    return "".join(h)


def short(v):
    return _d().short(v)


def _uw(unit, en):
    """The unit word of a bill quantity: strips / pieces (the doctor), पत्ते / नग (Darpan)."""
    if unit == "strip":
        return "strips" if en else "पत्ते"
    return "pieces" if en else "नग"
