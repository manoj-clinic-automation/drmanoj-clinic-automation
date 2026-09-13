#!/usr/bin/env python3
"""probe_live_shape_s247.py -- runs the NEW staff_ledger.py against a COPY of the
REAL ledger, in a throw-away folder, BEFORE anything is installed.

It renders every page the owner uses, and then actually performs the new collection
on the copy, so the thing being installed is proven on his own data rather than on a
fixture. The live store is only ever READ.

   usage: python3 probe_live_shape_s247.py <new staff_ledger.py> <probe dir> <real ledger dir>
"""
import datetime
import importlib.util
import os
import secrets
import shutil
import sys

new, probe, real = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(probe, exist_ok=True)
os.chmod(probe, 0o700)
for f in ("ledger.jsonl", "users.json", "ledger_settings.json", "advance_pct.json"):
    if os.path.exists(os.path.join(real, f)):
        shutil.copy2(os.path.join(real, f), os.path.join(probe, f))
os.environ["LEDGER_DIR"] = probe
spec = importlib.util.spec_from_file_location("sl_probe", new)
sl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl)
sl.LEDGER_DIR = probe

u = sl.load_users()
s = secrets.token_hex(16)
u["_s247probe"] = {"pw": sl.hash_pw("probe", s), "salt": s, "role": "checker",
                   "staff_link": "", "active": True}
sl.save_users(u)
app = sl.create_app()
app.testing = True
c = app.test_client()
c.post(sl.URL_PREFIX + "/login", data={"u": "_s247probe", "p": "probe"})

fails, n = [], 0


def ck(cond, msg):
    global n
    n += 1
    if not cond:
        fails.append(msg)


LEDGER = os.path.join(probe, "ledger.jsonl")


def raw():
    return open(LEDGER, "rb").read() if os.path.exists(LEDGER) else b""


cur = datetime.date.today().strftime("%Y-%m")
staff = sorted({r["staff"] for r in sl.load_ledger()
                if r["category"] == "ADVANCE_ISSUE"}) or ["x"]
paths = ["/", "/advances", "/loans", "/pending", "/perks", "/book", "/salary?m=" + cur] + \
        ["/statement?staff=" + st for st in staff]
for p in paths:
    code = c.get(sl.URL_PREFIX + p).status_code
    ck(code == 200, "GET %s answered %d" % (p, code))

ck(sl.APP_VERSION == "3.8-S247-LATE-COLLECT", "the new file is v3.8")

# ---- the close is still the close: an early one is still refused, writes nothing
before = raw()
r = c.post(sl.URL_PREFIX + "/salary/close", data={"m": cur}).data.decode()
ck("close NOT run" in r and raw() == before,
   "a close of the running month is still refused and writes nothing")

# ---- the new control, on his real open advances -----------------------------
rows = sl.load_ledger()
closed = sl.closed_months(rows)
ck(bool(closed), "the ledger has at least one closed month to offer")
opens = sl.open_advances()
offer = [(a, m) for a in opens for m in closed
         if not sl.late_collect_blocked(a["issue"], m, rows)]
page = c.get(sl.URL_PREFIX + "/advances").data.decode()
if offer:
    ck("/late-collect" in page, "the advances page offers the new control")
    ck("<option value='%s'>" % offer[0][1] in page,
       "a collectable month appears in the control")
else:
    ck("/late-collect" not in page,
       "with nothing collectable the control is not shown at all")

# ---- refusals write nothing, on his real data -------------------------------
if opens:
    aid = opens[0]["issue"]["id"]
    before = raw()
    body = c.post(sl.URL_PREFIX + "/late-collect",
                  data={"id": aid, "month": cur, "reason": "probe"}).data.decode()
    ck("NOT recorded" in body and raw() == before,
       "a collection into a month that is not closed is refused and writes nothing")
    before = raw()
    body = c.post(sl.URL_PREFIX + "/late-collect",
                  data={"id": aid, "month": (closed[0] if closed else cur),
                        "reason": "   "}).data.decode()
    ck("NOT recorded" in body and raw() == before,
       "a collection without a reason is refused and writes nothing")

# ---- and the real thing, once, on the copy ----------------------------------
did = ""
if offer:
    a, m = offer[0]
    aid = a["issue"]["id"]
    bal = a["balance"]
    n_before = len(sl.load_ledger())
    before = raw()
    code = c.post(sl.URL_PREFIX + "/late-collect",
                  data={"id": aid, "month": m, "reason": "probe on a copy"}).status_code
    after = sl.load_ledger()
    ck(code == 302, "the collection posts and returns to the page")
    ck(len(after) == n_before + 1, "exactly one row is written")
    ck(raw().startswith(before), "the ledger stays append-only — nothing before it moved")
    got = [r for r in after if r["category"] == "ADVANCE_INSTALMENT"
           and r["contra_of"] == aid and r.get("closed_month") == m
           and r["status"] == "APPROVED"]
    ck(len(got) == 1 and got[0]["amount"] == -bal,
       "the month now carries exactly that collection")
    ck(not any(x["issue"]["id"] == aid for x in sl.open_advances()),
       "the advance is settled and leaves the open list")
    body = c.post(sl.URL_PREFIX + "/late-collect",
                  data={"id": aid, "month": m, "reason": "twice"}).data.decode()
    ck("already has a collection" in body, "a second one for that month is refused")
    did = " — collected Rs %d for %s against %s, on the copy" % (bal, a["issue"]["staff"], m)

nrows = len(sl.load_ledger())
shutil.rmtree(probe, ignore_errors=True)
for f in fails:
    print("  FAIL: " + f)
print("live-shape probe: %d checks, %d failures (%d rows in the copy, %d statements rendered)%s"
      % (n, len(fails), nrows, len(staff), did))
sys.exit(1 if fails else 0)
