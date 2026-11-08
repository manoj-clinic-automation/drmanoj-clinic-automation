#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s755.py -- S755: what the kit would do on this box, READ ONLY (both databases opened mode=ro; readers only). Run it on the LIVE
files and on the kit's and read the difference: the awaited dealers of every ended month (reception's automatic cards; the daily line's
words), the hub's 'paper matches' count (F-1188) beside row 1's heading, the ledger months before the register began (F-1189).
    python3 -B proof_s755.py <finance dir to read with> <shared dir> <finance.db> <assets.db>
One last line:
    PROOF S755: ended months <n> · awaited <n> · automatic cards <n> · owner asks <n> · daily line <yes|no> · F-1188 <match/heading> · settled months <n>
Dealer names, months and counts only -- no phone number, no patient detail, no key."""
import datetime as dt
import os
import sqlite3
import sys
import traceback


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        print("PROOF S755: ERROR usage")
        return 2
    code, shared, db, adb = (os.path.abspath(x) for x in sys.argv[1:5])
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
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        print("PROOF S755: ERROR the register could not be read")
        return 1
    new = hasattr(SR, "s755_awaited")
    print("S755 proof · read only · %s files" % ("the kit's" if new else "the LIVE"))
    tm = dt.datetime.now().strftime("%Y-%m")
    months = sorted([m for m in SR.months_with_bills(con, 24) if m < tm and SR.month_class(con, m) == "counted"], reverse=True)
    n_aw, n_auto, n_own = 0, 0, 0
    asks = []
    try:
        asks = SR.s750_reception_asks(con)
    except Exception as e:                                    # noqa: BLE001
        print("  reception's asks could not be read: %s" % str(e)[:120])
    n_auto = sum(1 for a in asks if a.get("auto"))
    n_own = sum(1 for a in asks if not a.get("auto"))
    for m in months:
        try:
            ds = SR.s750_dealers(con, m)
        except Exception as e:                                # noqa: BLE001
            print("  %s: the dealers could not be read: %s" % (m, str(e)[:120]))
            continue
        aw = sorted(d["name"].title() for d in ds if d["state"] == "awaited")
        n_aw += len(aw)
        auto_m = sorted(a["name"].title() for a in asks if a.get("auto") and a["month"] == m)
        own_m = sorted(a["name"].title() for a in asks if not a.get("auto") and a["month"] == m)
        print("  %s · %d dealer(s) · awaited %d: %s" % (m, len(ds), len(aw), ", ".join(aw) or "none"))
        print("     reception's cards by themselves: %s" % (", ".join(auto_m) or ("none (not built)" if not new else "none")))
        if own_m:
            print("     the owner's own asks: %s" % ", ".join(own_m))
        try:
            r = SR.register(con, m)
            c = r.get("counts") or {}
            mo = SR.s749_month_open(con, m, r)
            head = c.get("verified", 0) + c.get("has_scan", 0) + c.get("accepted", 0) + c.get("confirmed", 0)
            print("     F-1188: the hub's 'paper matches' %d · row 1's heading %d / %d%s" % (mo.get("match", 0), head, r.get("total", 0), "" if mo.get("match") == head else "  <- differ"))
            f1188 = "%d/%d" % (mo.get("match", 0), head)
        except Exception as e:                                # noqa: BLE001
            print("     F-1188: could not be read: %s" % str(e)[:100])
            f1188 = "?"
    daily = "no"
    if new:
        try:
            import owner_notice as ON
            now = dt.datetime.now(ON.IST).replace(hour=11, minute=0)
            msgs = ON._part_summaries(con, now)
            for m in msgs:
                print("  the daily line (as it would read at 11:00 today): %s -- %s" % (m["title"], m["body"][:160]))
            daily = "yes (%d)" % len(msgs) if msgs else "no (nothing awaited)"
        except Exception as e:                                # noqa: BLE001
            print("  the daily line could not be read: %s" % str(e)[:120])
            daily = "error"
    n_set = 0
    try:
        rf = str(SR.setting(con, "purchase.register_from", "2026-10-01"))[:7]
        keys = [str(r[0]) for r in con.execute("SELECT DISTINCT supplier_norm FROM purchase_bill WHERE supplier_norm IS NOT NULL AND COALESCE(month, substr(bill_date,1,7)) < ? ORDER BY 1", (rf,))]
        for k in keys:
            L = PA.s750_ledger(con, k)
            for mo in L.get("months") or []:
                if mo["month"] < rf:
                    n_set += 1 if mo.get("settled") else 0
        print("  F-1189: %d dealer(s) with bills before %s; %d ledger month(s) read 'settled outside the system'%s" % (len(keys), rf, n_set, "" if new else " (LIVE: not built)"))
    except Exception as e:                                    # noqa: BLE001
        print("  F-1189: could not be read: %s" % str(e)[:120])
    print("PROOF S755: ended months %d · awaited %d · automatic cards %d · owner asks %d · daily line %s · F-1188 %s · settled months %d"
          % (len(months), n_aw, n_auto, n_own, daily, f1188 if months else "-", n_set))
    return 0


if __name__ == "__main__":
    sys.exit(main())
