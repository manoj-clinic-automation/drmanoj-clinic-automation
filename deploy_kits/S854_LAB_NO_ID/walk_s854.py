#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s854.py -- kit S854_LAB_NO_ID (the parent, S477, 17-Nov-2026). Usage:
   walk_s854.py <dir holding slip_log.py + check_screens.py under test> <dir of every other finance module> <a finance.db copy> [--control]
On a SCRATCH copy, with made-up patients (IDs above every real one, made-up names) and made-up lab mails in January 2027 (the clock
pinned by SLIP_NOW / RECORDS_NOW). Prints ok/BAD lines and counts only. Last line "WALK OK n/n" | "WALK RED k of n" | with
--control "CONTROL: red ..." (it must go red on the live files)."""
import importlib, os, shutil, sqlite3, sys, tempfile
K, LIB, SRC = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3]
CONTROL = "--control" in sys.argv
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
sys.path[:] = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]          # F-1441
for p in (LIB, K):
    while p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
T = tempfile.mkdtemp(prefix="s854w.")
DB = os.path.join(T, "f.db")
shutil.copyfile(SRC, DB)
os.environ.update(FINANCE_DB=DB, SLIP_NOW="2027-01-21 10:00:00", RECORDS_NOW="2027-01-21 10:00:00")
RES = []


def ck(name, ok, why=""):
    RES.append(bool(ok))
    print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)[:220]) if (why != "" and not ok) else ""))


def finish():
    shutil.rmtree(T, ignore_errors=True)
    bad = RES.count(False)
    if CONTROL:
        print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
    else:
        print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
    sys.exit(0 if (bad if CONTROL else not bad) else 1)


try:
    SL = importlib.import_module("slip_log")
    R = importlib.import_module("records")
    CS = importlib.import_module("check_screens")
    if CS.R is None:
        CS.attach(R)
    ck("A1 slip_log and check_screens from the kit dir", os.path.dirname(os.path.abspath(SL.__file__)) == K and
       os.path.dirname(os.path.abspath(CS.__file__)) == K)
except Exception as e:                                                  # noqa: BLE001
    ck("A import", False, repr(e))
    finish()
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
SL.ensure(con); SL.blood_ensure(con); SL.noid_ensure(con); R.ensure(con)
top = max([int(r[0]) for r in con.execute("SELECT clinic_id FROM patient_ref UNION SELECT clinic_id FROM patient_visit") if str(r[0] or "").isdigit()] + [0])
P = {k: str(top + 1000 + i) for i, k in enumerate(("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "Z1", "Z2", "Z3"))}
NAME = {"P1": "KORVAN TELBI", "P2": "KORVAN MIRAX", "P3": "SELVOR PINDA", "P4": "GHOMPU RATZE", "P5": "GHOMPU WELVIK",
        "P6": "KORVAN ZEBLO", "P7": "TRUVEX HALMO", "P8": "PIRQAN DELVO", "P9": "QUEMBO VARTIL",
        "Z1": "ZORPLA", "Z2": "ZORPLA", "Z3": "ZORPLA QUENTISH"}           # two open slips with a first name only, one full name in the list
for k, cid in P.items():
    con.execute("INSERT INTO patient_ref (clinic_id, name) VALUES (?,?)", (cid, NAME[k]))


def order(k, day):
    con.execute("INSERT INTO blood_order (day, clinic_id, name_seen, logged_by, logged_at) VALUES (?,?,?,?,?)",
                (day, P[k], NAME[k], "walk", day + " 11:00:00"))


def noid(mid, name, at, cid="", how=""):
    con.execute("INSERT INTO lab_noid (msg_id, name, received_at, clinic_id, how, pushed_at) VALUES (?,?,?,?,?,?)", (mid, name, at, cid, how, at))


order("P1", "2027-01-19")                                            # open slip 1 day before R1 -> the strong one
order("P6", "2027-01-16")                                            # 4 days before: inside S391's 7 days -> a second open slip
order("P9", "2027-01-18")
order("Z1", "2027-01-19"); order("Z2", "2027-01-18")                                            # R6: the ONLY open slip with its name -> "sabse pakka"
con.execute("INSERT INTO patient_visit (visit_id, visit_date, clinic_id, patient_uid) VALUES (990001, '2027-01-18', ?, 'walk-u2')", (P["P2"],))
order("P3", "2027-01-19")
con.execute("INSERT INTO lab_report (msg_id, clinic_id, received_at, pushed_at) VALUES ('s854walkrep3', ?, '2027-01-19 20:00:00', 'w')", (P["P3"],))
noid("s854walkR1", "KORVAN TELBY", "2027-01-20 12:00:00")
noid("s854walkR2", "SELVOR PINDA", "2027-01-20 12:05:00")
noid("s854walkR3", "GHOMPU RATZE", "2027-01-20 12:10:00")
noid("s854walkR4", "XYLQUV", "2027-01-20 12:15:00")
noid("s854walkR5", "OLDNAM QUESTO", "2026-12-01 12:00:00")          # 51 days old, never placed
noid("s854walkR6", "QUEMBO VARTEL", "2027-01-20 12:20:00")
con.commit()
# ---------------------------------------------------------------- B: the old automatic rule is unchanged
ck("B1 S391's automatic rule still declines R1 (two open slips with the name)", SL.noid_match(con, "KORVAN TELBY", "2027-01-20 12:00:00") == "")
has = hasattr(SL, "noid_candidates")
ck("B2 noid_candidates present", has)
C = (lambda n, at: SL.noid_candidates(con, n, at)) if has else (lambda n, at: [])
c1 = C("KORVAN TELBY", "2027-01-20 12:00:00")
ck("B3 R1: two open slips with the name -> both offered (the two-word match first), none 'sabse pakka', each saying 2 are open; the one-word visitor left out",
   [x["cid"] for x in c1] == [P["P1"], P["P6"]] and not any(x["strong"] for x in c1) and all("2 parchi khuli" in x["why"] for x in c1),
   [(x["cid"] == P["P1"], x["strong"], x["why"]) for x in c1])
c6 = C("QUEMBO VARTEL", "2027-01-20 12:20:00")
cz = C("ZORPLA QUENTISH", "2027-01-20 12:30:00")
ck("B4b a two-word report name never hides an OPEN one-word slip: both open slips offered first, with the warning, none strong",
   [x["cid"] for x in cz][:2] == sorted([P["Z1"], P["Z2"]], key=lambda c: (c != P["Z1"])) and all("2 parchi khuli" in x["why"] for x in cz[:2])
   and not any(x["strong"] for x in cz) and P["Z3"] in [x["cid"] for x in cz], [(x["open"], x["strong"]) for x in cz])
ck("B4 R6: the only open slip with the name -> strong", [x["cid"] for x in c6] == [P["P9"]] and c6[0]["strong"] and "blood parchi" in c6[0]["why"], c6)
c2 = C("SELVOR PINDA", "2027-01-20 12:05:00")
ck("B5 R2: a slip whose report already came is offered, NOT strong, and says so",
   len(c2) == 1 and c2[0]["cid"] == P["P3"] and not c2[0]["strong"] and "aa chuki" in c2[0]["why"], c2)
c3 = C("GHOMPU RATZE", "2027-01-20 12:10:00")
ck("B6 R3: no slip, no visit -> the patient list, the same name exactly (not GHOMPU WELVIK)",
   [x["cid"] for x in c3] == [P["P4"]] and c3[0]["tier"] == 3, c3)
ck("B7 R4: nobody -> no suggestion", C("XYLQUV", "2027-01-20 12:15:00") == [])
ck("B8 a name with no usable word -> no suggestion (never a guess)", C("MR", "2027-01-20 12:15:00") == [])
pend = {r["msg_id"] for r in SL.noid_pending(con)}
ck("B9 the 51-day-old unplaced report is back on the list", "s854walkR5" in pend and "s854walkR1" in pend, sorted(pend))
# ---------------------------------------------------------------- C: reception's card and the one-tap pick
U = {"user": "walk", "roles": ["maker"]}
html = SL._pend_blood_html(con, U, [], [], [])
ck("C1 the card offers each report's patients, one tap each", ("noid_pick:%s" % P["P1"]) in html and ("noid_pick:%s" % P["P9"]) in html)
k9 = html.find("noid_pick:%s" % P["P9"])
ck("C2 the strong one is marked 'sabse pakka', the ambiguous one is not", "sabse pakka" in html[k9:k9 + 400] and
   "sabse pakka" not in html[html.find("noid_pick:%s" % P["P1"]):html.find("noid_pick:%s" % P["P1"]) + 400])
import re as _re                                                        # noqa: E402
forms = [f for f in _re.findall(r'<form[^>]*class="rb nxf"[^>]*>.*?</form>', html, _re.S)]
ck("C7 Enter in the ID box submits the typed ID: every card's first button is the plain 'noid_pick'",
   forms and all(_re.search(r'<button[^>]*>', f).group(0).count('value="noid_pick"') == 1 for f in forms), len(forms))
ck("C3 a report with nobody says so and keeps the ID box and 'Hamara nahi'", "Naam se koi mareez nahi mila" in html and "noid_gone" in html)
from flask import Flask                                                 # noqa: E402
app = Flask("walk854")
app.secret_key = "walk"
SL.init(app, lambda: con, lambda *a, **k: (U, None), None, unit="slips")
cl = app.test_client()
r = cl.post("/finance/slips/pending/act", data={"key": "nx:s854walkR1", "act": "noid_pick:%s" % P["P1"], "cid2": P["P2"]})
row = con.execute("SELECT clinic_id FROM lab_noid WHERE msg_id='s854walkR1'").fetchone()
ck("C8 a suggestion tapped with a different ID typed is refused, nothing filed", r.status_code == 303 and row["clinic_id"] == "")
r = cl.post("/finance/slips/pending/act", data={"key": "nx:s854walkR1", "act": "noid_pick:WALK-IN"})
row = con.execute("SELECT clinic_id FROM lab_noid WHERE msg_id='s854walkR1'").fetchone()
ck("C9 a posted letter ID or unknown patient is refused", row["clinic_id"] == "")
r = cl.post("/finance/slips/pending/act", data={"key": "nx:s854walkR1", "act": "noid_pick:%s" % P["P1"]})
row = con.execute("SELECT clinic_id, how FROM lab_noid WHERE msg_id='s854walkR1'").fetchone()
ck("C4 one tap files R1 on P1 (picked) and its order closes", r.status_code == 303 and row and (row["clinic_id"], row["how"]) == (P["P1"], "pick")
   and SL._report_for(con, P["P1"], "2027-01-19") is not None, (r.status_code, tuple(row) if row else None))
r = cl.post("/finance/slips/pending/act", data={"key": "nx:s854walkR3", "act": "noid_pick", "cid2": P["P4"]})
row = con.execute("SELECT clinic_id FROM lab_noid WHERE msg_id='s854walkR3'").fetchone()
ck("C5 the typed ID still works", row and row["clinic_id"] == P["P4"])
r = cl.post("/finance/slips/pending/act", data={"key": "nx:s854walkR4", "act": "noid_gone"})
row = con.execute("SELECT how FROM lab_noid WHERE msg_id='s854walkR4'").fetchone()
ck("C6 'Hamara nahi' still closes it", row and row["how"] == "gone")
# ---------------------------------------------------------------- D: the owner's "Filed by themselves" and Move
noid("s854walkR7", "TRUVEX HALMO", "2027-01-10 09:00:00", P["P7"], "auto")
con.execute("INSERT INTO lab_report (msg_id, clinic_id, received_at, pushed_at) VALUES ('s854walkR7', ?, '2027-01-10 09:00:00', 'w')", (P["P7"],))
con.execute("INSERT INTO record_file (clinic_id, kind, day, drive_id, file_name, source, source_ref) VALUES (?, 'blood', '2027-01-10', 'walkdrive', "
            "'walk.pdf', 'lab_mail', 's854walkR7#1A')", (P["P7"],))
noid("s854walkR8", "TRUVEX HALMO", "2027-01-11 09:00:00", P["P7"], "auto")   # filed by itself but its PDF not filed yet -> not listed
con.commit()
fi = [i for i in CS.filed_items(con) if i["key"].startswith("lm:s854walk")]
ck("D1 the auto-filed lab report is on 'Filed by themselves' (with its report), the unfiled PDF is not",
   [i["key"] for i in fi] == ["lm:s854walkR7"] and fi[0].get("lab") and fi[0]["fid"], [i["key"] for i in fi])
DOC = {"user": "walkdoc", "roles": ["checker"]}
st, j = CS.answer(con, U, {"key": "lm:s854walkR7", "a": "moved", "new_id": P["P8"]})
ck("D2 staff cannot move it", st == 403, (st, j))
st, j = CS.answer(con, DOC, {"key": "lm:s854walkR7", "a": "moved", "new_id": P["P7"]})
ck("D3 the same ID is refused", st == 400)
st, j = CS.answer(con, DOC, {"key": "lm:s854walkR7", "a": "moved", "new_id": P["P8"], "check": 1})
ck("D4 the check names the patient and writes nothing", st == 200 and j.get("name") == NAME["P8"] and
   con.execute("SELECT clinic_id FROM record_file WHERE source_ref='s854walkR7#1A'").fetchone()[0] == P["P7"], j)
st, j = CS.answer(con, DOC, {"key": "lm:s854walkR7", "a": "moved", "new_id": P["P8"]})
f = con.execute("SELECT clinic_id, note FROM record_file WHERE source_ref='s854walkR7#1A'").fetchone()
lr = con.execute("SELECT clinic_id FROM lab_report WHERE msg_id='s854walkR7'").fetchone()
nx = con.execute("SELECT clinic_id, how FROM lab_noid WHERE msg_id='s854walkR7'").fetchone()
ck("D5 the move: the file, the report line and the mail's row all on P8, with a note", st == 200 and f["clinic_id"] == P["P8"] and
   "moved from" in f["note"] and lr["clinic_id"] == P["P8"] and tuple(nx) == (P["P8"], "move"), (st, j))
fi = [i for i in CS.filed_items(con) if i["key"] == "lm:s854walkR7"]
ck("D6 still listed after the move, now on P8, saying it was moved", fi and fi[0]["cid"] == P["P8"] and "moved" in fi[0]["detail"])
ck("D7 an X-ray move ('mv:') is untouched by this kit", CS.answer(con, DOC, {"key": "mv:999999999", "a": "moved", "new_id": P["P8"]})[0] == 409)
con.execute("INSERT INTO record_file (clinic_id, kind, day, drive_id, file_name, source, source_ref) VALUES (?, 'blood', '2027-01-20', 'walkdrive', "
            "'walk.pdf', 'lab_mail', 's854walkR1#1B')", (P["P1"],))
con.commit()
fp = [i for i in CS.filed_items(con) if i["key"] == "lm:s854walkR1"]
ck("D8 reception's one-tap pick is on his list too, saying who picked it, so a wrong pick can be moved", fp and "picked at reception by walk" in fp[0]["detail"], fp)
finish()
