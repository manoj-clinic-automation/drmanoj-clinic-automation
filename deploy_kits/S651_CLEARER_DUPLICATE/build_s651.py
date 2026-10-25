#!/usr/bin/env python3
"""build_s651.py -- S651_CLEARER_DUPLICATE (D761 for the scan app; F-992's scan-app half): counted edits on three live files.
    python3 build_s651.py <FROM folder> <TO folder>
Each FROM must be at its pin and each edit's old text must occur exactly once, or nothing is written."""
import hashlib
import os
import sys

PINS = {"scan_checks_s441.py": "b9ba6839ec7979cb709909214d6a0b69",
        "asset_register.py": "068440f7106b6e78b78c1ca3266b9a47",
        "sorting_desk.py": "ca9fda745914c2875c8056a0091b0c1a"}

CLEARER = '''

# ------------------------------------------------------------------ S651 (D761): when two scans are one paper, keep the clearer
# The owner, 22-Oct-2026 (F-992, Kedar A000211: the bottom-total scan kept, the whole bill set aside): the scan with item lines is
# kept over one with none. Only in the clinic's own lanes (the pharmacy lane's copies are the Sanjeevni side's: its order list
# already reads the clearer copy), both scans read, of the same kind, document kind, person and month, and only when the scan that
# would be given up is UNTOUCHED -- not approved or set aside, no joined pages, not a rescan and none of its own, no other copy
# pointing at it, no record of the scan app on it (a machine, a procedure-room line, stationery, a warranty, a payment, an X-ray
# mark ...), nothing a person did to it after the scan, and no link in the finance database (read only; when that database cannot
# be read, nothing is swapped).
D761_BLOCK = ("desk_", "d664_", "d710_", "challan", "payment", "paid", "machine_link", "subgroup", "kind", "pe_who", "to_accountant",
              "doc_kind", "mixed", "rescan", "blur_kept", "not_duplicate", "s441_page", "s441_answer", "paper_deleted", "kept_clearer",
              "relane", "month")
D761_REF_OK = ("bills", "bill_items", "bill_audit", "claude_reading", "scan_lie", "scan_check_s441", "scan_question")
D761_FIN_COLS = ("asset_bill_id", "scan_bill_id", "scan_id", "done_bill_id")     # a scan's id (read from the live schema, 25-Oct)
D761_FIN_REFS = ("scan_ref", "stamp")                                            # a scan's stamp (or id) as text
D761_FIN_KNOWN = D761_FIN_COLS + D761_FIN_REFS + ("scan_norm", "scan_name", "scan_at")   # every column named *scan* the finance db has
D761_NOT_LANES = ("pharmacy",)


def _c(r, k):
    try:
        return r[k] if k in r.keys() else None
    except Exception:                                          # noqa: BLE001
        return None


def _q(name):
    return '"%s"' % str(name).replace('"', '""')


def _n_items(db, bid):
    return db.execute("SELECT COUNT(*) FROM bill_items WHERE bill_id=?", (bid,)).fetchone()[0]


def _held_here(db, bid, other):
    \"\"\"Why the scan app itself holds this scan (a reason), or ''.\"\"\"
    for col in ("page_of", "rescan_of"):
        if db.execute("SELECT 1 FROM bills WHERE %s=? LIMIT 1" % col, (bid,)).fetchone():
            return "another scan is its %s" % col
    if db.execute("SELECT 1 FROM bills WHERE dup_of=? AND id<>? LIMIT 1", (bid, other)).fetchone():
        return "another copy points at it"
    for (act,) in db.execute("SELECT action FROM bill_audit WHERE bill_id=?", (bid,)):
        if str(act or "").startswith(D761_BLOCK):
            return "a person's step on it (%s)" % act
    names = [t for (t,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    if "xray_mark" in names and db.execute("SELECT 1 FROM xray_mark WHERE kind='paper' AND ref_id=? AND removed_at='' LIMIT 1", (bid,)).fetchone():
        return "an X-ray mark on it"
    for t in names:
        if t in D761_REF_OK or t.startswith("sqlite_"):
            continue
        for col in [r[1] for r in db.execute("PRAGMA table_info(%s)" % _q(t))]:
            if col == "bill_id" or col.endswith("_bill_id"):
                if db.execute("SELECT 1 FROM %s WHERE %s=? LIMIT 1" % (_q(t), _q(col)), (bid,)).fetchone():
                    return "a record on it (%s)" % t
    return ""


def _held_in_finance(bid, fin_path=None, stamp=None):
    \"\"\"Why the finance database holds this scan (a reason), '' when it does not -- None when it cannot be read, or when it has a
    column named *scan* this rule does not know (a link it could not see).\"\"\"
    con = _fin_ro(fin_path)
    if con is None:
        return None
    try:
        refs = [str(bid)] + ([str(stamp)] if stamp else [])
        for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            for col in [r[1] for r in con.execute("PRAGMA table_info(%s)" % _q(t))]:
                if "scan" in col.lower() and col not in D761_FIN_KNOWN:
                    return None
                if col in D761_FIN_COLS:
                    if con.execute("SELECT 1 FROM %s WHERE %s=? LIMIT 1" % (_q(t), _q(col)), (bid,)).fetchone():
                        return "linked in the finance database (%s)" % t
                elif col in D761_FIN_REFS:
                    if con.execute("SELECT 1 FROM %s WHERE CAST(%s AS TEXT) IN (%s) LIMIT 1" % (_q(t), _q(col), ",".join("?" * len(refs))), refs).fetchone():
                        return "named in the finance database (%s)" % t
        return ""
    except _sqlite3.Error:
        return None
    finally:
        con.close()


def _same(a, b):
    return (a or "") == (b or "")


def clearer(db, keep, drop, fin_path=None):
    \"\"\"D761: the pair as it should be set -- (keep, drop, why). Swapped (the fuller scan kept) only when `drop` has item lines,
    `keep` has none, and every condition above holds; `why` then says so, else None. Never raises; writes nothing.\"\"\"
    try:
        if keep is None or drop is None or keep["id"] == drop["id"]:
            return keep, drop, None
        k = db.execute("SELECT * FROM bills WHERE id=?", (keep["id"],)).fetchone()
        d = db.execute("SELECT * FROM bills WHERE id=?", (drop["id"],)).fetchone()
        if k is None or d is None:
            return keep, drop, None
        nk, nd = _n_items(db, k["id"]), _n_items(db, d["id"])
        if nk or not nd:
            return keep, drop, None
        if k["status"] not in ("draft", "captured") or d["status"] not in ("draft", "captured"):
            return keep, drop, None
        lane = k["lane"] or "clinic"
        if lane != (d["lane"] or "clinic") or lane in D761_NOT_LANES:
            return keep, drop, None
        if _c(k, "ocr_status") not in ("read", "empty") or _c(d, "ocr_status") != "read":
            return keep, drop, None
        for col in ("kind", "doc_kind", "pe_who"):
            if not _same(_c(k, col), _c(d, col)):
                return keep, drop, None
        if not _same(_c(k, "bill_month"), _c(d, "bill_month")):        # K1 M2: a month confirmed on either is never lost
            return keep, drop, None
        if _c(k, "page_of") or _c(d, "page_of") or _c(k, "rescan_of") or _c(d, "rescan_of"):
            return keep, drop, None
        if _held_here(db, k["id"], d["id"]):
            return keep, drop, None
        if _held_in_finance(k["id"], fin_path, k["stamp_no"]) != "":
            return keep, drop, None
        return drop, keep, "D761: the clearer scan kept -- %s has %d item line%s, %s none" % (
            d["stamp_no"] or "#%d" % d["id"], nd, "" if nd == 1 else "s", k["stamp_no"] or "#%d" % k["id"])
    except Exception:                                          # noqa: BLE001
        return keep, drop, None


def settle_swap(db, kept_id, gone_id, who="server (D761)"):
    \"\"\"After a D761 swap: the kept scan's amber and open question about the scan set aside are closed, and its verdict that
    pointed at it reads 'clear' -- so no later tap can set the kept scan aside onto the one already set aside.\"\"\"
    db.execute("UPDATE bills SET dup_flag='no' WHERE id=? AND dup_flag='maybe' AND dup_cand=?", (kept_id, gone_id))
    try:
        db.execute("UPDATE scan_question SET answer='same', answered_by=?, answered_at=? WHERE answer IS NULL AND kind='twin' AND "
                   "((bill_id=? AND cand_id=?) OR (bill_id=? AND cand_id=?))", (who, now_ist(), kept_id, gone_id, gone_id, kept_id))
        db.execute("UPDATE scan_check_s441 SET verdict='clear', other_id=NULL, detail=? WHERE bill_id=? AND other_id=? "
                   "AND verdict IN ('double','twin_q')", ("kept; %d set aside (D761)" % gone_id, kept_id, gone_id))
    except _sqlite3.Error:
        pass
'''

EDITS = {
"scan_checks_s441.py": [
('VERSION = "S441.1"\n', 'VERSION = "S441.2"   # S651 (D761): clearer() -- when two scans are one paper, the one with item lines is kept\n'),
('''def _ask(db, bid, kind, cand, detail):
''', CLEARER.lstrip("\n") + '''

def _ask(db, bid, kind, cand, detail):
'''),
('''            if drop["status"] == "approved":                     # an approved clinic bill is never set aside by a rule
''', '''            keep, drop, why761 = clearer(db, keep, drop, fin_path)     # S651 (D761): the clearer scan kept
            if drop["status"] == "approved":                     # an approved clinic bill is never set aside by a rule
'''),
('''                _set_aside(db, drop, keep, "S441 sure: supplier + bill-number tail + amount within 2%")
''', '''                _set_aside(db, drop, keep, "S441 sure: supplier + bill-number tail + amount within 2%" + ("; " + why761 if why761 else ""))
                if why761:
                    settle_swap(db, keep["id"], drop["id"])
'''),
('''            if drop["status"] == "approved":
                keep, drop = drop, keep
            if drop["status"] != "rejected" and drop["status"] != "approved":
                _set_aside(db, drop, keep, "S441 person: the same paper (%s)" % who)
''', '''            if drop["status"] == "approved":
                keep, drop = drop, keep
            keep, drop, why761 = clearer(db, keep, drop)               # S651 (D761): the clearer scan kept
            if drop["status"] != "rejected" and drop["status"] != "approved" and keep["status"] != "rejected":   # S651: never onto a set-aside
                _set_aside(db, drop, keep, "S441 person: the same paper (%s)" % who + ("; " + why761 if why761 else ""))
                if why761:
                    settle_swap(db, keep["id"], drop["id"])
'''),
],
"asset_register.py": [
('''def _mark_dup(db, bid, first, how):
    \"\"\"The new bill is rejected as a duplicate of `first`; its stamp stays (void-pair). The paper carries the first number.\"\"\"
    db.execute(''', '''def _mark_dup(db, bid, first, how):
    \"\"\"The new bill is rejected as a duplicate of `first`; its stamp stays (void-pair). The paper carries the first number.
    S651 (D761): when the new scan has item lines and `first` none, and every condition of scan_checks_s441.clearer holds, `first`
    is the one set aside instead (the paper then carries the new scan's number too). A `first` already set aside onto this scan
    leaves it kept. Returns the id of the scan kept.\"\"\"
    fr = db.execute("SELECT * FROM bills WHERE id=?", (first["id"],)).fetchone()
    if fr is not None and fr["status"] == "rejected" and fr["dup_of"] == bid:          # S651: never onto a scan already set aside onto it
        return bid
    if S441 is not None and hasattr(S441, "clearer") and fr is not None:
        nb = db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
        k, d, why = S441.clearer(db, fr, nb) if nb is not None else (None, None, None)
        if why and k is not None and k["id"] == bid:
            db.execute("SAVEPOINT s651")
            try:
                db.execute("UPDATE bills SET status='rejected', dup_of=?, dup_flag='yes', dup_why=?, reject_reason=?, approved_by=?, approved_at=? "
                           "WHERE id=?", (bid, "%s; %s" % (how, why), "duplicate of %s" % (nb["stamp_no"] or ("#%d" % bid)),
                                          "server (duplicate guard, D761)", _now_ist(), fr["id"]))
                _audit_bill(db, fr["id"], "duplicate", {"of": bid, "of_stamp": nb["stamp_no"], "how": how, "d761": why})
                _audit_bill(db, bid, "kept_clearer", {"set_aside": fr["id"], "set_aside_stamp": fr["stamp_no"], "how": how})
                S441._verdict(db, fr["id"], "double", bid, why)
                S441.settle_swap(db, bid, fr["id"])
                db.execute("RELEASE s651")
                return bid
            except Exception as e:                                   # noqa: BLE001
                db.execute("ROLLBACK TO s651")
                db.execute("RELEASE s651")
                print("S651 _mark_dup: the swap was undone (%s); the old rule applies" % type(e).__name__, file=_sys.stderr)
    db.execute('''),
('''    _audit_bill(db, bid, "duplicate", {"of": first["id"], "of_stamp": first["stamp_no"], "how": how})


def _mark_maybe(db, bid, cand, how):''', '''    _audit_bill(db, bid, "duplicate", {"of": first["id"], "of_stamp": first["stamp_no"], "how": how})
    return first["id"]


def _mark_maybe(db, bid, cand, how):'''),
('''        _mark_dup(db, bid, first, "checker")
        db.commit()
        flash("%s marked a duplicate of %s." % (b["stamp_no"] or ("#%d" % bid), first["stamp_no"] or ("#%d" % first["id"])))
''', '''        kept = _mark_dup(db, bid, first, "checker")
        db.commit()
        if kept == bid:                                                  # S651 (D761)
            flash("%s kept; %s is set aside as its second scan." % (b["stamp_no"] or ("#%d" % bid),
                                                                                        first["stamp_no"] or ("#%d" % first["id"])))
        else:
            flash("%s marked a duplicate of %s." % (b["stamp_no"] or ("#%d" % bid), first["stamp_no"] or ("#%d" % first["id"])))
'''),
],
"sorting_desk.py": [
('''            AR._mark_dup(db, bid, first, "desk")
            return {"message": "%s is set aside as a second scan of %s." % (st, fst)}
''', '''            kept = AR._mark_dup(db, bid, first, "desk")
            if kept == bid:                                              # S651 (D761): the clearer scan kept
                return {"message": "%s is kept; %s is set aside as its second scan." % (st, fst)}
            return {"message": "%s is set aside as a second scan of %s." % (st, fst)}
'''),
],
}


def main(src, dst):
    out = {}
    for f, pin in PINS.items():
        b = open(os.path.join(src, f), "rb").read()
        if hashlib.md5(b).hexdigest() != pin:
            print("%s: FROM is %s, not the pin %s -- STOP" % (f, hashlib.md5(b).hexdigest()[:8], pin[:8]))
            return 1
        t = b.decode("utf-8")
        for i, (o, n) in enumerate(EDITS[f], 1):
            c = t.count(o)
            if c != 1:
                print("%s E%d: old text found %d times -- STOP, nothing written" % (f, i, c))
                return 1
            t = t.replace(o, n)
        out[f] = t
    os.makedirs(dst, exist_ok=True)
    for f, t in out.items():
        open(os.path.join(dst, f), "wb").write(t.encode("utf-8"))
        print("%s: %d counted edits; TO %s" % (f, len(EDITS[f]), hashlib.md5(t.encode("utf-8")).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
