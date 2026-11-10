# -*- coding: utf-8 -*-
"""walk_s770.py -- the S770 probe on a made-up root: a made-up database, a stub Drive (records_drive.py's own stub
mode) and made-up pictures drawn here (white text on black, as a film's printing). No real patient anywhere.
Proves: a printed date is read and scored right; metadata (EXIF) dates are read; a picture with no date says so;
a check-folder picture with ID + film date is offered for filing on that day; a no-ID picture is placed by name on
the film date; the report carries no made-up name or ID; nothing is written to the database.
CONTROL: with the film's text left unread (S770_CONTROL=1 -> no tesseract on PATH) the known-day score must drop
to the metadata ones only -- the walk asserts that it does (the control goes red on purpose).
Run: python walk_s770.py <path to probe_s770.py> <path to records_drive.py>"""
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

PROBE, HELPER = sys.argv[1], sys.argv[2]
root = tempfile.mkdtemp(prefix="walk770_")
stub = os.path.join(root, "drive")
os.makedirs(stub)
dbp = os.path.join(root, "finance.db")
ok = fail = 0


def check(cond, what):
    global ok, fail
    if cond:
        ok += 1
        print("  PASS", what)
    else:
        fail += 1
        print("  FAIL", what)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def film(path, top, bottom, exif_date=None):
    im = Image.new("L", (1800, 2200), 20)
    d = ImageDraw.Draw(im)
    d.ellipse((500, 600, 1300, 1700), fill=150)           # a 'bone'
    d.text((40, 30), top, fill=235, font=font(44))
    d.text((40, 2120), bottom, fill=235, font=font(40))
    kw = {}
    if exif_date:
        ex = Image.Exif()
        ex[0x0132] = exif_date
        kw["exif"] = ex.tobytes()
    im.convert("RGB").save(path, "JPEG", quality=90, **kw)


# the made-up database
c = sqlite3.connect(dbp)
c.executescript("""
CREATE TABLE record_setting(key TEXT PRIMARY KEY, value TEXT, set_at TEXT);
CREATE TABLE xray_filing(src_id TEXT PRIMARY KEY, orig_name TEXT, file_time TEXT, action TEXT, clinic_id TEXT, day TEXT,
  new_name TEXT, dest_id TEXT, file_id INTEGER, state TEXT, verdict TEXT, planned_at TEXT, done_at TEXT);
CREATE TABLE record_file(id INTEGER PRIMARY KEY, clinic_id TEXT, kind TEXT, day TEXT, drive_id TEXT, file_name TEXT, mime TEXT,
  bytes INTEGER, source TEXT, source_ref TEXT, state TEXT, note TEXT, added_by TEXT, added_at TEXT);
CREATE TABLE slip(id INTEGER PRIMARY KEY, day TEXT, clinic_id TEXT, series TEXT, state TEXT, name_seen TEXT, slip_no TEXT, logged_at TEXT);
CREATE TABLE slip_item(id INTEGER PRIMARY KEY, slip_id INTEGER, kind TEXT, name TEXT, side TEXT, sort INTEGER);
CREATE TABLE clinic_day_line(business_date TEXT, clinic_id TEXT, section TEXT, patient TEXT);
CREATE TABLE patient_ref(id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, merged_into TEXT);
""")
c.execute("INSERT INTO record_setting VALUES('xray_check_id','CHECKFOLDER0001','')")
people = [("7001", "TESTA KUMARI"), ("7002", "TESTB SINGHAL"), ("7003", "TESTC VERMANI"), ("7004", "TESTD PRAKASHAN")]
for cid, nm in people:
    c.execute("INSERT INTO patient_ref(clinic_id,name) VALUES(?,?)", (cid, nm))


def slip(day, cid, nm):
    cur = c.execute("INSERT INTO slip(day,clinic_id,series,state,name_seen) VALUES(?,?,?,?,?)", (day, cid, "xp", "ok", nm))
    c.execute("INSERT INTO slip_item(slip_id,kind,name) VALUES(?,?,?)", (cur.lastrowid, "xray", "Knee AP"))


slip("2026-10-12", "7001", "TESTA KUMARI")      # filed truth
slip("2026-10-14", "7002", "TESTB SINGHAL")     # filed truth (EXIF only)
slip("2026-10-20", "7003", "TESTC VERMANI")     # re-added, ID + date -> file
slip("2026-10-21", "7003", "TESTC VERMANI")     # a second pending day: only the film date can choose
slip("2026-10-25", "7004", "TESTD PRAKASHAN")   # parked, no ID -> by name on the film date
slip("2026-10-26", "7001", "TESTA KUMARI")      # a second patient that day? no -- different name
pics = {
    "FILEDA00000001": ("TESTA KUMARI 7001.jpg", "TESTA KUMARI   ID 7001   12/10/2026  10:42", "AP VIEW  CLINIC", None),
    "FILEDB00000002": ("TESTB SINGHAL 7002.jpg", "TESTB SINGHAL   M  45Y", "LAT", "2026:10:14 11:05:00"),
    "FILEDC00000003": ("TESTA KUMARI 7001 ..jpg", "TESTA KUMARI", "nothing here", None),
    "CHECKA0000001": ("TESTC VERMANI 7003.jpg", "TESTC VERMANI 7003", "Date: 20-Oct-2026", None),
    "CHECKB0000002": ("TESTD PRAKASHAN ..jpg", "TESTD PRAKASHAN F 61Y", "2026/10/25 09:10", None),
}
listing = []
for fid, (name, top, bottom, ex) in pics.items():
    film(os.path.join(stub, fid), top, bottom, ex)
    if fid.startswith("CHECK"):
        listing.append({"id": fid, "name": name, "mimeType": "image/jpeg", "modifiedTime": "2026-11-09T13:40:00.000Z"})
json.dump(listing, open(os.path.join(stub, "list_CHECKFOLDER0001.json"), "w"))
c.execute("INSERT INTO xray_filing(src_id,orig_name,file_time,action,clinic_id,day,state,verdict,planned_at) VALUES"
          "('CHECKA0000001','TESTC VERMANI 7003.jpg','2026-11-09 19:10:00','check','7003','2026-11-09','check','not on list','2026-11-09 19:25:20')")
c.execute("INSERT INTO xray_filing(src_id,orig_name,file_time,action,clinic_id,day,state,verdict,planned_at) VALUES"
          "('CHECKB0000002','TESTD PRAKASHAN ..jpg','2026-10-25 09:20:00','check','','2026-10-25','check','no ID','2026-10-25 10:25:20')")
for i, (fid, cid, day) in enumerate((("FILEDA00000001", "7001", "2026-10-12"), ("FILEDB00000002", "7002", "2026-10-14"),
                                     ("FILEDC00000003", "7001", "2026-10-12")), 1):
    c.execute("INSERT INTO record_file(clinic_id,kind,day,drive_id,file_name,source,state) VALUES(?,?,?,?,?,?,?)",
              (cid, "xray", day, fid, "x.jpg", "xray_inbox", "ok"))
c.commit()
c.close()
h0 = hashlib.md5(open(dbp, "rb").read()).hexdigest()


def run(control):
    out = os.path.join(root, "out_c" if control else "out")
    env = dict(os.environ, S770_DB=dbp, S770_HELPER=HELPER, S770_OUT=out, S770_MAIL="0", RECORDS_HELPER_STUB=stub)
    if control:
        env["PATH"] = "/nonexistent"
    p = subprocess.run([sys.executable, "-B", PROBE], env=env, capture_output=True, text=True, timeout=600)
    return p.returncode, open(os.path.join(out, "report.txt")).read() if os.path.exists(os.path.join(out, "report.txt")) else p.stderr


print("walk -- the probe on a made-up root")
rc, rep = run(False)
print(rep)
check(rc == 0, "the probe ran")
check("filed (known day): 3 pictures" in rep, "3 filed pictures read")
check("the known day found 2 " in rep, "the printed date and the EXIF date both scored right (2 of 3)")
check("nothing found 1" in rep, "the picture with no date says so")
check("file: ID + film date = an X-ray day with no photo" in rep, "the re-added picture: ID + film date -> file")
check("file by name on the film date" in rep, "the no-ID picture: placed by name on the film date")
check(not any(w in rep for w in ("TESTA", "TESTB", "TESTC", "TESTD", "KUMARI", "SINGHAL", "VERMANI", "PRAKASHAN")), "no name in the report")
check(not any(x in rep for x in ("7001", "7002", "7003", "7004", "FILEDA", "CHECKA")), "no clinic ID or Drive id in the report")
check(hashlib.md5(open(dbp, "rb").read()).hexdigest() == h0, "the database is unchanged")
print("CONTROL -- the film's text not read")
rc2, rep2 = run(True)
check("tesseract NO" in rep2, "control: no OCR tool")
red = "the known day found 2 " in rep2
print("  CONTROL", "stayed green -- WRONG" if red else "went RED as it must (only the EXIF date is found)")
check(not red and "the known day found 1 " in rep2, "control red: without the film's text only the metadata date scores")
shutil.rmtree(root, ignore_errors=True)
print("\nwalk %d/%d" % (ok, ok + fail))
sys.exit(1 if fail else 0)
