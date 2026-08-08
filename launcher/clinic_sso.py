#!/usr/bin/env python3
# clinic_sso.py -- Clinic SSO signed-token + cookie helper (Step 1 of the portal SSO broker).
# Pure standard library. No Flask, no third-party deps -> the VPS venv needs nothing new.
#
# ROLE IN THE DESIGN
#   - The BROKER (portal) calls make_token(...) on a successful login and sets the cookie.
#   - EVERY app's verify-shim (attendance / ledger / asset -- later steps) calls verify_token(...).
#   This module is the "one thing to trust" that all apps share.
#
# SECURITY (F-31 / D176)
#   - The signing secret is read from the environment (CLINIC_SSO_SECRET). It is NEVER hardcoded,
#     never logged, never printed. get_secret() fails LOUD if it is missing.
#   - Signatures are verified in constant time (hmac.compare_digest).
#
# TOKEN FORMAT:  <payload_b64url> "." <sig_b64url>
#   payload = {"u": user, "r": role, "e": epoch, "iat": issued_at, "exp": expires_at}  (UTC seconds)
#   sig     = HMAC-SHA256(secret, payload_b64url)

import os
import json
import time
import hmac
import base64
import hashlib

COOKIE_NAME = "clinic_sso"
COOKIE_DOMAIN = ".dr-manoj.in"
DEFAULT_TTL = 30 * 24 * 3600            # ~30 days, matches the design
SECRET_ENV = "CLINIC_SSO_SECRET"


def _b64u_encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64u_decode(txt):
    pad = "=" * (-len(txt) % 4)
    return base64.urlsafe_b64decode(txt + pad)


def _sign(payload_b64, secret):
    mac = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256)
    return _b64u_encode(mac.digest())


def get_secret(env=SECRET_ENV):
    """Read the shared SSO secret from the environment. Fail LOUD if absent (never a default)."""
    val = os.environ.get(env, "")
    if not val or not val.strip():
        raise RuntimeError(env + " is not set -- refusing to run without the SSO signing secret")
    return val


def make_token(user, role, epoch, secret, ttl=DEFAULT_TTL, now=None):
    """Broker call: build a signed token for a logged-in user."""
    if now is None:
        now = int(time.time())
    payload = {"u": user, "r": role, "e": int(epoch), "iat": int(now), "exp": int(now) + int(ttl)}
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64u_encode(body)
    sig = _sign(payload_b64, secret)
    return payload_b64 + "." + sig


def verify_token(token, secret, current_epoch=None, now=None):
    """Shim call: return {user, role, epoch, iat, exp} if the token is valid, else None.

    Rejects on: bad shape, bad signature, expiry, or an epoch older than current_epoch
    (that is how 'sign out everywhere' invalidates every existing token at once).
    """
    if not token or not isinstance(token, str) or token.count(".") != 1:
        return None
    payload_b64, sig = token.split(".", 1)
    expected = _sign(payload_b64, secret)
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        payload = json.loads(_b64u_decode(payload_b64).decode("utf-8"))
    except Exception:
        return None
    if now is None:
        now = int(time.time())
    try:
        exp = int(payload["exp"])
        tok_epoch = int(payload["e"])
    except (KeyError, ValueError, TypeError):
        return None
    if now > exp:
        return None
    if current_epoch is not None and tok_epoch < int(current_epoch):
        return None
    return {"user": payload.get("u"), "role": payload.get("r"),
            "epoch": tok_epoch, "iat": payload.get("iat"), "exp": exp}


def cookie_kwargs(ttl=DEFAULT_TTL):
    """Flags for resp.set_cookie(COOKIE_NAME, token, **cookie_kwargs()). Flask-agnostic."""
    return {"domain": COOKIE_DOMAIN, "secure": True, "httponly": True,
            "samesite": "Lax", "max_age": int(ttl), "path": "/"}


def clear_cookie_kwargs():
    """Flags to expire the cookie on logout (this device)."""
    return {"domain": COOKIE_DOMAIN, "secure": True, "httponly": True,
            "samesite": "Lax", "max_age": 0, "expires": 0, "path": "/"}


# ------------------------------------------------------------------------------- selftest
def _selftest():
    n = 0
    S = "test-secret-not-real"

    def ok(cond, label):
        nonlocal n
        assert cond, "FAIL: " + label
        n += 1

    # round trip
    now = 1_000_000
    t = make_token("manoj", "doctor", 3, S, ttl=100, now=now)
    d = verify_token(t, S, current_epoch=3, now=now)
    ok(d is not None, "round-trip verifies")
    ok(d["user"] == "manoj", "user preserved")
    ok(d["role"] == "doctor", "role preserved")
    ok(d["epoch"] == 3, "epoch preserved")
    ok(d["exp"] == now + 100, "exp computed")

    # tamper payload
    body, sig = t.split(".", 1)
    bad_payload = _b64u_encode(b'{"u":"attacker","r":"doctor","e":3,"iat":1,"exp":9999999999}') + "." + sig
    ok(verify_token(bad_payload, S, now=now) is None, "tampered payload rejected")

    # tamper signature
    ok(verify_token(body + ".AAAABBBBCCCC", S, now=now) is None, "tampered signature rejected")

    # wrong secret
    ok(verify_token(t, "wrong-secret", current_epoch=3, now=now) is None, "wrong secret rejected")

    # expiry
    ok(verify_token(t, S, current_epoch=3, now=now + 101) is None, "expired token rejected")
    ok(verify_token(t, S, current_epoch=3, now=now + 100) is not None, "exact-exp still valid")

    # epoch / sign-out-everywhere
    ok(verify_token(t, S, current_epoch=4, now=now) is None, "older epoch rejected (signed out)")
    ok(verify_token(t, S, current_epoch=3, now=now) is not None, "same epoch accepted")
    ok(verify_token(t, S, current_epoch=None, now=now) is not None, "no epoch check accepted")

    # malformed
    for bad in ["", "no-dot", "a.b.c", None, 12345]:
        ok(verify_token(bad, S, now=now) is None, "malformed rejected: " + repr(bad))

    # get_secret
    saved = os.environ.pop(SECRET_ENV, None)
    raised = False
    try:
        get_secret()
    except RuntimeError:
        raised = True
    ok(raised, "get_secret fails loud when unset")
    os.environ[SECRET_ENV] = "x"
    ok(get_secret() == "x", "get_secret returns env value")
    if saved is None:
        os.environ.pop(SECRET_ENV, None)
    else:
        os.environ[SECRET_ENV] = saved

    # cookie flags
    ck = cookie_kwargs()
    ok(ck["domain"] == COOKIE_DOMAIN and ck["secure"] and ck["httponly"] and ck["samesite"] == "Lax",
       "cookie flags correct")
    ok(clear_cookie_kwargs()["max_age"] == 0, "clear cookie expires")

    # secret never appears in the token
    ok(S not in t, "secret not embedded in token")

    print("clinic_sso selftest: " + str(n) + "/" + str(n) + " PASSED")
    return n


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest()
    else:
        print("clinic_sso.py -- import me. Run with --selftest to verify.")
