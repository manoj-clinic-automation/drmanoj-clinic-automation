#!/usr/bin/env python3
"""proof_s744.py -- S744 on the LIVE stores, READ-ONLY, COUNTS ONLY (no name, number or text is printed).
usage: proof_s742.py <new calls_console.py> <live calls_console.py> <portal dir> <console.db> <inbox.db> [<finance.db>]
The page's data is read through the live and the new module for today, yesterday and 7 days: the CALL figures must be
identical (S742 adds WhatsApps and lists, it never changes how a call is counted); the new page must render; each read
must take under 20 s. S744: the follow-up list and Call ke baad must also be identical (the kit adds only the staff
cards); the cards are printed as counts. Prints 'PROOF CLEAN' or 'PROOF RED: <why>'."""
import importlib.util
import os
import sqlite3
import sys
import time

new_p, live_p, pdir, cdb, idb = sys.argv[1:6]
fdb = sys.argv[6] if len(sys.argv) > 6 else None
sm = sys.argv[7] if len(sys.argv) > 7 else "/root/staff_master.csv"
pu = sys.argv[8] if len(sys.argv) > 8 else "/root/punches.csv"
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
H = {"console_conn": conn, "console_meta": lambda: {"ok": True, "built_at": ""}, "spam_phones": lambda: [], "reviews_maps": lambda: ({}, {})}
for M in (NEW, LIVE):
    M._H.update(H)
KEYS = ("calls", "callers", "in_ok", "out_ok", "miss_then_ok", "miss_open", "flagged", "mismatch")
red = []
for span in ("today", "yesterday", "7"):
    c1, c2 = conn(), conn()
    t0 = time.time()
    dn = NEW.page_data(c1, span=span, inbox_path=idb, fin_db=fdb, master_path=sm, punch_path=pu)
    tn = time.time() - t0
    dl = LIVE.page_data(c2, span=span, inbox_path=idb, fin_db=fdb)
    a = {k: dn["counts"][k] for k in KEYS}
    b = {k: dl["counts"][k] for k in KEYS}
    fu, k = dn["fu"], dn["ckb"]
    print("%-9s calls %s | people new %d (live %d) WhatsApps in %d | follow-ups %s open %d folded %d today %s came-wk %d visits_ok %s | "
          "Call ke baad ok %s booked %d came %d awaited %d never %d | read %.1f s"
          % (span, "SAME" if a == b else "DIFFER", len(dn["people"]), len(dl["people"]), dn["counts"]["wa_in"],
             fu["src"] or "none", fu["open"], fu["removed"], fu.get("today"), len(fu["came"]), fu["visits_ok"],
             k["ok"], k.get("booked", 0), k.get("came", 0), k.get("due", 0), k.get("noshow", 0), tn))
    if a != b:
        red.append("%s: the call counts differ" % span)
    fl, kl = dl["fu"], dl["ckb"]
    if (fu["open"], fu["removed"], len(fu["came"]), fu.get("today")) != (fl["open"], fl["removed"], len(fl["came"]), fl.get("today")):
        red.append("%s: the follow-up list differs" % span)
    if (k.get("booked"), k.get("came"), k.get("due"), k.get("noshow")) != (kl.get("booked"), kl.get("came"), kl.get("due"), kl.get("noshow")):
        red.append("%s: Call ke baad differs" % span)
    st = dn["staff"]
    print("          staff cards %d: rose %d amber %d green %d | duty matched %d | duty list read %s | to check %d"
          % (len(st), sum(1 for x in st if x["tone"] == "rose"), sum(1 for x in st if x["tone"] == "amber"),
             sum(1 for x in st if x["tone"] == "green"), sum(1 for x in st if x["matched"]),
             all(x["duty_ok"] for x in st) if st else "-", sum(x["check"] for x in st)))
    if tn > 20:
        red.append("%s: the read took %.0f s" % (span, tn))
    if not dn["wa_ok"]:
        red.append("the inbox could not be read")
    c1.close()
    c2.close()
try:
    from flask import Flask
    app = Flask("proof")
    NEW.register(app, lambda f: f, lambda: "manoj", lambda kk, d=None: {"PORTAL_INBOX_DB": idb, "SR_STAFF_MASTER": sm, "SR_PUNCH_CSV": pu}.get(kk, d), H)
    c = conn()
    with app.test_request_context("/portal/console"):
        html = NEW.render(c, {})
    c.close()
    print("render    %d bytes, %d sections folded, %d opened" % (len(html), html.count("<details"), html.count("<details open")))
    if len(html) < 5000 or "id=\"followups\"" not in html or "id=\"staff\"" not in html:
        red.append("the page did not render whole")
except Exception as e:
    red.append("render raised %s" % type(e).__name__)
print("PROOF CLEAN" if not red else "PROOF RED: " + "; ".join(red))
sys.exit(0 if not red else 1)
