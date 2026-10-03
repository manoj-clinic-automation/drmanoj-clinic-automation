#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_dutymap_s454p1.py -- kit S454_BILL_REGISTER, part 1: DUTY_MAP v3 (S452) -> v4.

CLAUDE.md "Every duty has a door": the reception screen of S454 moves four duties onto its one-task home (Order karna hai · Maal aaya? ·
Bill scan karna hai · Photo dekh kar bataiye) and adds Darpan's one new step (save the order sheet as text); the NEFT backup line counts
the payment messages only. Each due_sql is ONE read-only SELECT returning (n, since), run on the live database before it is written in
(the installer's step 1 runs every one of them read-only and stops on an error).

    make_dutymap_s454p1.py --json <DUTY_MAP.json v3> --md <DUTY_MAP.md> --out DIR
"""
import argparse
import hashlib
import json
import os

FROM_JSON = "s452"
MARK = "S454_BILL_REGISTER"
SRC_SQL = ("SELECT CASE WHEN COALESCE((SELECT value FROM setting WHERE key = 'order.freeze'), '') <> '' THEN 0 "
           "WHEN COALESCE((SELECT value FROM setting WHERE key = 'order.source'), 'marg_sheet') = 'system' THEN "
           "(SELECT COUNT(DISTINCT p.supplier_norm) FROM order_proposal p WHERE p.day = date('now','localtime') AND p.status = 'open') "
           "ELSE (SELECT COUNT(DISTINCT l.supplier_norm) FROM order_sheet_line l WHERE l.state = 'to_order' AND NOT EXISTS (SELECT 1 FROM purchase_order o "
           "WHERE o.status = 'draft' AND o.order_src = 's454' AND o.supplier_norm = l.supplier_norm)) END AS n, "
           "(SELECT MIN(COALESCE(l.reorder_day, l.line_date)) FROM order_sheet_line l WHERE l.state = 'to_order') AS since")
ARRIVAL_SQL = ("SELECT COUNT(*) AS n, MIN(substr(o.created_at,1,10)) AS since FROM purchase_order o WHERE o.status = 'sent' "
               "AND NOT EXISTS (SELECT 1 FROM order_scan_tie t WHERE t.order_id = o.id)")
SCAN_SQL = ("SELECT (SELECT COUNT(*) FROM purchase_order o WHERE o.status = 'received' AND NOT EXISTS (SELECT 1 FROM order_scan_tie t WHERE t.order_id = o.id) "
            "AND substr(o.received_at,1,7) >= substr(COALESCE((SELECT value FROM setting WHERE key = 'purchase.register_from'), '2026-10-01'),1,7) "
            "AND date(substr(o.received_at,1,10)) > date('now','localtime','-' || COALESCE((SELECT value FROM setting WHERE key = 'purchase.arrival_scan_days'), '7') || ' days') "
            "AND NOT EXISTS (SELECT 1 FROM purchase_bill b WHERE b.supplier_norm = COALESCE(o.supplier_norm, o.vendor) AND b.bill_date >= substr(o.created_at,1,10) "
            "AND NOT EXISTS (SELECT 1 FROM purchase_scan_link k WHERE k.bill_id = b.id))) + "
            "(SELECT COUNT(*) FROM purchase_bill b WHERE b.month >= substr(COALESCE((SELECT value FROM setting WHERE key = 'purchase.register_from'), '2026-10-01'),1,7) "
            "AND EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND (e.md5 = b.bw_md5 OR e.md5 = b.sw_md5)) "
            "AND NOT EXISTS (SELECT 1 FROM purchase_scan_link k WHERE k.bill_id = b.id) AND NOT EXISTS (SELECT 1 FROM s454_paper_missing m WHERE m.bill_id = b.id) "
            "AND COALESCE(b.verdict,'') <> 'WRONG' AND NOT EXISTS (SELECT 1 FROM purchase_scan_state s WHERE s.likely_bill = b.id "
            "AND s.why IN ('number_differs','amount_differs','no_digits'))) AS n, "
            "(SELECT MIN(b.bill_date) FROM purchase_bill b WHERE b.month >= substr(COALESCE((SELECT value FROM setting WHERE key = 'purchase.register_from'), '2026-10-01'),1,7) "
            "AND NOT EXISTS (SELECT 1 FROM purchase_scan_link k WHERE k.bill_id = b.id)) AS since")
Q_SQL = ("SELECT COUNT(*) AS n, MIN(substr(s.checked_at,1,10)) AS since FROM purchase_scan_state s JOIN purchase_bill b ON b.id = s.likely_bill "
         "WHERE NOT EXISTS (SELECT 1 FROM purchase_scan_link k WHERE k.asset_bill_id = s.asset_bill_id) AND s.why IN ('number_differs','amount_differs','no_digits') "
         "AND NOT EXISTS (SELECT 1 FROM s454_scan_answer a WHERE a.asset_bill_id = s.asset_bill_id AND a.kind = 'pharmacy') "
         "AND COALESCE(b.month, substr(b.bill_date,1,7)) >= substr(COALESCE((SELECT value FROM setting WHERE key = 'purchase.register_from'), '2026-10-01'),1,7)")
SHEET_SQL = ("SELECT CASE WHEN COALESCE((SELECT MAX(received_at) FROM mi_file WHERE verdict <> 'VERIFIED' AND (type = 'ORDER_PENDING' OR reason LIKE '%ORDER_PENDING%' "
             "OR reason LIKE '%PENDING ORDERS%')), '') > COALESCE((SELECT MAX(received_at) FROM mi_file WHERE type = 'ORDER_PENDING' AND verdict = 'VERIFIED'), '') "
             "THEN 1 ELSE 0 END AS n, (SELECT MAX(received_at) FROM mi_file WHERE verdict <> 'VERIFIED' AND (type = 'ORDER_PENDING' OR reason LIKE '%ORDER_PENDING%' "
             "OR reason LIKE '%PENDING ORDERS%')) AS since")
NEFT_SQL = ("SELECT COUNT(*) AS n, MIN(substr(queued_at,1,10)) AS since FROM supplier_msg WHERE status IN ('queued','failed') AND kind IN ('neft','cheque') "
            "AND replace(queued_at,'T',' ') <= datetime('now','localtime','-30 minutes')")

CHANGE = {
    "reception.medicine_orders": dict(
        duty="Order from Darpan's order sheet (or, on order.source = system, the day's proposals): 'Sab ko WhatsApp bhejo', or call and tap 'Order ho gaya' -- "
             "S454 (D666): one card per supplier still to be ordered",
        duty_hi="Order karna hai", due_sql=SRC_SQL, door="/finance/porders", door_marker="Order karna hai", tile="Purchase orders",
        owner_line="Suppliers still to be ordered: {n} -- since {since}", coded="order_sheet.owner_lines (an order of the sheet never placed; a supplier with no number)",
        allowed_days=1),
    "reception.order_arrival": dict(
        duty="When goods come, scan the supplier's bill ('Naya bill scan karo' / 'Bill scan karo') -- the scan records the delivery by itself (S454, D668); "
             "'Bill nahi hai, ya kam aaya?' only when something came short",
        duty_hi="Maal aaya? -- bill scan karo", due_sql=ARRIVAL_SQL, door="/finance/porders", door_marker="Maal aaya?", tile="Purchase orders",
        owner_line="Orders made, goods not recorded: {n} -- oldest {since}", coded=None, allowed_days=7),
    "reception.bill_scan": dict(
        duty="Scan the paper of each bill still to scan: goods received with no bill scan, and Marg bills of a counted month with no scan (S454: "
             "purchase.register_from; earlier months behind 'Purana kaam', optional)",
        duty_hi="Bill scan karna hai", due_sql=SCAN_SQL, door="/finance/porders", door_marker="Bill scan karna hai", tile="Purchase orders",
        owner_line="Bill scan pending on {n} bill(s) -- oldest {since}", coded="porders.needs_you_lines", allowed_days=3),
    "reception.scan_questions": dict(
        duty="Answer the question about a scan, one at a time ('Photo dekh kar bataiye': is this the bill? the amount on the paper; whose bill; is it a "
             "pharmacy bill?) -- counted months",
        duty_hi="Photo dekh kar bataiye", due_sql=Q_SQL, door="/finance/porders", door_marker="Photo dekh kar bataiye", tile="Purchase orders",
        owner_line="Scan questions unanswered: {n} -- oldest {since} (reception)", coded=None, allowed_days=2),
    "shavez.supplier_messages": dict(due_sql=NEFT_SQL),
}
NEW = [dict(id="darpan.order_sheet", person="darpan", tile="Kal ka hisaab", door="/finance/darpan/kal", door_marker="Order sheet adhoori thi",
            duty="After making the order in Marg, save the report PENDING ORDERS (PURCHASE) as TEXT, the default way (S454, D666) -- due only when the newest "
                 "file was refused (save it again)",
            duty_hi="Order sheet TEXT mein save kijiye", due_sql=SHEET_SQL, owner_line="Darpan's order sheet refused -- since {since}",
            coded="order_sheet.owner_lines (refused today)", allowed_days=0)]

MD_EDITS = (
    ("by S452_AMIR_PANEL_FIXES (F-686, F-687; the owner's rulings of 02-Oct evening).**",
     "by S452_AMIR_PANEL_FIXES (F-686, F-687; the owner's rulings of 02-Oct evening); 03-Oct-2026 by S454_BILL_REGISTER part 1 (D666, D668, D669: the "
     "one-task reception screen, Darpan's order sheet).**"),
    ("| Send the orthotic order to Yuvika | orthotic shortage computed by porders (count + purchases − sales vs keep) | Purchase orders → /finance/porders; card \"Orthotic kam hai\" on Kal ka hisaab | Needs-you, porders: \"Orthotic shortages: N items -- order not sent\" |\n",
     "| Send the orthotic order to Yuvika | orthotic shortage computed by porders (count + purchases − sales vs keep) | Purchase orders → /finance/porders; card \"Orthotic kam hai\" on Kal ka hisaab | Needs-you, porders: \"Orthotic shortages: N items -- order not sent\" |\n"
     "| **S454:** after making the order in Marg, save PENDING ORDERS (PURCHASE) as TEXT, the default way `[darpan.order_sheet]` | due only when the newest order-sheet file was refused (`mi_file` not VERIFIED, ORDER_PENDING) and no later sheet was taken | Kal ka hisaab → card \"Order sheet\": \"<dd-mm> ki sheet mil gayi · N dawa · M supplier · reception ke paas pahunch gayi\", or \"Order sheet adhoori thi, system ne nahi li — Marg se dobara TEXT mein save kijiye\"; the one instruction always under it | Needs-you, order_sheet: \"Darpan's order sheet refused today\" |\n"),
    ("| Backup send of a supplier NEFT message unsent 30 min `[shavez.supplier_messages]` | `supplier_msg.status` queued / failed, queued 30+ min |",
     "| Backup send of a supplier NEFT message unsent 30 min `[shavez.supplier_messages]` | `supplier_msg.status` queued / failed, queued 30+ min, kind neft / cheque (S454: an order message is the order screen's) |"),
    ("| Scan every Marg purchase bill `[reception.bill_scan]` | `purchase_bill` from `porders.scan_from` (01-Sep), in a live export, with no `purchase_scan_link` | Purchase orders → /finance/porders \"Scan karo\" → Scan Purchase | Needs-you, porders: \"Bill scan pending on N purchase bills\" |\n"
     "| Answer \"Yahi bill hai?\" and \"Supplier chuno\" `[reception.scan_questions]` | `purchase_scan_state` unlinked with a likely bill, or vendor unknown and not chosen | Purchase orders \"Yahi bill hai?\" / \"Supplier chuno\" | JSON |\n"
     "| \"Amount milao\": type the paper's amount when scan and Marg differ | linked scan more than 2% from Marg, no `amount_state` (needs assets.db) | Purchase orders \"Amount milao\" | Needs-you, porders (when it goes to the owner) |\n"
     "| Send the day's medicine orders `[reception.medicine_orders]` | `order_proposal.status='merged'` due, no later 'sent' for the supplier | Purchase orders \"Aaj ke order\" | Needs-you, order_rules: \"Order not sent: …\" |\n"
     "| Send the orthotic order | porders' computed shortage | Purchase orders | Needs-you, porders |\n"
     "| Tap \"Order aaya?\" when goods arrive `[reception.order_arrival]` | `purchase_order.status='sent'` | Purchase orders \"Order aaya?\" | JSON |\n",
     "**S454 (03-Oct-2026, D666 / D668): the Purchase-orders tile opens \"Aaj ka kaam\" — the big \"Naya bill scan karo\" and a row for each kind of work, shown only while it has work.** "
     "The old page stays one tap away (`?old=1`, \"Purana page\" for the owner and Shavez).\n\n"
     "| Order from the suppliers still to be ordered `[reception.medicine_orders]` | `porders.simple`=1: Darpan's sheet lines `order_sheet_line.state='to_order'` (on `order.source`=system: today's open `order_proposal`); the orthotic shortage card (S403) beside them | Purchase orders → /finance/porders \"Order karna hai\" → a card per supplier: \"Sab ko WhatsApp bhejo\", \"Kholiye\" (Call karo, the number under it), \"Order ho gaya\" | Needs-you, order_sheet: a supplier with no number; an order of the sheet never placed; the phone silent while messages wait. One push a day at `order.remind_times` (17:00) naming those still to order |\n"
     "| When goods come, scan the bill `[reception.order_arrival]` | `purchase_order.status='sent'` with no bill scan tied (`order_scan_tie`) | Purchase orders \"Maal aaya?\" → \"Bill scan karo\" (the scan records the delivery by itself); \"Bill nahi hai, ya kam aaya?\" for a short delivery | JSON |\n"
     "| Scan each paper still to scan `[reception.bill_scan]` | orders received on the arrival screen with no bill scan (for `purchase.arrival_scan_days`), and Marg bills of a counted month (`purchase.register_from`) with no scan and no likely scan, not marked \"paper nahi mila\" | Purchase orders \"Bill scan karna hai\" → by supplier, five at a time, \"Scan karo\"; \"Koi paper nahi mil raha?\" | Needs-you, porders |\n"
     "| Answer the question about a scan `[reception.scan_questions]` | the matcher's questions (likely bill, amount, supplier), S441's, and \"is it a pharmacy bill?\" for a paper with nothing read — counted months | Purchase orders \"Photo dekh kar bataiye\" → one question on the screen, \"Sawaal i / N\" | JSON |\n"
     "| A parked month's work (optional) | `purchase.parked_months` (2026-09): its bills to scan and its questions | Purchase orders → \"Purana kaam: September\" at the foot of the home | none (no count, no reminder, no alert, nothing to Amir) |\n"),
)


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(jpath, mpath, out):
    d = json.load(open(jpath, encoding="utf-8"))
    if d.get("version") != 3 or d.get("kit") != "S452_AMIR_PANEL_FIXES":
        raise SystemExit("STOP: %s is not the v3 map of S452 -- nothing written" % jpath)
    ids = [x["id"] for x in d["duties"]]
    for k in CHANGE:
        if ids.count(k) != 1:
            raise SystemExit("STOP: duty %s occurs %d times" % (k, ids.count(k)))
    for x in d["duties"]:
        if x["id"] in CHANGE:
            x.update(CHANGE[x["id"]])
    for n in NEW:
        if n["id"] in ids:
            raise SystemExit("STOP: %s is there already" % n["id"])
        at = max(i for i, x in enumerate(d["duties"]) if x["person"] == n["person"])
        d["duties"].insert(at + 1, n)
    d["version"] = 4
    d["kit"] = MARK
    d["_note"] = d["_note"] + (" S454 (03-Oct-2026, part 1): the reception screen's one-task home -- reception.medicine_orders (Order karna hai: Darpan's sheet, "
                               "or on order.source=system the day's proposals), reception.order_arrival (Maal aaya?: an order with no bill scan tied), "
                               "reception.bill_scan (Bill scan karna hai: counted months only), reception.scan_questions (Photo dekh kar bataiye: counted "
                               "months); darpan.order_sheet added (Kal ka hisaab's 'Order sheet' card; due only when the newest sheet was refused); "
                               "shavez.supplier_messages counts the payment kinds only.")
    os.makedirs(out, exist_ok=True)
    bj = (json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    open(os.path.join(out, "DUTY_MAP.json"), "wb").write(bj)
    md = open(mpath, "rb").read().decode("utf-8")
    for old, new in MD_EDITS:
        if md.count(old) != 1:
            raise SystemExit("STOP: DUTY_MAP.md -- an anchor occurs %d times: %r" % (md.count(old), old[:80]))
        md = md.replace(old, new, 1)
    bm = md.encode("utf-8")
    open(os.path.join(out, "DUTY_MAP.md"), "wb").write(bm)
    print("built DUTY_MAP.json v4 %s · DUTY_MAP.md %s" % (md5b(bj), md5b(bm)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    build(a.json, a.md, a.out)
