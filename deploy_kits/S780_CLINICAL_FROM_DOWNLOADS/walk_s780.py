"""S780 walk: python -B walk_s780.py <dir holding docterz_clinical_send.py>   (made-up files in a temp folder; prints WALK OK n/n)"""
import sys, os, tempfile, importlib, time, json, hashlib
code = sys.argv[1]
root = tempfile.mkdtemp(prefix="s780.")
dl, ar, de = (os.path.join(root, x) for x in ("Downloads", "Archive", "Drive"))
for d in (dl, ar, de):
    os.makedirs(d)
os.environ.update(CLINICAL_SEND_DOWNLOADS=dl, CLINICAL_SEND_ARCHIVE=ar, CLINICAL_SEND_DEST=de, CLINICAL_SEND_ALL_OFF=os.path.join(root, "ALL_OFF.txt"))
sys.path.insert(0, code); S = importlib.import_module("docterz_clinical_send")
CL = "Sr No,Patient Name,Patient UID,Consultation Date,Mode Of Payment,Diagnosis,Drugs Prescribed,Follow Up\nDr. Manoj Agarwal Clinic\n1,T A,WUID1,01-03-2031 10:00 AM,Cash,OA KNEE,x,15-03-2031\n2,T B,WUID2,14-03-2031 11:00 AM,UPI,,,\n"
CO = "Sr No,Patient Name,Patient UID,Consultation Date,Mode Of Payment,Bill Amount\nDr. Manoj Agarwal Clinic\n1,T A,WUID1,14-03-2031 10:00 AM,Cash,500\n"
def put(name, text, age):
    p = os.path.join(dl, name); open(p, "w").write(text); t = time.time() - age; os.utime(p, (t, t)); return p
res = []
def check(n, c): res.append((n, bool(c)))
put("clinical data report (1).csv", CL, 600)
put("consultation_report_x.csv", CO, 600)
old = put("clinical data report.csv", CL.replace("OA KNEE", "OLD"), 600); t = S.FROM_DAY - 86400; os.utime(old, (t, t))
put("clinical data report (2).csv", CL.replace("OA KNEE", "FRESH"), 10)
r = S.one_pass()
got = sorted(os.listdir(de))
check("one pass sends exactly one file", r == "sent 1" and len(got) == 1)
check("the clinical report (any name) is the one sent, named by its latest day", got and got[0].startswith("clinical_data_report_2031-03-14_manojz_"))
check("the bytes in Drive are the original's", got and hashlib.md5(open(os.path.join(de, got[0]), "rb").read()).hexdigest() == hashlib.md5(CL.encode()).hexdigest())
check("a consultation report is not sent", not any("OLD" in open(os.path.join(de, g)).read() or "Bill Amount" in open(os.path.join(de, g)).read() for g in got))
check("the original stays in Downloads", os.path.exists(os.path.join(dl, "clinical data report (1).csv")))
check("no temporary file is left in Drive", not any(g.startswith("~") for g in os.listdir(de)))
r2 = S.one_pass()
check("a second pass sends nothing again", r2 == "sent 0" and len(os.listdir(de)) == 1)
f2 = os.path.join(dl, "clinical data report (2).csv"); t = time.time() - 600; os.utime(f2, (t, t))
r3 = S.one_pass()
check("a file still being written waits, then goes on a later pass", r3 == "sent 1" and len(os.listdir(de)) == 2)
check("the file downloaded before 10-Nov-2026 is never sent", not any("OLD" in open(os.path.join(de, g)).read() for g in os.listdir(de)))
open(os.path.join(ar, "_clinical_send_OFF.txt"), "w").write("off"); put("clinical data report (3).csv", CL.replace("OA KNEE", "OFFTEST"), 600)
check("the switch stops it", S.one_pass() == "off" and len(os.listdir(de)) == 2)
os.remove(os.path.join(ar, "_clinical_send_OFF.txt"))
os.rename(de, de + "_gone")
check("no Drive folder: nothing sent, it says so", S.one_pass() == "no-dest")
os.rename(de + "_gone", de)
log = open(os.path.join(ar, "_clinical_send_log.txt")).read()
check("the log carries no name", "T A" not in log and "T B" not in log)
check("main() always ends 0", S.main() == 0)
bad = [n for n, ok in res if not ok]
for n, ok in res:
    print(("ok    " if ok else "FAIL  ") + n)
print(("WALK OK %d/%d" % (len(res), len(res))) if not bad else "WALK FAILED %d/%d" % (len(res) - len(bad), len(res)))
