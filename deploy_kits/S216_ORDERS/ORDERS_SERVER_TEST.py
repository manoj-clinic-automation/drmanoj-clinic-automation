#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORDERS_SERVER_TEST.py - S216: the medicine list on the server."""
import os,sys,json,tempfile,importlib.util,shutil,glob
BASE=os.path.dirname(os.path.abspath(__file__))
N=[0,0]
def check(n_,ok,note=""):
    N[0]+=1
    if ok: N[1]+=1; print("  ok  "+n_+("  "+note if note else ""))
    else:  print("FAIL  "+n_+("  "+note if note else ""))

tmp=tempfile.mkdtemp(prefix="cp_orders_")
try:
    import sqlite3
    for nm in ("console.db","finance.db"):
        sqlite3.connect(os.path.join(tmp,nm)).close()
    os.environ["PORTAL_CASEPACK_DIR"]=os.path.join(tmp,"casepack")
    os.environ["PORTAL_CONSOLE_DB"]=os.path.join(tmp,"console.db")
    os.environ["PORTAL_FINANCE_DB"]=os.path.join(tmp,"finance.db")
    spec=importlib.util.spec_from_file_location("cpo",os.path.join(BASE,"casepack_portal.py"))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    from flask import Flask
    app=Flask(__name__)
    mod.register(app,(lambda f:f),lambda:"orderstest")
    c=app.test_client()

    print("\n-- the list seeds itself from his template, once --")
    j=c.get("/portal/casepack/meds").get_json()
    check("list reads ok", j["ok"])
    items=[r["Item"] for r in j["rows"]]
    check("seeded with his own medicines", len(items)>=13, "%d items"%len(items))
    for want in ("5% DNS","Inj Vinbactum DS","Inj Butrum 2 Mg","Inj Pcm 100 Ml"):
        check("seed contains "+want, want in items)
    check("IV fluids carry no frequency (they are the fluid group)",
          all(not r["Freq"] for r in j["rows"] if r["Item"] in ("5% DNS","NS","Ringer Lactate")))
    check("nothing is pre-marked Ayushman or package - his to mark",
          all(not r["Ayushman"] and not r["Package"] for r in j["rows"]))

    print("\n-- his edits persist, and are marked --")
    rows=j["rows"]
    rows[3]["Ayushman"]="1"; rows[4]["Package"]="1"
    rows.append({"Item":"Inj Test Med","Route":"IV","Freq":"BD","Ayushman":"1","Package":"","Active":"1","Sort":"900"})
    r=c.post("/portal/casepack/meds",json={"rows":rows}); j2=r.get_json()
    check("save accepted", j2["ok"], str(j2))
    j3=c.get("/portal/casepack/meds").get_json()
    check("the new item is there", "Inj Test Med" in [x["Item"] for x in j3["rows"]])
    check("the Ayushman mark stuck", any(x["Ayushman"]=="1" for x in j3["rows"]))
    check("the package mark stuck", any(x["Package"]=="1" for x in j3["rows"]))
    check("it does NOT re-seed over his list", len(j3["rows"])==len(rows))

    print("\n-- it never destroys --")
    baks=glob.glob(os.path.join(tmp,"casepack","med_list.csv.bak_*"))
    check("the previous list is kept, dated", len(baks)==1, "%d backup(s)"%len(baks))

    print("\n-- it refuses what is almost certainly a bug --")
    check("an empty list is REFUSED", c.post("/portal/casepack/meds",json={"rows":[]}).status_code==400)
    check("a list of blank names is REFUSED",
          c.post("/portal/casepack/meds",json={"rows":[{"Item":"  "}]}).status_code==400)
    check("an absurd list is REFUSED",
          c.post("/portal/casepack/meds",json={"rows":[{"Item":"x"}]*401}).status_code==400)
    j4=c.get("/portal/casepack/meds").get_json()
    check("and after all three refusals his list is INTACT",
          len(j4["rows"])==len(rows) and "Inj Test Med" in [x["Item"] for x in j4["rows"]])

    print("\n-- the rest of the portal is untouched --")
    check("the case ledger route still answers", c.get("/portal/casepack/cases").get_json()["ok"])
finally:
    shutil.rmtree(tmp,ignore_errors=True)
print("\n%d/%d server checks passed"%(N[1],N[0]))
sys.exit(0 if N[0]==N[1] else 1)
