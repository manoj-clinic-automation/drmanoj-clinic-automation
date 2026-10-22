#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s619.py -- kit S619_ORDER_TRACKER (22-Oct-2026): the anchored builder. Reads the LIVE files, checks each FROM pin, applies each edit at
an anchor that must occur EXACTLY ONCE (else it stops and writes nothing), and writes the built files into --out:

    python3 -B make_s619.py --finance /root/finance --out <dir> [--kit <this folder>]

    <out>/order_sheet.py  <out>/porders_s454.py  <out>/darpan_kal.py  <out>/darpan_kal.html  <out>/order_sheet_pdf.py  <out>/marg_order_pdf.py
    <out>/order_track.py  (new: this kit's own file, byte for byte)

The blocks inserted are this kit's own files (s619_*_block.txt), byte for byte. No file outside --out is written."""
import argparse
import hashlib
import os
import sys

FROM = {"order_sheet.py": "ff9375f98c46f0a004a02a3582693a83", "porders_s454.py": "4d1506480b2b1388ae1020c302e71a84",     # S618's TO
        "darpan_kal.py": "d6ba4882b5f8c4d365016eff87ddba52", "darpan_kal.html": "c0ddc0eaa167b78bbb39bcebbb53c1b0",
        "order_sheet_pdf.py": "7a6d47c040536a24407ebfbb91d171e1", "marg_order_pdf.py": "bdcf2d00f303a6932c9d1ffe686afffa"}


def md5b(b):
    return hashlib.md5(b).hexdigest()


def block(kit, name):
    with open(os.path.join(kit, name), "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def edits(kit):
    """[(file, anchor, new_text_for_the_anchor, what)] -- each anchor once in the live file."""
    E = []
    # ============================================================================================== order_sheet.py
    f = "order_sheet.py"
    E.append((f, r'''#      a silence.
# =============================================================================
''', r'''#      a silence.
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
''', "order_sheet: the header names S619"))
    E.append((f, r'''    "order.sheet_notice_max_min": ("60", "Order sheet arrived: minutes after which the arrival notice is no longer sent"),   # S494 (F-767)
}
''', r'''    "order.sheet_notice_max_min": ("60", "Order sheet arrived: minutes after which the arrival notice is no longer sent"),   # S494 (F-767)
    "order.deliver_days": ("2", "S619 (the owner, 22-Oct): an order is late this many days after it was made, at 18:00 -- the days in order.deliver_skip not counted"),
    "order.deliver_skip": ("SUN", "S619: days not counted towards order.deliver_days (MON..SUN, comma-separated)"),
    "order.deliver_window": ("15:00-18:00,-11:00", "S619: the delivery hours asked of the dealers; a 'Maal aaya' tap outside them shows its time on the order list"),
    "order.wa_delivery_line": ("Kripya maal dopahar 3 se shaam 6 baje ke beech, ya subah 11 baje tak bhejein.",
                               "S619 (the owner, 22-Oct): the last line of every WhatsApp order, and once on the printed sheets"),
    "order.track_since": ("2026-10-12", "S619: the order list, the late rule and the carry count the orders made on or after this day"),
}
''', "order_sheet: the five S619 settings"))
    E.append((f, r'''def _ia():
    import item_alias                                         # noqa: PLC0415
    return item_alias
''', r'''def _ia():
    import item_alias                                         # noqa: PLC0415
    return item_alias


def _ot():
    import order_track                                        # noqa: PLC0415 -- S619, beside this file
    return order_track
''', "order_sheet: _ot() (order_track, imported inside functions)"))
    E.append((f, r'''    con.commit()


def audit(con, who, action, ref="", detail=None):
''', r'''    try:                                                      # S619: the carry's table -- order_track.CARRY_DDL, the one DDL
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
''', "order_sheet: ensure() makes order_carry and s454_line_edit.reason"))
    E.append((f, r'''    removed = {(r[0], r[1]) for r in con.execute("SELECT ref, item FROM s454_line_edit WHERE src='sheet' AND removed=1")}
''', r'''    removed, dealer_no = _s619_removed(con, ns)                # S619: a 'Dealer ke paas nahi hai' removal lifts on a newer sheet
''', "order_sheet: open_order reads the live removals"))
    E.append((f, r'''                 removed=((str(l["id"]), l["item"]) in removed))
''', r'''                 removed=((str(l["id"]), l["item"]) in removed), dealer_no=((str(l["id"]), l["item"]) in dealer_no))
''', "order_sheet: open_order marks a dealer_no line"))
    E.append((f, r'''    records a part), after 'maal aa gaya · ' for a line ordered here whose order has come (by the bill's scan or the arrival tap)."""
    if marg_received(l):
''', r'''    records a part), after 'maal aa gaya · ' for a line ordered here whose order has come (by the bill's scan or the arrival tap)."""
    if l.get("dealer_no"):                                    # S619: removed 'Dealer ke paas nahi hai'
        return "the dealer does not have it" if en else "dealer ke paas nahi"
    if marg_received(l):
''', "order_sheet: old_word says 'dealer ke paas nahi'"))
    E.append((f, r'''def _edits(con, src, ref):
    return {r[0]: dict(qty=r[1], removed=int(r[2] or 0)) for r in con.execute("SELECT item, qty, removed FROM s454_line_edit WHERE src=? AND ref=?", (src, str(ref)))}
''', r'''def _edits(con, src, ref):
    """S619: a removal 'Dealer ke paas nahi hai' counts only while it lives (_s619_live): a sheet line's until a newer Marg sheet, any other's for its day."""
    has = _has_col(con, "s454_line_edit", "reason")
    taken = _s619_taken(con) if src == "sheet" else ""
    out = {}
    for r in con.execute("SELECT item, qty, removed, %s, at FROM s454_line_edit WHERE src=? AND ref=?" % ("reason" if has else "NULL"), (src, str(ref))):
        out[r[0]] = dict(qty=r[1], removed=(int(r[2] or 0) if _s619_live(r[3], r[4], src, taken) else 0), reason=r[3])
    return out
''', "order_sheet: _edits honours the reason"))
    E.append((f, r'''    for sn, d in drafts.items():                              # a supplier whose WhatsApp was tapped: its draft order is its card
''', r'''    try:                                                      # S619 (3.4): a medicine that did not come rides on its dealer's NEXT card
        for cr in _ot().open_carries(con):
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
''', "order_sheet: entries() puts the open carries on the dealer's next card"))
    E.append((f, r'''    _mark_sources(con, e, oid, "ordered" if via == "call" else "in_line", who)
    if via == "whatsapp":
''', r'''    _mark_sources(con, e, oid, "ordered" if via == "call" else "in_line", who)
    _s619_carry_done(con, e, oid)                             # S619: the carried lines ride on this order (never carried again)
    if via == "whatsapp":
''', "order_sheet: order_supplier marks the carried lines done"))
    E.append((f, r'''def wa_body(con, lines, vendor=""):
    """The order's text as built today -- the shop's heading, then one line per medicine with its quantity and unit (qty_words: never
    'units')."""
    pa = _pa()
    qw = whole_units(con)                                     # S543: the one loader of the whole-unit list
    body = []
    for l in lines:
        if qw is not None:
            q = qw.words(int(l["packs"]) * (int(l["pack_size"] or 1) if int(l["pack_size"] or 1) > 1 else 1), pack=int(l["pack_size"] or 1), name=l["item"])
        else:
            q = "%d" % int(l["packs"])
        body.append("%s — %s" % (l["item"], q))
    return pa.WA_HEADER + "\n\n" + "\n".join(body)
''', r'''def wa_body(con, lines, vendor="", carried=None):
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
''', "order_sheet: wa_body -- the carried words and the delivery line"))
    E.append((f, r'''    body = wa_body(con, lines, e["vendor"])
''', r'''    body = wa_body(con, lines, e["vendor"], carried=_s619_carried(con, oid))   # S619: both queue paths
''', "order_sheet: _queue_message passes the carried lines"))
    E.append((f, r'''    rd = _date(o["received_at"])
    if not rd or (t - rd).days >= int_setting(con, "purchase.arrival_scan_days"):
        return False
''', r'''    rd = _date(o["received_at"])
    if not rd or (t - rd).days >= int_setting(con, "purchase.arrival_scan_days"):
        return False
    if not _s619_may_ask(con, o["id"]):                       # S619 (3.3): nothing came, or every line answered with Marg in
        return False
''', "order_sheet: _asking -- the two S619 rules"))
    E.append((f, r'''        if o["status"] == "received" and not _asking(con, o, t, mc):
            continue
''', r'''        if o["status"] == "received" and not _asking(con, o, t, mc):
            continue
        if o["status"] == "sent" and not _s619_may_ask(con, o["id"]):
            continue                                          # S619: an order where nothing came never asks
''', "order_sheet: awaiting_scan -- an order where nothing came never asks"))
    E.append((f, r'''        if cand:
            o = cand[0]
            if smd and smd < _md(o["created_at"]):
''', r'''        if cand:
            o = cand[0]
            if len(cand) >= 2:                                # S619 (3.3): two or more orders waiting -- the reading picks, once it is in
                if not (str(s.get("ocr_status") or "") in ("read", "empty", "failed") or (now() - s["at"]) > dt.timedelta(minutes=10)):
                    continue                                  # (ten minutes at most), else the oldest
                o = _s619_pick(con, cand, s, sn) or o
            if smd and smd < _md(o["created_at"]):
''', "order_sheet: tie_pass -- the reading picks among two or more waiting orders"))
    E.append((f, r'''        out["marg_lines"] = "error: %s" % str(e)[:80]
    return out
''', r'''        out["marg_lines"] = "error: %s" % str(e)[:80]
    try:                                                      # S619 (3.4): a short line goes on its dealer's next order by itself
        out["carry"] = _ot().carry_pass(con, now())
    except Exception as e:                                    # noqa: BLE001
        out["carry"] = "error: %s" % str(e)[:80]
    return out
''', "order_sheet: cron_pass runs the carry after Marg's detection"))
    E.append((f, r'''        out.extend(_s605_owner_lines(con))                   # S605: the orthotic line never offered; the order the phone never confirmed
''', r'''        out.extend(_s605_owner_lines(con))                   # S605: the orthotic line never offered; the order the phone never confirmed
        try:                                                  # S619: late orders and medicines short (what the other two voices do not say)
            _ol = _ot().owner_line(con, now())
            if _ol:
                out.append(_ol)
        except Exception:                                     # noqa: BLE001
            pass
''', "order_sheet: owner_lines -- the order list's one line"))
    E.append((f, r'''    if wrote:
        con.commit()
    return rp, cl
''', r'''    if wrote:
        con.commit()
    return rp, cl
''' + block(kit, "s619_os_block.txt"), "order_sheet: the S619 helpers at the end"))
    # ============================================================================================== porders_s454.py
    f = "porders_s454.py"
    E.append((f, r'''#  The owner's cards (who decides, the agreement line, the old pending orders, the sheet's state) and the settings card sit on the old
''', r'''#  S619_ORDER_TRACKER (22-Oct-2026): one order, five steps (order_track):
#    GET  /finance/porders/s454/late                  Order ka maal nahi aaya -- call karo: the late orders (and part orders), Call and Maal aaya
#    GET  /finance/porders/s454/track                 the order list -- the owner (English), porders.rescan_askers (Roman Hindi); writes nothing
#    The home's call row (late, order_track) replaces S605's 'Aaj ke order -- call karo'; Maal aaya lists the orders not arrived and not yet
#    late; the owner's / Shavez's home carries the order list's card instead of S618's separate 'Scans to redo' link; the remove asks a reason.
#  The owner's cards (who decides, the agreement line, the old pending orders, the sheet's state) and the settings card sit on the old
''', "porders_s454: the header names S619"))
    E.append((f, r'''def maal_orders(con):
    """Orders made and not yet received: status sent, no bill scan tied -- S543: and not closed by Marg (OS.marg_closed_order)."""
    tied = OS.ties(con)
    M = OS.marg_lines(con)
    out = []
    for o in con.execute("SELECT * FROM purchase_order WHERE status='sent' ORDER BY created_at, id"):
        o = dict(o)
        if o["id"] in tied or OS.marg_closed_order(con, o, M):
            continue
        o["n"] = con.execute("SELECT COUNT(*) FROM purchase_order_line WHERE order_id=?", (o["id"],)).fetchone()[0]
        out.append(o)
    return out
''', r'''def maal_orders(con):
    """S619: the orders not arrived and not yet late (order_track's light half) -- the late ones are on the call row ('Order ka maal nahi aaya')."""
    out = []
    for s in _s619_ot().awaited(con, OS.now()):
        o = dict(con.execute("SELECT * FROM purchase_order WHERE id=?", (s["id"],)).fetchone())
        o["n"] = s["n"]
        out.append(o)
    return out
''', "porders_s454: maal_orders reads order_track"))
    E.append((f, r'''                scan=len(scan_lines(con)), q=len(questions(con)), rescan=_s618_open_count(con))      # S618: Phir se scan karo
''', r'''                scan=len(scan_lines(con)), q=len(questions(con)), rescan=_s618_open_count(con),      # S618: Phir se scan karo
                late=_s619_late_n(con))                         # S619: Order ka maal nahi aaya -- call karo
''', "porders_s454: counts() carries the late count"))
    E.append((f, r'''    rows = (("order", P + "/s454/order", "r_order"), ("maal", P + "/s454/maal", "r_maal"), ("scan", P + "/s454/scan", "r_scan"), ("q", P + "/s454/q", "r_q"))
''', r'''    rows = (("order", P + "/s454/order", "r_order"), ("late", P + "/s454/late", "r_late"), ("maal", P + "/s454/maal", "r_maal"),   # S619: the call row
            ("scan", P + "/s454/scan", "r_scan"), ("q", P + "/s454/q", "r_q"))
''', "porders_s454: the home's rows -- the call row after the order row"))
    E.append((f, r'''        rows = rows[:2] + (("rescan", P + "/s454/rescan", "r_rescan"),) + rows[2:]
''', r'''        rows = rows[:3] + (("rescan", P + "/s454/rescan", "r_rescan"),) + rows[3:]
''', "porders_s454: Phir se scan karo stays directly above Bill scan karna hai"))
    E.append((f, r'''    for k, href, lab in rows:
        if k == "order" and c[k] <= 0:                        # S605 (F-962): nothing left to order -- the day's orders, each with its Call
            try:                                              # S613 (F-962): THE count, here only -- today's s454 orders still 'sent' (any way but paper)
                nd = int(con.execute("SELECT COUNT(*) FROM purchase_order WHERE order_src='s454' AND status='sent' AND order_via<>'paper' "
                                     "AND substr(created_at,1,10)=?", (OS.today().isoformat(),)).fetchone()[0])
            except sqlite3.Error:
                nd = 0
            if nd:
                any_ = True
                h.append('<a class="row" id="row_call" href="%s"><span class="n">%d</span><span class="l">%s</span><span>›</span></a>' % (href, nd, L(en, "r_call")))
            continue
        if c[k] > 0:
''', r'''    for k, href, lab in rows:
        if c.get(k, 0) > 0:                                   # S619: the call row stands on its own (S605's 'Aaj ke order -- call karo' retired)
''', "porders_s454: S605's call row retired"))
    E.append((f, r'''    if _s618_asker(con, kind, _s618_login(u, login)):          # S618: Scans to redo -- the owner and the askers, while there is any
        _n618 = _s618_count(con)
        if _n618:
            h.append('<div class="lnk"><a id="redo" href="%s/s454/scans">%s</a></div>' % (P, L(en, "redo_link", _n618)))
''', r'''    if _s618_asker(con, kind, _s618_login(u, login)):          # S619: the order list's card -- the one way in (Scans to redo is a section of it)
        h.append(_s619_track_card(con, en))
''', "porders_s454: the order list's card replaces S618's Scans to redo link"))
    E.append((f, r'''                ctl = ('<span class="qbox"><button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:-1}))">−</button><b>%d</b>'
                       '<button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:1}))">+</button>'
                       '<button class="sm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{remove:1}))">%s</button></span>'
                       % (P, b, int(l["qty"]), P, b, P, b, L(en, "remove")))
                items.append('<div class="li"><span class="i">%s</span>%s</div>' % (esc(l["item"]), ctl))
            else:
                items.append('<div class="li"><span class="i">%s</span><span class="q">%s</span></div>' % (esc(l["item"]), esc(q)))
''', r'''                ctl = ('<span class="qbox"><button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:-1}))">−</button><b>%d</b>'
                       '<button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:1}))">+</button></span>'
                       % (P, b, int(l["qty"]), P, b)) + _s619_remove_chips(en, b)           # S619: the one remove door asks a reason
                items.append('<div class="li" style="flex-wrap:wrap"><span class="i">%s%s</span>%s</div>' % (esc(l["item"]), _s619_carry_tag(en, l), ctl))
            else:
                items.append('<div class="li"><span class="i">%s%s</span><span class="q">%s</span></div>' % (esc(l["item"]), _s619_carry_tag(en, l), esc(q)))
''', "porders_s454: supplier_page -- the reason chips and the carried words"))
    E.append((f, r'''    if src not in ("sheet", "proposal", "ortho"):
        return jsonify(ok=False, error="bad_line"), 400
''', r'''    if src not in ("sheet", "proposal", "ortho", "carry"):     # S619: + a carried line
        return jsonify(ok=False, error="bad_line"), 400
''', "porders_s454: api_qty takes a carried line"))
    E.append((f, r'''    l = next(l for l in e["lines"] if l["src"] == src and l["ref"] == ref and l["item"] == item)
    if b.get("remove"):
''', r'''    l = next(l for l in e["lines"] if l["src"] == src and l["ref"] == ref and l["item"] == item)
    reason = str(b.get("reason") or "")
    if b.get("remove"):                                       # S619: a reason on the one remove door -- only on a card with no draft yet
        if e.get("draft") or e.get("state") != "pending":
            return jsonify(ok=False, error="has_draft", message="Is supplier ka order ban chuka hai — ab line nahi hat sakti."), 409
        if reason not in ("dealer_no", "not_now"):
            return jsonify(ok=False, error="reason_needed", message="Wajah chuniye: Dealer ke paas nahi hai / Abhi nahi chahiye."), 400
    if b.get("remove"):
''', "porders_s454: api_qty -- the reason, refused on a card with a draft"))
    E.append((f, r'''        con.execute("INSERT INTO s454_line_edit (src, ref, item, qty, removed, by, at) VALUES (?,?,?,?,1,?,?) ON CONFLICT(src, ref, item) DO UPDATE SET removed=1, by=excluded.by, at=excluded.at",
                    (src, ref, item, None, who(u), OS.now_iso()))
        OS.audit(con, who(u), "s454_line_removed", ref, dict(src=src, item=item))
''', r'''        con.execute("INSERT INTO s454_line_edit (src, ref, item, qty, removed, by, at, reason) VALUES (?,?,?,?,1,?,?,?) ON CONFLICT(src, ref, item) DO UPDATE SET "
                    "removed=1, by=excluded.by, at=excluded.at, reason=excluded.reason", (src, ref, item, None, who(u), OS.now_iso(), reason))
        if src == "carry":                                    # S619: a carried line removed (either reason) is dropped
            con.execute("UPDATE order_carry SET dropped_at=?, dropped_by=? WHERE id=? AND done_at IS NULL AND dropped_at IS NULL", (OS.now_iso(), who(u), int(ref)))
        OS.audit(con, who(u), "s454_line_removed", ref, dict(src=src, item=item, reason=reason))
''', "porders_s454: api_qty stores the reason (s454_line_edit.reason); a carry dropped"))
    E.append((f, r'''    lim = {"order.sheet_max_age_days": (1, 60), "order.whatsapp_wait_min": (5, 600),
''', r'''    if key == "order.deliver_skip":                           # S619: the five settings of the order list
        ds = [x.strip().upper() for x in v.split(",") if x.strip()]
        return all(x in ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN") for x in ds), ",".join(ds)
    if key == "order.deliver_window":
        parts = [x.strip() for x in v.split(",") if x.strip()]
        return bool(parts) and all(re.match(r"^(\d{1,2}:\d\d)?-(\d{1,2}:\d\d)?$", x) for x in parts), ",".join(parts)
    if key == "order.wa_delivery_line":
        return 0 < len(v) <= 200 and not re.search(r"\d{7,}", v), v
    if key == "order.track_since":
        return bool(re.match(r"^\d{4}-\d\d-\d\d$", v)), v
    lim = {"order.sheet_max_age_days": (1, 60), "order.whatsapp_wait_min": (5, 600),
''', "porders_s454: _valid -- the S619 settings"))
    E.append((f, r'''           "purchase.entry_wait_days": (1, 60), "stock.gap_min_packs": (0, 100)}.get(key)
''', r'''           "purchase.entry_wait_days": (1, 60), "stock.gap_min_packs": (0, 100), "order.deliver_days": (0, 7)}.get(key)
''', "porders_s454: _valid -- order.deliver_days 0..7"))
    E.append((f, r'''    OS.audit(con, who(u), "s618_rescan_withdrawn", aid, dict(kit="S618"))
    con.commit()
    return jsonify(ok=True)
# ---- S618 end ---------------------------------------------------------------------------------------------------------------------------
''', r'''    OS.audit(con, who(u), "s618_rescan_withdrawn", aid, dict(kit="S618"))
    con.commit()
    return jsonify(ok=True)
# ---- S618 end ---------------------------------------------------------------------------------------------------------------------------
''' + block(kit, "s619_p4_block.txt"), "porders_s454: the call row's page, the order list, the words (at the end)"))
    # ============================================================================================== darpan_kal.py
    f = "darpan_kal.py"
    E.append((f, r'''# ------------------------------------------------------------------ api: the day
def _day_payload(con, iso, who):
''', r'''def _s619_line_safe(con, iso):
    """S619: one read-only line -- the goods of the last order day on or before the viewed date, dated (order_track, finance.db only); never breaks the page."""
    try:
        import order_sheet                                   # noqa: PLC0415
        import order_track                                   # noqa: PLC0415
        return order_track.darpan_line(con, iso, order_sheet.now())
    except Exception as e:                                   # noqa: BLE001
        return dict(ok=False, text="", lines=[], error=str(e)[:80])


def _s619_yday(con, oid, status):
    """S619: his order tab's 'माल आया' / 'अभी नहीं आया' from order_track's light half (the same reader as his day line)."""
    try:
        import order_sheet                                   # noqa: PLC0415
        import order_track                                   # noqa: PLC0415
        return order_track.yesterday_state(con, oid, order_sheet.now())
    except Exception:                                        # noqa: BLE001
        return "arrived" if status == "received" else "ordered"


# ------------------------------------------------------------------ api: the day
def _day_payload(con, iso, who):
''', "darpan_kal: _s619_line_safe and _s619_yday"))
    E.append((f, r'''                order_sheet=_s454_sheet_safe(con))             # S454 (D666): his order sheet -- taken, or refused
''', r'''                order_sheet=_s454_sheet_safe(con),             # S454 (D666): his order sheet -- taken, or refused
                order_track=_s619_line_safe(con, iso))         # S619: one read-only line -- the last order day's goods
''', "darpan_kal: the day payload carries the order line"))
    E.append((f, r'''        for o in con.execute("SELECT vendor, supplier_norm, status, created_at, received_at FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') "
''', r'''        for o in con.execute("SELECT vendor, supplier_norm, status, created_at, received_at, id FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') "
''', "darpan_kal: _s485_yesterday reads the order's id"))
    E.append((f, r'''            out.append(dict(display=OR._short(o[0]), vendor=o[0], state="arrived" if o[2] == "received" else "ordered", at=_s485_hhmm(o[3])))
''', r'''            out.append(dict(display=OR._short(o[0]), vendor=o[0], state=_s619_yday(con, o[5], o[2]), at=_s485_hhmm(o[3])))   # S619: order_track
''', "darpan_kal: his order tab reads order_track"))
    # ============================================================================================== darpan_kal.html
    f = "darpan_kal.html"
    E.append((f, r''' h+=ordersTodaySec(j.orders_today); /* S410 (D626): Aaj ke order -- N (M bheja) */
''', r''' h+=ordersTodaySec(j.orders_today); /* S410 (D626): Aaj ke order -- N (M bheja) */
 h+=orderTrackSec(j.order_track);   /* S619: one read-only line -- the last order day's goods; nothing to tap */
''', "darpan_kal.html: the order line after Aaj ke order"))
    E.append((f, r'''/* S403 (D618): 'Orthotic kam hai -- N'. S605 (D749): the lines put to him -- हटाओ on each, then हाँ, ऑर्डर में डालो / इस बार नहीं;
''', r'''/* S619: 'dd-mm ke order: ...' -- order_track.darpan_line, dated (never 'Kal'); read only */
function orderTrackSec(o){
 if(!o||!o.ok||!o.text) return "";
 return sec('<div class="row" id="orderTrack"><span class="k">Order ka maal</span></div>'+(o.lines||[o.text]).map(t=>'<div class="'+(o.state==="late"?"amber":(o.state==="all"?"ok":"muted"))+'">'+esc(t)+'</div>').join(""));
}
/* S403 (D618): 'Orthotic kam hai -- N'. S605 (D749): the lines put to him -- हटाओ on each, then हाँ, ऑर्डर में डालो / इस बार नहीं;
''', "darpan_kal.html: orderTrackSec"))
    # ============================================================================================== order_sheet_pdf.py
    f = "order_sheet_pdf.py"
    E.append((f, r'''#  build(con, lay=None, now=None): now is the print's moment (the route's one clock; order_sheet.now() when not given).
''', r'''#  build(con, lay=None, now=None): now is the print's moment (the route's one clock; order_sheet.now() when not given).
#
#  S619_ORDER_TRACKER (22-Oct-2026): order.wa_delivery_line once in every page's foot (the FOOT lines, measured by _foot_h); a carried line (a
#  medicine that did not come, on its dealer's next card -- entries(), the same reader the screen uses) prints 'pichhle order se baaki (dd-mm)';
#  a line removed 'Dealer ke paas nahi hai' prints 'dealer ke paas nahi' with no Order box (never 'order karna hai').
''', "order_sheet_pdf: the header names S619"))
    E.append((f, r'''def _old_row(l):
    """S543: an old line of Marg's open order -- Marg's pending quantity, its day and its one word."""
''', r'''def _old_row(l):
    """S543: an old line of Marg's open order -- Marg's pending quantity, its day and its one word."""
    if l.get("dealer_no"):                                    # S619: removed 'Dealer ke paas nahi hai' -- printed so, no Order box
        return dict(item=l["item"], pack=(l["packing"] or "").rstrip("."), qty=OS.qty_of(l), kind="dealer_no", ticked=False, aaya=False, marg=True,
                    tag="dealer ke paas nahi")
''', "order_sheet_pdf: a dealer_no line's row"))
    E.append((f, r'''    oo = OS.open_order(con)
    G = oo["groups"]
''', r'''    DELIVERY[0] = OS.setting(con, "order.wa_delivery_line")   # S619: the page foot, once
    oo = OS.open_order(con)
    G = oo["groups"]
''', "order_sheet_pdf: layout reads the delivery line"))
    E.append((f, r'''                                                             qty=OS.qty_of(l), kind=k, ticked=False, aaya=False, marg=False, tag=""))
''', r'''                                                             qty=OS.qty_of(l), kind=k, ticked=False, aaya=False, marg=False,
                                                             tag=(("pichhle order se baaki (%s)" % OS.ddmm(l.get("carry_from"))) if l["src"] == "carry" else "")))
''', "order_sheet_pdf: a carried line's tag"))
    E.append((f, r'''    olds = G["old"] if print_old else []
''', r'''    olds = G["old"] if print_old else [x for x in G["old"] if x.get("dealer_no")]   # S619: a dealer_no line prints whatever print_old says
''', "order_sheet_pdf: dealer_no lines always print"))
    E.append((f, r'''    ga, gd, gb, gc = (len(G[k]) for k in ("to_order", "in_line", "ordered", "old"))
''', r'''    ga, gd, gb = (len(G[k]) for k in ("to_order", "in_line", "ordered"))
    gn = sum(1 for x in G["old"] if x.get("dealer_no"))       # S619: 'dealer ke paas nahi' is not old pending
    gc = len(G["old"]) - gn
''', "order_sheet_pdf: the head counts dealer_no apart"))
    E.append((f, r'''                                (gc, "%d purane pending" % gc)) if n]
''', r'''                                (gc, "%d purane pending" % gc), (gn, "%d dealer ke paas nahi" % gn)) if n]
''', "order_sheet_pdf: the head names dealer_no"))
    E.append((f, r'''def _foot_lines():
    return wrap(FOOT1, FOOT1_SZ, RM - LM), wrap(FOOT2, FOOT2_SZ, RM - LM)
''', r'''DELIVERY = [""]                                             # S619: order.wa_delivery_line, set by layout() (once in every page's foot)


def _foot_lines():
    f1 = wrap(FOOT1, FOOT1_SZ, RM - LM)
    if DELIVERY[0]:
        f1 = f1 + wrap(DELIVERY[0], FOOT1_SZ, RM - LM)
    return f1, wrap(FOOT2, FOOT2_SZ, RM - LM)
''', "order_sheet_pdf: the delivery line in the FOOT lines (_foot_h measures it)"))
    E.append((f, r'''                for i in ((4,) if r["kind"] == "old" else (3, 4)):
''', r'''                for i in ((4,) if r["kind"] in ("old", "dealer_no") else (3, 4)):
''', "order_sheet_pdf: no Order box on a dealer_no row"))
    # ============================================================================================== marg_order_pdf.py
    f = "marg_order_pdf.py"
    E.append((f, r'''#  (porders_s454.nums_text, the one builder; book_card, the one reader; _latin folds it as every PDF string).
''', r'''#  (porders_s454.nums_text, the one builder; book_card, the one reader; _latin folds it as every PDF string).
#  S619 (the owner, 22-Oct): order.wa_delivery_line once, after Marg's last row, inside the floor check (Marg's rows as Marg printed them).
''', "marg_order_pdf: the header names S619"))
    E.append((f, r'''    if p is None:
        p, y = new_page()
        _draw_row(p, y, heads, ws, True, 0.86)
    pages.append(p)
''', r'''    if p is None:
        p, y = new_page()
        y -= _draw_row(p, y, heads, ws, True, 0.86)
    dl = OS.setting(con, "order.wa_delivery_line")             # S619: once, after Marg's last row, inside the floor check
    if dl:
        if y - _book_h(dl, ws) < floor:
            pages.append(p)
            p, y = new_page()
        y -= _draw_book(p, y, dl)
    pages.append(p)
''', "marg_order_pdf: the delivery line once after the last row"))
    return E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--out", required=True)
    ap.add_argument("--kit", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    src = {}
    for n in FROM:
        p = os.path.join(a.finance, n)
        with open(p, "rb") as fh:
            raw = fh.read()
        if md5b(raw) != FROM[n]:
            print("STOP: %s is %s, not its FROM pin %s -- it changed after the brief; nothing written" % (p, md5b(raw), FROM[n]))
            return 2
        src[n] = raw.decode("utf-8")
    for f, anchor, new, what in edits(a.kit):
        c = src[f].count(anchor)
        if c != 1:
            print("STOP: the anchor for '%s' occurs %d times in %s (must be once) -- nothing written" % (what, c, f))
            return 3
        src[f] = src[f].replace(anchor, new, 1)
        print("  %-18s anchored once, applied: %s" % (f, what))
    os.makedirs(a.out, exist_ok=True)
    for n, text in src.items():
        with open(os.path.join(a.out, n), "wb") as fh:
            fh.write(text.encode("utf-8"))
    with open(os.path.join(a.kit, "order_track.py"), "rb") as fh:
        ot = fh.read()
    with open(os.path.join(a.out, "order_track.py"), "wb") as fh:
        fh.write(ot)
    for n in sorted(list(src) + ["order_track.py"]):
        with open(os.path.join(a.out, n), "rb") as fh:
            print("BUILT %-18s %s" % (n, md5b(fh.read())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
