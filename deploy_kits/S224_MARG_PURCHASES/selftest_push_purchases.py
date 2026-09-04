#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_push_purchases.py -- the manojz leg, proven offline.

Builds a temp archive under $HOME/tmp (or %TEMP%) from THREE real archived
exports -- the two SUPPLIER WISE August files (same period, two stamps: the
supersede case) and the BILL/ITEM WISE file -- plus a hand-written index.csv,
then exercises the parsers, the plan, the ledger, the dry run, the feed, the
vendor count, and the watchdog on a fake stale _last_pull.txt.

NOTHING HERE TOUCHES THE REAL ARCHIVE, LEDGER, PICTURE OR _last_pull.txt, and
nothing reaches the network: the only "server" used is 127.0.0.1:9, which
refuses instantly and proves the unreachable path records itself.

    python selftest_push_purchases.py [--archive DIR] [--margsync DIR]
"""
import argparse
import glob
import io
import json
import os
import re
import shutil
import sys
import tempfile
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import marg_purchase_rows as PR     # noqa: E402
import push_purchases as PP         # noqa: E402

DEF_ARCHIVE = PP.DEF_ARCHIVE
IST = PP.IST
OK = [0]
FAIL = []


def ck(label, cond, detail=""):
    if cond:
        OK[0] += 1
        print("  ok   %s" % label)
    else:
        FAIL.append(label)
        print("  FAIL %s %s" % (label, detail))


def _tmp_root():
    h = os.path.expanduser("~")
    t = os.path.join(h, "tmp")
    try:
        os.makedirs(t, exist_ok=True)
        return t
    except OSError:
        return tempfile.gettempdir()


def _pick(archive, sub, n):
    files = sorted(glob.glob(os.path.join(archive, sub, "*", "*.XLS")) +
                   glob.glob(os.path.join(archive, sub, "*", "*.xlsx")))
    return files[-n:] if files else []


def build_archive(real, dst):
    """Three real files, one index.csv, nothing else."""
    idx_cols = ("seen_at,type,variant,date_from,date_to,data_from,data_to,"
                "export_stamp,md5,verdict,reason,rows,archived_path,source_path,uploaded")
    # the two SUPPLIER WISE August exports (same period) and the BILL/ITEM WISE one
    sw = [p for p in _pick(real, "PURCHASE_SUPPLIERWISE", 5) if "2026-08-01_to_2026-08-31" in p][-2:]
    bi = _pick(real, "PURCHASE_BILLITEMWISE", 1)
    picked = [("PURCHASE_SUPPLIERWISE", p) for p in sw] + [("PURCHASE_BILLITEMWISE", p) for p in bi]
    rows = []
    for typ, p in picked:
        name = os.path.basename(p)
        m = re.search(r"__(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})__(\d{8}-\d{6})__", name)
        d = os.path.join(dst, typ, m.group(1)[:7])
        os.makedirs(d, exist_ok=True)
        shutil.copy2(p, os.path.join(d, name))
        with open(p, "rb") as fh:
            import hashlib
            md5 = hashlib.md5(fh.read()).hexdigest()
        rows.append("2026-09-04 00:00:00,%s,DEFAULT,%s,%s,,,%s,%s,VERIFIED,structural,0,%s,,"
                    % (typ, m.group(1), m.group(2), m.group(3), md5,
                       r"D:\nowhere\%s" % name))      # deliberately wrong: _resolve must rebuild it
    # one row that is NOT verified, and one of a non-purchase type -- both must be ignored
    rows.append("2026-09-04 00:00:00,PURCHASE_BILLWISE,DEFAULT,2026-01-01,2026-01-31,,,20260101-000000,"
                "abcdefabcdefabcdefabcdefabcdefab,UNKNOWN,,0,x,,")
    rows.append("2026-09-04 00:00:00,SALE_BILLWISE,DETAIL,2026-01-01,2026-01-01,,,20260101-000001,"
                "fedcbafedcbafedcbafedcbafedcbafe,VERIFIED,,0,x,,")
    with io.open(os.path.join(dst, "index.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write(idx_cols + "\r\n" + "\r\n".join(rows) + "\r\n")
    return picked


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    a = ap.parse_args(argv)
    if not os.path.isdir(a.archive):
        print("archive not found: %s" % a.archive)
        return 2
    root = os.path.join(_tmp_root(), "s224_selftest")
    shutil.rmtree(root, ignore_errors=True)
    arch = os.path.join(root, "MargArchive")
    ana = os.path.join(root, "_analysis")
    os.makedirs(arch)
    picked = build_archive(a.archive, arch)
    print("temp archive %s (%d real files)" % (arch, len(picked)))

    print("-- primitives (the shared parser, marg_purchase_rows)")
    ck("paise 1234.5 -> 123450", PR.paise(1234.5) == 123450)
    ck("paise '1,234.50' -> 123450", PR.paise("1,234.50") == 123450)
    ck("paise '  -' and '' -> 0 (credit bill, no cash)", PR.paise("  -") == 0 and PR.paise("") == 0)
    ck("billno 160.0 / '160.0' / 'a000163'",
       PR.billno(160.0) == "160" and PR.billno("160.0") == "160" and PR.billno("a000163") == "a000163")
    ck("norm collapses space, case, trailing dots", PR.norm("  L.K. drug   house. ") == "L.K. DRUG HOUSE")
    ck("iso_date strips the city overflow in 'BA03-08-2026'", PR.iso_date("BA03-08-2026") == "2026-08-03")
    ck("iso_date rejects junk", PR.iso_date("TOTAL") is None and PR.iso_date("") is None)
    ck("supplier_key joins 'X  BAREILLY' with 'X'", PR.supplier_key("JANTA PHARMACEUTICALS         BAREILLY")
       == PR.supplier_key("JANTA PHARMACEUTICALS"))

    print("-- parsers on the temp copies")
    sw = [p for t, p in picked if t == "PURCHASE_SUPPLIERWISE"]
    bi = [p for t, p in picked if t == "PURCHASE_BILLITEMWISE"]
    if sw:
        rep = PR.read_supplierwise(sw[-1])
        ck("SUPPLIERWISE rows sum to its GRAND TOTAL",
           rep["grand_amount_p"] is not None and PP.sum_rows_p("SUPPLIERWISE", rep["rows"]) == rep["grand_amount_p"],
           "%s vs %s" % (PP.sum_rows_p("SUPPLIERWISE", rep["rows"]), rep["grand_amount_p"]))
        ck("SUPPLIERWISE row shape", set(rep["rows"][0]) == {"supplier", "bill_date", "bill_no", "cash_p", "credit_p"})
        ck("SUPPLIERWISE carries the supplier down", all(r["supplier"] for r in rep["rows"]))
        ck("SUPPLIERWISE period read from the title", (rep["period_from"], rep["period_to"]) == ("2026-08-01", "2026-08-31"))
        ck("SUPPLIERWISE dates the overflowed 'BA' cell",
           any(r["supplier"].startswith("ESSENTIAL") and r["bill_date"] == "2026-08-03" for r in rep["rows"]))
    if bi:
        rep = PR.read_billitemwise(bi[0])
        ck("BILLITEMWISE rows sum to its TOTAL",
           rep["grand_amount_p"] is not None and PP.sum_rows_p("BILLITEMWISE", rep["rows"]) == rep["grand_amount_p"])
        ck("BILLITEMWISE every row dated, supplier None",
           all(r["bill_date"] and r["supplier"] is None for r in rep["rows"]))
        ck("BILLITEMWISE money in paise ints",
           all(isinstance(r["amount_p"], int) and isinstance(r["rate_p"], int) for r in rep["rows"]))
        want = {"bill_no", "bill_date", "supplier", "item", "packing", "batch", "expiry", "tax", "qty",
                "free", "rate_p", "discount_pct", "amount_p", "net_rate_p", "net_amount_p", "loose_qty",
                "purchase_rate_p", "direction"}
        ck("BILLITEMWISE row shape is the contract's", set(rep["rows"][0]) == want)
    # the two readers not in the temp set, read-only against the real archive
    iw = _pick(a.archive, "PURCHASE_ITEMWISE", 1)
    if iw:
        body = PR.payload(iw[0], "ITEMWISE", read_purchase=PP.MP.read_purchase)
        ck("ITEMWISE (real, read-only) rows, bill_date None, paise",
           body["rows"] and all(r["bill_date"] is None and isinstance(r["amount_p"], int) for r in body["rows"]))
    bw = _pick(a.archive, "PURCHASE_BILLWISE", 1)
    if bw:
        rep = PR.read_billwise(bw[0])
        ck("BILLWISE (real, read-only) rows sum to TOTAL",
           rep["grand_amount_p"] is not None and PP.sum_rows_p("BILLWISE", rep["rows"]) == rep["grand_amount_p"])
    try:
        PR.payload("x", "NOPE")
        ck("payload refuses an unknown type", False)
    except PR.Refused:
        ck("payload refuses an unknown type", True)

    print("-- plan, supersede, ledger")
    items = PP.plan(arch, {}, False)
    ck("plan sees exactly the 3 VERIFIED purchase rows (UNKNOWN and SALE ignored)", len(items) == 3, str(len(items)))
    ck("plan rebuilt the path when archived_path was wrong", all(it["path"] and os.path.isfile(it["path"]) for it in items))
    sws = [it for it in items if it["type"] == "SUPPLIERWISE"]
    ck("same type+period: older stamp marked superseded, newer not",
       len(sws) == 2 and sws[0]["superseded_by"] == sws[1]["stamp"] and sws[1]["superseded_by"] is None)
    ck("older stamp is sent FIRST", sws[0]["stamp"] < sws[1]["stamp"])
    ck("superseded export is still 'send' (server keeps history)", sws[0]["decision"] == "send")
    body = items[0]["body"]
    ck("body keys are the contract's",
       set(body) == {"type", "md5", "file", "period_from", "period_to", "export_stamp", "n_rows",
                     "grand_amount_p", "rows"})
    ck("body n_rows equals rows sent", body["n_rows"] == len(body["rows"]))
    ck("body file is a bare name, no path", "/" not in body["file"] and "\\" not in body["file"])
    led = {items[0]["md5"]: {"when": "2026-09-04T00:00:00", "http": 200, "result": "new"}}
    items2 = PP.plan(arch, led, False)
    ck("ledger http 200 -> skipped", items2[0]["decision"].startswith("skip: sent"))
    ck("--all re-sends it", PP.plan(arch, led, True)[0]["decision"] == "send")
    led400 = {items[0]["md5"]: {"when": "x", "http": 400, "result": "malformed"}}
    ck("ledger http 400 -> retried", PP.plan(arch, led400, False)[0]["decision"] == "send")

    print("-- dry run")
    rc = PP.main(["--dry-run", "--archive", arch, "--analysis", ana, "--base", "http://127.0.0.1:9/x"])
    sp = os.path.join(ana, PP.SAMPLE_NAME)
    ck("dry run exits 0 and writes the sample JSON", rc == 0 and os.path.isfile(sp))
    ck("dry run writes NO ledger", not os.path.exists(os.path.join(ana, PP.LEDGER_NAME)))
    txt = io.open(sp, encoding="utf-8").read()
    ck("sample JSON carries no 10-digit run (F-185)", re.search(r"\d{10}", txt) is None)
    ck("sample JSON parses and has rows", json.loads(txt)["rows"])

    print("-- send path, unreachable server")
    tokdir = os.path.join(root, "tok")
    os.makedirs(tokdir)
    with io.open(os.path.join(tokdir, "token.txt"), "w", encoding="utf-8") as fh:
        fh.write("selftest-token-not-real\n")
    PP.DEF_TOKEN_UNC = os.path.join(root, "no-such-share", "token.txt")
    PP.DEF_TOKEN_CACHE = os.path.join(tokdir, "token.txt")
    tok, where = PP.read_token()
    ck("read_token falls back to the cache", tok == "selftest-token-not-real" and where == "cache")
    rc = PP.main(["--archive", arch, "--analysis", ana, "--base", "http://127.0.0.1:9/x"])
    lp = os.path.join(ana, PP.LEDGER_NAME)
    ck("unreachable server -> exit 2", rc == 2, str(rc))
    ledger = PP.load_ledger(lp)
    ck("ledger records the failed attempt (http None, unreachable)",
       len(ledger) == 1 and list(ledger.values())[0]["http"] is None
       and "unreachable" in list(ledger.values())[0]["result"])
    ck("--verify against an unreachable server -> 2", PP.verify("http://127.0.0.1:9/x") == 2)

    print("-- feed and vendors")
    pf = os.path.join(root, "_last_pull.txt")
    with io.open(pf, "w", encoding="utf-8") as fh:
        fh.write("START 04-09-2026  6:40:01.44\nEND 04-09-2026  6:40:21.70 -- ok\nSTART 04-09-2026  7:50:01.00\n")
    when, note = PP.parse_last_pull(pf)
    ck("parse_last_pull takes the last END, not the trailing START",
       when == dt.datetime(2026, 9, 4, 6, 40, 21, tzinfo=IST) and note == "ok")
    fb = PP.feed_body(pf, dt.datetime(2026, 9, 4, 7, 30, tzinfo=IST))
    ck("feed 49 min -> asleep, ISO +05:30",
       fb["state"] == "asleep" and fb["pull_age_min"] == 49 and fb["pull_last"].endswith("+05:30"))
    fb = PP.feed_body(pf, dt.datetime(2026, 9, 4, 6, 50, tzinfo=IST))
    ck("feed 9 min -> ok", fb["state"] == "ok" and fb["pull_age_min"] == 9)
    ck("feed keys are the contract's", set(fb) == {"pull_last", "pull_age_min", "state", "host"})
    fb = PP.feed_body(os.path.join(root, "missing.txt"))
    ck("feed with no _last_pull -> asleep, null time", fb["state"] == "asleep" and fb["pull_last"] is None)
    vf = os.path.join(root, "vendors.json")
    with io.open(vf, "w", encoding="utf-8") as fh:
        json.dump({"pairs": {"A": "x1", "B": "x2", "C": " ", "": "x3"}, "missing": ["D"]}, fh)
    ck("vendor_pairs keeps only non-empty name AND number", PP.vendor_pairs(vf) == {"A": "x1", "B": "x2"})
    ck("--vendors --dry-run exits 0", PP.main(["--vendors", "--dry-run", "--vendors-file", vf]) == 0)

    print("-- watchdog on a fake stale pull (temp copy)")
    wd = None
    for cand in (os.path.join(os.path.dirname(os.path.abspath(a.archive)), "MargPull", "pull_watchdog.py"),
                 os.path.join(HERE, "pull_watchdog.py")):
        if os.path.isfile(cand):
            wd = cand
            break
    if wd is None:
        print("  (pull_watchdog.py not found next to the archive -- watchdog checks skipped)")
    else:
        sys.path.insert(0, os.path.dirname(wd))
        import pull_watchdog as WD
        pic = os.path.join(root, "MARG_PICTURE.txt")
        orig = "MARG SALE REPORTS -- the picture at 2026-09-04 06:40:21\r\narchive: x\r\n\r\nline\r\n"
        io.open(pic, "w", encoding="utf-8", newline="").write(orig)
        st = os.path.join(root, "_wd.txt")
        al = os.path.join(root, "_alarm.txt")
        t0 = dt.datetime(2026, 9, 4, 7, 30, tzinfo=IST)
        c = WD.check(pf, st, t0)
        ck("watchdog first run: pull 49 min old but no own stamp -> 'woke', not blamed",
           c["state"] == "woke" and c["just_woke"])
        WD.main(["--pull-file", pf, "--picture", pic, "--stamp-file", st, "--alarm-file", al,
                 "--logdir", os.path.join(root, "logs"), "--now", t0.isoformat(), "--no-feed"])
        ck("first run wrote no alarm", not os.path.exists(al) and not io.open(pic, encoding="utf-8").read().startswith("PULL"))
        t1 = dt.datetime(2026, 9, 4, 7, 45, tzinfo=IST)
        ck("15 min later, still stale -> asleep", WD.check(pf, st, t1)["state"] == "asleep")
        WD.main(["--pull-file", pf, "--picture", pic, "--stamp-file", st, "--alarm-file", al,
                 "--logdir", os.path.join(root, "logs"), "--now", t1.isoformat(), "--no-feed"])
        body = io.open(pic, encoding="utf-8", newline="").read()
        ck("red line prepended: 'PULL ASLEEP since 06:40 IST (64 min)'",
           body.startswith("PULL ASLEEP since 06:40 IST (64 min)\r\n"))
        ck("alarm file written", os.path.isfile(al))
        t2 = dt.datetime(2026, 9, 4, 8, 0, tzinfo=IST)
        WD.main(["--pull-file", pf, "--picture", pic, "--stamp-file", st, "--alarm-file", al,
                 "--logdir", os.path.join(root, "logs"), "--now", t2.isoformat(), "--no-feed"])
        body = io.open(pic, encoding="utf-8", newline="").read()
        ck("third run: ONE alarm line, updated, never stacked",
           body.count("PULL ASLEEP") == 1 and "(79 min)" in body)
        with io.open(pf, "a", encoding="utf-8") as fh:
            fh.write("END 04-09-2026  8:10:21.70 -- ok\n")
        t3 = dt.datetime(2026, 9, 4, 8, 15, tzinfo=IST)
        WD.main(["--pull-file", pf, "--picture", pic, "--stamp-file", st, "--alarm-file", al,
                 "--logdir", os.path.join(root, "logs"), "--now", t3.isoformat(), "--no-feed"])
        ck("pull wakes -> picture restored byte-identical (CRLF kept), alarm gone",
           io.open(pic, encoding="utf-8", newline="").read() == orig and not os.path.exists(al))
        # a PC that slept 3 hours: the pull is 3h old AND the watchdog is 3h old -> not blamed
        t4 = dt.datetime(2026, 9, 4, 11, 15, tzinfo=IST)
        ck("PC asleep 3 h (watchdog stamp also old) -> 'woke', no alarm",
           WD.check(pf, st, t4)["state"] == "woke")

    print("-- F-185 gate over this kit's own files")
    bad = []
    for f in sorted(glob.glob(os.path.join(HERE, "*.py"))):
        t = io.open(f, encoding="utf-8").read()
        if re.search(r"\d{10}", t):
            bad.append(os.path.basename(f))
    ck("no 10-digit run in any kit .py", not bad, str(bad))

    print()
    if FAIL:
        print("SELFTEST FAILED -- %d ok, %d failed: %s" % (OK[0], len(FAIL), FAIL))
        return 1
    print("SELFTEST PASSED -- %d checks OK" % OK[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
