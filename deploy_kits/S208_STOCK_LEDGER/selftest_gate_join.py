#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_gate_join.py — the proof that was missing, and cost S207 a dead loop.

THE FAULT THIS EXISTS TO CATCH
    The S207 kit proved two halves and never the join between them:
      * push_snapshot.py --dry-run  returns BEFORE the network call
      * selftest_stock_app.py       drives the routes through a test client
                                    inside a bare app that has NO front gate
    So nothing anywhere exercised: real header -> real gate -> real route.
    The header was wrong (the MARG token sent as X-Finance-Cron) and the path
    was not allow-listed, so every real push would have been refused 401 --
    silently, to a console nobody reads.

WHAT THIS DOES
    Builds a miniature app carrying finance_app.py's ACTUAL fail-closed gate,
    verbatim, runs patch_finance_app.py over it exactly as the installer does,
    mounts the real stock_app, and drives the real routes with the real header
    that push_snapshot.py sends.

    python3 selftest_gate_join.py      exit 0 = passed, 1 = a check failed
"""
import io
import json
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from flask import Flask, jsonify, request        # noqa: E402
import patch_finance_app as P                     # noqa: E402

_fail, _pass = [], 0


def ck(label, cond, detail=""):
    global _pass
    if cond:
        _pass += 1
        print("  ok   %s" % label)
    else:
        _fail.append(label)
        print("  FAIL %s   %s" % (label, detail))


# ---------------------------------------------------------------------------
# A miniature finance_app. The gate below is COPIED VERBATIM from the live
# finance_app.py's @app.before_request _gate() -- the token branches and the
# fail-closed fallthrough. If the real gate is ever rewritten, the patcher's
# anchor check refuses and this test's anchors stop matching too. That is the
# intended failure: loud, not silent.
# ---------------------------------------------------------------------------
MINI = '''import os
from flask import Flask, jsonify, request

UNIT = "medical"
MARG_TOKEN = os.environ.get("FINANCE_MARG_TOKEN", "")
CRON_TOKEN = os.environ.get("FINANCE_CRON_TOKEN", "")
PUBLIC_PATHS = ("/finance/healthz",)
SIGNED_IN = {"who": None}          # the test drives this

app = Flask(__name__)


def db():
    import sqlite3
    if not hasattr(db, "con"):
        db.con = sqlite3.connect(os.environ["MINI_DB"], check_same_thread=False)
        db.con.row_factory = sqlite3.Row
    return db.con


@app.before_request
def _gate():
    p = request.path.rstrip("/") or request.path
    if p in PUBLIC_PATHS or request.path in PUBLIC_PATHS:
        return None
    if CRON_TOKEN and request.headers.get("X-Finance-Cron") == CRON_TOKEN:
        return None
    if MARG_TOKEN and p in ("/finance/api/marg-push",
                            "/finance/api/pipeline-status") \\
            and request.headers.get("X-Finance-Marg") == MARG_TOKEN:
        return None
    if not SIGNED_IN["who"]:
        return jsonify(ok=False, error="no_identity"), 401
    return None


def require(*roles, unit=UNIT):
    who = SIGNED_IN["who"]
    if not who or who[1] not in roles:
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return {"user": who[0], "role": who[1]}, None


if __name__ == "__main__":
    app.run()
'''

tmp = tempfile.mkdtemp(prefix="gate_join_")
MOD = os.path.join(tmp, "mini_app.py")
with io.open(MOD, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(MINI)
os.environ["MINI_DB"] = os.path.join(tmp, "t.db")
TOK = "test-marg-token-not-a-real-secret"
os.environ["FINANCE_MARG_TOKEN"] = TOK
os.environ["FINANCE_CRON_TOKEN"] = "a-completely-different-cron-secret"

print("[1] the patcher, on a gate shaped like the real one")
src = P.read(MOD)
ok, notes = P.check(src)
ck("every anchor found exactly once", ok, notes)

print("\n[2] BEFORE the patch — this is what S207 would have shipped")
sys.path.insert(0, tmp)
import mini_app                                   # noqa: E402
import stock_app                                  # noqa: E402
stock_app.init(mini_app.app, mini_app.db, mini_app.require,
               unit="medical", marg_token=TOK)
c = mini_app.app.test_client()
mini_app.SIGNED_IN["who"] = None

r = c.post("/finance/stock/api/snapshot",
           json={"as_on": "27-08-2026", "items": [{"item": "X", "qty": 1}]},
           headers={"X-Finance-Cron": TOK})       # the S207 header, S207 gate
ck("the Marg token sent as X-Finance-Cron is refused 401 by the gate",
   r.status_code == 401, r.status_code)
ck("and the route never ran — nothing was written",
   sqlite3.connect(os.environ["MINI_DB"]).execute(
       "SELECT count(*) FROM sqlite_master WHERE name='stock_snapshot'"
   ).fetchone()[0] == 0)
r = c.post("/finance/stock/api/snapshot", json={"as_on": "27-08-2026", "items": [{"item": "X"}]},
           headers={"X-Finance-Marg": TOK})
ck("even the RIGHT header is refused while the path is not allow-listed",
   r.status_code == 401, r.status_code)

print("\n[3] apply the patch, exactly as the installer does")
P.write(MOD, P.apply(src))
import importlib                                   # noqa: E402
mini_app = importlib.reload(mini_app)
# NOTE: no init() call here. The patch itself mounts the blueprint at import
# time -- that IS the thing under test. Calling init() again would register the
# blueprint twice and Flask would refuse, which is a fair proof in itself.
c = mini_app.app.test_client()
mini_app.SIGNED_IN["who"] = None

print("\n[4] AFTER — the real header, the real gate, the real route")
r = c.post("/finance/stock/api/snapshot", json={"as_on": "", "items": []},
           headers={"X-Finance-Marg": TOK})
ck("an EMPTY body answers 400 bad_request — what --verify checks for",
   r.status_code == 400 and r.get_json().get("error") == "bad_request",
   (r.status_code, r.get_json()))
r = c.post("/finance/stock/api/snapshot",
           json={"as_on": "27-08-2026", "source": "push_snapshot",
                 "items": [{"item": "ACILOC 300", "qty": 77, "pack_size": 20}]},
           headers={"X-Finance-Marg": TOK})
ck("a real snapshot is accepted with NOBODY signed in", r.status_code == 200,
   (r.status_code, r.get_data(as_text=True)[:120]))
ck("and it landed", r.get_json().get("items") == 1)

print("\n[5] the token still opens NOTHING else")
for path, method in (("/finance/stock/api/count", "post"), ("/finance/stock/api/open", "get"),
                     ("/finance/stock/api/losses", "get"), ("/finance/api/anything", "get")):
    r = getattr(c, method)(path, json={}, headers={"X-Finance-Marg": TOK})
    ck("%-24s is still refused" % path, r.status_code in (401, 403), r.status_code)

print("\n[6] a signed-in human is unaffected by any of this")
mini_app.SIGNED_IN["who"] = ("drmanoj", "checker")
ck("a checker may read the losses", c.get("/finance/stock/api/losses").status_code == 200)
mini_app.SIGNED_IN["who"] = ("darpan", "maker")
ck("a maker may load a snapshot",
   c.post("/finance/stock/api/snapshot",
          json={"as_on": "28-08-2026", "items": [{"item": "ACILOC 300", "qty": 77}]}
          ).status_code == 200)

print("\n[7] the patch reverses exactly")
P.write(MOD, P.revert(P.read(MOD)))
ck("byte-identical to before the patch", P.read(MOD) == MINI)

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail:
    print("  FAILED:", f)
import shutil                                      # noqa: E402
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if _fail else 0)
