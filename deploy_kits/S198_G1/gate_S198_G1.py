#!/usr/bin/env python3
"""S198_G1 gate — the gist filled (D241 buildable slice).
Run: python3 gate_S198_G1.py <portal.py> <portal_gist.py> --baseline <live_portal.py>"""
import importlib.util, subprocess, sys
PASS = FAIL = 0
def check(label, ok):
    global PASS, FAIL
    if ok: PASS += 1
    else:
        FAIL += 1; print("FAIL: " + label)
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

por_path, gist_path = sys.argv[1], sys.argv[2]
base_path = sys.argv[sys.argv.index("--baseline") + 1]

# 1 — the builder's own selftest, all green at the projected count
r = subprocess.run([sys.executable, gist_path, "--selftest"],
                   capture_output=True, text=True)
check("portal_gist selftest 27/27 (was 21; +6 exactly)",
      "SELFTEST: 27 checks, 0 failed" in r.stdout)

# 2 — the page renders the three new cards from a full payload
cand = load(por_path, "cand_g1")
FULL = {"ok": True, "stale": False, "age_min": 3, "gist": {
    "stale_after_min": 45, "sources_ok": True, "notes": [],
    "pipeline": {"never_recorded_7d": 0, "missed_7d": 4, "escalate_lokesh": False},
    "calls": {"in_today": 12, "out_today": 5, "in_7d": 80, "out_7d": 33},
    "unfiled_outcomes": 2, "third_strikes_7d": 1,
    "funnel": {"answered_7d": 61, "transcribed_7d": 58, "judged_7d": 55,
               "unjudged_open": 6, "top_unjudged_reason": "no transcript"},
    "staff_ai": {"total_7d": 55, "filed_7d": 49, "mismatch_7d": 3, "filed_pct": 89},
    "leads": {"new_7d": 9, "answered_7d": 7, "unanswered_7d": 2},
}}
cand._usable = lambda: True; cand._authed = lambda r: True
cand._sso_ready = lambda: True
cand._sso_user = lambda r: {"user": "manoj", "role": "doctor"}
cand._is_doctor = lambda r: True; cand._is_clinic_pc = lambda r: False
cand._gist_view = lambda path=None, now=None: FULL
with cand.app.test_client() as c:
    h = c.get("/portal/gist").get_data(as_text=True)
check("funnel card renders the three stages + unjudged reason",
      "Judgment funnel" in h and "61" in h and "58" in h and "55" in h
      and "no transcript" in h)
check("staff-vs-AI card: mismatch count + filed% + coach link",
      "3 mismatch" in h and "49/55" in h and "(89%)" in h
      and "/portal/console?view=staff" in h)
check("leads card: counts + open link",
      "New leads" in h and "7 answered" in h and "2 never reached" in h
      and "/portal/console?view=leads" in h)

# 3 — fail-loud: null blocks render as 'unavailable', never zero
NULLED = {"ok": True, "stale": False, "age_min": 3, "gist": dict(
    FULL["gist"], funnel=None, staff_ai=None, leads=None, sources_ok=False,
    notes=["console: connect refused"])}
cand._gist_view = lambda path=None, now=None: NULLED
with cand.app.test_client() as c:
    h = c.get("/portal/gist").get_data(as_text=True)
check("null console blocks say 'unavailable' (never a silent zero)",
      h.count("unavailable") >= 3 and "0 mismatch" not in h)

# 4 — zero tile changes vs the live baseline
base = load(base_path, "base_g1")
bt = {t["name"]: (t["url"], t["live"], tuple(t["roles"])) for t in base.TILES}
ct = {t["name"]: (t["url"], t["live"], tuple(t["roles"])) for t in cand.TILES}
check("ZERO tile changes vs live baseline", bt == ct)

print("GATE %d/%d %s" % (PASS, PASS + FAIL, "GREEN" if FAIL == 0 else "RED"))
sys.exit(0 if FAIL == 0 else 1)
