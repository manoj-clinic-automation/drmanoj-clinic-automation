#!/usr/bin/env python3
"""proof_s817.py -- S817 on the LIVE stores, READ-ONLY, COUNTS ONLY (no patient name, number or text is printed).
usage: proof_s817.py <new calls_console.py> <live calls_console.py> <portal dir> <console.db> <inbox.db> <finance.db>
                     <staff_master.csv> <punches.csv> <review db>
The follow-up list through the live and the new page, at the same minute:
  . the new list is never longer; the rows that leave it are exactly the ones this kit's rules close (a visit before the
    due date by D893, or a clinic ID written '12.0' meeting '12');
  . 'called' can only fall (calls on or before the due day no longer count in Grace and older);
  . who called today is the same; today's line -- due, called, reached -- is the same and only 'came' may rise; the
    strip, the people and the staff cards are the same;
  . the new page renders on the live rows; each read under 20 s.
Prints the sections' figures, then 'PROOF CLEAN' or 'PROOF RED: <why>'. (A reading that lands between the two reads can
differ by itself, so a red is tried once more before it is said.)"""
import importlib.util
import os
import sqlite3
import sys
import tempfile
import time

new_p, live_p, pdir, cdb, idb, fdb, sm, pu, rvdb = sys.argv[1:10]
sys.path.insert(0, pdir)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def conn():
    c = sqlite3.connect("file:%s?mode=ro" % cdb, uri=True, timeout=10)
    c.row_factory = sqlite3.Row
    return c


NEW, LIVE = load("cc_new", new_p), load("cc_live", live_p)
RV = rvdb if os.path.exists(rvdb) else os.path.join(tempfile.mkdtemp(prefix="s817proof_"), "call_review.db")
if RV != rvdb:
    NEW.rv_init(RV)
CFG = {"PORTAL_INBOX_DB": idb, "SR_STAFF_MASTER": sm, "SR_PUNCH_CSV": pu, "FINANCE_DB_PATH": fdb, "PORTAL_CALL_REVIEW_DB": RV}
from flask import Flask   # noqa: E402
APP = Flask("s817proof")
NEW.register(APP, lambda f: f, lambda: "manoj", lambda k, d=None: CFG.get(k, d),
             {"console_conn": conn, "console_meta": lambda: {"ok": True, "built_at": ""}, "spam_phones": lambda: [], "reviews_maps": lambda: ({}, {})})
LIVE._H.update({"console_conn": conn, "console_meta": lambda: {"ok": True, "built_at": ""}, "spam_phones": lambda: [], "reviews_maps": lambda: ({}, {})})
LIVE._CFG = lambda k, d=None: CFG.get(k, d)


def staff_key(d):
    return [(c["key"], c["answered"], c["rung"], c["missed"], c["made"], c.get("net_missed"), len(c["not_logged"]), len(c["mismatch"]))
            for c in (d.get("staff") or [])]


def once(say):
    red = []
    now = NEW.now_ist()
    c = conn()
    try:
        t0 = time.time()
        dn = NEW.page_data(c, span="today", now=now, inbox_path=idb, fin_db=fdb, master_path=sm, punch_path=pu)
        tn = time.time() - t0
        dl = LIVE.page_data(c, span="today", now=now, inbox_path=idb, fin_db=fdb, master_path=sm, punch_path=pu)
        with APP.test_request_context("/portal/console"):
            html = NEW.render(c, {}, now=now)
    finally:
        c.close()
    fn, fo = dn["fu"], dl["fu"]
    if fn["found"] != fo["found"]:
        red.append("the feed reads %s on the new page and %s on the live one" % (fn["found"], fo["found"]))
    if not fn["found"]:
        if say:
            print("  the follow-up feed is not readable just now on either page -- nothing to compare")
    else:
        old = {b[0]: b for b in fo["bands"]}
        for k, title, sub, rows, n, called, reached, tone in fn["bands"]:
            L = fn["fl"][k]
            if say:
                print("  %-8s %3d %s (was %3d) · called today %d · reached today %d · earlier days %d called, %d reached · "
                      "'called' by the old count %d, now %d" % (k, n, "patients" if k == "today" else "not visited", old[k][4],
                                                               L["ct"], L["rt"], L["ec"], L["er"], old[k][5], called))
        if say:
            print("  advised period read for %d of the list's rows (dx_visit %s) · rows this kit takes off the list: %d (%d by a visit "
                  "before the due date) · visits %s" % (fn["advised"], "read" if fn["advice_ok"] else "NOT readable -- the old rule for every row",
                                                        fn["dropped"], fn["early"], "read" if fn["visits_ok"] else "not read in full"))
            print("  today's line: due %d · called %d · reached %d (the same on both) · came %d (was %d)" % (
                fn["today"].get("due", 0), fn["today"].get("called", 0), fn["today"].get("reached", 0), fn["today"].get("came", 0), fo["today"].get("came", 0)))
        if fn["open"] > fo["open"]:
            red.append("the new list is longer (%d open, was %d)" % (fn["open"], fo["open"]))
        if fo["open"] - fn["open"] != fn["dropped"]:
            red.append("%d rows left the list but %d were closed by this kit's rules" % (fo["open"] - fn["open"], fn["dropped"]))
        if sum(b[5] for b in fn["bands"]) > sum(b[5] for b in fo["bands"]):
            red.append("'called' rose")
        if fn["who"] != fo["who"]:
            red.append("who called today changed")
        if any(fn["today"].get(k) != fo["today"].get(k) for k in ("due", "called", "reached")):
            red.append("today's line changed (due / called / reached)")
        if (fn["today"].get("came") or 0) < (fo["today"].get("came") or 0):
            red.append("'came' on today's line fell")
        if 'id="fu-grace"' not in html or "Called today" not in html:
            red.append("the new page did not draw the follow-up lines")
    if dn["counts"] != dl["counts"] or dn["chips"] != dl["chips"]:
        red.append("the strip or the people changed")
    if staff_key(dn) != staff_key(dl):
        red.append("the staff cards changed")
    if not html.rstrip().endswith("</body></html>"):
        red.append("the new page did not render whole")
    if tn > 20:
        red.append("the read took %.0f s" % tn)
    if say:
        print("  the strip, the people and %d staff cards: the same on both · the page drawn (%d KB) · read %.1f s" % (
            len(staff_key(dn)), len(html) // 1024, tn))
    return red


try:
    RED = once(True)
    if RED:
        time.sleep(20)
        RED = once(False)
except Exception as e:
    RED = ["%s: %s" % (type(e).__name__, str(e)[:100])]
print("PROOF CLEAN" if not RED else "PROOF RED: " + "; ".join(RED))
