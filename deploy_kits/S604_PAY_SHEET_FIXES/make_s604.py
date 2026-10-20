#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s604.py -- kit S604_PAY_SHEET_FIXES (20-Oct-2026). The anchored patcher: builds the two TO files from the LIVE bytes.

    python3 -B make_s604.py --finance /root/finance --out <dir>                    -> <dir>/purchase_app.py   (60f2d846 -> TO)
    python  -B make_s604.py --marg-txt <Drive ToMedical\\_kit\\marg_txt.py> --out <dir>  -> <dir>/marg_txt.py  (a59a222f -> TO)

Each edit is (name, anchor, replacement); every anchor must occur EXACTLY once in the file as it stands, else nothing is written.
The FROM md5 of each input is checked first. The output is written with the input's own line endings (LF on the server, as read).
F-956 (the reader's returns inside; the server counting returns as returns), F-955 (the clipped-name twin), F-954 (the two boxes),
the owner's ask of 20-Oct 08:25 (the month-end reports card) and the one lock gate."""
import argparse
import hashlib
import os
import sys

FROM = {"purchase_app.py": "60f2d846155659c4eddc33e4a0d42b39", "marg_txt.py": "a59a222faf32a72ccc19c8635955cf8d",
        "KIT_MANIFEST.txt": "0bf248e43381bd27f6d011648b8405ee"}

# =============================================================================================== marg_txt.py (the medical PC's reader)
MT = []

MT.append(("reader: VERSION", 'VERSION = "S546"\n', 'VERSION = "S604"\n'))

MT.append(("reader: the S604 paragraph of the docstring",
'''  Excel export carries it; two or more spaces inside it still refuse. Every text the reader took before converts to the same bytes.

    python marg_txt.py report.txt out.XLS      convert one file''',
'''  Excel export carries it; two or more spaces inside it still refuse. Every text the reader took before converts to the same bytes.

S604 (F-956, 20-Oct-2026, the owner's "do all what is required for the NEFT payment sheet so that it accepts reports"): RETURNS
  INSIDE A SUPPLIER'S BLOCK. Marg's SUPPLIER/ITEM WISE PURCHASE STATEMENT prints a supplier's purchase returns as ordinary lines and
  subtracts them in its own TOTAL, so the lines exceed the TOTAL by exactly twice the returns (L.K. DRUG HOUSE, 20-Oct 08:06, line
  177). Such a block is taken only when a set of at most 6 of its lines -- in a block of at most 40 lines, every line positive in
  both money columns -- adds to exactly half the excess in both columns at once (to the paisa), found by a bounded search over
  paise states (capped at 200,000); a larger block, a non-positive line, the cap, or no such set refuses with the words of before.
  The GRAND TOTAL is then held against the sum of the printed supplier TOTALs (within a rupee a line, as before). The sheet written
  is unchanged -- no line is marked: the reader cannot tell which lines are the returns (each has an identical purchase twin); the
  server counts them from Marg's own minus sign on the bill. BILL/ITEM WISE is not changed.

    python marg_txt.py report.txt out.XLS      convert one file'''))

_OLD_CHK = '''def _chk_purchase_items(grouped):
    """SUPPLIER/ITEM WISE (grouped: a TOTAL under every supplier, then the GRAND TOTAL) and BILL/ITEM WISE (one TOTAL at the end)."""
    def chk(rows, at, lines):
        sa = sv = ga = gv = 0.0
        sn = gn = 0
        end = None
        for r, ln in zip(rows[_body(rows):], at[_body(rows):]):
            if _is_head(r):
                continue
            if _words(r).startswith("GRAND TOTAL") if grouped else r[0] == "TOTAL":
                end = (ln, _f(r[9]), _f(r[11]))
                continue
            if grouped and _has(r, "TOTAL"):
                if not sn:
                    raise Refused("line %d: a supplier TOTAL with no line above it" % ln)
                if not (_near(_f(r[9]), sa, sn) and _near(_f(r[11]), sv, sn)):
                    raise Refused("line %d: a supplier's TOTAL (%.2f) is not the sum of its lines (%.2f)" % (ln, _f(r[9]), sa))
                ga, gv, gn = ga + sa, gv + sv, gn + sn
                sa = sv = 0.0
                sn = 0
                continue
            if isinstance(r[11], float) and r[9] != "":
                if end is not None:
                    raise Refused("line %d: an item line after the last TOTAL" % ln)
                try:
                    amt = _f(str(r[9]).split()[0]) if isinstance(r[9], str) else r[9]
                except ValueError:
                    raise Refused("line %d: an item line whose amount cannot be read" % ln)
                sa, sv, sn = sa + amt, sv + r[11], sn + 1
        if grouped and sn:
            raise Refused("the last supplier's lines have no TOTAL")
        if not grouped:
            ga, gv, gn = sa, sv, sn
        if end is None:
            raise Refused("no %s line" % ("GRAND TOTAL" if grouped else "TOTAL"))
        if not gn:
            raise EmptyReport("no item lines")
        if not (_near(end[1], ga, gn) and _near(end[2], gv, gn)):
            raise Refused("line %d: the total printed (%.2f) is not the sum of the lines (%.2f)" % (end[0], end[1], ga))
    return chk
'''

_NEW_CHK = '''S604_MAX_LINES, S604_MAX_SET, S604_CAP = 40, 6, 200000
RETURNS_INSIDE = []          # S604: the supplier TOTAL lines the last purchase check took as "returns inside" (for the proof; the sheet is unchanged)


def _returns_inside(block, ea, ev):
    """S604 (F-956): block = [(line, amount, net)] of one supplier; ea, ev = by how many paise its lines exceed the printed TOTAL
    (amount, net), both > 0. The line numbers of a set of at most S604_MAX_SET lines adding to exactly half the excess in BOTH
    columns (twice the set = the excess, to the paisa), or None: a block of more than S604_MAX_LINES lines, a line not positive in
    both columns, the search reaching S604_CAP states, or no such set. A dynamic pass over (amount, net) paise states, each state
    keeping its shortest witness -- bounded, it cannot hang the watcher."""
    if len(block) > S604_MAX_LINES:
        return None
    pts = []
    for ln, a, v in block:
        pa, pv = int(round(a * 100)), int(round(v * 100))
        if pa <= 0 or pv <= 0:
            return None
        pts.append((ln, pa, pv))
    states = {(0, 0): ()}
    for i, (ln, pa, pv) in enumerate(pts):
        new = {}
        for (sa, sv), w in states.items():
            if len(w) >= S604_MAX_SET:
                continue
            na, nv = sa + pa, sv + pv
            if 2 * na > ea + 1 or 2 * nv > ev + 1:
                continue
            if abs(2 * na - ea) <= 1 and abs(2 * nv - ev) <= 1:
                return [pts[j][0] for j in w + (i,)]
            have = new.get((na, nv), states.get((na, nv)))
            if have is None or len(have) > len(w) + 1:
                new[(na, nv)] = w + (i,)
        states.update(new)
        if len(states) > S604_CAP:
            return None
    return None


def _chk_purchase_items(grouped):
    """SUPPLIER/ITEM WISE (grouped: a TOTAL under every supplier, then the GRAND TOTAL) and BILL/ITEM WISE (one TOTAL at the end).
    S604: grouped, a supplier block whose lines exceed its TOTAL by exactly twice a set of its lines is "returns inside"
    (_returns_inside), and the GRAND TOTAL is held against the sum of the printed TOTALs. BILL/ITEM WISE as before."""
    def chk(rows, at, lines):
        del RETURNS_INSIDE[:]
        sa = sv = ga = gv = 0.0
        pa = pv = 0.0
        sn = gn = 0
        blk = []
        end = None
        for r, ln in zip(rows[_body(rows):], at[_body(rows):]):
            if _is_head(r):
                continue
            if _words(r).startswith("GRAND TOTAL") if grouped else r[0] == "TOTAL":
                end = (ln, _f(r[9]), _f(r[11]))
                continue
            if grouped and _has(r, "TOTAL"):
                if not sn:
                    raise Refused("line %d: a supplier TOTAL with no line above it" % ln)
                if not (_near(_f(r[9]), sa, sn) and _near(_f(r[11]), sv, sn)):
                    ea = sum(int(round(x[1] * 100)) for x in blk) - int(round(_f(r[9]) * 100))
                    ev = sum(int(round(x[2] * 100)) for x in blk) - int(round(_f(r[11]) * 100))
                    if not (ea > 0 and ev > 0 and _returns_inside(blk, ea, ev)):
                        raise Refused("line %d: a supplier's TOTAL (%.2f) is not the sum of its lines (%.2f)" % (ln, _f(r[9]), sa))
                    RETURNS_INSIDE.append(ln)
                ga, gv, gn = ga + sa, gv + sv, gn + sn
                pa, pv = pa + _f(r[9]), pv + _f(r[11])
                sa = sv = 0.0
                sn = 0
                blk = []
                continue
            if isinstance(r[11], float) and r[9] != "":
                if end is not None:
                    raise Refused("line %d: an item line after the last TOTAL" % ln)
                try:
                    amt = _f(str(r[9]).split()[0]) if isinstance(r[9], str) else r[9]
                except ValueError:
                    raise Refused("line %d: an item line whose amount cannot be read" % ln)
                sa, sv, sn = sa + amt, sv + r[11], sn + 1
                blk.append((ln, amt, r[11]))
        if grouped and sn:
            raise Refused("the last supplier's lines have no TOTAL")
        if not grouped:
            ga, gv, gn = sa, sv, sn
            pa, pv = ga, gv
        if end is None:
            raise Refused("no %s line" % ("GRAND TOTAL" if grouped else "TOTAL"))
        if not gn:
            raise EmptyReport("no item lines")
        if not (_near(end[1], pa, gn) and _near(end[2], pv, gn)):
            raise Refused("line %d: the total printed (%.2f) is not the sum of the lines (%.2f)" % (end[0], end[1], ga))
    return chk
'''
MT.append(("reader: _chk_purchase_items takes a block whose returns are inside it (bounded), GRAND against the printed TOTALs", _OLD_CHK, _NEW_CHK))

MT.append(("reader: the selftest calls the S604 checks",
'''    _selftest_s480(ck)                                                   # S480: one check per spec, the three byte-equalities, the empty day
''',
'''    _selftest_s480(ck)                                                   # S480: one check per spec, the three byte-equalities, the empty day
    _selftest_s604(ck)                                                   # S604: returns inside a supplier's block (made-up blocks)
'''))

MT.append(("reader: the S604 selftest (made-up blocks shaped as L.K. and KEDAR)",
'''def selftest(sample=None):
''',
'''def _s604_text(blocks, grand_shift=(0.0, 0.0)):
    """A made-up SUPPLIER/ITEM WISE text: blocks = [(supplier, [(amount, net)], (TOTAL amount, TOTAL net))]; the GRAND TOTAL is the
    sum of the printed TOTALs (plus grand_shift)."""
    L = [_t((7, "SUPPLIER/ITEM WISE PURCHASE STATEMENT FROM 01-01-2030 TO 31-01-2030")), _R132, _PI_HEAD, _R132]
    ga = gv = 0.0
    for k, (name, items, tot) in enumerate(blocks):
        L.append(name)
        for j, (a, v) in enumerate(items):
            L.append(_pi_item(str(100 + k * 50 + j), "TESTMED %d" % j, "TB%03d" % j, "%.2f" % a, "%.2f" % v))
        L += [_t((80, "-" * 52)), _pi_total(80, "TOTAL", "%.2f" % tot[0], "%.2f" % tot[1])]
        ga, gv = ga + tot[0], gv + tot[1]
    L += [_R132, _pi_total(0, "GRAND TOTAL", "%.2f" % (ga + grand_shift[0]), "%.2f" % (gv + grand_shift[1])), _R132, END]
    return _txt(L)


def _selftest_s604(ck):
    """S604 (F-956): a block whose lines exceed its TOTAL by twice a set of its lines is taken; nothing else that did not add up is."""
    ret = [(116.26, 116.55), (1862.12, 2489.04), (2005.18, 2737.92)]                       # the three returns, as printed lines
    lk_items = [(116.26, 116.55), (1200.00, 1260.50), (1862.12, 2489.04), (350.75, 368.30), (2005.18, 2737.92), (999.99, 1049.95)] + ret
    lk_tot = (round(sum(a for a, v in lk_items) - 2 * sum(a for a, v in ret), 2), round(sum(v for a, v in lk_items) - 2 * sum(v for a, v in ret), 2))
    kd_items = [(500.00, 525.00), (250.50, 263.10), (1000.00, 1050.00)]
    kd_tot = (round(sum(a for a, v in kd_items), 2), round(sum(v for a, v in kd_items), 2))

    def blocks(lk=lk_tot, kd=kd_tot, lki=lk_items):
        return [("TEST RETURNS AGENCY", lki, lk), ("TEST KEDAR PHARMA", kd_items, kd)]

    def takes(raw):
        try:
            spec_rows(raw)
            return True, list(RETURNS_INSIDE)
        except Refused as ex:
            return False, str(ex)[:80]

    ok_, got = takes(_s604_text(blocks()))
    ck("S604: a block whose lines exceed its TOTAL by twice three of its lines is taken, 'returns inside'", ok_ and len(got) == 1, got)
    xa, _ = convert(_s604_text(blocks()))
    ck("S604: the sheet of a returns-inside text is the same bytes every time (no line marked)", xa == convert(_s604_text(blocks()))[0])
    for d in (0.02, -0.02):
        ok_, got = takes(_s604_text(blocks(lk=(round(lk_tot[0] + d, 2), round(lk_tot[1] + d, 2)))))
        ck("S604: the returns block's TOTAL moved by %+.2f is refused (the half-excess no longer matches)" % d, not ok_, got)
    ok_, got = takes(_s604_text(blocks(kd=(round(kd_tot[0] - 100, 2), round(kd_tot[1] - 100, 2)))))
    ck("S604: another block's TOTAL moved by more than its line count in rupees (-100) is refused", not ok_, got)
    ok_, got = takes(_s604_text(blocks(kd=(round(kd_tot[0] + 0.02, 2), round(kd_tot[1] + 0.02, 2)))))
    ck("S604: another block's TOTAL moved by +0.02 is taken (a rupee a line, as before)", ok_, got)
    ok_, got = takes(_s604_text(blocks(lk=(round(lk_tot[0] + 2 * 3983.56 - 37.11, 2), round(lk_tot[1] + 2 * 5343.51 - 41.17, 2)))))
    ck("S604: an excess that no set of at most 6 lines explains is refused", not ok_, got)
    big = [(100.00 + j, 105.00 + j) for j in range(40)] + [ret[0]]
    bt = (round(sum(a for a, v in big) - 2 * ret[0][0], 2), round(sum(v for a, v in big) - 2 * ret[0][1], 2))
    t0 = __import__("time").time()
    ok_, got = takes(_s604_text([("TEST BIG AGENCY", big, bt), ("TEST KEDAR PHARMA", kd_items, kd_tot)]))
    ck("S604: a 41-line block with a returns-shaped excess is refused, and the check does not hang", not ok_ and __import__("time").time() - t0 < 10, got)
    ok_, got = takes(_s604_text(blocks(lki=lk_items[:-1] + [(-2005.18, -2737.92)])))
    ck("S604: a block holding a line that is not positive is refused", not ok_, got)
    ok_, got = takes(_s604_text(blocks(), grand_shift=(-50.0, -50.0)))
    ck("S604: a GRAND TOTAL that is not the sum of the printed TOTALs is refused", not ok_, got)


def selftest(sample=None):
'''))

# =============================================================================================== purchase_app.py (the server)
PA = []

# ---------------------------------------------------------------- 3.3 the clipped-name twin (F-955)
PA.append(("store: the lookup goes through _s604_bill_lookup",
'''        key = supplier_key(sup)
        have = con.execute("SELECT id, bill_date, date_src, supplier FROM purchase_bill "
                           "WHERE supplier_norm=? AND bill_no=?", (key, bno)).fetchall()
        target = None
''',
'''        key = supplier_key(sup)
        have = _s604_bill_lookup(con, typ, md5, key, bno, d, cash + credit)   # S604 (F-955): the exact key, a retired twin, a clipped name
        target = None
'''))

PA.append(("store: _s604_bill_lookup defined before _store_bills",
'''def _store_bills(con, typ, md5, rows):
''',
'''_S604_TWIN_RE = re.compile(r"^twin of bill (\\d+)\\b")
_S604_KEY_TABLES = ("purchase_line", "amir_bill_answer", "amir_bill_disposition", "amir_self_wait", "amir_claim")


def _s604_carries(con, key, bno):
    """S604: the first table that names the bill (supplier key, bill number), or '' -- a missing table names nothing.
    purchase_scan_alias carries no bill number: any alias on the key counts."""
    for t in _S604_KEY_TABLES:
        try:
            if con.execute("SELECT 1 FROM %s WHERE supplier_norm=? AND bill_no=? LIMIT 1" % t, (key, bno)).fetchone():
                return t
        except sqlite3.Error:
            continue
    try:
        if con.execute("SELECT 1 FROM purchase_scan_alias WHERE supplier_norm=? LIMIT 1", (key,)).fetchone():
            return "purchase_scan_alias"
    except sqlite3.Error:
        pass
    return ""


def _s604_bill_lookup(con, typ, md5, key, bno, d, amount_p):
    """S604 (F-955) -- the rows _store_bills matches an incoming bill against, as (id, bill_date, date_src, supplier).
    1. The exact key (supplier_norm, bill_no), as before -- but a row retired as 'twin of bill N' (both report columns empty) is
       read as bill N: a re-export carrying the clipped name lands on the real bill and never revives the twin.
    2. No live row has the exact key: the ONE row of the same bill number and date whose OTHER report carries the same amount,
       whose column for THIS report is empty or holds another export (a re-export), and whose key is a word-boundary prefix of
       the incoming one or the other way round -- Marg's supplier-wise report clips a 32-letter name ('BASS PHARMA DISTRIBUTORS
       PVT' | 'LTD29-09-2026'). It is joined, audited 'twin_joined'; a stored shorter key is renamed to the longer one only when
       nothing else names (short key, bill_no). The UPDATE branch of _store_bills then keeps the longer name and the bill-wise
       date, and never changes supplier_norm."""
    col = "bw_md5" if typ == "BILLWISE" else "sw_md5"
    ocol, oamt = ("sw_md5", "sw_amount_p") if typ == "BILLWISE" else ("bw_md5", "bw_amount_p")
    have = []
    for r in con.execute("SELECT id, bill_date, date_src, supplier, bw_md5, sw_md5, reason FROM purchase_bill "
                         "WHERE supplier_norm=? AND bill_no=?", (key, bno)).fetchall():
        m = _S604_TWIN_RE.match(r[6] or "") if (r[4] is None and r[5] is None) else None
        if m:
            real = con.execute("SELECT id, bill_date, date_src, supplier FROM purchase_bill WHERE id=?",
                               (int(m.group(1)),)).fetchone()
            if real is not None:
                have.append((real[0], real[1], real[2], real[3]))
                _audit(con, "push_purchases", "twin_joined", real[0],
                       dict(incoming=key, bill_no=bno, bill_date=d, md5=md5, type=typ, via="retired twin %d" % r[0]))
                continue
        have.append((r[0], r[1], r[2], r[3]))
    if have:
        return have
    cands = []
    for r in con.execute("SELECT id, bill_date, date_src, supplier, supplier_norm, %s, %s, %s FROM purchase_bill "
                         "WHERE bill_no=? AND bill_date=? AND supplier_norm<>?" % (oamt, ocol, col), (bno, d, key)).fetchall():
        other = r[4] or ""
        long_, short_ = (key, other) if len(key) > len(other) else (other, key)
        if not (short_ and long_.startswith(short_ + " ")):
            continue
        if r[5] is None or int(r[5]) != int(amount_p) or not r[6] or r[7] == md5:
            continue
        cands.append(r)
    if len(cands) != 1:
        return []
    r = cands[0]
    other, renamed, why = r[4], False, ""
    if len(key) > len(other):
        why = _s604_carries(con, other, bno)
        if not why:
            con.execute("UPDATE purchase_bill SET supplier_norm=? WHERE id=?", (key, r[0]))
            renamed = True
    _audit(con, "push_purchases", "twin_joined", r[0],
           dict(incoming=key, stored=other, bill_no=bno, bill_date=d, md5=md5, type=typ, renamed=renamed,
                kept_name=("%s names (%s, %s)" % (why, other, bno)) if why else ""))
    return [(r[0], r[1], r[2], r[3])]


def _store_bills(con, typ, md5, rows):
'''))

# ---------------------------------------------------------------- 3.2 returns counted as returns (F-956 B)
PA.append(("summary: a bill with Marg's minus sign counts its positive lines negative",
'''    agree, returns, short, no_lines, used = [], [], [], [], set()
    iw = 0
    for b in bills:
        t = _bill_lines(b, sets, stray)
        if t is None:
            no_lines.append(b)
            continue
        used.add((t["supplier_norm"], t["bill_no"]))
        iw += t["net_p"]
        d = t["net_p"] - b["marg_p"]
        x = dict(bill=b, net_p=t["net_p"], gross_p=t["gross_p"], n=t["n"], diff_p=d)
        if d > AGREE_P:
            returns.append(x)
        elif d < -AGREE_P:
            short.append(x)
        else:
            agree.append(b)
''',
'''    agree, returns, short, no_lines, used = [], [], [], [], set()
    signed = []          # S604 (F-956 B): the bills whose positive lines count NEGATIVE -- Marg's own minus sign on the bill
    iw = 0
    for b in bills:
        t = _bill_lines(b, sets, stray)
        if t is None:
            no_lines.append(b)
            continue
        used.add((t["supplier_norm"], t["bill_no"]))
        net = t["net_p"]
        sg = b["marg_p"] < 0 and net > 0              # Marg prints a return's lines as a purchase; the bill carries the minus
        if sg:
            net = -net
            signed.append(b["id"])
        iw += net
        d = net - b["marg_p"]
        x = dict(bill=b, net_p=net, gross_p=t["gross_p"], n=t["n"], diff_p=d)
        if d > AGREE_P and not sg:
            returns.append(x)
        elif d < -AGREE_P or d > AGREE_P:             # a signed bill that still differs is offered a verdict, never a "return"
            short.append(x)
        else:
            agree.append(b)
'''))

PA.append(("summary: returns `signed`",
'''                can_finalise=can, reasons=reasons, story=story, head=head)
''',
'''                can_finalise=can, reasons=reasons, story=story, head=head, signed=signed)
'''))

# ---------------------------------------------------------------- 3.4 / 3.5 the reports, the refusal, the one gate
PA.append(("reports: _month_reports, the refusal, _lock_gate, the gated story, the card -- before _months",
'''def _months(con, n=6):
''',
'''# ====================================================================== S604: the month-end reports, and the ONE lock gate
# The owner, 20-Oct-2026 08:25: "The vendor payment kit should specifically ask for the final uploads of the REQUIRED purchase
# reports as text files and should give confirmation when these files are received by it." A report's arrival is its
# purchase_export row (read here only); a refusal is its mi_file row; the lock is _lock_gate (api_finalise, the month page's button
# and note, the hub's 'ready to finalise' and the card's green line all read it). _month_summary never calls any of these
# (_verify_statement calls _month_summary: a call back would recurse -- R1-B1).
_S604_REPORTS = (
    ("SUPPLIERWISE", ("SUPPLIERWISE",), "supplier-wise statement", "SUPPLIER WISE PURCHASE STATEMENT"),
    ("BILLWISE", ("BILLWISE",), "bill-wise statement", "BILL WISE PURCHASE STATEMENT"),
    ("ITEMS", ("ITEMWISE", "BILLITEMWISE"), "item lines", "SUPPLIER/ITEM WISE PURCHASE STATEMENT"),
)
_S604_REFUSED = "the medical PC refused it: PURCHASE text"
_S604_STOP_RE = re.compile(r"PURCHASE text -- the reader refused it \\(line (\\d+)\\)$")


def _s604_last_day(month):
    """'2026-09' -> '2026-09-30' (the month's own last day; the old test was the 28th)."""
    return "%s-%02d" % (month, _days_in_month(month))


def _s604_dt(ts):
    """A stored time as a naive IST datetime: '+05:30' (mi_file) converted; naive (purchase_export, now_iso) read as IST."""
    try:
        d = dt.datetime.fromisoformat(str(ts).strip().replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if d.tzinfo is not None:
        d = d.astimezone(IST).replace(tzinfo=None)
    return d


def _s604_dmy(iso):
    return "%s-%s-%s" % (iso[8:10], iso[5:7], iso[:4])


def _s604_period(pf, pt):
    """('2026-09-01', '2026-09-30') -> '01\\u201330 Sep'; across months '01 Sep\\u201303 Oct'."""
    try:
        a, b = dt.date.fromisoformat(pf), dt.date.fromisoformat(pt)
    except (TypeError, ValueError):
        return "%s to %s" % (pf, pt)
    if (a.year, a.month) == (b.year, b.month):
        return "%02d\\u2013%02d %s" % (a.day, b.day, a.strftime("%b"))
    return "%02d %s\\u2013%02d %s" % (a.day, a.strftime("%b"), b.day, b.strftime("%b"))


def _month_reports(con, month, s=None):
    """S604 -- the three reports month M needs, one entry each, from purchase_export alone: the newest LIVE export whose period
    covers the 1st..the last day (supplier-wise, bill-wise: by export stamp, with its row count as bills; item lines: ITEMWISE or
    BILLITEMWISE, the newest arrival, and s['no_lines'] / s['gap_dates'] -- no row count). s = _month_summary(con, month) when
    given; computed only when not (never from inside _month_summary)."""
    if s is None:
        s = _month_summary(con, month)
    first, last = month + "-01", _s604_last_day(month)
    out = []
    for key, types, label, title in _S604_REPORTS:
        rows = [dict(r) for r in con.execute(
            "SELECT md5, type, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p FROM purchase_export "
            "WHERE type IN (%s) AND superseded_by IS NULL AND period_from<=? AND period_to>=? "
            "ORDER BY export_stamp DESC, received_at DESC" % ",".join("?" * len(types)), tuple(types) + (first, last))]
        e = dict(key=key, label=label, title=title, first=first, last=last, state="not yet", export=None, covering=rows)
        if rows:
            pick = rows[0] if key != "ITEMS" else max(rows, key=lambda r: (_s604_dt(r["received_at"]) or dt.datetime.min))
            e.update(state="received", export=pick)
        if key == "ITEMS":
            e.update(no_lines=len(s["no_lines"]), gap_dates=list(s["gap_dates"]))
        out.append(e)
    return out


def _s604_refusal(con, month, reps):
    """The newest purchase refusal from the medical PC (mi_file REFUSED, 'the medical PC refused it: PURCHASE text ...') that came
    after the month's last day AND after the newest arrival among the three reports' covering exports -- times compared as
    parsed datetimes (+05:30 against naive IST). One plain line, or ''. The server cannot tell which report it was (type '')."""
    try:
        rows = con.execute("SELECT received_at, reason FROM mi_file WHERE verdict='REFUSED' AND reason LIKE ?",
                           (_S604_REFUSED + "%",)).fetchall()
    except sqlite3.Error:
        return ""
    last = dt.date.fromisoformat(_s604_last_day(month))
    got = [x for x in (_s604_dt(r["received_at"]) for e in reps for r in e["covering"]) if x is not None]
    newest = max(got) if got else None
    best = None
    for r in rows:
        t = _s604_dt(r[0])
        if t is None or t.date() <= last or (newest is not None and t <= newest):
            continue
        if best is None or t > best[0]:
            best = (t, str(r[1] or ""))
    if best is None:
        return ""
    t, reason = best
    at = t.strftime("%H:%M") + ("" if t.date() == dt.datetime.now(IST).date() else " on " + t.strftime("%d-%b"))
    m = _S604_STOP_RE.search(reason)
    if m:
        return ("The medical PC refused a purchase report at %s \\u2014 it could not read it (line %s). Nothing for you to redo."
                % (at, m.group(1)))
    rest = reason[len(_S604_REFUSED):].strip().lstrip("-").strip()
    first = re.split(r" \\(|;| -- ", rest, 1)[0].strip().rstrip(".") or "no reason given"
    return "The medical PC refused a purchase report at %s: %s." % (at, first)


def _lock_gate(con, month, s):
    """S604 -- THE lock gate, (can, reasons): _month_summary's own reasons, plus one per required report not received, plus --
    only when the supplier-wise statement is received -- the cross-check's first problem when it does not agree. s is
    _month_summary(con, month), computed by the caller; nothing here calls _month_summary (R1-B1). A FINAL month is not asked."""
    reasons = list(s["reasons"])
    reps = _month_reports(con, month, s)
    for e in reps:
        if e["state"] != "received":
            reasons.append("the %s for %s %s not reached the server"
                           % (e["label"], _s604_period(e["first"], e["last"]), "have" if e["key"] == "ITEMS" else "has"))
    if reps[0]["state"] == "received":
        v = _verify_statement(con, month, s)
        if not v["ok"]:
            reasons.append("the cross-check against the supplier-wise statement does not agree: %s"
                           % (v["problems"][0] if v["problems"] else "see the check on the payment page"))
    return (not reasons), reasons


def _story_gated(s, gate):
    """The hub's / month page's story with 'ready to finalise' only when the one gate is open."""
    st = s["story"]
    tail = "; ready to finalise."
    if s["can_finalise"] and not gate[0] and st.endswith(tail):
        st = st[:-len(tail)] + "; the lock waits for the month-end reports and the cross-check."
    return st


def _s604_reports_card(con, month, s, final):
    """The card at the top of /page/pay/<M> (owner English; whoever sees the page sees it)."""
    try:
        reps = _month_reports(con, month, s)
        refused = _s604_refusal(con, month, reps)
        gate = (False, []) if final else _lock_gate(con, month, s)
    except Exception as ex:                                        # noqa: BLE001
        return ('<!--s604card--><div class="card" id="s604reports"><h2>Month-end reports</h2><div class="muted">the reports card '
                'is unavailable (%s)</div></div><!--/s604card-->' % _esc(str(ex)[:120]))
    span = "FROM %s TO %s" % (_s604_dmy(reps[0]["first"]), _s604_dmy(reps[0]["last"]))
    lines = []
    for e in reps:
        x, cls = e["export"], ""
        if e["state"] == "received":
            txt = "Received %s \\u00b7 %s" % (_hhmm_ist_full(x["received_at"]), _s604_period(x["period_from"], x["period_to"]))
            if e["key"] != "ITEMS":
                txt += " \\u00b7 %s" % _plural(int(x["n_rows"] or 0), "bill")
            if e["key"] == "SUPPLIERWISE" and x["grand_amount_p"]:
                g = int(x["grand_amount_p"])
                if abs(g - s["marg_p"]) <= AGREE_P:
                    txt += " \\u00b7 its total %s agrees with the sheet" % _r(g)
                else:
                    txt += " \\u00b7 its total %s \\u2014 the sheet adds up to %s (see the check below)" % (_r(g), _r(s["marg_p"]))
                    cls = "warn"
            if e["key"] == "ITEMS" and e["no_lines"]:
                txt += (" \\u2014 but %s still %s no item lines (%s): export %s, %s, as a TEXT file"
                        % (_plural(e["no_lines"], "bill"), "has" if e["no_lines"] == 1 else "have",
                           _dates_text(e["gap_dates"]), e["title"], span))
                cls = "warn"
        else:
            txt = "Not yet \\u2014 export from Marg as a TEXT file: %s, %s" % (e["title"], span)
            cls = "warn"
        lines.append('<div class="s604r" style="margin:6px 0"><b>%s</b> \\u2014 <span class="%s">%s</span></div>'
                     % (_esc(e["label"][:1].upper() + e["label"][1:]), cls, _esc(txt)))
    if gate[0]:
        lines.append('<div class="ok" style="margin:8px 0"><b>All three reports are in and agree \\u2014 the month can be '
                     'locked.</b></div>')
    if refused:
        lines.append('<div class="warn" style="margin:8px 0">%s</div>' % _esc(refused))
    if dt.datetime.now(IST).date() <= dt.date.fromisoformat(reps[0]["last"]):
        lines.append('<div class="muted">The month is not over yet \\u2014 export these after %s.</div>'
                     % _esc(_human(reps[0]["last"])))
    return ('<!--s604card--><div class="card" id="s604reports"><h2>Month-end reports for %s</h2>%s'
            '<div class="muted" style="margin-top:6px">Each report shows here within about a quarter of an hour of being exported. '
            'Exporting the same report again, with nothing changed in Marg, adds nothing \\u2014 the time above stays.</div>'
            '</div><!--/s604card-->' % (_esc(_month_name(month)), "".join(lines)))


def _months(con, n=6):
'''))

PA.append(("finalise: api_finalise refuses on _lock_gate",
'''    if not s["can_finalise"]:
        return jsonify(ok=False, error="cannot_finalise", month=month, reasons=s["reasons"]), 409
''',
'''    can, why = _lock_gate(con, month, s)                       # S604: the lock asks for the three reports and an agreeing cross-check
    if not can:
        return jsonify(ok=False, error="cannot_finalise", month=month, reasons=why), 409
'''))

PA.append(("hub: the story's 'ready to finalise' through the gate",
'''        s = _month_summary(con, m)
        st = s["status"]["status"].upper()
''',
'''        s = _month_summary(con, m)
        st = s["status"]["status"].upper()
        story = s["story"] if st == "FINAL" else _story_gated(s, _lock_gate(con, m, s))       # S604: the one gate
'''))

PA.append(("hub: the row shows the gated story",
'''                       "ok" if st == "FINAL" else "warn", st, _esc(s["story"])))
''',
'''                       "ok" if st == "FINAL" else "warn", st, _esc(story)))
'''))

PA.append(("pay rows: the signed bills read",
'''    ret_by = {x["bill"]["id"]: x for x in s["returns"]}
    short_by = {x["bill"]["id"]: x for x in s["short"]}
    groups, cur = [], None
''',
'''    ret_by = {x["bill"]["id"]: x for x in s["returns"]}
    short_by = {x["bill"]["id"]: x for x in s["short"]}
    signed_ids = set(s.get("signed") or [])                    # S604 (F-956 B)
    groups, cur = [], None
'''))

PA.append(("pay rows: the return's flag in plain words",
'''            flag = ("bill-wise says %s and supplier-wise says %s — the two Marg reports disagree."
                    % (_r(b["bw_p"]), _r(b["sw_p"])))
        note = "" if t else "the item lines for this bill have not arrived yet."
''',
'''            flag = ("bill-wise says %s and supplier-wise says %s — the two Marg reports disagree."
                    % (_r(b["bw_p"]), _r(b["sw_p"])))
        elif b["id"] in signed_ids:
            flag = "a purchase return — Marg prints its lines as a purchase; counted as a return."
        note = "" if t else "the item lines for this bill have not arrived yet."
'''))

PA.append(("verify: s given, the month's last day",
'''def _verify_statement(con, month):
''',
'''def _verify_statement(con, month, s=None):
'''))

PA.append(("verify: s used when given",
'''    s = _month_summary(con, month)
    bills = s["bills"]
    problems, notes = [], []
''',
'''    if s is None:                                              # S604: the gate passes its own summary (no second build, no recursion)
        s = _month_summary(con, month)
    bills = s["bills"]
    problems, notes = [], []
'''))

PA.append(("verify: the period test on the last day, not the 28th",
'''        "ORDER BY export_stamp DESC LIMIT 1", (month + "-01", month + "-28")).fetchone()
''',
'''        "ORDER BY export_stamp DESC LIMIT 1", (month + "-01", _s604_last_day(month))).fetchone()
'''))

# ---------------------------------------------------------------- 3.6 the two boxes (F-954)
PA.append(("pay line: a minus a phone types, a refusal for an unreadable figure, the note kept, the reply says what was saved",
'''    def money(key):
        v = b.get(key + "_p")
        n = _int_or_none(v)
        if n is not None:
            return n
        raw = str(b.get(key) or "").replace(",", "").replace("₹", "").strip()
        if raw == "":
            return None
        try:
            return int(round(float(raw) * 100))
        except ValueError:
            return None

    carry, paid = money("carry_fwd"), money("paid")
    note = str(b.get("note") or "").strip()[:300]
    before = con.execute("SELECT carry_fwd_p, paid_p, note FROM purchase_pay_line WHERE month=? "
                         "AND vendor_norm=?", (month, vendor)).fetchone()
    con.execute("INSERT INTO purchase_pay_line (month, vendor_norm, carry_fwd_p, paid_p, note, "
                "updated_by, updated_at) VALUES (?,?,?,?,?,?,?) ON CONFLICT(month, vendor_norm) "
                "DO UPDATE SET carry_fwd_p=excluded.carry_fwd_p, paid_p=excluded.paid_p, "
                "note=excluded.note, updated_by=excluded.updated_by, updated_at=excluded.updated_at",
                (month, vendor, carry, paid, note or None, _who(u), now_iso()))
    _audit(con, _who(u), "pay_line", "%s %s" % (month, vendor),
           {"carry_fwd_p": carry, "paid_p": paid, "note": note,
            "before": dict(before) if before else None})
    con.commit()
    return jsonify(ok=True, month=month, vendor_norm=vendor, carry_fwd_p=carry, paid_p=paid)
''',
'''    bad = []

    def money(key):
        v = b.get(key + "_p")
        n = _int_or_none(v)
        if n is not None:
            return n
        typed = str(b.get(key) if b.get(key) is not None else "").strip()
        raw = typed.replace(",", "").replace("₹", "").replace(" ", "")
        if raw.endswith("/-"):                                 # S604 (F-954): '400/-' as it is written on paper
            raw = raw[:-2]
        if raw[:1] in ("\\u2212", "\\u2013"):                    # S604: the minus a phone types (U+2212), or a dash (U+2013)
            raw = "-" + raw[1:]
        if raw == "":
            return None
        try:
            f = float(raw)
            if f != f or abs(f) == float("inf"):
                raise ValueError(raw)
            return int(round(f * 100))
        except ValueError:
            bad.append((key, typed[:40]))
            return None

    carry, paid = money("carry_fwd"), money("paid")
    if bad:                                                    # S604: refused with words, never saved blank
        what = {"carry_fwd": "Carried in", "paid": "Paid"}
        return jsonify(ok=False, error="malformed",
                       message="That figure could not be read: %s. Type a number such as 400 or -400; nothing was saved."
                       % "; ".join("%s \\u201c%s\\u201d" % (what.get(k, k), t) for k, t in bad)), 400
    before = con.execute("SELECT carry_fwd_p, paid_p, note FROM purchase_pay_line WHERE month=? "
                         "AND vendor_norm=?", (month, vendor)).fetchone()
    if "note" in b:                                            # S604: the note is written only when the request carries it
        note = str(b.get("note") or "").strip()[:300]
    else:
        note = (before["note"] if before else None) or ""
    at = now_iso()
    con.execute("INSERT INTO purchase_pay_line (month, vendor_norm, carry_fwd_p, paid_p, note, "
                "updated_by, updated_at) VALUES (?,?,?,?,?,?,?) ON CONFLICT(month, vendor_norm) "
                "DO UPDATE SET carry_fwd_p=excluded.carry_fwd_p, paid_p=excluded.paid_p, "
                "note=excluded.note, updated_by=excluded.updated_by, updated_at=excluded.updated_at",
                (month, vendor, carry, paid, note or None, _who(u), at))
    _audit(con, _who(u), "pay_line", "%s %s" % (month, vendor),
           {"carry_fwd_p": carry, "paid_p": paid, "note": note,
            "before": dict(before) if before else None})
    con.commit()
    payable = None
    try:
        payable = next((g["payable_p"] for g in _pay_rows(con, month)[1] if g["norm"] == vendor), None)
    except Exception:                                          # noqa: BLE001
        payable = None
    return jsonify(ok=True, month=month, vendor_norm=vendor, carry_fwd_p=carry, paid_p=paid, payable_p=payable,
                   payable=_r(payable) if payable is not None else "", updated_at=at, updated_by=_who(u))
'''))

PA.append(("sheet: the saved words, defined before _pay_sheet_table",
'''def _pay_sheet_table(groups, prefix, month, editable):
''',
'''def _s604_saved_words(g):
    """S604 (F-954): 'Saved 20-Oct 07:54 by manoj \\u2014 payable now \\u20b90', from the pay line's own updated_at / updated_by."""
    w = "Saved %s by %s \\u2014 payable now %s" % (_hhmm_ist_full(g["at"]), g.get("by") or "?", _r(g["payable_p"]))
    if g.get("note"):
        w += " \\u00b7 note: %s" % g["note"]
    return w


def _pay_sheet_table(groups, prefix, month, editable):
'''))

PA.append(("sheet: Carried in takes a minus on a phone (no numeric keypad)",
'''        inp = ('<input class="pin" id="cf_%s" value="%s" inputmode="numeric" '
''',
'''        inp = ('<input class="pin" id="cf_%s" value="%s" '
'''))

PA.append(("sheet: the saved line under a vendor with a pay line, only when editable",
'''                       _esc(g["norm"]), _r(g["payable_p"]), pin))
    tot_f1 = sum(g["f1_p"] for g in groups)
''',
'''                       _esc(g["norm"]), _r(g["payable_p"]), pin))
        if editable and g.get("at"):                           # S604 (F-954): what was saved, by whom (never on the printed pack)
            rows.append('<tr class="s604saved"><td colspan="7" class="muted" style="padding-top:0">%s</td></tr>'
                        % _esc(_s604_saved_words(g)))
    tot_f1 = sum(g["f1_p"] for g in groups)
'''))

PA.append(("pay page: the month-end reports card at the top",
'''               _s446_earlier_card(con, month, prefix) + _pay_months_nav_s264(con, month, prefix),   # S446: an earlier month's baaki
''',
'''               _s604_reports_card(con, month, s, final) +                                         # S604: the month-end reports
               _s446_earlier_card(con, month, prefix) + _pay_months_nav_s264(con, month, prefix),   # S446: an earlier month's baaki
'''))

PA.append(("pay page js: 'Saved -- payable now' beside the box, then the reload",
'''  if(!j.ok){alert(j.message||'could not save that');return;}
  location.reload();
 }).catch(function(){el.disabled=false;alert('could not save that just now');});}
''',
'''  if(!j.ok){alert(j.message||'could not save that');return;}
  var sv=document.createElement('span');sv.className='ok';sv.textContent=' Saved \\\\u2014 payable now '+(j.payable||'');
  el.parentNode.appendChild(sv);
  setTimeout(function(){location.reload();},1200);
 }).catch(function(){el.disabled=false;alert('could not save that just now');});}
'''))

# ---------------------------------------------------------------- the month page: the signed chip and the gate
PA.append(("month page: the gate read once, before the page is built",
'''    s = _month_summary(con, month)
    final = s["status"]["status"] == "final"
    doctor, viewer = _is_doctor(u), _is_viewer_only(u)
''',
'''    s = _month_summary(con, month)
    final = s["status"]["status"] == "final"
    doctor, viewer = _is_doctor(u), _is_viewer_only(u)
    gate = (False, []) if final else _lock_gate(con, month, s)          # S604: the one gate
'''))

PA.append(("month page: the signed bills read",
'''    short_by = {x["bill"]["id"]: x for x in s["short"]}
    for name, bills in groups:
''',
'''    short_by = {x["bill"]["id"]: x for x in s["short"]}
    signed_ids = set(s.get("signed") or [])                    # S604 (F-956 B)
    for name, bills in groups:
'''))

PA.append(("month page: a signed bill that agrees says so",
'''            elif not n:
                vh = '<span class="warn">no item lines yet</span>'
            else:
                vh = '<span class="ok">agrees</span>'
''',
'''            elif not n:
                vh = '<span class="warn">no item lines yet</span>'
            elif b["id"] in signed_ids:
                vh = ('<span class="ok">agrees</span> <span class="muted">a purchase return \\u2014 Marg prints its lines as a '
                      'purchase; counted as a return</span>')
            else:
                vh = '<span class="ok">agrees</span>'
'''))

PA.append(("month page: the story through the gate",
'''                "bad" if s["wrong"] else "", s["wrong"], s["to_check"], _esc(s["story"])))
''',
'''                "bad" if s["wrong"] else "", s["wrong"], s["to_check"], _esc(s["story"] if final else _story_gated(s, gate))))
'''))

PA.append(("month page: the button and the note on the gate",
'''        if s["can_finalise"]:
            st = ('<div class="note"><b>PROVISIONAL</b> \\u2014 ready to finalise. %s</div>'
''',
'''        if gate[0]:
            st = ('<div class="note"><b>PROVISIONAL</b> \\u2014 ready to finalise. %s</div>'
'''))

PA.append(("month page: the reasons are the gate's",
'''                  % ("".join("<li>%s</li>" % _esc(r) for r in s["reasons"]),
''',
'''                  % ("".join("<li>%s</li>" % _esc(r) for r in gate[1]),
'''))


def apply(name, src, edits):
    out = src
    for label, old, new in edits:
        n = out.count(old)
        if n != 1:
            print("!! %s: anchor '%s' occurs %d times (must be exactly once) -- nothing written" % (name, label, n))
            sys.exit(2)
        out = out.replace(old, new, 1)
        print("   %s: anchored once, applied: %s" % (name, label))
    return out


def build(path, name, edits, outdir):
    raw = open(path, "rb").read()
    got = hashlib.md5(raw).hexdigest()
    if got != FROM[name]:
        print("!! %s is %s, not the FROM pin %s -- it changed after the brief: nothing written" % (path, got, FROM[name]))
        sys.exit(3)
    txt = raw.decode("utf-8")
    crlf = "\r\n" in txt
    if crlf:
        txt = txt.replace("\r\n", "\n")
    res = apply(name, txt, edits)
    if crlf:
        res = res.replace("\n", "\r\n")
    data = res.encode("utf-8")
    dst = os.path.join(outdir, name)
    with open(dst, "wb") as fh:
        fh.write(data)
    print("   %s: %s -> %s (%d edits, %d -> %d bytes)" % (name, FROM[name][:8], hashlib.md5(data).hexdigest(), len(edits), len(raw), len(data)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", default="")
    ap.add_argument("--marg-txt", default="")
    ap.add_argument("--manifest", default="", help="Drive ToMedical\\_kit\\KIT_MANIFEST.txt (0bf248e4); needs --marg-txt: the reader's line takes the new md5")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not (a.finance or a.marg_txt):
        ap.error("--finance and/or --marg-txt")
    if a.manifest and not a.marg_txt:
        ap.error("--manifest needs --marg-txt (the new md5 is the built reader's)")
    os.makedirs(a.out, exist_ok=True)
    if a.finance:
        build(os.path.join(a.finance, "purchase_app.py"), "purchase_app.py", PA, a.out)
    if a.marg_txt:
        build(a.marg_txt, "marg_txt.py", MT, a.out)
    if a.manifest:
        new = hashlib.md5(open(os.path.join(a.out, "marg_txt.py"), "rb").read()).hexdigest()
        line = "marg_txt.py | D:\\SendToClinic\\marg_txt.py | "
        build(a.manifest, "KIT_MANIFEST.txt", [("manifest: the reader's line carries its new md5 (nothing else changed)",
                                                line + FROM["marg_txt.py"] + "\n", line + new + "\n")], a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
