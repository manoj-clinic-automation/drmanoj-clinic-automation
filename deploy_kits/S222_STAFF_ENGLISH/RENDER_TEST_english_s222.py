#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_allrecs_s222.py -- the two things the owner found, in a real browser.

  1  a COMPLETE record must be openable. His was not: the page lists only what is
     unfinished, so Amir's 6/6 record -- the one the S222 login check was built for --
     could not be reached at all.
  2  an EXISTING login must have its password TRIED, not asserted. His login existed;
     nothing knew whether the password the page printed was the one he had set.

Drives the patched page with chromium against the patched joiner_app.

    python3 -B RENDER_TEST_allrecs_s222.py <dir with the patched files>
"""
import datetime as dt
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time

FIN = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
PORT = 8761
FAILED, PASSED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail else ""))


def main():
    sys.path.insert(0, FIN)
    tmp = tempfile.mkdtemp(prefix="s222_all_")
    portal = os.path.join(tmp, "portal")
    os.makedirs(portal)
    import shutil as _sh
    src_cu = os.environ.get("CLINIC_USERS_PY")
    if not src_cu or not os.path.exists(src_cu):
        raise SystemExit("set CLINIC_USERS_PY to the repo's launcher/clinic_users.py")
    _sh.copyfile(src_cu, os.path.join(portal, "clinic_users.py"))
    store = os.path.join(portal, "clinic_users.json")
    json.dump({"epoch": 1, "roles": ["doctor", "manager", "staff"], "users": {}},
              open(store, "w"))
    os.environ["PORTAL_DIR"] = portal
    os.environ["CLINIC_USERS_FILE"] = store
    sys.path.insert(0, portal)
    import clinic_users as CU
    # the live shape the owner actually has: the login EXISTS, made by his own hand
    CU.add_user(store, "amir", "staff", "amir1234")

    db = os.path.join(tmp, "finance.db")
    con = sqlite3.connect(db)
    con.executescript(open(os.path.join(FIN, "joiner_schema.sql"), encoding="utf-8").read())
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    today = dt.date.today().isoformat()
    # ONE COMPLETE record (Amir's shape) and ONE still open, so the lists differ
    con.execute("INSERT INTO joiner (ref,kind,person,role,status,username,employment,"
                "authorities,emp_code,opened_on,opened_by,closed_on,closed_by,created_at,"
                "updated_at) VALUES ('JOIN-2026-0001','JOIN','AMIR SOHAIL','purchase',"
                "'COMPLETE','amir','BIWEEKLY','self','101',?,'Dr Manoj',?,'Dr Manoj',?,?)",
                (today, today, now, now))
    con.execute("INSERT INTO joiner (ref,kind,person,role,status,username,employment,"
                "authorities,opened_on,opened_by,created_at,updated_at) VALUES "
                "('JOIN-2026-0002','JOIN','Nobody Yet','counter','DECIDED','nobody',"
                "'FULLTIME','self',?,'Dr Manoj',?,?)", (today, now, now))
    jid = con.execute("SELECT id FROM joiner WHERE ref='JOIN-2026-0001'").fetchone()[0]
    for s in ("DECIDED", "ACCOUNT_CREATED", "CREDENTIALS_SENT", "FIRST_LOGIN",
              "BIOMETRIC", "STAFF_MASTER"):
        con.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by) "
                    "VALUES (?,?,?,'Dr Manoj')", (jid, s, today))
    con.commit()
    con.close()

    from flask import Flask, Response
    import joiner_app as JA, staff_pages as SP
    src = open(JA.__file__, encoding="utf-8").read()
    html = open(os.path.join(FIN, "staff_manage.html"), encoding="utf-8").read()
    print("-- 0  what is under test ------------------------------------------")
    ck("joiner_app carries the S222 ALL RECORDS route", "S222 ALL RECORDS" in src)
    ck("the page carries the sab-record button", "All records" in html)
    ck("the page no longer states the password unconditionally",
       "password_works" in html)
    hindi = [w for w in ("jodna", "vidaai", "kholo", "kaun", "haalat", "adhoora",
                         "banao", "jaanch", "kijiye", "ho gaya", "wapas",
                         "dikhao", "Aapka naam") if w in html]
    ck("NO romanised Hindi is left in the owner console", not hindi, str(hindi))
    ck("the page declares itself English", 'lang="en"' in html)

    app = Flask("s222_all")

    def _db():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    def _require(*roles, **kw):
        return dict(user="manoj", role="doctor", roles=["checker"]), None

    JA.init(app, _db, SP.joiner_require(_require), url_prefix="/finance/staff")

    @app.route("/finance/staff/")
    def page():
        return Response(html, mimetype="text/html")

    threading.Thread(target=lambda: app.run(port=PORT, threaded=True,
                                            use_reloader=False), daemon=True).start()
    time.sleep(1.5)

    from playwright.sync_api import sync_playwright
    url = "http://127.0.0.1:%d/finance/staff/" % PORT
    chrome = os.environ.get("PW_CHROME",
                            "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome)
        pg = b.new_page(viewport={"width": 390, "height": 850})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url, wait_until="networkidle")
        pg.evaluate("localStorage.setItem('staff_by','Dr Manoj')")
        time.sleep(0.8)

        print("\n-- 1  THE FAULT HE HIT: a finished record is unreachable ---------")
        home = pg.inner_text("body")
        ck("the pending list says there is nothing unfinished",
           "Koi adhoora record nahin" in home or "Nobody Yet" in home)
        ck("AMIR is NOT in the pending list", "AMIR SOHAIL" not in home)

        print("\n-- 2  SAB RECORD: the closed one is there, and opens -------------")
        pg.click("button:has-text('All records')")
        time.sleep(1.2)
        body = pg.inner_text("#allrecs")
        ck("AMIR SOHAIL is listed", "AMIR SOHAIL" in body)
        ck("his record reads 6/6", "6/6" in body)
        ck("it is marked complete", "complete" in body)
        ck("the still-open one is listed too", "Nobody Yet" in body)
        pg.click("#allrecs tr:has-text('AMIR SOHAIL') button")
        time.sleep(1.5)
        rec = pg.inner_text("body")
        ck("his record page opened", "AMIR SOHAIL" in rec and "JOIN-2026-0001" in rec)
        ck("no javascript error", not errs, "; ".join(errs))

        print("\n-- 3  THE PASSWORD IS TRIED, NOT ASSERTED ------------------------")
        line = pg.inner_text("#loginState")
        ck("it says the login exists", "login amir exists" in line)
        ck("it names the role from the store", "(staff)" in line)
        ck("it says the password ACTUALLY WORKS", "works right now" in line, line[:120])

        print("\n-- 4  CHANGE THE PASSWORD BEHIND ITS BACK ------------------------")
        CU.set_password(store, "amir", "something-else")
        pg.evaluate("showRec('JOIN-2026-0001')")
        time.sleep(1.5)
        line = pg.inner_text("#loginState")
        ck("it no longer claims the password works", "works right now" not in line)
        ck("it warns that the printed password does NOT sign in",
           "does NOT sign in" in line, line[:160])
        ck("it still says the login itself exists", "login amir exists" in line)
        ck("no javascript error", not errs, "; ".join(errs))

        print("\n-- 5  SEARCH, and the missing-login path still warns -------------")
        pg.evaluate("goHome()")
        time.sleep(0.8)
        pg.fill("#allq", "nobody")
        pg.click("button:has-text('All records')")
        time.sleep(1.2)
        body = pg.inner_text("#allrecs")
        ck("search narrows to the one asked for",
           "Nobody Yet" in body and "AMIR SOHAIL" not in body)
        pg.click("#allrecs tr:has-text('Nobody Yet') button")
        time.sleep(1.5)
        line = pg.inner_text("#loginState")
        ck("a joiner with no login still gets the warning, not credentials",
           "has NOT been created" in line, line[:120])
        ck("no javascript error", not errs, "; ".join(errs))

        b.close()

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    n = len(PASSED) + len(FAILED)
    print("\n%s -- %d passed, %d failed"
          % ("RENDER GREEN" if not FAILED else "RENDER RED", len(PASSED), len(FAILED)))
    for x in FAILED:
        print("   FAILED: %s" % x)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
