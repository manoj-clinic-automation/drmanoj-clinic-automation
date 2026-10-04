#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s479.py -- S479_YES_MONTHLY_READER (session 294, 04-Oct-2026; F-725). Exact-anchor edits on THREE files, built from their
real bytes on the box: /root/finance/packs.py 1bc18b26 (S476, live since the evening of 04-Oct), /root/finance/finance_yesbank.py
3509f728 and /root/finance/yes_branch.py fec5c520 (both S475). Every anchor must be found exactly once; all three are verified
before any is written. The reader itself is a NEW file, yes_monthly.py, placed beside them by the installer.

WHAT. Yes Bank mails every account its month as a locked PDF in a layout neither Yes Bank reader knows ('YOUR ACCOUNT STATEMENT
FROM .. TO ..'). The shelf opens it with the owner's password, and then: the identifier took its bank from a narration (ICICI) and
gave it no period; the reader refused it ("does not print 'Period: <from> - <to>'"). Three such statements sit opened and refused
on the shelf (Sanjeevni Medicos, September; the HUF, August and September).
 1. identify_text(): the monthly layout names itself (yes_monthly.ident) -- the bank is Yes Bank by the layout, the holder is the
    'Primary Holder' line, the period and the tail come from the account's own section line.
 2. read_file(): a Yes Bank file is read by yes_branch (the branch's print), else by yes_monthly (the monthly e-mailed layout),
    else by finance_yesbank (the net-banking download), each recognising its own layout.
 3. THE SHELF ROW SAYS WHAT WAS WRITTEN: "11 lines: 7 new, 4 already held from another file" where the reader left rows another
    file already holds on the table (one line once); "ingested N lines" otherwise, as before.
 4. A PERSON IS HANDED THE COPY HE CAN OPEN: where the shelf opened a locked e-statement, the accountants' attachment, the owner's
    preview and Amir's pack take the unlocked copy (_best_path) -- until now all three took the locked original, which the
    accountants and Amir cannot open. A file that was never locked is served exactly as before.
 5. ONE LINE ONCE, IN ALL THREE YES BANK READERS. The three layouts key a row differently (the reference text), so the table's own
    key lets the same bank row in once per layout. yes_monthly.py does not write a row another file holds; with this kit the two
    older readers do the same toward the other layouts: finance_yesbank.py (the net-banking download) does not write a row the
    monthly statement or the branch's print already put on the table, and yes_branch.py does not write a row a file of another
    layout holds -- by date, withdrawal, deposit and the cash flag, counted. Without it, a net-banking download uploaded AFTER the month's
    statement was read would put every row on the shared Sanjeevni table a second time, and the pharmacy's cash check would raise a
    'bank deposit not booked' for each doubled cash deposit. Between two files of the SAME layout nothing changes (their own
    reference keys them, as before). Each answers already_held beside new_lines.
NOT TOUCHED: the parsing and the proofs of finance_yesbank.py and yes_branch.py, reconcile_cash_deposits, stmt_shelf.py, the tables'
shape, the cells' rules, the password card, every page.
   usage: apply_s479.py <packs.py> <finance_yesbank.py> <yes_branch.py>
"""
import hashlib
import sys

FROM = {"packs.py": "1bc18b263af7e652a8d093e29e018ea8", "finance_yesbank.py": "3509f7285fbae0d40fcb2daadb3a5b9f",
        "yes_branch.py": "fec5c520bfc4f563439d8f2dd6b24105"}

DOC = '''
S479 (F-725, 04-Oct-2026): the Yes Bank MONTHLY E-MAILED statement is read. A third layout ('YOUR ACCOUNT STATEMENT FROM .. TO ..',
'Primary Holder : ..', one foot line with the opening, the two totals and the closing): the shelf opened it with the owner's password,
the identifier took its bank from a narration and gave it no period, and the net-banking reader refused it. yes_monthly.py (new,
parent's) names it and reads it with the same proofs as S360 / S433, and never writes a row another file already holds (date +
amounts): the net-banking download of 1 Aug - 20 Sep sits beside September's statement on the shared Sanjeevni tables. And a person is
handed the copy he can open: the accountants' attachment, the owner's preview and Amir's pack take the UNLOCKED copy of a statement
the shelf opened (_best_path) -- the locked original is something only the owner can read.
'''

A_DOC = 'unlocked copy when the shelf opened it) -- a statement is read in its own bytes before its reader is judged (F-720). Nothing stored.\n"""\nimport datetime as dt\n'
B_DOC = 'unlocked copy when the shelf opened it) -- a statement is read in its own bytes before its reader is judged (F-720). Nothing stored.\n' + DOC + '"""\nimport datetime as dt\n'

A_IDENT = '''    except ImportError:
        pass
    head = _header(text)
'''
B_IDENT = '''    except ImportError:
        pass
    try:                                                              # S479 (F-725): Yes Bank's monthly e-mailed statement names itself
        import yes_monthly                                            # noqa: PLC0415
        if yes_monthly.is_monthly(text):
            b = yes_monthly.ident(text)
            return dict(bank="YES", kind=b["kind"], tail=b["tail"], period_from=b["period_from"], period_to=b["period_to"],
                        up=" ".join(b["holder"].upper().split()), holder=b["holder"], tokens=sorted(_tokens(b["holder"])))
    except ImportError:
        pass
    head = _header(text)
'''

A_RDR = '''            rdr = yes_branch if yes_branch.is_branch_blob(blob) else finance_yesbank
'''
B_RDR = '''            import yes_monthly                            # noqa: PLC0415  S479 (F-725)
            rdr = yes_branch if yes_branch.is_branch_blob(blob) else (yes_monthly if yes_monthly.is_monthly_blob(blob) else finance_yesbank)
'''

A_HELPER = '''def _file_text(lp):
'''
B_HELPER = '''def _best_path(con, fid):
    """S479: the file a person can open -- the unlocked copy when the shelf opened a locked e-statement, else the file as fetched.
    (path, name); (None, name) when neither is on disk; (None, None) when the shelf has no such file."""
    r = con.execute("SELECT local_path, name, unlocked_path FROM stmt_file WHERE id=?", (fid,)).fetchone()
    if not r:
        return None, None
    for p in (r[2], r[0]):
        if p and os.path.exists(p):
            return p, r[1]
    return None, r[1]


def _file_text(lp):
'''

A_ATT = '''                fr = con.execute("SELECT local_path, name FROM stmt_file WHERE id=?", (fid,)).fetchone()
                if fr and fr[0] and os.path.exists(fr[0]):
'''
B_ATT = '''                fr = _best_path(con, fid)                              # S479: the copy the accountants can open
                if fr[0]:
'''

A_FILE = '''    r = _db().execute("SELECT local_path, name FROM stmt_file WHERE id=?", (fid,)).fetchone()
    if not r or not r[0] or not os.path.exists(r[0]):
        return "not on the shelf", 404
'''
B_FILE = '''    r = _best_path(_db(), fid)                                         # S479: the unlocked copy when the shelf opened it
    if not r[0]:
        return "not on the shelf", 404
'''

A_AMIR = '''    r = con.execute("SELECT local_path, name FROM stmt_file WHERE id=?", (fid["id"],)).fetchone()
    if not r or not r[0] or not os.path.exists(r[0]):
        return "not on the shelf", 404
'''
B_AMIR = '''    r = _best_path(con, fid["id"])                                     # S479: the copy Amir can open
    if not r[0]:
        return "not on the shelf", 404
'''

A_SAID = '''    matched = "ingested %d lines" % res.get("lines", 0)
'''
B_SAID = '''    matched = "ingested %d lines" % res.get("lines", 0)
    if res.get("already_held"):                                       # S479: one line once -- what was written, and what another file held
        matched = "%d lines: %d new, %d already held from another file" % (res.get("lines", 0), res.get("new_lines", 0), res["already_held"])
'''

# ---- finance_yesbank.py (the net-banking download)
A_FY = '''    added = 0
    for ln in parsed["lines"]:
        cur = con.execute(
            "INSERT OR IGNORE INTO " + ltab + " (account_ref, txn_date, value_date,"
'''
B_FY = '''    # S479 (F-725): ONE LINE ONCE across the three Yes Bank layouts. A row the monthly e-mailed statement (yes_monthly.py) or the
    # branch's print (yes_branch.py) already put on this table -- date + withdrawal + deposit + cash flag, counted -- is not written a second
    # time under this layout's reference. Between two net-banking downloads nothing changes: their own reference keys them.
    others = {}
    days = [l["txn_date"] for l in parsed["lines"]]
    if days:
        for r in con.execute("SELECT txn_date, withdrawal_p, deposit_p, is_cash_deposit FROM " + ltab + " WHERE account_ref=? AND txn_date BETWEEN ? AND ? "
                             "AND (source_file LIKE 'monthly:%' OR source_file LIKE 'branch:%')", (parsed["account_ref"], min(days), max(days))):
            k = (r[0], r[1], r[2], 1 if r[3] else 0)      # the cash flag is part of the match: a cash deposit is never skipped for a transfer
            others[k] = others.get(k, 0) + 1
    added = already = 0
    for ln in parsed["lines"]:
        k = (ln["txn_date"], ln["withdrawal_p"], ln["deposit_p"], 1 if ln["is_cash_deposit"] else 0)
        if others.get(k, 0) > 0:
            others[k] -= 1
            already += 1
            continue
        cur = con.execute(
            "INSERT OR IGNORE INTO " + ltab + " (account_ref, txn_date, value_date,"
'''
A_FY2 = '''                parsed["period_to"]), lines=len(parsed["lines"]), new_lines=added,
                cash_deposits=len(cash),
'''
B_FY2 = '''                parsed["period_to"]), lines=len(parsed["lines"]), new_lines=added, already_held=already,
                cash_deposits=len(cash),
'''

# ---- yes_branch.py (the branch's print)
A_YB = '''    added = 0
    for ln in parsed["lines"]:
        cur = con.execute("INSERT OR IGNORE INTO " + ltab + " (account_ref, txn_date, value_date, description, reference, withdrawal_p, deposit_p, "
'''
B_YB = '''    # S479 (F-725): ONE LINE ONCE across the three Yes Bank layouts. A row a file of ANOTHER layout already put on this table --
    # date + withdrawal + deposit + cash flag, counted -- is not written a second time under the branch print's reference.
    others = {}
    days = [x["txn_date"] for x in parsed["lines"]]
    if days:
        for r in con.execute("SELECT txn_date, withdrawal_p, deposit_p, is_cash_deposit FROM " + ltab + " WHERE account_ref=? AND txn_date BETWEEN ? AND ? "
                             "AND COALESCE(source_file,'') NOT LIKE 'branch:%'", (acct, min(days), max(days))):
            k = (r[0], r[1], r[2], 1 if r[3] else 0)      # the cash flag is part of the match: a cash deposit is never skipped for a transfer
            others[k] = others.get(k, 0) + 1
    added = already = 0
    for ln in parsed["lines"]:
        k = (ln["txn_date"], ln["withdrawal_p"], ln["deposit_p"], 1 if ln["is_cash_deposit"] else 0)
        if others.get(k, 0) > 0:
            others[k] -= 1
            already += 1
            continue
        cur = con.execute("INSERT OR IGNORE INTO " + ltab + " (account_ref, txn_date, value_date, description, reference, withdrawal_p, deposit_p, "
'''
A_YB2 = '''        added += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    base.update(new_lines=added)
    return base
'''
B_YB2 = '''        added += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    base.update(new_lines=added, already_held=already)
    return base
'''

EDITS = {"packs.py": [(A_DOC, B_DOC), (A_IDENT, B_IDENT), (A_RDR, B_RDR), (A_HELPER, B_HELPER), (A_ATT, B_ATT), (A_FILE, B_FILE), (A_AMIR, B_AMIR),
                      (A_SAID, B_SAID)],
         "finance_yesbank.py": [(A_FY, B_FY), (A_FY2, B_FY2)],
         "yes_branch.py": [(A_YB, B_YB), (A_YB2, B_YB2)]}
ORDER = ("packs.py", "finance_yesbank.py", "yes_branch.py")


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: apply_s479.py <packs.py> <finance_yesbank.py> <yes_branch.py>")
    out = {}
    for name, path in zip(ORDER, argv[1:]):
        with open(path, encoding="utf-8", newline="") as fh:
            src = fh.read()
        if md5(src.encode("utf-8")) != FROM[name]:
            raise SystemExit("%s is %s, not the %s this kit was built on -- nothing written" % (name, md5(src.encode("utf-8")), FROM[name]))
        for i, (a, b) in enumerate(EDITS[name], 1):
            n = src.count(a)
            if n != 1:
                raise SystemExit("%s: anchor %d found %d times (must be exactly once) -- nothing written" % (name, i, n))
            src = src.replace(a, b)
        compile(src, name, "exec")
        out[name] = (path, src)
    for name in ORDER:                                    # all three verified; only now is any written
        path, src = out[name]
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(src)
        print("%s  %s  (%d edits)" % (md5(src.encode("utf-8")), name, len(EDITS[name])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
