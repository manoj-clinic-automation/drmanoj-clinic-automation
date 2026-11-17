#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s852.py -- kit S852_SMALL_FIXES (the parent, S474, 17-Nov-2026). Anchored patches on the LIVE bytes.

    python make_s852.py <live_dir> <out_dir>

owner_console.py fe5e915c  (AF-41) the approve-days line: the oldest day's age, and a day skipped between approved ones
parchi_desk.py   de24e3a4  (F-1430) the radd door refuses a name as the clinic ID, as the other doors (S844)
month_read.py    b2d30289  (F-1418) the Scan App's month by group: receipts, statements and summaries are not money, a challan
                           only when final, a page joined into another once, a credit note LESS (from the bill it is against)
Every FROM pin is checked; every anchor must occur exactly once."""
import hashlib, os, sys

LIVE, OUT = sys.argv[1:3]
FROM = {"owner_console.py": "fe5e915cd2b0329e5949748e102386e6", "parchi_desk.py": "de24e3a4", "month_read.py": "b2d30289fc109f1d919757a432c68079"}
P = {}

P["owner_console.py"] = [(
'''                elif d["id"] == "manoj.approve_days":
                    days = [dmy(r[0]) for r in con.execute(
                        "SELECT business_date FROM day_entry WHERE unit='medical' AND status IN ('submitted','draft') "
                        "ORDER BY business_date LIMIT 40")]
                    if days:
                        ln["who"] = ", ".join(days)
''',
'''                elif d["id"] == "manoj.approve_days":
                    wait = [str(r[0]) for r in con.execute(
                        "SELECT business_date FROM day_entry WHERE unit='medical' AND status IN ('submitted','draft') "
                        "ORDER BY business_date LIMIT 40")]
                    if wait:                                   # S852 (AF-41): the oldest day's age; a day passed over between approved ones
                        last_ok = str(con.execute("SELECT MAX(business_date) FROM day_entry WHERE unit='medical' "
                                                  "AND status IN ('approved','locked')").fetchone()[0] or "")
                        skipped = [x for x in wait if last_ok and x < last_ok]
                        bits = []
                        try:
                            age = (dt.date.fromisoformat(cx["today"]) - dt.date.fromisoformat(wait[0])).days
                            bits.append("the oldest has waited %d day%s" % (age, "" if age == 1 else "s"))
                        except Exception:                      # noqa: BLE001
                            pass
                        if skipped:
                            bits.append("passed over while later days were approved: %s" % ", ".join(dmy(x) for x in skipped))
                            ln["dot"] = "b"
                        ln["who"] = " · ".join(bits + [", ".join(dmy(x) for x in wait)])
''')]

P["parchi_desk.py"] = [(
'''        if p not in ("/finance/slips/save", "/finance/slips/blood", "/finance/slips/pending/new", "/finance/slips/pending/act"):''',
'''        if p not in ("/finance/slips/save", "/finance/slips/blood", "/finance/slips/pending/new", "/finance/slips/pending/act",
                     "/finance/slips/radd"):                   # S852 (F-1430): the radd door too'''), (
'''        elif p == "/finance/slips/pending/new":
            v = SL._clean_id(f.get("clinic_id"))
        else:''',
'''        elif p == "/finance/slips/pending/new":
            v = SL._clean_id(f.get("clinic_id"))
        elif p == "/finance/slips/radd":                     # S852 (F-1430): only where the door would WRITE the ID onto a
            v = SL._clean_id(f.get("clinic_id"))              # slip with none; a slip already carrying an ID is left as before
            try:
                had = _db().execute("SELECT clinic_id FROM slip WHERE id=?", (int(f.get("slip_id") or 0),)).fetchone()
            except Exception:                                 # noqa: BLE001
                had = None
            if had is None or str(had[0] or ""):
                return None
        else:'''), (
'''        if p == "/finance/slips/save":
            return SL._form_err(_S844_MSG)''',
'''        if p == "/finance/slips/save":
            return SL._form_err(_S844_MSG)
        if p == "/finance/slips/radd":                           # S852: back to the list the radd came from, the reason said
            import slip_adjust                                   # noqa: PLC0415
            return slip_adjust._back(f.get("back") if f.get("back") in ("list", "late") else "list",
                                     err="Naam clinic ID nahi hai -- Docterz wali clinic ID ka number likhiye.")''')]

P["month_read.py"] = [(
'''        mo = _bill_month_sql(bcols)
        where = "%s=? AND COALESCE(status,'')<>'rejected'" % mo + (" AND dup_of IS NULL" if "dup_of" in bcols else "")
        lane = "COALESCE(lane, CASE kind WHEN 'Pharmacy' THEN 'pharmacy' WHEN 'Lab' THEN 'lab_purchase' WHEN 'Expense' THEN 'owner_expense' WHEN 'Document' THEN 'other_doc' ELSE 'clinic' END)" \\
            if "lane" in bcols else "CASE kind WHEN 'Pharmacy' THEN 'pharmacy' WHEN 'Lab' THEN 'lab_purchase' WHEN 'Expense' THEN 'owner_expense' WHEN 'Document' THEN 'other_doc' ELSE 'clinic' END"
        sg = "COALESCE(subgroup,'')" if "subgroup" in bcols else "''"
        groups, lanes = {}, {}
        for r in ac.execute("SELECT %s AS ln, %s AS sg, COUNT(*), COALESCE(SUM(total_amount),0) FROM bills WHERE %s GROUP BY 1, 2" % (lane, sg, where), (ym,)):
            ln, g = str(r[0] or "clinic"), str(r[1] or "")
            if ln == "clinic":
                groups[g] = (int(r[2]), float(r[3] or 0))
            n0, a0 = lanes.get(ln, (0, 0.0))
            lanes[ln] = (n0 + int(r[2]), a0 + float(r[3] or 0))
        ids = [int(r[0]) for r in ac.execute("SELECT id FROM bills WHERE %s AND %s='pharmacy'" % (where, lane), (ym,))]
''',
'''        mo = _bill_month_sql(bcols)
        where = "%s=? AND COALESCE(status,'')<>'rejected'" % mo + (" AND dup_of IS NULL" if "dup_of" in bcols else "")
        if "page_of" in bcols:
            where += " AND page_of IS NULL"                # S852 (F-1418): a page joined into another paper counts in that paper
        lane = "COALESCE(lane, CASE kind WHEN 'Pharmacy' THEN 'pharmacy' WHEN 'Lab' THEN 'lab_purchase' WHEN 'Expense' THEN 'owner_expense' WHEN 'Document' THEN 'other_doc' ELSE 'clinic' END)" \\
            if "lane" in bcols else "CASE kind WHEN 'Pharmacy' THEN 'pharmacy' WHEN 'Lab' THEN 'lab_purchase' WHEN 'Expense' THEN 'owner_expense' WHEN 'Document' THEN 'other_doc' ELSE 'clinic' END"
        sg = "COALESCE(subgroup,'')" if "subgroup" in bcols else "''"
        dk = "COALESCE(NULLIF(doc_kind,''),'bill')" if "doc_kind" in bcols else "'bill'"
        cs = "COALESCE(challan_state,'')" if "challan_state" in bcols else "''"
        groups, lanes, ids, cns = {}, {}, [], []

        def _add(ln, g, n, amt):
            if ln == "clinic":
                n0, a0 = groups.get(g, (0, 0.0))
                groups[g] = (n0 + n, a0 + amt)
            n0, a0 = lanes.get(ln, (0, 0.0))
            lanes[ln] = (n0 + n, a0 + amt)

        # S852 (F-1418), the Scan App's own rule (clinic_papers._live, sorting_desk._s566_total): a receipt, a statement or a
        # summary is not money; a challan counts only once final; a credit note is LESS, in the group of the bill it is against.
        for r in ac.execute("SELECT id, %s AS ln, %s AS sg, %s AS dk, %s AS cs, COALESCE(total_amount,0) FROM bills WHERE %s" % (lane, sg, dk, cs, where), (ym,)):
            bid, ln, g, k, c, amt = int(r[0]), str(r[1] or "clinic"), str(r[2] or ""), str(r[3] or "bill"), str(r[4] or ""), float(r[5] or 0)
            if k in ("receipt", "statement", "summary") or (k == "challan" and c != "final"):
                continue
            if k == "credit_note":
                cns.append((bid, ln, g, amt))
                continue
            _add(ln, g, 1, amt)
            if ln == "pharmacy":
                ids.append(bid)
        if cns:
            to = {}
            if _has(ac, "credit_note"):
                for c in cns:
                    try:
                        h = ac.execute("SELECT %s, %s FROM bills WHERE id=(SELECT against_bill_id FROM credit_note WHERE cn_bill_id=? "
                                       "AND COALESCE(voided_at,'')='' ORDER BY id DESC LIMIT 1)" % (lane, sg), (c[0],)).fetchone()
                    except sqlite3.Error:                      # S852: an older credit_note table -- the paper's own lane
                        h = None
                    if h:
                        to[c[0]] = (str(h[0] or "clinic"), str(h[1] or ""))
            for bid, ln, g, amt in cns:
                ln2, g2 = to.get(bid, (ln, g))
                if ln2 != "pharmacy":                          # the pharmacy's rupees are Marg's; its credit notes are not scans of bills
                    _add(ln2, g2, 0, -amt)
''')]


def m5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


os.makedirs(OUT, exist_ok=True)
for name, patches in P.items():
    src = os.path.join(LIVE, name)
    h = m5(src)
    if not h.startswith(FROM[name]):
        sys.exit("STOP: %s is %s, not the FROM pin %s" % (name, h[:8], FROM[name][:8]))
    s = open(src, encoding="utf-8").read()
    for a, b in patches:
        if s.count(a) != 1:
            sys.exit("STOP: an anchor in %s occurs %d times: %r" % (name, s.count(a), a[:70]))
        s = s.replace(a, b)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(s)
    print("%s %s -> %s" % (name, h[:8], m5(os.path.join(OUT, name))[:8]))
