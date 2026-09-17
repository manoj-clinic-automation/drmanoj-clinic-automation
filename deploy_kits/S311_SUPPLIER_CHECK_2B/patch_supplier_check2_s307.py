#!/usr/bin/env python3
"""S307_SUPPLIER_CHECK_2 -- the wrong-supplier check, second stage, on Amir's step 4 (bills).

S285 (D530) warns when an item on a bill has never come from the supplier the bill names. Two cases it could
not see, from the Sanjeevni plan ("the wrong-supplier check, second stage"):

  (a) A PURCHASE RETURN written under the wrong supplier. A return is a purchase_bill with a negative amount
      and its own item lines, so S285's test already runs on it -- but its words spoke of a bill that "came".
      For a return the words now say what is wrong: the goods are being returned to a supplier who never
      supplied them.
  (b) THE SAME BILL NUMBER AND DATE UNDER TWO SUPPLIERS. Every other bill with that number and date under
      another supplier, in a live bill-wise export, is named on the bill. Where the amount is also the same,
      the words say plainly that one bill may have been entered twice under two names (the owner's August
      case shape: 502 of 18-Aug under MANNAT PHARMA and DEEPAM PHARMA, Rs 10,641 each). Where the amounts
      differ, it is a softer look -- two suppliers' series can meet.

Nothing is decided for him: the reason "Supplier galat likha" (S285) is still his to pick, and Theek hai clears it.

amir_day.py (anchored edits over S285 b3c20319):
  1. _twin_bills_s307(cx, b) beside _supplier_warn_s285;
  2. _bills() computes d["twin"] beside d["warn"];
  3. _bill_block() words the S285 warning for a return, and adds the twin warning.

    python3 -B patch_supplier_check2_s307.py --file amir_day.py [--from M] [--dry-run]
"""
from __future__ import print_function
import argparse
import hashlib
import io
import shutil
import sys

TWIN_BLOCK = '''

def _twin_bills_s307(cx, b):
    """S307: other bills with THIS bill number and THIS date under ANOTHER supplier, each still carried by a
    live bill-wise export: [(supplier, amount_p, same_amount)]. Any failure to read means no warning, never a
    broken page."""
    out = []
    try:
        if not (_table_exists(cx, "purchase_bill") and _table_exists(cx, "purchase_export")):
            return out
        rows = cx.execute(
            "SELECT b.supplier_norm, MAX(b.supplier), MAX(b.amount_p) FROM purchase_bill b "
            "JOIN purchase_export e ON e.md5 = b.bw_md5 "
            "WHERE e.superseded_by IS NULL AND e.type = 'BILLWISE' AND b.bill_no = ? AND b.bill_date = ? "
            "AND b.supplier_norm <> ? GROUP BY b.supplier_norm ORDER BY b.supplier_norm",
            (b.get("bill_no"), b.get("bill_date"), b.get("supplier_norm"))).fetchall()
        mine = b.get("amount_p")
        for s_norm, s_name, amt in rows:
            out.append((s_name or s_norm, amt, mine is not None and amt is not None and int(amt) == int(mine)))
    except Exception:
        return out
    return out
'''

EDITS = [
    ('def _supplier_warn_s285(cx, b):\n',
     TWIN_BLOCK.lstrip("\n") + '\n\ndef _supplier_warn_s285(cx, b):\n'),
    ('''    for d in today_rows + carry:
        d["warn"] = _supplier_warn_s285(cx, d)
''',
     '''    for d in today_rows + carry:
        d["warn"] = _supplier_warn_s285(cx, d)
        d["twin"] = _twin_bills_s307(cx, d)                  # S307: same number, same date, another supplier
'''),
    ('''    for item, usual, n in (b.get("warn") or []):
        was += ("<div class=swarn>&#9888; <b>%s</b> pehle hamesha <b>%s</b> se aaya hai "
                "(%d bill). Is bill par <b>%s</b> likha hai &mdash; Marg mein bill dekh lijiye.</div>"
                % (_esc(item), _esc(usual), n, _esc(b.get("supplier") or b.get("supplier_norm"))))
''',
     '''    is_return = int(b.get("amount_p") or 0) < 0                # S307: a purchase return is a bill with a minus amount
    for item, usual, n in (b.get("warn") or []):
        if is_return:
            was += ("<div class=swarn>&#9888; Ye <b>wapsi</b> hai. <b>%s</b> kabhi <b>%s</b> se nahi aaya &mdash; "
                    "pehle hamesha <b>%s</b> se aaya hai (%d bill). Wapsi galat supplier ke naam to nahi likhi? "
                    "Marg mein dekh lijiye.</div>"
                    % (_esc(item), _esc(b.get("supplier") or b.get("supplier_norm")), _esc(usual), n))
        else:
            was += ("<div class=swarn>&#9888; <b>%s</b> pehle hamesha <b>%s</b> se aaya hai "
                    "(%d bill). Is bill par <b>%s</b> likha hai &mdash; Marg mein bill dekh lijiye.</div>"
                    % (_esc(item), _esc(usual), n, _esc(b.get("supplier") or b.get("supplier_norm"))))
    for other, amt, same in (b.get("twin") or []):
        if same:
            was += ("<div class=swarn>&#9888; Isi bill number aur isi taareekh ka bill <b>%s</b> ke naam bhi hai, "
                    "aur rakam bhi wahi &#8377;%s hai. Ek hi bill do supplier ke naam to nahi chadh gaya? "
                    "Marg mein dono dekh lijiye.</div>" % (_esc(other), _esc(_rupees(amt))))
        else:
            was += ("<div class=swarn>&#9888; Isi bill number aur isi taareekh ka ek bill <b>%s</b> ke naam bhi hai "
                    "(&#8377;%s). Do alag supplier ho sakte hain &mdash; ek baar Marg mein dekh lijiye.</div>"
                    % (_esc(other), _esc(_rupees(amt))))
'''),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="from_md5", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    raw = io.open(a.file, "rb").read()
    cur = md5(raw)
    text = raw.decode("utf-8")
    if "def _twin_bills_s307(cx, b):" in text:
        print("ALREADY PATCHED: %s is %s" % (a.file, cur))
        return 0
    if a.from_md5 and cur != a.from_md5.lower():
        sys.exit("REFUSING: %s is %s, expected %s" % (a.file, cur, a.from_md5))
    for old, new in EDITS:
        if text.count(old) != 1:
            sys.exit("REFUSING: anchor not found exactly once in %s: %r" % (a.file, old[:80]))
        text = text.replace(old, new)
    out = text.encode("utf-8")
    if a.dry_run:
        print("would write %s : %s -> %s" % (a.file, cur, md5(out)))
        return 0
    shutil.copy2(a.file, "%s.bak_S307_%s" % (a.file, cur[:8]))
    with io.open(a.file, "wb") as fh:
        fh.write(out)
    back = md5(io.open(a.file, "rb").read())
    print("patched %s : %s -> %s" % (a.file, cur, back))
    return 0 if back == md5(out) else 4


if __name__ == "__main__":
    sys.exit(main())
