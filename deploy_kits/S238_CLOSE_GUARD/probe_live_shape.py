#!/usr/bin/env python3
"""probe_live_shape.py -- S238_CLOSE_GUARD. Runs the NEW staff_ledger.py against a
COPY of the real ledger (in a throw-away folder) BEFORE it is installed, and
renders the pages the owner uses. The live store is never opened for writing.
   usage: python3 probe_live_shape.py <new staff_ledger.py> <probe dir> <real ledger dir>"""
import sys, os, shutil, importlib.util, secrets, datetime
new, probe, real = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(probe, exist_ok=True); os.chmod(probe, 0o700)
for f in ("ledger.jsonl", "users.json", "ledger_settings.json", "advance_pct.json"):
    if os.path.exists(os.path.join(real, f)):
        shutil.copy2(os.path.join(real, f), os.path.join(probe, f))
os.environ["LEDGER_DIR"] = probe
spec = importlib.util.spec_from_file_location("sl_probe", new)
sl = importlib.util.module_from_spec(spec); spec.loader.exec_module(sl)
sl.LEDGER_DIR = probe
u = sl.load_users(); s = secrets.token_hex(16)
u["_s238probe"] = {"pw": sl.hash_pw("probe", s), "salt": s, "role": "checker", "staff_link": "", "active": True}
sl.save_users(u)
app = sl.create_app(); app.testing = True; c = app.test_client()
c.post(sl.URL_PREFIX + "/login", data={"u": "_s238probe", "p": "probe"})
fails, n = [], 0
def ck(cond, msg):
    global n; n += 1
    if not cond: fails.append(msg)
cur = datetime.date.today().strftime("%Y-%m")
staff = sorted({r["staff"] for r in sl.load_ledger() if r["category"] == "ADVANCE_ISSUE"}) or ["x"]
paths = ["/", "/advances", "/loans", "/pending", "/perks", "/book", "/salary?m=" + cur] + \
        ["/statement?staff=" + st for st in staff]
for p in paths:
    code = c.get(sl.URL_PREFIX + p).status_code
    ck(code == 200, "GET %s answered %d" % (p, code))
page = c.get(sl.URL_PREFIX + "/salary?m=" + cur).data.decode()
ck("opens on <b>" + sl.close_opens_on(cur) + "</b>" in page and ("Run monthly close for " + cur) not in page,
   "the running month (%s) offers no close, and says when it opens" % cur)
before = open(os.path.join(probe, "ledger.jsonl"), "rb").read()
r = c.post(sl.URL_PREFIX + "/salary/close", data={"m": cur}).data.decode()
ck("close NOT run" in r and open(os.path.join(probe, "ledger.jsonl"), "rb").read() == before,
   "a close of the running month is refused and writes nothing")
ck(sl.APP_VERSION == "3.7-S238-CLOSE-GUARD", "the new file is v3.7")
nrows = len(sl.load_ledger())
shutil.rmtree(probe, ignore_errors=True)
for f in fails: print("  FAIL: " + f)
print("live-shape probe: %d checks, %d failures (%d real rows copied, %d statements rendered)" % (n, len(fails), nrows, len(staff)))
sys.exit(1 if fails else 0)
