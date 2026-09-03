#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RENDER_TEST_sections_s222.py -- the owner's punch-list, checked in a real browser."""
import datetime as dt, json, os, sqlite3, sys, tempfile, threading, time, shutil
FIN = os.path.abspath(sys.argv[1]); PORT = 8779
F = []
def ck(l, c, d=""):
    print("  %s  %s%s" % ("PASS" if c else "FAIL", l, ("   [%s]" % d) if d else ""))
    if not c: F.append(l)

def main():
    sys.path.insert(0, FIN)
    tmp = tempfile.mkdtemp(); portal = os.path.join(tmp, "portal"); os.makedirs(portal)
    shutil.copyfile(os.environ["CLINIC_USERS_PY"], os.path.join(portal, "clinic_users.py"))
    store = os.path.join(portal, "clinic_users.json")
    json.dump({"epoch":1,"roles":["doctor","manager","staff"],"users":{}}, open(store,"w"))
    os.environ["PORTAL_DIR"]=portal; os.environ["CLINIC_USERS_FILE"]=store
    sys.path.insert(0, portal); import clinic_users as CU
    for u in ("darpan","shivani","alisha","shavez","amir"): CU.add_user(store,u,"staff",u+"1234")
    db = os.path.join(tmp,"finance.db"); c = sqlite3.connect(db)
    c.executescript(open(os.path.join(FIN,"joiner_schema.sql"),encoding="utf-8").read())
    c.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    c.commit(); c.close()
    from flask import Flask, Response
    import joiner_app as JA, staff_pages as SP
    html = open(os.path.join(FIN,"staff_manage.html"),encoding="utf-8").read()
    app = Flask("t")
    def _db():
        x=sqlite3.connect(db); x.row_factory=sqlite3.Row; return x
    def _req(*r,**k): return dict(user="manoj",role="doctor",roles=["checker"]),None
    JA.init(app,_db,SP.joiner_require(_req),url_prefix="/finance/staff")
    @app.route("/finance/staff/")
    def pg_(): return Response(html,mimetype="text/html")
    threading.Thread(target=lambda: app.run(port=PORT,threaded=True,use_reloader=False),daemon=True).start()
    time.sleep(1.5)
    from playwright.sync_api import sync_playwright
    base = "http://127.0.0.1:%d/finance/staff/" % PORT
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ["PW_CHROME"])
        pg = b.new_page(viewport={"width":390,"height":950}); errs=[]; dlg=[]
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("dialog", lambda d: (dlg.append(d.message), d.dismiss()))
        pg.goto(base, wait_until="networkidle")
        pg.evaluate("localStorage.setItem('staff_by','Dr Manoj')")

        print("-- 1  BACK GOES BACK TO MANAGE USERS, and the loop is gone -------")
        pg.goto(base+"?flow=join", wait_until="networkidle"); time.sleep(1.2)
        ck("the address bar no longer carries ?flow (browser Back leaves the app)",
           "flow=" not in pg.url, pg.url)
        a = pg.query_selector("#flow a.btn")
        ck("back is a link to Manage users", bool(a) and "Manage users" in a.inner_text(),
           a.inner_text() if a else "none")
        ck("it points at the portal", "portal/users" in (a.get_attribute("href") or ""),
           a.get_attribute("href") if a else "")
        pg.goto(base+"?flow=exit", wait_until="networkidle"); time.sleep(1.2)
        a = pg.query_selector("#flow a.btn")
        ck("the exit picker's back goes there too",
           bool(a) and "Manage users" in a.inner_text())

        print("\n-- 2  NOTHING IS TYPED THAT COULD BE CHOSEN ----------------------")
        pg.goto(base+"?flow=join", wait_until="networkidle"); time.sleep(1.2)
        jobs = [x.inner_text().strip() for x in pg.query_selector_all("#jf_jobs button")]
        ck("jobs are chips, from the register", "purchase" in jobs and "counter" in jobs, str(jobs))
        ck("and there is an 'other…' escape", "other…" in jobs)
        emps = [x.inner_text().strip() for x in pg.query_selector_all("#jf_emps button")]
        ck("employment is chips", sorted(emps)==["biweekly","fulltime","parttime"], str(emps))
        ck("a new kind can be added", bool(pg.query_selector("#jf_empnewbtn")))
        ck("the confusing 'as the roster spells it' hint is gone",
           "roster spells" not in html)

        print("\n-- 3  A SECOND AMIR GETS amir2 -----------------------------------")
        pg.fill("#jf_name", "Amir Khan"); time.sleep(1.4)
        ck("the login was bumped, not collided", pg.input_value("#jf_user")=="amir2",
           pg.input_value("#jf_user"))
        ck("and it says why", "already taken" in pg.inner_text("#jf_userwhy"),
           pg.inner_text("#jf_userwhy"))

        print("\n-- 4  FOUR SECTIONS, AND TWO OF THEM TELL THE TRUTH INSTEAD ------")
        secs = [x.inner_text().split("\n")[0] for x in pg.query_selector_all("details.grp summary")]
        ck("four systems are shown", len(secs)==4, str(secs))
        body = pg.inner_text("#jf_groups")
        ck("Marg holds the six pharmacy powers",
           all(w in body for w in ("purchase order","purchase entry","expiry check",
                                   "returns","salt fix","stock count")))
        ck("the scan app section has NO tick boxes",
           len(pg.query_selector_all("details.grp:has-text('Scan app') input"))==0)
        # the Scan app section is collapsed because it has nothing to tick -- open
        # it, which also proves its note is one click away rather than buried
        pg.click("details.grp:has-text('Scan app') summary"); time.sleep(0.4)
        scan = pg.inner_text("details.grp:has-text('Scan app')")
        ck("it says the scan app comes with the login",
           "Comes with the portal login" in scan, scan[:80])
        ck("it names the A-D21 limit", "A-D21" in scan)
        ck("attendance says salary is never shown to staff",
           "SALARY IS NEVER SHOWN TO STAFF" in body)
        ck("attendance names the own-month and present-request rulings",
           "D337" in body and "D334" in body)

        print("\n-- 5  THE RUNNING SUMMARY ----------------------------------------")
        pg.click("#jf_jobs button[data-job='purchase']")
        pg.check(".jf_a[value=purchase_order]")
        time.sleep(0.4)
        sm = pg.inner_text("#jf_sum")
        ck("it names the job, the employment and the powers",
           "purchase" in sm and "fulltime" in sm and "purchase order" in sm, sm)

        print("\n-- 6  IT STILL RECORDS WHAT IT SHOWS -----------------------------")
        pg.click("#jf_emps button[data-emp=BIWEEKLY]")
        pg.click("button:has-text('Create the record')"); time.sleep(1.5)
        cx = sqlite3.connect(db); cx.row_factory=sqlite3.Row
        r = cx.execute("SELECT person,role,employment,authorities,username FROM joiner").fetchone()
        cx.close()
        ck("employment", r["employment"]=="BIWEEKLY", r["employment"])
        ck("job", r["role"]=="purchase", r["role"])
        ck("authorities", set(r["authorities"].split(","))=={"self","purchase_order"}, r["authorities"])
        ck("username", r["username"]=="amir2", r["username"])
        ck("no dialog was raised in the whole join", not dlg, str(dlg))

        print("\n-- 7  THE EMP CODE IS A FIELD, NOT A DIALOG ----------------------")
        pg.click("button:has-text('done ✓')"); time.sleep(0.8)   # ACCOUNT_CREATED
        pg.click("button:has-text('done ✓')"); time.sleep(0.8)   # CREDENTIALS_SENT
        pg.click("button:has-text('done ✓')"); time.sleep(0.8)   # FIRST_LOGIN
        pg.click("button:has-text('done ✓')"); time.sleep(1.0)   # BIOMETRIC
        ck("an Emp Code panel opened on the page", bool(pg.query_selector("#bio_code")))
        ck("no dialog", not dlg, str(dlg))
        ck("it is prefilled with the register's next code",
           (pg.input_value("#bio_code") or "").isdigit(), pg.input_value("#bio_code"))
        ck("it carries the never-reuse warning IN ITS OWN WORDS",
           "never reissued" in pg.inner_text("#askBox").lower(),
           pg.inner_text("#askBox")[:110])
        ck("and the register's own rule about gaps as well",
           "gap" in pg.inner_text("#askBox").lower())
        pg.click("#bio_ok"); time.sleep(1.2)
        cx = sqlite3.connect(db)
        got = cx.execute("SELECT emp_code FROM joiner").fetchone()[0]; cx.close()
        ck("the code reached the record", bool(got and str(got).isdigit()), str(got))

        print("\n-- 8  PASSWORD RESET PICKS A PERSON ------------------------------")
        pg.evaluate("goHome()"); time.sleep(0.5)
        pg.click("#rp_box summary"); time.sleep(1.0)
        opts = [o.inner_text().strip() for o in pg.query_selector_all("#rp_person option")]
        ck("the logins are offered, not typed",
           all(u in " ".join(opts) for u in ("darpan","shavez","amir")), str(opts))
        ck("there is a reason field on the page", bool(pg.query_selector("#rp_reason")))
        ck("no javascript error at any point", not errs, "; ".join(errs))
        b.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s -- %d failed" % ("SECTIONS GREEN" if not F else "SECTIONS RED", len(F)))
    for x in F: print("   FAILED:", x)
    return 1 if F else 0

sys.exit(main())
