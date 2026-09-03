#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_forms_s222.py -- a real browser filling the joiner form and picking a leaver.

The point of this gate is not that the form looks right. It is that the form RECORDS WHAT THE
PROMPTS THREW AWAY: `/api/open` has always accepted the employment type, the authorities and a
chosen username, and since S208 the page asked for none of them. So the browser fills the form,
and then the DATABASE is read to prove the values landed.

And on the exit side: the leaver is CHOSEN from a list. The test asserts no name is ever typed.

    python3 -B RENDER_TEST_forms_s222.py <dir with the patched files>
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
PORT = 8767
FAILED, PASSED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail else ""))


def main():
    sys.path.insert(0, FIN)
    tmp = tempfile.mkdtemp(prefix="s222_forms_")
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
    for u in ("darpan", "shivani", "alisha", "shavez", "amir"):
        CU.add_user(store, u, "staff", u + "1234")

    db = os.path.join(tmp, "finance.db")
    con = sqlite3.connect(db)
    con.executescript(open(os.path.join(FIN, "joiner_schema.sql"), encoding="utf-8").read())
    con.commit()
    con.close()

    from flask import Flask, Response
    import joiner_app as JA, staff_pages as SP
    src = open(JA.__file__, encoding="utf-8").read()
    html = open(os.path.join(FIN, "staff_manage.html"), encoding="utf-8").read()
    print("-- 0  what is under test ------------------------------------------")
    ck("joiner_app carries the S222 FORMS routes", "S222 FORMS" in src)
    ck("the page carries the joiner form", "New joiner</h2>" in html)
    ck("the old two-prompt openFlow is gone",
       "New joiner's full name?" not in html and "What is the job?" not in html)

    app = Flask("s222_forms")

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
        pg = b.new_page(viewport={"width": 390, "height": 900})
        errs, dialogs = [], []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
        pg.goto(url, wait_until="networkidle")
        pg.evaluate("localStorage.setItem('staff_by','Dr Manoj')")
        time.sleep(0.6)

        print("\n-- 1  ALL LOGINS on the home screen ------------------------------")
        pg.click("button:has-text('All logins')")
        time.sleep(1.0)
        lg = pg.inner_text("#logins")
        ck("every login in the store is listed",
           all(u in lg for u in ("darpan", "shivani", "alisha", "shavez", "amir")), lg[:90])
        ck("their state is shown", "active" in lg)
        ck("it points at the portal's own page for add/remove", "Manage Users" in lg)

        print("\n-- 2  NEW JOINER IS A FORM, NOT A CHAIN OF PROMPTS ---------------")
        pg.click("button:has-text('New joiner')")
        time.sleep(1.0)
        ck("no dialog was raised", not dialogs, str(dialogs))
        for sel, what in (("#jf_name", "full name"), ("#jf_role", "job"),
                          ("#jf_user", "portal login"), ("#jf_by", "opened by")):
            ck("the form has a %s field" % what, bool(pg.query_selector(sel)))
        emps = [e.inner_text().strip() for e in pg.query_selector_all("input[name=jf_e]")]
        ck("employment choices came from the register",
           len(pg.query_selector_all("input[name=jf_e]")) == 3,
           str(len(pg.query_selector_all("input[name=jf_e]"))))
        auths = [e.get_attribute("value") for e in pg.query_selector_all(".jf_a")]
        ck("the authorities list came from the register (8 of them)",
           len(auths) == 8, str(auths))
        ck("'purchase_order' is offered", "purchase_order" in auths)

        print("\n-- 3  FILL IT, AND THE VALUES MUST REACH THE DATABASE ------------")
        pg.fill("#jf_name", "Zahir Ahmad")
        time.sleep(0.3)
        ck("the login was derived from the first name",
           pg.input_value("#jf_user") == "zahir", pg.input_value("#jf_user"))
        pg.fill("#jf_role", "purchase")
        pg.check("input[name=jf_e][value=BIWEEKLY]")
        pg.check(".jf_a[value=purchase_order]")
        pg.check(".jf_a[value=stock_count]")
        pg.click("button:has-text('Create the record')")
        time.sleep(1.5)
        body = pg.inner_text("body")
        ck("his record opened", "Zahir Ahmad" in body and "JOIN-" in body)
        ck("no dialog was raised anywhere in the join", not dialogs, str(dialogs))
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        r = c.execute("SELECT person,role,employment,authorities,username FROM joiner "
                      "WHERE kind='JOIN'").fetchone()
        c.close()
        ck("EMPLOYMENT was recorded (the prompts always lost this)",
           r["employment"] == "BIWEEKLY", r["employment"])
        ck("the AUTHORITIES were recorded (the prompts always lost these)",
           set((r["authorities"] or "").split(",")) == {"self", "stock_count", "purchase_order"},
           r["authorities"])
        ck("the job was recorded", r["role"] == "purchase", r["role"])
        ck("the username was recorded", r["username"] == "zahir", r["username"])
        ck("no javascript error", not errs, "; ".join(errs))

        print("\n-- 4  EXIT IS A PICKER: nothing is typed -------------------------")
        pg.evaluate("goHome()")
        time.sleep(0.6)
        pg.click("button:has-text('Exit / leaver')")
        time.sleep(1.2)
        ck("no dialog was raised", not dialogs, str(dialogs))
        xp = pg.inner_text("#xp")
        ck("the real people are offered",
           all(u in xp for u in ("darpan", "shivani", "alisha", "shavez")), xp[:100])
        ck("there is no free-text name box on this screen",
           not pg.query_selector("#xp input"))
        n_start = len(pg.query_selector_all("#xp button.warn"))
        ck("each of them has a 'start exit' button", n_start >= 5, str(n_start))

        print("\n-- 5  START ONE, AND IT SHOWS AS IN PROGRESS ---------------------")
        pg.click("#xp tr:has-text('shavez') button")
        time.sleep(1.5)
        body = pg.inner_text("body")
        ck("the exit ladder opened for him", "EXIT" in body and "shavez" in body.lower())
        pg.evaluate("goHome()")
        time.sleep(0.5)
        pg.click("button:has-text('Exit / leaver')")
        time.sleep(1.2)
        xp = pg.inner_text("#xp")
        ck("he now reads as an exit in progress", "exit in progress" in xp, xp[:120])
        ck("and cannot be started twice",
           len(pg.query_selector_all("#xp button.warn")) == n_start - 1,
           str(len(pg.query_selector_all("#xp button.warn"))))
        ck("no javascript error at any point", not errs, "; ".join(errs))

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
