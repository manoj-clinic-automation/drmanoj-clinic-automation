#!/usr/bin/python3
"""walk_s839.py -- kit S839_FREE_XRAY_WORDS (the parent, S465, 14-Nov-2026; S836's walk with the words of S839). Usage:
   walk_s839.py <dir holding check_screens.py, records.py, owner_console.py> <a finance.db copy> [--control]
On a SCRATCH copy, with made-up patients (IDs made at run time above every real one) on made-up days in January 2027 (the clock
set by RECORDS_NOW). Prints ok/BAD lines and counts only -- never a real patient's name or number.
Last line: "WALK OK n/n" | "WALK RED k of n" | with --control "CONTROL: red ..." (it must go red on the old files)."""
import importlib, json, os, shutil, sqlite3, sys, tempfile
K, SRC = os.path.abspath(sys.argv[1]), sys.argv[2]
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s836w."); DB = os.path.join(T, "f.db"); shutil.copyfile(SRC, DB)
os.environ["FINANCE_DB"] = DB
os.environ["RECORDS_NOW"] = "2027-01-21 10:00:00"
for p in [x for x in os.environ.get("S836_LIBS", "").split(os.pathsep) if x] + [K]:
    while p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why != "" and not ok) else ""))
def finish():
    shutil.rmtree(T, ignore_errors=True)
    bad = RES.count(False)
    if CONTROL:
        print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
    else:
        print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
    sys.exit(0 if (bad if CONTROL else not bad) else 1)
try:
    R = importlib.import_module("records"); CS = importlib.import_module("check_screens")
    if CS.R is None:
        CS.attach(R)
    ck("A1 check_screens and records from the kit dir", os.path.dirname(os.path.abspath(CS.__file__)) == K)
    ck("A2 S836 functions present", all(hasattr(CS, f) for f in ("day_strip", "kal_card", "_pairs", "s836_pairs")))
except Exception as e:  # noqa: BLE001
    ck("A import", False, repr(e)[:160]); finish()
if not all(hasattr(CS, f) for f in ("day_strip", "kal_card", "_pairs", "s836_pairs")):
    finish()
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
R.ensure(con); R.xray_ensure(con)
top = max([int(r[0]) for r in con.execute("SELECT clinic_id FROM patient_ref UNION SELECT clinic_id FROM slip UNION SELECT clinic_id "
                                           "FROM clinic_day_line") if str(r[0] or "").isdigit()] + [0])
P = {t: str(top + 1000 + i) for i, t in enumerate("ABCDEFGHIJKLMNOPQRST")}
NAME = {t: "ZQWALK %s%sXY" % (t, t) for t in P}
sn = [990000]
def slip(t, day, logged):
    sn[0] += 1
    cur = con.execute("INSERT INTO slip (series, slip_no, day, clinic_id, state, logged_at, name_seen) VALUES ('xp',?,?,?,'ok',?,?)",
                      (sn[0], day, P[t], logged, NAME[t]))
    con.execute("INSERT INTO slip_item (slip_id, kind, name) VALUES (?, 'xray', 'WALK VIEW')", (cur.lastrowid,))
def photo(t, day):
    con.execute("INSERT INTO record_file (clinic_id, kind, day, source, source_ref) VALUES (?, 'xray', ?, 'walk', ?)", (P[t], day, "w" + P[t] + day))
def pic(sid, day, name, timed=True):
    con.execute("INSERT INTO xray_filing (src_id, orig_name, file_time, clinic_id, day, state) VALUES (?,?,?,?,?, 'check')",
                (sid, name, (day + " 18:00:00") if timed else "", "", day))
def near(t):                                       # the patient's ID with one keystroke wrong
    c = P[t]
    return c[:-1] + ("1" if c[-1] != "1" else "2")
def ans(key, a, by="walkdoc", kind="xray_file"):
    con.execute("INSERT INTO record_check (key, kind, clinic_id, answer, note, answered_by, answered_at) VALUES (?,?,?,?,?,?,?)",
                (key, kind, "", a, "", by, "2027-01-20 10:00:00"))
SID = {k: "s836walkpic%s000000" % k for k in ("U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8", "U9", "U10", "U11", "U12", "U13")}
# 19-Jan: A no photo (morning), B filed; U1 a picture with no name -> THE PAIR, files itself
slip("A", "2027-01-19", "2027-01-19 11:00:00"); slip("B", "2027-01-19", "2027-01-19 11:30:00"); photo("B", "2027-01-19")
def film(sid, day, cid):
    con.execute("INSERT OR REPLACE INTO xray_filmdate (src_id, dates, ids, how) VALUES (?,?,?, 'walk')", (sid, json.dumps([day]), json.dumps([cid])))
pic(SID["U1"], "2027-01-19", "IMG_0001.jpg"); film(SID["U1"], "2027-01-19", near("A"))   # a sign: the FILM reads A's ID one keystroke off
# 18-Jan: C, D no photo; one picture -> no pair (two X-rays without a photo)
slip("C", "2027-01-18", "2027-01-18 11:00:00"); slip("D", "2027-01-18", "2027-01-18 12:00:00"); pic(SID["U2"], "2027-01-18", "IMG_0002.jpg")
# 17-Jan: E no photo; two pictures (two people) -> no pair
slip("E", "2027-01-17", "2027-01-17 11:00:00"); pic(SID["U3"], "2027-01-17", "IMG_0003.jpg"); pic(SID["U4"], "2027-01-17", "QXVOLP TRENBA.jpg")
# 16-Jan: F no photo; one picture already marked 'not in Docterz' by a person -> asked, never by itself
slip("F", "2027-01-16", "2027-01-16 11:00:00"); pic(SID["U5"], "2027-01-16", "IMG_0005.jpg"); ans("xf:" + SID["U5"], "no_docterz")
# 15-Jan: G no photo; one picture that someone said 'Nahi' to -> no pair
slip("G", "2027-01-15", "2027-01-15 11:00:00"); pic(SID["U6"], "2027-01-15", "IMG_0006.jpg"); ans("ep:" + SID["U6"], "not_pair", kind="xray_pair")
# 20-Jan (yesterday): H evening (not due till 21-Jan 15:00), I morning (due 20-Jan 15:00 -> pending), J filed; U7 -> no pair (window open)
slip("H", "2027-01-20", "2027-01-20 19:00:00"); slip("I", "2027-01-20", "2027-01-20 11:00:00"); slip("J", "2027-01-20", "2027-01-20 11:30:00")
photo("J", "2027-01-21"); pic(SID["U7"], "2027-01-20", "IMG_0007.jpg")
# 13-Jan: M no photo, N filed; U8 has no sign at all -> ASKED only
slip("M", "2027-01-13", "2027-01-13 11:00:00"); slip("N", "2027-01-13", "2027-01-13 11:30:00"); photo("N", "2027-01-13"); pic(SID["U8"], "2027-01-13", "IMG_%s.jpg" % near("M"))   # a camera counter like M's ID: never a sign
# 12-Jan (cold review R1): O's own picture U9 already given O's ID (not yet filed); another picture U10 -> no pair
slip("O", "2027-01-12", "2027-01-12 11:00:00"); pic(SID["U9"], "2027-01-12", "IMG_0009.jpg"); ans("xf:" + SID["U9"], "id_fixed")
con.execute("UPDATE record_check SET note=? WHERE key=?", (P["O"], "xf:" + SID["U9"])); pic(SID["U10"], "2027-01-12", "IMG_%s.jpg" % near("O"))
# 11-Jan (R2): Q no photo; U11 (a sign) pairs and files; U12 of that day closed by a tap (Muft) is never touched
slip("Q", "2027-01-11", "2027-01-11 11:00:00"); pic(SID["U11"], "2027-01-11", "IMG_0011.jpg"); film(SID["U11"], "2027-01-11", near("Q"))
pic(SID["U12"], "2027-01-11", "IMG_0012.jpg"); ans("xf:" + SID["U12"], "no_docterz"); ans("pg:" + SID["U12"], "explained", kind="xray_payment")
# 10-Jan (R4): R no photo; U13 has no time and no film date (its day is a guess) -> never paired
slip("R", "2027-01-10", "2027-01-10 11:00:00"); pic(SID["U13"], "2027-01-10", "IMG_%s.jpg" % near("R"), timed=False)
# 21-Jan (today): K morning, not due yet
slip("K", "2027-01-21", "2027-01-21 09:30:00")
# blood: A 19-Jan with a report 20-Jan -> in; C 18-Jan none -> pending; K 21-Jan -> not due; L 18-Jan not tested -> answered
for t, d in (("A", "2027-01-19"), ("C", "2027-01-18"), ("K", "2027-01-21"), ("L", "2027-01-18")):
    con.execute("INSERT INTO blood_order (day, clinic_id, name_seen, state, outcome) VALUES (?,?,?, 'ok', ?)", (d, P[t], NAME[t], "not_tested" if t == "L" else ""))
con.execute("INSERT INTO lab_report (msg_id, clinic_id, received_at) VALUES ('s836walk1', ?, '2027-01-20 16:00:00')", (P["A"],))
con.commit()
WHO = {v: k for k, v in P.items()}
def mine(rows):
    return {WHO[r["cid"]]: r for r in rows if r["cid"] in WHO}

# ---- B: the date strip
S = CS.day_strip(con)
ck("B1 seven days, newest first, today first", [s["day"] for s in S] == ["2027-01-%02d" % d for d in range(21, 14, -1)] and S[0]["today"])
D = {s["day"][-2:]: s for s in S}
x19, x20, x18 = mine(D["19"]["x"]["rows"]), mine(D["20"]["x"]["rows"]), mine(D["18"]["x"]["rows"])
ck("B2 19-Jan: A pending (subah), B filed", x19.get("A", {}).get("st") == "pending" and x19["A"]["sh"] == "subah" and x19.get("B", {}).get("st") == "filed", x19)
ck("B3 20-Jan: H not due (shaam), I pending (subah), J filed (a photo the next day counts)",
   x20.get("H", {}).get("st") == "notdue" and x20["H"]["sh"] == "shaam" and x20.get("I", {}).get("st") == "pending" and x20.get("J", {}).get("st") == "filed", x20)
ck("B4 21-Jan: K not due yet", mine(D["21"]["x"]["rows"]).get("K", {}).get("st") == "notdue")
ck("B5 18-Jan: C and D pending", x18.get("C", {}).get("st") == "pending" and x18.get("D", {}).get("st") == "pending")
ck("B6 unplaced pictures counted on their day as 'dikkat' (19:1 18:1 17:2 16:1 15:1 20:1)",
   [D[d]["x"]["unplaced"] for d in ("19", "18", "17", "16", "15", "20")] == [1, 1, 2, 1, 1, 1], [D[d]["x"]["unplaced"] for d in ("19", "18", "17", "16", "15", "20")])
ck("B7 the day's sums agree with its rows (19-Jan: our 2 + any real)", D["19"]["x"]["n"] == len(D["19"]["x"]["rows"]) and D["19"]["x"]["issue"] >= 1)
b19, b18, b21 = mine(D["19"]["b"]["rows"]), mine(D["18"]["b"]["rows"]), mine(D["21"]["b"]["rows"])
ck("B8 blood: A in, C pending, L answered, K not due", b19.get("A", {}).get("st") == "in" and b18.get("C", {}).get("st") == "pending"
   and b18.get("L", {}).get("st") == "answered" and b21.get("K", {}).get("st") == "notdue", (b19, b18, b21))
ck("B9 names come with each row", x19.get("A", {}).get("name") == NAME["A"])

# ---- C: Kal ki X-ray (reception)
KC = CS.kal_card(S)
ck("C1 Kal = 20-Jan, 3 X-rays, 1 filed", KC and KC["day"] == "2027-01-20" and KC["n"] == 3 and KC["filed"] == 1, KC and (KC["day"], KC["n"], KC["filed"]))
kr = mine(KC["rows"]) if KC else {}
ck("C2 its rows: H (not due) and I (pending), never the filed J", set(kr) == {"H", "I"}, sorted(kr))
ko = mine(KC["older"]) if KC else {}
ck("C3 older pending: A, C, D, E, F, G (the days before, not today)", {"A", "C", "D", "E", "F", "G"} <= set(ko) and "K" not in ko, sorted(ko))
ck("C4 before 15:00 it is 'by 3 pm' (late False)", KC and KC["late"] is False)

# ---- D: the pair
PR = CS._pairs(con, {})
ck("D1 U1 (19-Jan) pairs with A, and may file itself", PR.get(SID["U1"], {}).get("id") == P["A"] and PR[SID["U1"]]["auto"] is True, PR.get(SID["U1"]))
ck("D2 U5 (16-Jan, marked not in Docterz) pairs with F but is only ASKED", PR.get(SID["U5"], {}).get("id") == P["F"] and PR[SID["U5"]]["auto"] is False)
ck("D3 no pair: two X-rays without a photo (U2), two pictures (U3, U4), a 'Nahi' (U6), the window open (U7), O's own picture on its "
   "way (U10, R1), a day that is a guess (U13, R4)", not any(SID[u] in PR for u in ("U2", "U3", "U4", "U6", "U7", "U10", "U13")),
   [u for u in ("U2", "U3", "U4", "U6", "U7", "U10", "U13") if SID[u] in PR])
ck("D3b no sign on the picture (U8): ASKED, never by itself", PR.get(SID["U8"], {}).get("id") == P["M"] and PR[SID["U8"]]["auto"] is False)
ck("D3c U11 pairs with Q by itself; the tapped U12 is not in its group", PR.get(SID["U11"], {}).get("auto") is True and SID["U12"] not in PR[SID["U11"]]["group"])
os.environ["RECORDS_NOW"] = "2027-01-20 16:00:00"
p_early = CS._pairs(con, {}).get(SID["U1"]) or {}
os.environ["RECORDS_NOW"] = "2027-01-21 10:00:00"
ck("D3d R3: on 20-Jan after 3 pm the 19-Jan pair is ASKED, not yet filed by itself (S791's rules have the day first)",
   p_early.get("id") == P["A"] and p_early.get("auto") is False, p_early)
Q = {i["sid"]: i for i in CS.xray_queue(con)}
ck("D4 the staff queue carries the pair on U1's card", (Q.get(SID["U1"]) or {}).get("pair", {}) and Q[SID["U1"]]["pair"]["id"] == P["A"])
n = CS.s787_auto(con)
a1 = con.execute("SELECT answer, note, answered_by FROM record_check WHERE key=?", ("xf:" + SID["U1"],)).fetchone()
ck("D5 the filing plan's pass gives U1 to A as 'system · S836 P'", a1 is not None and a1["answer"] == "id_fixed" and a1["note"] == P["A"]
   and a1["answered_by"].startswith("system · S836 P"), a1 and tuple(a1))
a5 = con.execute("SELECT answer FROM record_check WHERE key=?", ("xf:" + SID["U5"],)).fetchone()
ck("D6 U5 untouched (still the person's 'no_docterz')", a5 and a5["answer"] == "no_docterz")
a12 = con.execute("SELECT answer FROM record_check WHERE key=?", ("xf:" + SID["U12"],)).fetchone()
a11 = con.execute("SELECT answer, note FROM record_check WHERE key=?", ("xf:" + SID["U11"],)).fetchone()
ck("D6b U11 given Q; U12 (closed by a tap) still 'no_docterz' (R2)", a11 and a11["note"] == P["Q"] and a12 and a12["answer"] == "no_docterz")
a8 = con.execute("SELECT answered_by FROM record_check WHERE key=?", ("xf:" + SID["U8"],)).fetchone()
ck("D6c U8 (no sign) not given an ID by S836", not a8 or "S836" not in a8["answered_by"])
ck("D7 U2/U3/U7 never given an ID by S836", all((con.execute("SELECT answered_by FROM record_check WHERE key=?", ("xf:" + SID[u],)).fetchone() or {"answered_by": ""})["answered_by"].find("S836") < 0
                                              for u in ("U2", "U3", "U7")))
DOC = {"user": "walkdoc", "roles": ["checker"]}
code, d = CS.answer(con, DOC, {"key": "ep:" + SID["U5"], "a": "not_pair", "new_id": P["F"]}, en=True)
ck("D8 'No' on the pair is recorded and the pair is gone", code == 200 and SID["U5"] not in CS._pairs(con, {}), (code, d))
code, d = CS.answer(con, DOC, {"key": "ep:" + SID["U5"], "a": "bogus"}, en=True)
ck("D9 an unknown answer on ep: is refused", code == 400)

# ---- E: Not in Docterz = complimentary
it5 = next((i for i in CS.xray_queue(con, nodz_only=True) if i["sid"] == SID["U5"]), None)
ck("E1 the wording: 'free X-ray?' (Hindi and English), no 'PAYMENT GAP', no 'muft'", it5 and "free X-ray?" in it5["reason"]
   and "free X-ray?" in it5["reason_en"] and "PAYMENT" not in it5["reason_en"].upper() and "muft" not in (it5["reason"] + it5["reason_en"]).lower(), it5 and it5["reason_en"][-90:])
ck("E2 it is open (pg) until a tap", it5 and it5["pg"] and SID["U5"] in [i["sid"] for i in CS.pgap_items(con)])
code, d = CS.answer(con, DOC, {"key": "pg:" + SID["U5"], "a": "explained", "why": "muft"}, en=True)
ck("E3 one tap 'muft' closes it", code == 200 and SID["U5"] not in [i["sid"] for i in CS.pgap_items(con)], (code, d))
it5 = next((i for i in CS.xray_queue(con, nodz_only=True) if i["sid"] == SID["U5"]), None)
ck("E4 his list keeps it, saying 'free X-ray'", it5 and "explained: free X-ray" in it5["reason_en"])
code, d = CS.answer(con, {"user": "walkrecep", "roles": ["maker"]}, {"key": "pg:" + SID["U5"], "a": "explained", "why": "slip"})
ck("E5 reception cannot close it (Shavez and the doctors only)", code in (403, 409))
src = open(os.path.join(K, "check_screens.py"), encoding="utf-8").read()
scr = src.split('STAFF_PAGE = r"""', 1)[1]                                   # the two pages as drawn
ck("E6 no 'payment gap' / 'paisa' wording left on the screens", all(w not in scr for w in ("paisa liya", "Possible payment gap", "possible payment gap",
   "POSSIBLE PAYMENT GAP", "Registered nahi &mdash; paisa")) and "X-ray bina registration" not in src and ">Free X-ray</button>" in scr and "Muft" not in scr and "omplimentary" not in scr
   and "muft X-ray" not in scr and '"Free X-ray? %d"' in src)
try:
    OC = importlib.import_module("owner_console")
    ck("E7 his console: S791's red payment-gap line is gone", not hasattr(OC, "_s791_pgap_line") and "a possible payment gap" not in open(OC.__file__, encoding="utf-8").read()
       and "pgap_items" not in open(OC.__file__, encoding="utf-8").read())
except Exception as e:  # noqa: BLE001
    ck("E7 owner_console imports", False, repr(e)[:160])

# ---- F: the staff page (reception and Shavez) carries what the screens draw
from flask import Flask
app = Flask("walk")
with app.test_request_context("/finance/checks"):
    rr = CS.staff_page(con, {"user": "walkrecep", "roles": ["maker"]}, [])
    h = rr.get_data(as_text=True)
    j = json.loads(h.split("var B=", 1)[1].split(", IT=B.items", 1)[0])
    ck("F1 reception: no strip, a Kal card, the 9:30 flag", j["strip"] == [] and j["kal"] and j["kal"]["day"] == "2027-01-20" and j["kal_show"] is True)
    rr = CS.staff_page(con, DOC, [])
    j = json.loads(rr.get_data(as_text=True).split("var B=", 1)[1].split(", IT=B.items", 1)[0])
    ck("F2 a lab login: the 7-day strip, no Kal card", len(j["strip"]) == 7 and j["kal"] is None)
    ck("F3 the page opens on 'Din ke hisaab se' for a lab login", "F=B.lab&&(B.strip||[]).length?'days':'all'" in h)
os.environ["RECORDS_NOW"] = "2027-01-21 09:00:00"
with app.test_request_context("/finance/checks"):
    j = json.loads(CS.staff_page(con, {"user": "walkrecep", "roles": ["maker"]}, []).get_data(as_text=True).split("var B=", 1)[1].split(", IT=B.items", 1)[0])
    ck("F4 before 9:30 the Kal card is held back", j["kal_show"] is False)
con.close()
finish()
