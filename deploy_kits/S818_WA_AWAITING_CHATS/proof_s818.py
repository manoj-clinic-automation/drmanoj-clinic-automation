#!/usr/bin/env python3
"""proof_s818.py -- S818 on the LIVE stores, READ-ONLY, COUNTS ONLY (no patient name, number or text is printed).
usage: proof_s818.py <new calls_console.py> <live calls_console.py (S817's)> <portal dir> <console.db> <inbox.db> <finance.db>
                     <staff_master.csv> <punches.csv> <review db> <the marks store (need not exist yet)>
Today's page and yesterday's, through the live page and the new page at the same minute:
  . everything that is NOT the WhatsApp-awaiting rule is the same: the strip's call figures, the same people with the same
    calls and WhatsApps on each, the state of every person who has no WhatsApp, the follow-up sections' figures (only the
    'wrote back' pill may change, and it can only become rarer), who called today, Call ke baad, the week's unknown
    callers, the earlier days, and the staff cards' call figures (the same; where a number is marked Not a patient they
    may only fall);
  . the awaiting figures of the page's own people can only FALL: nobody whose WhatsApps the live page reads as answered
    is awaiting on the new one -- but for a person answered only by a DELIVERED row the new page refuses to take for a
    reply (a "Template:" text, an hsm / interactive / button type, no sender within 60 s): counted and said, not red; on every staff card the chats on duty are never more than the live page's messages on
    duty, and the chats not answered never more than its messages not answered;
  . every person the new page reads as awaiting by WhatsApp is on the awaiting block;
  . the new page renders whole on the live rows, the block drawn and MADE (not the "could not be made" line); each read
    under 20 s.
It also COUNTS, for the reader of this screen (no red comes of it): the Inbox's outgoing rows of the days the page reads, by
(source, type, status, sender recorded or not) -- the store's own columns src, mtype, status, sent_by; the rows whose text
begins "Template:" under a type other than 'template'; and the non-template rows with no sender recorded within 60 s after
an incoming message -- the two kinds of row the page now refuses to take for a reply.
Nothing is written: every store is opened read-only (the marks store too, when it is there).
Prints the figures, then 'PROOF CLEAN' or 'PROOF RED: <why>'. (A message or a call that lands between the two reads can make
them differ by itself, so a red is tried once more before it is said.)"""
import datetime as dt
import importlib.util
import os
import sqlite3
import sys
import tempfile
import time

new_p, live_p, pdir, cdb, idb, fdb, sm, pu, rvdb, awdb = sys.argv[1:11]
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
RV = rvdb if os.path.exists(rvdb) else os.path.join(tempfile.mkdtemp(prefix="s818proof_"), "call_review.db")
if RV != rvdb:
    NEW.rv_init(RV)
CFG = {"PORTAL_INBOX_DB": idb, "SR_STAFF_MASTER": sm, "SR_PUNCH_CSV": pu, "FINANCE_DB_PATH": fdb, "PORTAL_CALL_REVIEW_DB": RV,
       "PORTAL_WA_AWAITING_DB": awdb}
from flask import Flask   # noqa: E402
APP = Flask("s818proof")
HELP = {"console_conn": conn, "console_meta": lambda: {"ok": True, "built_at": ""}, "spam_phones": lambda: [], "reviews_maps": lambda: ({}, {})}
NEW.register(APP, lambda f: f, lambda: "manoj", lambda k, d=None: CFG.get(k, d), HELP)
LIVE._H.update(HELP)
LIVE._CFG = lambda k, d=None: CFG.get(k, d)
WA_KEYS = ("awaiting", "tried", "answered", "bar", "wa_replied")
CALL_F = ("answered", "rung", "missed", "made", "cb_in_h", "cb_later", "agreed", "credited")


def contacts(d):
    return sorted((p["phone"], p["n_calls"], p["n_wa"], p["n_in"], p["n_out"], p["n_missed"], p["flagged"], p["mismatch"]) for p in d["people"])


def open_old(p):
    return any(x["kind"] == "wa_in" and LIVE.wa_answer(x, p["calls"]) is None for x in p["calls"])


def open_new(p):
    return any(x["kind"] == "wa_in" and x.get("wa_st") == "open" for x in p["calls"])


def refused(d):
    """the people who hold a DELIVERED outgoing row the new page does not take for a reply (a "Template:" text, an hsm /
    interactive / button type, a row with no sender within 60 s of the message) -- the one way a person the live page reads
    as answered may be awaiting on the new page (the cautious side, meant)"""
    out = set()
    for p in d["people"]:
        last = None
        for x in p["calls"]:
            if x.get("kind") == "wa_in":
                last = x
            elif x.get("kind") == "wa_out" and (x.get("status") or "") in ("delivered", "read") and not NEW.wa_is_reply(x, last):
                out.add(p["phone"])
    return out


def fu_figs(d):
    fu = d["fu"]
    return (fu["found"], fu["open"], fu["today"], fu["who"], fu.get("fl"), [(b[0], b[4], b[5], b[6]) for b in fu["bands"]], len(fu["came"]))


def wrote(d):
    return sum(1 for b in d["fu"]["bands"] for r in b[3] if r["pill"].startswith("Wrote back"))


def one_day(span, say, red):
    lab = "today" if span == "today" else "yesterday"
    now = NEW.now_ist()
    c = conn()
    try:
        t0 = time.time()
        dn = NEW.page_data(c, span=span, now=now, inbox_path=idb, fin_db=fdb, master_path=sm, punch_path=pu)
        tn = time.time() - t0
        dl = LIVE.page_data(c, span=span, now=now, inbox_path=idb, fin_db=fdb, master_path=sm, punch_path=pu)
        with APP.test_request_context("/portal/console"):
            html = NEW.render(c, {} if span == "today" else {"span": span}, now=now)
    finally:
        c.close()
    aw = dn.get("wa_aw") or {}
    marks = len(aw.get("np") or [])
    if dn["wa_ok"] != dl["wa_ok"]:
        red.append("%s: the Inbox reads %s on the new page and %s on the live one" % (lab, dn["wa_ok"], dl["wa_ok"]))
    if {k: v for k, v in dn["counts"].items() if k not in WA_KEYS} != {k: v for k, v in dl["counts"].items() if k not in WA_KEYS}:
        red.append("%s: the strip's call figures changed" % lab)
    if contacts(dn) != contacts(dl):
        red.append("%s: the people or their calls and WhatsApps changed" % lab)
    old = {p["phone"]: p for p in dl["people"]}
    moved_calls = sum(1 for p in dn["people"] if not p["n_wa"] and not p.get("not_patient") and p["phone"] in old and old[p["phone"]]["state"] != p["state"])
    if moved_calls:
        red.append("%s: %d people with no WhatsApp changed state" % (lab, moved_calls))
    o_open = {p["phone"] for p in dl["people"] if open_old(p)}
    n_open = {p["phone"] for p in dn["people"] if open_new(p) and not p.get("not_patient")}
    ref = refused(dn)
    if not (n_open - o_open) <= ref:
        red.append("%s: %d people read answered on the live page and awaiting on the new one" % (lab, len(n_open - o_open - ref)))
    block = {x["phone"] for x in aw.get("chats", [])}
    if aw.get("failed"):
        red.append("%s: the awaiting block could not be made on the live rows" % lab)
    if span == "today" and aw and aw.get("ok") and not {p["phone"] for p in dn["people"] if p.get("wa_wait")} <= block:
        red.append("today: a person awaiting by WhatsApp is not on the awaiting block")
    if fu_figs(dn) != fu_figs(dl):
        red.append("%s: the follow-up sections' figures changed" % lab)
    if wrote(dn) > wrote(dl):
        red.append("%s: more 'wrote back' pills than on the live page" % lab)
    if dn["ckb"] != dl["ckb"] or dn["week"] != dl["week"] or dn["earlier"] != dl["earlier"]:
        red.append("%s: Call ke baad, the week or the earlier days changed" % lab)
    sn, sl = {x["key"]: x for x in (dn.get("staff") or [])}, {x["key"]: x for x in (dl.get("staff") or [])}
    if (dn.get("staff") is None) != (dl.get("staff") is None):
        red.append("%s: the staff cards were made on one page and not on the other" % lab)
    if not set(sn) <= set(sl) or (not marks and set(sn) != set(sl)):
        red.append("%s: the staff cards are not the same people" % lab)
    wa_new = wa_old = wa_no_new = wa_no_old = 0
    for k, x in sn.items():
        y = sl.get(k)
        if y is None:
            continue
        a = [x[f] for f in CALL_F] + [len(x["not_logged"]), len(x["mismatch"]), len(x["not_back"]), x.get("net_missed", 0)]
        b = [y[f] for f in CALL_F] + [len(y["not_logged"]), len(y["mismatch"]), len(y["not_back"]), y.get("net_missed", 0)]
        if (a != b) if not marks else any(i > j for i, j in zip(a, b)):
            red.append("%s: a staff card's call figures changed" % lab)
        if x["wa_in"] > y["wa_in"] or (not ref and (x["wa_in"] - x["wa_ans"]) > (y["wa_in"] - y["wa_ans"])):
            red.append("%s: a staff card counts more WhatsApps than the live page" % lab)
        wa_new, wa_old = wa_new + x["wa_in"], wa_old + y["wa_in"]
        wa_no_new, wa_no_old = wa_no_new + x["wa_in"] - x["wa_ans"], wa_no_old + y["wa_in"] - y["wa_ans"]
    if not html.rstrip().endswith("</body></html>") or 'id="wa-await"' not in html:
        red.append("%s: the new page did not render whole with the block" % lab)
    if tn > 20:
        red.append("%s: the read took %.0f s" % (lab, tn))
    if say:
        print("  %s: %d people, %d with WhatsApp · WhatsApp not answered: %d people on the live page, %d on the new · staff cards (%d): "
              "live %d messages on duty, %d not answered; new %d chats, %d not answered · call figures %s · read %.1f s%s"
              % (lab, len(dn["people"]), sum(1 for p in dn["people"] if p["n_wa"]), len(o_open), len(n_open), len(sn), wa_old, wa_no_old, wa_new, wa_no_new,
                 "the same" if not marks else "the same or lower (numbers are marked Not a patient)", tn,
                 (" · answered on the live page only by a delivered row the new page does not take for a reply, awaiting now as meant: %d" % len((n_open - o_open) & ref)) if (n_open - o_open) & ref else ""))
        if span == "today":
            if aw.get("failed"):
                print("  the awaiting block: COULD NOT BE MADE on these rows")
            elif not aw or not aw.get("ok"):
                print("  the awaiting block: the Inbox could not be read just now -- the page says so; nothing to count")
            else:
                print("  the awaiting block: %d chats awaiting (%d from an earlier day) · %d answered today · %d Done standing · Not a patient: %d · "
                      "the marks store %s · the page drawn (%d KB)"
                      % (aw["n"], aw["old"], len(aw["answered"]), len(aw["done"]), marks,
                         ("read" if os.path.exists(awdb) else "not there yet (made on the first tap)") if aw["marks_ok"] else "NOT readable -- the page shows every chat and says so",
                         len(html) // 1024))


def outgoing():
    """counts only: what the Inbox's outgoing rows look like (the store's own columns), over the days the page reads"""
    try:
        lo = (NEW.now_ist().date() - dt.timedelta(days=NEW.WA_BACK_DAYS + 1)).isoformat()
        c = sqlite3.connect("file:%s?mode=ro" % idb, uri=True, timeout=10)
        try:
            rows = c.execute("SELECT phone, dir, ts, mtype, body, status, sent_by, src FROM msgs WHERE substr(ts,1,10)>=? ORDER BY ts, rid", (lo,)).fetchall()
        finally:
            c.close()
        by, last_in, tpl_text, auto, n_out = {}, {}, 0, 0, 0
        for ph, d, ts, mt, body, st, sb, src in rows:
            ph, t = "".join(ch for ch in str(ph or "") if ch.isdigit())[-10:], NEW.parse_ts(ts)
            if str(d or "").lower() == "in":
                last_in[ph] = t
                continue
            n_out += 1
            mt, blank = str(mt or "text").strip().lower()[:14], not str(sb or "").strip()
            k = (str(src or "-")[:10], mt, str(st or "-").strip().lower()[:10], "no sender" if blank else "sender")
            by[k] = by.get(k, 0) + 1
            if mt != "template" and str(body or "").lstrip().lower().startswith("template:"):
                tpl_text += 1
            if mt != "template" and blank and t is not None and last_in.get(ph) is not None and 0 <= (t - last_in[ph]).total_seconds() <= NEW.WA_AUTO_WITHIN_S:
                auto += 1
        top = sorted(by.items(), key=lambda x: -x[1])
        print("  outgoing rows since %s: %d · by source / type / status / sender: %s%s" % (
            lo, n_out, " · ".join("%s/%s/%s/%s %d" % (k + (n,)) for k, n in top[:12]) or "none", (" · and %d more kinds" % (len(top) - 12)) if len(top) > 12 else ""))
        print("  of them: text beginning \"Template:\" under a type that is not 'template': %d · not a template, no sender recorded, within %d s after "
              "an incoming message: %d (neither is taken for a reply)" % (tpl_text, NEW.WA_AUTO_WITHIN_S, auto))
    except Exception as e:
        print("  the outgoing rows could not be counted (%s)" % type(e).__name__)


def once(say):
    red = []
    one_day("today", say, red)
    one_day("yesterday", say, red)
    if say:
        outgoing()
    return red


try:
    RED = once(True)
    if RED:
        time.sleep(20)
        RED = once(False)
except Exception as e:
    RED = ["the proof could not run (%s)" % type(e).__name__]        # the class name only: never the error's own text
print("PROOF CLEAN" if not RED else "PROOF RED: " + "; ".join(sorted(set(RED))))
