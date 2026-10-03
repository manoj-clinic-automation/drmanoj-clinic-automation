#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s454p1.py -- kit S454_BILL_REGISTER, part 1: builds the live files it changes from the LIVE bytes (CLAUDE.md rule 2).

Each live file is checked against its FROM pin (the brief's 03-Oct bundle, read live) and every edit is anchored -- its anchor must occur
EXACTLY once, else the build stops and writes nothing. The blocks the kit appends live beside this file. The three new modules
(order_sheet.py, porders_s454.py, order_sheet_pdf.py) are copied as they are.

    make_s454p1.py --finance /root/finance --marg /root/marg_ingest --out DIR
"""
import argparse
import hashlib
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {
    "porders.py": "3620b374a8fb3ac4988b8e6525795f84",
    "order_rules.py": "00a60efb515972313839662ff7f83495",
    "supplier_msg.py": "5cc35d2af444b5ab1996f636db8e54cf",
    "purchase_app.py": "341c663e52076f0ee264c356b49cf49e",
    "darpan_kal.py": "377ffd63786261cef4a6113482d43bb5",
    "darpan_kal.html": "9269afb04a454b626895a27666032752",
    "marg_take.py": "21e37b0e6fa6505a8825b32b7c24d41d",
    "signatures.json": "b2dcb2115a208bff81fac1c37c839428",
}
MARG_FILES = ("marg_take.py", "signatures.json")
NEW = ("order_sheet.py", "porders_s454.py", "order_sheet_pdf.py")
E = {}


def edit(f, old, new):
    E.setdefault(f, []).append((old, new))


# ------------------------------------------------------------------ porders.py
edit("porders.py",
     '        print("order_rules NOT mounted: %s" % _ex_or, file=sys.stderr)\n    return bp\n',
     '        print("order_rules NOT mounted: %s" % _ex_or, file=sys.stderr)\n'
     '    try:                                                      # S454 (D666 / D668): the one-task reception screens; fail-soft\n'
     '        import porders_s454                                   # noqa: PLC0415\n'
     '        porders_s454.init(app)\n'
     '    except Exception as _ex_s454:                             # noqa: BLE001\n'
     '        print("porders_s454 NOT mounted: %s" % _ex_s454, file=sys.stderr)\n'
     '    return bp\n')
edit("porders.py",
     '    login = str(u.get("login") or u.get("user") or "").lower()\n    with open(PAGE, encoding="utf-8") as fh:\n        html = fh.read()\n',
     '    login = str(u.get("login") or u.get("user") or "").lower()\n'
     '    if _s454_simple(con) and request.args.get("old") != "1" and kind in ("owner", "sender"):    # S454: the one-task screens; ?old=1 = this page\n'
     '        import porders_s454                                   # noqa: PLC0415\n'
     '        return porders_s454.home()\n'
     '    with open(PAGE, encoding="utf-8") as fh:\n        html = fh.read()\n'
     '    html = _s454_old_page(con, kind, html)                    # S454: the owner\'s ordering cards and the settings card, above the old page\n')
edit("porders.py",
     '        out.extend(_s440_owner_lines(con))                        # S440 (D640): a paper amount reception could not settle\n',
     '        out.extend(_s440_owner_lines(con))                        # S440 (D640): a paper amount reception could not settle\n'
     '        out.extend(_s454_owner_lines(con))                        # S454 (7.3): the owner\'s lines about ordering\n')
edit("porders.py",
     '    pa = _pa()\n    for o in con.execute("SELECT id, vendor, received_at, total_p FROM purchase_order WHERE status=\'received\' ORDER BY id DESC LIMIT 40"):\n'
     '        vn = pa.supplier_key(o[1])\n',
     '    pa = _pa()\n    tied = _s454_tied(con)                                    # S454 (D668): an order whose bill\'s scan is tied to it asks for no scan\n'
     '    for o in con.execute("SELECT id, vendor, received_at, total_p FROM purchase_order WHERE status=\'received\' ORDER BY id DESC LIMIT 40"):\n'
     '        if o[0] in tied:\n            continue\n'
     '        vn = pa.supplier_key(o[1])\n')
edit("porders.py",
     '        else:                                                     # 5 -- nothing for a person to do\n'
     '            note = ("Number / amount nahi padha gaya — manager isse theek karega, dobara scan mat karo" if why == "no_digits"\n',
     '        else:                                                     # 5 -- nothing for a person to do\n'
     '            if _s454_unread(s, sid):                              # S454 (4.7, F-695): a paper with nothing read is a question, never "wait"\n'
     '                continue\n'
     '            note = ("Number / amount nahi padha gaya — dobara scan mat karo" if why == "no_digits"\n')
edit("porders.py",
     'note_en=("OCR read no number / amount — the manager corrects it" if why == "no_digits"',
     'note_en=("OCR read no number / amount" if why == "no_digits"')

edit("porders.py",
     '        b = unscanned_bills(con)\n        if b:\n            out.append(dict(cls="warn", target="porders", text="Bill scan pending on %d purchase bill%s%s" % (\n',
     '        b = [x for x in unscanned_bills(con) if _s454_counted(con, x["bill_date"])]     # S454 (4.8): a parked month raises no Needs-you\n'
     '        if b:\n            out.append(dict(cls="warn", target="porders", text="Bill scan pending on %d purchase bill%s%s" % (\n')

edit("porders.py",
     '''                             "WHERE o.status='sent' AND o.vendor=? AND l.supplied IS NULL AND COALESCE(l.missing,0)=0", (vendor,)):\n''',
     '''                             "WHERE (o.status='sent'" + _s454_or_arrived(con) + ") AND o.vendor=? AND l.supplied IS NULL AND COALESCE(l.missing,0)=0",\n'''
     '''                             (vendor,)):                   # S454 (4.4): arrived by its bill's scan = counted until Marg answers\n''')

# ------------------------------------------------------------------ order_rules.py
edit("order_rules.py",
     '''                           "WHERE o.status='sent' AND o.created_at>=? AND l.supplied IS NULL AND COALESCE(l.missing,0)=0", (since,)).fetchall()\n''',
     '''                           "WHERE (o.status='sent'" + _s454_or_arrived(con) + ") AND o.created_at>=? AND l.supplied IS NULL AND COALESCE(l.missing,0)=0",\n'''
     '''                           (since,)).fetchall()            # S454 (4.4): arrived by its bill's scan = on the way until Marg answers\n''')
edit("order_rules.py",
     '''def tick(con, now=None):
    """The one cron line's worker: 05:30 nightly · 09:00 prepare + notice · 12:00 / 15:00 / 17:00 reminders; else nothing."""
    now = now or dt.datetime.now()
    forced = os.environ.get("ORDER_TICK", "")
    slot = forced
    if not slot:
        hm = (now.hour, now.minute)
        if hm == SLOTS["nightly"]:
            slot = "nightly"
        elif hm == SLOTS["prepare"]:
            slot = "prepare"
        elif hm in SLOTS["remind"]:
            slot = "remind%d" % now.hour
    today = _today()
    if slot == "nightly":
        return dict(slot=slot, **nightly(con, today))
    if slot == "prepare":
        made = prepare_day(con, today)
        return dict(slot=slot, made=made, notice=send_notice(con, today, "prepare"))
    if slot.startswith("remind"):
        return dict(slot=slot, notice=send_notice(con, today, slot))
    return dict(slot="none")
''',
     '''def tick(con, now=None):
    """The one cron line's worker (S454: every ten minutes, 05:00-21:50): 05:30 nightly · 09:00 prepare (its notice only on
    order.source = system) · the ONE reminder of the day at order.remind_times; and on every tick the order sheet's own work that must
    not wait for a page (order_sheet.cron_pass: the sheets the door took, the WhatsApp line, Marg's clearing, the bill-scan tie)."""
    now = now or dt.datetime.now()
    forced = os.environ.get("ORDER_TICK", "")
    slot = forced
    if not slot:
        hm = (now.hour, now.minute)
        if hm == SLOTS["nightly"]:
            slot = "nightly"
        elif hm == SLOTS["prepare"]:
            slot = "prepare"
    today = _today()
    s454 = _s454_pass(con)                                    # S454: before the notices, so the reminder names what is still due
    if slot == "nightly":
        return dict(slot=slot, s454=s454, **nightly(con, today))
    if slot == "prepare":
        made = prepare_day(con, today)
        return dict(slot=slot, made=made, s454=s454, notice=(send_notice(con, today, "prepare") if _s454_source(con) == "system"
                                                              else dict(ok=True, silent=True, slot="0900", why="order.source = marg_sheet")))
    if slot.startswith("remind"):                             # a walk's forced slot: the one reminder at its own hour; 12:00 / 15:00 are gone
        return dict(slot=slot, s454=s454, notice=_s454_remind(con, today, now, force=slot))
    return dict(slot="none", s454=s454, notice=_s454_remind(con, today, now))
''')
edit("order_rules.py",
     '        for p in con.execute("SELECT supplier_norm, vendor, MIN(day), merged_into FROM order_proposal WHERE status=\'merged\' AND merged_into<=? GROUP BY supplier_norm", (today.isoformat(),)):\n',
     '        for p in (con.execute("SELECT supplier_norm, vendor, MIN(day), merged_into FROM order_proposal WHERE status=\'merged\' AND merged_into<=? GROUP BY supplier_norm",\n'
     '                              (today.isoformat(),)) if _s454_source(con) == "system" else ()):    # S454: on marg_sheet the proposals reach no one\n')
edit("order_rules.py",
     '    """Darpan\'s card line and any other page: {ok, n, sent, unsent, text, url}. Fail-soft."""\n    try:\n        d = day_state(con)\n',
     '    """Darpan\'s card line and any other page: {ok, n, sent, unsent, text, url}. Fail-soft."""\n    try:\n'
     '        if _s454_source(con) == "marg_sheet":                 # S454: while the sheet decides, the sheet\'s suppliers still to be ordered\n'
     '            import order_sheet                                # noqa: PLC0415\n'
     '            return order_sheet.day_summary(con)\n'
     '        d = day_state(con)\n')

# ------------------------------------------------------------------ supplier_msg.py
edit("supplier_msg.py",
     'def ensure(con):\n    for d in DDL:\n        con.execute(d)\n    con.commit()\n',
     'def ensure(con):\n    for d in DDL:\n        con.execute(d)\n    _s454_cols(con)                                            # S454 (F-702): handed_at\n    con.commit()\n')
edit("supplier_msg.py",
     '    sql = "SELECT id, month, vendor_norm, vendor, kind, ref, status, queued_at, sent_at, sent_by, attempts, last_error, last_try_at FROM supplier_msg"\n'
     '    args = ()\n    if month:\n        sql += " WHERE month=?"\n',
     '    sql = ("SELECT id, month, vendor_norm, vendor, kind, ref, status, queued_at, sent_at, sent_by, attempts, last_error, last_try_at FROM supplier_msg"\n'
     '           " WHERE kind IN (\'neft\',\'cheque\')")                # S454: the payment messages only -- an order message is the order screen\'s\n'
     '    args = ()\n    if month:\n        sql += " AND month=?"\n')
edit("supplier_msg.py",
     '    cut = (_now() - dt.timedelta(minutes=RETRY_MIN)).isoformat()\n'
     '    r = con.execute("SELECT id, to_number, body FROM supplier_msg WHERE to_number IS NOT NULL AND attempts<? AND "\n'
     '                    "(status=\'queued\' OR (status=\'failed\' AND (last_try_at IS NULL OR last_try_at<=?))) ORDER BY queued_at, id LIMIT 1",\n'
     '                    (MAX_ATTEMPTS, cut)).fetchone()\n'
     '    if not r:\n        return jsonify({}), 200\n',
     '    cut = (_now() - dt.timedelta(minutes=RETRY_MIN)).isoformat()\n'
     '    gap = (_now() - dt.timedelta(minutes=_s454_gap(con))).isoformat()      # S454 (F-702): a message handed out is not handed again within the gap\n'
     '    r = con.execute("SELECT id, to_number, body FROM supplier_msg WHERE to_number IS NOT NULL AND attempts<? AND (handed_at IS NULL OR handed_at<=?) AND "\n'
     '                    "(status=\'queued\' OR (status=\'failed\' AND kind<>\'order\' AND (last_try_at IS NULL OR last_try_at<=?))) ORDER BY queued_at, id LIMIT 1",\n'
     '                    (MAX_ATTEMPTS, gap, cut)).fetchone()\n'
     '    if not r:\n        return jsonify({}), 200\n'
     '    con.execute("UPDATE supplier_msg SET handed_at=? WHERE id=?", (_iso(), r["id"]))\n    con.commit()\n')
edit("supplier_msg.py",
     '        con.execute("UPDATE supplier_msg SET status=\'failed\', attempts=attempts+1, last_error=?, last_try_at=? WHERE id=?", (errt or "phone said no", _iso(), mid))\n'
     '    con.commit()\n',
     '        con.execute("UPDATE supplier_msg SET status=\'failed\', attempts=attempts+1, last_error=?, last_try_at=? WHERE id=?", (errt or "phone said no", _iso(), mid))\n'
     '    con.commit()\n'
     '    _s454_done(con, mid, ok, errt)                       # S454: an order message sent makes its supplier ORDERED; one failed is withdrawn\n')
edit("supplier_msg.py",
     '        wait = int(con.execute("SELECT COUNT(*) FROM supplier_msg WHERE status IN (\'queued\',\'failed\') AND to_number IS NOT NULL").fetchone()[0])\n',
     '        wait = int(con.execute("SELECT COUNT(*) FROM supplier_msg WHERE status IN (\'queued\',\'failed\') AND to_number IS NOT NULL AND kind IN (\'neft\',\'cheque\')").fetchone()[0])   # S454\n')
edit("supplier_msg.py",
     'WhatsApp mein khol kar bhej deta hai, aur server ko bata deta hai "ho gaya". Aapko kuch type nahi karna.</p>\n',
     'WhatsApp mein khol kar bhej deta hai, aur server ko bata deta hai "ho gaya". Aapko kuch type nahi karna.</p>\n'
     '<p>S454: supplier ko <b>medicine ka order</b> bhi isi raste se jaata hai (Purchase orders par "Sab ko WhatsApp bhejo"). Har message ke baad phone '
     '<b>turant dobara poochhe</b>, jab tak jawab khaali (<code>{}</code>) na aaye — tabhi das message ek-do minute mein chale jaate hain.</p>\n')
edit("supplier_msg.py",
     '<li><b>End If</b>.</li>\n',
     '<li><b>End If</b>.</li>\n'
     '<li><b>S454:</b> agar message mila tha (<code>resp</code> mein <code>"id"</code> tha) to <b>turant step 1 se phir chalaiye</b> (MacroDroid: <i>Repeat Actions</i> / '
     '<i>While</i> loop), jab tak jawab khaali na ho. Ek message server do baar nahi deta: diya hua message 10 minute tak dobara nahi milta.</li>\n')

# ------------------------------------------------------------------ purchase_app.py
edit("purchase_app.py",
     '        r = acon.execute("SELECT COUNT(*), COALESCE(MAX(id),0) FROM bills WHERE kind=\'Pharmacy\'").fetchone()\n'
     '        return "%d:%d" % (r[0], r[1])\n',
     '        r = acon.execute("SELECT COUNT(*), COALESCE(MAX(id),0) FROM bills WHERE kind=\'Pharmacy\'").fetchone()\n'
     '        import hashlib as _h_s454                                  # noqa: PLC0415 -- S454 (D668): a supplier / number / amount filled in later\n'
     '        z = _h_s454.md5()                                          # (the OCR is a background job) changes the fingerprint too\n'
     '        for x in acon.execute("SELECT id, COALESCE(vendor,\'\'), COALESCE(bill_no,\'\'), COALESCE(total_amount,\'\'), COALESCE(status,\'\') "\n'
     '                              "FROM bills WHERE kind=\'Pharmacy\' ORDER BY id"):\n'
     '            z.update(("%s|%s|%s|%s|%s\\n" % tuple(x)).encode("utf-8", "replace"))\n'
     '        return "%d:%d:%s" % (r[0], r[1], z.hexdigest()[:12])\n')
edit("purchase_app.py",
     '        sel = ["id", "stamp_no", "vendor", "bill_no", "bill_date", "created_at"] + [c for c in ("dup_of", "submitted_by", "scanned_by", "created_by") if c in cols]\n',
     '        sel = ["id", "stamp_no", "vendor", "bill_no", "bill_date", "created_at", "total_amount"] + [c for c in ("dup_of", "submitted_by", "scanned_by", "created_by") if c in cols]   # S454: the amount read\n')
edit("purchase_app.py",
     '        elif why == "vendor_unknown" and not chosen:\n            reason = "supplier unread"\n        sup = None\n',
     '        elif why == "vendor_unknown" and not chosen:\n            reason = "supplier unread"\n'
     '        if reason is None and _s454_unread_row(r):                  # S454 (4.7, F-695): a paper with nothing read is never Amir\'s\n'
     '            reason = "unread paper"\n'
     '        sup = None\n')

# ------------------------------------------------------------------ darpan_kal.py / .html
edit("darpan_kal.py",
     '                amir_claims=_s446_claims(con))                 # S446 (D648): Amir\'s supplier claims -- Darpan\'s queue\n',
     '                amir_claims=_s446_claims(con),                 # S446 (D648): Amir\'s supplier claims -- Darpan\'s queue\n'
     '                order_sheet=_s454_sheet_safe(con))             # S454 (D666): his order sheet -- taken, or refused\n')
edit("darpan_kal.html",
     ' h+=orthoShortSec(j.ortho_short);   /* S403 (D618): Orthotic kam hai -- N */\n',
     ' h+=orderSheetSec(j.order_sheet);   /* S454 (D666): Order sheet -- mil gayi / adhoori; the one instruction */\n'
     ' h+=orthoShortSec(j.ortho_short);   /* S403 (D618): Orthotic kam hai -- N */\n')
edit("darpan_kal.html",
     "/* S410 (D626): 'Aaj ke order -- N (M bheja)' -- the count line; opens the Purchase orders screen */\n",
     "/* S454 (D666): his order sheet -- when the newest came, how many medicines and suppliers, that reception has it; or that it was refused.\n"
     "   Always the one instruction under it. */\n"
     "function orderSheetSec(o){\n"
     " if(!o||!o.ok) return \"\";\n"
     " let t='<div class=\"row\"><span class=\"k\"><b>Order sheet</b></span></div>';\n"
     " if(o.refused) t+='<div class=\"bad\">Order sheet adhoori thi, system ne nahi li</div><div class=\"muted\">Marg se dobara TEXT mein save kijiye.</div>';\n"
     " else if(o.sheet) t+='<div><b>'+esc(o.sheet.date)+' ki sheet mil gayi</b></div><div class=\"muted\">'+o.sheet.dawa+' dawa · '+o.sheet.suppliers+' supplier · reception ke paas pahunch gayi</div>';\n"
     " t+='<div class=\"muted\" style=\"margin-top:6px\">Marg mein order banane ke baad report ko TEXT mein save kijiye, jaise stock report save hoti hai. Naam badalne ki zaroorat nahi.</div>';\n"
     " return sec(t);\n"
     "}\n"
     "/* S410 (D626): 'Aaj ke order -- N (M bheja)' -- the count line; opens the Purchase orders screen */\n")

# ------------------------------------------------------------------ marg_take.py (/root/marg_ingest)
edit("marg_take.py",
     '            if typ == "STOCK_CLOSING" and verdict == "VERIFIED":                    # S404 (D620, F-529)\n'
     '                _rename_verify(con, dest if (dest and os.path.exists(dest)) else local, md5, stamp)\n',
     '            if typ == "STOCK_CLOSING" and verdict == "VERIFIED":                    # S404 (D620, F-529)\n'
     '                _rename_verify(con, dest if (dest and os.path.exists(dest)) else local, md5, stamp)\n'
     '            if typ == "ORDER_PENDING" and verdict == "VERIFIED":                    # S454 (D666): Darpan\'s order sheet, loaded at once\n'
     '                _order_sheet(db, dest if (dest and os.path.exists(dest)) else local, md5, sname, source, stamp)\n')
edit("marg_take.py",
     '# ------------------------------------------------------------------ the door\n',
     'def _order_sheet(db, path, md5, name, source, stamp):\n'
     '    """S454 (D666): a VERIFIED pending-orders sheet has just been taken -- the order screen\'s loader (finance/order_sheet.py) reads it\n'
     '    at once, on its own connection (every page read is the fallback). Fail-soft: the door never refuses a file because of this."""\n'
     '    fin = os.path.join(os.path.dirname(HERE), "finance")\n'
     '    try:\n'
     '        if fin not in sys.path:\n'
     '            sys.path.insert(0, fin)\n'
     '        import order_sheet                                       # noqa: PLC0415\n'
     '        c2 = sqlite3.connect(db, timeout=30)\n'
     '        c2.row_factory = sqlite3.Row\n'
     '        try:\n'
     '            order_sheet.load_file(c2, path, md5, name, source, stamp)\n'
     '        finally:\n'
     '            c2.close()\n'
     '    except Exception as e:                                       # noqa: BLE001\n'
     '        print("marg_take: the order sheet was not loaded now (%s) -- the page loads it" % str(e)[:120], file=sys.stderr)\n'
     '\n\n'
     '# ------------------------------------------------------------------ the door\n')

APPEND = {"porders.py": "porders_block_s454.py", "order_rules.py": "order_rules_block_s454.py", "supplier_msg.py": "supplier_block_s454.py",
          "darpan_kal.py": "darpan_block_s454.py"}
INSERT_BEFORE = {"purchase_app.py": ('\n\nif __name__ == "__main__":\n    import sys as _sys_s439\n', "purchase_block_s454.py")}
SIG_ANCHOR = '    }\n  ],\n  "_EXAMPLE_adding_a_new_type"'


def md5b(b):
    return hashlib.md5(b).hexdigest()


def sig_insert(txt):
    """signatures.json: ONE new entry, ORDER_PENDING, after the last -- the anchor exactly once; the result must parse, the entry once."""
    if txt.count(SIG_ANCHOR) != 1:
        raise SystemExit("STOP: signatures.json -- the insertion anchor occurs %d times" % txt.count(SIG_ANCHOR))
    entry = open(os.path.join(HERE, "sig_entry_s454.json"), "rb").read().decode("utf-8").rstrip("\n")
    out = txt.replace(SIG_ANCHOR, "    },\n" + entry + "\n  ],\n  \"_EXAMPLE_adding_a_new_type\"", 1)
    j = json.loads(out)
    if [s["type"] for s in j["signatures"]].count("ORDER_PENDING") != 1:
        raise SystemExit("STOP: signatures.json -- ORDER_PENDING is not there exactly once")
    return out


def build(finance, marg, out, check_pins=True, only=None):
    os.makedirs(out, exist_ok=True)
    res = {}
    for f in FROM:
        if only and f not in only:
            continue
        src = os.path.join(marg if f in MARG_FILES else finance, f)
        raw = open(src, "rb").read()
        if check_pins and md5b(raw) != FROM[f]:
            raise SystemExit("STOP: %s is %s, not its FROM pin %s -- someone changed it since the brief; nothing written" % (src, md5b(raw), FROM[f]))
        txt = raw.decode("utf-8")
        for old, new in E.get(f, []):
            n = txt.count(old)
            if n != 1:
                raise SystemExit("STOP: %s -- an anchor occurs %d times (must be exactly once): %r" % (f, n, old[:90]))
            txt = txt.replace(old, new, 1)
        if f == "signatures.json":
            txt = sig_insert(txt)
        if f in APPEND:
            txt = txt.rstrip("\n") + "\n\n\n" + open(os.path.join(HERE, APPEND[f]), "rb").read().decode("utf-8").strip("\n") + "\n"
        if f in INSERT_BEFORE:
            anchor, blk = INSERT_BEFORE[f]
            if txt.count(anchor) != 1:
                raise SystemExit("STOP: %s -- the insertion anchor occurs %d times" % (f, txt.count(anchor)))
            txt = txt.replace(anchor, "\n\n\n" + open(os.path.join(HERE, blk), "rb").read().decode("utf-8").strip("\n") + "\n" + anchor, 1)
        if f.endswith(".html") and re.search("[\u0900-\u097f]", txt.split("function orderSheetSec")[1].split("/* S410")[0]):
            raise SystemExit("STOP: %s -- the new card carries Devanagari" % f)
        b = txt.encode("utf-8")
        with open(os.path.join(out, f), "wb") as fh:
            fh.write(b)
        res[f] = md5b(b)
        print("built %-17s %s -> %s  (%d edits%s)" % (f, FROM[f][:8], md5b(b), len(E.get(f, [])), ", block added" if (f in APPEND or f in INSERT_BEFORE) else ""))
    for f in NEW:
        if only and f not in only:
            continue
        shutil.copyfile(os.path.join(HERE, f), os.path.join(out, f))
        res[f] = md5b(open(os.path.join(out, f), "rb").read())
        print("new   %-17s %s" % (f, res[f]))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--marg", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-pins", action="store_true")
    a = ap.parse_args()
    build(a.finance, a.marg, a.out, check_pins=not a.no_pins)
