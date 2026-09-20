#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
near_expiry.py -- S274 / kit S343_NEAR_EXPIRY (Sanjeevni).  D567 item 6: near-expiry from the archived
expiry exports (D409: a three-month window on each batch's OWN expiry date).

    /root/wa/venv/bin/python3 -B /root/finance/spine/near_expiry.py            (tonight's file)
    ... near_expiry.py --archive /root/marg_ingest/archive --spine /root/finance/spine/spine.db --out /root/finance/spine/expiry --date 2026-09-20
    ... near_expiry.py --read FILE.XLS                                          (read one export and print its reading)

WHAT IT DOES.  Every night it takes the NEWEST Marg expiry export the door has kept (archive/STOCK_EXPIRY/
<yyyy-mm>/*.xls -- the owner's / Shavez's 'Stock expiry' export, monthly on the 1st by the S270 plan), reads
it with a reader that can fail, and writes beside the spine:
    expiry/near_expiry_<date>.json  and  expiry/near_expiry_latest.txt
-- every batch in the export with its expiry month, how many months are left as of tonight, EXPIRED / NEAR
(within 3 months, D409) / LATER, its stock as Marg printed it, and the spine's own stock for the item today
(so a batch whose item has no stock left is said so).  A second section lists, from the spine's sale lines
(sp_sale_line carries batch and expiry per sold line), the batches SEEN SOLD whose expiry falls within the
window and whose item still has stock per the spine -- a cross-check on the export, never a substitute.
The file also says how old the newest export is; over 35 days it says OVERDUE (the monthly cadence).

THE READER (the S268 rule: every row classified positively, a witness that re-adds, made to fail on purpose):
  rows: shop header (rows 1-6) · TITLE 'EXP. BEFORE ...' · HEADER 'S.No. Description | Batch | Expiry |
  Stock Unit' · ITEM '<serial> <name> <packing>' + batch + 'M/YYYY' + '<strips>:<loose> <unit>' or
  '<n> <unit>' · blank spacer rows · TOTAL · Marg's advertisement footer.
  witness: the serial numbers run 1..N unbroken, and TOTAL = the sum of every row's units, where a row's
  units = strips*pack + loose (a negative '-3:8' is -(3*pack+8) -- measured 20-Sep on the archive: 218 and
  832 re-add exactly on the two exports checked, and only with that sign rule).

Reads: the kept exports (read-only), spine.db (read-only URI).  Writes: expiry/ beside the spine.
Nothing on any screen; nothing in finance.db; no existing file changed.  OFF: the spine's own switches.
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INGEST = os.environ.get("MARG_INGEST", "/root/marg_ingest")
ARCHIVE_DEFAULT = os.path.join(INGEST, "archive")
SPINE_DEFAULT = os.path.join(HERE, "spine.db")
OUT_DEFAULT = os.path.join(HERE, "expiry")
OFF_FLAGS = (os.path.join(HERE, "OFF"), "/root/finance/_off/ALL_OFF")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
KIT = "S343_NEAR_EXPIRY"
WINDOW_MONTHS = 3            # D409
EXPORT_DUE_DAYS = 35         # monthly export (S270 plan), a month plus slack

ITEM_RE = re.compile(r'^\s*(\d+)\s+(.*?)\s{2,}(\S+)\s*$')          # serial, name, packing (name and packing set apart by spaces)
ITEM_RE_1 = re.compile(r'^\s*(\d+)\s+(.+?)\s*$')                   # serial + name when no packing column shows
STOCK_RE = re.compile(r'^\s*(-?)(\d+)(?::(\d+))?\s*([A-Za-z]*)\s*$')
EXPIRY_RE = re.compile(r'^\s*(\d{1,2})\s*/\s*(\d{4})\s*$')
TITLE_RE = re.compile(r'EXP\.?\s*BEFORE|EXPIR', re.I)


def K(n):
    return re.sub(r'\s+', ' ', (n or "").strip())[:20].strip()


def pack_of(packing):
    m = re.match(r'^\s*(\d+)\s*\*\s*(\d+)', packing or "")
    return int(m.group(2)) if m and int(m.group(2)) > 0 else 1


def open_rows(path):
    """Every row as a list of cell strings, through the router's own opener (xlrd for .xls, stdlib .xlsx)."""
    if INGEST not in sys.path:
        sys.path.insert(0, INGEST)
    try:
        import marg_router as R                                  # noqa: PLC0415
        sh = R.open_sheet(path)
        return [[str(sh.cell_value(r, c)) for c in range(sh.ncols)] for r in range(sh.nrows)]
    except Exception:                                            # noqa: BLE001
        import xlrd                                              # noqa: PLC0415
        sh = xlrd.open_workbook(path).sheet_by_index(0)
        return [[str(sh.cell_value(r, c)) for c in range(sh.ncols)] for r in range(sh.nrows)]


def read_expiry(path):
    """-> dict(ok, checks, failed, items=[{serial,name,packing,pack,batch,expiry,strips,loose,units,unit}], printed_total, as_on)"""
    rows = open_rows(path)
    checks, anomalies, items = [], [], []
    header_row = None
    title = ""
    total = None
    for i, r in enumerate(rows):
        cells = [c for c in r]
        filled = [c.strip() for c in cells if c.strip()]
        if not filled:
            continue
        c0 = cells[0].strip() if cells else ""
        if header_row is None:
            if len(filled) >= 3 and filled[0].upper().startswith("S.NO") and any("EXPIRY" in f.upper() for f in filled):
                header_row = i
                continue
            if TITLE_RE.search(c0):
                title = c0
            continue                                             # the shop header and the title: furniture
        if c0.upper().startswith("TOTAL"):
            t = next((c for c in filled[1:] if c), "")
            try:
                total = float(t)
            except ValueError:
                anomalies.append((i + 1, "TOTAL", "unreadable total %r" % t[:20]))
            continue
        if re.search(r'\bMARG\b', " ".join(filled), re.I) and len(filled) == 1:
            continue                                             # Marg's advertisement footer
        m = ITEM_RE.match(c0) or ITEM_RE_1.match(c0)
        if not m or len(cells) < 4:
            anomalies.append((i + 1, "UNCLASSIFIED", c0[:40]))
            continue
        serial = int(m.group(1))
        name = m.group(2).strip()
        packing = m.group(3).strip() if m.lastindex and m.lastindex >= 3 else ""
        batch = cells[1].strip()
        if batch.endswith(".0"):
            batch = batch[:-2]
        em = EXPIRY_RE.match(cells[2])
        sm = STOCK_RE.match(cells[3])
        if not em or not sm:
            anomalies.append((i + 1, "UNCLASSIFIED", "expiry %r stock %r" % (cells[2][:12], cells[3][:12])))
            continue
        pack = pack_of(packing)
        sign = -1 if sm.group(1) else 1
        strips = int(sm.group(2))
        loose = int(sm.group(3) or 0)
        units = sign * (strips * pack + loose) if sm.group(3) is not None else sign * strips
        items.append(dict(serial=serial, name=name, packing=packing, pack=pack, batch=batch,
                          expiry="%04d-%02d" % (int(em.group(2)), int(em.group(1))), strips=sign * strips, loose=loose,
                          units=units, unit=sm.group(4).upper()))
    checks.append(("header row found", header_row is not None, ""))
    checks.append(("title names expiry", bool(TITLE_RE.search(title)), title[:40]))
    serials = [it["serial"] for it in items]
    checks.append(("serial run 1..N unbroken", serials == list(range(1, len(items) + 1)), "%s" % serials[:12]))
    checks.append(("every row classified", not anomalies, "; ".join("%s at row %d" % (a[1], a[0]) for a in anomalies[:4])))
    checks.append(("TOTAL row present", total is not None, ""))
    if total is not None:
        s = sum(it["units"] for it in items)
        checks.append(("TOTAL = sum of every row's units", abs(total - s) < 0.5, "printed %.1f, rows %.1f" % (total, s)))
    m = re.search(r'__(\d{4}-\d{2}-\d{2})__', os.path.basename(path))
    as_on = m.group(1) if m else dt.datetime.fromtimestamp(os.path.getmtime(path), IST).date().isoformat()
    return dict(ok=all(c[1] for c in checks), checks=checks, failed=[c[0] for c in checks if not c[1]],
                items=items, printed_total=total, as_on=as_on, path=path,
                md5=hashlib.md5(open(path, "rb").read()).hexdigest(), n=len(items))


def months_left(expiry_ym, today):
    y, m = int(expiry_ym[:4]), int(expiry_ym[5:7])
    return (y - today.year) * 12 + (m - today.month)


def newest_export(archive):
    files = [p for p in glob.glob(os.path.join(archive, "STOCK_EXPIRY", "*", "*")) if p.lower().endswith((".xls", ".xlsx"))]
    if not files:
        return None
    def stamp(p):
        m = re.search(r'__(\d{8}-\d{6})__', os.path.basename(p))
        return m.group(1) if m else "0"
    return max(files, key=stamp)


def spine_stock(spine, today):
    """{k20: units today} and the batches seen in sale lines with their expiry, from the spine (read-only)."""
    if not os.path.exists(spine):
        return {}, [], ""
    con = sqlite3.connect("file:%s?mode=ro" % spine, uri=True)
    con.row_factory = sqlite3.Row
    try:
        built = {r["key"]: r["value"] for r in con.execute("SELECT key, value FROM sp_meta")}.get("built", "")
        stock = {r["k20"]: r["u"] for r in con.execute("SELECT k20, COALESCE(SUM(units),0) AS u FROM sp_move WHERE date<=? GROUP BY k20", (today.isoformat(),))}
        seen = [dict(r) for r in con.execute(
            "SELECT k20, MAX(name20) AS name, batch, expiry, MAX(date) AS last_sold, COUNT(*) AS lines FROM sp_sale_line "
            "WHERE batch<>'' AND expiry<>'' GROUP BY k20, batch, expiry")]
    finally:
        con.close()
    return stock, seen, built


def norm_expiry(s):
    """'10/26' · '10/2026' · '2026-10' -> '2026-10' or ''."""
    s = (s or "").strip()
    m = re.match(r'^(\d{1,2})/(\d{2,4})$', s)
    if m:
        y = int(m.group(2))
        y = y + 2000 if y < 100 else y
        return "%04d-%02d" % (y, int(m.group(1)))
    m = re.match(r'^(\d{4})-(\d{2})', s)
    return m.group(0) if m else ""


def run(archive, spine, out_dir, today, log=print):
    for f in OFF_FLAGS:
        if os.path.exists(f):
            log("near_expiry: switched off (%s)" % f)
            return 0
    os.makedirs(out_dir, exist_ok=True)
    p = newest_export(archive)
    stock, seen, built = spine_stock(spine, today)
    rec = dict(kit=KIT, date=today.isoformat(), prepared_at=dt.datetime.now(IST).isoformat(timespec="seconds"), spine_built=built,
               export=None, rows=[], from_sales=[], window_months=WINDOW_MONTHS)
    lines = ["NEAR EXPIRY -- %s -- prepared %s (%s) · window %d months on each batch's own expiry (D409)"
             % (today.isoformat(), dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M"), KIT, WINDOW_MONTHS),
             "Read by the machine from Marg's own expiry export; nothing here changes stock. Every removal is a Marg voucher (R6)."]
    if p is None:
        lines.append("NO EXPIRY EXPORT KEPT on this box yet (archive/STOCK_EXPIRY empty) -- export 'Stock expiry' from Marg; the door keeps it.")
        rec["export"] = dict(missing=True)
    else:
        R = read_expiry(p)
        age = (today - dt.date.fromisoformat(R["as_on"])).days
        rec["export"] = dict(file=os.path.basename(p), md5=R["md5"], as_on=R["as_on"], age_days=age, ok=R["ok"], failed=R["failed"],
                             n=R["n"], printed_total=R["printed_total"], overdue=age > EXPORT_DUE_DAYS)
        lines.append("export: %s · as on %s · %d days old%s · reader %s" % (
            os.path.basename(p)[:70], R["as_on"], age, " · OVERDUE (monthly export due)" if age > EXPORT_DUE_DAYS else "",
            ("OK (%d rows, TOTAL %s re-adds)" % (R["n"], R["printed_total"])) if R["ok"] else ("FAILED: " + "; ".join(R["failed"]))))
        if R["ok"]:
            for it in R["items"]:
                ml = months_left(it["expiry"], today)
                status = "EXPIRED" if ml < 0 else ("NEAR" if ml <= WINDOW_MONTHS else "LATER")
                k = K(it["name"])
                sp = stock.get(k)
                row = dict(it, months_left=ml, status=status, key=k, spine_stock_today=sp)
                rec["rows"].append(row)
            rec["rows"].sort(key=lambda r: (r["expiry"], r["name"]))
            lines.append("")
            lines.append("-- from the export (%d batches): %d EXPIRED · %d NEAR (within %d months) · %d later" % (
                len(rec["rows"]), sum(1 for r in rec["rows"] if r["status"] == "EXPIRED"), sum(1 for r in rec["rows"] if r["status"] == "NEAR"),
                WINDOW_MONTHS, sum(1 for r in rec["rows"] if r["status"] == "LATER")))
            for r in rec["rows"]:
                lines.append("  %-8s %-30s batch %-12s exp %s (%+d m) · Marg %s%s%s · spine today %s" % (
                    r["status"], r["name"][:30], r["batch"][:12], r["expiry"], r["months_left"],
                    ("%d:%d" % (r["strips"], r["loose"]) if r["unit"] in ("STR",) else "%d" % r["strips"]), " " + r["unit"], " = %d u" % r["units"],
                    ("%.0f u" % r["spine_stock_today"]) if r["spine_stock_today"] is not None else "(item not in the spine)"))
    # from the spine's own sale lines: batches seen, expiring in the window, item still in stock
    near_sold = []
    for s in seen:
        e = norm_expiry(s["expiry"])
        if not e:
            continue
        ml = months_left(e, today)
        if ml <= WINDOW_MONTHS and (stock.get(s["k20"]) or 0) > 0:
            near_sold.append(dict(key=s["k20"], name=s["name"], batch=s["batch"], expiry=e, months_left=ml, last_sold=s["last_sold"],
                                  lines=s["lines"], spine_stock_today=stock.get(s["k20"]),
                                  in_export=any(r["key"] == s["k20"] and r["batch"] == s["batch"] for r in rec["rows"])))
    near_sold.sort(key=lambda r: (r["expiry"], r["name"]))
    rec["from_sales"] = near_sold
    lines.append("")
    lines.append("-- cross-check from the spine's sale lines: %d batch(es) seen sold, expiring within %d months, item still in stock; %d of them NOT in the export"
                 % (len(near_sold), WINDOW_MONTHS, sum(1 for r in near_sold if not r["in_export"])))
    for r in near_sold[:60]:
        lines.append("  %-30s batch %-12s exp %s (%+d m) · last sold %s · spine %.0f u%s" % (
            (r["name"] or "")[:30], r["batch"][:12], r["expiry"], r["months_left"], r["last_sold"], r["spine_stock_today"] or 0,
            "" if r["in_export"] else "  NOT IN EXPORT"))
    lines.append("")
    lines.append("A sold batch may be finished -- the spine holds stock per item, not per batch; the export is Marg's per-batch word.")
    txt = "\n".join(lines) + "\n"
    jp = os.path.join(out_dir, "near_expiry_%s.json" % today.isoformat())
    with open(jp + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    os.replace(jp + ".tmp", jp)
    lp = os.path.join(out_dir, "near_expiry_latest.txt")
    with open(lp + ".tmp", "w", encoding="utf-8") as fh:
        fh.write(txt)
    os.replace(lp + ".tmp", lp)
    for l in lines[:4]:
        log(l)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=ARCHIVE_DEFAULT)
    ap.add_argument("--spine", default=SPINE_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--date", default="")
    ap.add_argument("--read", default="", help="read one export and print its reading")
    a = ap.parse_args(argv)
    if a.read:
        R = read_expiry(a.read)
        for c in R["checks"]:
            print("  %-4s %s%s" % ("ok" if c[1] else "FAIL", c[0], ("  -- " + c[2]) if c[2] and not c[1] else ""))
        print("%s: %d rows, TOTAL %s, as on %s" % ("OK" if R["ok"] else "FAILED", R["n"], R["printed_total"], R["as_on"]))
        return 0 if R["ok"] else 1
    today = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(IST).date()
    return run(a.archive, a.spine, a.out, today)


if __name__ == "__main__":
    sys.exit(main())
