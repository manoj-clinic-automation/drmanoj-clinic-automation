#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""push_expected.py — what SHOULD be on the shelf, computed, not exported.

    baseline stock  +  purchases  -  vendor returns  -  sales  +  credit notes
    =  expected today

WHY THIS REPLACES push_snapshot.py AS THE DAILY FEED
    push_snapshot.py sends Marg's CLOSING-STOCK export. That export is taken
    occasionally, by hand. Scheduling it daily would re-send the same stale
    figure every morning and call it today's shelf.

    What actually arrives daily is the SALE report, by next morning. Purchases
    arrive when Amir visits, as a date-range export -- and a purchase reaches
    our books ONLY through that export, so a purchase we have not been sent is
    a purchase that has not happened as far as this ledger is concerned. That
    is the owner's rule and it is what makes this computation closed.

    push_snapshot.py is NOT retired. It is now the RE-BASELINE tool: run it
    when a fresh full closing export is taken, to reset the starting point.

THE TWO EXPORTS AMIR MUST TAKE, EVERY VISIT, OVER THE SAME DATE RANGE
    PURCHASE ITEM WISE      what came in: item, batch, expiry, quantity
    PURCHASE SUPPLIER WISE  supplier, DATE, bill number, amount
      -- or, since S224, PURCHASE BILL WISE: DATE group, bill number, party,
         amount. Either report dates a bill; both may be present. Where both
         name the same bill with DIFFERENT dates, SUPPLIER WISE is kept and
         the conflict is printed, never resolved silently.

    The item-wise report carries NO DATE on any row -- only supplier and bill
    number. Without a dated report there is no way to tell a purchase that
    happened after the baseline from one already inside it, and adding both
    would double-count. So a purchase file whose period reaches past the
    baseline is REFUSED unless every one of its bills can be dated.

WHAT IT REFUSES TO DO
    * push a figure for an item whose sales it could not read (see below)
    * count a purchase twice, or count one it cannot date
    * treat a category-filtered stock export as the whole shop (F-235)
    * claim a date for which purchases are not yet known -- it says so instead

    python3 push_expected.py --dry-run          compute and show, send nothing
    python3 push_expected.py --crosscheck       compute, then compare against
                                                Marg's OWN closing export for
                                                that date. The real test.
    python3 push_expected.py                    compute and send
    python3 push_expected.py --verify           prove the token, write nothing

Flask-free. Standard library plus the S206 readers, which are found relative to
this file -- no PYTHONPATH to set, and no path baked into a document.
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
for _sub in ("S206_SANJEEVNI_MARG_PURCHASE", "S206_SANJEEVNI_RECONCILE",
             "S224_MARG_PURCHASES", "S208_STOCK_LEDGER",
             os.path.join("S205_LIVE_TOOLS", "manojz")):
    _p = os.path.join(KITS, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, HERE)

import marg_report as MR            # noqa: E402  the daily sale report
import marg_stock as MS             # noqa: E402  closing stock
import marg_purchase as MP          # noqa: E402  purchase item-wise
import marg_purchase_rows as MBI    # noqa: E402  S224: BILL ITEM WISE
import purchase_returns as PR       # noqa: E402  marks return rows
import xlsx_sheet                   # noqa: E402
import packmap as PM                # noqa: E402  pack sizes, one match key
import resolve as RS                # noqa: E402  the 20-character truncation
import push_snapshot as PS          # noqa: E402  token, baseline picker, rates


# --- the S206 supersede rule (S212_SUPERSEDE, adopted S214) -----------------
# Two exports of one period are not two datasets; the later (or wider)
# replaces the earlier. Applied to FLOW reports only (sale / purchase):
# snapshot reports (STOCK_CLOSING, STOCK_EXPIRY) keep their own F-235
# largest-for-date pickers, where "latest stamp wins" would be the WRONG rule
# -- a later category-filtered export must not beat the whole-shop one.
sys.path.insert(0, os.path.join(KITS, "S212_SUPERSEDE"))
import marg_effective as _ME_sup


def _effective(paths):
    """Flow-report file list with superseded exports removed, loudly."""
    kept, superseded = _ME_sup.effective(sorted(paths))
    for _p, _by in superseded:
        print("  superseded export not counted: %s  (replaced by %s)"
              % (os.path.basename(_p), os.path.basename(_by)))
    return kept

MR._open_sheet = xlsx_sheet.open_sheet_any     # runtime only; live file untouched

DEF_ARCHIVE = PS.DEF_ARCHIVE
DEF_URL = PS.DEF_URL


# --------------------------------------------------------------- dates
def dkey(s):
    """'27-08-2026' or '2026-08-27' -> date. Anything else -> None."""
    s = str(s or "").strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def ddmmyyyy(d):
    return d.strftime("%d-%m-%Y")


# ------------------------------------------------------------ baseline
def baseline(archive, as_on=None):
    """The starting point: one whole-shop closing export.

    Reuses push_snapshot's picker, which already applies the F-235 guard --
    a category-filtered export carries the same store, the same date and a
    byte-identical header, so the universe is the LARGEST export for a date,
    never the latest file.
    """
    if as_on is None:
        rep, rejected = PS.newest_full(archive)
        return rep, rejected
    want = dkey(as_on)
    hits, available = [], []
    for p in sorted(glob.glob(os.path.join(archive, "STOCK_CLOSING", "*", "*"))):
        if not p.lower().endswith((".xls", ".xlsx")):
            continue
        try:
            rep = MS.read_closing(p)
        except Exception:                                      # noqa: BLE001
            continue
        if rep.get("store") != "WHOLE STORES":
            continue
        available.append((rep.get("as_on"), len(rep["rows"])))
        # Compare DATES, not the strings that spell them. A picker that only
        # matches text refuses a file it is holding, which is how "no export
        # found" gets reported about an archive that has one.
        if want is not None and dkey(rep.get("as_on")) == want:
            hits.append((len(rep["rows"]), rep))
    if not hits:
        return None, sorted(set(available))
    hits.sort(key=lambda t: t[0])
    return hits[-1][1], []


# --------------------------------------------------------------- sales
def sales_after(archive, after, upto=None):
    """Every sale item line dated after `after` (and up to `upto`).

    Deduplicated on (date, bill, line) because the same day is sometimes
    exported more than once -- 18-Aug and 24-Aug both have two files.
    """
    seen, lines, days, skipped = set(), [], set(), []
    pats = [os.path.join(archive, "SALE_BILLWISE", "*", "*.XLS"),
            os.path.join(archive, "SALE_BILLWISE", "*", "*.xlsx")]
    for p in _effective(sum([glob.glob(x) for x in pats], [])):
        try:
            rep = MR.read_report(p, keep_items=True)
        except Exception as e:                                 # noqa: BLE001
            skipped.append((os.path.basename(p), str(e)))
            continue
        if not rep.get("ok"):
            skipped.append((os.path.basename(p), "report not ok"))
            continue
        for d in rep.get("days") or []:
            for it in d.get("items") or []:
                bd = dkey(it.get("bill_date"))
                if bd is None or bd <= after or (upto and bd > upto):
                    continue
                ps = it.get("parsed") or {}
                key = (it.get("bill_date"), it.get("bill_no"), ps.get("seq"))
                if key in seen:
                    continue
                seen.add(key)
                days.add(bd)
                lines.append({"date": bd, "bill": it.get("bill_no"),
                              "item": ps.get("item_name"), "pack": ps.get("pack"),
                              "strips": ps.get("qty_strips"),
                              "loose": ps.get("qty_loose"),
                              "qty_raw": it.get("qty")})
    return lines, sorted(days), skipped


def sale_units(ln, size):
    """Base units on one sale line, and WHICH branch read it.

    The branch is named so a mis-read can be counted rather than guessed at.
    A strip line writes '0:1'; a tube, vial or spray writes '1.0'. A reader
    that knows only the first returns nothing for the second -- 2,807 lines,
    16.3% of the year, silently zero (F-225).
    """
    st, lo = ln.get("strips"), ln.get("loose")
    if st is not None or lo is not None:
        return PM.units(st or 0, lo or 0, size), "packs:loose"
    raw = str(ln.get("qty_raw") or "").strip()
    if not raw or raw == "-":
        return 0.0, "blank"
    try:
        return float(raw), "whole"
    except ValueError:
        return None, "unreadable"


# ----------------------------------------------------------- purchases
DATE_SOURCES = (("SUPPLIERWISE", "PURCHASE_SUPPLIERWISE"),
                ("BILLWISE", "PURCHASE_BILLWISE"))


def bill_dates(archive):
    """{(supplier, bill): date} from every PURCHASE SUPPLIER WISE export,
    then every PURCHASE BILL WISE export (S224).

    SUPPLIER WISE layout: a header row SUPPLIER NAME | DATE | BILL NO. | CASH
    | CREDIT, then one row per bill. The supplier cell is written once and
    left blank on the following rows of the same supplier, so it is carried
    down. TOTAL rows are skipped -- they are furniture, and a furniture row
    read as a bill is exactly the fault that made a page header look like a
    salt (S207).

    BILL WISE layout: a header row BILL NO. | PARTY NAME | CASH | CREDIT, then
    a DATE GROUP row (col0 = dd-mm-yyyy, the rest blank) and the bills under
    it: col0 bill number (may read as '160.0'), col1 party. The date carries
    down until the next date row; TOTAL ends the group.

    Merge rule: SUPPLIER WISE first. BILL WISE fills any (supplier, bill) not
    already dated. If both give DIFFERENT dates for one key, SUPPLIER WISE is
    kept and the pair is recorded in `conflicts` -- reported, never resolved.

    Returns (dates, files, conflicts). `files` rows read
    (name, bills read, bills newly dated, status, source).
    """
    out, files, conflicts = {}, [], []
    for source, sub in DATE_SOURCES:
        pats = [os.path.join(archive, sub, "*", "*.XLS"),
                os.path.join(archive, sub, "*", "*.xlsx")]
        for p in _effective(sum([glob.glob(x) for x in pats], [])):
            try:
                sh = xlsx_sheet.open_sheet_any(p)
            except Exception as e:                             # noqa: BLE001
                files.append((os.path.basename(p), 0, 0, str(e), source))
                continue
            if source == "SUPPLIERWISE":
                got = _supplierwise_rows(sh)
            else:
                got = _billwise_rows(sh)
            new = 0
            for key, date in got:
                have = out.get(key)
                if have is None:
                    out[key] = date
                    new += 1
                elif have != date and source != "SUPPLIERWISE":
                    conflicts.append((key[0], key[1], ddmmyyyy(have),
                                      ddmmyyyy(date), os.path.basename(p)))
                elif source == "SUPPLIERWISE":
                    out[key] = date            # within-source: later file wins
            files.append((os.path.basename(p), len(got), new, "ok", source))
    return out, files, conflicts


def _supplierwise_rows(sh):
    """[((supplier, bill), date)] from one SUPPLIER WISE sheet."""
    got, supplier = [], None
    for i in range(sh.nrows):
        cells = [_txt(c) for c in sh.row(i)]
        if not cells:
            continue
        first = cells[0].strip()
        rest = cells[1:] if len(cells) > 1 else []
        if first.upper().startswith("SUPPLIER NAME"):
            continue
        if first:
            supplier = first
        date = None
        bill = None
        for c in rest:
            cs = c.strip()
            if cs.upper().startswith("TOTAL"):
                date, bill = None, None
                break
            if date is None and dkey(cs):
                date = dkey(cs)
                continue
            if date is not None and bill is None and cs:
                bill = _billno(cs)
                break
        if supplier and date and bill:
            got.append(((PM.norm(supplier), bill), date))
    return got


def _billwise_rows(sh):
    """[((supplier, bill), date)] from one BILL WISE sheet.

    Nothing before the first date-group row is a bill: the shop's name,
    address and title lines sit above the header. TOTAL closes the group, so
    the footer line after it is never read as a bill either.
    """
    got, date = [], None
    for i in range(sh.nrows):
        cells = [_txt(c) for c in sh.row(i)]
        if not cells:
            continue
        first = cells[0].strip()
        if not first:
            continue
        up = first.upper()
        if up.startswith("BILL NO"):
            continue
        if up.startswith("TOTAL"):
            date = None
            continue
        rest = [c.strip() for c in cells[1:]]
        d = dkey(first)
        if d is not None and not any(rest):
            date = d
            continue
        if date is None:
            continue
        party = rest[0] if rest else ""
        if not party:
            continue
        got.append(((PM.norm(party), _billno(first)), date))
    return got


def _txt(cell):
    """xlsx_sheet hands back typed cells; take the printable part."""
    s = str(cell)
    if ":" in s and s.split(":", 1)[0] in ("text", "number", "empty", "date",
                                           "bool", "error", "blank"):
        s = s.split(":", 1)[1]
    return s.strip().strip("'")


def _billno(s):
    """'232.0' and '232' are the same bill. Keep it as a bare string."""
    s = str(s).strip().strip("'")
    try:
        return str(int(float(s)))
    except (TypeError, ValueError):
        return s



def billitem_after(archive, after):
    """S226. Purchase quantities from the BILL ITEM WISE export.

    WHY THIS EXISTS -- the owner, 06-Sep-2026: "check data of purchase exports
    in file, its there and was there in previous one also." He was right.

    This computation read PURCHASE_ITEMWISE and nothing else. Marg has a second
    report whose name differs by one word -- PURCHASE **BILL** ITEM WISE -- and
    it is the one that actually gets exported most mornings. It carries the same
    item, packing, quantity and loose quantity, and, unlike ITEM WISE, it
    carries THE BILL'S OWN DATE on every row, so nothing has to be dated by
    looking it up in another export. The server's money side has read it since
    S224. Only the stock side did not, and it cost a morning of exporting the
    right data into a reader that did not want it.

    A row is kept when its own bill date is after the baseline. The returned
    key set is (bill date, bill number, normalised item) so the ITEM WISE pass
    can skip anything already counted here -- a purchase counted twice is worse
    than a purchase not counted at all.

    LIMIT, STATED: this export exposes no variance rows, so purchase RETURNS
    cannot be identified in it the way purchase_returns.apply() identifies them
    in ITEM WISE. No negative or return row has ever appeared in one (every
    file in the archive was checked). If one does, this refuses rather than
    guess -- see the caller.
    """
    pats = [os.path.join(archive, "PURCHASE_BILLITEMWISE", "*", "*.XLS"),
            os.path.join(archive, "PURCHASE_BILLITEMWISE", "*", "*.xlsx")]
    rows, used, skipped, covered, negatives = [], [], [], {}, []

    # ONE EXPORT PER BILL DATE. Two BILL ITEM WISE exports overlap all the
    # time -- 01->06 Sep and 04->06 Sep both carry the 05-Sep bills -- and
    # neither supersedes the other, because their periods differ. Taking rows
    # from both counted every purchase TWICE: on the first run of this the
    # cross-check came back with eleven items out by exactly 2x, 1,480 units.
    #
    # Row-level de-duplication is the wrong tool: one bill can legitimately
    # carry the same item twice, in two batches. So the choice is made per
    # BILL DATE, the way F-322 chooses per as-on date: for each date, the
    # export with the LATEST capture stamp that covers it wins, and only that
    # export's rows for that date are read.
    def _taken(name):
        parts = str(os.path.basename(name)).split("__")
        return parts[2] if len(parts) > 2 else ""

    reps = []
    for path in _effective(sum([glob.glob(x) for x in pats], [])):
        try:
            rep = MBI.read_billitemwise(path)
        except Exception as e:                                 # noqa: BLE001
            skipped.append((os.path.basename(path), "unreadable: %s" % e))
            continue
        end = dkey(rep.get("period_to"))
        if end is None:
            skipped.append((os.path.basename(path), "no readable period"))
            continue
        if end <= after:
            skipped.append((os.path.basename(path),
                            "period ends %s, inside the baseline" % ddmmyyyy(end)))
            continue
        reps.append((path, rep, end))

    owner = {}          # bill date -> (capture stamp, path)
    for path, rep, _end in reps:
        for r in rep["rows"]:
            d = dkey(r.get("bill_date"))
            if d is None or d <= after:
                continue
            t = _taken(path)
            if d not in owner or t > owner[d][0]:
                owner[d] = (t, path)

    horizon = None
    for path, rep, end in reps:
        n, notmine = 0, 0
        for r in rep["rows"]:
            d = dkey(r.get("bill_date"))
            if d is None or d <= after:
                continue
            if owner[d][1] != path:
                notmine += 1
                continue
            if (r.get("qty") or 0) < 0 or (r.get("loose_qty") or 0) < 0:
                negatives.append((os.path.basename(path), r.get("bill_no"),
                                  r.get("item")))
                continue
            r["_date"] = d
            r["is_return"] = False
            r["bill"] = r.get("bill_no")
            rows.append(r)
            covered[(d, _billno(r.get("bill_no")), PM.norm(r.get("item")))] = True
            n += 1
        if notmine:
            skipped.append((os.path.basename(path),
                            "%d line(s) for day(s) a later export already "
                            "covers -- not counted twice" % notmine))
        if n:
            used.append((os.path.basename(path), n, ddmmyyyy(end)))
            horizon = end if horizon is None or end > horizon else horizon
    return rows, horizon, used, skipped, covered, negatives


def purchases_after(archive, after):
    """Dated purchase rows after the baseline. Refuses what it cannot date.

    A purchase file whose period ends on or before the baseline is SKIPPED
    whole -- everything in it is already inside the baseline figure, and
    adding it would count those goods twice. A file that reaches past the
    baseline must have every one of its bills datable, or the run refuses:
    an undated purchase is either double-counted or lost, and there is no
    third option.
    """
    dates, dfiles, dconf = bill_dates(archive)
    # S226: BILL ITEM WISE first. It dates itself, so it needs no lookup, and
    # what it covers the ITEM WISE pass must not count again.
    rows, bhorizon, bused, bskipped, covered, bnegatives = \
        billitem_after(archive, after)
    used = [(n + "  [BILL ITEM WISE]", k, e) for n, k, e in bused]
    skipped = [(n + "  [BILL ITEM WISE]", w) for n, w in bskipped]
    undated, conflicts = [], []
    pats = [os.path.join(archive, "PURCHASE_ITEMWISE", "*", "*.XLS"),
            os.path.join(archive, "PURCHASE_ITEMWISE", "*", "*.xlsx")]
    horizon = bhorizon
    for p in _effective(sum([glob.glob(x) for x in pats], [])):
        try:
            rep = MP.read_purchase(p)
        except Exception as e:                                 # noqa: BLE001
            skipped.append((os.path.basename(p), "unreadable: %s" % e))
            continue
        end = _period_end(rep.get("period"))
        if end is None:
            skipped.append((os.path.basename(p), "no readable period"))
            continue
        if end <= after:
            skipped.append((os.path.basename(p),
                            "period ends %s, inside the baseline" % ddmmyyyy(end)))
            continue
        PR.apply(rep)
        n = 0
        for r in rep["rows"]:
            key = (PM.norm(r.get("supplier")), _billno(r.get("bill")))
            d = dates.get(key)
            if d is None:
                undated.append((os.path.basename(p), r.get("supplier"),
                                r.get("bill"), r.get("item")))
                continue
            if d <= after:
                continue
            key = (d, _billno(r.get("bill")), PM.norm(r.get("item")))
            if key in covered:
                continue          # BILL ITEM WISE already counted this bill line
            r["_date"] = d
            rows.append(r)
            n += 1
        used.append((os.path.basename(p) + "  [ITEM WISE]", n, ddmmyyyy(end)))
        horizon = end if horizon is None or end > horizon else horizon
    return (rows, horizon, used, skipped, undated, dfiles, dconf,
            conflicts, bnegatives)


def _period_end(period):
    """A period reads like '2026-08-01 to 2026-08-26' or a pair. Take the end."""
    if isinstance(period, (list, tuple)) and len(period) == 2:
        return dkey(period[1])
    s = str(period or "")
    found = [dkey(t) for t in s.replace("_", " ").replace("to", " ").split()]
    found = [d for d in found if d]
    return max(found) if found else None


# ------------------------------------------------ S240 late-keyed bills
# THE OWNER, 11-Sep-2026 (D465): "Ravi bill date is 6 but it arrived late,
# don't confuse, the physical stock was a actual inventory at that time."
# And: a Marg stock export is ALWAYS the current stock -- there is no dated
# option. So the baseline is "everything KEYED into Marg by the moment it was
# exported", not "everything DATED on or before its as-on day".
#
# The ledger above adds purchases by BILL DATE (> baseline). Those two rules
# disagree for exactly two kinds of bill:
#   LATE   dated on/before the baseline, keyed AFTER the export was taken.
#          Not in the baseline, and skipped by the date rule. Lost -- ours
#          reads LOW. (Yuvika 571: dated 01-09, keyed 06-09 morning.)
#   EARLY  dated after the baseline, keyed BEFORE the export was taken.
#          In the baseline AND added again. Counted twice.
# Keying time is never exported, so it is bounded from the capture stamps:
#   hi = the first export (item level) that CONTAINS the bill
#   lo = the last export that covers its date and does NOT contain it
#        (never earlier than the bill's own date)
# If hi <= baseline capture   -> keyed before: inside the baseline.
# If lo >= baseline capture   -> keyed after:  LATE, proven by the exports.
# Otherwise the window straddles the baseline, and the whole-shop closing
# exports taken inside that window decide it: each of the bill's items is
# looked for as a step UP between two consecutive closings. If every item
# that shows a step shows it in the same gap, that gap is on one side of the
# baseline and settles it. Anything else is NAMED as "keying time unknown"
# and left out -- guessing either way is how a count gets blamed on a person.

def _stamp(path):
    parts = str(os.path.basename(path)).split("__")
    return parts[2] if len(parts) > 2 else ""


def _period_start(period):
    if isinstance(period, (list, tuple)) and len(period) == 2:
        return dkey(period[0])
    s = str(period or "")
    found = [dkey(t) for t in s.replace("_", " ").replace("to", " ").split()]
    found = [d for d in found if d]
    return min(found) if found else None


def _item_exports(archive, dates):
    """Every item-level purchase export, superseded ones INCLUDED -- a file
    replaced for counting is still a true picture of what was keyed at the
    moment it was taken. -> [(stamp, kind, start, end, {(date, bill): rows})]"""
    out = []
    for kind, sub in (("BILL ITEM WISE", "PURCHASE_BILLITEMWISE"),
                      ("ITEM WISE", "PURCHASE_ITEMWISE")):
        for p in sorted(glob.glob(os.path.join(archive, sub, "*", "*"))):
            if not p.lower().endswith((".xls", ".xlsx")):
                continue
            try:
                if kind == "BILL ITEM WISE":
                    rep = MBI.read_billitemwise(p)
                    start, end = dkey(rep.get("period_from")), dkey(rep.get("period_to"))
                else:
                    rep = MP.read_purchase(p)
                    PR.apply(rep)
                    start = _period_start(rep.get("period"))
                    end = _period_end(rep.get("period"))
            except Exception:                                  # noqa: BLE001
                continue
            if start is None or end is None:
                continue
            bills = collections.defaultdict(list)
            for r in rep["rows"]:
                if kind == "BILL ITEM WISE":
                    d, b = dkey(r.get("bill_date")), r.get("bill_no")
                else:
                    b = r.get("bill")
                    d = dates.get((PM.norm(r.get("supplier")), _billno(b)))
                if d is None:
                    continue
                bills[(d, _billno(b))].append(r)
            out.append((_stamp(p), kind, start, end, dict(bills),
                        os.path.basename(p)))
    # Bill-level exports (SUPPLIER WISE, BILL WISE) carry no items, but they
    # are taken far more often -- and a bill's presence or absence in one is
    # the same evidence of when it was keyed. Presence only: no rows.
    for source, sub in DATE_SOURCES:
        for p in sorted(glob.glob(os.path.join(archive, sub, "*", "*"))):
            if not p.lower().endswith((".xls", ".xlsx")):
                continue
            parts = os.path.basename(p).split("__")
            span = [dkey(x) for x in (parts[1].split("_to_")
                                      if len(parts) > 2 else [])]
            if not span or None in span:
                continue
            try:
                sh = xlsx_sheet.open_sheet_any(p)
                got = (_supplierwise_rows(sh) if source == "SUPPLIERWISE"
                       else _billwise_rows(sh))
            except Exception:                                  # noqa: BLE001
                continue
            if not got:
                continue
            bills = dict(((d, key[1]), []) for key, d in got)
            out.append((_stamp(p), source, min(span), max(span), bills,
                        os.path.basename(p)))
    return out


def _closings(archive):
    """Whole-shop closing exports by capture stamp: [(stamp, {key: units})]."""
    best = {}
    for p in glob.glob(os.path.join(archive, "STOCK_CLOSING", "*", "*")):
        if not p.lower().endswith((".xls", ".xlsx")):
            continue
        try:
            rep = MS.read_closing(p)
        except Exception:                                      # noqa: BLE001
            continue
        if rep.get("store") != "WHOLE STORES" or \
                len(rep["rows"]) < PS.FILTERED_MAX:
            continue
        t = _stamp(p)
        if t in best and len(best[t]["rows"]) >= len(rep["rows"]):
            continue
        best[t] = rep
    out = []
    for t in sorted(best):
        m = collections.Counter()
        for r in best[t]["rows"]:
            k = PM.norm(r.get("item"))
            if k:
                m[k] += (r.get("units") or 0)
        out.append((t, m))
    return out


def _complete_name(k, names):
    """ITEM WISE cuts long names ('...LF L ELA' for '...LF L ELAST'). Map a
    cut name to the ONE full name it is the start of; never guess between two,
    never touch a short name (a short name was not cut)."""
    if not k or k in names or len(k) < RS.TRUNC_LEN:
        return k
    fam = [m for m in names if len(m) > len(k) and m.startswith(k)]
    return fam[0] if len(fam) == 1 else k


def _closing_verdict(bill_rows, lo, hi, T_b, closings):
    """'late', 'in', or None. See the block comment above."""
    pre = [c for c in closings if c[0] <= lo]
    post = [c for c in closings if c[0] >= hi]
    if not pre or not post:
        return None, "no closing export on both sides"
    seq = [pre[-1]] + [c for c in closings if lo < c[0] < hi] + [post[0]]
    if len(seq) < 2:
        return None, "no closing export inside the window"
    names = set(seq[-1][1]) | set(seq[0][1])
    votes = set()
    for r in bill_rows:
        k = _complete_name(PM.norm(r.get("item")), names)
        incs = [seq[j + 1][1].get(k, 0) - seq[j][1].get(k, 0)
                for j in range(len(seq) - 1)]
        top = max(incs)
        if top <= 0 or incs.count(top) != 1:
            continue
        votes.add(incs.index(top))
    if len(votes) != 1:
        return None, ("no item stepped up" if not votes
                      else "items stepped up in different gaps")
    j = votes.pop()
    a, b = seq[j][0], seq[j + 1][0]
    if a >= T_b:
        return "late", "closings %s -> %s" % (a, b)
    if b <= T_b:
        return "in", "closings %s -> %s" % (a, b)
    return None, "the step straddles the baseline"


def keyed_vs_dated(archive, B, T_b):
    """-> (late_rows, late_report, early_keys, early_report, unknown_report).
    late_rows are ready to add to the purchase list (dated, '_late' marked)."""
    late_rows, late_rep, early, early_rep, unknown = [], [], set(), [], []
    if os.environ.get("LATE_KEYED", "").strip().lower() == "off":
        return late_rows, late_rep, early, early_rep, unknown   # switch-off
    if not T_b:
        return late_rows, late_rep, early, early_rep, unknown
    dates, _f, _c = bill_dates(archive)
    ex = _item_exports(archive, dates)
    if not ex:
        return late_rows, late_rep, early, early_rep, unknown
    closings = None
    # the bills as they stand NOW: per date, the newest export covering it
    newest = {}
    for e in ex:
        t, _k, s, en, bills, _n = e
        d = s
        while d <= en:
            if d not in newest or t > newest[d][0]:
                newest[d] = e
            d += dt.timedelta(days=1)
    for d in sorted(newest):
        t_new, _k, _s, _e, bills_new, _n = newest[d]
        if t_new <= T_b and d <= B:
            continue          # all of it keyed before the baseline: inside it
        for key in sorted(k for k in bills_new if k[0] == d):
            has = sorted(e[0] for e in ex if key in e[4])
            hi = has[0]
            lacks = [e[0] for e in ex if e[2] <= d <= e[3]
                     and key not in e[4] and e[0] < hi]
            lo = max(lacks + [d.strftime("%Y%m%d-000000")])
            # the rows to use: the newest BILL ITEM WISE holding the bill
            # (full names, dates itself), else the newest ITEM WISE
            srcs = sorted((e for e in ex if e[4].get(key)),
                          key=lambda e: (e[1] == "BILL ITEM WISE", e[0]))
            if not srcs:
                continue          # seen only in bill-level exports: no items
            src = srcs[-1]
            rows = src[4][key]
            if d <= B:
                if hi <= T_b:
                    continue                      # keyed before: in baseline
                if lo >= T_b:
                    verdict, why = "late", "not in the export of %s" % lo
                else:
                    if closings is None:
                        closings = _closings(archive)
                    verdict, why = _closing_verdict(rows, lo, hi, T_b, closings)
                if verdict == "late":
                    for r in rows:
                        r = dict(r)
                        r["_date"] = d
                        r["bill"] = r.get("bill") or r.get("bill_no")
                        r["is_return"] = bool(r.get("is_return"))
                        r["_late"] = True
                        late_rows.append(r)
                    late_rep.append((ddmmyyyy(d), key[1], len(rows), why, src[5]))
                elif verdict is None:
                    unknown.append((ddmmyyyy(d), key[1], len(rows), why))
            else:
                if hi <= T_b:
                    early.add(key)
                    early_rep.append((ddmmyyyy(d), key[1], len(rows),
                                      "in the export of %s" % hi))
    return late_rows, late_rep, early, early_rep, unknown


# ------------------------------------------ S240 clipped sale names (D466)
# THE OWNER, 11-Sep-2026: no product is renamed "until unless there is no
# other way, because everybody is accustomed and tuned to it" -- the counter,
# Amir, the whole shop. So the 20-character sale name stays, and the size it
# hides is found another way.
#
# THE OTHER WAY. The counter never sells "KNEE SUPPORT HINGED": it picks one
# real item in Marg -- L, M, XL or XXL -- and Marg takes that item's stock
# down. Only the sale EXPORT prints the name clipped. The whole-shop closing
# export prints 29 characters, which tells every one of the 22 apart, and it
# is taken every night. So between two closings, the size whose stock fell
# IS the size that was sold -- the same fact Marg recorded, read from a report
# that does not clip it.
#
# A family is settled for one gap between two closings only when the books
# balance exactly: for every size, (fall in stock + purchases of that size in
# the gap) is a whole number, and the family's total equals what the sale
# export says the family sold (returns netted). Anything else -- a purchase
# whose own name is clipped, a closing taken in the middle of a shop day, a
# sale after the last closing -- stays as before: not subtracted, and named.
# The next night's closing usually settles it.

def _gap_side(d, stamp):
    """Is a sale dated d before (-1) or after (+1) the closing taken at stamp?
    0 = cannot tell (closing taken during that day's shop hours)."""
    sd = dt.datetime.strptime(stamp[:8], "%Y%m%d").date()
    hm = stamp[9:13]
    if d < sd:
        return -1
    if d > sd:
        return 1
    if hm >= "2200":
        return -1
    if hm < "0900":
        return 1
    return 0


def resolve_clipped(lines, families, closings, pur, size_of, B, T_b):
    """-> (alloc {full key: net units sold}, settled line ids, report, open).
    lines: sale lines already keyed (ln['_key'] = the clipped name).
    families: {clipped key: [full keys]}."""
    alloc, settled, report, still = collections.Counter(), set(), [], []
    if os.environ.get("CLIP_RESOLVE", "").strip().lower() == "off":
        return alloc, settled, report, still
    mine = [ln for ln in lines if ln.get("_key") in families]
    if not mine or not T_b:
        return alloc, settled, report, still
    # the boundaries: the baseline itself, then every closing after it that
    # can be placed against the sale dates
    bounds = [(T_b, None)]
    for t, m in closings:
        if t > T_b and t[9:13] and (t[9:13] >= "2200" or t[9:13] < "0900"):
            bounds.append((t, m))
    base_map = dict(closings).get(T_b)
    if base_map is None:
        return alloc, settled, report, [(ln["date"], ln["bill"], ln["_key"], "baseline closing not readable") for ln in mine]
    bounds[0] = (T_b, base_map)
    for j in range(len(bounds) - 1):
        (ta, ma), (tb, mb) = bounds[j], bounds[j + 1]
        for fam, fulls in families.items():
            inside = [ln for ln in mine if ln["_key"] == fam
                      and (j == 0 or _gap_side(ln["date"], ta) == 1)
                      and _gap_side(ln["date"], tb) == -1]
            if not inside:
                continue
            want, bad = 0.0, False
            for ln in inside:
                u, _br = sale_units(ln, size_of(fulls[0]))
                if u is None:
                    bad = True
                    break
                want += -u if PS_is_cn(ln.get("bill")) else u
            if bad:
                continue
            da = dt.datetime.strptime(ta[:8], "%Y%m%d").date()
            db = dt.datetime.strptime(tb[:8], "%Y%m%d").date()
            # Purchases of the family in the gap. Their KEYING moment is what
            # the closings saw, and it is not exported, so three readings are
            # tried and only an exact balance is accepted: none keyed in the
            # gap; those dated in it (late-keyed bills left out); all dated
            # in it. A wrong reading cannot balance, because every size must
            # come out whole and the family must total what was sold.
            dated, dated_nl, clipped_buy = (collections.Counter(),
                                            collections.Counter(), False)
            for r in pur:
                k = PM.norm(r.get("item"))
                d = r.get("_date")
                if d is None or not (da <= d <= db):
                    continue
                if k in fulls:
                    q = r.get("loose_qty") or 0
                    q = -q if r.get("is_return") else q
                    dated[k] += q
                    if not r.get("_late"):
                        dated_nl[k] += q
                elif k and any(f.startswith(k) for f in fulls):
                    clipped_buy = True
            ok, sold = False, {}
            for bought in (collections.Counter(), dated_nl, dated):
                if clipped_buy and bought:
                    continue
                sold = {f: (ma.get(f, 0) - mb.get(f, 0)) + bought[f] for f in fulls}
                ok = (all(abs(v - round(v)) < 1e-6 for v in sold.values())
                      and abs(sum(sold.values()) - want) < 1e-6
                      and (want < 0 or all(v >= -1e-6 for v in sold.values())))
                if ok:
                    break
            if not ok:
                continue
            for f, v in sold.items():
                if abs(v) > 1e-6:
                    alloc[f] += v
            for ln in inside:
                settled.add(id(ln))
            report.append((ta, tb, fam, len(inside),
                           ", ".join("%s %+.0f" % (f, -v)
                                     for f, v in sorted(sold.items()) if abs(v) > 1e-6)))
    for ln in mine:
        if id(ln) not in settled:
            last = bounds[-1][0]
            why = ("sold after the last closing export (%s)" % last
                   if _gap_side(ln["date"], last) != -1 else
                   "the closings do not balance for this family in that gap")
            still.append((ln["date"], ln["bill"], ln["_key"], why))
    return alloc, settled, report, still


# ------------------------------------------------------------- compute
def compute(archive, base_as_on=None, upto=None):
    """Everything, in one pass. Returns a dict; raises nothing quietly."""
    base, rejected = baseline(archive, base_as_on)
    if base is None:
        have = ", ".join("%s (%d items)" % (d, n) for d, n in rejected) or "none"
        return {"error": "no WHOLE STORES closing export for %s. Available: %s"
                         % (base_as_on or "the newest date", have)}
    if len(base["rows"]) < PS.FILTERED_MAX:
        return {"error": "the baseline export has only %d rows -- that is a "
                         "filtered subset, not the shop (F-235)"
                         % len(base["rows"])}
    B = dkey(base.get("as_on"))
    if B is None:
        return {"error": "the baseline export carries no readable as-on date"}

    (pur, horizon, pused, pskipped, undated, dfiles, dconf,
     pconflicts, pnegatives) = purchases_after(archive, B)
    if pnegatives:
        return {"error": "%d BILL ITEM WISE line(s) carry a negative quantity. "
                         "That export marks no returns, so a negative cannot be "
                         "read safely. Nothing sent." % len(pnegatives),
                "billitem_negatives": pnegatives[:10]}
    if pconflicts:
        return {"error": "%d purchase line(s) appear in BOTH the BILL ITEM WISE "
                         "and the ITEM WISE export with DIFFERENT quantities. "
                         "One of the two exports is stale. Nothing sent."
                         % len(pconflicts),
                "purchase_conflicts": pconflicts[:10]}
    if undated:
        return {"error": "%d purchase line(s) could not be dated -- the "
                         "SUPPLIER WISE or BILL WISE export for the same range "
                         "is missing or does not cover them. Nothing sent."
                         % len(undated),
                "undated": undated[:10], "date_files": dfiles,
                "date_conflicts": dconf}

    # S240: bills keyed on the other side of the baseline's capture moment.
    T_b = _stamp(base.get("source") or "")
    late_rows, late_rep, early, early_rep, unknown = keyed_vs_dated(archive, B, T_b)
    if early:
        pur = [r for r in pur
               if (r.get("_date"), _billno(r.get("bill"))) not in early]
    bnames = {}
    for r in base["rows"]:
        bnames.setdefault(PM.norm(r.get("item")), r.get("item"))
    for r in late_rows:                 # ITEM WISE cuts long names
        k = _complete_name(PM.norm(r.get("item")), bnames)
        if k in bnames and k != PM.norm(r.get("item")):
            r["item"] = bnames[k]
    pur = pur + late_rows

    sale, sdays, sskipped = sales_after(archive, B, upto)
    if not sdays:
        return {"error": "no sale report dated after the baseline (%s). "
                         "Nothing to compute." % ddmmyyyy(B), "empty": True}
    last_sale = max(sdays)
    as_on = last_sale if upto is None else min(last_sale, upto)
    if upto is not None:
        # --upto is a cross-check tool: a purchase dated after it is not part
        # of the shelf on that day. (The daily run passes no --upto.)
        pur = [r for r in pur if r.get("_date") is None or r["_date"] <= as_on]

    # ---- pack sizes: observed, never assumed ----
    obs = []
    for r in base["rows"]:
        obs.append((r.get("item"), r.get("packing"), "stock"))
    for r in pur:
        obs.append((r.get("item"), r.get("packing"), "purchase"))
    for ln in sale:
        if ln.get("item"):
            obs.append((ln["item"], ln.get("pack"), "sale"))
    pmap, pconflicts = PM.build(obs)

    def size_of(name):
        return (pmap.get(PM.norm(name)) or {}).get("size")

    # ---- the master name list, and the sale report's truncation ----
    master = set()
    disp, packing = {}, {}
    for r in base["rows"]:
        k = PM.norm(r.get("item"))
        if k:
            master.add(k)
            disp.setdefault(k, r["item"])
            packing.setdefault(k, r.get("packing"))
    for r in pur:
        k = PM.norm(r.get("item"))
        if k:
            master.add(k)
            disp.setdefault(k, r["item"])
            packing.setdefault(k, r.get("packing"))
    skeys = set()
    for ln in sale:
        nm, _ = RS.unglue(ln.get("item"))
        ln["_key"] = PM.norm(nm)
        if ln["_key"]:
            skeys.add(ln["_key"])
    mapping, ambiguous, unresolved = RS.build_map(skeys, master)

    # ---- the ledger ----
    M = collections.defaultdict(lambda: collections.defaultdict(float))
    for r in base["rows"]:
        k = PM.norm(r.get("item"))
        if k:
            M[k]["base"] += (r.get("units") or 0)
    for r in pur:
        k = PM.norm(r.get("item"))
        q = r.get("loose_qty")
        if not k or q is None:
            continue
        M[k]["preturn" if r.get("is_return") else "purchased"] += q

    # S240 (D466): the clipped names, settled from the nightly closings.
    fams = {k: sorted(v) for k, v in dict(ambiguous).items()}
    clip_alloc, clip_done, clip_rep, clip_open = resolve_clipped(
        sale, fams, _closings(archive) if fams else [], pur, size_of, B, T_b)
    for f, u in clip_alloc.items():
        M[f]["sold"] += u

    branch = collections.Counter()
    blocked = set(ambiguous) | set(unresolved)
    blocked_names = collections.Counter()
    sold_lines = 0
    for ln in sale:
        k = ln.get("_key")
        if not k:
            continue
        if id(ln) in clip_done:
            branch["clipped, settled"] += 1
            continue
        if k in blocked:
            branch["blocked"] += 1
            blocked_names[ln.get("item") or k] += 1
            continue
        k = mapping.get(k, k)
        u, br = sale_units(ln, size_of(disp.get(k, k)))
        branch[br] += 1
        if u is None:
            blocked.add(k)                 # a line we cannot read poisons its item
            continue
        sold_lines += 1
        M[k]["credit" if PS_is_cn(ln.get("bill")) else "sold"] += u

    items, held = [], []
    for k, v in M.items():
        if k in blocked:
            held.append(disp.get(k, k))
            continue
        qty = (v["base"] + v["purchased"] - v["preturn"] - v["sold"] + v["credit"])
        items.append({"key": k, "item": disp.get(k, k), "qty": qty,
                      "packing": packing.get(k),
                      "moved": bool(v["purchased"] or v["sold"] or
                                    v["credit"] or v["preturn"])})
    if horizon is None:
        horizon = B          # no purchase export since the baseline means no
                             # purchase EXISTS since the baseline -- purchases
                             # reach these books only through that export.
    return {"baseline_as_on": B, "baseline_items": len(base["rows"]),
            "baseline_source": base.get("source") or "",
            "baseline_taken": T_b, "late_bills": late_rep,
            "early_bills": early_rep, "keying_unknown": unknown,
            "clipped_settled": clip_rep, "clipped_open": clip_open,
            "rejected": rejected, "as_on": as_on, "sale_days": sdays,
            "sale_lines": len(sale), "sold_lines": sold_lines,
            "purchase_rows": len(pur), "purchase_horizon": horizon,
            "purchase_files": pused, "purchase_skipped": pskipped,
            "sale_skipped": sskipped, "supplierwise_files": dfiles,
            "date_files": dfiles, "date_conflicts": dconf,
            "branches": dict(branch), "pack_conflicts": pconflicts,
            "blocked_names": blocked_names.most_common(20),
            "negative": sorted([(i["item"], i["qty"]) for i in items
                                if i["qty"] < 0], key=lambda t: t[1]), "ambiguous": sorted(ambiguous)[:20],
            "unresolved": sorted(unresolved)[:20], "held": sorted(held),
            "items": items, "packmap": pmap}


def PS_is_cn(bill):
    """A credit note is goods coming BACK. Subtracting it doubles the error."""
    return str(bill or "").strip().upper().startswith("CN")


# ---------------------------------------------------------- cross-check
def crosscheck(archive, rep):
    """Compare the computed figure against Marg's OWN closing export for the
    same date. This is the only independent test there is, and it is the
    method that found three faults at S206."""
    want = ddmmyyyy(rep["as_on"])
    marg, _ = baseline(archive, want)
    if marg is None:
        return None
    theirs = {}
    for r in marg["rows"]:
        k = PM.norm(r.get("item"))
        if k:
            theirs[k] = theirs.get(k, 0) + (r.get("units") or 0)
    same, diff, missing, extra, gap = 0, [], 0, 0, 0.0
    for it in rep["items"]:
        k = it["key"]
        if k not in theirs:
            extra += 1
            continue
        d = it["qty"] - theirs[k]
        if abs(d) < 0.001:
            same += 1
        else:
            diff.append((it["item"], it["qty"], theirs[k], d))
            gap += abs(d)
    ours = set(i["key"] for i in rep["items"])
    missing = len([k for k in theirs if k not in ours])
    diff.sort(key=lambda t: -abs(t[3]))
    return {"as_on": want, "same": same, "differ": len(diff), "gap_units": gap,
            "in_marg_not_ours": missing, "in_ours_not_marg": extra,
            "worst": diff[:15], "marg_items": len(theirs)}


# ----------------------------------------------------------------- send
def send(url, body, tok):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Finance-Marg": tok})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def _print_date_files(rep):
    """Which export dated the bills, and any date the two sources dispute."""
    for row in rep.get("date_files") or []:
        f, n, new, status, source = row
        print("dates      %-12s %s   %d bill(s), %d newly dated%s"
              % (source, f[:44], n, new, "" if status == "ok" else " -- " + status))
    conf = rep.get("date_conflicts") or []
    if conf:
        print("  !! %d bill(s) dated DIFFERENTLY by the two purchase reports -- "
              "SUPPLIER WISE kept, not resolved:" % len(conf))
        for sup, bill, kept, other, f in conf[:10]:
            print("     %-28s bill %-8s %s (supplier wise)  vs  %s (%s)"
                  % (sup[:28], bill, kept, other, f[:44]))


def _print_clipped(rep):
    """S240 (D466): sale names Marg clips at 20 characters, settled by size."""
    done, still = rep.get("clipped_settled") or [], rep.get("clipped_open") or []
    if not (done or still):
        return
    print("  CLIPPED SALE NAMES -- the size read from the nightly closing exports:")
    for ta, tb, fam, n, what in done:
        print("     %-20s %d line(s), closings %s -> %s : %s"
              % (fam[:20], n, ta[4:13], tb[4:13], what))
    if still:
        print("  %d clipped sale line(s) not settled yet -- NOT subtracted:" % len(still))
        for d, bill, fam, why in still[:10]:
            print("     %s %-9s %-20s %s" % (ddmmyyyy(d), bill, fam[:20], why))


def _print_keying(rep):
    """S240: bills whose keying moment, not their date, decides the count."""
    t = rep.get("baseline_taken") or "unknown"
    B = rep.get("baseline_as_on")
    if B and t[:8] == B.strftime("%Y%m%d") and "0900" <= t[9:13] < "2200":
        print("  note: the baseline export was taken at %s:%s on its own day. "
              "Sales rung up on %s AFTER that moment are in neither figure -- "
              "take the closing export after the counter shuts."
              % (t[9:11], t[11:13], ddmmyyyy(B)))
    late, early, unk = (rep.get("late_bills") or [], rep.get("early_bills") or [],
                        rep.get("keying_unknown") or [])
    if not (late or early or unk):
        print("keying     no bill keyed across the baseline export (taken %s)" % t)
        return
    print("keying     baseline export taken %s" % t)
    if late:
        print("  LATE-KEYED BILLS ADDED -- dated on/before the baseline, keyed after it:")
        for d, b, n, why, src in late:
            print("     bill %-9s dated %s  %d line(s)  (%s)" % (b, d, n, why))
    if early:
        print("  EARLY-KEYED BILLS NOT ADDED AGAIN -- already inside the baseline:")
        for d, b, n, why in early:
            print("     bill %-9s dated %s  %d line(s)  (%s)" % (b, d, n, why))
    if unk:
        print("  !! KEYING TIME UNKNOWN -- NOT added; may be missing from this figure:")
        for d, b, n, why in unk:
            print("     bill %-9s dated %s  %d line(s)  (%s)" % (b, d, n, why))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    ap.add_argument("--url", default=DEF_URL)
    ap.add_argument("--baseline", default=None,
                    help="pin the starting export, dd-mm-yyyy. Default: newest")
    ap.add_argument("--upto", default=None,
                    help="compute only to this date, dd-mm-yyyy")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--crosscheck", action="store_true",
                    help="compare against Marg's own closing export, send nothing")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)

    if a.verify:
        return PS.verify(a.url)
    if not os.path.isdir(a.archive):
        print("ARCHIVE NOT REACHABLE -- %s" % a.archive)
        return 2

    rep = compute(a.archive, a.baseline, dkey(a.upto) if a.upto else None)
    if rep.get("error"):
        print("REFUSING: %s" % rep["error"])
        for u in rep.get("undated", []):
            print("   undated: %s bill %s  %s" % (u[1], u[2], u[3]))
        _print_date_files(rep)
        return 0 if rep.get("empty") else 1

    for name, n in rep["rejected"]:
        print("  skipped %s (%d rows) -- a category filter, not the shop (F-235)"
              % (name, n))
    print("baseline   %s   %d items" % (ddmmyyyy(rep["baseline_as_on"]),
                                        rep["baseline_items"]))
    for f, n, end in rep["purchase_files"]:
        print("purchases  %s   %d dated line(s), period to %s" % (f[:44], n, end))
    for f, why in rep["purchase_skipped"]:
        print("  skipped %s -- %s" % (f[:44], why))
    _print_keying(rep)
    _print_date_files(rep)
    print("sales      %d line(s) over %d day(s), %s .. %s"
          % (rep["sale_lines"], len(rep["sale_days"]),
             ddmmyyyy(rep["sale_days"][0]), ddmmyyyy(rep["sale_days"][-1])))
    print("           read as %s" % rep["branches"])
    if rep["pack_conflicts"]:
        print("  %d item(s) whose sources disagree on pack size -- reported, "
              "never resolved:" % len(rep["pack_conflicts"]))
        for c in rep["pack_conflicts"][:5]:
            print("     %-28s %s" % (c["item"][:28],
                                     " vs ".join(v["packing"] for v in c["variants"])))
    print("EXPECTED AS ON %s : %d items, %d of them moved"
          % (ddmmyyyy(rep["as_on"]), len(rep["items"]),
             sum(1 for i in rep["items"] if i["moved"])))

    h = rep["purchase_horizon"]
    if h >= rep["as_on"]:
        print("  purchases known to %s -- complete for this date" % ddmmyyyy(h))
    else:
        print("  !! PURCHASES KNOWN ONLY TO %s, expected is for %s."
              % (ddmmyyyy(h), ddmmyyyy(rep["as_on"])))
        print("     Anything entered into Marg after that is NOT in this "
              "figure. Count after Amir's visit, not before it.")
    if rep["negative"]:
        print("  !! %d item(s) COMPUTE BELOW ZERO. That is not missing stock -- "
              "it is missing PURCHASE data:" % len(rep["negative"]))
        for nm, q in rep["negative"][:8]:
            print("     %-30s %.0f" % (nm[:30], q))
        print("     Sales were rung up for goods this ledger never saw arrive. "
              "Export PURCHASE > BILL ITEM WISE for the range in Marg -- that "
              "one report is enough, and it dates itself -- then run again.")
    if rep["blocked_names"]:
        print("  %d sale line(s) could not be tied to an item -- their units are "
              "NOT subtracted:" % sum(n for _, n in rep["blocked_names"]))
        for nm, n in rep["blocked_names"][:8]:
            print("     %-30s %d line(s)" % (str(nm)[:30], n))
    _print_clipped(rep)
    if rep["held"]:
        print("  %d item(s) NOT sent -- their sales could not be read safely:"
              % len(rep["held"]))
        for n in rep["held"][:10]:
            print("     %s" % n)

    if a.crosscheck:
        cc = crosscheck(a.archive, rep)
        if cc is None:
            print("\nno Marg closing export for %s to compare against."
                  % ddmmyyyy(rep["as_on"]))
            return 0
        print("\nCROSS-CHECK against Marg's own closing export for %s" % cc["as_on"])
        print("  exact match      %d of %d" % (cc["same"], cc["same"] + cc["differ"]))
        print("  differ           %d items, %.0f units in total"
              % (cc["differ"], cc["gap_units"]))
        print("  in Marg, not us  %d        in us, not Marg  %d"
              % (cc["in_marg_not_ours"], cc["in_ours_not_marg"]))
        for nm, ours, theirs, d in cc["worst"]:
            print("    %-30s ours %8.0f   Marg %8.0f   %+.0f"
                  % (nm[:30], ours, theirs, d))
        return 0

    body = {"as_on": ddmmyyyy(rep["as_on"]),
            "source": "push_expected base=%s pur_to=%s"
                      % (ddmmyyyy(rep["baseline_as_on"]),
                         ddmmyyyy(h) if h else "none"),
            "items": []}
    rt = PS.rates(a.archive)
    for it in rep["items"]:
        d = {"item": it["item"], "qty": int(round(it["qty"])),
             "packing": it["packing"],
             "pack_size": int(PM.pack_size(it["packing"]) or 1)}
        if it["item"] in rt:
            d["rate_p"] = rt[it["item"]]
        body["items"].append(d)

    if a.dry_run:
        print("dry run -- nothing sent")
        return 0
    tok, where = PS.read_token()
    if not tok:
        print("no token available (share or cache) -- nothing sent")
        return 2
    try:
        out = send(a.url, body, tok)
    except urllib.error.HTTPError as e:
        print("server said %s -- nothing recorded" % e.code)
        return 1
    except Exception as e:                                     # noqa: BLE001
        print("could not reach the server (%s) -- nothing recorded"
              % e.__class__.__name__)
        return 2
    print("sent (token from %s): %d items, %d difference(s) closed by themselves"
          % (where, out.get("items", 0), out.get("reconciled", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
