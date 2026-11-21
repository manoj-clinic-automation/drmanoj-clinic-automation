"""walk_s916.py -- kit S916_MANOJZ_SENDS_FU_CONS: docterz_clinical_send.py on a MADE-UP Downloads folder (no real patient,
no real number). usage: python walk_s916.py <dir holding docterz_clinical_send.py> <work dir>   -> last line 'WALK n/N'.
On the live (S780) file it must go red: that file sends clinical reports only."""
import importlib.util, json, os, shutil, sys, time

SRC, WORK = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.abspath(os.path.dirname(__file__))]   # F-1441
shutil.rmtree(WORK, ignore_errors=True)
DL, AR, DE = (os.path.join(WORK, x) for x in ("Downloads", "Archive", "Dest"))
for d in (DL, AR, DE):
    os.makedirs(d)
os.environ.update(CLINICAL_SEND_DOWNLOADS=DL, CLINICAL_SEND_ARCHIVE=AR, CLINICAL_SEND_DEST=DE,
                  CLINICAL_SEND_ALL_OFF=os.path.join(WORK, "ALL_OFF.txt"))
spec = importlib.util.spec_from_file_location("cs_walk", os.path.join(SRC, "docterz_clinical_send.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

OLD = time.mktime((2026, 11, 19, 10, 0, 0, 0, 0, -1))
NEW = time.mktime((2026, 11, 20, 23, 55, 0, 0, 0, -1))
def put(name, text, mt=NEW):
    p = os.path.join(DL, name)
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    os.utime(p, (mt, mt))
    return p
FU = "Appointment ID,Mobile No,Patient Name,Followup Text,Followup Date,Doctor Name,Comments\n" + \
     "".join("A%d,MOBILE,Test Person %d,review,%02d-12-2026,Dr X,\n" % (i, i, 1 + i % 20) for i in range(1, 9)) + \
     "A9,MOBILE,Test Person 9,review,21-11-2026,Dr X,\n"
CONS1 = "Consultation Date,Patient UID,Patient Name,Mode Of Payment,Amount\n" + \
        "".join("20-11-2026,UIDTEST%03d,Test %d,Cash,500\n" % (i, i) for i in range(5)) + "Credit Card,0,,,\n"
CONS3 = "Consultation Date,Patient UID,Patient Name,Mode Of Payment,Amount\n" + \
        "".join("%02d-11-2026,UIDTEST%03d,Test %d,Cash,500\n" % (18 + i % 3, i, i) for i in range(6))
CLIN = "Consultation Date,Patient UID,Diagnosis,Drugs Prescribed,Mode Of Payment\n" + \
       "".join("%02d-11-2026,UIDTEST%03d,Knee pain,Tab X,Cash\n" % (19 + i % 2, i) for i in range(4))
put("followup_logs (24).csv", FU)
put("consultation_report_2026-11-20.csv", CONS1)
put("consultation_report_range.csv", CONS3)
put("clinical_data_report_2026-11-20.csv", CLIN)
put("followup_logs_2026-11-20_reception_abcdef.csv", FU.replace("Dr X", "Dr Y"))          # the fetch's own file
fetched = put("followup_logs (25).csv", FU.replace("review", "seen"))                      # an md5 the fetch brought
put("followup_logs (23).csv", FU.replace("Dr X", "Dr Z"), OLD)                              # downloaded before the floor
import hashlib
with open(os.path.join(AR, "_server_fetch_state.json"), "w") as fh:
    json.dump({"have": {hashlib.md5(open(fetched, "rb").read()).hexdigest(): {"how": "fetched"}}}, fh)

R = []
def check(n, ok, why=""):
    R.append(bool(ok)); print(("ok   " if ok else "FAIL ") + n + ((" -- " + str(why)) if (why and not ok) else ""))
def dest():
    return sorted(f for f in os.listdir(DE) if not f.startswith("~"))

M.one_pass(now=NEW + 600)
d = dest()
check("C1 the clinical report sent, as before", any(f.startswith("clinical_data_report_2026-11-20_manojz_") for f in d), d)
check("F1 his follow-up log sent, named by its first due day", any(f.startswith("followup_logs_2026-11-21_manojz_") for f in d), d)
check("K1 his one-day consultation report sent", any(f.startswith("consultation_report_2026-11-20_manojz_") for f in d), d)
check("K2 a three-day consultation report NOT sent", sum(f.startswith("consultation_report_") for f in d) == 1, d)
check("N1 the fetch's _reception_ file NOT sent back", sum(f.startswith("followup_logs_") for f in d) == 1, d)
log = open(os.path.join(AR, "_clinical_send_log.txt"), encoding="utf-8").read()
check("K3 the three-day report said in the log, with the page to use", "NOT sent" in log and "Docterz reports page" in log)
check("L1 the log names kinds and counts, no patient name", "SENT a follow-up log" in log and "Test Person" not in log and "UIDTEST" not in log)
same = []
for f in d:
    if f.startswith("followup_logs_"):
        same.append(open(os.path.join(DE, f), "rb").read() == FU.encode())
check("B1 the copy is the file's own bytes", same == [True], same)
mts = [int(os.path.getmtime(os.path.join(DE, f))) for f in d if f.startswith("followup_logs_")]
check("B2 the copy keeps the export's own time (the server dates a log by it)", mts == [int(NEW)], (mts, int(NEW)))
n0 = len(d)
M.one_pass(now=NEW + 900)
check("P2 a second pass sends nothing again", len(dest()) == n0, dest())
# the switch for the two new kinds only
open(os.path.join(AR, "_fu_cons_send_OFF.txt"), "w").close()
put("followup_logs (26).csv", FU.replace("Dr X", "Dr W"))
put("clinical_data_report_2026-11-21.csv", CLIN.replace("Tab X", "Tab Y"))
M.one_pass(now=NEW + 1200)
d2 = dest()
check("S1 with _fu_cons_send_OFF.txt a new follow-up log waits", sum(f.startswith("followup_logs_") for f in d2) == 1, d2)
check("S2 ... and a clinical report still goes", sum(f.startswith("clinical_data_report_") for f in d2) == 2, d2)
os.remove(os.path.join(AR, "_fu_cons_send_OFF.txt"))
# the fetch's record unreadable: nothing of the two kinds is sent
with open(os.path.join(AR, "_server_fetch_state.json"), "w") as fh:
    fh.write("{not json")
M.one_pass(now=NEW + 1500)
check("U1 the fetch's record unreadable: the follow-up log waits", sum(f.startswith("followup_logs_") for f in dest()) == 1, dest())
with open(os.path.join(AR, "_server_fetch_state.json"), "w") as fh:
    json.dump({"have": {hashlib.md5(open(fetched, "rb").read()).hexdigest(): {"how": "fetched"}}}, fh)
M.one_pass(now=NEW + 1800)
check("U2 readable again: it goes", sum(f.startswith("followup_logs_") for f in dest()) == 2, dest())
check("O1 the file downloaded before 20-Nov 12:00 never sent", all("Dr Z" not in open(os.path.join(DE, f), encoding="utf-8").read() for f in dest()))
print("WALK %d/%d" % (sum(R), len(R)))
