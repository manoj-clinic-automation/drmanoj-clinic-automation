#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s452.py -- kit S452_AMIR_PANEL_FIXES: the data step, run AFTER the files are placed (and, in the walk, on a scratch copy).

  1. amir.vouchers_per_visit becomes 12 -- only if the row still reads 5 (a figure the owner set is never moved); made at 12 if missing;
     the additive table stock_rate_marg (Marg's own S.RATE / MRP of the rate list, which DUTY_MAP's amir.rate_entry reads);
  2. a NEW reception-phone key (supplier_msg.s452_new_token): the old one was readable by a staff login, so it answers 401 from now.
     The key is never printed -- only its length;
  3. the figures: Amir's bill list (listed / held, stamps and reasons), the NEFT line he sees for each recent month, the rate items due,
     where the count stands -- stamps, supplier names and counts only.

    apply_s452.py --finance DIR --db PATH [--settings-only | --figures-only]
"""
import argparse
import os
import re
import sqlite3
import sys


def settings(con):
    r = con.execute("SELECT value FROM setting WHERE key='amir.vouchers_per_visit'").fetchone()
    note = "S446 D649 / S452 (the owner, 02-Oct): medicine/consumable vouchers released to Amir per visit (Stage C); more on request"
    if r is None:
        con.execute("INSERT INTO setting (key, value, note) VALUES ('amir.vouchers_per_visit', '12', ?)", (note,))
        how = "made at 12"
    elif str(r[0]).strip() == "5":
        con.execute("UPDATE setting SET value='12', note=? WHERE key='amir.vouchers_per_visit' AND value='5'", (note,))
        how = "5 -> 12"
    else:
        how = "kept at %s (not 5: a figure set by hand)" % r[0]
    # the mirror of Marg's own S.RATE / MRP for the rate list (stock_app.S452_RATE_DDL, the same text): DUTY_MAP's amir.rate_entry reads it
    con.execute("CREATE TABLE IF NOT EXISTS stock_rate_marg (item TEXT PRIMARY KEY, s_rate TEXT, mrp TEXT, as_on TEXT, seen_at TEXT NOT NULL)")
    con.commit()
    print("S452 setting amir.vouchers_per_visit: %s; table stock_rate_marg ready" % how)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--settings-only", action="store_true")
    ap.add_argument("--figures-only", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, a.finance)
    os.chdir(a.finance)
    os.environ.setdefault("FINANCE_DB", a.db)
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    if not a.figures_only:
        settings(con)
        if a.settings_only:
            con.close()
            print("S452 apply done (settings only)")
            return 0
        import supplier_msg                                           # noqa: E402 -- the PLACED file (or the walk's copy)
        n = supplier_msg.s452_new_token(con)
        print("S452 reception phone: a new key made (%d characters, not shown); the old key answers 401 from now" % n)
    import amir_day                                                   # noqa: E402
    import purchase_app                                               # noqa: E402
    import stock_app                                                  # noqa: E402
    import supplier_msg                                               # noqa: E402,F811
    purchase_app._assets_db = os.environ.get("ASSETS_DB", purchase_app._assets_db)   # init() is not run here: the asset store's path
    r = purchase_app.scans_for_amir(con)
    print("Amir's step 2: %d bill(s) to put into Marg, %d held for reception" % (len(r["list"]), len(r["held"])))
    for x in r["list"]:
        print("   to enter  %s · %s · scan %s · %s · file %s" % (x["stamp"], x["supplier"], x["scan_ddmm"], ("bill " + x["bill_date"]) if x["bill_date"] else "bill date not clear", x["name"]))
    for x in r["held"]:
        print("   held      %s · %s · read as '%s'" % (x["stamp"], x["held"], re.sub(r"\s+", " ", x["read_vendor"])[:40]))
    for m in sorted({row[0] for row in con.execute("SELECT month FROM purchase_neft_event WHERE kind<>'rejected'")}, reverse=True)[:3]:
        c = supplier_msg.s452_neft_confirmed(con, m)
        print("NEFT %s for Amir: %s" % (m, supplier_msg.s452_amir_line(c) if c else "nothing (not confirmed)"))
    rt = stock_app.amir_rate_due(con)
    print("Rate daalo on his card: %d item(s)%s" % (len(rt), (" -- " + ", ".join(t["item"] for t in rt)) if rt else ""))
    st = stock_app.amir_stage(con)
    if st:
        C = st.get("C") or {}
        print("Count #%d: stage %s%s" % (st["count_id"], st["stage"], (" · Stage C %d/%d entered, %d released, %d verified" % (
            C.get("entered", 0), C.get("total", 0), C.get("released", 0), C.get("verified", 0))) if st["stage"] == "C" else ""))
    w = amir_day._work(con, amir_day._today())
    card = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", amir_day._s446_card(w, True))).replace("&mdash;", "--").replace("&#10003;", "(ok)").strip()
    print("Amir's card: %s" % (card or "(nothing open)"))
    con.close()
    print("S452 apply done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
