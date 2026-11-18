#!/usr/bin/env python3
"""make_s873.py -- kit S873_CARD_STMT_NO_PASSWORD (the parent, S480, 18-Nov-2026).

The 13:25 check on /finance/packs (October): the ICICI Amazon Pay statement 13-Sep..12-Oct that the owner downloaded from
the bank's website and put in Drive > Credit Card Statements > ICICI Amazon Pay (10:09) reached the shelf (file 176) and its
dates were read -- but it was held as 'locked original' and never read. The shelf took every file in a card folder to be
the bank's password-locked mail copy; a statement downloaded from the website carries no password.

/root/finance/packs.py (S866's TO da0013ab):
  1. _original_status: a card-folder statement that opened WITHOUT a password and whose date was read is 'read' (as an
     opened one); one with no password whose date could not be read is 'n/a' with that reason (never 'locked').
  2. _process_once: such a file already held as 'locked original' with locked=0 is looked at again (once it is read, or
     found truly locked -- locked=1 -- it is not picked again).
Usage: python make_s873.py SRC_DIR OUT_DIR
"""
import hashlib
import os
import sys

FROM = {"packs.py": "da0013ab52324e19b4f0d24cb9033435"}

P = []
P.append(('''        return "read", "statement dated %s · opened by the shelf" % _dmy(card["statement_date"])
''', '''        return "read", "statement dated %s · opened by the shelf" % _dmy(card["statement_date"])
    if not f.get("locked") and not f.get("unlocked_path"):
        # S873: not password-locked (downloaded from the bank's website, not the bank's locked mail copy): read as any other
        if card and card.get("statement_date"):
            con.execute("UPDATE stmt_file SET period_from=?, period_to=? WHERE id=?", (card.get("period_from"), card.get("period_to"), f["id"]))
            return "read", "statement dated %s · no password (downloaded from the bank)" % _dmy(card["statement_date"])
        if card is not None:
            return "n/a", "no password, but the statement date could not be read from the PDF"
        return "n/a", "the file could not be opened or read (not a password -- the file itself)"
'''))

P.append(('''"SELECT * FROM stmt_file WHERE (slot_id IS NULL AND COALESCE(read_status,'') NOT IN (?, ?)) OR read_status IS NULL ORDER BY id"''',
          '''"SELECT * FROM stmt_file WHERE (slot_id IS NULL AND COALESCE(read_status,'') NOT IN (?, ?)) OR read_status IS NULL "
                                                     "OR (folder='cards' AND read_status='locked original' AND COALESCE(locked,0)=0) ORDER BY id"'''))


# 3. the month's card cell took a card-folder file only when the shelf had opened it (unlocked copy); a statement with no
#    password at all, read, now counts the same
P.append(('''"COALESCE(unlocked_path,'')<>'' AND read_status='read')) AND period_to BETWEEN ? AND ? "   # S503''',
          '''"(COALESCE(unlocked_path,'')<>'' OR COALESCE(locked,0)=0) AND read_status='read')) AND period_to BETWEEN ? AND ? "   # S503, S873'''))


# 4. (cold review SHOULD 1) the 'newest original has no decrypted twin' flag: a read statement with no password needs no twin
P.append(('''            if orig and not (orig[0].get("unlocked_path") and orig[0].get("read_status") == "read") and''',
          '''            if orig and not ((orig[0].get("unlocked_path") or not orig[0].get("locked")) and orig[0].get("read_status") == "read") and'''))


def main():
    src, out = sys.argv[1], sys.argv[2]
    raw = open(os.path.join(src, "packs.py"), "rb").read()
    md5 = hashlib.md5(raw).hexdigest()
    if md5 != FROM["packs.py"]:
        raise SystemExit("STOP: packs.py is %s, not the FROM %s -- nothing written" % (md5, FROM["packs.py"]))
    text = raw.decode("utf-8")
    for i, (old, new) in enumerate(P, 1):
        n = text.count(old)
        if n != 1:
            raise SystemExit("STOP: anchor %d found %d times (want 1) -- nothing written" % (i, n))
        text = text.replace(old, new)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "packs.py"), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print("%s packs.py" % hashlib.md5(text.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
