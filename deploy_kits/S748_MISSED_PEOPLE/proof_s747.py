#!/usr/bin/env python3
"""proof_s747.py -- S747 on the LIVE stores, READ-ONLY, COUNTS ONLY (no patient name, number or text is printed).
usage: proof_s747.py <new calls_console.py> <live calls_console.py> <portal dir> <console.db> <inbox.db> <finance.db>
                     <staff_master.csv> <punches.csv> <review db>
Through the live and the new module, for today, yesterday and 7 days:
  . the CALL figures, the follow-up list and Call ke baad identical (S747 changes only the staff cards);
  . the staff cards: every answered / made / not-logged / staff≠AI / agreed call is on exactly the same total across the
    cards (a reception-mobile call only MOVES to the person on duty); missed calls and WhatsApps per person identical
    (the review store, read here as it stands -- empty before the install -- changes no figure until he taps);
  . the person's own card (the staff route, as each phone staff member) carries the same figures as the owner's card;
  . the page renders with the buttons; each read under 20 s.
And F-1168's reading: the MyOperator agents of the last 30 days by FIRST WORD with their call counts (staff names only), and
how many reception-mobile calls were credited / not credited (with why) in the 7 days.
Prints 'PROOF CLEAN' or 'PROOF RED: <why>'."""
import importlib.util
import os
import sqlite3
import sys
import tempfile
import time

new_p, live_p, pdir, cdb, idb, fdb, sm, pu, rvdb = sys.argv[1:10]
sys.path.insert(0, pdir)
TMPRV = None
if not os.path.exists(rvdb):                       # before the install: an empty store of the new shape, in a scratch folder
    TMPRV = os.path.join(tempfile.mkdtemp(prefix="s747proof_"), "call_review.db")
CUR = {"user": ""}


def login_required(f):                            # the portal's two names, as register() looks for them (this module plays it)
    return f


def _sso_user(req):
    return dict(CUR) if CUR["user"] else None


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
if TMPRV:
    NEW.rv_init(TMPRV)
RV = TMPRV or rvdb
CFG = {"PORTAL_INBOX_DB": idb, "SR_STAFF_MASTER": sm, "SR_PUNCH_CSV": pu, "FINANCE_DB_PATH": fdb, "PORTAL_CALL_REVIEW_DB": RV}
H = {"console_conn": conn, "console_meta": lambda: {"ok": True, "built_at": ""}, "spam_phones": lambda: [], "reviews_maps": lambda: ({}, {})}
for M in (NEW, LIVE):
    M._H.update(H)
    M._CFG = lambda k, d=None: CFG.get(k, d)
KEYS = ("calls", "callers", "in_ok", "out_ok", "miss_then_ok", "miss_open", "flagged", "mismatch")
red = []
print("review store: %s" % ("not on the box yet -- read as an empty one" if TMPRV else "on the box, read as it stands"))
for span in ("today", "yesterday", "7"):
    c1, c2 = conn(), conn()
    t0 = time.time()
    dn = NEW.page_data(c1, span=span, inbox_path=idb, fin_db=fdb, master_path=sm, punch_path=pu)
    tn = time.time() - t0
    dl = LIVE.page_data(c2, span=span, inbox_path=idb, fin_db=fdb, master_path=sm, punch_path=pu)
    a = {k: dn["counts"][k] for k in KEYS}
    b = {k: dl["counts"][k] for k in KEYS}
    fu, k, fl, kl = dn["fu"], dn["ckb"], dl["fu"], dl["ckb"]
    if a != b:
        red.append("%s: the call counts differ" % span)
    if (fu["open"], fu["removed"], len(fu["came"]), fu.get("today")) != (fl["open"], fl["removed"], len(fl["came"]), fl.get("today")):
        red.append("%s: the follow-up list differs" % span)
    if (k.get("booked"), k.get("came"), k.get("due"), k.get("noshow")) != (kl.get("booked"), kl.get("came"), kl.get("due"), kl.get("noshow")):
        red.append("%s: Call ke baad differs" % span)
    sn, sl = dn["staff"] or [], dl["staff"] or []
    if dn["staff"] is None:
        red.append("%s: the new cards could not be made" % span)

    def tot(cs):
        return (sum(x["answered"] for x in cs), sum(x["made"] for x in cs), sum(len(x["not_logged"]) for x in cs),
                sum(len(x["mismatch"]) for x in cs), sum(x["agreed"] for x in cs))
    rv_any = bool(NEW.rv_read(RV)[0]) or bool(NEW.rv_read(RV)[1])
    if tot(sn) != tot(sl) and not rv_any:
        red.append("%s: the cards' call totals differ (%s vs %s)" % (span, tot(sn), tot(sl)))
    per_new = {x["key"]: (x["missed"], x["wa_in"]) for x in sn if not x["rec"]}
    per_live = {x["key"]: (x["missed"], x["wa_in"]) for x in sl if x["key"] != "reception"}
    if per_new != per_live and not rv_any:
        red.append("%s: missed calls or WhatsApps per person differ" % span)
    rec = next((x for x in sn if x["rec"]), None)
    cred = sum(x["credited"] for x in sn)
    print("%-9s calls %s | follow-ups %s | Call ke baad %s | cards %d (live %d): totals %s %s | missed+WA per person %s | "
          "reception mobile: %d credited, %d not credited%s | read %.1f s"
          % (span, "SAME" if a == b else "DIFFER", "SAME" if fu["open"] == fl["open"] else "DIFFER",
             "SAME" if k.get("booked") == kl.get("booked") else "DIFFER", len(sn), len(sl), tot(sn),
             "SAME" if tot(sn) == tot(sl) else "DIFFER", "SAME" if per_new == per_live else "DIFFER",
             cred, len(rec["items"]) if rec else 0, (" (" + rec["duty_h"].split("(")[1].split(")")[0] + ")") if rec else "", tn))
    if tn > 20:
        red.append("%s: the read took %.0f s" % (span, tn))
    c1.close()
    c2.close()
# F-1168: which agents are on the box (first words, counts only)
c = conn()
try:
    rows = c.execute("SELECT ca.agent, COUNT(*) FROM call_agent ca JOIN calls cl ON cl.join_key=ca.join_key "
                     "WHERE substr(cl.ended_at_ist,1,10)>=date('now','-30 day') AND TRIM(COALESCE(ca.agent,''))<>'' GROUP BY ca.agent").fetchall()
    by = {}
    for ag, n in rows:
        fw = NEW.first_name(ag).lower()
        by[fw] = by.get(fw, 0) + n
    print("agents (first word, calls in 30 days): " + ", ".join("%s %d" % (k2, v) for k2, v in sorted(by.items(), key=lambda x: -x[1])))
    print("reception agent setting 'reception' %s among them" % ("IS" if "reception" in by else "is NOT"))
except sqlite3.Error as e:
    red.append("the agents could not be read (%s)" % type(e).__name__)
c.close()
try:
    from flask import Flask
    app = Flask("proof")
    NEW.register(app, lambda f: f, lambda: "manoj", lambda kk, d=None: CFG.get(kk, d), H)
    c = conn()
    with app.test_request_context("/portal/console"):
        html = NEW.render(c, {"span": "7"})
    c.close()
    print("render    %d bytes, %d sections folded, %d opened, review buttons %d" % (len(html), html.count("<details"), html.count("<details open"),
                                                                                 html.count('class="rb')))
    if len(html) < 5000 or 'id="followups"' not in html or 'id="staff"' not in html:
        red.append("the page did not render whole")
    cn = conn()
    pg = {x["key"]: x for x in (NEW.page_data(cn, span="yesterday", inbox_path=idb, fin_db=fdb, master_path=sm, punch_path=pu)["staff"] or [])}
    cn.close()
    for who_ in [k2.strip() for k2 in str(CFG.get("PORTAL_PHONE_STAFF") or NEW.PHONE_STAFF_DEFAULT).split(",") if k2.strip()]:
        CUR["user"] = who_
        with app.test_client() as cl:
            r = cl.get("/portal/console/api/mycard?span=yesterday")
            j = r.get_json() or {}
        card = j.get("card")
        same = (card is None and who_ not in pg) or (card and who_ in pg and card["figs"]["answered"] == pg[who_]["answered"]
                                                      and card["figs"]["missed"] == pg[who_]["missed"] and card["figs"]["not_logged"] == len(pg[who_]["not_logged"]))
        print("own card  %-8s yesterday: %s, %d calls listed, figures %s the owner's card" % (who_, "ok" if j.get("ok") else "NOT ok",
                                                                                           len((card or {}).get("calls", [])), "SAME as" if same else "DIFFER from"))
        if not j.get("ok") or not same:
            red.append("%s's own card is not the owner's" % who_)
except Exception as e:
    red.append("render or the staff route raised %s" % type(e).__name__)
print("PROOF CLEAN" if not red else "PROOF RED: " + "; ".join(red))
sys.exit(0 if not red else 1)
