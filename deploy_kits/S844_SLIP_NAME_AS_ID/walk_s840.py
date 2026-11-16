#!/usr/bin/python3
"""walk_s840.py -- kit S840_SLIPS_DESK_XRAY (the parent, S467, 14-Nov-2026). Usage:
   walk_s840.py <dir holding the live /root/finance/*.py with the parchi_desk.py under test> <a finance.db copy> [--control]
On a SCRATCH copy of the live database, with made-up patients (IDs made at run time above every real one, made-up names and
mobiles) on made-up days in January 2027 (RECORDS_NOW / SLIP_NOW). Prints ok/BAD lines and counts only -- never a real patient.
Last line: "WALK OK n/n" | "WALK RED k of n" | with --control "CONTROL: red ..." (it must go red on the live 5ec8aebc file)."""
import importlib, json, os, re, shutil, sqlite3, subprocess, sys, tempfile
K, SRC = os.path.abspath(sys.argv[1]), sys.argv[2]
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s840w."); DB = os.path.join(T, "f.db"); shutil.copyfile(SRC, DB)
os.environ["FINANCE_DB"] = DB
os.environ["RECORDS_NOW"] = os.environ["SLIP_NOW"] = "2027-01-21 10:00:00"
for p in [x for x in os.environ.get("S840_LIBS", "").split(os.pathsep) if x] + [K]:
    while p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)[:220]) if (why != "" and not ok) else ""))
def finish():
    shutil.rmtree(T, ignore_errors=True)
    bad = RES.count(False)
    if CONTROL:
        print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
    else:
        print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
    sys.exit(0 if (bad if CONTROL else not bad) else 1)
try:
    SL = importlib.import_module("slip_log"); PD = importlib.import_module("parchi_desk")
    R = importlib.import_module("records"); CS = importlib.import_module("check_screens")
    if CS.R is None:
        CS.attach(R)
    ck("A1 parchi_desk, slip_log, check_screens, records from the dir under test", all(os.path.dirname(os.path.abspath(m.__file__)) == K for m in (SL, PD, R, CS)))
except Exception as e:  # noqa: BLE001
    ck("A1 import", False, repr(e)[:200]); finish()
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
R.ensure(con); R.xray_ensure(con); SL.ensure(con); SL.blood_ensure(con)
top = max([int(r[0]) for r in con.execute("SELECT clinic_id FROM patient_ref UNION SELECT clinic_id FROM slip UNION SELECT clinic_id "
                                           "FROM clinic_day_line") if str(r[0] or "").isdigit()] + [0])
P = {t: str(top + 2000 + i) for i, t in enumerate("ABCMN")}
NAME = {"A": "Zorvak Quentil", "B": "Zorvak Quintar", "C": "Pelmo Draxit", "M": "Zorvak Quentil", "N": "Trevlin Osk"}
def mob(i):                                        # a made-up mobile, made at run time (no number in this file)
    return "".join(str((int(P["A"]) * 7 + i * 13 + k * 3) % 10) for k in range(10))
for i, t in enumerate("ABCMN"):
    con.execute("INSERT INTO patient_ref (clinic_id, name, phone_last4, mobile, merged_into) VALUES (?,?,?,?,?)",
                (P[t], NAME[t], mob(i)[-4:], mob(i), None))
mid = con.execute("SELECT id FROM patient_ref WHERE clinic_id=?", (P["A"],)).fetchone()[0]
con.execute("UPDATE patient_ref SET merged_into=? WHERE clinic_id=?", (mid, P["M"]))      # M: a merged duplicate of A
ALNUM = "ZQ%dX" % (top % 1000)                                                            # a known clinic ID with letters
con.execute("INSERT INTO patient_ref (clinic_id, name) VALUES (?, ?)", (ALNUM, "Quarnel Vest"))
sn = [991000]
def slip(t, day, logged):
    sn[0] += 1
    cur = con.execute("INSERT INTO slip (series, slip_no, day, clinic_id, state, logged_at, name_seen) VALUES ('xp',?,?,?,'ok',?,?)",
                      (sn[0], day, P[t], logged, NAME[t]))
    con.execute("INSERT INTO slip_item (slip_id, kind, name) VALUES (?, 'xray', 'WALK VIEW')", (cur.lastrowid,))
slip("A", "2027-01-19", "2027-01-19 11:00:00")                                            # morning, no photo -> pending
slip("B", "2027-01-19", "2027-01-19 11:30:00")                                            # filed
con.execute("INSERT INTO record_file (clinic_id, kind, day, source, source_ref) VALUES (?, 'xray', '2027-01-19', 'walk', 'w840b')", (P["B"],))
slip("N", "2027-01-21", "2027-01-21 09:30:00")                                            # today, not due yet
con.commit()

from flask import Flask
USER = {"user": "walkshavez", "roles": ["maker", "checker"]}
def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c
def require(*roles, unit="slips"):
    return dict(USER), None
app = Flask("walk840"); app.testing = True
SL.init(app, db, require, None, unit="slips")
if "parchi_desk" not in app.blueprints:
    PD.init(app, db, require, None, unit="slips")
c = app.test_client()
def jp(path, body):
    r = c.post(path, data=json.dumps(body), content_type="application/json")
    try:
        return json.loads(r.get_data(as_text=True) or "{}")
    except ValueError:
        return {}
def jg(path):
    r = c.get(path)
    try:
        return json.loads(r.get_data(as_text=True) or "{}")
    except ValueError:
        return {"_status": r.status_code}

# ---- B: the page
S = CS.day_strip(con)
UP = sum(int(s["x"]["pending"]) for s in S)
r = c.get("/finance/slips/desk"); h = r.get_data(as_text=True)
ck("B1 the desk opens (200)", r.status_code == 200, r.status_code)
box = h.split('<details id="s840x"', 1)[1].split("</details>", 1)[0] if '<details id="s840x"' in h else ""
ck("B2 the box 'X-ray, pichhle 7 din' sits under the skipped numbers", box != "" and h.index('<div id="missing"></div>') < h.index('<details id="s840x"') < h.index('<div class="cols">'))
ck("B3 the box: A (19-Jan, no photo) by name as 'photo baaki'; B (filed) not listed; N (today) 'abhi samay hai'",
   (P["A"] in box and NAME["A"] in box and "photo baaki" in box and P["B"] not in box and P["N"] in box and "abhi samay hai" in box), box[:300])
ck("B4 the green strip carries 'X-ray upload baaki N' with N = Check karein's own pending count (%d)" % UP,
   UP >= 1 and ('"X-ray upload baaki %d"' % UP) in h and 'id="s840u"' in h and ("upload baaki %d" % UP) in box)
ins = re.findall(r'<input id="(opd_id|xp_id|bl_id)" inputmode="(\w+)"', h)
ck("B5 the three clinic-ID boxes take text, each with its list", sorted(ins) == [("bl_id", "text"), ("opd_id", "text"), ("xp_id", "text")]
   and all('<div class="fd" id="%s_fd"></div>' % w in h for w in ("opd", "xp", "bl")), ins)
ck("B6 the labels: 'Clinic ID ya naam' / 'ya clinic ID / naam'", 'cid:["Clinic ID ya naam","Clinic ID or name"]' in h and 'or_id:["ya clinic ID / naam","or the clinic ID / name"]' in h)
scripts = re.findall(r"<script>(.*?)</script>", h, re.S)
okjs = bool(scripts)
NODE = shutil.which("node")
for i, sc in enumerate(scripts if NODE else []):
    f = os.path.join(T, "s%d.js" % i); open(f, "w", encoding="utf-8").write(sc)
    p = subprocess.run(["node", "--check", f], capture_output=True, text=True)
    okjs = okjs and p.returncode == 0
ck("B7 every script on the page parses (node --check, %d scripts)%s" % (len(scripts), "" if NODE else " -- no node on this box: proven at the build"), okjs)
main = max(scripts, key=len) if scripts else ""
ck("B8 a name never saves: OPD, X-ray and blood each ask idFor() and stop on null",
   "function idFor(wh)" in main and "var cidv=$('opd_noid').checked?$('opd_id').value.trim():idFor('opd');if(cidv===null)return;" in main
   and "var cidv=idFor('xp');if(cidv===null)return;" in main and "var cid=idFor('bl');if(cid===null)return;" in main
   and "clinic_id:cidv," in main and "clinic_id:$('opd_id').value.trim()," not in main)
ck("B9 a name is never looked up as an ID, never set as the X-ray / blood pick", "if(/[A-Za-z]/.test(v)&&!SELV[v]){out.textContent=w('byname')" in main
   and "function idOnly(v){return /[A-Za-z]/.test(v)&&!SELV[v]?'':v;}" in main
   and "pick.xp=idOnly(" in main and "pick.bl=idOnly(" in main)
ck("B10 the list closes on a save (3 paths), on Escape and on blur", main.count("fdClose('opd');msg(true") == 1 and main.count("fdClose('xp');msg(true") == 1
   and main.count("fdClose('bl');msg(true") == 1 and "e.key==='Escape')fdClose(wh)" in main and "addEventListener('blur'" in main)
# a behaviour run of idFor in node: one match picks and stops; none stops with the message; a number passes through
harness = ("var calls=[];var FD={opd:[],xp:[],bl:[]};var V={opd_id:''};function $(i){return {get value(){return V[i]||''},set value(x){V[i]=x},focus:function(){}};}"
           "function msg(ok,t){calls.push('msg:'+t);}function w(k){return k;}function fdPick(wh,p){calls.push('pick:'+p.id);}var SELV={};function fdShow(wh){calls.push('show');}\n"
           + (main.split("function idFor(wh)", 1)[1].split("msg(false,w('pickl'));return null;}", 1)[0] if "function idFor(wh)" in main else "")
           )
fn = ("function idFor(wh)" + harness.split("\n", 1)[1] + "msg(false,w('pickl'));return null;}") if "function idFor(wh)" in main else ""
js = harness.split("\n", 1)[0] + "\n" + fn + ("\nV.opd_id='4521';var a=idFor('opd');V.opd_id='Zorvak';FD.opd=[{id:'1'}];var b=idFor('opd');"
      "FD.opd=[];var c=idFor('opd');FD.opd=[{id:'1'},{id:'2'}];var d=idFor('opd');SELV['ZQ7X']=1;V.opd_id='ZQ7X';var e=idFor('opd');"
      "console.log(JSON.stringify([a,b,c,d,e,calls]));")
jf = os.path.join(T, "idfor.js"); open(jf, "w", encoding="utf-8").write(js)
if NODE:
    p = subprocess.run([NODE, jf], capture_output=True, text=True)
    try:
        out = json.loads(p.stdout.strip() or "null")
    except ValueError:
        out = None
    ck("B11 idFor in node: a number passes; a name with one match picks it and stops; none / two stop with the message (two: the list shown again); an ID picked from the list passes",
       out == ["4521", None, None, None, "ZQ7X", ["pick:1", "msg:pickl", "show", "msg:pickl"]], (out, p.stderr[-160:]))
else:
    ck("B11 idFor present (no node on this box: its behaviour proven at the build)", "function idFor(wh)" in main)

ck("B12 (review) a changed box drops the old list's answer at once; blur only hides the list; a picked master ID is not a name",
   "inp.addEventListener('input',function(){FD[wh]=[];go();})" in main and "setTimeout(function(){fdHide(wh);},250)" in main
   and "if(/[A-Za-z]/.test(v)&&!SELV[v]){out.textContent=w('byname')" in main and "SELV[p.id]=1" in main)

# ---- C: the name search door
d = jg("/finance/slips/desk/api/find?q=" + NAME["A"].replace(" ", "%20") + "&day=2027-01-19")
pats = d.get("pats") or []
ids = [x.get("id") for x in pats]
ck("C1 a name finds the patient: A in the list", d.get("ok") is True and P["A"] in ids, d)
ck("C2 never a merged patient (M, A's duplicate)", P["M"] not in ids, ids)
ck("C3 each row: id, name, the mobile's last four only, came", pats and all(set(x) == {"id", "name", "m4", "came"} and re.fullmatch(r"\d{4}|", x["m4"]) for x in pats)
   and not any(len(re.sub(r"\D", "", str(x["name"]) + str(x["m4"]))) >= 10 for x in pats),
   [(len(x), len(str(x.get("m4"))), bool(re.fullmatch(r"\d{4}|", str(x.get("m4")))), len(re.sub(r"\D", "", json.dumps(x)))) for x in pats])
ck("C4 digits or two letters: an empty list (an ID goes to /api/patient)", jg("/finance/slips/desk/api/find?q=" + P["A"]).get("pats") == []
   and jg("/finance/slips/desk/api/find?q=Zo").get("pats") == [])
a_row = next((x for x in pats if x.get("id") == P["A"]), {})
ck("C5 'came' is true for A on 19-Jan", a_row.get("came") is True, a_row)

# ---- D: the save door
st = jg("/finance/slips/desk/api/state").get("state") or {}
n0 = con.execute("SELECT COUNT(*) FROM slip").fetchone()[0]
d = jp("/finance/slips/desk/api/save", {"series": "opd", "slip_no": st.get("nx_opd"), "clinic_id": "Zorvak", "today_pick": True, "day": "2027-01-21"})
n1 = con.execute("SELECT COUNT(*) FROM slip").fetchone()[0]
ck("D1 OPD save with a NAME as the clinic ID: refused, nothing written", d.get("ok") is False and "Naam clinic ID nahi" in (d.get("err") or "") and n1 == n0, (d, n0, n1))
d = jp("/finance/slips/desk/api/save", {"series": "xp", "slip_no": st.get("nx_xp"), "clinic_id": "Pelmo", "today_pick": True, "day": "2027-01-21", "items": []})
ck("D2 X-ray save with a name: refused", d.get("ok") is False and "Naam clinic ID nahi" in (d.get("err") or ""), d)
d = jp("/finance/slips/desk/api/save", {"series": "opd", "slip_no": st.get("nx_opd"), "clinic_id": P["C"], "today_pick": True, "day": "2027-01-21", "gap_ok": True})
ck("D3 OPD save with a number: saved as before", d.get("ok") is True, d.get("err"))
st = jg("/finance/slips/desk/api/state").get("state") or {}
d = jp("/finance/slips/desk/api/save", {"series": "opd", "slip_no": st.get("nx_opd"), "clinic_id": ALNUM, "today_pick": True, "day": "2027-01-21", "gap_ok": True})
ck("D4 a clinic ID with letters that the master knows: saved as before", d.get("ok") is True, d.get("err"))
d = jp("/finance/slips/desk/api/save", {"series": "opd", "noid": True, "no_id_name": "Trevlin Osk", "slip_no": (jg("/finance/slips/desk/api/state").get("state") or {}).get("nx_opd"),
                                        "today_pick": True, "day": "2027-01-21", "gap_ok": True})
ck("D5 'ID nahi hai' with a name: saved as before", d.get("ok") is True, d.get("err"))

# ---- E: the blood door
d = jp("/finance/slips/desk/api/blood", {"clinic_id": "Zorvak"})
ck("E1 blood with a name: refused, nothing written", d.get("ok") is False and "Naam clinic ID nahi" in (d.get("err") or "")
   and not con.execute("SELECT 1 FROM blood_order WHERE clinic_id='Zorvak'").fetchone(), d)
d = jp("/finance/slips/desk/api/blood", {"clinic_id": P["N"]})
ck("E2 blood with a number: saved as before", d.get("ok") is True, d.get("err"))
con.close()
finish()
