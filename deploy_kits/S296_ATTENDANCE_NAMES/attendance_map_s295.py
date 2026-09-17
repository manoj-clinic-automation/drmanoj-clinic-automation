#!/usr/bin/env python3
"""attendance_map_s295.py -- READ-ONLY. Which portal logins open their own attendance page.

The 'Meri attendance' tile (S295) goes to /register/me, which shows a login ITS OWN staff row. A login
maps to a staff row by staff.username, else by an unambiguous first name (staff_register.py S196). This
report lists every active staff/manager login and says, for each, whether that page will open for it.
It writes nothing, anywhere. Names only -- never a number (F-31).
Usage: attendance_map_s295.py [USERS_JSON] [REGISTER_DB]
"""
import json
import sqlite3
import sys

users_path = sys.argv[1] if len(sys.argv) > 1 else "/root/portal/clinic_users.json"
db_path = sys.argv[2] if len(sys.argv) > 2 else "/root/staff_register/staff_register.db"
store = json.load(open(users_path, encoding="utf-8"))
con = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
con.row_factory = sqlite3.Row
staff = list(con.execute("SELECT staff_id, name, COALESCE(username,'') AS un FROM staff WHERE active=1"))


def maps(login):
    u = login.strip().lower()
    for s in staff:
        if s["un"].strip().lower() == u:
            return s["name"], "username"
    hits = [s for s in staff if (s["name"] or "").strip().lower().split()[:1] == [u]]
    if len(hits) == 1:
        return hits[0]["name"], "first name"
    if len(hits) > 1:
        return None, "first name shared by %d staff -- set staff.username" % len(hits)
    return None, "no staff row with this username or first name"


ok = bad = 0
print("login        role      opens 'Meri attendance'?")
for login, u in sorted(store.get("users", {}).items()):
    if not u.get("active", False) or u.get("role") not in ("staff", "manager"):
        continue
    name, how = maps(login)
    if name:
        ok += 1
        print("%-12s %-9s yes -> %s (by %s)" % (login, u.get("role"), name, how))
    else:
        bad += 1
        print("%-12s %-9s NO  -- %s" % (login, u.get("role"), how))
mapped_logins = {l.lower() for l in store.get("users", {})}
unlisted = [s["name"] for s in staff if s["un"].lower() not in mapped_logins
            and (s["name"] or "").strip().lower().split()[:1][0:1] and (s["name"] or "").strip().lower().split()[0] not in mapped_logins]
print("summary: %d open their page, %d do not; staff with no portal login yet: %d%s"
      % (ok, bad, len(unlisted), (" (" + ", ".join(unlisted) + ")") if unlisted else ""))
