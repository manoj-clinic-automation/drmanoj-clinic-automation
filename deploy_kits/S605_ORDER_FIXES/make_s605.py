#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s605.py -- kit S605_ORDER_FIXES: the builder. Anchored edits on the LIVE bytes of eight finance files, the clone's duty map and the
two kit-held walks of S603 / S598 (F-957); no file re-typed.

    python3 -B make_s605.py --finance /root/finance --repo /root/deploy/repo --out DIR

Every file is pinned (FROM md5, the brief's section 1); every anchor must occur exactly once in the text it edits, else STOP (exit 2,
nothing written). Writes into DIR: order_sheet.py, porders_s454.py, supplier_msg.py, order_sheet_pdf.py, marg_order_pdf.py, darpan_kal.py,
darpan_kal.html, spine/spine_build.py, DUTY_MAP.json, DUTY_MAP.md, walk_s603.py, walk_s598.py -- and prints each md5 (the installer
compares them with PINS.sh). The brief: claude_code_briefs/S605_ORDER_FIXES.md (v1, 20-Oct-2026, Sanjeevni session 334).
D749 / F-959: the orthotic list rides on the order only after Darpan's yes. F-960 (F-702): a message is handed to the phone once.
F-961: 'Sab ko WhatsApp bhejo' asks once. F-962: the home keeps a call row. The numbers: Call / WhatsApp on the cards and both PDFs.
F-951: a size of a shared key keeps its own key in the spine. F-957: the two walks lay their own days."""
import argparse
import hashlib
import json
import os
import re
import sys

FROM = {
    "order_sheet.py": "1f1e85c12c64521b50a10cea48220170",
    "porders_s454.py": "40f1755a7655deb733765456b9a466fe",
    "supplier_msg.py": "6366ed0f75e0496fcd5ea98866dbddbd",
    "order_sheet_pdf.py": "7fca11db1c016ec86a0c57c5020a7079",
    "marg_order_pdf.py": "c9cd44a55d4cb39247d3c2e8e2602f1d",
    "darpan_kal.py": "b28d7342469814e85129602ea35a7423",
    "darpan_kal.html": "7c9391912cf62972a8d9e3a41e9e2ebb",
    "spine/spine_build.py": "e3d3ed85973eab2df0326dc9621e230e",
    "DUTY_MAP.json": "b75ea78ea5c65005d2a6420960bad19c",
}

# ======================================================================================================================= order_sheet.py
OSE = []
OSE.append(("O1 the module header", '''#  NO phone number, token or patient detail is printed by this file; a phone number goes only into a page a sender opens to call,
#  or into the reception phone's message.
# =============================================================================
''', '''#  NO phone number, token or patient detail is printed by this file; a phone number goes only into a page a sender opens to call,
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
# =============================================================================
'''))
OSE.append(("O2 the hand-out setting's note", '''    "supplier_msg.handout_gap_min": ("10", "S454 (F-702): a message handed to the phone is not handed out again within this many minutes"),
''', '''    "supplier_msg.handout_gap_min": ("10", "S454 (F-702); S605 (F-960): only the owner's test message is handed to the phone again, after this "
                                           "many minutes -- every other message is handed once"),
'''))
OSE.append(("O3 the table of Darpan's answers", '''    "CREATE TABLE IF NOT EXISTS s454_paper_missing (bill_id INTEGER PRIMARY KEY, by TEXT, at TEXT NOT NULL, accepted_by TEXT, accepted_at TEXT)",
)
''', '''    "CREATE TABLE IF NOT EXISTS s454_paper_missing (bill_id INTEGER PRIMARY KEY, by TEXT, at TEXT NOT NULL, accepted_by TEXT, accepted_at TEXT)",
    "CREATE TABLE IF NOT EXISTS ortho_yes (id INTEGER PRIMARY KEY, tap INTEGER NOT NULL, at TEXT NOT NULL, by TEXT, answer TEXT NOT NULL "
    "CHECK (answer IN ('yes','no','remove')), item TEXT NOT NULL, qty INTEGER, short_at_answer INTEGER)",      # S605 (D749): never updated, never deleted
)
'''))
OSE.append(("O4 the offer, the kept lines, the answer (after _ortho_short)", '''def _ortho_short(con):
    try:
        import porders                                        # noqa: PLC0415
        sh = porders.shelf(con)
        return sh["vendor"], [it for it in sh["items"] if it["short"] > 0]
    except Exception:                                         # noqa: BLE001
        return None, []
''', '''def _ortho_short(con):
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


def _s605_ordered_since(con, sn, item, at):
    """An order of the new flow to the orthotic vendor (draft, sent or received), made at or after `at`, carries the item."""
    return con.execute("SELECT 1 FROM purchase_order o JOIN purchase_order_line l ON l.order_id=o.id WHERE o.order_src='s454' AND o.supplier_norm=? "
                       "AND o.status IN ('draft','sent','received') AND o.created_at>=? AND l.item=? LIMIT 1", (sn, at, item)).fetchone() is not None


def ortho_kept(con):
    """(vendor, [rows]) -- THE ONE RULE of the orthotic card (entries() reads it, nothing else): the lines whose newest answer is Darpan's
    'yes' and that no order to the orthotic vendor has carried since. Reads his rows and the order book only; writes nothing."""
    ensure(con)
    vendor = _s605_vendor(con)
    if not vendor:
        return None, []
    sn = _pa().supplier_key(vendor)
    out = [a for a in _s605_answers(con).values() if a["answer"] == "yes" and not _s605_ordered_since(con, sn, a["item"], a["at"])]
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
'''))
OSE.append(("O5 entries(): the orthotic card is Darpan's kept lines", '''    if with_ortho:                                            # S403's orthotic shortage: that supplier's card, on both settings
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
''', '''    if with_ortho:                                            # S605 (D749): the lines Darpan kept, not yet ordered -- never the shortage itself
        vendor, kept = ortho_kept(con)
        if vendor and kept:
            sn = pa.supplier_key(vendor)
            if sn not in drafts:
                c = card(sn, vendor)
                have = {pa.norm(x["item"]) for x in c["lines"]}
                for a in kept:
                    if pa.norm(a["item"]) in have:
                        continue                              # an item on both is shown once, with the sheet's quantity
                    ref = "ortho:%d" % a["id"]                # his yes row: reception's quantity edit keeps to the line
                    e = _edits(con, "ortho", ref).get(a["item"]) or {}
                    if e.get("removed"):
                        continue
                    c["lines"].append(dict(src="ortho", ref=ref, item=a["item"], qty=int(e["qty"]) if e.get("qty") is not None else int(a["qty"] or 0),
                                           loose=0, strip=0, pack_size=1, packing="1*1", rate_p=0, entry="", reordered=False, on_hand=None))
                c["sources"].add("ortho")
'''))
OSE.append(("O6 order_supplier: a handed message is never queued again", '''        if e["state"] == "withdrawn":
            _queue_message(con, e, oid, who, requeue=True)
''', '''        if e["state"] == "withdrawn":
            if _s605_handed(con, oid):                        # S605 (F-960): once handed to the phone, never queued again -- call
                return dict(ok=False, error="handed", message="WhatsApp nahi gaya — call kijiye"), 409
            _queue_message(con, e, oid, who, requeue=True)
'''))
OSE.append(("O7 whatsapp_all: the one list, checked against the screen's", '''def whatsapp_all(con, who):
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
''', '''def _s605_handed(con, oid):
    """S605 (F-960): the order's message was handed to the reception phone (handed_at, never reset by the server)."""
    return con.execute("SELECT 1 FROM supplier_msg WHERE kind='order' AND ref=? AND handed_at IS NOT NULL LIMIT 1", (int(oid),)).fetchone() is not None


def wa_plan(con):
    """S605 (F-961): (queue, nonum, call) -- THE ONE LIST of 'Sab ko WhatsApp bhejo': every card not in the phone's line with an Order
    WhatsApp number (queue), without one (nonum), and withdrawn after the phone was handed its message (call: never sent again). The
    confirm screen shows it; whatsapp_all queues it. Writes nothing."""
    q, nonum, call = [], [], []
    for e in entries(con):
        if e["state"] == "in_line":
            continue
        if e["state"] == "withdrawn" and _s605_handed(con, (e.get("draft") or {}).get("id") or 0):
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
'''))
OSE.append(("O8 withdraw_late: never-handed withdrawn, handed-unconfirmed ordered", '''def withdraw_late(con):
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
''', '''def withdraw_late(con):
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
        if st != "failed" and handed and d and (now() - d) >= dt.timedelta(minutes=wait):
            _s605_unconfirmed(con, mid, ref, vendor, handed, wait)
            n += 1
            continue
        if st == "failed" or (d and (now() - d) >= dt.timedelta(minutes=wait)):
            o = con.execute("SELECT status FROM purchase_order WHERE id=?", (int(ref or 0),)).fetchone()
'''))
OSE.append(("O9 the unconfirmed order, and the owner's lines' helpers (before arrival by the bill's scan)", '''# ------------------------------------------------------------------ arrival by the bill's scan (D668)
def _assets():
''', '''def _s605_unconfirmed(con, mid, ref, vendor, handed, wait):
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
    return out


# ------------------------------------------------------------------ arrival by the bill's scan (D668)
def _assets():
'''))
OSE.append(("O10 owner_lines: the S605 lines join", '''        for r in con.execute("SELECT supplier, line_date, COUNT(*) FROM order_sheet_line WHERE state='lapsed' AND lapsed_at>=? GROUP BY supplier_norm, line_date",
                             (since,)):
''', '''        out.extend(_s605_owner_lines(con))                   # S605: the orthotic line never offered; the order the phone never confirmed
        for r in con.execute("SELECT supplier, line_date, COUNT(*) FROM order_sheet_line WHERE state='lapsed' AND lapsed_at>=? GROUP BY supplier_norm, line_date",
                             (since,)):
'''))

# ======================================================================================================================= porders_s454.py
PSE = []
PSE.append(("P1 the module header", '''#    GET  /finance/porders/api/s454/state             the counts (the walk and the duty map read them)
''', '''#    GET  /finance/porders/api/s454/state             the counts (the walk and the duty map read them)
#  S605_ORDER_FIXES (20-Oct-2026; F-961, F-962, the owner's numbers of 15:28 / 15:54 IST):
#    GET  /finance/porders/s454/order/whatsapp        WhatsApp bhejna hai? -- the suppliers order_sheet.wa_plan queues now, each with its
#                                                     numbers, those with no number; "Haan, WhatsApp bhejo" posts the list it showed (409
#                                                     when the list moved); its read writes nothing. "Sab ko WhatsApp bhejo" is a link to it.
#    The home keeps "Aaj ke order — call karo" (the Ho chuke rule) once nothing is left to order. Every dealer line of the order screens
#    carries "Call: <call> · WhatsApp: <wa>" (nums_text: the one builder of these words, for the screens and both PDFs).
'''))
PSE.append(("P2 the words", '''    "margoff": ("Yeh line ab Marg ke order mein nahi hai.", "This line is no longer on Marg's order."),
}
''', '''    "margoff": ("Yeh line ab Marg ke order mein nahi hai.", "This line is no longer on Marg's order."),
    "r_call": ("Aaj ke order — call karo", "Today's orders — call"),                                    # S605 (F-962)
    "wa_q": ("WhatsApp bhejna hai?", "Send the WhatsApp?"), "wa_n": ("In %d supplier ko WhatsApp jayega", "These %d suppliers get a WhatsApp"),   # S605 (F-961)
    "wa_yes": ("Haan, WhatsApp bhejo", "Yes, send the WhatsApp"), "wa_back": ("Nahi, wapas", "No, back"),
    "wa_none": ("Abhi kisi supplier ko WhatsApp nahi jayega.", "No supplier gets a WhatsApp now."),
    "wa_nonum2": ("%s — number nahi hai, call kijiye.", "%s — no number, please call."),
    "darpan_haan": ("Darpan ki haan", "Darpan's yes"),
    "wa_unlock": ("Reception phone unlocked rakhiye. WhatsApp khud khulega, har minute ek supplier (%d minute).",
                  "Keep the reception phone unlocked. WhatsApp opens by itself, one supplier a minute (%d minutes)."),
}
'''))
PSE.append(("P3 nums_text, the one builder of the numbers' words (after L)", '''def month_name(ym):
''', '''def nums_text(call, wa, en=False, missing=None):
    """S605 (the owner, 20-Oct 15:28 / 15:54 IST): 'Call: <call> · WhatsApp: <wa>' from book_card's two numbers -- the ONE builder of these
    words for the screens and both PDFs. missing=None (the screens): a number that is not there is left out ('' when neither is); missing=
    <sentence> (the PDFs): a missing number prints its own label with that sentence, both missing print the sentence alone."""
    if missing is not None and not call and not wa:
        return missing
    parts = []
    for k, v in (("num_call", call), ("num_wa", wa)):
        if v:
            parts.append(L(en, k, v))
        elif missing is not None:
            parts.append(L(en, k, missing))
    return " · ".join(parts)


def month_name(ym):
'''))
PSE.append(("P4 the home: the call row (F-962)", '''    any_ = False
    for k, href, lab in rows:
        if c[k] > 0:
            any_ = True
            h.append('<a class="row" id="row_%s" href="%s"><span class="n">%d</span><span class="l">%s</span><span>›</span></a>' % (k, href, c[k], L(en, lab)))
''', '''    any_ = False
    for k, href, lab in rows:
        if k == "order" and c[k] <= 0:                        # S605 (F-962): nothing left to order -- the day's orders, each with its Call
            nd = len(_done_today(con))                        # the 'Ho chuke' rule of the order list (charter 13)
            if nd:
                any_ = True
                h.append('<a class="row" id="row_call" href="%s"><span class="n">%d</span><span class="l">%s</span><span>›</span></a>' % (href, nd, L(en, "r_call")))
            continue
        if c[k] > 0:
            any_ = True
            h.append('<a class="row" id="row_%s" href="%s"><span class="n">%d</span><span class="l">%s</span><span>›</span></a>' % (k, href, c[k], L(en, lab)))
'''))
PSE.append(("P5 _card: the numbers under the name", '''    q = quote(e["sn"], safe="")
    btn = ('<button class="g" onclick="s454(\\'%s/api/s454/ordered\\',{sn:%s})">%s</button>' % (P, esc(json.dumps(e["sn"])), L(en, "ordered")))
    return ('<div class="card" data-sn="%s"><div><div class="nm">%s</div><div class="sb%s">%s</div></div><div class="two"><a class="b" href="%s/s454/order/%s">%s</a>%s</div></div>'
            % (esc(e["sn"]), esc(e["vendor"]), " am" if am else "", esc(sub), P, q, L(en, "open"), btn))
''', '''    q = quote(e["sn"], safe="")
    btn = ('<button class="g" onclick="s454(\\'%s/api/s454/ordered\\',{sn:%s})">%s</button>' % (P, esc(json.dumps(e["sn"])), L(en, "ordered")))
    nt = nums_text(e.get("phone"), e.get("wa"), en)            # S605: the phone book's two numbers, named (a sender's / the owner's page)
    nums = ('<div class="sb nums">%s</div>' % esc(nt)) if nt else ""
    return ('<div class="card" data-sn="%s"><div><div class="nm">%s</div>%s<div class="sb%s">%s</div></div><div class="two"><a class="b" href="%s/s454/order/%s">%s</a>%s</div></div>'
            % (esc(e["sn"]), esc(e["vendor"]), nums, " am" if am else "", esc(sub), P, q, L(en, "open"), btn))
'''))
PSE.append(("P6 order_list: the unlock line, the link to the confirm screen", '''    alive, _why = OS.phone_state(con)
    if pend:
        h.append('<button class="big" id="waall" %s onclick="s454(\\'%s/api/s454/whatsapp\\',{})">%s</button>' % ("" if alive else "disabled", P, L(en, "wa_all")))
''', '''    nwait = _s605_waiting(con)
    if nwait:                                                 # S605 (F-961): while the day's order messages wait for the phone
        h.append('<div class="ok" id="waunlock"><div class="t">%s</div></div>' % esc(L(en, "wa_unlock", nwait)))
    alive, _why = OS.phone_state(con)
    if pend:
        if alive:                                             # S605 (F-961): the confirm screen first -- no POST from here
            h.append('<a class="big" id="waall" href="%s/s454/order/whatsapp">%s</a>' % (P, L(en, "wa_all")))
        else:
            h.append('<button class="big" id="waall" disabled>%s</button>' % L(en, "wa_all"))
'''))
PSE.append(("P7 the Ho chuke lines: the numbers", '''            mark = L(en, word)
            if OS.ddmm(d["sent_at"]) != OS.ddmm(OS.now_iso()):   # S593 (F-916): a done line of an earlier day says its own date
                mark = "%s · %s" % (esc(OS.ddmm(d["sent_at"])), mark)
            h.append('<div class="ln"><div class="t"><div class="a">%s</div><div class="s grn">✓ %s</div></div>%s</div>' % (esc(d["vendor"]), mark, callb))
''', '''            mark = L(en, word)
            if OS.ddmm(d["sent_at"]) != OS.ddmm(OS.now_iso()):   # S593 (F-916): a done line of an earlier day says its own date
                mark = "%s · %s" % (esc(OS.ddmm(d["sent_at"])), mark)
            nt = nums_text(d["phone"], d.get("wa"), en)          # S605: the phone book's two numbers, named
            h.append('<div class="ln"><div class="t"><div class="a">%s</div><div class="s grn">✓ %s</div>%s</div>%s</div>'
                     % (esc(d["vendor"]), mark, ('<div class="s nums">%s</div>' % esc(nt)) if nt else "", callb))
'''))
PSE.append(("P8 _done_today carries the WhatsApp number; the waiting count; the confirm screen", '''        out.append(dict(id=o["id"], vendor=o["vendor"], sn=o.get("supplier_norm") or _pa().supplier_key(o["vendor"]), via=o.get("order_via") or "",
                        sent_at=sent_at, by=o.get("created_by") or "", phone=_pa().book_number(con, o["vendor"], "call")))   # S574: the Calls number
    return out
''', '''        out.append(dict(id=o["id"], vendor=o["vendor"], sn=o.get("supplier_norm") or _pa().supplier_key(o["vendor"]), via=o.get("order_via") or "",
                        sent_at=sent_at, by=o.get("created_by") or "", phone=_pa().book_number(con, o["vendor"], "call"),   # S574: the Calls number
                        wa=_pa().book_number(con, o["vendor"], "order")))                                                     # S605: the Order WhatsApp number
    return out


def _s605_waiting(con):
    """S605 (F-961): today's order messages still waiting for the reception phone (queued -- handed or not -- with a number)."""
    try:
        return int(con.execute("SELECT COUNT(*) FROM supplier_msg WHERE kind='order' AND status='queued' AND to_number IS NOT NULL AND substr(queued_at,1,10)=?",
                               (OS.now().date().isoformat(),)).fetchone()[0])
    except sqlite3.Error:
        return 0


def wa_confirm_page():
    """S605 (F-961): 'WhatsApp bhejna hai?' -- the suppliers order_sheet.wa_plan would queue now (each with its line count and numbers), those
    with no number, those to call; 'Haan, WhatsApp bhejo' posts the list it showed. Its read writes nothing (no _every_read)."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    back = P + "/s454/order"
    import order_rules                                        # noqa: PLC0415
    if order_rules._frozen(con):
        return shell(con, u, L(en, "wa_q"), '<div class="err">%s</div>' % L(en, "frozen"), back=back, login=login)
    alive, _why = OS.phone_state(con)
    if not alive:
        return shell(con, u, L(en, "wa_q"), '<div class="mut" id="waoff">%s</div><a class="more" id="waback" href="%s">%s</a>' % (L(en, "wa_off"), back, L(en, "wa_back")),
                     back=back, login=login)
    q, nonum, call = OS.wa_plan(con)
    h = []
    if q:
        h.append('<h1 id="wan">%s</h1>' % esc(L(en, "wa_n", len(q))))
        for e in q:
            n = len(e["lines"])
            sub = L(en, "dawa", n) + ((" (%s)" % L(en, "darpan_haan")) if "ortho" in (e.get("sources") or []) else "")
            nt = nums_text(e.get("phone"), e.get("wa"), en) if kind in ("owner", "sender") else ""
            h.append('<div class="card" data-sn="%s"><div class="nm">%s</div><div class="sb">%s</div>%s</div>'
                     % (esc(e["sn"]), esc(e["vendor"]), esc(sub), ('<div class="sb nums">%s</div>' % esc(nt)) if nt else ""))
    else:
        h.append('<div class="ok" id="wanone"><div class="t">%s</div></div>' % L(en, "wa_none"))
    for e in nonum:
        h.append('<div class="mut am" data-nonum="%s">%s</div>' % (esc(e["sn"]), esc(L(en, "wa_nonum2", e["vendor"]))))
    for e in call:
        h.append('<div class="mut am" data-call="%s">%s — %s</div>' % (esc(e["sn"]), esc(e["vendor"]), L(en, "wa_no")))
    if q:
        h.append('<button class="big" id="wayes" onclick="s605wa()">%s</button>' % L(en, "wa_yes"))
        h.append("<script>function s605wa(){fetch('%s/api/s454/whatsapp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sns:%s})})"
                 ".then(function(r){return r.json().then(function(j){return [r,j];});}).then(function(x){var r=x[0],j=x[1];"
                 "if(r.ok&&j.ok){location.href='%s';return;}var m=document.getElementById('msg');m.textContent=j.message||j.error||('HTTP '+r.status);m.style.display='block';"
                 "if(j.error==='list_changed'){setTimeout(function(){location.reload();},1500);}}).catch(function(e){var m=document.getElementById('msg');"
                 "m.textContent=String(e);m.style.display='block';});}</script>" % (P, esc(json.dumps([e["sn"] for e in q])).replace("&quot;", '"'), back))
    h.append('<a class="more" id="waback" href="%s">%s</a>' % (back, L(en, "wa_back")))
    return shell(con, u, L(en, "wa_q"), "".join(h), back=back, login=login)
'''))
PSE.append(("P9 the confirm screen's route (before the supplier route)", '''@bp.route(P + "/s454/order/<path:sn>")
def r_supplier(sn):
''', '''@bp.route(P + "/s454/order/whatsapp")
def r_wa_confirm():
    return wa_confirm_page()                                  # S605 (F-961): a static rule, matched before the supplier's


@bp.route(P + "/s454/order/<path:sn>")
def r_supplier(sn):
'''))
PSE.append(("P10 api_whatsapp: the list the screen showed", '''    b, code = OS.whatsapp_all(con, who(u))
''', '''    b, code = OS.whatsapp_all(con, who(u), expect=[str(x) for x in (_body().get("sns") or [])])   # S605 (F-961): 409 when the list moved
'''))

# ======================================================================================================================= supplier_msg.py
SME = []
SME.append(("S1 api_next: handed once (F-960)", '''    gap = (_now() - dt.timedelta(minutes=_s454_gap(con))).isoformat()      # S454 (F-702): a message handed out is not handed again within the gap
    r = con.execute("SELECT id, to_number, body FROM supplier_msg WHERE to_number IS NOT NULL AND attempts<? AND (handed_at IS NULL OR handed_at<=?) AND "
                    "(status='queued' OR (status='failed' AND kind NOT IN ('order','test') AND (last_try_at IS NULL OR last_try_at<=?))) "
                    "ORDER BY (kind='test') DESC, queued_at, id LIMIT 1",          # S454 P1C: the owner's test first; a failed test is never retried
                    (MAX_ATTEMPTS, gap, cut)).fetchone()
''', '''    gap = (_now() - dt.timedelta(minutes=_s454_gap(con))).isoformat()      # S454 (F-702): the owner's test only, since S605
    r = con.execute("SELECT id, to_number, body FROM supplier_msg WHERE to_number IS NOT NULL AND attempts<? AND "
                    "((status='queued' AND (handed_at IS NULL OR (kind='test' AND handed_at<=?))) OR "      # S605 (F-960): handed ONCE -- never again
                    "(status='failed' AND kind NOT IN ('order','test') AND (handed_at IS NULL OR handed_at<=?) AND (last_try_at IS NULL OR last_try_at<=?))) "
                    "ORDER BY (kind='test') DESC, queued_at, id LIMIT 1",          # S454 P1C: the owner's test first; a failed test is never retried
                    (MAX_ATTEMPTS, gap, gap, cut)).fetchone()                       # a payment message the phone said it could not send: after RETRY_MIN
'''))
SME.append(("S2 the setup page's sentence", '''<p class="mut">Ek message server do baar nahi deta: diya hua message 10 minute tak dobara nahi milta. Agar''',
            '''<p class="mut">Ek message server ek hi baar deta hai. Agar'''))
SME.append(("S3 the S454 block's F-702 line", '''#   * F-702: a message handed to the phone is not handed out again for supplier_msg.handout_gap_min minutes (handed_at) -- this protects the
#     payment notices too. The phone is told on its setup page to ask again at once after each message, until the answer is empty.
''', '''#   * F-702: a message handed to the phone is not handed out again for supplier_msg.handout_gap_min minutes (handed_at) -- this protects the
#     payment notices too. The phone is told on its setup page to ask again at once after each message, until the answer is empty.
#     S605 (F-960): a message once handed is NEVER handed again (the owner's test apart, after the gap); a payment message the phone said it
#     could not send is retried after RETRY_MIN; an order message handed and never confirmed is the owner's line (order_sheet.withdraw_late).
'''))

# ======================================================================================================================= order_sheet_pdf.py
SPE = []
SPE.append(("Q1 the header's band words", '''#  column heads per page (Item · Pack · Qty · Order · Aaya · Kam aaya / nahi aaya); a shaded band per supplier with the phone book's
#  number(s) -- the screens' own words when none (porders_s454.T["nonum"], S584: one copy) -- and three boxes (WhatsApp · Call · Bill scan); a row per medicine with its quantity in
''', '''#  column heads per page (Item · Pack · Qty · Order · Aaya · Kam aaya / nahi aaya); a shaded band per supplier with the phone book's
#  numbers, named -- "Call: <call> · WhatsApp: <wa>" (S605: porders_s454.nums_text, the one builder; a missing one says the screens' own
#  T["nonum"] sentence, S584: one copy) -- and three boxes (WhatsApp · Call · Bill scan); a row per medicine with its quantity in
'''))
SPE.append(("Q2 layout: a block carries call and wa", '''        blocks.append(dict(name=b["name"], phones=OS.book_card(con, b["name"])[2], only_old=False, ticks=ticks, rows=b["rows"]))   # S574
''', '''        call, wa = OS.book_card(con, b["name"])[:2]               # S605: the Calls number and the Order WhatsApp number, named on the band
        blocks.append(dict(name=b["name"], call=call, wa=wa, only_old=False, ticks=ticks, rows=b["rows"]))
'''))
SPE.append(("Q3 layout: an only-old block too", '''        shown = OS.book_card(con, ls[0]["supplier"])[2]          # S574: the one reader (OFF: numbers 1-2, as before)
        if first_only is None:
            first_only = len(blocks)
        blocks.append(dict(name=ls[0]["supplier"], phones=shown, only_old=True, ticks=dict(whatsapp=False, call=False),
''', '''        call, wa = OS.book_card(con, ls[0]["supplier"])[:2]      # S574: the one reader; S605: both numbers, named
        if first_only is None:
            first_only = len(blocks)
        blocks.append(dict(name=ls[0]["supplier"], call=call, wa=wa, only_old=True, ticks=dict(whatsapp=False, call=False),
'''))
SPE.append(("Q5 layout's docstring names the band's fields", '''    """{line, date, blocks:[{name, phones, only_old, ticks:{whatsapp,call}, rows:[{item, pack, qty, kind, ticked, aaya, marg, tag}]}], counts, pages,
''', '''    """{line, date, blocks:[{name, call, wa, only_old, ticks:{whatsapp,call}, rows:[{item, pack, qty, kind, ticked, aaya, marg, tag}]}], counts, pages,
'''))
SPE.append(("Q4 the band prints Call / WhatsApp, never Ph.", '''    if b["phones"]:
        ph = "Ph. " + ", ".join(b["phones"])
    else:
        import porders_s454                                   # noqa: PLC0415 -- S584 (F-915): the screens' sentence, one copy; porders_s454 imports this file lazily (a top-level import would be a cycle)
        ph = porders_s454.T["nonum"][0]                       # "Number nahi hai -- Dr sahab ko dijiye" (_latin folds the dash for the PDF as it does for every string)
''', '''    import porders_s454                                       # noqa: PLC0415 -- S584 (F-915): the screens' words, one copy (a top-level import would be a cycle)
    ph = porders_s454.nums_text(b.get("call"), b.get("wa"), missing=porders_s454.T["nonum"][0])   # S605: "Call: … · WhatsApp: …" ("Ph." retired)
'''))

# ======================================================================================================================= marg_order_pdf.py
MPE = []
MPE.append(("M1 the header", '''#  Suppliers' phone numbers are printed because Marg prints them (a staff page); this file writes nothing anywhere.
''', '''#  Suppliers' phone numbers are printed because Marg prints them (a staff page); this file writes nothing anywhere.
#  S605 (the owner, 20-Oct 15:54 IST): Marg's rows stay exactly as Marg printed them; under the last row of each supplier's group (Marg groups
#  its export by supplier -- three archived exports read at S605) a shaded line "Phone book — Call: <call> · WhatsApp: <wa>"
#  (porders_s454.nums_text, the one builder; book_card, the one reader; _latin folds it as every PDF string).
'''))
MPE.append(("M2 the phone-book line's drawing (after _draw_row)", '''def _foot(con, ns):
''', '''def _book_text(con, supplier):
    """S605: 'Phone book — Call: <call> · WhatsApp: <wa>' for a supplier of Marg's sheet (a missing number says the screens' sentence)."""
    import porders_s454                                       # noqa: PLC0415 -- the screens' words, one copy
    call, wa = OS.book_card(con, supplier)[:2]
    return "Phone book — " + porders_s454.nums_text(call, wa, missing=porders_s454.T["nonum"][0])


def _book_h(text, ws):
    return _row_h([SP.wrap(text, SZ, (RM - LM) - 2 * PAD)])


def _draw_book(p, y, text):
    """One shaded line across the page under a supplier's last row; returns its height."""
    lines = SP.wrap(text, SZ, (RM - LM) - 2 * PAD)
    h = _row_h([lines])
    p.fill(LM, y - h, RM - LM, h, 0.93)
    p.box(LM, y - h, RM - LM, h, 0.5, 0.35)
    for k, s in enumerate(lines):
        p.text(LM + PAD, y - 1.5 - 0.8 * SZ - k * LH, s, SZ, "F3")
    return h


def _foot(con, ns):
'''))
MPE.append(("M3 build: the line under each supplier's group", '''    for i, cells in enumerate(body):
        bold = cells[0].upper() == "TOTAL" and i == len(body) - 1
        h = _row_h(_row_lines(cells, ws, bold))
        if p is None or y - h < floor:
            if p is not None:
                pages.append(p)
            p, y = new_page()
            y -= _draw_row(p, y, heads, ws, True, 0.86)
        y -= _draw_row(p, y, cells, ws, bold, 0.93 if bold else None)
''', '''    for i, cells in enumerate(body):
        bold = cells[0].upper() == "TOTAL" and i == len(body) - 1
        h = _row_h(_row_lines(cells, ws, bold))
        nxt = body[i + 1][0] if i + 1 < len(body) else ""
        book = _book_text(con, cells[0]) if (cells[0] and not bold and nxt != cells[0]) else ""   # S605: the group's last row
        hb = _book_h(book, ws) if book else 0.0
        if p is None or y - h - hb < floor:
            if p is not None:
                pages.append(p)
            p, y = new_page()
            y -= _draw_row(p, y, heads, ws, True, 0.86)
        y -= _draw_row(p, y, cells, ws, bold, 0.93 if bold else None)
        if book:
            y -= _draw_book(p, y, book)
'''))

# ======================================================================================================================= darpan_kal.py
DKE = []
DKE.append(("D1 the module history", '''S403 (D618, 26-Sep-2026): the day payload carries 'ortho_short' -- the orthotic shortages of the Purchase orders
screen (porders.shortage_summary, read in-process, fail-soft) -- for the card 'Orthotic kam hai -- N' on the page.
''', '''S403 (D618, 26-Sep-2026): the day payload carries 'ortho_short' -- the orthotic shortages of the Purchase orders
screen (porders.shortage_summary, read in-process, fail-soft) -- for the card 'Orthotic kam hai -- N' on the page.
S605 (D749, 20-Oct-2026): 'ortho_short' is the list PUT TO DARPAN (order_sheet.darpan_ortho: n, the lines, yes_at / no_at) and his
answer is one POST, /finance/darpan/kal/api/ortho (staff or owner, as the order tab; a cash recipient's view is refused) -- हटाओ one
line, हाँ the lines shown, इस बार नहीं; order_sheet.ortho_answer is the one door. Only the lines he keeps reach reception's order.
'''))
DKE.append(("D2 the section's payload", '''def _ortho_short_safe(con):
    """S403 (D618): 'Orthotic kam hai -- N' for Darpan's card, read from porders in-process; never breaks the page."""
    try:
        import porders                                       # noqa: PLC0415
        return porders.shortage_summary(con)
    except Exception as e:                                   # noqa: BLE001
        return dict(ok=False, n=0, items=[], error=str(e)[:80])
''', '''def _ortho_short_safe(con):
    """S403 (D618): 'Orthotic kam hai -- N' for Darpan's card. S605 (D749): the lines put to him for his yes (order_sheet.darpan_ortho, in
    process); never breaks the page."""
    try:
        import order_sheet                                   # noqa: PLC0415
        return order_sheet.darpan_ortho(con)
    except Exception as e:                                   # noqa: BLE001
        return dict(ok=False, n=0, items=[], error=str(e)[:80])


@bp.route("/finance/darpan/kal/api/ortho", methods=["POST"])
def api_s605_ortho():
    """S605 (D749): Darpan's answer to the orthotic list -- {action: remove | yes | no, items: [{item, qty}] as the section showed them}.
    Staff or owner only (a cash recipient's view of this page has no order work, as the order tab, charter 13)."""
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):
        return jsonify(ok=False, error="not_permitted"), 403
    import order_sheet                                       # noqa: PLC0415
    b = request.get_json(silent=True) or {}
    body, code = order_sheet.ortho_answer(con, str(u.get("user") or ""), str(b.get("action") or ""), b.get("items"))
    return jsonify(**body), code
'''))

# ======================================================================================================================= darpan_kal.html
DHE = []
DHE.append(("H1 the section: the lines, हटाओ, हाँ / इस बार नहीं", '''/* S403 (D618): 'Orthotic kam hai -- N' -- collapsed; the list; a button that opens the Purchase orders screen */
function orthoShortSec(o){
 if(!o||!o.ok) return "";
 const n=o.n||0;
 return sec('<details><summary><span class="k">Orthotic kam hai — <b>'+n+'</b></span>'+(n?'':' <span class="ok">सब ठीक</span>')+'</summary>'+
  (n?'<table>'+o.items.map(x=>'<tr><td>'+esc(x.item)+'</td><td class="n">'+x.short+' kam'+(x.approx?' <span class="badge amber">approx</span>':'')+'</td></tr>').join("")+'</table>':'')+
  (o.sent?'<div class="muted">order bheja: '+esc(o.sent.sent_text)+' · '+esc(o.sent.by)+'</div>':'')+
  '<a class="btn primary" href="'+esc(o.url||"/finance/porders")+'">Purchase orders खोलें ↗</a></details>');
}
''', '''/* S403 (D618): 'Orthotic kam hai -- N'. S605 (D749): the lines put to him -- हटाओ on each, then हाँ, ऑर्डर में डालो / इस बार नहीं;
   only the lines he keeps go on the order. After हाँ: one line "✓ ऑर्डर में गया · HH:MM". */
let ORTHO=[];
function orthoShortSec(o){
 if(!o||!o.ok) return "";
 const n=o.n||0; ORTHO=o.items||[];
 let h='<div class="row" id="orthoSec"><span class="k">Orthotic kam hai — <b>'+n+'</b>'+(n?' · '+esc(o.who||"")+' ko order?':'')+'</span>'+(n||o.yes_at||o.no_at?'':' <span class="ok">सब ठीक</span>')+'</div>';
 if(n){
  h+='<table>'+ORTHO.map((x,i)=>'<tr><td>'+esc(x.item)+'</td><td class="n">'+x.short+' kam'+(x.approx?' <span class="badge amber">approx</span>':'')+
   ' <span class="btn sm" onclick="orthoAns(\\'remove\\','+i+')">हटाओ</span></td></tr>').join("")+'</table>'+
   '<span class="btn primary" id="orthoYes" onclick="orthoAns(\\'yes\\')">हाँ, ऑर्डर में डालो</span><span class="btn" id="orthoNo" onclick="orthoAns(\\'no\\')">इस बार नहीं</span>';
 }
 if(o.yes_at) h+='<div class="ok" id="orthoDone">✓ ऑर्डर में गया · '+esc(o.yes_at)+'</div>';
 else if(o.no_at&&!n) h+='<div class="muted" id="orthoNot">इस बार नहीं · '+esc(o.no_at)+'</div>';
 return sec(h+'<div><a class="btn primary" href="'+esc(o.url||"/finance/porders")+'">Purchase orders खोलें ↗</a></div>');
}
async function orthoAns(action,i){
 const items=(action==="remove")?[ORTHO[i]]:ORTHO;
 try{await post("/finance/darpan/kal/api/ortho",{action:action,items:items.map(x=>({item:x.item,qty:x.short}))});load();}catch(e){toast(""+e);load();}
}
'''))

# ======================================================================================================================= spine/spine_build.py
SBE = []
SBE.append(("B1 the module history", '''  name's key, and the new name is recorded in sp_alias (kind 'rename'). An unticked rename maps nothing.
"""''', '''  name's key, and the new name is recorded in sp_alias (kind 'rename'). An unticked rename maps nothing.
* S605 (F-951): a rename whose old 20-character key is SHARED by more than one ticked rename (the orthotic sizes: KNEE SUPPORT HINGED L /
  M / XL / XXL all clip to one key) is not aliased -- each new name keeps its own key (sp_alias kind 'rename_family'). The old key's history
  stays one family figure up to the first full closing that prints any of the family's new names (its split day): a sale or purchase line
  of a new name dated on or before it stays under the old key (Marg prints today's name on an old line); on the split day each new key
  takes Marg's closing figure for it and the old key gives the same total (sp_move kind RENAME_SPLIT, never a sale or purchase kind --
  the family's sum is unchanged). A family no closing yet prints is aliased as before. A solo rename is aliased as before.
"""'''))
SBE.append(("B2 the shared keys (after rename_aliases)", '''class Gate:
''', '''def rename_family_keys(ren):
    """S605 (F-951): {new key: old key} of the ticked renames whose old key more than one ticked rename shares (a family of sizes)."""
    n = collections.Counter(ren.values())
    return {a: t for a, t in ren.items() if n[t] > 1}


class Gate:
'''))
SBE.append(("B3 build: a rename of a shared old key is not aliased", '''    ren = rename_aliases(finance_db)                             # S404: ticked renames, new clip -> old clip
    for a, t in ren.items():
        alias.setdefault(a, t)
    fam = rules.get("families", {})

    def Z(name):
        k = K(name)
        k = alias.get(k, k)
        return fam.get(k, k)
''', '''    ren = rename_aliases(finance_db)                             # S404: ticked renames, new clip -> old clip
    famren = rename_family_keys(ren)                             # S605 (F-951): a size of a shared key keeps its own key
    for a, t in ren.items():
        if a not in famren:
            alias.setdefault(a, t)
    fam = rules.get("families", {})
    split = {}                                                   # S605: old key -> its split day (the first full closing printing a new name)

    def Z(name):
        k = K(name)
        k = alias.get(k, k)
        return fam.get(k, k)

    def Zd(name, d):
        """S605: Z for a dated line -- a new name of a shared old key stays under the old key up to the family's split day."""
        k = K(name)
        if k in famren:
            sd = split.get(famren[k])
            if sd is None or str(d or "") <= sd:
                return Z(famren[k])
        return Z(name)
'''))
SBE.append(("B4 the split days, once the closings are known", '''    op = rules["opening"]
    opening = [r for r in CL if r["md5"].startswith(op["file_md5_prefix"])]
''', '''    for d in sorted(closings):                                   # S605 (F-951): each shared family's split day
        for i in closings[d]["data"]["items"]:
            k = K(i["name"])
            if k in famren and famren[k] not in split:
                split[famren[k]] = d
    op = rules["opening"]
    opening = [r for r in CL if r["md5"].startswith(op["file_md5_prefix"])]
'''))
SBE.append(("B5 movements: dated lines by Zd; the split moves", '''    if opening:
        for i in opening[0]["data"]["items"]:
            moves.append((Z(i["name"]), op["as_on"], "OPENING", i["units"], opening[0]["md5"][:8]))
    sale_lines = []
    for (d, b), bill in sbills.items():
        for ln in bill["lines"]:
            k = Z(ln["name"])
''', '''    if opening:
        for i in opening[0]["data"]["items"]:
            moves.append((Zd(i["name"], op["as_on"]), op["as_on"], "OPENING", i["units"], opening[0]["md5"][:8]))
    for old, sd in sorted(split.items()):                        # S605 (F-951): on the split day each size takes Marg's figure for it
        got = collections.defaultdict(float)
        for i in closings[sd]["data"]["items"]:
            if K(i["name"]) in famren and famren[K(i["name"])] == old:
                got[Z(i["name"])] += i["units"]
        for k, u in sorted(got.items()):
            if u:
                moves.append((k, sd, "RENAME_SPLIT", u, "S605 a size of %s" % old))
        tot = sum(got.values())
        if tot:
            moves.append((Z(old), sd, "RENAME_SPLIT", -tot, "S605 the sizes of %s" % old))
    sale_lines = []
    for (d, b), bill in sbills.items():
        for ln in bill["lines"]:
            k = Zd(ln["name"], d)
'''))
SBE.append(("B6 purchases by Zd", '''    for l in plines:
        k = Z(l["name"])
        u = ((l["qty"] or 0) + (l["free"] or 0)) * (1 if k in whole else (packn(l["packing"]) or 1))
''', '''    for l in plines:
        k = Zd(l["name"], l["date"])                             # S605 (F-951)
        u = ((l["qty"] or 0) + (l["free"] or 0)) * (1 if k in whole else (packn(l["packing"]) or 1))
'''))
SBE.append(("B7 the bills' re-add reads the same key", '''        for ln in bill["lines"]:
            k = Z(ln["name"])
            pk = packn(ln["pack"]) or pack_of.get(k, 1)
''', '''        for ln in bill["lines"]:
            k = Zd(ln["name"], d)                                # S605: the key the sale line was booked to
            pk = packn(ln["pack"]) or pack_of.get(k, 1)
'''))
SBE.append(("B8 build returns the family keys and split days", '''                facts=facts, whole=whole, Z=Z, checkable=checkable, pending=pending, alias=alias, rename_alias=ren, captures=captures)
''', '''                facts=facts, whole=whole, Z=Z, checkable=checkable, pending=pending, alias=alias,
                rename_alias={a: t for a, t in ren.items() if a not in famren}, rename_family=famren, split=split, captures=captures)
'''))
SBE.append(("B9 write: the family sizes in sp_alias", '''                    [(a, t, "rename", "marg_item_rename -- ticked by Amir (S404, D620)") for a, t in (B.get("rename_alias") or {}).items()])
''', '''                    [(a, t, "rename", "marg_item_rename -- ticked by Amir (S404, D620)") for a, t in (B.get("rename_alias") or {}).items()])
    con.executemany("INSERT OR IGNORE INTO sp_alias VALUES (?,?,?,?)",                   # S605 (F-951): a size keeps its own key
                    [(a, a, "rename_family", "S605: a size of a shared key keeps its own key (split %s from %s)" % ((B.get("split") or {}).get(t) or "not yet", t))
                     for a, t in sorted((B.get("rename_family") or {}).items())])
'''))
SBE.append(("B10 the build version", '''BUILD_VERSION = "S577.1"
''', '''BUILD_VERSION = "S605.1"
'''))

EDITS = {"order_sheet.py": OSE, "porders_s454.py": PSE, "supplier_msg.py": SME, "order_sheet_pdf.py": SPE, "marg_order_pdf.py": MPE,
         "darpan_kal.py": DKE, "darpan_kal.html": DHE, "spine/spine_build.py": SBE}

# ======================================================================================================================= the duty map (D648)
NOTE_ADD = (" S605 (20-Oct-2026; D749, F-959 ... F-962): no duty row added or removed. Darpan's orthotic duty MOVES: it was 'send the orthotic "
            "order' (porders' shortage on reception's card by itself); it is now 'say yes or no to the orthotic list' on his own Kal ka hisaab "
            "(section 'Orthotic kam hai -- N · Yuvika ko order?', हाँ / इस बार नहीं / हटाओ; rows of ortho_yes) and only the lines he keeps reach "
            "reception's Order karna hai. It has no due_sql: what is put to him is computed (porders.shelf: count + purchases - sales vs keep), "
            "which no single SELECT can say -- as before, it is a DUTY_MAP.md row (Darpan) with its door; no owner line (a line he does not answer "
            "waits on his page; an impossible figure is the owner's own line, order_sheet.owner_lines). reception.medicine_orders is unchanged: "
            "its SQL has never counted the orthotic card (S593). `DUTY_MAP.json` is v17.")
MD_OLD_ROW = ("| Send the orthotic order to Yuvika | orthotic shortage computed by porders (count + purchases − sales vs keep) | Purchase orders → "
              "/finance/porders; card \"Orthotic kam hai\" on Kal ka hisaab | Needs-you, porders: \"Orthotic shortages: N items -- order not sent\" |\n")
MD_NEW_ROW = ("| **S605 (D749):** say yes (or no) to the orthotic list before it reaches reception — हटाओ a line, then हाँ, ऑर्डर में डालो / इस "
              "बार नहीं | the orthotic shortage computed by porders (count + purchases − sales vs keep), less a line whose shelf or family figure "
              "is below zero (the owner's line instead), less a line he kept that is not yet ordered, less a line he answered while its "
              "shortage has not changed (`ortho_yes`, one row per tap and line) — computed, so no JSON row | Kal ka hisaab → /finance/darpan/kal, "
              "section \"Orthotic kam hai — N · Yuvika ko order?\"; after हाँ \"✓ ऑर्डर में गया · HH:MM\" and only the kept lines go on Yuvika's "
              "card for reception | none (an unanswered list waits on his page); Needs-you, order_sheet: an impossible figure, \"<ITEM> — the "
              "system's stock figure is −1 (Marg 1): not offered for ordering\"; porders' \"Orthotic shortages: N items\" stays |\n")
MD_ANCHOR = "`DUTY_MAP.json` is v16.\n"
MD_ADD = ("\n**20-Oct-2026 · kit S605_ORDER_FIXES (D749; F-959 … F-962):** Darpan's orthotic duty moves — he says yes (or no) to the orthotic "
          "list on Kal ka hisaab first, and only the lines he keeps reach reception's Order karna hai (the row under Darpan). Reception's "
          "\"Sab ko WhatsApp bhejo\" asks once on its own screen; the home keeps \"Aaj ke order — call karo\" once nothing is left to order "
          "(the same door, /finance/porders). No duty row added or removed in the JSON (Darpan's is computed — no single SELECT). "
          "`DUTY_MAP.json` is v17.\n")


def apply(raw, edits, label, pin):
    m = hashlib.md5(raw).hexdigest()
    if m != pin:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (label, m, pin))
        return None
    t = raw.decode("utf-8")
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            print("STOP: %s anchor %s occurs %d times (must be exactly 1) -- nothing built" % (label, name, n))
            return None
        t = t.replace(old, new, 1)
        print("edit %s %s: anchored once, applied" % (label, name))
    return t.encode("utf-8")


def build_duty_map(raw):
    m = hashlib.md5(raw).hexdigest()
    if m != FROM["DUTY_MAP.json"]:
        print("STOP: DUTY_MAP.json is %s, not the FROM pin %s (v16) -- nothing built" % (m, FROM["DUTY_MAP.json"]))
        return None
    j = json.loads(raw.decode("utf-8"))
    if (json.dumps(j, indent=1, ensure_ascii=False) + "\n").encode("utf-8") != raw or j.get("version") != 16:
        print("STOP: DUTY_MAP.json does not round-trip byte-equal, or is not v16 -- nothing built")
        return None
    j["version"] = 17
    j["kit"] = "S605_ORDER_FIXES"
    j["_note"] = j["_note"] + NOTE_ADD
    out = (json.dumps(j, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    back = json.loads(out.decode("utf-8"))
    assert back["version"] == 17 and len(back["duties"]) == len(j["duties"]) and back["duties"] == json.loads(raw.decode("utf-8"))["duties"]
    print("edit DUTY_MAP.json: v16 -> v17 (the note; no duty row added, removed or changed)")
    return out


def build_duty_md(raw):
    t = raw.decode("utf-8")
    if t.count(MD_ANCHOR) != 1 or t.count(MD_OLD_ROW) != 1 or "S605_ORDER_FIXES" in t:
        print("STOP: DUTY_MAP.md: the v16 line (%d) or Darpan's orthotic row (%d) is not there once, or S605 is already in -- nothing built"
              % (t.count(MD_ANCHOR), t.count(MD_OLD_ROW)))
        return None
    t = t.replace(MD_OLD_ROW, MD_NEW_ROW, 1).replace(MD_ANCHOR, MD_ANCHOR + MD_ADD, 1)
    print("edit DUTY_MAP.md: Darpan's orthotic row; the one dated S605 line after the S603 line")
    return t.encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--repo", required=True, help="the repository clone (its claude_code_briefs and deploy_kits)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    MW = {}                                                    # the F-957 edits of the two walks, kept apart: read, never imported
    exec(compile(open(os.path.join(here, "make_s605_walks.py"), encoding="utf-8").read(), "make_s605_walks.py", "exec"), MW)
    built = {}
    for label, edits in EDITS.items():
        out = apply(open(os.path.join(a.finance, label), "rb").read(), edits, label, FROM[label])
        if out is None:
            return 2
        built[label] = out
    briefs = os.path.join(a.repo, "claude_code_briefs")
    dm = build_duty_map(open(os.path.join(briefs, "DUTY_MAP.json"), "rb").read())
    md = build_duty_md(open(os.path.join(briefs, "DUTY_MAP.md"), "rb").read()) if dm else None
    if dm is None or md is None:
        return 2
    built["DUTY_MAP.json"], built["DUTY_MAP.md"] = dm, md
    for label, (rel, pin, edits) in MW["WALKS"].items():
        out = apply(open(os.path.join(a.repo, rel), "rb").read(), edits, label, pin)
        if out is None:
            return 2
        built[label] = out
    t = {k: v.decode("utf-8") for k, v in built.items()}
    # ---- the grep proofs (charter 2 and 9) on the built text
    o = t["order_sheet.py"]
    assert o.count("_ortho_short(con)") == 2 and o.count("def _ortho_short(") == 1, "_ortho_short: one reader, called by ortho_offer only (and its def)"
    assert o.count("ortho_kept(con)") == 3 and o.count("def ortho_kept(") == 1, "ortho_kept: its def, entries() and ortho_offer"
    assert "porders.shelf" in o and o.count("porders.shelf(") == 1, "one call of porders.shelf, inside _ortho_short"
    assert o.count("def wa_plan(") == 1 and o.count("wa_plan(con)") == 2, "wa_plan: whatsapp_all reads it (the screen through OS.wa_plan)"
    assert o.count("_s605_unconfirmed(con,") == 2 and o.count("_s605_owner_lines(con)") == 2, "each defined once, called once"
    assert '"ortho:" + t.isoformat()' not in o, "the dated orthotic ref is retired"
    p = t["porders_s454.py"]
    assert "api/s454/whatsapp\\',{})" not in p and "onclick=\"s454(\\'%s/api/s454/whatsapp" not in p, "no direct POST from #waall"
    assert p.count("OS.wa_plan(con)") == 1 and p.count("def nums_text(") == 1 and p.count("nums_text(") == 4, "nums_text: defined once, the card, Ho chuke, the confirm screen"
    assert p.count('"r_call"') == 2 and p.count("_done_today(con)") == 3, "the call row reads the Ho chuke rule"
    s = t["supplier_msg.py"]
    assert "diya hua message 10 minute tak" not in s and s.count("Ek message server ek hi baar deta hai.") == 1
    sp = t["order_sheet_pdf.py"]
    assert '"Ph. "' not in sp and "phones" not in sp.split("# =============================================================================", 2)[2], "Ph. retired; no phones field"
    assert t["marg_order_pdf.py"].count("_book_text(con, cells[0])") == 1
    assert t["darpan_kal.py"].count("order_sheet.darpan_ortho(con)") == 1 and "porders.shortage_summary(con)" not in t["darpan_kal.py"]
    assert t["darpan_kal.html"].count("/finance/darpan/kal/api/ortho") == 1 and t["darpan_kal.html"].count("Purchase orders खोलें ↗") == 2
    b = t["spine/spine_build.py"]
    assert b.count("Zd(") == 5 and b.count("def rename_family_keys(") == 1 and '"RENAME_SPLIT"' in b
    for label, out in built.items():                           # no run of ten digits added (a phone number) -- the live text's own are kept
        src = open(os.path.join(a.finance, label) if label in EDITS else (os.path.join(briefs, label) if label.startswith("DUTY_MAP")
                   else os.path.join(a.repo, MW["WALKS"][label][0])), "rb").read()
        assert len(re.findall(rb"\d{10}", out)) == len(re.findall(rb"\d{10}", src)), "a run of ten digits added in %s" % label
    for label, out in built.items():
        dst = os.path.join(a.out, label)
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s md5 %s  (FROM %s)" % (label, hashlib.md5(out).hexdigest(), FROM.get(label) or MW["WALKS"].get(label, ("", "-"))[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
