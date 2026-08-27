#!/usr/bin/env python3
"""
f195_proof.py  --  S205 · F-195 · THE PREDICATE-LEVEL RED PROOF

WHAT F-195 SAYS
---------------
    "Both checks passed for reasons other than the ones they name -- and so
     does the check written to fix them. Reverting the gate still gives
     721/721."

The S203 fix added a test that CLAIMS to post "the REAL caller's shape --
token header, NO session".  It does not.  `app.test_client()` carries no
cookie, but it does not need one: the selftest has already switched on
FINANCE_ALLOW_HEADER_AUTH and set FINANCE_DEV_USER / FINANCE_DEV_ROLE, so
`current_user()` hands back an identity to ANY client, `roles_for()` grants
that role outright, and `_gate()` returns None at the ROLE clause -- never
reaching the token clause the test exists to prove.

Delete the token clause and the test stays green.  That is the fault.

WHY THIS FILE EXISTS AND NOT A LIVE RUN
---------------------------------------
`selftest()` copies the LIVE finance database and cannot be run offline
against a fresh store -- the same limit that was stated out loud for the
S204_C2 kit.  So this does what was done there: it proves the PREDICATE.
`_gate`, `current_user` and `roles_for` below are the LIVE BYTES, copied
verbatim from

    deploy_kits/S204_C2/finance_app.py      (md5 70f79997... -- the running file)
        current_user()  lines 216-227
        _gate()         lines 245-299
        roles_for()     lines 316-326

with only the surrounding app trimmed away.  Nothing in the logic is
paraphrased; if it were, this proof would be worth nothing (F-208).

THE MATRIX IT RUNS
------------------
    two test styles      x   two gate states       =  four cells

      S203 test as written  |  gate exemption PRESENT   -> expect 200
      S203 test as written  |  gate exemption REMOVED   -> ??? <-- F-195
      fixed test            |  gate exemption PRESENT   -> expect 200
      fixed test            |  gate exemption REMOVED   -> ??? <-- the proof

A test that bites must go RED in the bottom-right cell.  The top-right cell
staying GREEN is F-195 itself, demonstrated rather than argued.

    python3 f195_proof.py
"""
import os
import sys

from flask import Flask, jsonify, redirect, request

# --------------------------------------------------------------- the switches
# These two are the whole experiment. Everything else is live bytes.
GATE_EXEMPTION = True     # are lines 266-269 of finance_app.py present?
NEUTRALISE_IDENTITY = False   # does the test really strip its own identity?

# ------------------------------------------------------- live module globals
# finance_app.py:121  ALLOW_HEADER_AUTH = os.environ.get(...) == "1"
ALLOW_HEADER_AUTH = False
# finance_app.py:128  MARG_TOKEN = os.environ.get("FINANCE_MARG_TOKEN", "")
MARG_TOKEN = ""
CRON_TOKEN = ""
RENEWALS_TOKEN = ""
PORTAL_LOGIN = "https://portal.example/login"
UNIT = "medical"
CLINIC_UNIT = "clinic"
CLINIC_NAME = "Advanced Orthopaedic Surgery Centre"

PUBLIC_PATHS = ("/finance/healthz",
                "/finance/scan/widget.js",
                "/finance/scan/jspdf.js")
IDENTITY_ONLY_PATHS = ("/finance/api/whoami", "/finance/clinic/api/whoami")

SSO_ROLE_MAP = {}
FINANCE_ROLES = ("maker", "checker", "viewer")

app = Flask(__name__)


def _sso_identity():
    """Live behaviour with no clinic cookie present: None.

    The real one verifies a signed cookie against the portal's key store. No
    test client in the suite ever carries that cookie, so for every cell of
    this matrix the live function returns None -- which is what this returns.
    """
    return None


def _unit_for_path(path):
    return CLINIC_UNIT if path.startswith("/finance/clinic/") else UNIT


class _Con:
    """unit_role, as the live DB answers it for a user who has no row.

    THE POINT: the identity the selftest invents ('selftest'/'checker') has NO
    unit_role row. It is granted its role purely by the ALLOW_HEADER_AUTH line
    inside roles_for(). So this returning nothing is not a simplification --
    it is the condition under which the fault appears.
    """
    def execute(self, *_a, **_k):
        return []


def db():
    return _Con()


# ============================ LIVE BYTES: current_user() =====================
# finance_app.py lines 216-227, verbatim.
def current_user():
    """Who is asking. Cookie first; headers only when explicitly allowed."""
    ident = _sso_identity()
    if ident:
        return ident
    if ALLOW_HEADER_AUTH:
        return {"user": request.headers.get("X-Clinic-User")
                        or os.environ.get("FINANCE_DEV_USER") or "",
                "role": request.headers.get("X-Clinic-Role")
                        or os.environ.get("FINANCE_DEV_ROLE") or ""}
    return {"user": "", "role": ""}


# ============================ LIVE BYTES: roles_for() ========================
# finance_app.py lines 316-326, verbatim.
def roles_for(con, unit, username, sso_role):
    """Roles are PER UNIT (S179): the doctor checks everything, Dr Bhawna also
    checks lab and clinic, each unit has its own maker. unit_role is the
    authority; the broker role only grants what SSO_ROLE_MAP says it grants."""
    got = {r["role"] for r in con.execute(
        "SELECT role FROM unit_role WHERE unit=? AND lower(username)=lower(?) AND active=1",
        (unit, username or ""))}
    got |= SSO_ROLE_MAP.get((sso_role or "").lower(), set())
    if ALLOW_HEADER_AUTH and sso_role in FINANCE_ROLES:
        got.add(sso_role)                    # offline testing only
    return got


# ============================ LIVE BYTES: _gate() ============================
# finance_app.py lines 245-299, verbatim -- EXCEPT that the four lines the
# experiment removes are wrapped in `if GATE_EXEMPTION:` so one run can have
# them and the next cannot. The condition itself is unchanged.
@app.before_request
def _gate():
    """FAIL CLOSED. Every route except the allow-list needs a resolved identity."""
    p = request.path.rstrip("/") or request.path
    if p in PUBLIC_PATHS or request.path in PUBLIC_PATHS:
        return None
    if CRON_TOKEN and request.headers.get("X-Finance-Cron") == CRON_TOKEN:
        return None
    # ---- finance_app.py lines 266-269. THE CLAUSE UNDER TEST. ----
    if GATE_EXEMPTION:
        if MARG_TOKEN and p in ("/finance/api/marg-push",
                                "/finance/api/pipeline-status") \
                and request.headers.get("X-Finance-Marg") == MARG_TOKEN:
            return None
    # --------------------------------------------------------------
    if RENEWALS_TOKEN and p == "/finance/api/renewals-push" \
            and request.headers.get("X-Finance-Renewals") == RENEWALS_TOKEN:
        return None
    u = current_user()
    if not u.get("user"):
        if request.path.startswith(("/finance/api/", "/finance/clinic/api/")):
            return jsonify(ok=False, error="not_signed_in",
                           message="Sign in on the clinic portal first."), 401
        return redirect(PORTAL_LOGIN, code=302)

    if request.path.rstrip("/") in IDENTITY_ONLY_PATHS:
        return None
    unit = _unit_for_path(request.path)
    if roles_for(db(), unit, u["user"], u.get("role")):
        return None
    if request.path.startswith(("/finance/api/", "/finance/clinic/api/")):
        return jsonify(ok=False, error="no_role_here",
                       message="You are signed in, but you have no role in %s."
                               % (CLINIC_NAME if unit == CLINIC_UNIT
                                  else "Sanjeevni Medicos")), 403
    return redirect(PORTAL_LOGIN, code=302)


# ==================== LIVE BYTES: the handler's own check ====================
# finance_app.py lines 4368-4393, trimmed to the auth half -- the DB write is
# not part of the predicate and a fake store would prove nothing about it.
@app.route("/finance/api/pipeline-status", methods=["POST"])
def api_pipeline_status():
    tok = os.environ.get("FINANCE_MARG_TOKEN", "")
    if not tok:
        return jsonify(ok=False, error="not_configured",
                       message="FINANCE_MARG_TOKEN is not set on the server."), 503
    if request.headers.get("X-Finance-Marg", "") != tok:
        return jsonify(ok=False, error="not_signed_in",
                       message="Sign in on the clinic portal first."), 401
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(ok=False, error="bad_payload",
                       message="a JSON object is required"), 400
    src = str(body.get("source") or "manojz")[:40]
    return jsonify(ok=True, source=src, received_at="2026-08-27T00:00:00")


# ============================================================================
#  THE TEST UNDER TEST
# ============================================================================
B2TOK = "smoke-b2-token"


def selftest_state():
    """The state the real selftest has already put the process in by the time
    it reaches the B2 block.

    finance_app.py:6813-6815 set ALLOW_HEADER_AUTH = True and the dev user;
    finance_app.py:9019 sets FINANCE_DEV_ROLE = 'checker'. Nothing between
    there and the B2 block at 9195 unsets any of them. That is the whole
    reason the 'anonymous' client is not anonymous.
    """
    global ALLOW_HEADER_AUTH, MARG_TOKEN
    ALLOW_HEADER_AUTH = True
    os.environ["FINANCE_DEV_USER"] = "selftest"
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    os.environ["FINANCE_MARG_TOKEN"] = B2TOK
    MARG_TOKEN = B2TOK


def the_b2_shape_test():
    """finance_app.py lines 9222-9240, the S203 fix's own test, verbatim in
    behaviour. It claims: 'the REAL caller's shape -- token header, NO session
    -- gets past _gate()'.

    NEUTRALISE_IDENTITY is the one-line difference between the test as it is
    written today and the test as it must be written to bite.
    """
    global ALLOW_HEADER_AUTH
    _saved = (ALLOW_HEADER_AUTH,
              os.environ.get("FINANCE_DEV_USER"),
              os.environ.get("FINANCE_DEV_ROLE"))
    try:
        if NEUTRALISE_IDENTITY:
            # ---- THE FIX. Three lines. A client that claims to have no
            # ---- session must actually have no way to acquire one.
            ALLOW_HEADER_AUTH = False
            os.environ.pop("FINANCE_DEV_USER", None)
            os.environ.pop("FINANCE_DEV_ROLE", None)
        _anon = app.test_client()
        r_good = _anon.post("/finance/api/pipeline-status",
                            json={"source": "manojz-shape"},
                            headers={"X-Finance-Marg": B2TOK})
        r_bad = _anon.post("/finance/api/pipeline-status",
                           json={"source": "manojz-shape"},
                           headers={"X-Finance-Marg": "not-the-token"})
        return r_good.status_code, r_bad.status_code
    finally:
        ALLOW_HEADER_AUTH, _u, _r = _saved
        if _u is not None:
            os.environ["FINANCE_DEV_USER"] = _u
        if _r is not None:
            os.environ["FINANCE_DEV_ROLE"] = _r


def cell(exemption, neutralise):
    global GATE_EXEMPTION, NEUTRALISE_IDENTITY
    GATE_EXEMPTION = exemption
    NEUTRALISE_IDENTITY = neutralise
    selftest_state()
    good, bad = the_b2_shape_test()
    # The claim the test makes, as the suite scores it:
    passes = (good == 200)
    return good, bad, passes


def main():
    print(__doc__.split("THE MATRIX IT RUNS")[0].rstrip())
    print("=" * 74)
    print("F-195 PREDICATE PROOF -- _gate/current_user/roles_for are live bytes")
    print("=" * 74)
    print()
    rows = []
    for neutralise, tname in ((False, "S203 test AS WRITTEN"),
                              (True,  "FIXED test (identity stripped)")):
        for exemption, gname in ((True,  "gate clause PRESENT"),
                                 (False, "gate clause REMOVED")):
            good, bad, passes = cell(exemption, neutralise)
            rows.append((tname, gname, good, bad, passes))

    print("%-32s %-22s %-9s %-9s %s"
          % ("test", "gate", "good tok", "bad tok", "suite says"))
    print("-" * 92)
    for tname, gname, good, bad, passes in rows:
        print("%-32s %-22s %-9s %-9s %s"
              % (tname, gname, good, bad, "PASS" if passes else "*** FAIL ***"))
    print()

    # ------------------------------------------------------------- the verdict
    as_written_present = rows[0][4]
    as_written_removed = rows[1][4]
    fixed_present = rows[2][4]
    fixed_removed = rows[3][4]

    verdicts = []

    def say(ok, line):
        verdicts.append((ok, line))
        print("%s  %s" % ("OK  " if ok else "FAIL", line))

    say(as_written_present,
        "as-written test passes while the gate clause is present")
    say(as_written_removed,
        "F-195 REPRODUCED: the gate clause is REMOVED and the test the S203 "
        "close\n      wrote to catch exactly that is STILL GREEN. It never "
        "reached the clause.")
    say(fixed_present,
        "fixed test still passes on the real, unmodified gate -- no false red")
    say(not fixed_removed,
        "THE PROOF: with the identity stripped, removing the gate clause turns "
        "the\n      test RED (HTTP %s, not 200). The test now bites."
        % rows[3][2])

    print()
    bad_cells = [v for v in verdicts if not v[0]]
    if bad_cells:
        print("PROOF INCOMPLETE -- %d expectation(s) did not hold." % len(bad_cells))
        return 1
    print("=" * 74)
    print("F-195 PROVEN, AND THE FIX PROVEN TO BITE.")
    print()
    print("  The fix is three lines inside the existing try: at finance_app.py")
    print("  line 9226 -- set ALLOW_HEADER_AUTH False and clear FINANCE_DEV_USER")
    print("  and FINANCE_DEV_ROLE, restoring all three in the finally: at 9239.")
    print()
    print("  SCOPE, SAID OUT LOUD: this proves the GATE PREDICATE, not a live")
    print("  721/721 run. selftest() copies the live database and cannot run")
    print("  offline against a fresh store -- the same limit stated for the")
    print("  S204_C2 kit, and stated here rather than letting an offline green")
    print("  stand in for the thing it does not test.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
