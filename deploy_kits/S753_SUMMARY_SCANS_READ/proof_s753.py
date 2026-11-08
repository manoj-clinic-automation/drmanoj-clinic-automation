#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s753.py -- S753: every summary scan on this box as the given files read it, READ ONLY (both databases opened mode=ro; only readers
are called: s750_summary_scans, _s750_dealer_of, s750_dealers, _s446_file_bytes). Run it on the LIVE files and on the kit's and read the
difference -- for each summary: the month it counts under, the dealer it is held against, whether the viewer would open it, the bill count.
    python3 -B proof_s753.py <finance dir to read with> <shared dir> <finance.db> <assets.db> [--brief]
One last line:
    PROOF S753: summaries <n> · viewer opens <n> · month by bills <n> · dealer by bills <n> · named as the buyer <n> · unknown <n> · agree <n> · differ <n>
Dealer names, scan stamps, months and counts only -- no phone number, no patient detail, no key."""
import os
import re
import sqlite3
import sys
import traceback

US = re.compile(r"SANJ[EI]+V[AE]?N[IY]\s*MEDICO", re.I)


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        print("PROOF S753: ERROR usage")
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
        scans = SR.s750_summary_scans(con)
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        print("PROOF S753: ERROR the summaries could not be read")
        return 1
    new = hasattr(SR, "_s753_dealer_by_bills")
    print("S753 proof · read only · %s files" % ("the kit's" if new else "the LIVE"))
    if scans is None:
        print("PROOF S753: ERROR assets.db not reachable")
        return 1
    try:
        dof = SR._s750_dealer_of(con, scans)
    except Exception as e:                                    # noqa: BLE001
        print("  the dealers could not be named: %s" % str(e)[:160])
        dof = {}
    names = {str(r[0]): str(r[1] or r[0]) for r in con.execute("SELECT DISTINCT supplier_norm, supplier FROM purchase_bill WHERE supplier_norm IS NOT NULL")}
    states = {}
    for m in sorted({s.get("month") for s in scans.values() if s.get("month")}):
        try:
            for d in SR.s750_dealers(con, m):
                sid = (d.get("summary") or {}).get("id")
                if sid is not None:
                    states[int(sid)] = d.get("state")
        except Exception as e:                                # noqa: BLE001
            print("  %s: the dealers could not be read: %s" % (m, str(e)[:160]))
    n = dict(opens=0, mbb=0, dbb=0, buyer=0, unknown=0, agree=0, differ=0)
    for sid, s in sorted(scans.items()):
        try:
            got = PA._s446_file_bytes(sid, ("Pharmacy", "Summary")) if new else PA._s446_file_bytes(sid)
        except TypeError:
            got = None
        opens = got is not None
        nb = sum(1 for x in (s.get("lines") or []) if isinstance(x, dict) and x.get("kind") == "bill")
        key = dof.get(sid) or ""
        st = states.get(sid) or ("unknown" if not key else "?")
        lm = SR._s753_lines_month(s.get("lines")) if new else ""
        pt = str(((s.get("reading") or {}).get("period_to") or ""))[:7]
        by_bills = lm and lm != pt and s.get("month") == lm
        buyer = bool(US.search(str(s.get("vendor") or "")) or US.search(str((s.get("reading") or {}).get("dealer") or "")))
        n["opens"] += 1 if opens else 0
        n["mbb"] += 1 if by_bills else 0
        n["dbb"] += 1 if s.get("dealer_by_bills") else 0
        n["buyer"] += 1 if buyer else 0
        n["unknown"] += 1 if not key else 0
        n["agree"] += 1 if st == "agrees" else 0
        n["differ"] += 1 if st == "differs" else 0
        print("  %-7s %-8s %-34s %-10s %2d bill(s) %-12s viewer %s%s%s%s" % (
            s.get("stamp_no") or ("#%d" % sid), s.get("month") or "?", (names.get(key) or key or "NOBODY -- the owner picks")[:34], st, nb,
            SR.rs(s.get("figure_p")) if s.get("figure_p") is not None else "-", "opens" if opens else "404",
            " · dealer by its bills" if s.get("dealer_by_bills") else "", " · month by its bills (printed %s)" % (pt or "?") if by_bills else "",
            " · the paper names the BUYER" if buyer else ""))
    print("PROOF S753: summaries %d · viewer opens %d · month by bills %d · dealer by bills %d · named as the buyer %d · unknown %d · agree %d · differ %d"
          % (len(scans), n["opens"], n["mbb"], n["dbb"], n["buyer"], n["unknown"], n["agree"], n["differ"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
