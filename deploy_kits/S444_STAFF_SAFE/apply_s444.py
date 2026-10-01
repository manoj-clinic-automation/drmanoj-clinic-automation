#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s444.py -- kit S444_STAFF_SAFE: the data step, run AFTER the files are placed (and, in the walk, on a scratch copy).

  1. the four settings the owner's lines read (INSERT OR IGNORE -- a value already set is never moved);
  2. KEDAR 195 (27-Sep), the owner's ruling of 01-Oct: Amir's own entry, corrected in Marg -- claim #1 settled
     ('amir_own_entry', by "S444 rule", audited), the bill's answer becomes 'self' and it waits for the next export that
     shows the paper's amount. Found BY KEY (supplier, bill number, bill date), never by counting; idempotent;
  3. the figures: what Amir sees on opening his day (the Marg sudhar card), KEDAR 195's state, the salt list's state,
     and the owner's Needs-you lines from this kit -- counts, suppliers and bill numbers only.

    apply_s444.py --finance DIR --db PATH [--figures-only]
"""
import argparse
import json
import os
import re
import sqlite3
import sys

KEY = ("KEDAR PHARMACEUTICAL", "195", "2026-09-27")
WHO = "S444 rule"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--figures-only", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, a.finance)
    os.chdir(a.finance)
    os.environ.setdefault("FINANCE_DB", a.db)
    import amir_day                                                   # noqa: E402 -- the PLACED file (or the walk's copy)
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    amir_day._ensure(con)
    amir_day._s444_ensure(con)
    if not a.figures_only:
        n = amir_day.s444_seed_settings(con)
        d = con.execute("SELECT reason, by_user FROM amir_bill_disposition WHERE supplier_norm=? AND bill_no=? AND bill_date=?", KEY).fetchone()
        if d is None:
            print("S444 rule: KEDAR 195 has no answer on the box -- nothing to change")
        elif d["reason"] == "self":
            print("S444 rule: KEDAR 195 already waits as 'self' -- nothing to change")
        elif d["reason"] == "ok":
            print("S444 rule: KEDAR 195 was already marked Theek hai by %s -- left as it is" % d["by_user"])
        else:
            con.execute("UPDATE amir_bill_disposition SET reason='self', by_user=?, at=? WHERE supplier_norm=? AND bill_no=? AND bill_date=?",
                        (WHO, amir_day._stamp()) + KEY)
            k = amir_day.s444_mark_self(con, KEY[0], KEY[1], KEY[2], "S444 rule (owner, 01-Oct: Amir's own entry)", settled_by=WHO)
            print("S444 rule: KEDAR 195 -- answer '%s' -> 'self'; %d claim(s) settled as amir_own_entry by %s" % (d["reason"], k, WHO))
        con.commit()
        print("S444 settings: %d added (%s)" % (n, ", ".join("%s=%s" % (r[0], r[1]) for r in con.execute(
            "SELECT key, value FROM setting WHERE key IN ('amir.salt_owed_days','amir.self_exports','amir.claim_open_days','amir.voucher_visits') ORDER BY key"))))
    # ---- the figures
    w = amir_day._work(con, amir_day._today())
    card = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", amir_day._s444_card(w))).replace("&mdash;", "--").replace("&middot;", "·").strip()
    print("Amir's Marg sudhar card: %s" % (card or "(nothing open -- no card)"))
    for c in (w.get("s444") or {}).get("counts") or []:
        print("   count #%d: %d vouchers made, %d open (%d orthotic, %d dawa; %d ISSUE, %d RECEIVE)" % (
            c["count_id"], c["made"], c["open"], c["ortho"], c["dawa"], c["issue"], c["receive"]))
    rn = (w.get("s444") or {}).get("renames")
    print("   renames: %s" % ("not shown -- vouchers still open on the count" if rn is None else ("%d to make (proof green)" % rn["open"] if rn.get("ready") else "not shown -- the proof is not green")))
    s = (w.get("s444") or {}).get("salt") or {}
    print("Salt list: %s" % (("OWED -- %d ticks newer than the last verified list (%s), %d day(s)" % (s["ticks"], s.get("last_list") or "none", s.get("days") or 0))
                            if s.get("pending") else "not owed -- the last verified list (%s) is newer than every salt tick" % (s.get("last_list") or "none")))
    cl = con.execute("SELECT id, state, settled_outcome, settled_by FROM amir_claim WHERE supplier_norm=? AND bill_no=? AND bill_date=?", KEY).fetchall()
    dd = con.execute("SELECT reason, by_user FROM amir_bill_disposition WHERE supplier_norm=? AND bill_no=? AND bill_date=?", KEY).fetchone()
    ww = con.execute("SELECT marg_p, paper_p, paper_src, export_md5, cleared_at FROM amir_self_wait WHERE supplier_norm=? AND bill_no=? AND bill_date=?", KEY).fetchone()
    print("KEDAR 195: answer %s · claims %s · waiting %s" % (
        ("%s (%s)" % (dd["reason"], dd["by_user"])) if dd else "-",
        ", ".join("#%d %s %s by %s" % (r["id"], r["state"], r["settled_outcome"] or "", r["settled_by"] or "-") for r in cl) or "none",
        ("Marg Rs %s, paper Rs %s (%s), cleared %s" % (amir_day._s444_rs(ww["marg_p"]), amir_day._s444_rs(ww["paper_p"]), ww["paper_src"], ww["cleared_at"] or "not yet")) if ww else "-"))
    lines = amir_day.needs_you_lines(con)
    print("Needs-you lines from S444: %d" % len(lines))
    for l in lines:
        print("   - %s" % l["text"])
    con.close()
    print("S444 apply done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
