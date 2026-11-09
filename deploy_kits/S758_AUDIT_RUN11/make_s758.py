#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s758.py -- builds kit S758_AUDIT_RUN11's three files from the LIVE bytes (the 09-Nov bundle; every base pinned by md5).

  python3 make_s758.py <dir holding the live finance_ingest.py, code_bundle.py, clinic_health_report.py> <out dir>

  finance_ingest.py        2 edits (AF-37): the S672 savepoint's failure is no longer silent -- the day gets an OPEN, high
                                   recon_exception 'noncash_at_ingest' ("do not approve until this clears") and the journal a line;
                                   the next good ingest of that day resolves it
  code_bundle.py           2 edits (ask 3): after the nightly bundle is shipped, two owner-owned slots in the same Drive folder
                                   are filled -- code_nightly.MD5SUMS (the bundle's own manifest) and finance_summary.json (counts
                                   and day totals of finance.db, read-only, no patient name or ID); a failure there is a WARNING
                                   line, never the bundle's failure
  clinic_health_report.py  1 edit (AF-36): the watchman writes '[YYYY-MM-DD HH:MM:SS] ...'; the 24-hour filter read s[:19] and,
                                   finding no time, showed EVERY line 'to be safe' -- July's included. It now reads the bracketed
                                   time; a line with no time at all is counted, not shown.
Each base must be the pinned live file and each piece must occur exactly once, or nothing is written."""
import hashlib
import os
import sys

BASE = {"finance_ingest.py": "029f5c203508a2fe40946737d3550c6a", "code_bundle.py": "d6f94b121ec814469e61a01e58791db7",
        "clinic_health_report.py": "27cbc9e4cb00b9c62ed85832bcc843ec"}

# ------------------------------------------------------------------------------------------------ finance_ingest.py
I1_OLD = '''    try:
        con.execute("SAVEPOINT s672_noncash")
        try:
            import day_resync as _dr672                                   # noqa: PLC0415
            _dr672.at_ingest(con, unit, business_date)
            con.execute("RELEASE SAVEPOINT s672_noncash")
        except Exception:                                                 # noqa: BLE001
            con.execute("ROLLBACK TO SAVEPOINT s672_noncash")
            con.execute("RELEASE SAVEPOINT s672_noncash")
    except Exception:                                                     # noqa: BLE001
        pass
    if commit:'''
I1_NEW = '''    # S758 (AF-37, the 09-Nov audit): the failure is no longer silent -- the day carries an open exception and the journal a line (v1).
    try:
        con.execute("SAVEPOINT s672_noncash")
        try:
            import day_resync as _dr672                                   # noqa: PLC0415
            _dr672.at_ingest(con, unit, business_date)
            con.execute("RELEASE SAVEPOINT s672_noncash")
            _s758_noncash_mark(con, unit, business_date, None)
        except Exception as _ex672:                                       # noqa: BLE001
            con.execute("ROLLBACK TO SAVEPOINT s672_noncash")
            con.execute("RELEASE SAVEPOINT s672_noncash")
            _s758_noncash_mark(con, unit, business_date, _ex672)
    except Exception as _ex672b:                                          # noqa: BLE001
        _s758_noncash_mark(con, unit, business_date, _ex672b)
    if commit:'''

I2_OLD = '''def reconcile_day_attribution(con, unit, business_date, now=None):'''
I2_NEW = '''S758_KIND = "noncash_at_ingest"


def _s758_noncash_mark(con, unit, business_date, ex):
    """S758 (AF-37): the S672 deduction at ingest failed (ex) or ran (None). A failure opens a HIGH recon_exception on the day,
    where the approver and the console look, and writes one journal line; a later good ingest of the day resolves it. Never
    raises -- the ingest stands exactly as before whatever happens here."""
    import sys as _sys                                                    # noqa: PLC0415
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    try:
        if ex is None:
            con.execute("UPDATE recon_exception SET status='resolved', resolution='the deduction ran at a later ingest', "
                        "closed_at=? WHERE unit=? AND business_date=? AND kind=? AND status='open'",
                        (now, unit, business_date, S758_KIND))
            return
        what = "%s: %s" % (type(ex).__name__, str(ex)[:160])
        print("S758 noncash-at-ingest FAILED unit=%s day=%s -- %s" % (unit, business_date, what), file=_sys.stderr, flush=True)
        con.execute(
            "INSERT INTO recon_exception (unit, business_date, kind, severity, status, detail, opened_at) "
            "VALUES (?,?,?, 'high', 'open', ?, ?) ON CONFLICT(unit, business_date, kind) DO UPDATE SET severity='high', "
            "status='open', detail=excluded.detail, opened_at=excluded.opened_at, resolution=NULL, closed_at=NULL",
            (unit, business_date, S758_KIND,
             "The home / procedure medicine bills were NOT deducted at ingest (%s). The 30-minute re-try works only while the "
             "day is NOT approved -- do not approve this day until this clears (S758, F-1037)." % what, now))
    except Exception as _e:                                               # noqa: BLE001
        try:
            print("S758 noncash-at-ingest: could not record (%s)" % type(_e).__name__, file=_sys.stderr, flush=True)
        except Exception:                                                 # noqa: BLE001
            pass


def reconcile_day_attribution(con, unit, business_date, now=None):'''

# ------------------------------------------------------------------------------------------------ code_bundle.py
B1_OLD = '''    log("held on Drive: %s (%d revisions = restore points)" % (SLOT, nrev))
'''
B1_NEW = '''    log("held on Drive: %s (%d revisions = restore points)" % (SLOT, nrev))
    try:                                                     # S758 (the 09-Nov audit, ask 3): the auditor's two small siblings
        s758_siblings(d, fid, path, summary)
    except Exception as ex:                                  # noqa: BLE001 -- the bundle above stands; this is extra
        log("S758 WARNING: the siblings were not shipped:", type(ex).__name__, str(ex)[:200])


# ------------------------------------------------------------------------------------------------ S758: the auditor's eyes
# THE AUDIT (runs 10 and 11, 02/09-Nov-2026): the auditor reads Drive through a channel capped at 10 MB, and the bundle (10.6 MB)
# and the database copy (11.3 MB) are past it. Two small files go beside them every night, each an OWNER-OWNED slot the service
# account updates in place (it cannot create files): code_nightly.MD5SUMS -- the bundle's own manifest, so any file's live md5
# can be checked without the tarball; finance_summary.json -- counts and day totals of finance.db, opened READ-ONLY, with no
# patient name, no clinic ID, no phone and no free text in it. A missing slot is a WARNING line, never the bundle's failure.
S758_SUMS = "code_nightly.MD5SUMS"
S758_SUMMARY = "finance_summary.json"
S758_DAYS = 62
S758_DB = under_root("root/finance/finance.db")


def s758_md5sums_text(path, summary):
    with tarfile.open(path, "r:gz") as tf:
        rows = tf.extractfile(tf.getmember(MANIFEST)).read().decode("utf-8")
    head = ("# code_nightly.MD5SUMS -- S758. The manifest of code_nightly.tar.gz shipped %s: %d files, tar md5 %s,"
            " finance_app.py %s. One row per file: md5, two spaces, the path inside the bundle (= the box path without"
            " the leading slash).\\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), summary["files"], summary["tar_md5"],
                                       summary["finance_app_md5"]))
    return head + rows


def s758_summary(db_path=None):
    """Counts and day totals of finance.db, read-only. Every section is its own try: one bad read is an 'error' entry."""
    import sqlite3                                           # noqa: PLC0415
    db_path = db_path or S758_DB
    con = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    out = {"kit": "S758", "built": time.strftime("%Y-%m-%d %H:%M:%S"), "host": socket.gethostname(),
           "what": "counts and day totals of finance.db (read-only); no patient name, clinic ID, phone or free text",
           "days_back": S758_DAYS}

    def q(sql, args=()):
        return [dict(r) for r in con.execute(sql, args)]

    def section(name, fn):
        try:
            out[name] = fn()
        except Exception as ex:                               # noqa: BLE001
            out[name] = {"error": "%s: %s" % (type(ex).__name__, str(ex)[:120])}
    try:
        since = q("SELECT date('now','localtime','-%d days') d" % S758_DAYS)[0]["d"]

        def tables():
            got = {}
            for r in q("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
                got[r["name"]] = q('SELECT COUNT(*) n FROM "%s"' % r["name"].replace('"', ''))[0]["n"]
            return got

        def days():
            d = {}
            for r in q("SELECT id, unit, business_date, status, approved_at, entered_at FROM day_entry WHERE business_date>=? "
                       "ORDER BY business_date, unit", (since,)):
                d.setdefault(r["business_date"], {})[r["unit"]] = {
                    "status": r["status"], "approved": bool(r["approved_at"]), "entered_at": r["entered_at"],
                    "approved_at": r["approved_at"], "_id": r["id"]}
            for day, units in d.items():
                for unit, e in units.items():
                    i = e.pop("_id")
                    e["lines"] = {"%s|%s" % (x["service"], x["mode"]): [x["n"], x["p"]] for x in
                                  q("SELECT service, mode, COUNT(*) n, SUM(amount_p) p FROM day_line WHERE day_entry_id=? "
                                    "GROUP BY service, mode", (i,))}
                    e["sale_items"] = {"%s|%s" % (x["service"], x["mode"]): [x["n"], x["p"]] for x in
                                       q("SELECT service, mode, COUNT(*) n, SUM(amount_p) p FROM sale_item WHERE day_entry_id=? "
                                         "GROUP BY service, mode", (i,))}
                    e["ingest"] = [[x["status"], x["n"], x["p"]] for x in
                                   q("SELECT status, COUNT(*) n, SUM(total_p) p FROM ingest_batch WHERE day_entry_id=? "
                                     "GROUP BY status", (i,))]
                    e["noncash_bills"] = {x["head"]: x["n"] for x in
                                          q("SELECT head, COUNT(*) n FROM day_noncash_bill WHERE day_entry_id=? GROUP BY head", (i,))}
            return d

        def exceptions():
            return [[x["unit"], x["business_date"], x["kind"], x["severity"], x["status"]] for x in
                    q("SELECT unit, business_date, kind, severity, status FROM recon_exception WHERE business_date>=? OR status='open' "
                      "ORDER BY business_date, unit, kind", (since,))]

        def drawer():
            return {x["business_date"]: [x["counted_p"], x["expected_p"]] for x in
                    q("SELECT business_date, counted_p, expected_p FROM clinic_drawer_day WHERE business_date>=? ORDER BY business_date",
                      (since,))}
        section("tables", tables)
        section("days", days)
        section("exceptions", exceptions)
        section("clinic_drawer", drawer)
    finally:
        con.close()
    return out


def s758_ship(d, files, name, local_path):
    slot = files.get(name)
    if not slot:
        log("S758 WARNING: slot", name, "missing in the Drive folder -- the owner's account must create it once (the service"
            " account cannot); the local copy is", local_path)
        return False
    want = md5_file(local_path)
    d.update_content(slot["id"], local_path)
    got = d.get(slot["id"])
    if got.get("md5Checksum") != want:
        log("S758 WARNING:", name, "did not verify on read-back (drive %s vs local %s)" % (got.get("md5Checksum"), want))
        return False
    d.patch_meta(slot["id"], {"description": "S758 . %s . md5 %s . shipped %s" % (name, want, time.strftime("%F %T"))})
    log("S758 shipped ->", name, ".", os.path.getsize(local_path), "bytes . md5", want, ". verified by read-back")
    return True


def s758_siblings(d, fid, path, summary):
    files = {f["name"]: f for f in d.list(fid)}
    p1 = os.path.join(OUT_DIR, S758_SUMS)
    with open(p1 + ".tmp", "w", encoding="utf-8") as fh:
        fh.write(s758_md5sums_text(path, summary))
    os.replace(p1 + ".tmp", p1)
    os.chmod(p1, 0o600)
    s758_ship(d, files, S758_SUMS, p1)
    p2 = os.path.join(OUT_DIR, S758_SUMMARY)
    data = json.dumps(s758_summary(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(data) > 1024 * 1024:
        log("S758 WARNING:", S758_SUMMARY, "is %d bytes, over 1 MB -- not shipped" % len(data))
        return
    with open(p2 + ".tmp", "wb") as fh:
        fh.write(data)
    os.replace(p2 + ".tmp", p2)
    os.chmod(p2, 0o600)
    s758_ship(d, files, S758_SUMMARY, p2)
'''
B2_OLD = '''    elif mode == "list":
        list_mode()
    else:
        print("usage: code_bundle.py build|run|list")'''
B2_NEW = '''    elif mode == "list":
        list_mode()
    elif mode == "summary":                                  # S758: print what finance_summary.json would carry (no Drive)
        print(json.dumps(s758_summary(argv[2] if len(argv) > 2 else None), ensure_ascii=False, sort_keys=True, indent=1))
    else:
        print("usage: code_bundle.py build|run|list|summary")'''

# ------------------------------------------------------------------------------------------------ clinic_health_report.py
H1_OLD = '''                # try to parse the leading timestamp 'YYYY-MM-DD HH:MM:SS'
                try:
                    ts = datetime.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
                    ts = ts.replace(tzinfo=IST)
                    if ts >= cutoff:
                        out.append(s)
                except Exception:
                    # no parseable timestamp -> include it to be safe (fail-loud)
                    out.append(s)'''
H1_NEW = '''                # S758 (AF-36): the watchman writes '[YYYY-MM-DD HH:MM:SS] ...' -- the bracket made every line unparseable,
                # and every unparseable line was shown 'to be safe', so the mail listed July's events as the last 24 hours.
                try:
                    ts = datetime.datetime.strptime(s.lstrip("[")[:19], "%Y-%m-%d %H:%M:%S")
                    ts = ts.replace(tzinfo=IST)
                    if ts >= cutoff:
                        out.append(s)
                except Exception:
                    undated[0] += 1                  # counted, not shown: a line with no time cannot be placed in the window'''
H2_OLD = '''    out = []
    if not os.path.exists(WATCHDOG_LOG):
        return out
    cutoff = datetime.datetime.now(IST) - datetime.timedelta(hours=24)'''
H2_NEW = '''    out = []
    undated = [0]
    if not os.path.exists(WATCHDOG_LOG):
        return out
    cutoff = datetime.datetime.now(IST) - datetime.timedelta(hours=24)'''
H3_OLD = '''    except Exception as e:
        log("WARN reading watchdog log: %s" % e)
    return out'''
H3_NEW = '''    except Exception as e:
        log("WARN reading watchdog log: %s" % e)
    if undated[0]:
        out.append("(%d watchman line(s) with no readable time were left out -- S758)" % undated[0])
    return out'''

EDITS = {"finance_ingest.py": [(I1_OLD, I1_NEW), (I2_OLD, I2_NEW)],
         "code_bundle.py": [(B1_OLD, B1_NEW), (B2_OLD, B2_NEW)],
         "clinic_health_report.py": [(H2_OLD, H2_NEW), (H1_OLD, H1_NEW), (H3_OLD, H3_NEW)]}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(src, out):
    built = {}
    for name, edits in EDITS.items():
        raw = open(os.path.join(src, name), "rb").read()
        if md5(raw) != BASE[name]:
            sys.exit("STOP: %s is %s, not the pinned live %s -- nothing written" % (name, md5(raw)[:8], BASE[name][:8]))
        txt = raw.decode("utf-8")
        for i, (old, new) in enumerate(edits, 1):
            n = txt.count(old)
            if n != 1:
                sys.exit("STOP: %s edit %d: the piece occurs %d times, not once -- nothing written" % (name, i, n))
            txt = txt.replace(old, new, 1)
        built[name] = txt.encode("utf-8")
    os.makedirs(out, exist_ok=True)
    for name, b in built.items():
        open(os.path.join(out, name), "wb").write(b)
        print("%-24s %s -> %s  %d counted edit(s)" % (name, BASE[name][:8], md5(b), len(EDITS[name])))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
