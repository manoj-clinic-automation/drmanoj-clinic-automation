#!/usr/bin/env python3
"""walk_s315.py -- the owner's two sheets, driven through the real module over a SCRATCH COPY of the
live finance.db. Proves the seed comes from the store, the guards refuse, and no other table is touched.
Usage: walk_s315.py MODULE_DIR DB_COPY"""
import importlib.util
import sqlite3
import sys

mod_dir, dbp = sys.argv[1], sys.argv[2]
sys.path.insert(0, mod_dir)
spec = importlib.util.spec_from_file_location("owner_sheets_walk", mod_dir + "/owner_sheets.py")
osh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(osh)
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
check("it names both sheets", "X-ray price list" in html and "Procedures and their consumables" in html)
check("the seed is the store's own amounts (500 billed under X-ray)", "&#8377; 500" in html)
check("it offers items to pick from the pharmacy list", "<datalist id='items'>" in html)
con = db()
seed = osh.billed_amounts(con, "xray")
check("X-ray seed rows carry times and last seen", seed and seed[0]["times"] > 0 and seed[0]["last_seen"])
check("a procedure seed exists too", bool(osh.billed_amounts(con, "proc")))
items = osh.consumable_items(con)
check("the item master is readable and non-empty", len(items) > 10)

r = cl.post("/finance/clinic/sheets/add", data={"kind": "xray", "name": "X-ray knee AP/LAT", "price": "500"})
check("naming a seeded amount is accepted", r.status_code in (302, 200))
r = cl.post("/finance/clinic/sheets/add", data={"kind": "xray", "name": "x-ray KNEE ap/lat", "price": "500"})
check("the same name twice is refused", "c=bad" in r.headers.get("Location", ""))
r = cl.post("/finance/clinic/sheets/add", data={"kind": "proc", "name": "Knee injection", "price": "1,500"})
check("a rupee amount with a comma is read", r.status_code in (302, 200))
rows = osh.services(db())
xr = [s for s in rows if s["kind"] == "xray"][0]
pr = [s for s in rows if s["kind"] == "proc"][0]
check("the price is stored in paise", xr["price_p"] == 50000 and pr["price_p"] == 150000)

r = cl.post("/finance/clinic/sheets/item/add", data={"id": xr["id"], "item": items[0]["item"], "qty": "1"})
check("an X-ray refuses consumables", "c=bad" in r.headers.get("Location", ""))
r = cl.post("/finance/clinic/sheets/item/add",
            data={"id": pr["id"], "item": items[0]["item"], "qty": "2", "unit": "no"})
check("a procedure takes one", r.status_code in (302, 200))
r = cl.post("/finance/clinic/sheets/item/add", data={"id": pr["id"], "item": items[0]["item"], "qty": "1"})
check("the same item twice is refused", "c=bad" in r.headers.get("Location", ""))
r = cl.post("/finance/clinic/sheets/item/add", data={"id": pr["id"], "item": items[1]["item"], "qty": "0"})
check("a zero quantity is refused", "c=bad" in r.headers.get("Location", ""))

u_before = len(seed)
check("a named amount drops out of the 'no name yet' list",
      len(osh.unnamed(db(), "xray")) == u_before - 1)

r = cl.post("/finance/clinic/sheets/price", data={"id": xr["id"], "price": "600"})
check("the price can be corrected", osh.services(db())[0]["price_p"] in (60000, 150000))
r = cl.post("/finance/clinic/sheets/price", data={"id": xr["id"], "price": "abc"})
check("a price that is not a number is refused", "c=bad" in r.headers.get("Location", ""))

r = cl.get("/finance/clinic/sheets/api/services").get_json()
check("the read-back door answers with both lists", r["ok"] and r["count"] == 2 and len(r["xray"]) == 1)
check("a procedure carries its consumables in the door", r["proc"][0]["items"][0]["qty"] == 2)
r = cl.post("/finance/clinic/sheets/active", data={"id": xr["id"], "on": "0"})
d = cl.get("/finance/clinic/sheets/api/services").get_json()
check("a hidden line leaves the door", d["count"] == 1)

un = osh.unnamed(db(), "xray")
check("a price moved off its seed puts that amount back on the list",
      50000 in [a["amount_p"] for a in un] and 60000 not in [a["amount_p"] for a in un])
check("the page still renders with rows on it",
      "X-ray knee AP/LAT" in cl.get("/finance/clinic/sheets").get_data(as_text=True))

WHO2 = {"user": "shavez"}
osh.OWNERS = ("manoj",)
globals()["WHO"] = WHO2
check("nobody but the doctor gets in", cl.get("/finance/clinic/sheets").status_code == 403)
globals()["WHO"] = {"user": "manoj"}

after = counts()
check("no other table was written", before == after)
print("WALK OK -- %d checks" % n[0])
