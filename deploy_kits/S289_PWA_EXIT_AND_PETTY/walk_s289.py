#!/usr/bin/env python3
"""walk_s289.py -- the live-shape walk of the petty book: THE REAL finance_app.py (patched) over a
SCRATCH COPY of the real finance.db, every role at the front gate and through each screen.
Nothing live is touched: the caller passes a copy. Header identity is used ONLY here.
Usage: FINANCE_DB=<copy> FINANCE_ALLOW_HEADER_AUTH=1 PETTY_UPLOAD_DIR=<tmp> PETTY_NOW=<iso> \
       python3 walk_s289.py <dir holding the patched finance_app.py + petty_book.py>
"""
import io
import os
import sqlite3
import sys

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def main():
    sys.path.insert(0, sys.argv[1])
    os.chdir(sys.argv[1])
    assert os.environ.get("FINANCE_ALLOW_HEADER_AUTH") == "1"
    dbp = os.environ["FINANCE_DB"]
    assert "walk" in dbp or "scratch" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
    import finance_app as fa
    check("petty_book mounted", "petty_book" in fa.app.blueprints)
    c = fa.app.test_client()

    def as_(user):
        return {"X-Clinic-User": user, "X-Clinic-Role": ""}

    def get(user, path):
        return c.get(path, headers=as_(user))

    def post(user, path, data, files=None):
        d = dict(data)
        if files:
            d.update(files)
        return c.post(path, data=d, headers=as_(user), content_type="multipart/form-data")

    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    # ---- the gate -------------------------------------------------------------------------
    r = get("stranger", "/finance/petty")
    check("a login with no petty role is refused at the gate", r.status_code in (302, 403))
    r = get("darpan", "/finance/petty")
    check("darpan (medical maker, no petty row) refused", r.status_code in (302, 403))
    r = get("bhati", "/finance/clinic/day")
    check("bhati still refused clinic pages", r.status_code in (302, 403))
    r = get("bhati", "/finance/approvals")
    check("bhati refused the Sanjeevni hub", r.status_code in (302, 403))
    # ---- keeper's home --------------------------------------------------------------------
    r = get("bhati", "/finance/petty")
    t = r.get_data(as_text=True)
    check("bhati home 200", r.status_code == 200)
    for word in ("Aaj aap aa rahe hain?", "Aapke haath mein", "Hari Om Ji", "Nanne", "Bhavani", "Ilyas",
                 "Mittal Electric", "Raja", "Cartage", "Rahul", "Koi aur", "Loan liya", "Darpan", "Shavez",
                 "Dr Manoj se mile", "Dr Bhawna se mile"):
        check("bhati home shows " + word, word in t)
    check("AC technician is not on the list", "AC" not in t.replace("ACC", ""))
    check("no English owner page for bhati", "The three" not in t)
    check("need shown: 10,000 when empty", "10,000" in t)
    # ---- availability ---------------------------------------------------------------------
    today = fa.dt.date.fromisoformat(os.environ["PETTY_NOW"][:10])
    post("bhati", "/finance/petty/available", {"day": today.isoformat(), "status": "yes"})
    check("availability stored", con.execute("SELECT status FROM petty_available WHERE day=?", (today.isoformat(),)).fetchone()[0] == "yes")
    post("bhati", "/finance/petty/available", {"day": "2020-01-01", "status": "no"})
    check("a far date refused", con.execute("SELECT COUNT(*) FROM petty_available WHERE day='2020-01-01'").fetchone()[0] == 0)
    r = get("shivani", "/finance/petty")
    t = r.get_data(as_text=True)
    check("reception viewer sees the line", r.status_code == 200 and "Bhati ji aaj available" in t)
    check("reception viewer sees nothing else", "haath" not in t and "Hari Om" not in t and "Loan" not in t)
    r = post("shivani", "/finance/petty/save", {"kind": "pay", "party": "raja", "amount": "10"})
    check("viewer cannot write", r.status_code in (302, 403) and con.execute("SELECT COUNT(*) FROM petty_entry").fetchone()[0] == 0)
    # ---- entries --------------------------------------------------------------------------
    r = get("bhati", "/finance/petty/new/pay/rahul")
    check("Rahul form pre-filled 5000", 'value="5000"' in r.get_data(as_text=True))
    post("bhati", "/finance/petty/save", {"kind": "receive", "party": "manoj", "amount": "10000"})
    post("bhati", "/finance/petty/save", {"kind": "pay", "party": "hariom", "amount": "2500"},
         {"photo": (io.BytesIO(b"\xff\xd8\xff fake jpeg"), "bill.jpg")})
    post("bhati", "/finance/petty/save", {"kind": "topup", "party": "darpan", "amount": "640"})
    post("bhati", "/finance/petty/save", {"kind": "pay", "party": "rahul", "amount": "5000"})
    post("bhati", "/finance/petty/save", {"kind": "pay", "party": "cartage", "amount": "300"})
    r = post("bhati", "/finance/petty/save", {"kind": "pay", "party": "other", "amount": "200"})
    check("other payee without a name refused", "msg=name" in r.headers.get("Location", ""))
    post("bhati", "/finance/petty/save", {"kind": "pay", "party": "other", "amount": "200", "other_name": "Plumber"})
    post("bhati", "/finance/petty/save", {"kind": "loan_out", "party": "self", "amount": "1000"})
    r = post("bhati", "/finance/petty/save", {"kind": "pay", "party": "raja", "amount": "abc"})
    check("non-number refused", "msg=amount" in r.headers.get("Location", ""))
    r = post("bhati", "/finance/petty/save", {"kind": "pay", "party": "actech", "amount": "100"})
    check("unknown payee refused", "msg=bad" in r.headers.get("Location", ""))
    r = post("bhati", "/finance/petty/save", {"kind": "pay", "party": "raja", "amount": "50"},
             {"photo": (io.BytesIO(b"MZ"), "x.exe")})
    check("a non-photo upload refused", "msg=photo" in r.headers.get("Location", ""))
    n = con.execute("SELECT COUNT(*) FROM petty_entry").fetchone()[0]
    check("seven entries saved", n == 7)
    import petty_book as pb
    f = pb.figures(con)
    # 10000 - 2500 - 640 - 5000 - 300 - 200 - 1000 = 360
    check("in hand arithmetic", f["hand_p"] == 36000)
    check("needs = hold - hand", f["need_p"] == 1000000 - 36000)
    check("loan kept apart", f["loan_p"] == 100000)
    ph = con.execute("SELECT photo FROM petty_entry WHERE party='hariom'").fetchone()[0]
    check("photo stored", ph and os.path.isfile(os.path.join(os.environ["PETTY_UPLOAD_DIR"], ph)))
    # cancel own same-day
    eid = con.execute("SELECT id FROM petty_entry WHERE party='cartage'").fetchone()[0]
    post("bhati", "/finance/petty/void/%d" % eid, {})
    check("keeper cancels own same-day entry", con.execute("SELECT void_by FROM petty_entry WHERE id=?", (eid,)).fetchone()[0] == "bhati")
    check("cancelled entry counts nowhere", pb.figures(con)["hand_p"] == 36000 + 30000)
    # ---- the doctors ----------------------------------------------------------------------
    r = get("manoj", "/finance/petty")
    t = r.get_data(as_text=True)
    check("owner page 200", r.status_code == 200)
    for word in ("Manoj Bhati today", "Available", "Needs your tap", "The three", "Payments", "Rahul",
                 "paid this month", "Hari Om Ji", "Plumber", "Bhati's loan", "photo", "Separate from Sanjeevni"):
        check("owner page shows " + word, word in t)
    check("owner page is English (no Hinglish keeper labels)", "Aapke haath" not in t)
    rid = con.execute("SELECT id FROM petty_entry WHERE kind='receive'").fetchone()[0]
    r = post("bhawna", "/finance/petty/confirm/%d" % rid, {})
    check("Dr Bhawna cannot confirm money Dr Manoj gave", "notyours" in r.headers.get("Location", ""))
    post("manoj", "/finance/petty/confirm/%d" % rid, {})
    check("Dr Manoj confirms his", con.execute("SELECT confirm_by FROM petty_entry WHERE id=?", (rid,)).fetchone()[0] == "manoj")
    lid = con.execute("SELECT id FROM petty_entry WHERE kind='loan_out'").fetchone()[0]
    post("bhawna", "/finance/petty/confirm/%d" % lid, {})
    check("a loan OK by either doctor", con.execute("SELECT confirm_by FROM petty_entry WHERE id=?", (lid,)).fetchone()[0] == "bhawna")
    post("manoj", "/finance/petty/count", {"holder": "darpan", "matches": "1"})
    post("manoj", "/finance/petty/count", {"holder": "shavez", "short": "150"})
    rows = sorted(tuple(x) for x in con.execute("SELECT holder, short_p FROM petty_count"))
    check("counts recorded", rows == [("darpan", 0), ("shavez", 15000)])
    r = post("bhati", "/finance/petty/count", {"holder": "darpan", "matches": "1"})
    check("keeper cannot record a count", r.status_code == 403)
    r = post("bhati", "/finance/petty/confirm/%d" % lid, {})
    check("keeper cannot confirm", r.status_code == 403)
    r = get("manoj", "/finance/petty/photo/%d" % con.execute("SELECT id FROM petty_entry WHERE party='hariom'").fetchone()[0])
    check("doctor opens the photo", r.status_code == 200)
    r = get("shivani", "/finance/petty/photo/1")
    check("viewer cannot open a photo", r.status_code == 403)
    # ---- independence ---------------------------------------------------------------------
    before = {t_: con.execute("SELECT COUNT(*) FROM %s" % t_).fetchone()[0]
              for t_ in ("day_entry", "day_expense", "cash_movement", "clinic_register_day", "clinic_physio_day")}
    post("bhati", "/finance/petty/save", {"kind": "pay", "party": "nanne", "amount": "999"})
    after = {t_: con.execute("SELECT COUNT(*) FROM %s" % t_).fetchone()[0] for t_ in before}
    check("no Sanjeevni or clinic table touched by a petty write", before == after)
    # ---- physio tick (read-only look) ---------------------------------------------------------
    d = con.execute("SELECT business_date FROM clinic_physio_day WHERE cash_p>0 OR upi_p>0 ORDER BY business_date DESC LIMIT 1").fetchone()
    if d:
        post("bhati", "/finance/petty/physio/%s" % d[0], {})
        check("physio tick stored", con.execute("SELECT COUNT(*) FROM petty_physio_check WHERE business_date=?", (d[0],)).fetchone()[0] == 1)
        check("physio table unchanged by the tick", after["clinic_physio_day"] == con.execute("SELECT COUNT(*) FROM clinic_physio_day").fetchone()[0])
    # ---- the rest of the app still answers --------------------------------------------------
    for path, user in (("/finance/physio", "bhati"), ("/finance/clinic/day", "manoj"), ("/finance/healthz", "manoj")):
        r = get(user, path)
        check("still 200: %s as %s" % (path, user), r.status_code == 200)
    print("WALK OK — %d checks (petty book over a scratch copy of the real finance.db)" % N[0])


if __name__ == "__main__":
    main()
