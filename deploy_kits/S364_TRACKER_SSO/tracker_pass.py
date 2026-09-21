#!/usr/bin/env python3
# tracker_pass.py -- kit S364_TRACKER_SSO (session 279, 21-Sep-2026)
# The Callback Tracker opened from the Clinic app, already signed in.
#
# WHY A PASS AND NOT THE COOKIE
#   The Tracker is a Google web app (script.google.com). It can never read the portal's
#   clinic_sso cookie, which lives on .dr-manoj.in. So when a signed-in person taps the
#   Call Tracker tile, the portal mints a SHORT pass (120 seconds) and sends the browser to
#   the Tracker with it. The Tracker hands the pass straight back to the portal's redeem
#   address, server to server (UrlFetchApp), and the portal answers who it belongs to.
#   The Tracker then signs that person in with their own agent key, exactly as if they had
#   typed it. The typed-key login keeps working unchanged as the fallback.
#
# NO NEW SECRET TO CARRY
#   The pass is signed with a key DERIVED from the portal's existing CLINIC_SSO_SECRET
#   (HMAC(secret, "tracker-pass-v1")), and only the portal ever checks it. So nothing new
#   has to be copied into Google, and a pass can never be used as a clinic_sso cookie
#   (different key), nor a cookie as a pass.
#
# ONE USE
#   The Tracker remembers every pass it has redeemed for 10 minutes and refuses a second
#   use; the pass itself dies after 120 seconds. "Sign out everywhere" (the epoch) also
#   kills every pass at once, as it kills every cookie.
#
# Pure standard library. Never prints or logs the secret or a pass.

import base64
import hashlib
import hmac
import json
import secrets
import time

PASS_TTL = 120
PASS_PURPOSE = b"tracker-pass-v1"


def _b64u(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _unb64u(txt):
    return base64.urlsafe_b64decode(txt + "=" * (-len(txt) % 4))


def _key(secret):
    if not secret:
        raise RuntimeError("no SSO secret -- refusing to mint or check a Tracker pass")
    return hmac.new(secret.encode("utf-8"), PASS_PURPOSE, hashlib.sha256).digest()


def mint(user, role, epoch, secret, now=None, ttl=PASS_TTL):
    """A signed pass for one signed-in person: <payload_b64u>.<sig_b64u>."""
    now = int(time.time()) if now is None else int(now)
    body = {"a": "tracker", "u": str(user), "r": str(role), "e": int(epoch),
            "iat": now, "exp": now + int(ttl), "n": secrets.token_urlsafe(9)}
    p = _b64u(json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    s = _b64u(hmac.new(_key(secret), p.encode("ascii"), hashlib.sha256).digest())
    return p + "." + s


def redeem(token, secret, current_epoch=None, now=None):
    """{user, role, exp} for a good pass, else None. Checks shape, signature, purpose,
    expiry and the sign-out-everywhere epoch. One-use is the Tracker's job (it is the
    only redeemer); this answer is the same however often it is asked."""
    if not token or not isinstance(token, str) or len(token) > 600 or token.count(".") != 1:
        return None
    p, s = token.split(".", 1)
    try:
        want = _b64u(hmac.new(_key(secret), p.encode("ascii"), hashlib.sha256).digest())
    except Exception:
        return None
    if not hmac.compare_digest(s, want):
        return None
    try:
        body = json.loads(_unb64u(p).decode("utf-8"))
        exp, iat, ep = int(body["exp"]), int(body["iat"]), int(body["e"])
    except Exception:
        return None
    now = int(time.time()) if now is None else int(now)
    if body.get("a") != "tracker" or now > exp or iat > now + 30 or exp - iat > PASS_TTL:
        return None
    if current_epoch is not None and ep < int(current_epoch):
        return None
    return {"user": body.get("u"), "role": body.get("r"), "exp": exp}


def _selftest():
    import clinic_sso
    n = 0
    S = "test-secret-not-real"

    def ok(c, label):
        nonlocal n
        assert c, "FAIL: " + label
        n += 1

    t0 = 2_000_000
    t = mint("shavez", "staff", 4, S, now=t0)
    d = redeem(t, S, current_epoch=4, now=t0 + 5)
    ok(d == {"user": "shavez", "role": "staff", "exp": t0 + 120}, "round trip")
    ok(redeem(t, S, current_epoch=4, now=t0 + 120) is not None, "valid at 120 s")
    ok(redeem(t, S, current_epoch=4, now=t0 + 121) is None, "dead at 121 s")
    ok(redeem(t, S, current_epoch=5, now=t0) is None, "sign-out-everywhere kills it")
    ok(redeem(t, "other", now=t0) is None, "wrong secret")
    p, s = t.split(".")
    forged = _b64u(json.dumps({"a": "tracker", "u": "manoj", "r": "doctor", "e": 4, "iat": t0,
                               "exp": t0 + 120, "n": "x"}, separators=(",", ":"),
                              sort_keys=True).encode()) + "." + s
    ok(redeem(forged, S, now=t0) is None, "payload swap refused")
    ok(redeem(p + ".AAAA", S, now=t0) is None, "bad signature refused")
    for bad in ["", None, 5, "a.b.c", "nodot", "x" * 700]:
        ok(redeem(bad, S, now=t0) is None, "malformed refused %r" % (bad if not isinstance(bad, str) else bad[:8]))
    # a clinic_sso cookie is not a pass, and a pass is not a cookie
    ck = clinic_sso.make_token("manoj", "doctor", 4, S, now=t0)
    ok(redeem(ck, S, now=t0) is None, "cookie refused as a pass")
    ok(clinic_sso.verify_token(t, S, now=t0) is None, "pass refused as a cookie")
    # a long-lived pass signed right is still refused (exp - iat > TTL)
    lp = mint("manoj", "doctor", 4, S, now=t0, ttl=3600)
    ok(redeem(lp, S, now=t0 + 10) is None, "over-long pass refused")
    ok(mint("a", "b", 1, S, now=t0) != mint("a", "b", 1, S, now=t0), "two passes in one second differ")
    ok(S not in t, "secret not in the pass")
    raised = False
    try:
        mint("a", "b", 1, "")
    except RuntimeError:
        raised = True
    ok(raised, "no secret -> refuses loud")
    print("tracker_pass selftest: %d/%d PASSED" % (n, n))
    return n


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest()
    else:
        print("tracker_pass.py -- import me. Run with --selftest to verify.")
