#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s750.py -- S750: the dealers of every counted month as the kit judges them on this box's own databases, READ ONLY (both opened
mode=ro; only readers are called: s750_summary_scans, s750_dealers, s750_open, s749_month_open, _lock_gate, _pay_rows, s750_ledger).
Run it on the LIVE files and on the kit's files and read the difference -- what row 7 will say, what the lock will hold, which dealers the
sheet's new column shows, and that no payable changes until the owner answers (no summary scanned yet = nothing accepted, nothing carried).
    python3 -B proof_s750.py <finance dir to read with> <shared dir> <finance.db> <assets.db> [--brief]
One last line:
    PROOF S750: <months> counted month(s) · dealers <n> · agree <n> · differ <n> · awaited <n> · unread <n> · summaries scanned <n> · payable changed <n> · ledgers <n>
Dealer names, bill numbers, scan stamps and amounts only -- no phone number, no patient detail, no key."""
import os
import sqlite3
import sys
import time
import traceback


def rs(p):
    if p is None:
        return "-"
    p = int(p)
    return "%sRs %s%s" % ("-" if p < 0 else "", "{:,}".format(abs(p) // 100), (".%02d" % (abs(p) % 100)) if abs(p) % 100 else "")


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        print("PROOF S750: ERROR usage")
        return 2
    code, shared, db, adb = (os.path.abspath(x) for x in sys.argv[1:5])
    brief = "--brief" in sys.argv
    sys.path.insert(0, shared)
    sys.path.insert(0, code)
    os.environ["SHARED_LIB_DIR"] = shared
    import warnings
    warnings.simplefilter("ignore")
    try:
        import purchase_app as PA
        PA._assets_db = adb
        import scan_register as SR
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
        con.row_factory = sqlite3.Row
        months = sorted(m for m in SR.months_with_bills(con, 24) if SR.month_class(con, m) == "counted")
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        print("PROOF S750: ERROR the register could not be read")
        return 1
    new = hasattr(SR, "s750_dealers")
    print("S750 proof · read only · %s files · counted months: %s" % ("the kit's" if new else "the LIVE", ", ".join(months) or "none"))
    if not new:
        for m in months:
            try:
                n = SR.s749_month_open(con, m)
                s = PA._month_summary(con, m)
                g = PA._lock_gate(con, m, s)
                print("  %s · %s · open %d · lock %s (%d reason(s))" % (m, n.get("words"), n.get("open", 0), "OPEN" if g[0] else "held", len(g[1])))
            except Exception as e:                            # noqa: BLE001
                print("  %s · could not be read: %s" % (m, str(e)[:120]))
        print("  row 7 'Dealer summaries': later (not built) · no summary read · the sheet has no dealer column · no ledger")
        print("PROOF S750: %d counted month(s) · dealers 0 · agree 0 · differ 0 · awaited 0 · unread 0 · summaries scanned 0 · payable changed 0 · ledgers 0 (LIVE files: not built)" % len(months))
        return 0
    try:
        scans = SR.s750_summary_scans(con)
    except Exception as e:                                    # noqa: BLE001
        scans = None
        print("  summary scans: could not be read (%s)" % str(e)[:120])
    print("  summary scans (kind 'Summary' in assets.db): %s" % ("assets.db not reachable" if scans is None else "%d -- %s" % (len(scans), ", ".join(
        "%s %s %s %s" % (s.get("stamp_no") or ("#%d" % sid), s.get("month") or "?", "read" if s.get("read") else "unread", rs(s.get("figure_p"))) for sid, s in sorted(scans.items())) or "none")))
    tot = dict(dealers=0, agree=0, differ=0, awaited=0, unread=0, changed=0, ledgers=0)
    t_all = 0.0
    for m in months:
        try:
            t0 = time.time()
            ds = SR.s750_dealers(con, m)
            op = SR.s750_open(con, m)
            n = SR.s749_month_open(con, m)
            s = PA._month_summary(con, m)
            gate = PA._lock_gate(con, m, s)
            _s, groups = PA._pay_rows(con, m)
            took = time.time() - t0
            t_all += took
        except Exception:                                     # noqa: BLE001
            print("  %s · could not be read:\n%s" % (m, traceback.format_exc()[-900:]))
            continue
        changed = [g for g in groups if (g.get("s750") or {}).get("payable_p") is not None and int(g["payable_p"]) != int(g["total_p"]) + int(g.get("carry_p") or 0)]
        auto = [g for g in groups if g.get("s750_carry_auto")]
        print("  %s · %d dealer(s) · %s · open %d (register %d + dealers %d) · lock %s · payable changed by the kit: %d · carried in by the kit: %d · %.1fs"
              % (m, len(ds), op.get("words") or "-", n.get("open", 0), n.get("open", 0) - n.get("dealers", 0), n.get("dealers", 0), "OPEN" if gate[0] else "held", len(changed), len(auto), took))
        for d in ds:
            if brief and d["state"] in ("awaited", "none", "confirm", "agrees"):
                continue
            a = d.get("answer") or {}
            print("     %-28s %-10s Marg %12s  summary %12s  %s%s" % (d["name"][:28], d["state"], rs(d["net_p"]), rs((d.get("summary") or {}).get("figure_p")), d["words"][:90],
                                                                    (" · answered: %s" % a["kind"]) if a else ""))
            for w in d.get("why", [])[:4]:
                print("        why: %s" % w[:140])
        for x in gate[1]:
            if "dealer summar" in x:
                print("     lock: %s" % x[:160])
        tot["dealers"] += len(ds)
        tot["agree"] += op.get("agree", 0)
        tot["differ"] += op.get("differ", 0) + op.get("asked", 0)
        tot["awaited"] += op.get("awaited", 0)
        tot["unread"] += op.get("unread", 0)
        tot["changed"] += len(changed)
    try:
        keys = [str(r[0]) for r in con.execute("SELECT DISTINCT supplier_norm FROM purchase_bill WHERE supplier_norm IS NOT NULL ORDER BY 1")]
        n_led = 0
        t0 = time.time()
        for k in keys:
            L = PA.s750_ledger(con, k)
            n_led += 1 if L.get("months") else 0
        print("  ledgers: %d dealer(s) read in %.1fs (every bill's item lines, the returns, the summaries, the payments)" % (n_led, time.time() - t0))
        tot["ledgers"] = n_led
    except Exception:                                         # noqa: BLE001
        print("  ledgers: could not be read:\n%s" % traceback.format_exc()[-600:])
    print("PROOF S750: %d counted month(s) · dealers %d · agree %d · differ %d · awaited %d · unread %d · summaries scanned %d · payable changed %d · ledgers %d"
          % (len(months), tot["dealers"], tot["agree"], tot["differ"], tot["awaited"], tot["unread"], len(scans or {}), tot["changed"], tot["ledgers"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
