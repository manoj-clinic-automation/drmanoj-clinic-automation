#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_joiner_login_s222.py -- a REAL BROWSER creating a real login, and using it.

The standing rule for this project's pages since S214 v5 shipped with dead taps. Here it earns
its keep twice over, because the fault being fixed IS a screen that told the truth's opposite.

It mounts the PATCHED joiner_app on a throwaway database, serves the PATCHED staff_manage.html,
points the portal user store at a temp file, and then drives the page with chromium:

  1  a joiner with no login  -> the page must WARN, not print credentials
  2  tap "login banao"       -> the role list must come from the STORE, and the login is made
  3  and then the proof that F-295 never had: clinic_users.verify_password() signs in as him
  4  the WhatsApp button     -> a wa.me link, with the message in it and NO number
  5  a disabled login        -> "BAND", not a green tick

Runs OFFLINE. The VPS has no browser.

    python3 -B RENDER_TEST_joiner_login_s222.py <dir with patched joiner_app.py + staff_manage.html>
"""
import datetime as dt
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.parse

FIN = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
PORT = 8753
FAILED, PASSED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail else ""))


def main():
    sys.path.insert(0, FIN)
    tmp = tempfile.mkdtemp(prefix="s222_login_")
    portal = os.path.join(tmp, "portal")
    os.makedirs(portal)
    # the portal's own module, beside its own store -- exactly the live shape
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

    db = os.path.join(tmp, "finance.db")
    con = sqlite3.connect(db)
    con.executescript(open(os.path.join(FIN, "joiner_schema.sql"), encoding="utf-8").read())
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    today = dt.date.today().isoformat()
    con.execute("INSERT INTO joiner (ref,kind,person,role,status,username,employment,"
                "authorities,opened_on,opened_by,created_at,updated_at) VALUES "
                "('JOIN-2026-0099','JOIN','Zahir Test','purchase','ACCOUNT_CREATED','zahir',"
                "'BIWEEKLY','self',?,'Dr Manoj',?,?)", (today, now, now))
    jid = con.execute("SELECT id FROM joiner WHERE ref='JOIN-2026-0099'").fetchone()[0]
    for s in ("DECIDED", "ACCOUNT_CREATED"):
        con.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by) "
                    "VALUES (?,?,?,'Dr Manoj')", (jid, s, today))
    con.commit()
    con.close()

    from flask import Flask, jsonify, Response
    import joiner_app as JA
    src = open(JA.__file__, encoding="utf-8").read()
    print("-- 0  what is under test ------------------------------------------")
    ck("joiner_app carries the S222 routes", "S222 PORTAL USER" in src)
    page_html = open(os.path.join(FIN, "staff_manage.html"), encoding="utf-8").read()
    ck("the page carries the S222 script", "S222 star-1-3" in page_html)
    ck("the page no longer asserts a password unconditionally",
       "pehla password: <b>'+\n   j.username+'1234</b>" not in page_html)

    app = Flask("s222_login")

    def _db():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    def _require(*roles, **kw):
        """finance_app's shape: a USER DICT."""
        return dict(user="manoj", role="doctor", roles=["checker"]), None

    # THE LIVE WIRING, not a convenience. staff_pages.joiner_require() is the
    # adapter that turns finance_app's user dict into the plain name the
    # register binds straight into SQL. Mounting joiner_app without it is how
    # v1 of this test produced a false RED -- and it is the SAME crash
    # ("type 'dict' is not supported") that S208's own selftest caught, in the
    # same file, for the same reason. A test that does not wire the app the way
    # the box wires it is not a test of the box.
    import staff_pages as SP
    JA.init(app, _db, SP.joiner_require(_require), url_prefix="/finance/staff")

    @app.route("/finance/staff/")
    def page():
        return Response(page_html, mimetype="text/html")

    threading.Thread(target=lambda: app.run(port=PORT, threaded=True,
                                            use_reloader=False), daemon=True).start()
    time.sleep(1.5)

    from playwright.sync_api import sync_playwright
    url = "http://127.0.0.1:%d/finance/staff/" % PORT
    chrome = os.environ.get("PW_CHROME",
                            "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome)
        pg = b.new_page(viewport={"width": 390, "height": 800})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url, wait_until="networkidle")
        pg.evaluate("localStorage.setItem('staff_by','Dr Manoj')")

        def open_rec():
            pg.evaluate("showRec('JOIN-2026-0099')")
            time.sleep(1.0)
            return pg.inner_text("body")

        print("\n-- 1  NO LOGIN YET: the page must warn, not print credentials ----")
        body = open_rec()
        ck("it says the login does not exist yet", "bana NAHIN hai" in body)
        ck("it does NOT print the old 'pehla password' claim",
           "pehla password" not in body)
        # scoped to #loginState: `button.btn.warn` alone also matches the home
        # page's hidden "Vidaai" button, and a selector that matches the wrong
        # element is a green check that proves nothing.
        ck("the 'login banao' button is on screen",
           bool(pg.query_selector("#loginState button")))
        ck("no javascript error", not errs, "; ".join(errs))

        print("\n-- 2  TAP IT: the role list comes from the store, not from code --")
        pg.click("#loginState button")
        time.sleep(1.2)
        picks = [e.inner_text().strip()
                 for e in pg.query_selector_all("#rolePick button")]
        ck("the choices offered are the STORE's own roles",
           sorted(picks) == ["doctor", "manager", "staff"], str(picks))
        pg.click("#rolePick button:has-text('manager')")
        time.sleep(1.8)
        body = pg.inner_text("body")
        ck("the line now says the login exists", "ban chuka hai" in body)
        ck("and names the role it was given", "(manager)" in body)
        ck("no javascript error", not errs, "; ".join(errs))

        print("\n-- 3  THE PROOF F-295 NEVER HAD: sign in as him ------------------")
        sys.path.insert(0, portal)
        import clinic_users as CU
        role = CU.verify_password(store, "zahir", "zahir1234")
        ck("clinic_users.verify_password() accepts the printed password", role == "manager",
           str(role))
        ck("the store now holds exactly one user",
           len(CU.list_users(store)) == 1, str(CU.list_users(store)))
        ck("a backup of the store was taken beside it",
           any(x.startswith("clinic_users.json.bak_S222_") for x in os.listdir(portal)),
           str(os.listdir(portal)))

        print("\n-- 4  THE WHATSAPP MESSAGE FINALLY HAS SOMEWHERE TO GO -----------")
        pg.click("button.btn:has-text('WhatsApp message dikhao')")
        time.sleep(1.0)
        a = pg.query_selector("#wa a")
        href = a.get_attribute("href") if a else ""
        ck("a send link is rendered", bool(a))
        ck("it is a wa.me link", href.startswith("https://wa.me/?text="))
        ck("the message text is in it",
           "Zahir" in urllib.parse.unquote(href) and "zahir1234" in urllib.parse.unquote(href))
        ck("NO phone number is in the link (F-185)",
           "wa.me/?text=" in href and not any(
               ch.isdigit() for ch in href.split("?text=")[0]))
        ck("no javascript error", not errs, "; ".join(errs))

        print("\n-- 5  A DISABLED LOGIN READS AS DISABLED, NOT AS A TICK ----------")
        CU.set_active(store, "zahir", False)
        body = open_rec()
        ck("it says BAND", "BAND" in body)
        ck("it does not claim the login is ready", "ban chuka hai" not in body)
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
