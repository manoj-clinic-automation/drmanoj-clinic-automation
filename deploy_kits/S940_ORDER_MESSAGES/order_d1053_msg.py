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
# =============================================================================
import datetime as dt
import html as _html
import json
import sqlite3
import sys

VERSION = "1.0"
KIT = "S940_ORDER_MESSAGES"

DDL = ("CREATE TABLE IF NOT EXISTS order_d1053_msg (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, ref TEXT NOT NULL, to_user TEXT NOT NULL,"
       " title TEXT, body TEXT, url TEXT, made_at TEXT NOT NULL, sent_at TEXT, result TEXT, UNIQUE (kind, ref, to_user))",)


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
    today = _os().today().isoformat()
    n = 0
    for r in [dict(x) for x in con.execute("SELECT * FROM order_d1053_msg WHERE sent_at IS NULL AND substr(made_at,1,10)=? ORDER BY id", (today,))]:
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
    for name, fn in (("A", _make_a), ("B", _make_b), ("C", _make_c), ("D", _make_d)):
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
        nmed, nsup = OS.day_order(con, ns["id"])
        oo = OS.open_order(con)
        h.append(_step(True, 1, "Marg sheet in · %s" % (oo.get("stamp_text") or D.hm(ns.get("taken_at"))), "%d suppliers · %d medicines" % (nsup, nmed)))
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
    since = fr["at"] if fr else OS.today().isoformat()
    msgs, orders = _batch(con, since) if fr else ([], [])
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
    h.append("</div></div>")
    return "".join(h)
