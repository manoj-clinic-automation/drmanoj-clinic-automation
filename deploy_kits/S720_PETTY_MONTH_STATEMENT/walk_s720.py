#!/usr/bin/env python3
"""walk_s720.py -- kit S720 (session 390, the parent). The petty book on a made-up database only.
   python walk_s720.py <petty_book.py under test> <the live petty_book.py>
Checks the new month statement against an independent sum, the owner's tap for Dr Bhawna, the refusals, and that
Bhati's own Hindi page and the viewer's line are byte-identical to the live module's. The control (live file as the
first argument) must go RED. Exit 0 = WALK OK."""
import datetime as dt, importlib.util, os, re, sqlite3, sys, tempfile

from flask import Flask, g, request

test, live = sys.argv[1], sys.argv[2]
os.environ["PETTY_NOW"] = "2026-11-06T14:30:00"
ROLES = {"manoj": {"checker"}, "bhawna": {"checker"}, "bhati": {"maker"}, "alisha": {"viewer"}, "amir": set()}
oks, fails = [], []


def ck(n, c):
    (oks if c else fails).append(n)
    print(("  ok   " if c else "  FAIL ") + n)


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def build(path, name, dbp):
    m = load(path, name)
    app = Flask(name)
    app.config["TESTING"] = True

    def db():
        if "con" not in g:
            g.con = sqlite3.connect(dbp)
            g.con.row_factory = sqlite3.Row
        return g.con

    @app.teardown_appcontext
    def _c(e):
        c = g.pop("con", None)
        if c:
            c.close()

    def require(*roles, unit=None):
        u = request.headers.get("X-User", "")
        r = ROLES.get(u, set())
        if not (r & set(roles)):
            return None, ("denied", 403)
        return {"user": u, "roles": sorted(r)}, None

    def audit(con, table, row_id, action, before=None, after=None, who=None):
        con.execute("CREATE TABLE IF NOT EXISTS audit (t TEXT, id INT, a TEXT, who TEXT)")
        con.execute("INSERT INTO audit VALUES (?,?,?,?)", (table, row_id, action, who))
    m.init(app, db, require, audit)
    return m, app.test_client()


def seed(dbp, mod):
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    mod._schema_done = False
    mod._ensure(con)
    con.execute("INSERT INTO petty_opening VALUES ('cash', 4400000, 'manoj', '2026-09-24 21:14:24')")
    rows = [  # date, kind, party, other, rupees, confirmed
        ("2026-09-18", "receive", "manoj", "", 20000, 1), ("2026-09-20", "receive", "bhawna", "", 15000, 1),
        ("2026-09-21", "pay", "nanne", "", 3000, 0), ("2026-09-22", "pay", "other", "Tea stall", 120, 0),
        ("2026-09-25", "topup", "shavez", "", 3000, 0), ("2026-10-02", "receive", "bhawna", "", 20000, 0),
        ("2026-10-03", "pay", "rahul", "", 5000, 0), ("2026-10-05", "pay", "ilyas", "", 9700, 0),
        ("2026-10-06", "pay", "hariom", "", 4000, 0), ("2026-10-09", "topup", "darpan", "", 4000, 0),
        ("2026-10-10", "loan_out", "", "", 2000, 0), ("2026-10-20", "loan_back", "", "", 500, 0),
        ("2026-10-21", "pay", "other", "Plumber", 800, 0), ("2026-10-22", "pay", "other", "plumber", 200, 0),
        ("2026-11-02", "receive", "bhawna", "", 10000, 0), ("2026-11-03", "pay", "hariom", "", 4000, 0),
        ("2026-11-04", "topup", "shavez", "", 8000, 0), ("2026-10-11", "pay", "nanne", "", 7777, 0)]
    for i, (d, k, p, o, a, c) in enumerate(rows, 1):
        con.execute("INSERT INTO petty_entry (id, entry_date, kind, party, other_name, amount_p, by_whom, at, confirm_by, confirm_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)", (i, d, k, p, o, a * 100, "bhati", d + " 10:00:00", "manoj" if c else "", d + " 11:00:00" if c else ""))
    con.execute("UPDATE petty_entry SET void_by='manoj', void_at='2026-10-11 12:00:00' WHERE id=18")   # a cancelled 7,777
    con.commit()
    con.close()


def hand_through(con, d):
    s = lambda k: con.execute("SELECT COALESCE(SUM(amount_p),0) FROM petty_entry WHERE void_at='' AND kind=? AND entry_date<=?", (k, d)).fetchone()[0]
    return 4400000 + s("receive") - s("topup") - s("pay") - s("loan_out") + s("loan_back")


t = tempfile.mkdtemp(prefix="s720_")
dbn, dbo = os.path.join(t, "new.db"), os.path.join(t, "old.db")
mn = load(test, "pb_seed")
seed(dbn, mn)
seed(dbo, mn)
M, C = build(test, "pb_new", dbn)
L, CL = build(live, "pb_live", dbo)
H = lambda u: {"X-User": u}

# 1 the statement
r = C.get("/finance/petty?m=2026-10", headers=H("manoj"))
page = r.get_data(as_text=True)
ck("1a the owner's page opens (200) with a Month statement section", r.status_code == 200 and "Month statement" in page)
ck("1b ?m=2026-10 opens that statement, October 2026", "Month statement — October 2026" in page and re.search(r"<details class='card fold' name='pb' open><summary><span class='ft'>Month statement", page) is not None)
con = sqlite3.connect(dbn)
has = hasattr(M, "statement")
con_r = sqlite3.connect(dbn)
con_r.row_factory = sqlite3.Row
st = M.statement(con_r, "2026-10") if has else {}
ck("1c in hand on 1 October = opening + everything to 30 Sep", has and st["open_hand_p"] == hand_through(con, "2026-09-30"))
ck("1d in hand at October's end = opening + everything to 31 Oct", has and st["close_hand_p"] == hand_through(con, "2026-10-31"))
ck("1e October's payments = 5,000 + 9,700 + 4,000 + 800 + 200 (the cancelled 7,777 counts nowhere)", has and st["paid_p"] == 1970000)
ck("1f accrued to 31 Oct = September's 3,120 + October's 19,700", has and st["accrued_p"] == 312000 + 1970000)
ck("1g received in October: Dr Bhawna 20,000 (1 not confirmed), Dr Manoj 0", has and [(x[0], x[2], x[3]) for x in st["recv"]] == [("manoj", 0, 0), ("bhawna", 2000000, 1)])
ck("1h others grouped by name, any letter case: plumber 1,000", has and [(o["other_name"].lower(), o["a"]) for o in st["others"]] == [("plumber", 100000)])
st11 = M.statement(con_r, "2026-11") if has else {}
ck("1i November: Rahul named 'due, not paid' (paid in October only)", has and ("Rahul", 500000) in st11["due"] and not M.statement(con_r, "2026-10")["due"])
ck("1j heads: construction October 13,700, monthly 5,000, others 1,000", has and st["heads"]["construction"][0] == 1370000 and st["heads"]["monthly"][0] == 500000 and st["heads"]["other"][0] == 100000)
ck("1k the months offered run from September 2026 to November 2026", has and M.statement_months(con_r) == ["2026-11", "2026-10", "2026-09"])
ck("1l the page shows the figures it computed", has and ("₹ %s" % M._r(st["close_hand_p"])) in page and ("₹ %s" % M._r(st["accrued_p"])) in page)
ck("1m the Entries section follows the chosen month (Oct)", "Entries — Oct" in page and "Plumber" in page)
r2 = C.get("/finance/petty/statement?m=2026-09", headers=H("manoj"))
ck("1n the statement as a page to print (200, September 2026)", r2.status_code == 200 and "September 2026" in r2.get_data(as_text=True))
ck("1o Bhati (maker) cannot open the statement page", C.get("/finance/petty/statement", headers=H("bhati")).get_data(as_text=True).count("Not permitted") == 1)
cx = sqlite3.connect(dbn); cx.execute("UPDATE petty_holder SET active=0 WHERE code='darpan'"); cx.execute("UPDATE petty_payee SET head='misc' WHERE code='raja'"); cx.commit()
st2 = M.statement(con_r, "2026-10") if has else {}
ck("1q an inactive holder's top-up still shows: start - rows = end", has and st2["open_hand_p"] + st2["recv_p"] - st2["top_p"] - st2["paid_p"] - st2["loan_out_p"] + st2["loan_back_p"] == st2["close_hand_p"]
   and ("Darpan", 400000) in st2["tops"])
pg3 = C.get("/finance/petty?m=2026-10", headers=H("manoj")).get_data(as_text=True)
ck("1r a payee under another head is not dropped (head 'misc' shown)", "Misc" in pg3)
cx.execute("UPDATE petty_holder SET active=1 WHERE code='darpan'"); cx.execute("UPDATE petty_payee SET head='construction' WHERE code='raja'"); cx.commit()
ck("1p a nonsense month falls back to this month", "Month statement — November 2026" in C.get("/finance/petty?m=1999-01", headers=H("manoj")).get_data(as_text=True))

# 3a first, before this walk writes anything: the other pages are the live module's
for who, path in (("bhati", "/finance/petty"), ("alisha", "/finance/petty"), ("amir", "/finance/petty")):
    a = C.get(path, headers=H(who)).get_data(as_text=True)
    b = CL.get(path, headers=H(who)).get_data(as_text=True)
    a = re.sub(r"<style>.*?</style>", "", a, flags=re.S); b = re.sub(r"<style>.*?</style>", "", b, flags=re.S)
    ck("3a %s's page is the live module's, byte for byte (the shared style sheet aside)" % who, a == b)

# 2 the owner taps for Dr Bhawna
pend = C.get("/finance/petty", headers=H("manoj")).get_data(as_text=True)
ck("2a the owner sees 'Yes, Dr Bhawna gave it' on her entries", "Yes, Dr Bhawna gave it" in pend)
r = C.post("/finance/petty/confirm/6", headers=H("manoj"))
row = con.execute("SELECT confirm_by, confirm_at FROM petty_entry WHERE id=6").fetchone()
ck("2b his tap confirms it, recorded 'manoj for bhawna'", row[0] == "manoj for bhawna" and row[1] != "")
ck("2c the entry then reads 'manoj for Dr Bhawna'", "manoj for Dr Bhawna" in C.get("/finance/petty?m=2026-10", headers=H("manoj")).get_data(as_text=True))
r = C.post("/finance/petty/confirm/6", headers=H("manoj"))
ck("2d a second tap is refused, the first stands", "msg=bad" in r.headers.get("Location", "") and con.execute("SELECT confirm_by FROM petty_entry WHERE id=6").fetchone()[0] == "manoj for bhawna")
con.execute("INSERT INTO petty_entry (id, entry_date, kind, party, amount_p, by_whom, at) VALUES (40,'2026-11-05','receive','manoj',100000,'bhati','2026-11-05 09:00:00')")
con.commit()
r = C.post("/finance/petty/confirm/40", headers=H("bhawna"))
ck("2e Dr Bhawna cannot confirm Dr Manoj's money (unchanged)", "notyours" in r.headers.get("Location", "") and con.execute("SELECT confirm_at FROM petty_entry WHERE id=40").fetchone()[0] == "")
r = C.post("/finance/petty/confirm/15", headers=H("bhawna"))
ck("2f Dr Bhawna still confirms her own (recorded 'bhawna')", con.execute("SELECT confirm_by FROM petty_entry WHERE id=15").fetchone()[0] == "bhawna")
r = C.post("/finance/petty/confirm/40", headers=H("bhati"))
ck("2g Bhati cannot confirm anything", con.execute("SELECT confirm_at FROM petty_entry WHERE id=40").fetchone()[0] == "")
r = C.post("/finance/petty/confirm/40", headers=H("manoj"))
ck("2h the owner confirms his own as before ('manoj')", con.execute("SELECT confirm_by FROM petty_entry WHERE id=40").fetchone()[0] == "manoj")

# 3 nothing else moved
ck("3b figures() unchanged in shape and value", M.figures(con_r) == L.figures(con_r))
sn = re.search(r"<style>(.*?)</style>", M._shell("x", "", "en"), re.S).group(1)
so = re.search(r"<style>(.*?)</style>", L._shell("x", "", "en"), re.S).group(1)
ck("3d the style sheet only gains lines (nothing of the live one removed or changed)", all(x in sn.splitlines() for x in so.splitlines()))
src_new, src_old = open(test, encoding="utf-8").read(), open(live, encoding="utf-8").read()
ck("3c no new table, no new write: the SCHEMA and every INSERT/UPDATE but the confirm are the live module's",
   M.SCHEMA == L.SCHEMA and sorted(re.findall(r"(INSERT[^\"]*|UPDATE petty_\w+ SET \w+)", src_new)) ==
   sorted(re.findall(r"(INSERT[^\"]*|UPDATE petty_\w+ SET \w+)", src_old)))
print(("WALK OK %d/%d" % (len(oks), len(oks) + len(fails))) if not fails else ("WALK RED %d of %d failed" % (len(fails), len(oks) + len(fails))))
sys.exit(1 if fails else 0)
