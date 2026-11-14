#!/usr/bin/python3
"""walk_s842.py -- kit S842_XRAY_SHEET_PHOTO (the parent, S467, 14-Nov-2026). Usage:
   walk_s842.py <dir holding the live /root/finance/*.py with the clinic_lists.py under test> <a finance.db copy> [--control]
On a SCRATCH copy of the live database, with made-up patients (IDs made at run time above every real one, made-up names) on
made-up days in January 2027 (CLINICLISTS_NOW / RECORDS_NOW). Prints ok/BAD lines and counts only -- never a real patient.
Last line: "WALK OK n/n" | "WALK RED k of n" | with --control "CONTROL: red ..." (it must go red on the live 92aca69e file)."""
import importlib, io, json, os, re, shutil, sqlite3, sys, tempfile, zipfile
K, SRC = os.path.abspath(sys.argv[1]), sys.argv[2]
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s842w."); DB = os.path.join(T, "f.db"); shutil.copyfile(SRC, DB)
os.environ["FINANCE_DB"] = DB
os.environ["RECORDS_NOW"] = os.environ["CLINICLISTS_NOW"] = os.environ["SLIP_NOW"] = "2027-01-21 10:00:00"
for p in [x for x in os.environ.get("S842_LIBS", "").split(os.pathsep) if x] + [K]:
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
    CL = importlib.import_module("clinic_lists"); R = importlib.import_module("records"); CS = importlib.import_module("check_screens")
    if CS.R is None:
        CS.attach(R)
    ck("A1 clinic_lists, check_screens, records from the dir under test", all(os.path.dirname(os.path.abspath(m.__file__)) == K for m in (CL, R, CS)))
except Exception as e:  # noqa: BLE001
    ck("A1 import", False, repr(e)[:200]); finish()
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
R.ensure(con); R.xray_ensure(con)
top = max([int(r[0]) for r in con.execute("SELECT clinic_id FROM patient_ref UNION SELECT clinic_id FROM slip UNION SELECT clinic_id "
                                           "FROM clinic_day_line") if str(r[0] or "").isdigit()] + [0])
P = {t: str(top + 3000 + i) for i, t in enumerate("ABCDEFGH")}
NAME = {t: "Qervan %sotl" % t for t in P}
sn = [992000]
def slip(t, day, logged, n=1, cid=True):
    sn[0] += 1
    cur = con.execute("INSERT INTO slip (series, slip_no, day, clinic_id, no_id_name, state, logged_at, name_seen) VALUES ('xp',?,?,?,?,'ok',?,?)",
                      (sn[0], day, P[t] if cid else "", "" if cid else NAME[t], logged, NAME[t]))
    for k in range(n):
        con.execute("INSERT INTO slip_item (slip_id, kind, name, price_p, sort) VALUES (?, 'xray', ?, 30000, ?)", (cur.lastrowid, "WALK VIEW %d" % k, k))
slip("A", "2027-01-19", "2027-01-19 11:00:00")                                       # morning, no photo -> Pending, due 19-Jan
slip("B", "2027-01-19", "2027-01-19 11:30:00")                                       # a photo the next day -> Filed
cur = con.execute("INSERT INTO record_file (clinic_id, kind, day, drive_id, source, source_ref) VALUES (?, 'xray', '2027-01-20', 'walkdrive842b', 'walk', 'w842b')", (P["B"],))
FID_B = cur.lastrowid
slip("C", "2027-01-20", "2027-01-20 19:00:00")                                       # evening -> due 21-Jan 15:00: Not due yet
slip("D", "2027-01-18", "2027-01-18 11:00:00")                                       # a picture of his parked in the check folder -> Issue
con.execute("INSERT INTO xray_filing (src_id, orig_name, file_time, clinic_id, day, state) VALUES ('s842walkD', 'IMG_D.jpg', '2027-01-18 18:00:00', ?, '2027-01-18', 'check')", (P["D"],))
slip("E", "2027-01-17", "2027-01-17 11:00:00")                                       # answered 'X-ray nahi hua' -> X-ray not done
con.execute("INSERT INTO record_check (key, kind, clinic_id, answer, note, answered_by, answered_at) VALUES (?, 'xray_missing', ?, 'not_done', '', 'walkdoc', '2027-01-18 10:00:00')",
            ("xm:2027-01-17:%s" % P["E"], P["E"]))
slip("F", "2027-01-16", "2027-01-16 11:00:00", n=2)                                  # two X-rays, one patient-day -> both lines Pending
con.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift) VALUES "
            "('2027-01-15', 'xray', 9901, ?, ?, 30000, 'Cash', 'Morning')", (NAME["G"], P["G"]))  # Docterz only -> Pending
slip("H", "2027-01-14", "2027-01-14 11:00:00", cid=False)                             # no clinic ID -> '-'
con.commit()

from flask import Flask
USER = {"user": "manoj", "roles": ["checker"]}
def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c
def require(*roles, unit="slips"):
    return dict(USER), None
app = Flask("walk842"); app.testing = True
CL.init(app, db, require, None, unit="slips")
c = app.test_client()
def page(qs=""):
    r = c.get("/finance/slips/lists/xray?m=2027-01" + qs)
    return r.status_code, r.get_data(as_text=True)
def row_of(h, t):
    rows = [x for x in re.findall(r"<tr>(.*?)</tr>", h, re.S) if ">" + P[t] + "<" in x or "'>" + P[t] in x or P[t] in x]
    return rows
def cells(row):
    return re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)

code, h = page()
ck("B1 his X-rays tab opens (200)", code == 200, code)
th = re.findall(r"<th[^>]*>(.*?)</th>", h)
ck("B2 the columns: ... Film, Films, Photo, Paid, Amount", th[-5:] == ["Film", "Films", "Photo", "Paid", "Amount"], th)
def photo(t, i=0):
    rs = row_of(h, t)
    return cells(rs[i])[8] if len(rs) > i and len(cells(rs[i])) > 8 else None
pa, pb, pcc, pd, pe, pf0, pf1, pg = photo("A"), photo("B"), photo("C"), photo("D"), photo("E"), photo("F", 0), photo("F", 1), photo("G")
ck("B3 A (19-Jan, no photo): Pending, due 19-Jan", pa and "Pending" in pa and "due 19-Jan" in pa, pa)
ck("B4 B (photo the next day): Filed, opening that photo", pb and ("/finance/records/file/%d" % FID_B) in pb and "Filed" in pb and "target='_blank'" in pb, pb)
ck("B5 C (evening, due tomorrow 3 pm): Not due yet", pcc and "Not due yet" in pcc, pcc)
ck("B6 D (his picture in the check folder): Issue, to his X-ray check page", pd and "Issue" in pd and "/finance/records/xray-check" in pd, pd)
ck("B7 E (answered 'X-ray nahi hua'): X-ray not done", pe and "X-ray not done" in pe, pe)
ck("B8 F (two X-rays, one patient-day): both lines Pending", pf0 and pf1 and "Pending" in pf0 and "Pending" in pf1, (pf0, pf1))
ck("B9 G (in Docterz only): Pending", pg and "Pending" in pg, pg)
hr = [x for x in re.findall(r"<tr>(.*?)</tr>", h, re.S) if NAME["H"] in x]
ck("B10 H (no clinic ID): '-'", hr and cells(hr[0])[8] == "—", hr and cells(hr[0])[8])
ck("B11 the count, per patient and day: 1 filed · 3 pending · 1 issue · 1 not due yet · 1 X-ray not done; 'Not filed only (5)'",
   "<b>1</b> filed" in h and "<b>3</b> pending" in h and "<b>1</b> issue" in h and "<b>1</b> not due yet" in h and "<b>1</b> X-ray not done" in h
   and "Not filed only (5)</a>" in h and "nf=1" in h, re.findall(r"Photos \(per patient and day\):.*?</p>", h)[:1])
code, h2 = page("&nf=1")
ids = [t for t in "ABCDEFG" if row_of(h2, t)]
ck("B12 'Not filed only': A, C, D, F, G (5 patient-days, as the button said); never B (filed), E (not done) or the no-ID row", code == 200 and ids == ["A", "C", "D", "F", "G"]
   and not any(NAME["H"] in x for x in re.findall(r"<tr>(.*?)</tr>", h2, re.S)) and "Show all</a>" in h2, ids)
ck("B13 the Excel link and the tab links keep the switch", re.search(r"xray\.xlsx\?[^']*nf=1", h2) is not None)
r = c.get("/finance/slips/lists/xray.xlsx?m=2027-01&nf=1")
txt = ""
try:
    z = zipfile.ZipFile(io.BytesIO(r.get_data()))
    txt = " ".join(z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith(".xml"))
except Exception as e:  # noqa: BLE001
    txt = "ERR " + repr(e)
ck("B14 the Excel: a Photo column; 'Pending (due 19-Jan)'; the filed one left out under the switch",
   r.status_code == 200 and "Photo" in txt and "Pending (due 19-Jan)" in txt and "Not due yet" in txt and P["B"] not in txt and P["A"] in txt, txt[:160])
code, hp = c.get("/finance/slips/lists/proc?m=2027-01").status_code, c.get("/finance/slips/lists/proc?m=2027-01").get_data(as_text=True)
ck("B15 the Procedures tab is as before (no Photo column)", code == 200 and "<th>Photo</th>" not in hp and "Not filed only" not in hp)
real = CS.day_strip
CS.day_strip = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("walk: unreadable"))
code, h3 = page()
code4, h4 = page("&nf=1")
CS.day_strip = real
pa3 = (cells(row_of(h3, "A")[0]) + [None] * 9)[8] if row_of(h3, "A") else None
ck("B16 when the states cannot be read: the sheet opens, the Photo column says '-', the line says so, the switch shows every row",
   code == 200 and pa3 == "—" and "could not be read" in h3 and "Not filed only" not in h3 and code4 == 200 and row_of(h4, "B"), (code, pa3))
USER["user"] = "bhawna"
ck("B17 still his alone (another checker: 403)", c.get("/finance/slips/lists/xray").status_code == 403)
con.close()
finish()
