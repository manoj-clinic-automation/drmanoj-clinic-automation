#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s474.py -- S474_FINANCE_TIDY (session 293, 04-Oct-2026). Exact-anchor edits on four files, built from the real
bytes of the 04-Oct 01:35 bundle: finance_app.py 727a2e7a · finance_ingest.py 747b4a50 · finance_returns.py a46a87e6 ·
marg_backfill.py fa33ec8a. Every anchor must be found exactly once; all four are verified before any is written.

WHAT (two sources):
 The S293 whole read of finance_app.py (dead 3, at the line):
  1. clinic_api_tile (S469): a non-checker -- reception's deposit banner -- was answered only AFTER the checker's whole month
     position had been computed and thrown away, and after refresh_missing_days() had WRITTEN to recon_exception on every
     page load. The non-checker is now answered first, from the custody figure and the threshold alone; no write.
  2. selftest(): _f6_ledger_prev was taken and never used -- LEDGER_DIR, FINANCE_LEDGER_JSONL and LEDGER_JSONL are now put
     back at teardown like DB_PATH, SCAN_DIR, UPI_DIR and YESBANK_DIR are.
  3. CLINIC_TENDERS, never referenced (CLINIC_TENDERS_ALL is the vocabulary), removed; the comment that named it now
     names the one that is used.
 F-716 (the Sanjeevni chat's proof of the parent's Marg-apply lead, 04-Oct), a money-record fault:
  4. ingest_day() and load_lines() committed inside themselves, so the con.rollback() a caller issued when a day's bill
     count did not match undid NOTHING -- a later export whose count mismatched was answered 'aborted' yet REPLACED the
     good day in the books. Both loaders take commit=True (default, every other caller unchanged); the three apply paths
     in finance_app.py (the S243 push apply, the autoreplay at save, the portal upload) and marg_backfill.py pass
     commit=False and commit once per day, after the lines and the attribution -- so their rollback is real.
  5. A file the server's own reader refused was pinned by its md5 as ALREADY-RECEIVED for ever (the same bytes could never
     be sent again, even after the reader was mended). A 'rejected' row no longer counts as received; when the same bytes
     arrive and read, the rejected row is replaced by the staged one.
   usage: apply_s474.py <finance_app.py> <finance_ingest.py> <finance_returns.py> <marg_backfill.py>
"""
import hashlib
import sys

FROM = {"finance_app.py": "727a2e7a5b23a606776fa12d75f8dcc8", "finance_ingest.py": "747b4a506042b95c862f3eafc74608f3",
        "finance_returns.py": "a46a87e65d951d59baeb9d86c9d8fe59", "marg_backfill.py": "fa33ec8a6dfa0ee0b6af5613160f3394"}

APP_EDITS = [
    # ---- 1. the non-checker answered first, no write
    ('''@app.route("/finance/clinic/api/tile")
def clinic_api_tile():
    con = db()
    refresh_missing_days(con, CLINIC_UNIT)
''',
     '''@app.route("/finance/clinic/api/tile")
def clinic_api_tile():
    con = db()
    # S474 (the S293 whole read): a non-checker -- reception's deposit banner (S469) -- is answered BEFORE any of the
    # checker's work: no refresh_missing_days (a write on every page load), no month figures; the custody figure and
    # the threshold are all the banner needs. The checker's answer below is unchanged.
    _u469 = current_user()
    if "checker" not in roles_for(con, CLINIC_UNIT, _u469["user"], _u469["role"]):
        _cust469 = con.execute("SELECT cash_p, custodian_name FROM v_cash_custody WHERE unit=?",
                               (CLINIC_UNIT,)).fetchone()
        _cash469 = int(_cust469["cash_p"]) if _cust469 else 0
        _thr469 = deposit_threshold_p(con, CLINIC_UNIT)
        _due469 = bool(_thr469 and _cash469 > _thr469)
        _out469 = dict(ok=True, unit_name=CLINIC_NAME, deposit_due=_due469)
        if _due469:
            _out469.update(cash_in_hand=rupees(_cash469), deposit_threshold=rupees(_thr469),
                           deposit_excess=rupees(max(_cash469 - _thr469, 0)))
        return jsonify(**_out469)
    refresh_missing_days(con, CLINIC_UNIT)
'''),
    ('''    # S469 (F-707's last part, the clinic twin of F-127): reception's entry page reads this for ONE deposit banner.
    # A non-checker is given that banner's figures and nothing else; the checker's answer below is unchanged.
    _u469 = current_user()
    if "checker" not in roles_for(con, CLINIC_UNIT, _u469["user"], _u469["role"]):
        _due469 = bool(thr and cash_p > thr)
        _out469 = dict(ok=True, unit_name=CLINIC_NAME, deposit_due=_due469)
        if _due469:
            _out469.update(cash_in_hand=rupees(cash_p), deposit_threshold=rupees(thr),
                           deposit_excess=rupees(max(cash_p - thr, 0)))
        return jsonify(**_out469)
    return jsonify(ok=True, unit_name=CLINIC_NAME,
                   drawings_month_to_date=rupees(drawings_mtd),
''',
     '''    # S469 (F-707's last part, the clinic twin of F-127): reception's banner is answered at the top (S474).
    return jsonify(ok=True, unit_name=CLINIC_NAME,
                   drawings_month_to_date=rupees(drawings_mtd),
'''),
    # ---- 2. the ledger env back at teardown
    ('''    SCAN_DIR = _s461_scan_prev                                    # S461
    UPI_DIR, YESBANK_DIR = _s468_dirs_prev                        # S468
''',
     '''    SCAN_DIR = _s461_scan_prev                                    # S461
    UPI_DIR, YESBANK_DIR = _s468_dirs_prev                        # S468
    for _k474, _v474 in (("LEDGER_DIR", _f6_ledger_prev[0]), ("FINANCE_LEDGER_JSONL", _f6_ledger_prev[1])):   # S474
        if _v474 is None:
            os.environ.pop(_k474, None)
        else:
            os.environ[_k474] = _v474
    LEDGER_JSONL = _f6_ledger_prev[2]                              # S474
'''),
    # ---- 3. the unused constant
    ('''#     attribution. The tender vocabulary is CLINIC_TENDERS below — a later
''',
     '''#     attribution. The tender vocabulary is CLINIC_TENDERS_ALL below — a later
'''),
    ('''CLINIC_TENDERS = ("cash", "upi")     # C1 vocabulary, kept for the compat path
''',
     ''''''),
    # ---- 4. the three apply paths commit once per day; the loaders no longer commit under them
    ('''            res = finance_ingest.ingest_day(
                con, UNIT, iso, "marg_export", day["lines_csv"], run_by=by,
                source_ref="autoreplay:%s" % (row["file_md5"] or "")[:8])
''',
     '''            res = finance_ingest.ingest_day(
                con, UNIT, iso, "marg_export", day["lines_csv"], run_by=by,
                source_ref="autoreplay:%s" % (row["file_md5"] or "")[:8], commit=False)   # S474 (F-716)
'''),
    ('''            n_lines = finance_returns.load_lines(con, UNIT, iso, irows,
                                                 batch_id=res.get("batch_id"))
            if irows and n_lines == 0:
                con.rollback(); continue
''',
     '''            n_lines = finance_returns.load_lines(con, UNIT, iso, irows,
                                                 batch_id=res.get("batch_id"), commit=False)   # S474 (F-716)
            if irows and n_lines == 0:
                con.rollback(); continue
'''),
    ('''                res = finance_ingest.ingest_day(con, UNIT, iso, "marg_export", lbuf.getvalue(),
                                                run_by=u["user"],
                                                source_ref="portal:" + f.filename[:60])
''',
     '''                res = finance_ingest.ingest_day(con, UNIT, iso, "marg_export", lbuf.getvalue(),
                                                run_by=u["user"],
                                                source_ref="portal:" + f.filename[:60], commit=False)   # S474 (F-716)
'''),
    ('''                n_lines = finance_returns.load_lines(con, UNIT, iso, irows, batch_id=res.get("batch_id"))
''',
     '''                n_lines = finance_returns.load_lines(con, UNIT, iso, irows, batch_id=res.get("batch_id"), commit=False)   # S474
'''),
    ('''            res = finance_ingest.ingest_day(con, UNIT, iso_d, "marg_export",
                                            d["lines_csv"], run_by=u["user"],
                                            source_ref="push:%s" % row["file_md5"][:8])
''',
     '''            res = finance_ingest.ingest_day(con, UNIT, iso_d, "marg_export",
                                            d["lines_csv"], run_by=u["user"],
                                            source_ref="push:%s" % row["file_md5"][:8], commit=False)   # S474 (F-716)
'''),
    ('''            n_lines = finance_returns.load_lines(con, UNIT, iso_d, irows,
                                                 batch_id=res.get("batch_id"))
''',
     '''            n_lines = finance_returns.load_lines(con, UNIT, iso_d, irows,
                                                 batch_id=res.get("batch_id"), commit=False)   # S474 (F-716)
'''),
    # ---- 5. a rejected file may be sent again
    ('''    dup = con.execute("SELECT id, status, received_at FROM marg_push_staging "
                      "WHERE file_md5=?", (file_md5,)).fetchone()
    if dup:
''',
     '''    dup = con.execute("SELECT id, status, received_at FROM marg_push_staging "
                      "WHERE file_md5=? AND status<>'rejected'", (file_md5,)).fetchone()   # S474: a refused file may come again
    if dup:
'''),
    ('''        cur = con.execute(
            "INSERT INTO marg_push_staging (unit, file_md5, filename_hint, "
            "status, survey_json, parsed_json) VALUES (?,?,?, 'pending', ?,?)",
            (UNIT, file_md5, f.filename[:80], survey_json, parsed_json))
''',
     '''        con.execute("DELETE FROM marg_push_staging WHERE file_md5=? AND status='rejected'", (file_md5,))   # S474: it reads now
        cur = con.execute(
            "INSERT INTO marg_push_staging (unit, file_md5, filename_hint, "
            "status, survey_json, parsed_json) VALUES (?,?,?, 'pending', ?,?)",
            (UNIT, file_md5, f.filename[:80], survey_json, parsed_json))
'''),
]

INGEST_EDITS = [
    ('''def ingest_day(con, unit, business_date, adapter, payload, run_by="system",
               source_ref=None, now=None):
    """Run one adapter over one day. Returns a summary dict.
    Re-running supersedes the previous batch for that day rather than duplicating."""
''',
     '''def ingest_day(con, unit, business_date, adapter, payload, run_by="system",
               source_ref=None, now=None, commit=True):
    """Run one adapter over one day. Returns a summary dict.
    Re-running supersedes the previous batch for that day rather than duplicating.
    S474 (F-716): commit=False leaves the day's writes open for the caller to commit -- or roll back -- as one."""
'''),
    ('''    reconcile_day_attribution(con, unit, business_date, now)
    con.commit()
    return dict(ok=True, batch_id=batch_id, adapter=adapter, rows_read=len(lines),
''',
     '''    reconcile_day_attribution(con, unit, business_date, now)
    if commit:
        con.commit()
    return dict(ok=True, batch_id=batch_id, adapter=adapter, rows_read=len(lines),
'''),
]

RETURNS_EDITS = [
    ('''def load_lines(con, unit, business_date, rows, batch_id=None):
    """Store the drug lines from a Button B export.
''',
     '''def load_lines(con, unit, business_date, rows, batch_id=None, commit=True):
    """Store the drug lines from a Button B export. S474 (F-716): commit=False leaves them for the caller to commit.
'''),
    ('''        n += 1
    con.commit()
    return n
''',
     '''        n += 1
    if commit:
        con.commit()
    return n
'''),
]

BACKFILL_EDITS = [
    ('''            res = finance_ingest.ingest_day(
                con, a.unit, iso, "marg_export", lbuf.getvalue(),
                run_by="marg_backfill_S183",
                source_ref=os.path.basename(a.xls))
''',
     '''            res = finance_ingest.ingest_day(
                con, a.unit, iso, "marg_export", lbuf.getvalue(),
                run_by="marg_backfill_S183",
                source_ref=os.path.basename(a.xls), commit=False)   # S474 (F-716): one commit per day, below
'''),
    ('''            n_lines = finance_returns.load_lines(con, a.unit, iso, irows, batch_id=batch_id)
            # load_lines commits; if it read zero from a non-empty item set, that
            # is the silent-zero trap on the LINE side — undo the whole day.
''',
     '''            n_lines = finance_returns.load_lines(con, a.unit, iso, irows, batch_id=batch_id, commit=False)   # S474
            # if it read zero from a non-empty item set, that
            # is the silent-zero trap on the LINE side — undo the whole day.
'''),
    ('''            if not irows:
                con.commit()     # bills-only day; load_lines never ran to commit

''',
     '''            con.commit()     # S474: the day's bills and lines go in together, or not at all

'''),
]


def apply(src, edits, what):
    for n, (old, new) in enumerate(edits, 1):
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! %s anchor %d was found %d time(s), expected 1 - nothing written" % (what, n, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 5:
        raise SystemExit("usage: apply_s474.py <finance_app.py> <finance_ingest.py> <finance_returns.py> <marg_backfill.py>")
    plan = [("finance_app.py", sys.argv[1], APP_EDITS), ("finance_ingest.py", sys.argv[2], INGEST_EDITS),
            ("finance_returns.py", sys.argv[3], RETURNS_EDITS), ("marg_backfill.py", sys.argv[4], BACKFILL_EDITS)]
    outs = []
    for name, path, edits in plan:
        raw = open(path, "rb").read()
        have = hashlib.md5(raw).hexdigest()
        if have != FROM[name]:
            raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM[name]))
        out = apply(raw.decode("utf-8"), edits, name).encode("utf-8")
        compile(out, path, "exec")
        outs.append((name, path, raw, out, len(edits)))
    for name, path, raw, out, n in outs:                   # all four verified before any is written
        with open(path, "wb") as fh:
            fh.write(out)
        print("%s %s -> %s (%d edits; %+d bytes)" % (name, hashlib.md5(raw).hexdigest()[:8], hashlib.md5(out).hexdigest()[:8], n, len(out) - len(raw)))


if __name__ == "__main__":
    main()
