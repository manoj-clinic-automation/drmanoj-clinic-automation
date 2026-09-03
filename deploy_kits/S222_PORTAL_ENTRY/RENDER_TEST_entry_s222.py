#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_entry_s222.py -- does the Manage Users link actually LAND somewhere useful?

The owner's flow is: portal -> Manage Users -> "Add a new joiner" -> and he is filling the form.
Not looking at a screen with a button that opens the form. So this drives the two URLs the
portal card links to and checks what is on screen when the page settles, plus the no-flag case,
which must still be the ordinary home screen.

    python3 -B RENDER_TEST_entry_s222.py <dir with the patched files>
"""
import os,sys,json,sqlite3,tempfile,threading,time,shutil
FIN=sys.argv[1]; sys.path.insert(0,FIN)
tmp=tempfile.mkdtemp(); portal=os.path.join(tmp,"portal"); os.makedirs(portal)
shutil.copyfile(os.environ["CLINIC_USERS_PY"], os.path.join(portal,"clinic_users.py"))
store=os.path.join(portal,"clinic_users.json")
json.dump({"epoch":1,"roles":["doctor","manager","staff"],"users":{}},open(store,"w"))
os.environ["PORTAL_DIR"]=portal; os.environ["CLINIC_USERS_FILE"]=store
sys.path.insert(0,portal); import clinic_users as CU
for u in ("darpan","shivani","alisha","shavez","amir"): CU.add_user(store,u,"staff",u+"1234")
db=os.path.join(tmp,"finance.db"); c=sqlite3.connect(db)
c.executescript(open(os.path.join(FIN,"joiner_schema.sql"),encoding="utf-8").read()); c.commit(); c.close()
from flask import Flask,Response
import joiner_app as JA, staff_pages as SP
html=open(os.path.join(FIN,"staff_manage.html"),encoding="utf-8").read()
app=Flask("e")
def _db():
    x=sqlite3.connect(db); x.row_factory=sqlite3.Row; return x
def _req(*r,**k): return dict(user="manoj",role="doctor",roles=["checker"]),None
JA.init(app,_db,SP.joiner_require(_req),url_prefix="/finance/staff")
@app.route("/finance/staff/")
def pg_(): return Response(html,mimetype="text/html")
threading.Thread(target=lambda: app.run(port=8771,threaded=True,use_reloader=False),daemon=True).start()
time.sleep(1.5)
from playwright.sync_api import sync_playwright
F=[]
def ck(l,c,d=""):
    print("  %s  %s%s"%("PASS" if c else "FAIL",l,("   [%s]"%d) if d else ""))
    if not c: F.append(l)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ["PW_CHROME"])
    pg=b.new_page(viewport={"width":390,"height":900}); errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.on("dialog",lambda d:d.dismiss())
    base="http://127.0.0.1:8771/finance/staff/"
    pg.goto(base,wait_until="networkidle"); pg.evaluate("localStorage.setItem('staff_by','Dr Manoj')")
    print("-- ?flow=join lands ON the form ----------------------------------")
    pg.goto(base+"?flow=join",wait_until="networkidle"); time.sleep(1.2)
    ck("the joiner form is open, with no extra click",bool(pg.query_selector("#jf_name")))
    ck("the home screen is hidden", pg.eval_on_selector("#home","e=>getComputedStyle(e).display")=="none")
    ck("the authority list rendered", len(pg.query_selector_all(".jf_a"))==8, str(len(pg.query_selector_all(".jf_a"))))
    print("-- ?flow=exit lands ON the picker --------------------------------")
    pg.goto(base+"?flow=exit",wait_until="networkidle"); time.sleep(1.2)
    xp=pg.inner_text("#xp")
    ck("the leaver picker is open",bool(pg.query_selector("#xp")))
    ck("real people are listed",all(u in xp for u in ("darpan","alisha","shavez")),xp[:80])
    ck("still no text box on it",not pg.query_selector("#xp input"))
    print("-- no flag = the ordinary home screen ----------------------------")
    pg.goto(base,wait_until="networkidle"); time.sleep(1.0)
    ck("home is shown", pg.eval_on_selector("#home","e=>getComputedStyle(e).display")!="none")
    ck("no form is open",not pg.query_selector("#jf_name"))
    ck("no javascript error",not errs,"; ".join(errs))
    b.close()
shutil.rmtree(tmp,ignore_errors=True)
print("\n%s -- %d failed"%("ENTRY GREEN" if not F else "ENTRY RED",len(F)))
sys.exit(1 if F else 0)
