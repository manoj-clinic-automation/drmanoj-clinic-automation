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

    The item-wise report carries NO DATE on any row -- only supplier and bill
    number. Without the supplier-wise report there is no way to tell a purchase
    that happened after the baseline from one already inside it, and adding
    both would double-count. So a purchase file whose period reaches past the
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
             os.path.join("S205_LIVE_TOOLS", "manojz")):
    _p = os.path.join(KITS, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, HERE)

import marg_report as MR            # noqa: E402  the daily sale report
import marg_stock as MS             # noqa: E402  closing stock
import marg_purchase as MP          # noqa: E402  purchase item-wise
import purchase_returns as PR       # noqa: E402  marks return rows
import xlsx_sheet                   # noqa: E402
import packmap as PM                # noqa: E402  pack sizes, one match key
import resolve as RS                # noqa: E402  the 20-character truncation
import push_snapshot as PS          # noqa: E402  token, baseline picker, rates

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
    for p in sorted(sum([glob.glob(x) for x in pats], [])):
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
def bill_dates(archive):
    """{(supplier, bill): date} from every PURCHASE SUPPLIER WISE export.

    Layout: a header row SUPPLIER NAME | DATE | BILL NO. | CASH | CREDIT, then
    one row per bill. The supplier cell is written once and left blank on the
    following rows of the same supplier, so it is carried down. TOTAL rows are
    skipped -- they are furniture, and a furniture row read as a bill is
    exactly the fault that made a page header look like a salt (S207).
    """
    out, files = {}, []
    pats = [os.path.join(archive, "PURCHASE_SUPPLIERWISE", "*", "*.XLS"),
            os.path.join(archive, "PURCHASE_SUPPLIERWISE", "*", "*.xlsx")]
    for p in sorted(sum([glob.glob(x) for x in pats], [])):
        try:
            sh = xlsx_sheet.open_sheet_any(p)
        except Exception as e:                                 # noqa: BLE001
            files.append((os.path.basename(p), 0, str(e)))
            continue
        n, supplier = 0, None
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
                out[(PM.norm(supplier), bill)] = date
                n += 1
        files.append((os.path.basename(p), n, "ok"))
    return out, files


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


def purchases_after(archive, after):
    """Dated purchase rows after the baseline. Refuses what it cannot date.

    A purchase file whose period ends on or before the baseline is SKIPPED
    whole -- everything in it is already inside the baseline figure, and
    adding it would count those goods twice. A file that reaches past the
    baseline must have every one of its bills datable, or the run refuses:
    an undated purchase is either double-counted or lost, and there is no
    third option.
    """
    dates, dfiles = bill_dates(archive)
    rows, used, skipped, undated = [], [], [], []
    pats = [os.path.join(archive, "PURCHASE_ITEMWISE", "*", "*.XLS"),
            os.path.join(archive, "PURCHASE_ITEMWISE", "*", "*.xlsx")]
    horizon = None
    for p in sorted(sum([glob.glob(x) for x in pats], [])):
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
            r["_date"] = d
            rows.append(r)
            n += 1
        used.append((os.path.basename(p), n, ddmmyyyy(end)))
        horizon = end if horizon is None or end > horizon else horizon
    return rows, horizon, used, skipped, undated, dfiles


def _period_end(period):
    """A period reads like '2026-08-01 to 2026-08-26' or a pair. Take the end."""
    if isinstance(period, (list, tuple)) and len(period) == 2:
        return dkey(period[1])
    s = str(period or "")
    found = [dkey(t) for t in s.replace("_", " ").replace("to", " ").split()]
    found = [d for d in found if d]
    return max(found) if found else None


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

    pur, horizon, pused, pskipped, undated, dfiles = purchases_after(archive, B)
    if undated:
        return {"error": "%d purchase line(s) could not be dated -- the "
                         "SUPPLIER WISE export for the same range is missing "
                         "or does not cover them. Nothing sent." % len(undated),
                "undated": undated[:10]}

    sale, sdays, sskipped = sales_after(archive, B, upto)
    if not sdays:
        return {"error": "no sale report dated after the baseline (%s). "
                         "Nothing to compute." % ddmmyyyy(B), "empty": True}
    last_sale = max(sdays)
    as_on = last_sale if upto is None else min(last_sale, upto)

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

    branch = collections.Counter()
    blocked = set(ambiguous) | set(unresolved)
    blocked_names = collections.Counter()
    sold_lines = 0
    for ln in sale:
        k = ln.get("_key")
        if not k:
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
            "rejected": rejected, "as_on": as_on, "sale_days": sdays,
            "sale_lines": len(sale), "sold_lines": sold_lines,
            "purchase_rows": len(pur), "purchase_horizon": horizon,
            "purchase_files": pused, "purchase_skipped": pskipped,
            "sale_skipped": sskipped, "supplierwise_files": dfiles,
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
              "Get the two purchase exports for the range and run again.")
    if rep["blocked_names"]:
        print("  %d sale line(s) could not be tied to an item -- their units are "
              "NOT subtracted:" % sum(n for _, n in rep["blocked_names"]))
        for nm, n in rep["blocked_names"][:8]:
            print("     %-30s %d line(s)" % (str(nm)[:30], n))
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
