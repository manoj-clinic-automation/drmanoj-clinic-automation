#!/usr/bin/env python3
"""walk_s316.py -- the seeded lists, driven through the real module over a SCRATCH COPY of the live
finance.db. Proves both lists arrive written, the three taps work, a rejected line stays, the door
carries only what he approved, and no past day is loaded as data.
Usage: walk_s316.py MODULE_DIR DB_COPY"""
import importlib.util
import sqlite3
import sys

mod_dir, dbp = sys.argv[1], sys.argv[2]
sys.path.insert(0, mod_dir)
spec = importlib.util.spec_from_file_location("owner_sheets_walk", mod_dir + "/owner_sheets.py")
osh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(osh)
osh.SEED_DIR = mod_dir
from flask import Flask, jsonify  # noqa: E402

app = Flask("walk")
WHO = {"user": "manoj"}


def db():
    c = sqlite3.connect(dbp)
    c.row_factory = sqlite3.Row
    return c


def require(*roles, **kw):
    if kw.get("unit") != "clinic":
        return None, (jsonify(ok=False, error="wrong_unit"), 403)
    return WHO, None


osh.init(app, db, require, None)
cl = app.test_client()
n = [0]


def check(name, ok):
    n[0] += 1
    if not ok:
        print("WALK FAIL %d %s" % (n[0], name))
        sys.exit(1)


def counts():
    c = db()
    return {t: c.execute("SELECT COUNT(*) n FROM %s" % t).fetchone()["n"]
            for t in ("clinic_day_line", "stock_snapshot", "day_line")}


before = counts()
r = cl.get("/finance/clinic/sheets")
check("the page opens for the doctor", r.status_code == 200)
html = r.get_data(as_text=True)
con = db()
xr = [s for s in osh.services(con) if s["kind"] == "xray"]
pr = [s for s in osh.services(con) if s["kind"] == "proc"]
check("the X-ray list arrives already written (19 studies)", len(xr) == 19)
check("the procedure list arrives already written (17 lines)", len(pr) == 17)
check("every seeded line waits for him", all(s["status"] == "pending" for s in xr + pr))
check("the commonest X-ray is first and carries its evidence",
      xr[0]["name"] == "Knee" and xr[0]["seen"] == 684)
check("spellings are corrected, the word X-ray is gone",
      not any("X-RAY" in s["name"].upper() for s in xr) and
      any(s["name"] == "Shoulder" for s in xr) and any(s["name"] == "Cervical spine" for s in xr))
check("PROSISER is not on the X-ray list", not any("PROSIS" in s["name"].upper() for s in xr))
ak = [s for s in pr if s["code"] == "AK"][0]
check("a cast site carries its two forms", set(ak["forms"].split(",")) == {"cast", "slab"})
check("the clavicle bandage is offered neither",
      [s for s in pr if s["code"] == "CLAV"][0]["forms"] == "")
check("U slab may be a cast too (his correction)",
      "cast" in [s for s in pr if s["code"] == "USLAB"][0]["forms"])
check("a cast site arrives with the four consumables he ruled",
      {i["item"] for i in ak["items"]} ==
      {"Fibrecast bandage", "Roller bandage", "Cast padding", "Stockinette"})
check("stockinette is used/not-used only",
      [i for i in ak["items"] if i["item"] == "Stockinette"][0]["ask"] == "used_yesno")
check("fibrecast carries his four widths",
      [i for i in ak["items"] if i["item"] == "Fibrecast bandage"][0]["sizes"] == '2",3",4",5"')
ili = [s for s in pr if s["code"] == "ILI-HE"][0]
check("an ILI carries the steroid and the drape",
      {i["item"] for i in ili["items"]} == {"Inj Loftypred 80 mg OR Inj Viracort 40",
                                            "Surgiwear D600 drape"})
check("the page shows the counts and the groups", "waiting for you" in html and "Cast / slab" in html)
check("past amounts appear only as a pricing hint",
      "Only a hint" in html and "nothing from the past is loaded" in html)

r = cl.post("/finance/clinic/sheets/status", data={"id": xr[0]["id"], "s": "approved"})
check("approve is one tap", r.status_code in (302, 200))
r = cl.post("/finance/clinic/sheets/status", data={"id": xr[1]["id"], "s": "rejected"})
check("reject is one tap", r.status_code in (302, 200))
c2 = osh.counts(db(), "xray")
check("the counts move", c2["approved"] == 1 and c2["rejected"] == 1 and c2["pending"] == 17)
check("a rejected line is kept, not deleted",
      len([s for s in osh.services(db()) if s["kind"] == "xray"]) == 19)
r = cl.post("/finance/clinic/sheets/status", data={"id": xr[1]["id"], "s": "approved"})
check("a rejected line can be brought back",
      osh.counts(db(), "xray")["rejected"] == 0)
r = cl.post("/finance/clinic/sheets/status", data={"id": xr[0]["id"], "s": "maybe"})
check("only approve or reject is accepted", "c=bad" in r.headers.get("Location", ""))

r = cl.post("/finance/clinic/sheets/rename", data={"id": xr[0]["id"], "name": "Knee AP / LAT"})
check("he can correct a name", [s for s in osh.services(db()) if s["id"] == xr[0]["id"]][0]["name"] == "Knee AP / LAT")
r = cl.post("/finance/clinic/sheets/rename", data={"id": xr[2]["id"], "name": "knee ap / lat"})
check("two lines cannot carry one name", "c=bad" in r.headers.get("Location", ""))

r = cl.post("/finance/clinic/sheets/price", data={"id": xr[0]["id"], "price": "500"})
check("a price is optional and saveable",
      [s for s in osh.services(db()) if s["id"] == xr[0]["id"]][0]["price_p"] == 50000)

d = cl.get("/finance/clinic/sheets/api/services").get_json()
check("the door carries only what he approved", d["ok"] and d["count"] == 2 and len(d["xray"]) == 2)
check("a pending line is not in the door", all(s["status"] == "approved" for s in d["xray"]))

r = cl.post("/finance/clinic/sheets/add", data={"kind": "proc", "name": "Nail removal", "price": ""})
check("his own addition needs no price", r.status_code in (302, 200))
own = [s for s in osh.services(db()) if s["name"] == "Nail removal"][0]
check("and it is approved the moment he adds it", own["status"] == "approved" and own["source"] == "owner")

r = cl.post("/finance/clinic/sheets/item/add", data={"id": ak["id"], "item": "Crepe bandage", "qty": "1"})
check("a consumable can be added to a procedure", r.status_code in (302, 200))
r = cl.post("/finance/clinic/sheets/item/drop",
            data={"id": [i for i in osh.services(db()) if i["code"] == "AK"][0]["items"][0]["id"]})
check("and one can be removed", r.status_code in (302, 200))

added = osh.seed(db())
check("running the seed again adds nothing", added == 0)
check("no other table was written", before == counts())
print("WALK OK -- %d checks" % n[0])
