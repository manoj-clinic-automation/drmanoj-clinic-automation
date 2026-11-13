#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s814.py FINANCE_DIR SPINE_DB FINANCE_DB -- kit S814's walk on COPIES (never the live database): the Ask, end to end.
FINANCE_DIR holds the files under test (marg_billwatch.py, amir_day.py, owner_notice.py, marg_hand_change.py and the rest). Last line 'WALK n/m'."""
import datetime as dt, os, shutil, sqlite3, sys, tempfile

FIN, SPINE, DB = sys.argv[1:4]
sys.path.insert(0, FIN)
os.environ["SPINE_DB"] = SPINE
tmp = tempfile.mkdtemp(prefix="w814_")
db = os.path.join(tmp, "finance.db")
shutil.copy(DB, db)
import marg_hand_change as H                                      # noqa: E402
import marg_billwatch as BW                                       # noqa: E402
ok = tot = 0


def check(name, cond):
    global ok, tot
    tot += 1
    ok += bool(cond)
    print("%s  %s" % ("PASS" if cond else "FAIL", name))


con = sqlite3.connect(db)
for t in ("billwatch_act", "marg_watch_ask", "marg_watch_ask_row"):   # ON THE COPY ONLY: every move open again, no ask yet -- the walk does not
    if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone():   # depend on what he closed on the live page
        con.execute("DELETE FROM %s" % t + (" WHERE fkey LIKE 'hand:%'" if t == "billwatch_act" else ""))
if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='amir_job'").fetchone():
    con.execute("DELETE FROM amir_job WHERE kind='ask'")
con.commit()
H.refresh(con, SPINE, finance_db=db, force=True)
BW.ensure(con)
check("the ask tables are made by ensure", BW._ask_tables(con))
V = BW.hand_view(con)
fl = [r for r in V["counted"] if r["item"] == "FLEMCORT 6"]
check("two FLEMCORT 6 moves are open to ask about (%d)" % len(fl), len(fl) >= 2)
r0 = next(r for r in fl if r["day_to"] == "2026-10-25")
h = BW.hand_html(con)
check("every open move carries an Ask box", h.count('class="closep mwask"') == len(V["counted"]))
check("the answer notice switch is on section A, Off", "Phone line when a staff answer comes back: <b>Off</b>" in h)
keys = ["hand:%d" % int(r0["id"])] + ["hand:%d" % int(p["id"]) for p in r0["peers"] if p["item"] == "FLEMCORT 6"]
check("a move the page did not offer is refused", BW.ask_send(con, "manoj", ["hand:999999"], "amir", True)[2] == 409)
check("whom must be one of the three", BW.ask_send(con, "manoj", keys, "sohan", True)[2] == 400)
okk, msg, code = BW.ask_send(con, "manoj", keys, "amir", True)
check("asked Amir on his card (%s)" % msg, okk)
a = con.execute("SELECT id, text_hi, staff_ref FROM marg_watch_ask ORDER BY id DESC LIMIT 1").fetchone()
check("the text starts at the matter -- no name, no 'ji' (D927)", a[1].startswith("Marg mein stock badla") and " ji" not in a[1] and "Amir" not in a[1])
check("the text names the moves", a[1].count("FLEMCORT 6") == len(keys) and "Apne card par jawab chuniye." in a[1])
jid = int(a[2].split(":")[1])
j = con.execute("SELECT kind, show_from, sub_hi FROM amir_job WHERE id=?", (jid,)).fetchone()
check("one job of kind 'ask' on Amir's card, shown now, three answers", j[0] == "ask" and j[1] and j[2] == "fixed,right,unknown")
S = BW.ask_state(con)
check("the rows say Asked · Amir", all(S.get(k, {}).get("to") == "amir" and not S[k]["answered"] for k in keys))
check("the chip on the row", "Asked · Amir" in BW.hand_html(con))
# ---- S446 review fixes S3, S4
check("the same row cannot go on Amir's card twice while unanswered (S3)", BW.ask_send(con, "manoj", keys[:1], "amir", True)[2] == 409)
many = (["hand:%d" % int(r["id"]) for r in V["counted"]] + ["hand:%d" % (990000 + i) for i in range(13)])[:13]
n_ask = con.execute("SELECT COUNT(*) FROM marg_watch_ask").fetchone()[0]
check("13 rows in one question are refused, never cut, nothing written (S4)", BW.ask_send(con, "manoj", many, "darpan", False)[2] == 400
      and con.execute("SELECT COUNT(*) FROM marg_watch_ask").fetchone()[0] == n_ask)
# ---- Amir's side
import amir_day as A                                              # noqa: E402
USED = set(keys)


def pick(item):
    """The move of that item if open, else any open move not yet used by the walk (the live list changes day to day)."""
    rs = BW.hand_view(con)["counted"]
    r = next((x for x in rs if x["item"] == item and "hand:%d" % int(x["id"]) not in USED), None) or \
        next((x for x in rs if "hand:%d" % int(x["id"]) not in USED), None)
    if r is not None:
        USED.add("hand:%d" % int(r["id"]))
    return r
J = A._s494_read(con)
asks = [x for x in J["jobs"] if x["kind"] == "ask"]
check("his card reads the question first", J["jobs"] and J["jobs"][0]["kind"] == "ask" and len(asks) == 1)
L = "".join(A._s494_lines(J["jobs"]))
check("Enter in the note box sends no answer: the form opens with a disabled button (M2)",
      "<form method=post style='margin-top:8px'><button type=submit disabled hidden aria-hidden=true></button>" in L)
check("his card shows 'Doctor sahab ka sawaal', the moves and three one-tap answers", "Doctor sahab ka sawaal" in L and L.count("name=ans value=") == 3
      and "FLEMCORT 6" in L and "Marg mein theek kar diya" in L and "Supplier ne bill badla" not in L)
check("no take-back, no 'check this' on his line", "wapas" not in L.lower() and "check" not in L.lower())
check("an answer not offered on this row is refused", A._s494_tap(con, "amir", "ask:%d:supplier" % jid, "") == 0)
check("a made-up word is refused", A._s494_tap(con, "amir", "ask:%d:hello" % jid, "") == 0)
check("his tap is taken", A._s494_tap(con, "amir", "ask:%d:fixed" % jid, "galat batch | par chadh gaya tha") == 1)
check("... once", A._s494_tap(con, "amir", "ask:%d:right" % jid, "") == 0)
check("the line leaves his card", not [x for x in A._s494_read(con)["jobs"] if x["kind"] == "ask"])
ak = BW.ask_state(con)[keys[0]]
check("the answer comes back to the row (%s / %s)" % (ak.get("kind"), ak.get("line")), ak["answered"] and ak["kind"] == "fixed" and ak["line"] == "galat batch par chadh gaya tha")
h3 = BW.hand_html(con)
check("the row says Answered · Amir and shows his words", "Answered · Amir" in h3 and "galat batch par chadh gaya tha" in h3)
check("Marg not yet back: 'not seen yet' is said", "not seen yet" in h3)
check("the row stays open: only he closes it", any(r["id"] == r0["id"] for r in BW.hand_view(con)["counted"]))
# ---- the phone line: OFF until he turns it on; then only what comes after
check("the notice is OFF: nothing to tell", BW.ask_messages(con, dt.datetime.now()) == [])
ru = pick("RUNVACE TP")
if ru is not None:                                                # an answer on his card that no page view has synced yet
    BW.ask_send(con, "manoj", ["hand:%d" % int(ru["id"])], "amir", True)
    jr = int(con.execute("SELECT staff_ref FROM marg_watch_ask ORDER BY id DESC LIMIT 1").fetchone()[0].split(":")[1])
    A._s494_tap(con, "amir", "ask:%d:right" % jr, "")
BW.ask_set_notice(con, "manoj", True)
check("the switch is written last, with every earlier answer marked (M1)", BW.setting(con, "ask.notice") == "on" and
      con.execute("SELECT COUNT(*) FROM marg_watch_ask WHERE answered_at IS NOT NULL AND told_at IS NULL").fetchone()[0] == 0)
check("turned on: the answer that came before is not told", BW.ask_messages(con, dt.datetime.now()) == [])
okk, msg, code = BW.ask_send(con, "manoj", ["hand:%d" % int(pick("NORTIMER TAB")["id"])], "amir", True)
jid2 = int(con.execute("SELECT staff_ref FROM marg_watch_ask ORDER BY id DESC LIMIT 1").fetchone()[0].split(":")[1])
A._s494_tap(con, "amir", "ask:%d:unknown" % jid2, "")
msgs = BW.ask_messages(con, dt.datetime.now())
check("an answer after the switch is told (%d)" % len(msgs), len(msgs) == 1 and "Pata nahi" in msgs[0]["body"] and msgs[0]["key"].startswith("ask:"))
import owner_notice as ON                                          # noqa: E402
now = dt.datetime.now().replace(hour=10, minute=0)
pa = ON._part_ask(con, now)
check("owner_notice's part carries it, kind 'ask'", len(pa) == 1 and pa[0]["kind"] == "ask")
check("the message opens the Marg watch", ON._payload(pa[0]["key"], pa[0]["title"], pa[0]["body"]).get("url") == "/finance/sanjeevni/marg-watch")
check("nothing at night", ON._part_ask(con, dt.datetime.now().replace(hour=23, minute=30)) == [])
ro = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
check("the notice reads only: an unsynced answer is read from his card on a read-only connection (S8)", len(BW.ask_messages(ro, dt.datetime.now())) == 1)
ro.close()
# ---- S446 review S6, S7: he closes a row -> the question leaves Amir's card; a closed row gets no Ask box
gl = pick("GLI-ME SR1")
if gl is not None:
    BW.ask_send(con, "manoj", ["hand:%d" % int(gl["id"])], "amir", True)
    jg = int(con.execute("SELECT staff_ref FROM marg_watch_ask ORDER BY id DESC LIMIT 1").fetchone()[0].split(":")[1])
    okc = BW.hand_close(con, "manoj", int(gl["id"]), "ok", "")
    BW.hand_view(con)
    jr2 = con.execute("SELECT done_at, done_how FROM amir_job WHERE id=?", (jg,)).fetchone()
    check("closing the row takes its question off Amir's card, as withdrawn (S6) %s" % (okc[:1],), okc[0] and jr2[0] and jr2[1] == "withdrawn")
    check("... and it is gone from his card", not [x for x in A._s494_read(con)["jobs"] if x["id"] == jg])
    hc = BW.hand_html(con)
    check("a closed row carries no Ask box (S7)", hc.count('class="closep mwask"') == len(BW.hand_view(con)["counted"]))
# ---- copy / WhatsApp: recorded as 'text taken', nothing on any card
nk = "hand:%d" % int(pick("EXLAIN A")["id"])
n0 = con.execute("SELECT COUNT(*) FROM amir_job").fetchone()[0]
okk, msg, code = BW.ask_send(con, "manoj", [nk], "shavez", False)
check("Shavez: the text is noted on the row, no card line", okk and con.execute("SELECT COUNT(*) FROM amir_job").fetchone()[0] == n0
      and BW.ask_state(con)[nk]["card"] is False)
okk, msg, code = BW.ask_send(con, "manoj", [nk], "darpan", True)
check("Darpan: no card in this kit -- noted only", okk and con.execute("SELECT COUNT(*) FROM amir_job").fetchone()[0] == n0)
# ---- B: a bill row
B = BW.build(con, paper=False)
f = next((x for x in B["findings"] if x["status"] == "open" and x["side"] == "purchase"), None)
if f is not None:
    okk, msg, code = BW.ask_send(con, "manoj", [f["fkey"]], "amir", True)
    t = con.execute("SELECT text_hi, codes FROM marg_watch_ask ORDER BY id DESC LIMIT 1").fetchone()
    check("a bill row: asked with its own words and the supplier answer (%s)" % t[0][:50], okk and f["no"] in t[0] and "supplier" in t[1])
g = next((x for x in B["findings"] if x["side"] == "sale" and x["kind"] == "gone"), None)
if g is not None:
    box = BW.ask_box_b(dict(g, status="open"))
    check("a removed sale bill suggests no one and offers its own answers", "(suggested)" not in box and "returned,mistake,unknown" in box)
# ---- amber after two days
con.execute("UPDATE marg_watch_ask SET asked_at='2026-11-01 09:00:00' WHERE answered_at IS NULL AND staff_ref IS NOT NULL")
con.commit()
check("unanswered for two days: amber", any(v["amber"] for v in BW.ask_state(con).values()))
# ---- the whole page renders
p = BW.page_html(con)
check("the page renders with the asks on A and B", p.count('class="closep mwask"') >= 3 and "mwAskInit" in p)
print("WALK %d/%d" % (ok, tot))
sys.exit(0 if ok == tot else 1)
