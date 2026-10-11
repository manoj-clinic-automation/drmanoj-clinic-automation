#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_s528.py -- kit S528_AMIR_PAGE: the install-day state (charter 7), printed by the installer before and after placing, and the
read-back of the live board through the app after the restart.

    FINANCE_DB=/root/finance/finance.db python3 -B state_s528.py --finance /root/finance --mode state
    FINANCE_DB=... FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR=<scratch> python3 -B state_s528.py --finance /root/finance --mode readback

  state     the stage (A/B/C/done, open/entered/total/pending, the proof's state and reason), the 23 rename rows' states by old_name, the
            pending orthotic line(s), the exact card words Amir sees (the new file) or the old card's words (the old file). Reads the live
            database; amir_stage may write its once-only stage events (printed before/after, as S524's read-back did).
  readback  the board as the owner and as amir (header auth, a scratch SSO dir), the hub's step 7, Amir's step 6, the stage events before/after.
No person, phone or account number is printed."""
import argparse
import html as _html
import os
import re
import sqlite3
import sys
import time


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--mode", default="state")
    a = ap.parse_args()
    sys.path.insert(0, a.finance)
    os.chdir(a.finance)
    import finance_app as fa                                    # noqa: E402
    import stock_app as SA                                      # noqa: E402
    import item_alias as IA                                     # noqa: E402
    DB = os.environ.get("FINANCE_DB") or os.path.join(a.finance, "finance.db")
    con = sqlite3.connect(DB, timeout=60)
    con.row_factory = sqlite3.Row
    root = SA._s446_root(con)
    NEW = hasattr(SA, "_s521_stage_words")
    ev0 = [tuple(r) for r in con.execute("SELECT stage, event, ref, at, detail FROM stock_stage_event WHERE count_id=? ORDER BY id", (root,))]
    if a.mode == "state":
        st = SA.amir_stage(con, root)
        A = (st or {}).get("A") or {}
        pr = A.get("proof") or {}
        print("STATE: count #%s stage %s; A open %s, entered %s of %s, pending %s; proof %s%s%s; renames_visible %s; B %s"
              % (root, (st or {}).get("stage"), A.get("open"), A.get("entered"), A.get("total"), A.get("pending"), pr.get("state"),
                 (" why " + str(pr.get("why"))) if pr.get("why") else "", (" as_after " + str(pr.get("as_after"))) if pr.get("as_after") else "",
                 (st or {}).get("renames_visible"), {k: v for k, v in ((st or {}).get("B") or {}).items() if k in ("total", "verified", "ticked", "questions", "open", "old")}))
        try:
            d = SA._report_cached(con, root)
            pend = SA._voucher_pending(con, d, section="Orthotics") if d else []
            print("   pending orthotic line(s): %s" % mask([(p["item"], p["change"]) for p in pend]))
        except Exception as e:                                  # noqa: BLE001
            print("   pending orthotic line(s): could not be read (%s)" % str(e)[:100])
        for r in IA.rows(con):
            q = r.get("question") if isinstance(r, dict) else None
            print("   %-9s %-31s -> %-30s %s%s" % (r["state"], r["old_name"], r["new_name"], (r.get("verified_as_on") or ""),
                                                 (" question: Marg prints '%s' (%s)" % (q.get("seen_name"), q.get("event"))) if q else ""))
        if NEW:
            sw = SA._s521_stage_words(con, st)
            print("   CARD (Amir): %s" % sw.get("card_hi"))
            print("   OWNER: %s" % sw.get("owner_en"))
            for l in sw.get("owner_lines") or []:
                print("   OWNER LINE: %s" % mask(l.get("text")))
        else:
            import amir_day as AD                               # noqa: E402
            card = AD._s446_card(dict(s446=dict(stage=st)))
            print("   OLD CARD (Amir): %s" % " | ".join(x for x in [_html.unescape(t).strip() for t in re.findall(r">([^<]{3,300})<", card)] if x))
        ev1 = [tuple(r) for r in con.execute("SELECT stage, event, ref, at, detail FROM stock_stage_event WHERE count_id=? ORDER BY id", (root,))]
        print("   stage events of count %s: %d before the read, %d after%s" % (root, len(ev0), len(ev1), (" -- NEW: %s" % ev1[len(ev0):]) if len(ev1) > len(ev0) else " (none written)"))
        print("STATE OK")
        return 0
    # readback
    c = fa.app.test_client()
    for who, role in (("manoj", "doctor"), ("amir", "staff")):
        t0 = time.perf_counter()
        r = c.get("/finance/stock/api/pad/amir/%d" % root, headers={"X-Clinic-User": who, "X-Clinic-Role": role})
        ms = int((time.perf_counter() - t0) * 1000)
        raw = r.get_data(as_text=True)
        j = r.get_json(silent=True) or {}
        rn = j.get("renames") or {}
        print("as %s: board %s in %d ms, %d bytes; stage %s; proof %r; vouchers listed %d (%d with a take-back button); renames ready %r, rows %d, questions %d, done_hi %r"
              % (who, r.status_code, ms, len(raw.encode("utf-8")), (j.get("stage") or {}).get("stage") if isinstance(j.get("stage"), dict) else None, j.get("proof"),
                 len(j.get("vouchers") or []), sum(1 for v in (j.get("vouchers") or []) if v.get("can_clear")), rn.get("ready"), len(rn.get("rows") or []), len(rn.get("questions") or []), rn.get("done_hi")))
        if who == "manoj":
            for q in rn.get("questions") or []:
                print("   question: %s -> %s: Marg prints %r (%s)" % (q.get("old_name"), q.get("new_name"), q.get("seen_name"), q.get("event")))
        r = c.get("/finance/stock/page/amir?count=%d" % root, headers={"X-Clinic-User": who, "X-Clinic-Role": role})
        h = r.get_data(as_text=True)
        print("   page as %s: %s; file input %s; Wapas in page %s" % (who, r.status_code, 'type="file"' in h, "Wapas" in h))
    r = c.get("/finance/stock/api/pad/hub/%d" % root, headers={"X-Clinic-User": "manoj", "X-Clinic-Role": "doctor"})
    j = r.get_json(silent=True) or {}
    P = j.get("proof") or {}
    print("hub step 7 as the owner: %s; state %r; text %r; rows %s; lines %s" % (r.status_code, P.get("state"), P.get("text"), mask([(x.get("item"), x.get("why")) for x in (P.get("rows") or [])][:6]), mask([x.get("text") for x in (P.get("lines") or [])][:6])))
    r = c.get("/finance/amir/step/6", headers={"X-Clinic-User": "amir", "X-Clinic-Role": "staff"})
    h = r.get_data(as_text=True)
    tx = [re.sub(r"\s+", " ", _html.unescape(x)).strip() for x in re.findall(r">([^<]{3,300})<", h)]
    print("amir's step 6: %s; card lines: %s" % (r.status_code, mask([x for x in tx if x.startswith(("Orthotic", "Naam", "Dawa", "Stock ke", "Marg sudhar"))][:6])))
    r = c.get("/finance/sanjeevni/api/needs-you", headers={"X-Clinic-User": "manoj", "X-Clinic-Role": "doctor"})
    j = r.get_json(silent=True) or {}
    print("Needs-you stock lines: %s" % mask([l.get("text") for l in (j.get("lines") or []) if l.get("target") == "stock"][:6]))
    ev1 = [tuple(r) for r in con.execute("SELECT stage, event, ref, at, detail FROM stock_stage_event WHERE count_id=? ORDER BY id", (root,))]
    print("stage events of count %s: %d before the read, %d after%s" % (root, len(ev0), len(ev1), (" -- NEW: %s" % ev1[len(ev0):]) if len(ev1) > len(ev0) else " (none written)"))
    print("READ_BACK OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
