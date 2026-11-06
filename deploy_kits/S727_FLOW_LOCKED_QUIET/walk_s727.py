#!/usr/bin/env python3
"""walk_s727.py -- kit S727 (S724 checks, then a locked month) (session 390, the parent). The register's month-end flow on a made-up database, with a
stand-in salary engine (its compute() returns the figures the walk chooses); the real Flask routes of the file under test.
   python walk_s724.py <staff_register.py under test>          exit 0 = WALK OK
The control (the live file) must go RED."""
import datetime as dt, importlib.util, os, sys, tempfile, types

path = os.path.abspath(sys.argv[1])
t = tempfile.mkdtemp(prefix="s724_")
os.environ["SR_DB_PATH"] = os.path.join(t, "sr.db")
os.environ["ATT_REGISTER_DB"] = os.environ["SR_DB_PATH"]
sys.path.insert(0, os.path.dirname(path))
oks, fails = [], []


def ck(n, c):
    (oks if c else fails).append(n)
    print(("  ok   " if c else "  FAIL ") + n)


s = importlib.util.spec_from_file_location("sr_walk", path)
M = importlib.util.module_from_spec(s)
s.loader.exec_module(M)
M.init_db()
FIG = {"staff": [{"name": "Asha", "net": 9000.0, "late_charge": 0, "marks": {"P": 26}}], "ledger_closed": True, "enforced": True}
P = types.SimpleNamespace(compute=lambda ym, **k: {**FIG, "ym": ym}, load_settings=lambda: {"require_pack_approval": 1},
                          sheet1_html=lambda res, **k: "<html>S1 %s</html>" % k.get("approve_html", ""),
                          sheet2_html=lambda res, **k: "<html>S2 %s</html>" % k.get("approve_html", ""),
                          sheets34_html=lambda res, **k: "<html>S34</html>", hold_state=lambda: {}, prev_ym=lambda ym: ym,
                          money=lambda x: "%g" % x)
M._policy_module = lambda: (P, "")
M.current_user = lambda req: {"user": "manoj", "role": "doctor", "via": "sso", "caps": {k: True for k in ("active", "salary", "lock")}}
M.approval_blockers = lambda con, ym: {"missing": [], "draft": [], "required": 0, "approved": 0}
SAID = []
M._render_salary = lambda ym, u, msg="", msg_kind="block": (SAID.append(msg), "DESK: " + msg)[1]
import logging
M.app.logger.disabled = True
logging.getLogger("werkzeug").disabled = True
C = M.app.test_client()
today = dt.date.today()
prev = (today.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
cur = today.strftime("%Y-%m")

# 1 the flow's default month
with M.app.test_request_context("/register/salary/flow"):
    ck("1a the flow opens on the month just ended (%s), not the running month (%s)" % (prev, cur), M._flow_ym() == prev)
with M.app.test_request_context("/register/salary/flow?ym=2026-09"):
    ck("1b a month asked for is the month shown", M._flow_ym() == "2026-09")
with M.app.test_request_context("/register/salary/flow?ym=bad"):
    ck("1c a bad month falls back to the month just ended", M._flow_ym() == prev)
r = C.post("/register/salary/flow/approve", data={"ym": "bad", "sheet": "sheet1"})
ck("1d a bad approve press goes back to the month just ended", ("ym=" + prev) in r.headers.get("Location", ""))

# 2 an approval keeps its fingerprint
ym = "2026-11"
r = C.post("/register/salary/flow/approve", data={"ym": ym, "sheet": "sheet1"})
r = C.post("/register/salary/flow/approve", data={"ym": ym, "sheet": "sheet2"})
con = M.get_db()
rows = {x["sheet"]: dict(x) for x in con.execute("SELECT * FROM pack_approval WHERE ym=?", (ym,))}
con.close()
h = M._fig_hash(FIG["staff"]) if hasattr(M, "_fig_hash") else None
ck("2a both approvals stored with the fingerprint of the figures they were given on",
   h is not None and rows.get("sheet1", {}).get("fig_hash") == h and rows.get("sheet2", {}).get("fig_hash") == h)
st = M.pack_status(ym, FIG["staff"]) if h else {}
ck("2b with the same figures both hold", bool(st.get("sheet1")) and bool(st.get("sheet2")) and not st.get("_stale"))
ck("2c the fingerprint does not depend on the order of keys", h is not None and M._fig_hash([{"marks": {"P": 26}, "late_charge": 0, "net": 9000.0, "name": "Asha"}]) == h)
ck("2d a set in the figures does not make it unstable", h is not None and M._fig_hash([{"s": {"b", "a", "c"}}]) == M._fig_hash([{"s": {"c", "a", "b"}}]))

# 3 the figures change: the approval no longer holds
FIG["staff"][0]["net"] = 8500.0
st = M.pack_status(ym, FIG["staff"]) if h else {}
ck("3a a changed figure: neither approval holds, both named stale", not st.get("sheet1") and not st.get("sheet2") and set((st.get("_stale") or {})) == {"sheet1", "sheet2"})
pg = C.get("/register/salary/flow/sheet1?ym=" + ym).get_data(as_text=True)
ck("3b the sheet page offers APPROVE again and says why", "APPROVE SHEET 1" in pg and "no longer holds" in pg)
pg = C.get("/register/salary/flow?ym=" + ym).get_data(as_text=True)
ck("3c the flow page shows the approve buttons again and names the stale approval", "Approve Sheet 1" in pg and "figures have changed since" in pg)
M.month_has_ended = lambda ym: True
SAID.clear()
r = C.post("/register/salary/lock", data={"ym": ym})
ck("3d the lock refuses a stale approval, and says so", any("changed since" in (m or "") for m in SAID))
con = M.get_db()
ck("3e nothing was locked", not con.execute("SELECT 1 FROM locked_run WHERE ym=? AND status='locked'", (ym,)).fetchone())
con.close()

# 4 approved again on the new figures: it holds; the lock passes the approval check
C.post("/register/salary/flow/approve", data={"ym": ym, "sheet": "sheet1"})
C.post("/register/salary/flow/approve", data={"ym": ym, "sheet": "sheet2"})
st = M.pack_status(ym, FIG["staff"]) if h else {}
ck("4a approved again on the new figures, both hold", bool(st.get("sheet1")) and bool(st.get("sheet2")))
SAID.clear()
try:
    C.post("/register/salary/lock", data={"ym": ym})
except Exception:
    pass
ck("4b the lock goes past the approval check this time (no 'changed since', no 'not approved')",
   not any(("changed since" in (m or "")) or ("not approved yet" in (m or "")) for m in SAID))

# 5 an approval from before fingerprints (as October's) does not hold
con = M.get_db()
con.execute("INSERT OR REPLACE INTO pack_approval (ym, sheet, approved_by, approved_ts) VALUES ('2026-12','sheet1','manoj','2026-11-05 20:49:00')")
con.commit(); con.close()
st = M.pack_status("2026-12", FIG["staff"]) if h else {"sheet1": 1}
ck("5a an approval with no fingerprint is stale", not st.get("sheet1") and "sheet1" in (st.get("_stale") or {}))
ck("5b pack_status without figures is as before (the row is there)", bool(M.pack_status("2026-12").get("sheet1")))

# 6 the figures cannot be worked out: nothing is approved
M._policy_module = lambda: (None, "engine missing")
r = C.post("/register/salary/flow/approve", data={"ym": "2027-01", "sheet": "sheet1"})
con = M.get_db()
ck("6a the engine missing: NOT approved, and it says so", "NOT approved" in r.headers.get("Location", "").replace("%20", " ")
   and not con.execute("SELECT 1 FROM pack_approval WHERE ym='2027-01'").fetchone())
con.close()
# 7 S727: a locked month's approvals are history
M._policy_module = lambda: (P, "")
con = M.get_db()
cols = [r[1] for r in con.execute("PRAGMA table_info(locked_run)")]
vals = {"ym": "2026-10", "status": "locked", "locked_by": "manoj", "locked_ts": "2026-11-06 07:19:00", "total_payout": 1000, "report_html": ""}
use = [c for c in cols if c in vals]
con.execute("INSERT OR REPLACE INTO locked_run (%s) VALUES (%s)" % (",".join(use), ",".join("?" * len(use))), [vals[c] for c in use])
con.execute("INSERT OR REPLACE INTO pack_approval (ym, sheet, approved_by, approved_ts) VALUES ('2026-10','sheet1','manoj','2026-10-05 20:49:00')")
con.execute("INSERT OR REPLACE INTO pack_approval (ym, sheet, approved_by, approved_ts) VALUES ('2026-10','sheet2','manoj','2026-10-05 20:49:00')")
con.commit(); con.close()
pg = C.get("/register/salary/flow?ym=2026-10").get_data(as_text=True)
ck("7a a locked month's flow page shows its approvals, no 'approve again'", "figures have changed since" not in pg and "approved by manoj" in pg)
pg = C.get("/register/salary/flow/sheet1?ym=2026-10").get_data(as_text=True)
ck("7b a locked month's sheet page shows the approval, not the approve strip", "no longer holds" not in pg and "APPROVE SHEET 1" not in pg)
pg = C.get("/register/salary/flow?ym=" + ym).get_data(as_text=True)
FIG["staff"][0]["net"] = 7777.0
pg = C.get("/register/salary/flow?ym=" + ym).get_data(as_text=True)
ck("7c an unlocked month still says when its approval no longer holds", "figures have changed since" in pg)
print(("WALK OK %d/%d" % (len(oks), len(oks) + len(fails))) if not fails else ("WALK RED %d of %d failed" % (len(fails), len(oks) + len(fails))))
sys.exit(1 if fails else 0)
