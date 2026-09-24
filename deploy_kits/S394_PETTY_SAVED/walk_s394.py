#!/usr/bin/env python3
"""walk_s394.py -- kit S394_PETTY_SAVED (S393 walk + the saved card in Hindi). The real S393 petty_book.py over a SCRATCH COPY of the live finance.db.
(1) Same numbers: every rupee figure on the doctors' page and on Bhati's page with the live file is on the new page too.
(2) The folds: a strip on top, one-line figures, one fold open at a time (name='pb'), no <script>.
(3) The repeat guard, replaying 22-Sep 21:29 (one 9,000 top-up saved at :26, :38, :55): the 2nd and 3rd are refused,
    another amount or another party is not, and after 10 minutes the same entry is allowed; a cancelled entry does
    not block. The live file (S300 or S393) is the negative control.
Prints counts only. Usage: FINANCE_DB=<scratch copy> python3 walk_s393.py <dir with the kit petty_book.py> <live petty_book.py>"""
import importlib.util, os, re, sqlite3, sys
new_dir, live = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
dbp = os.environ["FINANCE_DB"]
assert "walk" in dbp or "scratch" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
os.environ["PETTY_UPLOAD_DIR"] = os.path.join(os.path.dirname(dbp), "petty_walk_uploads")
N = [0]


def ok(c, label, got=None):
    N[0] += 1
    if not c:
        print("WALK RED %d: %s %s" % (N[0], label, "" if got is None else got)); sys.exit(1)


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


from flask import Flask
USER = {"u": {"user": "manoj", "roles": ["checker"]}}


def build(path, tag):
    m = load(path, "petty_" + tag)
    a = Flask("w" + tag)

    def dbg():
        c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row; return c

    def req(*roles, **kw):
        u = USER["u"]
        if not set(u["roles"]) & set(roles):
            from flask import jsonify
            return None, (jsonify(ok=False, error="not_permitted"), 403)
        return u, None
    m.init(a, dbg, req)
    return a, m


A, P = build(os.path.join(new_dir, "petty_book.py"), "new")
A0, P0 = build(live, "old")
c, c0 = A.test_client(), A0.test_client()
os.environ["PETTY_NOW"] = "2026-09-24T21:00:00"
con = sqlite3.connect(dbp); con.row_factory = sqlite3.Row


def nums(html):
    return sorted(re.findall(r"₹ ?([0-9][0-9,]*)", re.sub(r"<[^>]+>", " ", html).replace("&nbsp;", " ")))


for who, roles in (("manoj", ["checker"]), ("bhati", ["maker"]), ("reception", ["viewer"])):
    USER["u"] = {"user": who, "roles": roles}
    new, old = c.get("/finance/petty").get_data(as_text=True), c0.get("/finance/petty").get_data(as_text=True)
    ok("<script" not in new.lower(), "%s: still no JavaScript" % who)
    missing = [x for x in set(nums(old)) if x not in set(nums(new))]
    ok(not missing, "%s: every rupee figure of the live page is on the new page" % who, missing)
    if who != "reception":
        ok("class='strip'" in new and new.count("<details class='card fold' name='pb'") >= 5,
           "%s: a strip on top and the sections as folds" % who, new.count("fold' name='pb'"))
        ok(new.count("name='pb' open") <= 1, "%s: at most one fold open" % who)
    else:
        cut = lambda h: re.sub(r"<style>.*?</style>", "", h, flags=re.S)
        ok(cut(new) == cut(old), "reception's one line is unchanged")

# the owner's strip carries hand, loan, today
USER["u"] = {"user": "manoj", "roles": ["checker"]}
pg = c.get("/finance/petty").get_data(as_text=True)
f = P.figures(con)
strip = pg[pg.index("class='strip'"):pg.index("</div>", pg.index("class='strip'"))]
ok("₹ %s" % P._r(f["hand_p"]) in strip.replace("&nbsp;", " ") and "Loan" in strip and "Bhati today" in strip, "the owner's strip: today, in hand, loan")
ok("Bhati&#x27;s cash" in pg or "Bhati's cash" in pg, "Bhati's cash is a fold")
ok("Entries —" in pg and "Payments" in pg and "Diaries" in pg and "Needs your tap" in pg, "every section is still there")

# the repeat guard -- the walk's own day, a walk-only other_name so nothing real is touched
USER["u"] = {"user": "bhati", "roles": ["maker"]}
con.execute("DELETE FROM petty_entry WHERE entry_date='2001-04-10'"); con.commit()


def save(client, amount, party="shavez", kind="topup", name=""):
    d = {"kind": kind, "party": party, "amount": str(amount)}
    if name:
        d["other_name"] = name
    return client.post("/finance/petty/save", data=d)


def n_walk():
    return con.execute("SELECT COUNT(*) FROM petty_entry WHERE entry_date='2001-04-10' AND void_at=''").fetchone()[0]


os.environ["PETTY_NOW"] = "2001-04-10T21:29:26"
r = save(c, 9000)
ok(r.status_code == 302 and "msg=saved" in r.headers["Location"] and n_walk() == 1, "21:29:26 the top-up is saved")
pg = c.get(r.headers["Location"]).get_data(as_text=True)
card = pg[pg.find("class='saved'"):pg.find("</table>", pg.find("class='saved'"))]
ok("सेव हो गया" in pg and "डायरी भरी" in card and "Shavez" in card and "₹ 9,000" in card and "21:29" in card,
   "S394: the card says, in Hindi, what was saved -- kind, name, amount, time")
ok("गलती हुई — कैंसल करें" in pg, "S394: the card has its own cancel")
USER["u"] = {"user": "someoneelse", "roles": ["maker"]}
ok("सेव हो गया" not in c.get(r.headers["Location"]).get_data(as_text=True), "S394: nobody else is shown Bhati's card")
USER["u"] = {"user": "bhati", "roles": ["maker"]}
os.environ["PETTY_NOW"] = "2001-04-10T21:29:38"
r = save(c, 9000)
ok("msg=dup" in r.headers["Location"] and n_walk() == 1, "21:29:38 the same again is refused ('abhi-abhi save ho chuki')")
os.environ["PETTY_NOW"] = "2001-04-10T21:29:55"
r = save(c, 9000)
ok("msg=dup" in r.headers["Location"] and n_walk() == 1, "21:29:55 and again: refused -- one entry, as the owner said")
pg = c.get("/finance/petty?msg=dup").get_data(as_text=True)
pg = c.get(r.headers["Location"]).get_data(as_text=True)
ok("पहले ही सेव है" in pg and "₹ 9,000" in pg and "21:29" in pg, "Bhati sees why, in Hindi, with the entry that stands and its time")
r = save(c, 8000)
ok("msg=saved" in r.headers["Location"] and n_walk() == 2, "another amount is not a repeat")
r = save(c, 8000, party="darpan")
r_recv = save(c, 20000, kind="receive", party="bhawna")
pgr = c.get(r_recv.headers["Location"]).get_data(as_text=True)
ok("पैसे मिले" in pgr and "Dr Bhawna" in pgr and "₹ 20,000" in pgr, "S394: money received says from whom")
con.execute("DELETE FROM petty_entry WHERE entry_date='2001-04-10' AND kind='receive'"); con.commit()
ok("msg=saved" in r.headers["Location"] and n_walk() == 3, "another person is not a repeat")
r = save(c, 650, kind="pay", party="other", name="WALK KANDEY")
pgk = c.get(r.headers["Location"]).get_data(as_text=True)
ok("भुगतान किया" in pgk and "WALK KANDEY" in pgk and "₹ 650" in pgk, "S394: a payment card names the person as typed")
r2 = save(c, 650, kind="pay", party="other", name="WALK OTHER")
ok("msg=saved" in r.headers["Location"] and "msg=saved" in r2.headers["Location"] and n_walk() == 5,
   "the same amount to two different named people is two payments")
os.environ["PETTY_NOW"] = "2001-04-10T21:40:30"
r = save(c, 9000)
ok("msg=saved" in r.headers["Location"] and n_walk() == 6, "after 10 minutes the same entry is allowed")
eid = con.execute("SELECT MAX(id) FROM petty_entry WHERE entry_date='2001-04-10'").fetchone()[0]
c.post("/finance/petty/void/%d" % eid)
r = save(c, 9000)
ok("msg=saved" in r.headers["Location"], "a cancelled entry does not block its replacement")

# negative control: the live file takes the repeats
con.execute("DELETE FROM petty_entry WHERE entry_date='2001-04-10'"); con.commit()
for t in ("21:29:26", "21:29:38", "21:29:55"):
    os.environ["PETTY_NOW"] = "2001-04-10T" + t
    save(c0, 9000)
if not hasattr(P0, "DUP_MINUTES"):
    ok(n_walk() == 3, "negative control: the live petty_book (S300) saved the same top-up three times -- 22-Sep's fault", n_walk())
ok(not hasattr(P0, "_saved_card"), "negative control: the live petty_book has no saved card")
ok({r.rule for r in A.url_map.iter_rules()} == {r.rule for r in A0.url_map.iter_rules()}, "routes identical")
con.execute("DELETE FROM petty_entry WHERE entry_date='2001-04-10'"); con.commit()
print("WALK OK %d/%d checks" % (N[0], N[0]))
