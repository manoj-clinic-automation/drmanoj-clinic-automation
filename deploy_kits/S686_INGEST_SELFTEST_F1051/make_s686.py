#!/usr/bin/env python3
"""make_s686.py -- kit S686_INGEST_SELFTEST_F1051 (31-Oct-2026, the parent, S372).

Builds the new /root/finance/finance_ingest.py from the box's OWN live bytes.
ONE counted edit: the selftest section (from the '# --- selftest' rule line up
to, not including, 'if __name__ == "__main__":') is replaced whole. Nothing
above it -- ingest_day, the adapters, the ladder -- is touched; the walk proves
that function by function.

    python3 -B make_s686.py <root> <outdir>      -> <outdir>/finance/finance_ingest.py

Refuses (exit 2, nothing written) unless the live file is exactly FROM.
"""
import hashlib
import os
import sys

F = "finance/finance_ingest.py"
FROM = "ce01a9e1f8acd82370477a7468a6412b"
START = "# ----------------------------------------------------------------- selftest\n"
END = '\n\nif __name__ == "__main__":\n'

NEW_REGION = r'''# ----------------------------------------------------------------- selftest
# S686 / F-1051 -- the selftest is a REPORT, never a crash. Before S686 one
# check that found no row (fetchone() is None) raised a TypeError: the run
# stopped half way, printed no score, and skipped its clean-up, so every failed
# run left its throwaway copy of finance.db (patients) in the temp folder.
# Now: every lookup that can find nothing is a failed check; any other error in
# the database part is ONE failed check named with the error; the copy is
# removed in a finally, whatever happens.

def _one(con, sql, args=()):
    """The first column of the first row, or None when there is no row."""
    r = con.execute(sql, args).fetchone()
    return r[0] if r else None


def _selftest_db(con, check):
    """The checks that need a database. `con` is a THROWAWAY copy."""
    date = _one(con, "SELECT MAX(business_date) FROM day_entry WHERE unit='medical'")
    check("the copy has a medical day to test on", date is not None)
    sid = _one(con, "SELECT id FROM ingest_source WHERE unit='medical' AND adapter='marg_export'")
    check("the copy has the medical marg_export source", sid is not None)
    # The made-up patients carry IDs the clinic never issues (ZZ..., S686), checked
    # unused below, so "created" can pass on any copy of the store.
    taken = _one(con, "SELECT COUNT(*) FROM patient_ref WHERE clinic_id IN ('ZZ9471','ZZ5120')")
    check("the made-up clinic IDs are unused in the copy", taken == 0)
    if date is None or sid is None:
        return

    # configure a Marg-shaped export, purely as column mapping
    con.execute("UPDATE ingest_source SET active=1, config_json=? WHERE id=?",
                (json.dumps({"delimiter": ",", "date_format": "%d/%m/%Y"}), sid))
    for f, c, req in (("bill_no", "Bill No", 1), ("bill_date", "Bill Date", 0),
                      ("patient_name", "Customer", 1), ("amount", "Net Amt", 1),
                      ("description", "Particulars", 0)):
        con.execute("INSERT OR REPLACE INTO ingest_column_map (source_id, our_field, their_column, "
                    "transform, required) VALUES (?,?,?,?,?)",
                    (sid, f, c, "ddmmyyyy" if f == "bill_date" else None, req))
    con.commit()

    marg = ("Bill No,Bill Date,Customer,Particulars,Net Amt\n"
            "H-9001,13/08/2026,ZZ9471 Ramesh Kumar,Tab Calcium,Rs 450.00\n"
            "H-9002,13/08/2026,Sunita Devi (ZZ5120),Knee cap,\"1,250.00\"\n"
            "H-9003,13/08/2026,Walk in customer,Bandage,120\n"
            "H-9004,13/08/2026,,,\n")
    res = ingest_day(con, "medical", date, "marg_export", marg, run_by="selftest",
                     source_ref="marg_test.csv")
    check("marg export ingests", res["ok"])
    check("blank row skipped", res.get("rows_read") == 3)
    check("two identified lines accepted", res.get("accepted") == 2)
    check("unidentified line goes to review", res.get("review") == 1)
    check("attributed total right", res.get("attributed_p") == 45000 + 125000)

    pr = {r[0]: r[1] for r in con.execute("SELECT clinic_id, name FROM patient_ref")}
    check("patient ZZ9471 created", pr.get("ZZ9471") == "Ramesh Kumar")
    check("patient ZZ5120 created", pr.get("ZZ5120") == "Sunita Devi")

    rec = reconcile_day_attribution(con, "medical", date)
    check("attribution reconciled", rec is not None and rec["attributed_p"] == 170000)
    n = _one(con, "SELECT COUNT(*) FROM recon_exception WHERE unit='medical' AND "
                  "business_date=? AND kind='line_sum_vs_day_total' AND status='open'", (date,))
    check("unattributed remainder shouts", n == 1)

    # re-running supersedes rather than duplicating
    ingest_day(con, "medical", date, "marg_export", marg, run_by="selftest")
    tot = _one(con, "SELECT COUNT(*) FROM sale_item WHERE day_entry_id=("
                    "SELECT id FROM day_entry WHERE unit='medical' AND business_date=?)", (date,))
    check("re-run supersedes, no duplicates", tot == 2)
    sup = _one(con, "SELECT COUNT(*) FROM ingest_batch WHERE status='superseded'")
    check("old batch marked superseded", (sup or 0) >= 1)

    # a missing required column must fail loudly, not silently produce nothing
    bad = "Invoice,Name,Total\nX-1,4471 Ramesh,100\n"
    res3 = ingest_day(con, "medical", date, "marg_export", bad, run_by="selftest")
    check("wrong format fails loudly", (not res3["ok"]) and "not found" in (res3.get("error") or ""))
    still = _one(con, "SELECT COUNT(*) FROM sale_item WHERE day_entry_id=("
                      "SELECT id FROM day_entry WHERE unit='medical' AND business_date=?)", (date,))
    check("failed run does not destroy good lines", still == 2)

    # sarvam is honestly unavailable here rather than silently empty
    res4 = ingest_day(con, "medical", date, "sarvam_ocr", "x", run_by="selftest")
    check("sarvam reports unavailable", (not res4["ok"]) and res4.get("error"))

    # ------------------------------------------------------------------ S180
    # Sale returns. These run LAST on purpose: ingest_day supersedes the earlier
    # batch for a day and deletes what it produced, so anything asserted about
    # the previous batches has to have been asserted already.
    #
    # A Marg export carrying a credit note, written the way Marg writes one.
    # Before S180 the CN row was skipped outright and the day read as though no
    # refund had happened.
    marg_cn = ("Bill No,Bill Date,Customer,Particulars,Net Amt\n"
               "A002966,13/08/2026,ZZ9471 Ramesh Kumar,Tab Calcium,1150.00\n"
               "CN00167,13/08/2026,ZZ9471 Ramesh Kumar,Tab Calcium returned,-400.00\n"
               "A002970,13/08/2026,Sunita Devi (ZZ5120),Knee cap,1000.00\n")
    resr = ingest_day(con, "medical", date, "marg_export", marg_cn, run_by="selftest",
                      source_ref="marg_returns.csv")
    check("credit note is read, not skipped", resr.get("rows_read") == 3)
    check("credit note is accepted", resr.get("accepted") == 3)
    check("credit note counted as a return", resr.get("returns") == 1)
    check("return nets out of the attributed total",
          resr.get("attributed_p") == 115000 - 40000 + 100000)

    kinds = {r[0]: r[1] for r in con.execute(
        "SELECT source_ref, service FROM sale_item WHERE ingest_batch_id=?", (resr.get("batch_id"),))}
    check("return row marked pharmacy_return", kinds.get("CN00167") == "pharmacy_return")
    check("sale rows unchanged", kinds.get("A002966") == "pharmacy")

    stored = _one(con, "SELECT amount_p FROM sale_item WHERE source_ref='CN00167' "
                       "AND ingest_batch_id=?", (resr.get("batch_id"),))
    check("return stored as a positive magnitude", stored == 40000)

    view_p = _one(con, "SELECT attributed_p FROM v_day_attribution WHERE unit='medical' "
                       "AND business_date=?", (date,))
    check("the VIEW nets the return too (migration applied)",
          view_p == 115000 - 40000 + 100000)

    # S686 / F-1051 -- a return nobody could put a name to. WHERE it goes is the
    # owner's setting ingest.anonymous_to_walkin (S186 / F-114; unset = on), so
    # the test runs it BOTH ways on this throwaway copy, whatever the live
    # store says, and puts the copy's setting back after.
    marg_anon = ("Bill No,Bill Date,Customer,Particulars,Net Amt\n"
                 "CN00168,13/08/2026,,Returned,-77.00\n")
    key = "ingest.anonymous_to_walkin"
    saved = _setting(con, key, None)

    def _anon_run(flag):
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?, ?)", (key, flag))
        con.commit()
        return ingest_day(con, "medical", date, "marg_export", marg_anon, run_by="selftest",
                          source_ref="marg_anon_%s.csv" % flag)

    # ON -- as the live store runs it: accepted onto WALK-IN, as a return
    resa = _anon_run("1")
    check("unidentified return is not silently dropped", resa.get("rows_read") == 1)
    check("setting on: an unidentified return is accepted, not parked",
          resa.get("accepted") == 1 and resa.get("review") == 0)
    check("setting on: it is counted as a return", resa.get("returns") == 1)
    row = con.execute("SELECT s.service, s.amount_p, p.clinic_id FROM sale_item s "
                      "LEFT JOIN patient_ref p ON p.id=s.patient_ref_id "
                      "WHERE s.ingest_batch_id=?", (resa.get("batch_id"),)).fetchone()
    check("setting on: it lands on WALK-IN as a pharmacy_return of 77.00",
          row is not None and tuple(row) == ("pharmacy_return", 7700, WALK_IN))

    # OFF -- parked for a human, the return kept signed
    resb = _anon_run("0")
    check("setting off: an unidentified return goes to review",
          resb.get("review") == 1 and resb.get("accepted") == 0)
    rv = _one(con, "SELECT amount_p FROM sale_item_review WHERE ingest_batch_id=?",
              (resb.get("batch_id"),))
    check("setting off: review keeps the return signed", rv == -7700)

    if saved is None:
        con.execute("DELETE FROM setting WHERE key=?", (key,))
    else:
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?, ?)", (key, saved))
    con.commit()


def selftest(db_path="finance.db"):
    """Runs as an INSTALL GATE, so it must never touch the live store.
    ingest_day() commits internally by design, so a rollback at the end is NOT
    enough -- the whole thing runs on a throwaway copy that is deleted after,
    in a finally (S686 / F-1051)."""
    ok, fail = 0, []

    def check(name, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fail.append(name)

    # clinic id splitting -- the whole patient spine rests on this
    check("id before name", split_clinic_id("4471 Ramesh Kumar")[:2] == ("4471", "Ramesh Kumar"))
    check("id with dash", split_clinic_id("4471-Ramesh Kumar")[:2] == ("4471", "Ramesh Kumar"))
    check("id in brackets", split_clinic_id("Ramesh Kumar (4471)")[:2] == ("4471", "Ramesh Kumar"))
    check("prefixed id", split_clinic_id("AO4471 Sita Devi")[:2] == ("AO4471", "Sita Devi"))
    check("name only -> no id", split_clinic_id("Ramesh Kumar")[0] is None)
    check("id only -> no name", split_clinic_id("4471")[:2] == ("4471", None))
    check("blank is nothing", split_clinic_id("")[:2] == (None, None))

    # S180 -- sale returns must survive the junk filter that used to eat them
    check("zero is still junk", classify_amount(0) == (None, None))
    check("no amount is still junk", classify_amount(None) == (None, None))
    check("a sale keeps its sign", classify_amount(115000) == (115000, KIND_SALE))
    check("a negative is a RETURN", classify_amount(-115000) == (115000, KIND_RETURN))
    check("return service medical", service_for("medical", KIND_RETURN) == "pharmacy_return")
    check("return service lab", service_for("lab", KIND_RETURN) == "lab_test_return")
    check("sale service unchanged", service_for("medical", KIND_SALE) == "pharmacy")
    check("signed sale", signed(115000, KIND_SALE) == 115000)
    check("signed return", signed(115000, KIND_RETURN) == -115000)

    check("paise plain", paise("1234") == 123400)
    check("paise decimal", paise("1234.50") == 123450)
    check("paise rupee sign", paise("₹ 1,234.50") == 123450)
    check("paise Rs prefix", paise("Rs 900") == 90000)
    check("paise bracket negative", paise("(250)") == -25000)
    check("paise rejects text", paise("N/A") is None)

    check("date dmy", parse_date("13/08/2026") == dt.date(2026, 8, 13))
    check("date iso", parse_date("2026-08-13") == dt.date(2026, 8, 13))
    check("date rejects year 26", parse_date("13/08/0026") is None)

    if not os.path.exists(db_path):
        print("INGEST %d/%d passed (db tests skipped)" % (ok, ok + len(fail)))
        for f in fail:
            print("  FAIL:", f)
        return 0 if not fail else 1

    import shutil
    import tempfile
    live_db = db_path
    fd, tmp_db = tempfile.mkstemp(prefix="finance_ingest_smoke_", suffix=".db")
    os.close(fd)
    con = None
    try:
        shutil.copyfile(live_db, tmp_db)
        con = sqlite3.connect(tmp_db)
        con.execute("PRAGMA foreign_keys=ON")
        _selftest_db(con, check)
    except Exception as ex:                                        # noqa: BLE001
        fail.append("the database checks stopped: %s: %s" % (type(ex).__name__, ex))
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:                                      # noqa: BLE001
                pass
        for p in (tmp_db, tmp_db + "-journal", tmp_db + "-wal", tmp_db + "-shm"):
            try:
                os.remove(p)
            except OSError:
                pass
    print("INGEST %d/%d passed  (throwaway copy; %s untouched)"
          % (ok, ok + len(fail), os.path.basename(live_db)))
    for f in fail:
        print("  FAIL:", f)
    return 0 if not fail else 1
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) != 3:
        print("usage: make_s686.py <root> <outdir>")
        return 2
    root, out = argv[1], argv[2]
    src = os.path.join(root, F)
    raw = open(src, "rb").read()
    if md5(raw) != FROM:
        print("REFUSED: %s is %s, not FROM %s -- nothing written" % (src, md5(raw)[:8], FROM[:8]))
        return 2
    text = raw.decode("utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        print("REFUSED: the selftest boundaries are not each found exactly once -- nothing written")
        return 2
    a = text.index(START)
    b = text.index(END)
    if not a < b:
        print("REFUSED: the boundaries are out of order -- nothing written")
        return 2
    new = text[:a] + NEW_REGION.rstrip("\n") + "\n" + text[b:]
    dst = os.path.join(out, F)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(new.encode("utf-8"))
    print("BUILT %s  %s -> %s  (1 edit: the selftest section, %d -> %d bytes; above it unchanged)"
          % (F, FROM[:8], md5(new.encode("utf-8"))[:8], b - a, len(NEW_REGION.rstrip("\n")) + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
