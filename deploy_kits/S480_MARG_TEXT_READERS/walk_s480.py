#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s480.py -- kit S480_MARG_TEXT_READERS: the walk (the brief's section 9). Every section has a negative control on the OLD file.

  python -B walk_s480.py manojz ...   sections 1, 2, 3, 4a, 5, 6, 7 -- on Dr Manoj's PC, against the medical PC's captured texts and
                                      MargArchive. The samples are READ where they lie; nothing of them is printed (counts, verdicts
                                      and titles only) and nothing leaves the PC. Run at build time; its output is in the report.
  python -B walk_s480.py server ...   sections 4, 8 -- on the server, on scratch copies (finance.db by the backup API; its own rows,
                                      keyed W480; a walk-only login store and secret). Run by the installer before anything is placed.

Nothing is imported from inside deploy_kits: every module is copied into the work folder first (CLAUDE.md rule 11).
"""
import argparse
import datetime as dt
import glob
import hashlib
import html as _html
import importlib.util
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys

TAG = "W480JSON "
OLD_TXT = "ed17bb763c202f81cb8b3708fac61b52"
OLD_WATCH = "297cc3d9ff5edddc894390426bdc463a"
OLD_SIG = "64943ac6719a0f2ee06a15ef56d8c3d1"
ROUTER = "318086e36b0088f2da57b95d19a86b98"
USERS = {"darpan": "staff", "shavez": "manager", "amir": "staff", "manoj": "doctor"}
FAR_DAY, FAR_TODAY = "2031-03-05", "2031-03-06"          # a day the copies hold nothing of: the walk's own rows live there
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + mask(str(got))[:600] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def md5b(b):
    return hashlib.md5(b).hexdigest()


def md5f(p):
    return md5b(open(p, "rb").read())


def load(name, path):
    """A module from a FILE, under its own name -- two versions of one module side by side."""
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def steady(h):
    h = re.sub(r"\b\d{1,2}:\d\d(:\d\d)?\b", "HH:MM", h or "")
    return re.sub(r"\b[0-9a-f]{16,}\b", "HEX", h)


def xls_write(mt, rows, path):
    with open(path, "wb") as fh:
        fh.write(mt.ole2(mt.workbook_stream(rows)))


# ============================================================================================================================ manojz
def xrows(path):
    import xlrd
    sh = xlrd.open_workbook(path).sheet_by_index(0)
    return [[(c.value.strip() if c.ctype == 1 else c.value) for c in sh.row(r)] for r in range(sh.nrows)]


def norm(R):
    """The prototype's normalisation: strings stripped, a whole number a float, all-blank rows dropped."""
    R = [[(float(x) if isinstance(x, (int, float)) else x.strip()) for x in r] for r in R]
    return [r for r in R if any(x != "" for x in r)]


def drop_advert(X):
    if X and isinstance(X[-1][0], str) and re.search(r"MARG|QRCODE", X[-1][0], re.I):
        return X[:-1]
    return X


def sample(ref, stamp):
    f = [x for x in glob.glob(os.path.join(ref, stamp + "*.txt")) if not x.endswith(".why.txt")]
    return f[0] if f else None


def manojz(a):
    W = os.path.abspath(a.work)
    assert os.sep + "_scratch" + os.sep in W + os.sep, "the work folder must be inside the repository's _scratch: " + W
    if os.path.isdir(W):
        shutil.rmtree(W)
    for d in ("new", "old", "router", "out", "spine"):
        os.makedirs(os.path.join(W, d))
    shutil.copy(os.path.join(a.kit, "marg_txt.py"), os.path.join(W, "new", "marg_txt.py"))
    shutil.copy(os.path.join(a.kit, "marg_watch.py"), os.path.join(W, "new", "marg_watch.py"))
    shutil.copy(os.path.join(a.mirror, "marg_txt.py"), os.path.join(W, "old", "marg_txt.py"))
    shutil.copy(os.path.join(a.mirror, "marg_watch.py"), os.path.join(W, "old", "marg_watch.py"))
    for f in ("marg_router.py", "xlsx_stdlib.py"):
        shutil.copy(os.path.join(a.pull, f), os.path.join(W, "router", f))
    shutil.copy(os.path.join(a.kit, "marg_report.py"), os.path.join(W, "router", "marg_report.py"))
    shutil.copy(os.path.join(a.kits, "S331_SPINE", "marg_read.py"), os.path.join(W, "spine", "marg_read.py"))
    check("the OLD files are the ones the medical PC runs (marg_txt ed17bb76, marg_watch 297cc3d9); the router is 318086e3, not edited",
          md5f(os.path.join(W, "old", "marg_txt.py")) == OLD_TXT and md5f(os.path.join(W, "old", "marg_watch.py")) == OLD_WATCH
          and md5f(os.path.join(W, "router", "marg_router.py")) == ROUTER and md5f(a.old_signatures) == OLD_SIG)
    NEW = load("marg_txt_new", os.path.join(W, "new", "marg_txt.py"))
    OLD = load("marg_txt_old", os.path.join(W, "old", "marg_txt.py"))
    sys.path.insert(0, os.path.join(W, "router"))
    import marg_router as R                                             # noqa: E402
    import marg_report as MR                                            # noqa: E402
    MR._open_sheet = R.open_sheet
    cap = os.path.join(a.mirror, "_captured_txt")
    ref = os.path.join(cap, "refused")

    # ------------------------------------------------------------------------------------------------------------------ 1
    print("-- 1  byte equality of the three live kinds (every text the medical PC took since 24-Sep)")
    texts = sorted(glob.glob(os.path.join(cap, "*.txt")))
    spool = {}
    for p in glob.glob(os.path.join(a.archive, "_spool", "*_TXT__*.XLS")):
        m = re.match(r"^\d{8}-\d{6}__(.+_TXT)__[0-9a-f]{8}__[0-9a-f]{8}\.XLS$", os.path.basename(p), re.I)
        if m:
            spool[m.group(1)] = p
    same = kinds = paired = pair_same = 0
    diff = []
    for p in texts:
        raw = open(p, "rb").read()
        try:
            xo, io_ = OLD.convert(raw)
        except Exception as ex:                                         # noqa: BLE001
            diff.append((os.path.basename(p)[:15], "OLD raised %s" % ex.__class__.__name__))
            continue
        xn, in_ = NEW.convert(raw, exported_at=os.path.getmtime(p))
        same += xo == xn
        kinds += io_["kind"] == in_["kind"] and in_["kind"] in ("SALE", "STOCK", "ORDER")
        if xo != xn:
            diff.append((os.path.basename(p)[:15], "bytes differ"))
        key = re.sub(r"__[0-9a-f]{8}\.txt$", "", os.path.basename(p))
        if key in spool:
            paired += 1
            pair_same += open(spool[key], "rb").read() == xn
    check("every captured text converts to the SAME BYTES by marg_txt S480 and by ed17bb76 (%d texts; 21 when the brief was written)"
          % len(texts), len(texts) >= 21 and same == len(texts) and kinds == len(texts) and not diff, (same, len(texts), diff[:3]))
    check("S480's output is the kept conversion in MargArchive\\_spool, paired by the capture stamp and slot in the spool name (%d pairs)"
          % paired, paired >= 1 and pair_same == paired, (pair_same, paired))
    raw = open(texts[-1], "rb").read()
    t2 = re.sub(rb"(\d)\.(\d)(\d)(\s)", lambda m: m.group(1) + b"." + m.group(2) + (b"1" if m.group(3) != b"1" else b"2") + m.group(4), raw, count=1)
    try:
        x2 = NEW.convert(t2, exported_at=os.path.getmtime(texts[-1]))[0]
        neg = x2 != NEW.convert(raw, exported_at=os.path.getmtime(texts[-1]))[0]
    except NEW.Refused:
        neg = True                                                      # a changed figure no longer adds up: refused
    check("negative control: one figure changed in a text -> other bytes (or the reader's own totals refuse it)", t2 != raw and neg)

    # ------------------------------------------------------------------------------------------------------------------ 2
    print("-- 2  the cutter against Marg's own Excel (the prototype's normalisation)")

    def text_sheet(stamp, mutate=None):
        raw = open(sample(ref, stamp), "rb").read()
        if mutate:
            raw = mutate(raw)
        p = os.path.join(W, "out", "cut_%s%s.XLS" % (stamp[9:], "_neg" if mutate else ""))
        with open(p, "wb") as fh:
            fh.write(NEW.convert(raw)[0])
        return p

    def one_figure(raw):
        ms = list(re.finditer(rb"\d+\.\d\d(?=\r?\n)", raw))
        m = ms[len(ms) // 2]
        v = m.group(0)
        return raw[:m.start()] + v[:-1] + (b"1" if v[-1:] != b"1" else b"2") + raw[m.end():]
    want_cells = {"20261004-093801": 72, "20261004-094002": 564, "20261004-141519": 3505}
    tot = 0
    for stamp, xg, skip in (("20261004-093801", "PURCHASE_BILLWISE/*/*20261004-093939*", 3),
                            ("20261004-094002", "PURCHASE_ITEMWISE/*/*20261004-094014*", 3),
                            ("20261004-141519", "SALT_WISE_ITEM_LIST/*/*20261004-141631*", 0)):
        xf = glob.glob(os.path.join(a.archive, *xg.split("/")))
        if not xf or not sample(ref, stamp):
            check("the same-moment pair %s is on this PC" % stamp[9:], False)
            continue
        X = drop_advert(norm(xrows(xf[0]))[skip:])
        T = norm(xrows(text_sheet(stamp)))
        cells = sum(len(r) for r in X)
        bad = [i for i in range(max(len(T), len(X))) if (T[i] if i < len(T) else None) != (X[i] if i < len(X) else None)]
        tot += cells
        check("%s text  =  Marg's own Excel of the same moment, cell for cell: %d rows, %d cells, %d rows differ"
              % (stamp[9:], len(X), cells, len(bad)), not bad and cells == want_cells[stamp] and len(T) == len(X), (len(T), len(X), cells))
        Tn = norm(xrows(text_sheet(stamp, one_figure)))
        nb = sum(1 for i in range(max(len(Tn), len(X))) for j in range(len(X[0]))
                 if ((Tn[i][j] if i < len(Tn) and j < len(Tn[i]) else None) != (X[i][j] if i < len(X) else None)))
        check("   negative control: one figure changed in that text -> exactly one cell differs", nb == 1, nb)
    check("the three same-moment pairs come to 4,141 cells", tot == 4141, tot)
    sys.path.insert(0, os.path.join(W, "spine"))
    import marg_read                                                    # noqa: E402  (the spine's certified reader, 7ec9b325)
    for stamp, xg, fam, floor, key in (("20261004-155650", "ITEM_MASTER/*/*20260918-204558*", "ITEM_MASTER", 0.97,
                                        lambda d: (d["name"], d["packing"], d["company"])),
                                       ("20261004-143140", "CATEGORY_WISE_ITEM_LIST/*/*20260918-074830*", "CATEGORY_WISE_ITEM_LIST", 0.90,
                                        lambda d: (d["group"], d["name"], d["packing"], d["p_rate"], d["s_rate"], d["mrp"]))):
        xf = glob.glob(os.path.join(a.archive, *xg.split("/")))
        if not xf or not sample(ref, stamp):
            check("the other-day pair %s is on this PC" % stamp[9:], False)
            continue
        ft, Rt, _m = marg_read.read_file(text_sheet(stamp))
        fx, Rx, _m = marg_read.read_file(xf[0])
        it, ix = [key(d) for d in Rt.data["items"]], [key(d) for d in Rx.data["items"]]
        found = sum(1 for k in ix if k in set(it))
        check("%s (text 04-Oct, Excel 18-Sep): the spine's reader reads both as %s; of the Excel's %d items %d are "
              "in the text identical at the reader's output (the rest changed in Marg between the two days)"
              % (fam, ft, len(ix), found), ft == fx == fam and (Rt.ok and Rx.ok or fam != "ITEM_MASTER") and found >= floor * len(ix),
              (len(it), len(ix), found, "text ok=%s" % Rt.ok, "excel ok=%s" % Rx.ok, [re.sub(r" at row \d+", "", f) for f in Rt.failed()][:3]))
        hit = next(d for d in Rx.data["items"] if key(d) in set(it) and len(d["name"]) > 6)   # an item both hold: one figure of ITS line is changed

        def one_of_its(raw, name=hit["name"].encode("latin-1")):
            i = raw.index(b"  " + name + b" ")
            j = raw.index(b"\n", i)
            line = raw[i:j].rstrip(b"\r")
            k = max(m.start() for m in re.finditer(rb"\d", line))
            return raw[:i + k] + (b"1" if line[k:k + 1] != b"1" else b"2") + raw[i + k + 1:]
        _f2, Rn, _m = marg_read.read_file(text_sheet(stamp, one_of_its))
        check("   negative control: one figure changed on one item's line in that text -> one item fewer found",
              sum(1 for k in ix if k in set(key(d) for d in Rn.data["items"])) == found - 1)
    print("   (the known nuance, named: a company name overrunning two column heads -- Marg's sheet puts its first word one cell further")
    print("    right than rule A; the item list is therefore proved at the reader's output: item, packing, company)")

    # ------------------------------------------------------------------------------------------------------------------ 3
    print("-- 3  landing: every sample of A.2 through the router (read_preamble -> identify -> verify) with the NEW signatures")
    A2 = [("20261004-093801", "PURCHASE_BILLWISE", "DEFAULT"), ("20261004-094002", "PURCHASE_ITEMWISE", "DEFAULT"),
          ("20261004-183328", "PURCHASE_ITEMWISE", "DEFAULT"), ("20261001-090549", "PURCHASE_SUPPLIERWISE", "DEFAULT"),
          ("20261004-183119", "PURCHASE_BILLITEMWISE", "DEFAULT"), ("20261004-141519", "SALT_WISE_ITEM_LIST", "DEFAULT"),
          ("20261004-143140", "CATEGORY_WISE_ITEM_LIST", "DEFAULT"), ("20261004-155650", "ITEM_MASTER", "DEFAULT"),
          ("20261004-182159", "SALE_BILLWISE", "SUMMARY1"), ("20261004-182424", "SALE_BILLWISE", "SUMMARY1"),
          ("20261004-183024", "SALE_RETURN", "SUMMARY"), ("20261004-183541", "SALE_RETURN", "DEFAULT"),
          ("20261004-182137", "STOCK_VALUATION", "BATCHWISE"), ("EXPIRY", "STOCK_EXPIRY", "DEFAULT"),
          ("20261004-183952", "STOCK_ITEM_LEDGER", "TEXT")]
    sig_new = R.load_signatures(os.path.join(a.kit, "signatures.json"))
    sig_old = R.load_signatures(a.old_signatures)

    def land(p, sigs):
        sh = R.open_sheet(p)
        t, h, hr, c0 = R.read_preamble(sh)
        sig, status, why = R.identify(t, h, sigs)
        d = list(R.dates_from(t, sh, hr, c0))
        if sig and sig.get("dating") == "file_mtime" and not d[0]:      # as marg_router.process does
            d = [dt.date.fromtimestamp(os.path.getmtime(p)).isoformat()] * 2 + [None, None]
        if status != "IDENTIFIED":
            return ("UNKNOWN" if status == "UNKNOWN" else "REFUSED", "", "", why)
        v, reason = R.verify(p, sh, sig, t, h, hr, *d)
        return (v, sig["type"], sig.get("variant", ""), reason)
    ok_new, olds, kinds_seen = 0, {}, {}
    for stamp, typ, var in A2:
        src = a.expiry_sample if stamp == "EXPIRY" else sample(ref, stamp)
        if not src or not os.path.exists(src):
            check("sample %s is on this PC" % stamp, False)
            continue
        raw = open(src, "rb").read()
        try:
            x, info = NEW.convert(raw)
        except Exception as ex:                                         # noqa: BLE001
            check("%s converts" % stamp[-6:], False, "%s at %s" % (ex.__class__.__name__, re.sub(r":.*$", "", str(ex))[:40]))
            continue
        p = os.path.join(W, "out", "land_%s.XLS" % stamp[-6:])
        with open(p, "wb") as fh:
            fh.write(x)
        vn = land(p, sig_new)
        vo = land(p, sig_old)
        olds[(typ, var)] = vo[0]
        kinds_seen[info["kind"]] = kinds_seen.get(info["kind"], 0) + 1
        ok_new += check("%s  %-9s -> NEW: %s %s/%s   (OLD signatures: %s%s)" % (stamp[-6:], info["kind"], vn[0], vn[1], vn[2], vo[0],
                                                                               (" " + vo[1] + "/" + vo[2]) if vo[1] else ""),
                        vn[:3] == ("VERIFIED", typ, var), mask(vn[3])[:120] or None)
    check("all fifteen samples of A.2 land VERIFIED and typed with the NEW signatures", ok_new == len(A2), ok_new)
    check("negative control, the server's OLD signatures (64943ac6): category UNKNOWN, valuation REFUSED, register REFUSED (its title is "
          "known there, its two-line heads are not -- the prototype's cut lost the title and so read UNKNOWN)",
          olds.get(("CATEGORY_WISE_ITEM_LIST", "DEFAULT")) == "UNKNOWN" and olds.get(("STOCK_VALUATION", "BATCHWISE")) == "REFUSED"
          and olds.get(("STOCK_ITEM_LEDGER", "TEXT")) == "REFUSED",
          {k[0]: v for k, v in olds.items() if v != "VERIFIED"})
    check("the register is a PHI type by its signature (STOCK_ITEM_LEDGER): the server deletes it at the door (walked there, section 4)",
          any(s["type"] == "STOCK_ITEM_LEDGER" and s.get("variant") == "TEXT" for s in sig_new))
    for stamp, _t, _v in A2:
        src = a.expiry_sample if stamp == "EXPIRY" else sample(ref, stamp)
        raw = open(src, "rb").read()
        try:
            OLD.convert(raw)
            took = True
        except Exception:                                               # noqa: BLE001
            took = False
        if took:
            check("negative control: marg_txt ed17bb76 takes none of them (%s)" % stamp[-6:], False)
            break
    else:
        check("negative control: marg_txt ed17bb76 (the medical PC today) takes none of the fifteen", True)
    check("both signatures.json will be the same bytes: the kit's file is what manojz's own copy becomes (7f72c572 + the edits)",
          md5f(os.path.join(a.kit, "signatures.json")) == md5f(os.path.join(a.built_manojz, "signatures.json")),
          md5f(os.path.join(a.kit, "signatures.json")))

    # ------------------------------------------------------------------------------------------------------------------ 4a
    print("-- 4a the empty day, on the real zero-bill text of 04-Oct 09:43:21 (it carries no bill, so no patient)")
    ep = sample(ref, "20261004-094321")
    E = open(ep, "rb").read()
    made = NEW.EMPTY_DAY_SAMPLE.replace(b"02-01-2030", b"04-10-2026")
    check("the real text is, byte for byte, the made-up sample of the selftest with its date (so the server's section 4 walks the same shape)",
          E.rstrip() == made.rstrip(), (len(E), len(made)))
    x, info = NEW.convert(E, exported_at=dt.datetime(2026, 10, 5, 9, 0, 0))
    p = os.path.join(W, "out", "empty.XLS")
    with open(p, "wb") as fh:
        fh.write(x)
    rows = norm(xrows(p))
    check("exported the NEXT day -> a no-sale day: title, heads, 'Total No. of | Bills: 0 | DAY TOTAL :' and six zeros; info empty, as_on 04-10-2026",
          info.get("empty") is True and info.get("as_on") == "04-10-2026" and len(rows) == 3
          and rows[2] == ["Total No. of", "Bills: 0", "DAY TOTAL :", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], rows[2][:3])
    for when, label in ((dt.datetime(2026, 10, 4, 9, 43, 21), "exported on its own day (as it was)"), ("20261004-094321", "re-offered from refused by its stamp")):
        try:
            NEW.convert(E, exported_at=when)
            check("%s -> refused in the staff's words" % label, False)
        except NEW.TodayNotOver as ex:
            check("%s -> refused in the staff's words" % label, str(ex) == NEW.TODAY_WORDS and "kal ki tareekh" in str(ex))
    rep = MR.read_report(p)
    check("the kit's marg_report (the four non-finance copies are these bytes) reads it ok / empty, one day, from the title",
          rep["ok"] and rep.get("empty") is True and [d["date"] for d in rep["days"]] == ["2026-10-04"] and rep["days"][0]["bills"] == []
          and rep["footer_bills"] == 0, (rep["ok"], rep.get("empty"), rep["errors"][:1]))
    vn, vo = land(p, sig_new), land(p, sig_old)
    check("the EMPTY sheet through the router: NEW signatures VERIFIED SALE_BILLWISE/DETAIL; OLD signatures REFUSED (TRUNCATED: GRAND TOTAL)",
          vn[:3] == ("VERIFIED", "SALE_BILLWISE", "DETAIL") and vo[0] == "REFUSED" and "GRAND TOTAL" in vo[3], (vn[0], vo[0]))
    try:
        OLD.to_rows(E)
        check("negative control: marg_txt ed17bb76 refuses the text ('no GRAND TOTAL line')", False)
    except OLD.Refused as ex:
        check("negative control: marg_txt ed17bb76 refuses the text ('no GRAND TOTAL line')", "no GRAND TOTAL line" in str(ex))
    MO = load("marg_report_old", os.path.join(a.pull, "marg_report.py"))
    MO._open_sheet = R.open_sheet
    ro = MO.read_report(p)
    check("negative control: manojz's OLD marg_report (28b47d44) says TRUNCATED of the same sheet",
          not ro["ok"] and any("TRUNCATED" in e for e in ro["errors"]) and "empty" not in ro)

    # ------------------------------------------------------------------------------------------------------------------ 5
    print("-- 5  the marker: every SALE_BILLWISE sheet in MargArchive carries 'Total No. of' within its last 40 rows (B.3)")
    sales = sorted(glob.glob(os.path.join(a.archive, "SALE_BILLWISE", "*", "*.XLS")) + glob.glob(os.path.join(a.archive, "SALE_BILLWISE", "*", "*.xls"))
                   + glob.glob(os.path.join(a.archive, "SALE_BILLWISE", "*", "*.xlsx")), key=lambda q: q.lower())
    seen_p, uniq = set(), []
    for q in sales:
        if q.lower() not in seen_p:
            seen_p.add(q.lower())
            uniq.append(q)
    have, lack, variants = 0, [], {}
    for q in uniq:
        sh = R.open_sheet(q)
        t, h, hr, c0 = R.read_preamble(sh)
        sig, status, why = R.identify(t, h, sig_new)
        variants[(sig or {}).get("variant", status)] = variants.get((sig or {}).get("variant", status), 0) + 1
        if R.ends_with(sh, "Total No. of"):
            have += 1
        else:
            lack.append(os.path.basename(q)[:40])
    check("%d sale sheets read (56 when the brief was written): every one carries 'Total No. of' in its last 40 rows -- one that does not = STOP"
          % len(uniq), len(uniq) >= 56 and have == len(uniq), (have, len(uniq), lack[:3], variants))
    v_all = 0
    for q in uniq:
        v_all += land(q, sig_new)[0] == "VERIFIED"
    v_old = sum(1 for q in uniq if land(q, sig_old)[0] == "VERIFIED")
    check("with the NEW marker and the kit's reader every one of them still verifies exactly as with the OLD ones (%d of %d, was %d)"
          % (v_all, len(uniq), v_old), v_all == v_old, (v_all, v_old))
    full = xrows(uniq[-1])
    cutat = max(i for i, r in enumerate(full) if any(isinstance(c, str) and "Total No. of" in c for c in r))
    pc = os.path.join(W, "out", "cut_before_footer.XLS")
    xls_write(NEW, [[(float(c) if isinstance(c, (int, float)) else c) for c in r] for r in full[:cutat - 1]], pc)
    vc = land(pc, sig_new)
    check("negative control: a sale sheet cut before its footer is REFUSED by the router under the new marker (TRUNCATED)",
          vc[0] == "REFUSED" and "Total No. of" in vc[3], vc[0])

    # ------------------------------------------------------------------------------------------------------------------ 6
    print("-- 6  the watcher, in a scratch folder with a made-up marg_push.py (no key, no address: nothing can be sent)")
    res = {}
    for side in ("new", "old"):
        d = os.path.join(W, "watch_" + side)
        os.makedirs(os.path.join(d, "marg", "17476"))
        shutil.copy(os.path.join(W, side, "marg_watch.py"), d)
        shutil.copy(os.path.join(W, "new", "marg_txt.py"), d)          # the reader is S480 on both sides: the WATCHER is what is compared
        with open(os.path.join(d, "marg_push.py"), "w") as fh:
            fh.write("# W480: a made-up pusher -- no key, no address\ndef main(argv=None):\n    return 0\n")
        with open(os.path.join(d, "MARG_TXT_LIVE.txt"), "w") as fh:
            fh.write("LIVE\n")
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe-watch", d], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=600)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        res[side] = json.loads(js[-1][len(TAG):]) if js else None
        if not js:
            print("   the %s watcher probe did not finish:" % side)
            for l in p.stdout.splitlines()[-12:]:
                print("     " + mask(l)[:200])
    n_, o_ = res["new"], res["old"]
    if check("both watcher probes ran to the end", n_ is not None and o_ is not None):
        check("a made-up salt list cut short, saved as user_1.txt, is KEPT and logged by S480 (kind SALT, a reason, a note waiting)",
              n_["user_kept"] == 1 and n_["user_logged"] and n_["user_verdict"].startswith("NOT TAKEN") and n_["note_kind"] == "SALT", n_["user_verdict"][:80])
        check("negative control: the watcher of today (297cc3d9) drops it -- 'not a Marg report', nothing kept, no line in the log",
              o_["user_kept"] == 0 and not o_["user_logged"] and o_["user_verdict"] == "not a Marg report", o_["user_verdict"])
        check("its report.txt twin with the same bytes is not kept twice (S480: one kept copy; before: none at all)",
              n_["twin_kept"] == 1 and o_["twin_kept"] == 0, (n_["twin_kept"], o_["twin_kept"]))
        check("the complete made-up salt list under user_2.txt is TAKEN by S480 as the reader's own .XLS", n_["full_taken"] and n_["full_same_bytes"])
        check("every kind word reaches note_of: %s" % ", ".join(sorted(n_["kinds"])),
              sorted(n_["kinds"]) == sorted(["ORDER", "STOCK", "SALE", "PURCHASE", "SALT", "CATEGORY", "ITEMS", "SALE_SHORT", "RETURN", "VALUATION",
                                             "EXPIRY", "LEDGER"]), n_["kinds"])
        check("negative control: before, every one of the nine new kinds had no word (the note said nothing of what it was)",
              sorted(o_["kinds"]) == ["", "ORDER", "SALE", "STOCK"], o_["kinds"])
        check("the census lists the kept text with its title (before: not listed)", n_["census_lists"] and not o_["census_lists"])
        check("a note never carries a line of the file", n_["note_clean"])

    # ------------------------------------------------------------------------------------------------------------------ 7
    print("-- 7  the salts reader on the archive's list of 04-Oct 17:55 (235e9643)")
    sl = [q for q in glob.glob(os.path.join(a.archive, "SALT_WISE_ITEM_LIST", "*", "*235e9643*")) if q.lower().endswith(".xls")]
    if check("the list 235e9643 is in MargArchive", bool(sl) and md5f(sl[0]).startswith("235e9643")):
        out = {}
        for side, path in (("new", a.salts_new), ("old", a.salts_old)):
            d = os.path.join(W, "salts_" + side)
            os.makedirs(d)
            shutil.copy(path, os.path.join(d, "salts_refresh.py"))
            S = load("salts_refresh_" + side, os.path.join(d, "salts_refresh.py"))
            items, _as_on = S.read_marg_salt_list(sl[0], ingest="")
            by = {}
            for it in items:
                by.setdefault(it["salt"], []).append(it["item"])
            firm = str(xrows(sl[0])[0][0]).upper()
            out[side] = dict(n=len(items), firm=len(by.get(firm, [])), advert=sum(1 for s in by if re.search(r"MARG ERP|QRCODE", s)),
                             salt={i["item"]: i["salt"] for i in items})
        want = {"CALFLIP CQ": "CALCIUM + CISSUS", "CROCAL EXTRA TAB": "CALCIUM + CISSUS", "NURVION LC TAB": "LEVOCARNITINE",
                "JARDIANCE 10": "EMPAGLOFLIZON 10"}
        got = {k: out["new"]["salt"].get(k) for k in want}
        check("NEW: 0 items under the firm's name, 380 items kept", out["new"]["firm"] == 0 and out["new"]["n"] == 380, (out["new"]["firm"], out["new"]["n"]))
        check("NEW: the four the brief names land on their salts (%s)" % ", ".join("%s -> %s" % kv for kv in sorted(got.items())), got == want)
        check("negative control, OLD (40cb2615): 12 items filed under the firm's name", out["old"]["firm"] == 12 and out["old"]["n"] == 380,
              (out["old"]["firm"], out["old"]["n"]))
        moved = sum(1 for k, v in out["new"]["salt"].items() if out["old"]["salt"].get(k) != v)
        check("only those 12 items change salt between OLD and NEW; nothing else in the list moves", moved == 12, moved)
    shutil.rmtree(os.path.join(W, "out"), ignore_errors=True)           # the converted samples (patient names in two of them) do not stay
    return finish("manojz")


def probe_watch(d):
    """One watcher (the file in D) on a made-up salt list -- collected notes only, nothing sent."""
    sys.path.insert(0, d)
    os.chdir(d)
    import marg_watch as MW                                             # noqa: E402
    import marg_txt as MT                                               # noqa: E402
    MW.NOTE_SINK = []
    MW.TXT_LIVE_FORCE = True
    log = []
    spool = os.path.join(d, "spool")
    cap = MW.prime_captured(spool)
    M = MT._s480_samples()
    SL = M["SALT_WISE_ITEM_LIST"]
    cut = SL[:SL.rindex(b"***")]
    refd = os.path.join(d, "_captured_txt", "refused")
    kept = lambda b: len([f for f in (os.listdir(refd) if os.path.isdir(refd) else []) if md5b(b) in f and f.endswith(".txt") and not f.endswith(".why.txt")])
    u1 = os.path.join(d, "marg", "17476", "user_1.txt")
    open(u1, "wb").write(cut)
    MW.capture(u1, spool, cap, log.append)
    out = dict(user_kept=kept(cut), user_logged=any("user_1.txt" in m for m in log), user_verdict=str(MW.TXT_VERDICT.get(u1, (0, ""))[1]),
               note_kind=(MW.NOTE_SINK[-1]["kind"] if MW.NOTE_SINK else None))
    tw = os.path.join(d, "marg", "17476", "report.txt")
    open(tw, "wb").write(cut)
    MW.capture(tw, spool, cap, log.append)
    out["twin_kept"] = kept(cut)
    cen = MW.text_census([os.path.join(d, "marg")])
    out["census_lists"] = any("user_1.txt" in l and "SALT WISE ITEM LIST" in l for l in cen)
    u2 = os.path.join(d, "marg", "17476", "user_2.txt")
    open(u2, "wb").write(SL)
    out["full_taken"] = MW.capture(u2, spool, cap, log.append) is True
    out["full_same_bytes"] = os.path.isdir(spool) and any(md5f(os.path.join(spool, f)) == md5b(MT.convert(SL)[0]) for f in os.listdir(spool))
    kinds = set()
    for k in M:
        kinds.add(MW.note_of("x.txt", "0" * 32, M[k][:-60], "cut")["kind"])
    for raw in (MT.SELFTEST_SAMPLE, MT.STOCK_SAMPLE, MT.ORDER_SAMPLE):
        kinds.add(MW.note_of("x.txt", "0" * 32, raw[:-60], "cut")["kind"])
    out["kinds"] = sorted(kinds)
    lines = [l.strip() for l in cut.decode("latin-1").splitlines()          # the title and the end mark are the reason's own fixed words
             if len(l.strip()) >= 12 and "SALT WISE ITEM LIST" not in l and "End of Report" not in l]
    out["note_clean"] = not [l for l in lines for n in MW.NOTE_SINK if any(l in str(v) for v in n.values())]
    print(TAG + json.dumps(out))


# ============================================================================================================================ server
def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def at_rest(root, md5):
    """Every file under ROOT whose bytes are these (the sidecar .txt of a quarantined file is not the file)."""
    hits = []
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                if md5f(p) == md5:
                    hits.append(os.path.relpath(p, root))
            except OSError:
                pass
    return hits


def probe_door():
    """Section 4 for ONE side (NEW = the box + S480, OLD = the box as it is): read_report x3, the door, sales_after / compute."""
    ING, FIN, WORK, DB, IN = (os.environ[k] for k in ("INGDIR", "FINDIR", "WORKDIR", "FINANCE_DB", "INDIR"))
    sys.path.insert(0, ING)
    out = {}
    empty, short, ledger, stock = (open(os.path.join(IN, n), "rb").read() for n in ("empty.XLS", "short.XLS", "ledger.XLS", "stock.XLS"))
    import xlrd                                                         # noqa: E402,F401  (the vendored reader, as the live door has it)
    rr = {}
    for label, path in (("ingest", os.path.join(ING, "marg_report.py")), ("lib", os.path.join(ING, "lib", "marg_report.py")),
                        ("finance", os.path.join(FIN, "marg_report.py"))):
        M = load("mr_" + label, path)
        try:
            rep = M.read_report(os.path.join(IN, "empty.XLS"))
            rr[label] = dict(ok=rep["ok"], empty=rep.get("empty"), days=[d["date"] for d in rep["days"]], bills=sum(len(d["bills"]) for d in rep["days"]),
                             truncated=any("TRUNCATED" in e for e in rep["errors"]), totals=M.day_totals(rep) if rep["ok"] else None)
        except Exception as ex:                                         # noqa: BLE001
            rr[label] = dict(ok=False, error=str(ex)[:120])
    out["read_report"] = rr
    import marg_take as MT                                              # noqa: E402
    MI = MT.MI
    assert MI.HERE == ING and MT.__file__.startswith(ING), (MI.HERE, MT.__file__)

    _RealLock = MT._Lock

    class _WalkLock(_RealLock):                                         # the walk's own lock: never the collector's /tmp/marg_ingest.lock
        def __init__(self, path=None, wait=None):
            _RealLock.__init__(self, os.path.join(WORK, "w480_take.lock"), wait)
    MT._Lock = _WalkLock
    arch = os.path.join(ING, "archive")
    os.makedirs(MI.WORK, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    takes = {}
    for key, raw, name in (("empty", empty, "MEDICAL__20300103-090000__W480_report_TXT__%s.XLS" % md5b(empty)[:8]),
                           ("short", short, "MEDICAL__20300103-090100__W480_user_TXT__%s.XLS" % md5b(short)[:8]),
                           ("ledger", ledger, "MEDICAL__20300103-090200__W480_report_TXT__%s.XLS" % md5b(ledger)[:8]),
                           ("empty_again", empty, "W480_again.XLS")):
        r = MT.take(raw, name=name, source="test", db=DB, archive=arch)
        m5 = md5b(raw)
        row = con.execute("SELECT type, variant, verdict, reason, lines, kept, date_from, date_to, source FROM mi_file WHERE md5=?", (m5,)).fetchone()
        takes[key] = dict(status=r["status"], type=r["type"], variant=r["variant"], verdict=r["verdict"], lines=r["lines"], kept=r["kept"],
                          reason=r["reason"][:120], date_from=r["date_from"], date_to=r["date_to"], row=dict(row) if row else None,
                          sale_lines=con.execute("SELECT COUNT(*) FROM mi_sale_line WHERE md5=?", (m5,)).fetchone()[0],
                          at_rest=at_rest(ING, m5))
    out["take"] = takes
    con.close()
    # the PC's side of B.5: an archive where sale sheets ARE kept (manojz's MargArchive), built by the router itself
    pca = os.path.join(WORK, "pc_archive")
    os.makedirs(pca, exist_ok=True)
    R = MI._readers()
    sigs = R.load_signatures(os.path.join(ING, "signatures.json"))
    cfg = {"archive": pca, "outbox": os.path.join(WORK, "pc_outbox"), "dry": False, "index": os.path.join(pca, "index.csv")}
    seen = {}
    filed = {}
    for n, raw in (("W480__20300101-090000__stock_TXT.XLS", stock), ("W480__20300103-090000__report_TXT.XLS", empty)):
        p = os.path.join(WORK, n)
        with open(p, "wb") as fh:
            fh.write(raw)
        res = R.process(p, sigs, cfg, seen, lambda m: None) or {}
        filed[n[6:14] + n[21:27]] = "%s %s/%s" % (res.get("verdict"), res.get("type"), res.get("variant"))
    out["pc_filed"] = filed
    sys.path.insert(0, os.path.join(ING, "lib"))
    import push_expected as PE                                          # noqa: E402
    assert PE.__file__.startswith(ING), PE.__file__
    lines, days, skipped = PE.sales_after(pca, dt.date(2026, 9, 24))
    out["sales_after"] = dict(lines=len(lines), days=[d.isoformat() for d in days], skipped=len(skipped))
    try:
        rep = PE.compute(pca, base_as_on="24-09-2026")
        out["compute"] = dict(as_on=rep["as_on"].isoformat() if rep.get("as_on") else None, error=(rep.get("error") or "")[:100],
                              items=len(rep.get("items") or []), sale_days=[d.isoformat() for d in rep.get("sale_days") or []])
    except Exception as ex:                                             # noqa: BLE001
        out["compute"] = dict(as_on=None, error="%s: %s" % (ex.__class__.__name__, str(ex)[:100]))
    print(TAG + json.dumps(out, default=str))


def probe_eye():
    """Section 8 for ONE side: the four homes and the reports tile as the copies are; then the walk's own SUMMARY1 row on a far day."""
    FIN, POR = os.environ["FINDIR"], os.environ["PORDIR"]
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import reports_tile as RT                                           # noqa: E402
    assert RT.__file__.startswith(FIN), RT.__file__
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W480J"])["pw"]
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % os.environ["FINANCE_DB"], uri=True)
    eye = {}
    for who in ("shavez", "darpan", "amir", "manoj"):
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        tok = m.group(1) if m else ""
        r = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
        home = r.get_data(as_text=True)
        seen = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', home)]
        ck = "clinic_sso=" + tok

        def page(path):
            body, code = "", 0
            for _hop in range(4):
                rr2 = fc.get(path, base_url=BASE, headers={"Cookie": ck})
                code = rr2.status_code
                if code in (301, 302, 303) and rr2.headers.get("Location", "").replace(BASE, "").startswith("/finance/"):
                    path = rr2.headers["Location"].replace(BASE, "")
                    continue
                body = rr2.get_data(as_text=True)
                break
            return code, body
        pages = {"home": hashlib.md5(steady(home.replace(tok, "TOKEN")).encode()).hexdigest()}
        rows, doors = [], set()
        mine = {who, (dm.get("shared") or {}).get(who)}
        for du in dm.get("duties") or []:
            if du.get("person") not in mine:
                continue
            row = {"id": du.get("id"), "tile": du.get("tile"), "tile_seen": (du.get("tile") in seen) if du.get("tile") else None}
            sql = str(du.get("due_sql") or "").strip().rstrip(";")
            n = None
            if sql:
                try:
                    rr = ro.execute(sql).fetchone()
                    n = int((rr[0] if rr else 0) or 0)
                except Exception as e:                                  # noqa: BLE001
                    n = "ERR " + str(e)[:80]
            row["due_n"] = n
            door, mark = du.get("door"), du.get("door_marker")
            if door and str(door).startswith("/finance/"):
                doors.add(str(door))
                if mark and isinstance(n, int) and n > 0:
                    row["door_seen"] = mark in page(str(door))[1]
            rows.append(row)
        doors.add("/finance/reports/aaj")
        for d in sorted(doors):
            code, body = page(d)
            pages[d] = "%s %s" % (code, hashlib.md5(steady(body.replace(tok, "TOKEN")).encode()).hexdigest())
        eye[who] = dict(status=r.status_code, n_tiles=len(seen), duties=rows, pages=pages)
    ro.close()
    out = {"eye": eye}
    # ---- the walk's own rows, on a far day (found by key, never by counting)
    cx = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    cx.row_factory = sqlite3.Row

    def row(md5, variant, at):
        cx.execute("INSERT OR REPLACE INTO mi_file (md5, drive_id, drive_name, drive_folder, drive_mtime, size, stamp, type, variant, date_from, date_to, "
                   "verdict, reason, server_name, kept, lines, pc_type, pc_verdict, agree, received_at, source) VALUES "
                   "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (md5, "", "W480_%s.XLS" % variant, "test", "", 1, "20310306-090000", "SALE_BILLWISE", variant, FAR_DAY, FAR_DAY, "VERIFIED", "", "", 0, 0,
                    "", "", "", at, "test"))
        cx.commit()

    def sale():
        s = RT._sale_row(cx, FAR_DAY, FAR_TODAY)
        return dict(state=s.get("state"), reason_hi=s.get("reason_hi") or "", reason=(s.get("reason") or "")[:60])
    out["far_before"] = sale()
    row("w480" + "5" * 28, "SUMMARY1", FAR_TODAY + "T09:05:00+05:30")
    out["far_short"] = sale()
    row("w480" + "d" * 28, "DETAIL", FAR_TODAY + "T09:20:00+05:30")
    out["far_detail"] = sale()
    cx.execute("DELETE FROM mi_file WHERE md5 LIKE 'w480%'")
    cx.commit()
    cx.close()
    # ---- the salts page as the owner reads it: as the copy is, then with the newest salt list read by THIS side's reader (scratch copy only)
    import salts_refresh as SR                                          # noqa: E402
    import purchase_app as pa                                           # noqa: E402
    assert SR.__file__.startswith(FIN) and pa.__file__.startswith(FIN), (SR.__file__, pa.__file__)

    def confirms():
        _code, body = page("/finance/purchase/page/salts")              # `page` still carries the owner's cookie (the last login above)
        m = re.search(r"Marg confirms (\d+)", re.sub(r"<[^>]+>", "", body))
        return int(m.group(1)) if m else None
    sal = dict(before=confirms())
    try:
        newest = SR.find_newest(os.environ.get("LIVE_ARCHIVE", "/root/marg_ingest/archive"))      # read only
        body = SR.build_payload(newest, os.environ["INGDIR"])
        c2 = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
        c2.row_factory = sqlite3.Row
        pa._store_marg_salts(c2, body)
        c2.close()
        sal.update(n=len(body["marg_items"]), firm=sum(1 for i in body["marg_items"] if i["salt"].startswith("SANJEEVNI")),
                   advert=sum(1 for i in body["marg_items"] if re.search(r"MARG ERP|QRCODE", i["salt"])), md5=body["marg_md5"][:8], after=confirms())
    except Exception as e:                                              # noqa: BLE001
        sal["error"] = "%s: %s" % (e.__class__.__name__, str(e)[:120])
    out["salts"] = sal
    print(TAG + json.dumps(out, default=str))


def server(a):
    W = os.path.abspath(a.work)
    assert W.startswith("/tmp/") and a.por.startswith("/tmp/"), "refusing a non-scratch path: %s %s" % (W, a.por)
    os.makedirs(W, exist_ok=True)
    kp = os.path.join(W, "kitpy")
    os.makedirs(kp, exist_ok=True)
    shutil.copy(os.path.join(a.kit, "marg_txt.py"), kp)
    NEW = load("marg_txt_new", os.path.join(kp, "marg_txt.py"))
    oldp = os.path.join(a.kits, "S454_BILL_REGISTER", "P1_ORDER_SHEET_RECEPTION", "medical", "marg_txt.py")
    OLD = None
    if os.path.exists(oldp) and md5f(oldp) == OLD_TXT:
        os.makedirs(os.path.join(W, "oldpy"), exist_ok=True)
        shutil.copy(oldp, os.path.join(W, "oldpy", "marg_txt.py"))
        OLD = load("marg_txt_old", os.path.join(W, "oldpy", "marg_txt.py"))
    # ---- the made-up texts (the selftest's own; AS ON 02-01-2030), converted by the kit's reader
    IN = os.path.join(W, "in")
    os.makedirs(IN, exist_ok=True)
    M = NEW._s480_samples()
    E = NEW.EMPTY_DAY_SAMPLE
    print("-- 4  the empty day (a made-up zero-bill text AS ON 02-01-2030 -- the real 09:43:21 text is the same bytes but for its date: section 4a)")
    x, info = NEW.convert(E, exported_at=dt.datetime(2030, 1, 3, 9, 0, 0))
    open(os.path.join(IN, "empty.XLS"), "wb").write(x)
    check("marg_txt S480, exported the NEXT day -> the EMPTY sheet (3 rows; info empty, as_on 02-01-2030)",
          info.get("empty") is True and info.get("as_on") == "02-01-2030" and info["rows"] == 3)
    try:
        NEW.convert(E, exported_at=dt.datetime(2030, 1, 2, 9, 43, 21))
        check("the same text exported on ITS OWN day -> refused with the staff's words", False)
    except NEW.TodayNotOver as ex:
        check("the same text exported on ITS OWN day -> refused with the staff's words: %s" % str(ex).replace("—", "--"), str(ex) == NEW.TODAY_WORDS)
    if OLD is not None:
        try:
            OLD.to_rows(E)
            check("negative control: marg_txt ed17bb76 refuses it ('no GRAND TOTAL line')", False)
        except OLD.Refused as ex:
            check("negative control: marg_txt ed17bb76 refuses it ('no GRAND TOTAL line')", "no GRAND TOTAL line" in str(ex))
    else:
        print("   (marg_txt ed17bb76 is not reachable here -- its negative control is the manojz walk's section 4a)")
    for key, name in (("SALE_BILLWISE_SUMMARY1", "short.XLS"), ("STOCK_ITEM_LEDGER_TEXT", "ledger.XLS")):
        open(os.path.join(IN, name), "wb").write(NEW.convert(M[key])[0])
    # a made-up whole-shop closing stock of 24-09-2026 for B.5's baseline: 240 items (a baseline under 200 rows is refused as a subset, F-235)
    big = ["", " " * 31 + "TEST SHOP", " " * 24 + "TEST STREET", "", " " * 19 + "WHOLE STORES CLOSING STOCK AS ON 24-09-2026", "-" * 80,
           "S.No.  Description" + " " * 45 + "Total Stock  Unit", "-" * 80]
    big += [NEW._stock_line(i, ("W480 ITEM %03d" % i).ljust(30) + "1*10", "1:0", "STRI").rstrip("\r\n") for i in range(1, 241)]
    big += ["-" * 80, "TOTAL" + "2400".rjust(70), "-" * 80, NEW.END, ""]
    open(os.path.join(IN, "stock.XLS"), "wb").write(NEW.convert("\r\n".join(big).encode("latin-1"))[0])

    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W480 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                 # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    try:
        clinic_users.add_role(store, "staff")
    except ValueError:
        pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])

    def run(mode, side, ing, fin):
        wd = os.path.join(W, "%s_%s" % (mode, side))
        os.makedirs(wd, exist_ok=True)
        dbp, adbp, spp = [os.path.join(wd, "w480_%s.db" % x) for x in ("fin", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, SIDE=side, INGDIR=ing, FINDIR=fin, PORDIR=a.por, WORKDIR=wd, INDIR=IN, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp,
                   FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por, CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store,
                   TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map,
                   W480J=json.dumps(dict(pw=pw)), MI_ARCHIVE=os.path.join(ing, "archive"))
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "FINANCE_MARG_TOKEN"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe-" + mode], env=env, cwd=fin if mode == "eye" else wd,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s %s probe did not finish (exit %s); its last lines:" % (side, mode, p.returncode))
            for l in p.stdout.splitlines()[-30:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    DN, DO = run("door", "new", a.ingest_new, a.fin_new), run("door", "old", a.ingest_old, a.fin_old)
    if not check("both door probes ran to the end (NEW = the box + S480, OLD = the box as it is)", DN is not None and DO is not None):
        return finish("server")
    day = "2030-01-02"
    rn, ro = DN["read_report"], DO["read_report"]
    check("every patched read_report -- /root/marg_ingest, its lib copy, and /root/finance (the one the door runs) -- reads the EMPTY sheet ok / "
          "empty, one day, from the title (%s), no bills; day_totals gives that day with zeros" % day,
          all(rn[k].get("ok") and rn[k].get("empty") is True and rn[k].get("days") == [day] and rn[k].get("bills") == 0
              and (rn[k].get("totals") or [{}])[0].get("business_date") == day and (rn[k].get("totals") or [{}])[0].get("net_p") == 0
              for k in ("ingest", "lib", "finance")), {k: (v.get("ok"), v.get("empty"), v.get("days")) for k, v in rn.items()})
    check("negative control: each OLD read_report says TRUNCATED of the same sheet (not ok, no empty)",
          all((not ro[k].get("ok")) and ro[k].get("truncated") and not ro[k].get("empty") for k in ("ingest", "lib", "finance")),
          {k: (v.get("ok"), v.get("truncated")) for k, v in ro.items()})
    tn, to = DN["take"], DO["take"]
    e = tn["empty"]
    check("the door (marg_take.take) on the scratch copy: the EMPTY sale is TAKEN, VERIFIED SALE_BILLWISE/DETAIL, lines 0, date_from = date_to = %s"
          % day, e["status"] == "TAKEN" and (e["verdict"], e["type"], e["variant"], e["lines"]) == ("VERIFIED", "SALE_BILLWISE", "DETAIL", 0)
          and e["date_from"] == e["date_to"] == day, (e["status"], e["verdict"], e["type"], e["variant"], e["date_from"]))
    check("its mi_file row: reason 'EMPTY (em dash) no sale on %s' exactly as the brief words it, dates the title's, kept 0; mi_sale_line "
          "untouched for its md5; the file itself deleted as every sale file is (S186) -- nowhere at rest" % day,
          bool(e["row"]) and e["row"]["reason"] == "EMPTY — no sale on %s" % day and e["row"]["date_from"] == e["row"]["date_to"] == day
          and e["row"]["kept"] == 0 and e["row"]["lines"] == 0 and e["sale_lines"] == 0 and e["at_rest"] == [],
          (e["row"] and e["row"]["reason"].replace("—", "--"), e["sale_lines"], e["at_rest"]))
    check("the same bytes again: ALREADY, nothing counted twice", tn["empty_again"]["status"] == "ALREADY" and tn["empty_again"]["verdict"] == "VERIFIED")
    eo = to["empty"]
    check("negative control, the door as it is: the same sheet is REFUSED (TRUNCATED) -- no EMPTY row",
          eo["verdict"] != "VERIFIED" and not (eo["row"] and str(eo["row"]["reason"]).startswith("EMPTY")), (eo["status"], eo["verdict"], eo["reason"][:70]))
    s = tn["short"]
    check("the short sale statement (SUMMARY1) LANDS through the new door: TAKEN, VERIFIED SALE_BILLWISE/SUMMARY1, no line read, deleted (S186)",
          s["status"] == "TAKEN" and (s["verdict"], s["type"], s["variant"], s["lines"], s["kept"]) == ("VERIFIED", "SALE_BILLWISE", "SUMMARY1", 0, 0)
          and s["at_rest"] == [] and s["sale_lines"] == 0, (s["status"], s["verdict"], s["variant"], s["at_rest"]))
    so = to["short"]
    check("negative control, the door as it is: the same sheet is NOT taken ('%s') and no mi_file row is written" % so["reason"][:50],
          so["status"] != "TAKEN" and so["row"] is None, (so["status"], so["at_rest"]))
    if so["at_rest"]:
        print("   NOTED (outside this kit's edit, mended by it at THIS door): the door as it is leaves that refused short statement AT REST in the")
        print("   archive (%s) -- a sale file. With S480's marg_take it is deleted." % so["at_rest"][0][:60])
    lg = tn["ledger"]
    check("the converted stock register: VERIFIED STOCK_ITEM_LEDGER/TEXT, a PHI type -- deleted at the door, kept nowhere (kept 0, not at rest)",
          (lg["status"], lg["verdict"], lg["type"], lg["variant"], lg["kept"]) == ("TAKEN", "VERIFIED", "STOCK_ITEM_LEDGER", "TEXT", 0) and lg["at_rest"] == [],
          (lg["verdict"], lg["type"], lg["variant"], lg["kept"], lg["at_rest"]))
    lo = to["ledger"]
    check("negative control, the OLD signatures: the register is not known (%s %s)" % (lo["verdict"], lo["type"]), lo["verdict"] != "VERIFIED")
    check("B.5 on a scratch archive where sale sheets are kept (as manojz's): the router files the made-up closing stock and the EMPTY day; "
          "the kit's push_expected.sales_after lists %s with no lines; compute gives as_on = %s" % (day, day),
          DN["sales_after"]["days"] == [day] and DN["sales_after"]["lines"] == 0 and DN["compute"]["as_on"] == day and not DN["compute"]["error"],
          (DN["pc_filed"], DN["sales_after"], DN["compute"]))
    check("negative control, OLD files: the EMPTY sheet is refused at the router, sales_after lists no day, compute has nothing to compute",
          DO["sales_after"]["days"] == [] and not DO["compute"]["as_on"], (DO["pc_filed"], DO["sales_after"], DO["compute"]["error"][:60]))

    print("-- 8  the staff-eye walk (D648): shavez, darpan, amir and the owner, on the scratch copy, a walk-only login store")
    EN, EO = run("eye", "new", a.ingest_new, a.fin_new), run("eye", "old", a.ingest_old, a.fin_old)
    if not check("both staff-eye probes ran to the end", EN is not None and EO is not None):
        return finish("server")
    for who in ("shavez", "darpan", "amir", "manoj"):
        n_, o_ = EN["eye"][who], EO["eye"][who]
        check("%s signs in; the home is byte-equal before and after (%d tiles); every door page too (%d pages)"
              % (who, n_["n_tiles"], len(n_["pages"])), n_["status"] == 200 and n_["n_tiles"] > 0 and n_["pages"] == o_["pages"],
              [k for k in n_["pages"] if n_["pages"][k] != o_["pages"].get(k)])
        due = [d for d in n_["duties"] if isinstance(d.get("due_n"), int) and d["due_n"] > 0]
        hid = [d["id"] for d in due if d.get("tile_seen") is False or d.get("door_seen") is False]
        check("   %s: %d duties in the map, %d due now -- each due one is visible (its tile on the home, its marker on its door); "
              "the same on both sides" % (who, len(n_["duties"]), len(due)), not hid and n_["duties"] == o_["duties"], hid)
    check("the walk's far day holds nothing before its rows go in: the sale row is 'due' on both sides",
          EN["far_before"]["state"] == "due" and EO["far_before"]["state"] == "due", (EN["far_before"], EO["far_before"]))
    check("a VERIFIED SUMMARY1 sale sheet does NOT tick the tile's sale row: the staff see the tile's own words -- '%s'" % EN["far_short"]["reason_hi"],
          EN["far_short"]["state"] == "refused" and EN["far_short"]["reason_hi"].startswith("Item detail nahi hai"), EN["far_short"])
    check("negative control, reports_tile as it is (9d2244a6): the same row DOES count as the day's sale report (state %s)" % EO["far_short"]["state"],
          EO["far_short"]["state"] in ("ok", "arrived", "bad"), EO["far_short"])
    check("the DETAIL report for the same day, arriving after it, is what the row then shows -- on both sides",
          EN["far_detail"]["state"] in ("ok", "arrived", "bad") and EN["far_detail"]["state"] == EO["far_detail"]["state"], (EN["far_detail"], EO["far_detail"]))
    sn, so_ = EN["salts"], EO["salts"]
    check("the salts reader on the server's own newest list (%s): NEW files %s of its %s items under the firm's name; OLD (40cb2615) files %s"
          % (sn.get("md5"), sn.get("firm"), sn.get("n"), so_.get("firm")),
          "error" not in sn and "error" not in so_ and sn["firm"] == 0 and sn["advert"] == 0 and sn["n"] == so_["n"] and so_["firm"] > 0, (sn, so_))
    check("the owner's salts page on the scratch copy: 'Marg confirms %s' as it is; with the corrected list %s (the brief expects 78 -> 82); "
          "with the list as the OLD reader reads it, %s" % (sn.get("before"), sn.get("after"), so_.get("after")),
          sn.get("before") is not None and sn.get("before") == so_.get("before") == so_.get("after") and (sn.get("after") or 0) > sn["before"],
          (sn.get("before"), sn.get("after"), so_.get("after")))
    return finish("server")


def finish(where):
    if FAILS:
        print("WALK_S480 %s RED -- %d of %d checks failed:" % (where, len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:200])
        return 1
    print("WALK_S480 %s GREEN -- %d checks" % (where, N[0]))
    return 0


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe-watch":
        return probe_watch(sys.argv[2])
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe-door":
        return probe_door()
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe-eye":
        return probe_eye()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="where", required=True)
    m = sub.add_parser("manojz")
    for k in ("--kit", "--work", "--mirror", "--archive", "--pull", "--kits", "--expiry-sample", "--old-signatures", "--built-manojz", "--salts-new",
              "--salts-old"):
        m.add_argument(k, required=True)
    s = sub.add_parser("server")
    for k in ("--kit", "--work", "--kits", "--ingest-new", "--ingest-old", "--fin-new", "--fin-old", "--por", "--db", "--adb", "--spine", "--duty-map"):
        s.add_argument(k, required=True)
    a = ap.parse_args()
    return manojz(a) if a.where == "manojz" else server(a)


if __name__ == "__main__":
    sys.exit(main() or 0)
