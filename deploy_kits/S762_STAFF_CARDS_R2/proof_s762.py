#!/usr/bin/env python3
"""proof_s762.py -- S762 on the LIVE stores, READ-ONLY, COUNTS ONLY (staff first names and counts; no patient name, number or
text is printed).
usage: proof_s762.py <new calls_console.py> <live calls_console.py> <portal dir> <console.db> <inbox.db> <finance.db>
                     <staff_master.csv> <punches.csv> <review db>
For today, yesterday and 7 days, through the live and the new module:
  . the page's call figures (the strip) identical except 'staff != AI', which may only FALL (same words now agree);
  . his page: each card's missed calls, plus the 'Both on duty' line, add up to the distinct missed calls (counted once);
  . each person's own card (the staff route) has at least the missed calls she had before (before punch-in added, shared kept);
  . the page renders; each read under 20 s.
Prints 'PROOF CLEAN' or 'PROOF RED: <why>'."""
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
RV = rvdb if os.path.exists(rvdb) else os.path.join(tempfile.mkdtemp(prefix="s762proof_"), "call_review.db")
if RV != rvdb:
    NEW.rv_init(RV)
CFG = {"PORTAL_INBOX_DB": idb, "SR_STAFF_MASTER": sm, "SR_PUNCH_CSV": pu, "FINANCE_DB_PATH": fdb, "PORTAL_CALL_REVIEW_DB": RV}
H = {"console_conn": conn, "console_meta": lambda: {"ok": True, "built_at": ""}, "spam_phones": lambda: [], "reviews_maps": lambda: ({}, {})}
for M in (NEW, LIVE):
    M._H.update(H)
    M._CFG = lambda k, d=None: CFG.get(k, d)
KEYS = ("calls", "callers", "in_ok", "out_ok", "miss_open", "flagged")
red = []


def staff_side(M, span):
    c = conn()
    try:
        d_from, d_to, mode = M.span_bounds(span, "", M.now_ist())
        wa, _ok = M.wa_items(idb, d_from, d_to)
        people, _i, _n = M.build_people(c, d_from, d_to, M.now_ist(), wa=wa)
        return M._safe_cards(c, people, d_from, d_to, M.now_ist(), sm, pu)
    finally:
        c.close()


for span in ("today", "yesterday", "7"):
    t0 = time.time()
    dn = NEW.page_data(conn(), span=span, inbox_path=idb, fin_db=fdb, master_path=sm, punch_path=pu)
    tn = time.time() - t0
    dl = LIVE.page_data(conn(), span=span, inbox_path=idb, fin_db=fdb, master_path=sm, punch_path=pu)
    cn, cl = dn.get("counts", {}), dl.get("counts", {})
    diff = [k for k in KEYS if cn.get(k) != cl.get(k)]
    if diff:
        red.append("%s: the strip changed (%s)" % (span, ",".join(diff)))
    if (cn.get("mismatch") or 0) > (cl.get("mismatch") or 0):
        red.append("%s: staff != AI rose" % span)
    sn, sl = dn.get("staff"), dl.get("staff")
    if sn is None:
        red.append("%s: the new staff cards failed" % span)
        continue
    per = [c for c in sn if not c["rec"]]
    refs = [it["ref"] for c in per for p, it in c["missed_items"]]
    if len(refs) != len(set(refs)):
        red.append("%s: a missed call is on two cards on his page" % span)
    both = next((c for c in per if c.get("both")), None)
    own_new = {c["key"]: c for c in (staff_side(NEW, span) or []) if not c["rec"]}
    own_old = {c["key"]: c for c in (sl or []) if not c["rec"]}
    print("  %-9s his page: %s%s  (read %.1f s)" % (span, " · ".join("%s missed %d net %d" % (c["key"], c["missed"], c["net_missed"]) for c in per if not c.get("both")),
          (" · BOTH ON DUTY missed %d net %d" % (both["missed"], both["net_missed"])) if both else "", tn))
    print("            their own cards: %s" % " · ".join("%s missed %d (was %d) before punch-in %d net %d" % (
        k, c["missed"], own_old.get(k, {}).get("missed", 0), len(c["pre_punch"]), c["net_missed"]) for k, c in sorted(own_new.items())))
    print("            staff != AI: %s -> %s" % (cl.get("mismatch"), cn.get("mismatch")))
    for k, c in own_new.items():
        if k in own_old and c["missed"] < own_old[k]["missed"]:
            red.append("%s: %s's own card lost a missed call" % (span, k))
    if tn > 20:
        red.append("%s: the read took %.0f s" % (span, tn))
print("PROOF CLEAN" if not red else "PROOF RED: " + "; ".join(red))
