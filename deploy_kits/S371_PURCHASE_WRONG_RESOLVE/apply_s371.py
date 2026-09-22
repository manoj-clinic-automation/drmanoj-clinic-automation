#!/usr/bin/env python3
"""apply_s371.py -- kit S371_PURCHASE_WRONG_RESOLVE. Anchored edits on purchase_app.py d1476f80 (S255 bytes):
F-614 -- a bill marked WRONG cleared itself only by a person's Correct, and the Correct button left the row the
moment bill-wise and supplier-wise agreed again, so a WRONG could never be cleared and the month never finalised.
  1. _resolve_wrong(): after a BILLWISE / SUPPLIERWISE push, a WRONG bill whose live Marg amount now equals
     the amount that was marked right (within Rs 1) becomes CORRECT by itself, with an audit row that names
     the export. Also runnable over every WRONG bill (resolve_now.py at install).
  2. A WRONG bill always keeps its Correct button until the month is final (needs_verdict includes wrong).
  python3 apply_s371.py --dir /root/finance [--out DIR]
"""
import argparse, hashlib, os
ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--out")
a = ap.parse_args()
p = os.path.join(a.dir, "purchase_app.py"); s = open(p, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "d1476f80836e8b68fae2da1855c7105f", "purchase_app.py is not d1476f80"
def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)
rep('''purchase_app.py -- S224: Marg's purchases, on the box.  (rev 12, S225, 05-Sep-2026)
''', '''purchase_app.py -- S224: Marg's purchases, on the box.  (rev 13, S371 / Session 281, 22-Sep-2026)

REV 13 (S371, 22-Sep, F-614 -- the owner: "add 6 rupees in kedar and 39 in lk, and it will be final"):
    a bill marked WRONG resolves ITSELF when Marg's next bill-wise or supplier-wise export carries the
    amount that was marked right (within Rs 1) -- verdict CORRECT, reason names the export, audit row
    'verdict_resolved'. And a WRONG bill keeps its Correct button until the month is final, so a person can
    always clear it by hand. Before this, the button left with the disagreement and the month could never
    finalise.
''')
rep('''class _Malformed(Exception):
    pass
''', '''class _Malformed(Exception):
    pass


def _resolve_wrong(con, md5=None, stamp=None, who="marg re-export"):
    """S371 (F-614): every WRONG bill whose live Marg amount is now the amount marked right becomes
    CORRECT. Limited to the bills the export `md5` touched when given; over every WRONG bill otherwise.
    Returns the resolved bills as (id, supplier, bill_no, amount_p)."""
    q = ("SELECT b.id, b.supplier, b.bill_no, b.amount_p, b.wrong_amount_p, b.bw_amount_p, b.sw_amount_p, "
         "b.bw_md5, b.sw_md5, b.month FROM purchase_bill b WHERE b.verdict='WRONG' AND b.wrong_amount_p IS NOT NULL")
    args = ()
    if md5:
        q += " AND (b.bw_md5=? OR b.sw_md5=?)"
        args = (md5, md5)
    out = []
    for r in con.execute(q, args).fetchall():
        st = _month_status(con, r["month"] or "")
        if st["status"] == "final":
            continue
        live = con.execute("SELECT md5 FROM purchase_export WHERE superseded_by IS NULL AND md5 IN (?,?)",
                           (r["bw_md5"] or "", r["sw_md5"] or "")).fetchall()
        live = {x[0] for x in live}
        sw = r["sw_amount_p"] if (r["sw_md5"] in live and r["sw_amount_p"] is not None) else None
        bw = r["bw_amount_p"] if (r["bw_md5"] in live and r["bw_amount_p"] is not None) else None
        now_p = sw if sw is not None else (bw if bw is not None else r["amount_p"])
        if now_p is None or abs(int(now_p) - int(r["wrong_amount_p"])) > AGREE_P:
            continue
        reason = "resolved: Marg's re-export%s carries %s, the amount marked right" % (
            (" " + stamp) if stamp else "", _r(int(now_p)))
        con.execute("UPDATE purchase_bill SET verdict='CORRECT', verdict_by=?, verdict_at=?, reason=? WHERE id=?",
                    (who, now_iso(), reason, r["id"]))
        _audit(con, who, "verdict_resolved", r["id"],
               dict(before="WRONG", wrong_amount_p=r["wrong_amount_p"], now_p=int(now_p), export=md5, stamp=stamp))
        out.append((r["id"], r["supplier"], r["bill_no"], int(now_p)))
    return out
''')
rep('''    _redate_lines(con)
    _audit(con, "push_purchases", "push", md5, dict(type=typ, period=[pf, pt], rows=n,
                                                     superseded=[r[0] for r in rivals]))
''', '''    _redate_lines(con)
    if typ in ("BILLWISE", "SUPPLIERWISE"):
        _resolve_wrong(con, md5=md5, stamp=stamp)                  # S371 (F-614)
    _audit(con, "push_purchases", "push", md5, dict(type=typ, period=[pf, pt], rows=n,
                                                     superseded=[r[0] for r in rivals]))
''')
rep('''    needs_verdict = {x["bill"]["id"] for x in short} | {b["id"] for b in disagree}
    wrong = [b for b in bills if b["verdict"] == "WRONG"]
''', '''    wrong = [b for b in bills if b["verdict"] == "WRONG"]
    # S371 (F-614): a WRONG bill keeps its Correct button until the month is final
    needs_verdict = {x["bill"]["id"] for x in short} | {b["id"] for b in disagree} | {b["id"] for b in wrong}
''')
rep('''            elif v == "CORRECT":
                vh = '<span class="chip ok">Correct</span>'
''', '''            elif v == "CORRECT":
                vh = '<span class="chip ok">Correct</span>' + (
                    ' <span class="muted">%s</span>' % _esc(b["reason"])
                    if (b["reason"] or "").startswith("resolved:") else "")     # S371
''')
out = os.path.join(a.out or a.dir, "purchase_app.py")
open(out, "w", encoding="utf-8").write(s)
print("purchase_app.py ->", hashlib.md5(s.encode("utf-8")).hexdigest())
