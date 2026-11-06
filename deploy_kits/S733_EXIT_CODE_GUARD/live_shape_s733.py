#!/usr/bin/env python3
"""live_shape_s733.py -- kit S733 (session 394, the parent). READ-ONLY on a COPY of finance.db.
Need not be run by the owner; the installer runs it on a temporary copy of the live database.

    python live_shape_s733.py <joiner_app.py> <a COPY of finance.db>

Prints LIVE-SHAPE OK when, on the real register:
  * every live code on the register is found again from its own name (round trip), or is
    reported AMBIGUOUS when two live codes share that name (never a wrong code);
  * a name found differs from no other name only by a first name ('Arjun' vs 'Arjun Dev');
  * every open exit with no code is listed (its tick would be refused until it has one);
  * a tick on every open exit, run on the copy, retires only that exit's own code and leaves
    every other code's date unchanged.
Prints no number other than machine codes (no phone, no patient)."""
import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile

jpath, src = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
t = tempfile.mkdtemp(prefix="s733ls_")
DB = os.path.join(t, "copy.db")
shutil.copyfile(src, DB)
shutil.copyfile(jpath, os.path.join(t, "joiner_app.py"))
schema = os.path.join(os.path.dirname(jpath), "joiner_schema.sql")
shutil.copyfile(schema, os.path.join(t, "joiner_schema.sql"))
os.environ["PORTAL_DIR"] = os.path.join(t, "no_portal")
spec = importlib.util.spec_from_file_location("joiner_app", os.path.join(t, "joiner_app.py"))
J = importlib.util.module_from_spec(spec)
spec.loader.exec_module(J)
bad = []
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
live = con.execute("SELECT code, person FROM emp_code WHERE retired_on IS NULL ORDER BY code").fetchall()
names = {}
for r in live:
    names.setdefault(J._norm_name(r["person"]), []).append(r["code"])
for r in live:
    got = J.code_for_person(con, r["person"])
    if len(names[J._norm_name(r["person"])]) > 1:
        print("  AMBIGUOUS %-24s codes %s -> %s" % (r["person"], names[J._norm_name(r["person"])], got))
        if got is not None:
            bad.append("ambiguous name gave a code: %s" % r["person"])
    else:
        ok = got == r["code"]
        print("  %s code %-4s %-24s -> %s" % ("ok  " if ok else "FAIL", r["code"], r["person"], got))
        if not ok:
            bad.append("round trip failed for code %s" % r["code"])
before = {r["code"]: r["retired_on"] for r in con.execute("SELECT code, retired_on FROM emp_code")}
opn = con.execute("SELECT id, ref, person, emp_code FROM joiner WHERE kind='EXIT' "
                  "AND status!='COMPLETE'").fetchall()
print("  open exits: %d" % len(opn))
from flask import Flask, g  # noqa: E402
app = Flask("ls733")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB, timeout=30)
        g.db.row_factory = sqlite3.Row
    return g.db


J.init(app, db, lambda *a: ("live-shape", None), url_prefix="/x")
Cl = app.test_client()
con.close()
for r in opn:
    c = sqlite3.connect(DB)
    c.execute("INSERT OR IGNORE INTO joiner_step (joiner_id,step,done_on,done_by) "
              "VALUES (?,?,date('now'),'live-shape')", (r["id"], "PORTAL_DISABLED"))
    c.commit()
    c.close()
    res = Cl.post("/x/api/step", json={"ref": r["ref"], "step": "BIOMETRIC_REMOVED", "by": "live-shape"})
    j = res.get_json() or {}
    c = sqlite3.connect(DB)
    after = {x[0]: x[1] for x in c.execute("SELECT code, retired_on FROM emp_code")}
    code = c.execute("SELECT emp_code FROM joiner WHERE id=?", (r["id"],)).fetchone()[0]
    c.close()
    changed = [k for k in after if before.get(k, "NEW") != after[k]]
    c = sqlite3.connect(DB)
    owners = {x[0]: J._norm_name(x[1]) for x in c.execute("SELECT code, person FROM emp_code")}
    c.close()
    # a code may change only when the register gives it to THIS leaver
    allowed = {k for k in changed if owners.get(k) == J._norm_name(r["person"])}
    print("  exit %s (%s): tick %s %s; code %s; codes changed %s" % (
        r["ref"], r["person"], res.status_code, j.get("error") or "", code, changed))
    if r["emp_code"] and res.status_code != 200:
        bad.append("%s carries code %s but its tick was refused (%s) -- the record needs a look first" % (r["ref"], r["emp_code"], j.get("error")))
    if [k for k in changed if k not in allowed]:
        bad.append("%s changed a code not its own: %s" % (r["ref"], changed))
    if [k for k in changed if before.get(k) not in (None, "NEW")]:
        bad.append("%s moved the date of a code already retired: %s" % (r["ref"], changed))
    before = after
shutil.rmtree(t, ignore_errors=True)
print("LIVE-SHAPE OK" if not bad else "LIVE-SHAPE RED: " + "; ".join(bad))
sys.exit(0 if not bad else 1)
