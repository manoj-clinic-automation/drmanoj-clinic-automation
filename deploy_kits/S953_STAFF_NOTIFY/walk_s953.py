#!/usr/bin/env python3
"""walk_s953.py -- S953_STAFF_NOTIFY: the walk of callback_clock.py (and the staff page's ?tab=) on S948 + S951's MADE-UP stores
(every number 500000xxxx; 'today' 24-Nov, a Tuesday). Nothing here reads a real store or sends anything: the push, the device list
and ntfy are stubs; every path is a temp file.

  python walk_s953.py walk <code dir>    every check; exit 0 only when all pass (the code dir holds callback_clock.py, calls_staff.py,
                                         calls_console.py, ring_outcome.py, ring_common.py)
"""
import datetime as _dt
import fcntl
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FAILS = []
N = [0]


def ok(cond, what):
    N[0] += 1
    print(("  PASS  " if cond else "  FAIL  ") + what)
    if not cond:
        FAILS.append(what)


SENT, NTFY = [], []


def pusher(w, payload):
    SENT.append((w, payload))
    return 1, 0


def at(d, hm):
    return _dt.datetime.combine(_dt.date.fromisoformat(d), _dt.time(*[int(x) for x in hm.split(":")]))


ENV_KEYS = ("PORTAL_CLOCK_LISTS", "PORTAL_CLOCK_AGAIN_ON", "PORTAL_CLOCK_WA_ON", "PORTAL_CLOCK_WA_MIN", "PORTAL_CLOCK_T1_MIN",
            "PORTAL_CLOCK_T2_MIN", "PORTAL_STAFF_NTFY_URL")


def world(now, punches="both", **env):
    """A fresh made-up root: S951's fixture (today + yesterday + visits), console built 5 min before `now`, spam 3016."""
    root = tempfile.mkdtemp(prefix="s953w_")
    con_p, inbox_p = W1.fixture(root)
    c = sqlite3.connect(con_p)
    c.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", (now.strftime("%Y-%m-%d %H:%M:%S"),))
    c.commit()
    c.close()
    rev = os.path.join(root, "console_reviews.db")
    r = sqlite3.connect(rev)
    r.execute("CREATE TABLE dispositions (join_key TEXT PRIMARY KEY, final_outcome TEXT)")
    r.execute("INSERT INTO dispositions VALUES (?,?)", (W.ph(3016) + "_1795000000", "Spam / marketing"))
    r.commit()
    r.close()
    pf = os.path.join(root, "punches.csv")
    if punches == "shivani":
        open(pf, "w").write("user_id,datetime\n1,%s 08:00:00\n" % W.TODAY)
    elif punches == "none":
        open(pf, "w").write("user_id,datetime\n")
    elif punches == "missing":
        os.remove(pf)
    for k in ENV_KEYS:
        os.environ.pop(k, None)
    os.environ.update({"PORTAL_INBOX_DB": inbox_p, "SR_STAFF_MASTER": os.path.join(root, "staff_master.csv"), "SR_PUNCH_CSV": pf,
                       "FINANCE_DB_PATH": os.path.join(root, "no_finance.db"), "PORTAL_PHONE_STAFF": "shivani,alisha",
                       "PORTAL_CALL_REVIEW_DB": os.path.join(root, "call_review.db"),
                       "PORTAL_WA_AWAITING_DB": os.path.join(root, "wa_awaiting.db"), "PORTAL_WA_ENV": os.path.join(root, "no.env")})
    os.environ.update({k: str(v) for k, v in env.items()})
    CC._H.clear()
    try:
        CC._CARD_CACHE.clear()
    except Exception:
        pass
    del SENT[:]
    del NTFY[:]
    return {"root": root, "con": con_p, "rev": rev, "store": os.path.join(root, "callback_clock.db")}


def go(w, now, dry=False):
    del SENT[:]
    c = sqlite3.connect(w["con"])
    c.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", (now.strftime("%Y-%m-%d %H:%M:%S"),))
    c.commit()
    c.close()
    return CB.run(dry=dry, pusher=pusher, now=now, console=w["con"], store=w["store"], reviews=w["rev"])


def sent_rows(w, stage):
    if not os.path.exists(w["store"]):
        return []
    c = sqlite3.connect(w["store"])
    try:
        return c.execute("SELECT phone, t0 FROM sent WHERE stage=?", (stage,)).fetchall()
    finally:
        c.close()


def phones(w, stage):
    return {p for p, _t in sent_rows(w, stage)}


def by_tag(tag):
    return [(who, p) for who, p in SENT if p.get("tag") == tag]


OLD = "/portal/go/call-tracker"


def lands(t, tab):
    """Every push of the tag lands right: an admitted login on the staff page's tab, the reception mobile (not admitted by
    the page's default settings) on S796's landing."""
    return bool(t) and all(p["url"] == (OLD if who == "reception" else "/portal/console/staff?tab=" + tab) for who, p in t)


def P(*ns):
    return {W.ph(n) for n in ns}


def do_walk(code):
    T = W.TODAY
    print("[1] 11:30 -- the 30 / 60 minute stages follow the Incoming missed tab (today's + yesterday's carried)")
    w = world(at(T, "11:30"))
    res = go(w, at(T, "11:30"))
    s1, s2 = phones(w, 1), phones(w, 2)
    ok(res.get("ok") and res.get("lists") is True, "the run is ok and read the staff lists")
    ok(P(7, 11, 2001, 2005) <= s1, "today's missed, not tried, 30+ duty min -> stage 1 (7 . 11 . 2001 . 2005)")
    ok(P(3001, 3002, 3013, 3018, 3020, 3014, 3023, 3012) <= s1, "yesterday's carried misses -> stage 1 (after hours . daytime . "
       "two misses . existing patient . answered BEFORE . visit before yesterday . tried 3x yesterday)")
    ok(not (P(2002, 3005, 3006) & s1), "a caller tried once / twice is not chased by stage 1 (Call again / Evening has him)")
    ok(not (P(3003, 3008, 3004, 3010, 3021, 3022, 3011, 3016, 2003) & s1),
       "not chased: answered the same day . reached today . wrote after . visited (ID / mobile) . two days ago . spam . wrote today")
    ok(P(11, 3001, 3002) <= s2 and not (P(7, 2001, 2005) & s2), "stage 2 (60+): 11 and the carried; not 7 / 2001 / 2005 (under 60)")
    rows1 = dict(sent_rows(w, 1))
    ok(rows1.get(W.ph(3001)) == "C" + T and rows1.get(W.ph(7), "").startswith(T + " 10:55"),
       "a carried miss is keyed by today (C%s); today's by its own time" % T)
    t1, t2 = by_tag("cb-clock-1"), by_tag("cb-clock-2")
    ok(bool(t1) and {x[0] for x in t1} == {"shivani", "alisha", "reception"} and lands(t1, "missed"),
       "stage 1 -> the phone staff, tap opens /portal/console/staff?tab=missed")
    ok(any(w_ == "reception" and p["url"] == OLD for w_, p in t1), "the reception mobile (not admitted by the staff page) keeps S796's landing")
    ok(bool(t2) and {x[0] for x in t2} == {"shavez"} and t2[0][1]["url"] == "/portal/console/staff?tab=missed", "stage 2 -> Shavez, same tab")
    ok(not by_tag("cb-clock-3"), "11:30: no Call again is due yet (the first is due 12:00) -> no Call again push")
    s4 = phones(w, 4)
    ok(P(10, 2003, 3010, 3004) <= s4 and not (P(2005, 1) & s4),
       "WhatsApp waiting 30+ duty min -> pushed (10 . 2003 . 3010 . 3004); answered chats not (2005 . 1)")
    t4 = by_tag("cb-clock-4")
    ok(bool(t4) and lands(t4, "wa") and {x[0] for x in t4} == {"shivani", "alisha", "reception"},
       "WhatsApp -> the phone staff on duty + reception, tap opens ?tab=wa")
    ok(bool(t4) and "WhatsApp waiting: %d" % len(s4) == t4[0][1]["title"], "WhatsApp title says the count")
    n1 = len(sent_rows(w, 1))
    res2 = go(w, at(T, "11:35"))
    ok(len(sent_rows(w, 1)) == n1 + res2["new1"] and not (s1 & {p for p, _t in sent_rows(w, 1)[n1:]}),
       "11:35: nobody is notified twice for a stage")
    ok(res2.get("new_wa") == 0 and not by_tag("cb-clock-4") and phones(w, 4) == s4, "11:35: no WhatsApp chat pushed twice")

    print("[2] 12:30 -- Call again due (2 h after one unanswered try)")
    w = world(at(T, "12:30"))
    go(w, at(T, "12:30"))
    s3 = phones(w, 3)
    ok(P(2002, 3005, 2) <= s3, "Call again due -> pushed (2002 missed-path . 3005 carried . 2 follow-up)")
    ok(not (P(5, 3006) & s3), "two tries (Evening calls) are not Call again")
    t3 = by_tag("cb-clock-3")
    ok(bool(t3) and lands(t3, "again") and t3[0][1]["title"] == "Call again due: %d" % len(s3),
       "Call again -> tap opens ?tab=again, the title says the count")
    ok(bool(sent_rows(w, 3)) and all(t == "A" + T for _p, t in sent_rows(w, 3)), "Call again keyed once per number per day")
    r35 = go(w, at(T, "12:35"))
    ok(r35.get("new_again") == 0 and not by_tag("cb-clock-3") and phones(w, 3) == s3, "12:35: Call again not pushed twice")

    print("[3] who gets the new pushes -- the duty (staff_master + punches, calls_console's own reading)")
    for how, want in (("shivani", {"shivani", "reception"}), ("none", {"reception", "shavez"}),
                      ("missing", {"shivani", "alisha", "reception"})):
        w = world(at(T, "12:30"), punches=how)
        r = go(w, at(T, "12:30"))
        t3 = by_tag("cb-clock-3")
        ok(t3 and {x[0] for x in t3} == want, "punches %s -> %s (%s)" % (how, ", ".join(sorted(want)), r.get("duty")))
        ok({x[0] for x in by_tag("cb-clock-1")} == {"shivani", "alisha", "reception"}, "punches %s: stage 1 still to the three as S796" % how)

    print("[4] settings")
    w = world(at(T, "12:30"), PORTAL_CLOCK_AGAIN_ON="0", PORTAL_CLOCK_WA_ON="off")
    go(w, at(T, "12:30"))
    ok(not by_tag("cb-clock-3") and not by_tag("cb-clock-4") and by_tag("cb-clock-1"), "Call again / WhatsApp off -> none; stage 1 still")
    w = world(at(T, "11:30"), PORTAL_CLOCK_WA_MIN="45")
    go(w, at(T, "11:30"))
    ok(W.ph(10) not in phones(w, 4) and W.ph(2003) in phones(w, 4), "WhatsApp at 45 min: 10 (30 min) waits, 2003 (60) pushed")
    w = world(at(T, "11:30"), PORTAL_CLOCK_T1_MIN="40", PORTAL_CLOCK_T2_MIN="bad")
    go(w, at(T, "11:30"))
    ok(W.ph(7) not in phones(w, 1) and W.ph(2001) in phones(w, 1) and W.ph(11) in phones(w, 2),
       "stage 1 at 40 min: 7 (35) waits, 2001 (48) pushed; a bad 60 reads as 60")
    w = world(at(T, "11:30"), PORTAL_CLOCK_LISTS="0")
    r = go(w, at(T, "11:30"))
    ok(r.get("lists") is False and W.ph(2002) in phones(w, 1) and not by_tag("cb-clock-4") and
       lands(by_tag("cb-clock-1"), "missed"),
       "lists off -> the S796 rule (2002, tried once, is chased), no new pushes, the tap still opens the new page")

    print("[5] a fault in the lists -> S796's rule, nothing lost")
    w = world(at(T, "11:30"))
    real = CS.build_lists
    CS.build_lists = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        r = go(w, at(T, "11:30"))
    finally:
        CS.build_lists = real
    ok(r.get("ok") and r.get("lists") is False and W.ph(7) in phones(w, 1) and by_tag("cb-clock-1"),
       "build_lists raises -> run ok, lists False, stage 1 still sent by the S796 rule")

    print("[5b] a PART of the lists fails (yesterday's carry, caught inside the page's builder) -> S796's rule too")
    w = world(at(T, "11:30"))
    real_bp = CC.build_people
    CC.build_people = lambda conn, d_from, *a_, **k_: (_ for _ in ()).throw(RuntimeError("y")) if d_from == W1.YDAY else real_bp(conn, d_from, *a_, **k_)
    try:
        r = go(w, at(T, "11:30"))
    finally:
        CC.build_people = real_bp
    ok(r.get("lists") is False and P(3001, 3013, 3018) <= phones(w, 1),
       "carry_ok False -> lists False, the after-hours carried callers still chased by S796's rule (3001 . 3013 . 3018)")
    ok(bool(by_tag("cb-clock-4")) and P(10, 2003) <= phones(w, 4), "only the carry failed -> today's WhatsApp reminders still go")
    import contextlib
    import io
    import re as _re
    w = world(at(T, "11:30"))
    CC.build_people = lambda conn, d_from, *a_, **k_: (_ for _ in ()).throw(KeyError(W.ph(3001))) if d_from == W1.YDAY else real_bp(conn, d_from, *a_, **k_)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stderr(buf):
            go(w, at(T, "11:30"))
    finally:
        CC.build_people = real_bp
    ok("failed" in buf.getvalue() and not _re.search(r"\d{10}", buf.getvalue()) and "......" in buf.getvalue(),
       "the page builder's failure line reaches the clock's log with the number masked")

    print("[5e] the staff page's admitted logins cannot be read -> every tap keeps S796's landing")
    w = world(at(T, "11:30"))
    real_ak = CS.allowed_keys
    CS.allowed_keys = lambda: (_ for _ in ()).throw(RuntimeError("cfg"))
    try:
        go(w, at(T, "11:30"))
    finally:
        CS.allowed_keys = real_ak
    ok(bool(by_tag("cb-clock-1")) and all(p["url"] == OLD for _w, p in by_tag("cb-clock-1") + by_tag("cb-clock-4")),
       "allowed_keys() unreadable -> stage 1 and WhatsApp land on S796's page for everyone")

    print("[5c] a carried caller missed AGAIN today after his carried reminder -> the new miss has its own clock")
    w = world(at(T, "11:30"))
    go(w, at(T, "11:30"))
    c = sqlite3.connect(w["con"])
    W1.add_call(c, 3002, "In", 0, T, "11:40")
    c.commit()
    c.close()
    go(w, at(T, "12:15"))
    ks = sorted(t for p_, t in sent_rows(w, 1) if p_ == W.ph(3002))
    ok(len(ks) == 2 and ("C" + T) in ks and any(k_.startswith(T + " 11:40") for k_ in ks), "3002: the carried reminder (C%s), then one for 11:40" % T)

    print("[5d] a 0 written in portal_config.py switches a reminder off")
    w = world(at(T, "12:30"))
    import types
    had = hasattr(CB, "_PC")                            # the FROM (S796) has no settings at all: the check just fails there
    if had:
        CB._PC[:] = [types.SimpleNamespace(PORTAL_CLOCK_AGAIN_ON=0, PORTAL_CLOCK_WA_ON=False), True]
    try:
        go(w, at(T, "12:30"))
    finally:
        if had:
            CB._PC[:] = [None, False]
    ok(not by_tag("cb-clock-3") and not by_tag("cb-clock-4") and by_tag("cb-clock-1"), "AGAIN_ON = 0 / WA_ON = False in portal_config -> off")

    print("[6] outside duty, the closing, dry, stale, the lock")
    w = world(at(T, "21:00"))
    r = go(w, at(T, "21:00"))
    t9 = by_tag("cb-clock-9")
    ok(not by_tag("cb-clock-1") and not by_tag("cb-clock-3") and not by_tag("cb-clock-4"), "21:00: no staff push outside duty")
    old = CB.open_callers(*CB.read_console(w["con"], W1.YDAY, T)[1:], CB.spam_phones(w["rev"]), CB.window(_dt.date.fromisoformat(W1.YDAY))[1])
    ok(bool(t9) and t9[0][0] == "manoj" and t9[0][1]["title"] == "Callers not called back today: %d" % len(old) and t9[0][1]["url"] == "/portal/console",
       "21:00: the owner's closing line, S796's own count (%d), his Call Console" % len(old))
    go(w, at(T, "21:05"))
    ok(not by_tag("cb-clock-9"), "21:05: the closing line once a day")
    w = world(at(T, "11:30"))
    r = go(w, at(T, "11:30"), dry=True)
    ok(bool(r.get("ok")) and not SENT and not os.path.exists(w["store"]) and r.get("again_due") == 0 and r.get("wa_due", 0) >= 4,
       "--dry: counts only, nothing sent, nothing written")
    w = world(at(T, "11:30"))
    c = sqlite3.connect(w["con"])
    c.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", ((at(T, "10:50")).strftime("%Y-%m-%d %H:%M:%S"),))
    c.commit()
    c.close()
    r = CB.run(pusher=pusher, now=at(T, "11:30"), console=w["con"], store=w["store"], reviews=w["rev"])
    ok(r.get("why") == "stale" and not SENT, "console.db 40 min old -> nothing judged, nothing sent")
    w = world(at(T, "11:30"))
    fh = open(w["store"] + ".lock", "w")
    fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        r = go(w, at(T, "11:30"))
    finally:
        fh.close()
    ok(r.get("why") == "locked" and not SENT, "another run holds the lock -> this run skipped, nothing sent")

    print("[7] ntfy -- only for a login with no device, only when a staff topic is set")
    CB.SUBS_OF = lambda u: [] if u == "alisha" else [{"endpoint": "x"}]
    CB.NTFY_POST = lambda url, title, body, click: NTFY.append((url, title, body, click)) or True
    try:
        w = world(at(T, "12:30"))
        go(w, at(T, "12:30"))
        ok(not NTFY, "no PORTAL_STAFF_NTFY_URL -> no ntfy")
        w = world(at(T, "12:30"), PORTAL_STAFF_NTFY_URL="https://ntfy.invalid/clinic-staff")
        r = go(w, at(T, "12:30"))
        ok(NTFY and all(u == "https://ntfy.invalid/clinic-staff" and "(alisha)" in b for u, _t, b, _c in NTFY)
           and any(c_ == "https://followup.dr-manoj.in/portal/console/staff?tab=again" for _u, _t, _b, c_ in NTFY)
           and (r.get("sent") or {}).get("ntfy", 0) >= 1, "a topic set -> one ntfy per push naming alisha (no device), tap to the right tab")
        import re as _re
        ok(NTFY and not any(_re.search(r"\d{5} ?\d{5}", b_) for _u, _t, b_, _c in NTFY) and any("......" in b_ for _u, _t, b_, _c in NTFY),
           "ntfy (an outside server) carries numbers to the last four only")
    finally:
        CB.SUBS_OF = None
        CB.NTFY_POST = None

    print("[8] the staff page reads ?tab=")
    app, _cc, _pm, _ = W.build_app(tempfile.mkdtemp(prefix="s953p_"), *W.make_fixture(tempfile.mkdtemp(prefix="s953q_")), W.NOW)
    cl = app.test_client()
    r = cl.get("/portal/console/staff?tab=missed", headers=W.H("shivani"))
    t = r.get_data(as_text=True)
    ok(r.status_code == 200 and 'URLSearchParams(location.search).get("tab")' in t and t.find("URLSearchParams") < t.find('sessionStorage.getItem("s948tab")'),
       "the page reads ?tab= first, the remembered tab after")
    ok(all(('id="t-%s"' % k) in t for k in ("missed", "again", "wa")), "the three tabs the taps name exist on the page")
    ok('history.replaceState(null,"",location.pathname)' in t, "after using ?tab= the page clears it (its 5-minute reload keeps her own tab)")
    print("")
    print("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    CODE = os.path.abspath(sys.argv[2])
    os.environ["RING_PORTAL_DIR"] = CODE
    sys.path.insert(0, CODE)
    import walk_s948 as W  # noqa: E402
    W.CODE = CODE
    import walk_s951 as W1  # noqa: E402
    import calls_console as CC  # noqa: E402
    import calls_staff as CS  # noqa: E402
    import callback_clock as CB  # noqa: E402
    CB.PORTAL_DIR = CODE
    CC._ro()._mobile_fp = lambda m: "fp" + str(m)[-4:]
    sys.exit(do_walk(CODE))
