#!/usr/bin/env python3
"""walk_sr_s300.py -- S300 (D540): the live-shape walk of the staff self page.

THE KIT's staff_register.py, over a SCRATCH COPY of the live staff_register.db, with today's real
punch file and staff_master.csv read (never written). Every active staff login that the register
maps renders /register/me exactly as it will after the install; the refusals are posted against the
scratch copy and must write nothing; the doctor's review page must still answer.
Nothing live is touched: the database path must be under /tmp, and the kit's copy must be the one
imported. Prints no usernames and no numbers -- only counts.

Usage: SR_DB_PATH=/tmp/.../walk.db python3 walk_sr_s300.py <dir holding the kit staff_register.py> [<live app dir for its config>]
"""
import os
import sqlite3
import sys
import urllib.parse

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def main():
    kit = os.path.abspath(sys.argv[1])
    live = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else ""
    dbp = os.path.abspath(os.environ.get("SR_DB_PATH", ""))
    if not dbp.startswith("/tmp/"):
        print("FAIL 0: refusing a database outside /tmp")
        sys.exit(1)
    sys.path.insert(0, kit)
    if live:
        sys.path.insert(1, live)                   # staff_register_config and the SSO libraries
    os.chdir(kit)
    import staff_register as sr
    check("the kit copy is the module imported", os.path.dirname(os.path.abspath(sr.__file__)) == kit)
    check("the database is the scratch copy", os.path.abspath(sr.DB_PATH) == dbp)
    sr.init_db()                                   # migrations, on the scratch copy only
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    users = [r["username"] for r in con.execute(
        "SELECT username FROM staff WHERE active=1 AND COALESCE(username,'')<>'' ORDER BY staff_id")]
    check("at least one mapped staff login on the live register", len(users) > 0)
    c = sr.app.test_client()
    pages = can_present = punched = feed = overtime = other = 0
    for u in users:
        with c.session_transaction() as s:
            s["sr_user"] = u
            s["sr_role"] = "self"
        r = c.get("/register/me")
        t = r.get_data(as_text=True)
        tag = "staff login #%d" % (users.index(u) + 1)
        check(tag + ": the self page answers 200", r.status_code == 200)
        check(tag + ": Hinglish heading", "Meri attendance" in t)
        check(tag + ": no My month link", "My month" not in t and "me/month" not in t)
        check(tag + ": no Mark my exit", "Mark my exit" not in t)
        check(tag + ": no typed reason box", '<input name="reason"' not in t)
        pages += 1
        if "Mujhe present lagao" in t:
            check(tag + ": five tap reasons", t.count('type="radio" name="reason"') == len(sr.PRESENT_REASONS))
            can_present += 1
        elif "Aaj aapka punch" in t:
            punched += 1
        elif "jaankari abhi nahi mil rahi" in t:
            feed += 1
        else:
            other += 1
        if "Mark overtime" in t:
            check(tag + ": two buttons, Bhawna first", "Told Dr Bhawna" in t and "Told Dr Manoj" in t
                  and t.index("Told Dr Bhawna") < t.index("Told Dr Manoj") and "Told Reception" not in t)
            overtime += 1
    # refusals write nothing (scratch copy)
    u = users[0]
    with c.session_transaction() as s:
        s["sr_user"] = u
        s["sr_role"] = "self"
    np0 = con.execute("SELECT COUNT(*) FROM present_request").fetchone()[0]
    ne0 = con.execute("SELECT COUNT(*) FROM exit_request").fetchone()[0]
    r = c.post("/register/me/request", data={"reason": "typed words"})
    check("a typed present reason is refused", "c=err" in r.headers.get("Location", ""))
    r = c.post("/register/me/exit", data={"reason": "overtime", "told": "reception"})
    check("an overtime told to reception is refused", "c=err" in r.headers.get("Location", ""))
    r = c.post("/register/me/exit", data={"reason": "late_patients", "told": "manoj"})
    check("an old exit reason is refused", "c=err" in r.headers.get("Location", ""))
    msg = urllib.parse.unquote_plus(r.headers.get("Location", ""))
    check("the refusal reads Hinglish", "Ek karan chuniye" in msg)
    check("refusals wrote nothing", con.execute("SELECT COUNT(*) FROM present_request").fetchone()[0] == np0
          and con.execute("SELECT COUNT(*) FROM exit_request").fetchone()[0] == ne0)
    # the doctor's side still answers
    with c.session_transaction() as s:
        s["sr_user"] = "manoj"
        s["sr_role"] = "override"
    r = c.get("/register/review")
    check("the review page answers 200 for the doctor", r.status_code == 200)
    r = c.get("/register/")
    check("the register grid answers 200 for the doctor", r.status_code == 200)
    print("WALK OK — %d checks; %d staff self pages (%d can mark present, %d punched, %d feed down, %d other; "
          "%d show Mark overtime now)" % (N[0], pages, can_present, punched, feed, other, overtime))


if __name__ == "__main__":
    main()
