#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s757.py -- kit S757_XRAY_LAB_CHECK's walk on a MADE-UP clinic (invented names, 4-digit IDs built at run time).

  python3 walk_s757.py <dir with the files to test> <the app's own finance dir> <schema.sql or a finance.db to copy the schema of>
                       [--control]

The first dir is searched first (the kit's files, or the live ones for the control), the second for everything else
(slip_adjust, aaj_floor ...). A scratch database is made from the schema alone (no row is copied), filled with made-up rows,
and the real Flask blueprints are mounted on a test app with a stand-in login. Drive is stubbed (RECORDS_DRIVE_STUB).
The last line is 'WALK OK n/n' or 'WALK RED at check k: ...'; with --control the last line is 'CONTROL: red at check k ...'
when the files tested are NOT the kit's (the walk must go red on the live files), or 'CONTROL: GREEN -- wrong' otherwise.
"""
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
CONTROL = "--control" in sys.argv
NEW, FIN, SCHEMA = ARGS[0], ARGS[1], ARGS[2]
sys.path[:0] = [os.path.abspath(NEW), os.path.abspath(FIN)]
TMP = tempfile.mkdtemp(prefix="w757.")
DB = os.path.join(TMP, "walk.db")
STUB = os.path.join(TMP, "drive")
os.makedirs(STUB)
os.environ.update(RECORDS_NOW="2026-11-09T10:00:00", SLIP_NOW="2026-11-09T10:00:00", RECORDS_DRIVE_STUB=STUB, FINANCE_DB=DB,
                  CONSOLE_SNAPSHOT=os.path.join(TMP, "c.dat"), CONSOLE_BUILD_LOG=os.path.join(TMP, "c.log"))
N = {"n": 0}


def red(msg):
    print("WALK RED at check %d: %s" % (N["n"], msg))
    if CONTROL:
        print("CONTROL: red at check %d (%s)" % (N["n"], msg[:120]))
    sys.exit(1)


def check(cond, msg):
    N["n"] += 1
    if not cond:
        red(msg)


# ---------------------------------------------------------------- the scratch database: the schema, no rows
if SCHEMA.endswith(".sql"):
    ddl = open(SCHEMA, encoding="utf-8").read()
else:
    s = sqlite3.connect("file:%s?mode=ro" % SCHEMA, uri=True)
    ddl = "\n".join(r[0] + ";" for r in s.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
                                                  "ORDER BY type='table' DESC, name"))
    s.close()
con0 = sqlite3.connect(DB)
for stmt in ddl.split(";\n"):
    st = stmt.strip().rstrip(";")
    if st:
        try:
            con0.execute(st)
        except sqlite3.Error:
            pass
con0.commit()
con0.row_factory = sqlite3.Row


SEQ = {"n": 0}


def ins(table, **kw):
    cols = {r[1]: r for r in con0.execute("PRAGMA table_info(%s)" % table)}
    npk = sum(1 for r in cols.values() if r[5])
    for c, r in cols.items():                             # a NOT NULL column with no default gets a value (a key part: a fresh one)
        rowid = r[5] and npk == 1 and "INT" in (r[2] or "").upper()
        if c not in kw and (r[3] or r[5]) and r[4] is None and not rowid:
            SEQ["n"] += 1
            kw[c] = (SEQ["n"] if r[5] else 0) if "INT" in (r[2] or "").upper() else ("k%d" % SEQ["n"] if r[5] else "")
    kw = {k: v for k, v in kw.items() if k in cols}
    cur = con0.execute("INSERT INTO %s(%s) VALUES (%s)" % (table, ",".join(kw), ",".join("?" * len(kw))), tuple(kw.values()))
    return cur.lastrowid


def tid(prefix, width, n):                                 # a made-up Drive id, built here (the number gate)
    return prefix + str(n).rjust(width, "0")


B = 7000 + 0                                              # made-up IDs, built here: 7001 ...
I = {k: str(B + n) for k, n in (("meena", 1), ("ajay", 2), ("pooja", 3), ("kamla", 4), ("ram", 5), ("ghost", 6), ("hari", 7),
                                   ("sun1", 8), ("sun2", 9), ("twice", 10), ("early", 11))}
NM = {"meena": "Meena Sharma", "ajay": "Ajay Singh Rawat", "pooja": "Pooja Saxena", "kamla": "Kamla Devi", "ram": "Ram Prakash",
      "hari": "Hari Om Verma", "sun1": "Sunita Devi", "sun2": "Sunita Devi", "twice": "Unknown Twice", "early": "Lalit Mohan"}
D, DM1, DP1, TODAY = "2026-11-06", "2026-11-05", "2026-11-07", "2026-11-09"
for k, nm in NM.items():
    ins("patient_ref", clinic_id=I[k], name=nm, phone_last4="0000")
ins("patient_ref", clinic_id=I["ghost"], name="Unknown Person", phone_last4="0000")


def slip(day, cid, series, no, xrays=(), name=""):
    sid = ins("slip", series=series, slip_no=no, day=day, clinic_id=cid, name_seen=name, state="ok", logged_at=day + " 11:00:00")
    for k, x in enumerate(xrays):
        ins("slip_item", slip_id=sid, kind="xray", name=x, side="", price_p=30000, sort=k)
    return sid


slip(D, I["meena"], "xp", 501, ["Knee AP/Lat"], NM["meena"])
slip(D, I["ajay"], "xp", 502, ["Wrist PA"], NM["ajay"])
slip(D, I["pooja"], "opd", 801, [], NM["pooja"])
slip(DM1, I["kamla"], "xp", 499, ["LS Spine"], NM["kamla"])
slip(D, I["hari"], "opd", 802, [], NM["hari"])
slip(D, I["sun2"], "opd", 803, [], NM["sun2"])                       # a namesake visits; sun1 went straight to the lab
slip("2026-11-02", I["early"], "opd", 790, [], NM["early"])          # seen four days before the report
ins("clinic_day_line", business_date=D, clinic_id=I["ram"], patient=NM["ram"], section="xray", amount_p=30000, mode="cash")
ins("clinic_day_line", business_date=D, clinic_id=I["pooja"], patient=NM["pooja"], section="consult", amount_p=50000, mode="cash")

import records                                            # noqa: E402  (after the path and the environment)

records.ensure(con0)
records.xray_ensure(con0)
SA, SB, SC, SD = ("PIC%sAAAAAAAAAAAAAA" % x for x in "ABCD")
for sid, orig, ft in ((SA, "MEENA SHARMA.jpg", D + " 13:10:00"), (SB, "AJAY %s.jpg" % (I["ajay"][:2] + I["ajay"][3] + I["ajay"][2]), D + " 13:20:00"),
                      (SC, "SCAN.jpg", D + " 14:00:00"), (SD, "OLD.jpg", D + " 15:00:00")):
    ins("xray_filing", src_id=sid, orig_name=orig, file_time=ft, action="check", day=D, state="check", verdict="in the check folder",
        planned_at=D + " 17:40:00")
    open(os.path.join(STUB, sid), "wb").write(b"\xff\xd8\xff\xe0 made-up jpeg")
ins("record_check", key="xf:" + SD, kind="xray_file", clinic_id="", answer="not_xray", answered_by="alisha", answered_at=D + " 18:00:00")
con0.execute("INSERT INTO record_setting(key, value, set_at) VALUES ('xray_check_id','CHECKFOLDER0001','x')")
json.dump([{"id": s, "name": n, "mimeType": "image/jpeg", "modifiedTime": "2026-11-06T08:00:00.000Z"} for s, n in
           ((SA, "MEENA SHARMA.jpg"), (SB, "AJAY.jpg"), (SC, "SCAN.jpg"))], open(os.path.join(STUB, "list_CHECKFOLDER0001.json"), "w"))


def lab(cid, day, did, lname):
    fid = ins("record_file", clinic_id=cid, kind="blood", day=day, drive_id=did, file_name="%s · %s · %s · Blood Report.pdf" % (day, cid, lname),
              mime="application/pdf", source="lab_mail", source_ref="m%s#%s" % (did, did), state="ok", added_by="mailbox", added_at=day)
    open(os.path.join(STUB, did), "wb").write(b"%PDF-1.4 made-up")
    return fid


L1 = lab(I["pooja"], D, tid("LABPDF", 10, 1), "Mrs. Pooja Saxena")          # came that day, OPD only -> item, slip on D
L2 = lab(I["ghost"], D, tid("LABPDF", 10, 2), "Hari Om Verma")              # no visit on the ID; the name is Hari's -> wrong ID
L3 = lab(I["meena"], D, tid("LABPDF", 10, 3), "Mrs. Meena Sharma")          # a blood slip that week -> no item
L4 = lab(I["ajay"], DP1, tid("LABPDF", 10, 4), "Ajay Singh Rawat")
L5 = lab(I["sun1"], D, tid("LABPDF", 10, 5), "Mrs. Sunita Devi")       # her own name: never offered as a wrong ID
L6 = lab(I["twice"], D, tid("LABPDF", 10, 6), "Hari Om Verma")         # two reports that day: no move offered
L7 = lab(I["twice"], D, tid("LABPDF", 10, 7), "Hari Om Verma")
L8 = lab(I["early"], D, tid("LABPDF", 10, 8), "Lalit Mohan")           # the slip goes on the day he was seen          # came the day before -> item, slip on D
ins("blood_order", day=DM1, clinic_id=I["meena"], name_seen=NM["meena"], state="ok", outcome="", logged_by="shavez", logged_at=DM1)
ins("blood_order", day="2026-11-04", clinic_id=I["kamla"], name_seen=NM["kamla"], state="ok", outcome="", logged_by="shavez", logged_at="x")
# filed by themselves since 8-Nov; one before it; a no-slip X-ray (Pooja: OPD only)
F1 = ins("record_file", clinic_id=I["ram"], kind="xray", day=D, drive_id=tid("XRAYDEST", 8, 1), file_name="%s · %s · Ram Prakash · X-ray 1.jpg" % (D, I["ram"]),
         mime="image/jpeg", source="xray_inbox", source_ref=tid("SRCX", 12, 1), state="ok", added_by="mailbox", added_at="2026-11-08 18:00:00")
ins("xray_filing", src_id=tid("SRCX", 12, 1), orig_name="RAM %s.jpg" % I["ram"], file_time=D + " 12:00:00", action="file", clinic_id=I["ram"],
    day=D, state="done", file_id=F1, verdict="S752 re-try: ID %s is now on 06-Nov-2026's X-ray list" % I["ram"], done_at="2026-11-08 18:00:00")
F2 = ins("record_file", clinic_id=I["kamla"], kind="xray", day=DM1, drive_id=tid("XRAYDEST", 8, 2), file_name="%s · %s · Kamla Devi · X-ray 1.jpg" % (DM1, I["kamla"]),
         mime="image/jpeg", source="xray_inbox", source_ref=tid("SRCX", 12, 2), state="ok", added_by="mailbox", added_at="2026-11-01 18:00:00")
ins("xray_filing", src_id=tid("SRCX", 12, 2), orig_name="KAMLA.jpg", day=DM1, state="done", file_id=F2, verdict="S752 re-try: no ID on the picture",
    done_at="2026-11-01 18:00:00")
F3 = ins("record_file", clinic_id=I["pooja"], kind="xray", day=D, drive_id=tid("XRAYDEST", 8, 3), file_name="%s · %s · Pooja Saxena · X-ray 1.jpg" % (D, I["pooja"]),
         mime="image/jpeg", source="xray_inbox", source_ref=tid("SRCX", 12, 3), state="ok", added_by="mailbox", added_at="2026-11-08 18:30:00")
ins("xray_filing", src_id=tid("SRCX", 12, 3), orig_name="POOJA.jpg", day=D, state="done", file_id=F3, verdict="ID %s given by alisha" % I["pooja"],
    done_at="2026-11-08 18:30:00")
for did in (tid("XRAYDEST", 8, 1), tid("XRAYDEST", 8, 2), tid("XRAYDEST", 8, 3)):
    open(os.path.join(STUB, did), "wb").write(b"\xff\xd8\xff made-up")
con0.commit()

# ---------------------------------------------------------------- the app, a stand-in login, the real blueprints
from flask import Flask, jsonify  # noqa: E402

ROLES = {("checks", "alisha"): {"maker"}, ("checks", "shavez"): {"maker"}, ("checks", "manoj"): {"checker"},
         ("records", "manoj"): {"checker"}, ("slips", "shavez"): {"maker"}, ("slips", "alisha"): {"maker"},
         ("slips", "manoj"): {"checker"}}
WHO = {"u": "alisha"}


def require(*roles, unit="medical"):
    have = ROLES.get((unit, WHO["u"]), set())
    if not have.intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return {"user": WHO["u"], "role": "", "roles": sorted(have)}, None


def db():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c


app = Flask("w757")
records.init(app, db, require, None, unit="records")
import slip_log  # noqa: E402

slip_log.init(app, db, require, None, unit="slips")
cl = app.test_client()
if "--serve" in sys.argv:                                 # for a look in a browser: ?as=<login> picks the stand-in login
    from flask import request as _rq  # noqa: E402

    @app.before_request
    def _as():
        WHO["u"] = _rq.args.get("as") or _rq.cookies.get("as") or WHO["u"]

    @app.after_request
    def _keep(resp):
        if _rq.args.get("as"):
            resp.set_cookie("as", _rq.args.get("as"))
        return resp
    app.run(port=int(os.environ.get("PORT", "8757")), threaded=True)
    sys.exit(0)


def as_(u):
    WHO["u"] = u


def boot(html):
    m = re.search(r"var B=(\{.*?\}), IT=", html, re.S) or re.search(r"var B=(\{.*?\}), TAB=", html, re.S)
    return json.loads(m.group(1)) if m else None


def jscheck(html, tag):
    for k, sc in enumerate(re.findall(r"<script>(.*?)</script>", html, re.S)):
        p = os.path.join(TMP, "%s_%d.js" % (tag, k))
        open(p, "w").write(sc)
        try:
            r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
        except FileNotFoundError:                         # no node on this machine: the scripts were checked when the kit was built
            return ""
        if r.returncode != 0:
            return "%s script %d: %s" % (tag, k, (r.stderr or "")[-300:])
    return ""


# 1-6 · the staff page (the CONTROL goes red here: the live file has no photo screen)
as_("alisha")
r = cl.get("/finance/checks")
html = r.get_data(as_text=True)
check(r.status_code == 200, "Check karein answered %s" % r.status_code)
bt = boot(html)
check(bt is not None and "X-ray photo" in html, "Check karein is not the photo screen (the old list?)")
keys = [i["key"] for i in bt["items"]]
check(sorted(keys) == sorted(["xf:" + SA, "xf:" + SB, "xf:" + SC]) and not bt["lab"], "alisha's queue is %s" % keys)
check([i["day"] for i in bt["items"]] == sorted([i["day"] for i in bt["items"]], reverse=True), "not newest first")
check("Aur sawaal" in html and 'name="key" value="bo:2026-11-04:%s"' % I["kamla"] in html, "the old items are not under 'Aur sawaal'")
check(not jscheck(html, "staff"), jscheck(html, "staff"))
check("ae===document.body||ae.id==='yes'" in html and "!e.repeat" in html, "R3: Enter may file from another button")
# 7-12 · the picker
r = cl.get("/finance/checks/api/pats?sid=" + SA).get_json()
check(r["ok"] and r["pats"][0]["id"] == I["meena"] and r["pats"][0]["tag"] == "Naam milta hai" and r["pats"][0]["top"],
      "MEENA SHARMA.jpg: the top row is %s" % (r["pats"][:1],))
ids = [p["id"] for p in r["pats"]]
check(I["pooja"] in ids and I["ram"] in ids and I["hari"] in ids, "the day's OPD and Docterz patients are not all on the list: %s" % ids)
pj = next(p for p in r["pats"] if p["id"] == I["pooja"])
check(pj["nox"] and not next(p for p in r["pats"] if p["id"] == I["meena"])["nox"], "the 'no X-ray slip' flag is wrong")
km = next((p for p in r["pats"] if p["id"] == I["kamla"]), None)
check(km is not None and km["near"], "the day before's X-ray patient is not offered as 'near'")
r = cl.get("/finance/checks/api/pats?sid=" + SB).get_json()
check(r["pats"][0]["id"] == I["ajay"] and r["pats"][0]["tag"] == "Ek ank alag", "AJAY <swapped ID>.jpg: top row %s" % (r["pats"][:1],))
check(cl.get("/finance/checks/api/pats?sid=" + SD).status_code == 404, "an answered picture's patients are still served")
# 13-18 · the answers on a picture
r = cl.post("/finance/checks/api/answer", json={"key": "xf:" + SC, "a": "id_fixed", "new_id": I["pooja"], "check": 1}).get_json()
check(r["ok"] and r.get("check") and r["name"] == NM["pooja"] and r["nox"], "the ID check said %s" % r)
check(not con0.execute("SELECT 1 FROM record_check WHERE key=?", ("xf:" + SC,)).fetchone(), "a check wrote an answer")
r = cl.post("/finance/checks/api/answer", json={"key": "xf:" + SB, "a": "id_fixed", "new_id": I["ajay"]}).get_json()
row = con0.execute("SELECT * FROM record_check WHERE key=?", ("xf:" + SB,)).fetchone()
check(r["ok"] and row and row["answer"] == "id_fixed" and row["note"] == I["ajay"] and row["answered_by"] == "alisha", "Haan did not answer the S373 way")
r = cl.post("/finance/checks/api/answer", json={"key": "xf:" + SB, "a": "id_fixed", "new_id": I["ajay"]})
check(r.status_code == 409, "a second answer was taken (%s)" % r.status_code)
r = cl.post("/finance/checks/api/answer", json={"key": "xf:" + SC, "a": "id_fixed", "new_id": "9" * 4})
check(r.status_code == 400, "an unknown ID was taken")
items, notes = records.xray_actions(db())
check(any(i["id"] == SB and i["action"] == "file" and I["ajay"] in i["name"] for i in items), "the next run does not file the answered picture: %s" % items)
r = cl.post("/finance/checks/api/answer", json={"key": "xf:" + SC, "a": "not_xray"}).get_json()
check(r["ok"] and "xf:" + SC not in [i["key"] for i in boot(cl.get("/finance/checks").get_data(as_text=True))["items"]], "'Yeh X-ray nahi' did not close it")
# 19-22 · the photo door
con0.execute("UPDATE xray_filing SET state='check' WHERE src_id=?", (SA,))
con0.commit()
r = cl.get("/finance/checks/photo/" + SA)
check(r.status_code == 200 and r.data.startswith(b"\xff\xd8") and r.mimetype == "image/jpeg", "the open picture is not served (%s)" % r.status_code)
check(cl.get("/finance/checks/photo/" + SC).status_code == 404, "an answered picture is still served")
as_("bhati")
check(cl.get("/finance/checks/photo/" + SA).status_code == 403, "a login with no Check karein role got the picture")
check(cl.get("/finance/checks/api/pats?sid=" + SA).status_code == 403, "a login with no role got the day's patients")
# 23-32 · the lab queue
as_("shavez")
html = cl.get("/finance/checks").get_data(as_text=True)
bt = boot(html)
labs = {i["key"]: i for i in bt["items"] if i["kind"] == "lab"}
extra = {k: labs.pop(k) for k in ["ln:%s:%s" % (D, I[x]) for x in ("sun1", "twice", "early")] if k in labs}
check(len(extra) == 3 and not extra["ln:%s:%s" % (D, I["sun1"])]["wrong"], "R1: her own name was offered as a wrong ID: %s" % extra.get("ln:%s:%s" % (D, I["sun1"])))
check(not extra["ln:%s:%s" % (D, I["twice"])]["wrong"] and extra["ln:%s:%s" % (D, I["twice"])]["n"] == 2, "R2: a move offered for two reports")
check(extra["ln:%s:%s" % (D, I["early"])]["slip_day"] == "2026-11-02", "R5: the slip day is %s" % extra["ln:%s:%s" % (D, I["early"])]["slip_day"])
as_("alisha")
check("s757l" not in cl.get("/finance/slips/desk?lab=" + "ln:%s:%s" % (D, I["early"])).get_data(as_text=True), "R4: alisha got a lab item on the desk")
check(not cl.post("/finance/slips/desk/api/blood", json={"clinic_id": I["early"], "lab_key": "ln:%s:%s" % (D, I["early"])}).get_json()["ok"],
      "R4: alisha wrote a back-dated slip")
as_("shavez")
for k in extra:
    cl.post("/finance/checks/api/answer", json={"key": k, "a": "direct_lab"})
check(bt["lab"] and set(labs) == {"ln:%s:%s" % (D, I["pooja"]), "ln:%s:%s" % (D, I["ghost"]), "ln:%s:%s" % (DP1, I["ajay"])},
      "shavez's lab items are %s" % sorted(labs))
p_it, g_it, a_it = labs["ln:%s:%s" % (D, I["pooja"])], labs["ln:%s:%s" % (D, I["ghost"])], labs["ln:%s:%s" % (DP1, I["ajay"])]
check(p_it["note"].startswith("Isi din") and p_it["slip_day"] == D and not p_it["wrong"], "Pooja's item: %s" % p_it)
check(a_it["note"].startswith("Ek din pehle") and a_it["slip_day"] == D, "Ajay's item: %s" % a_it)
check(g_it["wrong"] and g_it["sug"] == I["hari"], "the wrong-ID item: %s" % g_it)
check(cl.get("/finance/checks/report/%d" % L1).status_code == 200, "shavez cannot open the open report")
check(cl.get("/finance/checks/report/%d" % L3).status_code == 404, "a report with a blood slip is served from the queue")
as_("alisha")
check(cl.get("/finance/checks/report/%d" % L1).status_code == 403, "alisha got a lab report")
check(cl.post("/finance/checks/api/answer", json={"key": p_it["key"], "a": "direct_lab"}).status_code == 403, "alisha answered a lab item")
as_("shavez")
r = cl.post("/finance/checks/api/answer", json={"key": g_it["key"], "a": "moved", "new_id": I["pooja"]})
check(r.status_code == 400, "a move to an ID the item does not suggest was taken")
r = cl.post("/finance/checks/api/answer", json={"key": g_it["key"], "a": "moved", "new_id": I["hari"]}).get_json()
check(r["ok"] and con0.execute("SELECT clinic_id FROM record_file WHERE id=?", (L2,)).fetchone()[0] == I["hari"], "the report did not move")
# 33-38 · the Parchi desk: the strip and the blood slip from a lab item
html = cl.get("/finance/slips/desk?lab=" + p_it["key"]).get_data(as_text=True)
check("s757s" in html and "s757l" in html and NM["pooja"] in html, "the desk carries no strip / no lab slip box")
check(not jscheck(html, "desk"), jscheck(html, "desk"))
r = cl.post("/finance/slips/desk/api/blood", json={"clinic_id": I["ajay"], "lab_key": p_it["key"]}).get_json()
check(not r["ok"], "the desk wrote a slip for another patient on a lab key")
r = cl.post("/finance/slips/desk/api/blood", json={"clinic_id": I["pooja"], "lab_key": p_it["key"]}).get_json()
bo = con0.execute("SELECT day FROM blood_order WHERE clinic_id=? AND state='ok'", (I["pooja"],)).fetchall()
check(r["ok"] and [x[0] for x in bo] == [D], "the lab slip was not written on the visit day: %s %s" % (r, [tuple(x) for x in bo]))
keys = [i["key"] for i in boot(cl.get("/finance/checks").get_data(as_text=True))["items"]]
check(p_it["key"] not in keys and g_it["key"] not in keys, "a saved blood slip / a move did not close the item: %s" % keys)
r = cl.post("/finance/slips/desk/api/blood", json={"clinic_id": I["hari"]}).get_json()
check(r["ok"] and con0.execute("SELECT day FROM blood_order WHERE clinic_id=?", (I["hari"],)).fetchone()[0] == TODAY, "the desk's own blood slip changed")
# 39-41 · Aaj ka kaam's door
m = cl.get("/finance/checks/api/mine").get_json()
check(m["ok"] and m["open"] == m["xray"] + m["lab"] + m["xbill"] and m["lab"] == 2 and m["xray"] == 1 and "baaki" in m["text"], "shavez's count: %s" % m)
check("ln:%s:%s" % (D, I["hari"]) in [i["key"] for i in boot(cl.get("/finance/checks").get_data(as_text=True))["items"]],
      "the moved report is not now asked of its right patient (no blood slip on Hari's ID)")
as_("alisha")
m = cl.get("/finance/checks/api/mine").get_json()
check(m["lab"] == 0 and m["open"] == 1, "alisha's count: %s" % m)
as_("bhati")
check(cl.get("/finance/checks/api/mine").status_code == 403, "a login with no role got a count")
# 42-52 · his page
as_("alisha")
check(cl.get("/finance/records/xray-check").status_code == 403, "alisha opened the owner's page")
check(cl.post("/finance/records/xray-check/api/answer", json={"key": "nx:%s:%s" % (D, I["pooja"]), "a": "tell_shavez"}).status_code == 403,
      "alisha answered on the owner's door")
as_("manoj")
html = cl.get("/finance/records/xray-check").get_data(as_text=True)
ob = boot(html)
check(ob is not None and "Waiting for staff" in html and not jscheck(html, "owner"), "his page: %s" % jscheck(html, "owner"))
check([i["fid"] for i in ob["filed"]] == [F3, F1] or sorted(i["fid"] for i in ob["filed"]) == sorted([F1, F3]),
      "filed since 8-Nov: %s" % [i["fid"] for i in ob["filed"]])
check(any("Alisha" in i["detail"] for i in ob["filed"]) and any("its ID came" in i["detail"] for i in ob["filed"]), "how each was filed")
check([i["cid"] for i in ob["nox"]] == [I["pooja"]], "X-ray with no X-ray slip: %s" % [i["cid"] for i in ob["nox"]])
check(len(ob["wait"]) == 1 and len(ob["lab"]) == 2, "waiting %d, lab %d" % (len(ob["wait"]), len(ob["lab"])))
r = cl.post("/finance/records/xray-check/api/answer", json={"key": ob["nox"][0]["key"], "a": "tell_shavez"}).get_json()
check(r["ok"] and not boot(cl.get("/finance/records/xray-check").get_data(as_text=True))["nox"], "'Missed -- tell Shavez' did not close it")
as_("shavez")
xb = [i for i in boot(cl.get("/finance/checks").get_data(as_text=True))["items"] if i["kind"] == "xbill"]
check(len(xb) == 1 and xb[0]["cid"] == I["pooja"], "Shavez did not get the X-ray to bill: %s" % xb)
r = cl.post("/finance/checks/api/answer", json={"key": xb[0]["key"], "a": "slip_made"}).get_json()
check(r["ok"] and not [i for i in boot(cl.get("/finance/checks").get_data(as_text=True))["items"] if i["kind"] == "xbill"], "'Parchi bana di' did not close it")
as_("manoj")
r = cl.post("/finance/records/xray-check/api/answer", json={"key": "mv:%d" % F1, "a": "moved", "new_id": I["kamla"]}).get_json()
f = con0.execute("SELECT clinic_id, note FROM record_file WHERE id=?", (F1,)).fetchone()
check(r["ok"] and f[0] == I["kamla"] and "moved from %s" % I["ram"] in f[1], "the move: %s %s" % (r, tuple(f)))
check(cl.get("/finance/records/xray-check/photo/" + SA).status_code == 200, "his photo door")
r = cl.post("/finance/records/xray-check/api/answer", json={"key": "xf:" + SA, "a": "id_fixed", "new_id": I["meena"]}).get_json()
check(r["ok"] and con0.execute("SELECT answered_by FROM record_check WHERE key=?", ("xf:" + SA,)).fetchone()[0] == "manoj", "he cannot file a picture")
# 53-56 · the old list, the old answer, the records home, the fallback
as_("alisha")
html = cl.get("/finance/checks?list=1").get_data(as_text=True)
check('form class="ck"' in html and "var B=" not in html, "?list=1 is not the old list")
r = cl.post("/finance/checks/answer", data={"key": "bo:2026-11-04:%s" % I["kamla"], "a": "asked"})
check(r.status_code == 303 and con0.execute("SELECT answer FROM record_check WHERE key=?", ("bo:2026-11-04:%s" % I["kamla"],)).fetchone()[0] == "asked",
      "the old answer door")
as_("manoj")
check("/finance/records/xray-check" in cl.get("/finance/records").get_data(as_text=True), "the records home has no way to his page")
import check_screens  # noqa: E402

c = check_screens.counts(db())
check(c == {"filed": 2, "wait": 0, "nox": 0, "lab": 2, "xbill": 0}, "counts: %s" % c)
# 57-60 · his console line, Aaj ka kaam, the grants
import owner_console  # noqa: E402

lines = owner_console.sec_papers(db(), {"clinic_day": D})["lines"]
ln = [x for x in lines if "photos & lab reports:" in x.get("text", "")]
check(ln and ln[0].get("href") == "/finance/records/xray-check", "his console has no line: %s" % [x.get("text") for x in lines])
dj = json.load(open(os.path.join(NEW, "aaj_duties.json.kit") if os.path.exists(os.path.join(NEW, "aaj_duties.json.kit"))
                    else os.path.join(NEW, "aaj_duties.json")))
du = [x for x in dj["extra"] if x["id"] == "shavez.check_karein"]
check(du and du[0]["fetch"]["url"] == "/finance/checks/api/mine" and du[0]["kind"] == "fetch", "the duty: %s" % du)
import aaj_seed  # noqa: E402

sh = next(p for p in aaj_seed.PEOPLE if p["key"] == "shavez")
check(any(l["id"] == "shavez.check_karein" and l["on"] and l["when"] == "first" for l in sh["lines"]), "Shavez's seed line")
tg = os.path.join(NEW, "tile_grants.json.kit") if os.path.exists(os.path.join(NEW, "tile_grants.json.kit")) else os.path.join(NEW, "tile_grants.json")
g = json.load(open(tg))
check(g["version"] == 44 and "Marg Purchases" not in g["users"]["manoj"]["mask"] and "Order Medicines" in g["users"]["manoj"]["mask"],
      "the grants: version %s, mask %s" % (g["version"], g["users"]["manoj"]["mask"]))
print("WALK OK %d/%d" % (N["n"], N["n"]))
if CONTROL:
    print("CONTROL: GREEN -- wrong, the control must go red")
    sys.exit(1)
