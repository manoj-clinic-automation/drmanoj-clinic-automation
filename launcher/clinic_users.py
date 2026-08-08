#!/usr/bin/env python3
# clinic_users.py -- Clinic SSO broker: the user + role store and its admin CLI (Step 1).
# Pure standard library. No third-party deps.
#
# WHAT THIS IS
#   The single clinic login list the SSO broker owns. Users and roles are DATA (a JSON file),
#   not code -- so adding lab / Manoj Bhati / Sanjeevni later is one admin command, no rebuild.
#
# SECURITY (F-31 / D176)
#   - Passwords are stored ONLY as salted PBKDF2-HMAC-SHA256 hashes. The plaintext is never
#     written, never logged. Password entry is via getpass (never on the command line / argv,
#     never echoed to screen).
#   - listusers NEVER prints a hash or salt.
#   - Password checks use a constant-time compare.
#
# ROLES
#   Stored as data (store["roles"]). Defaults: doctor, manager. addrole extends the set.
#   adduser / setrole refuse a role that is not registered (typo guard).
#
# SIGN OUT EVERYWHERE
#   A single global "epoch" integer. bump_epoch() increments it; the broker stamps the current
#   epoch into every token it issues; every app's shim rejects a token whose epoch is older than
#   the current one -> one action logs the whole family out.

import os
import sys
import json
import time
import hmac
import base64
import hashlib
import argparse

DEFAULT_STORE = os.environ.get("CLINIC_USERS_FILE", "/root/portal/clinic_users.json")
DEFAULT_ROLES = ["doctor", "manager"]
MIN_PW_LEN = 6
PBKDF2_ITERS = 200_000


# ------------------------------------------------------------------------------- store I/O
def _empty_store():
    return {"epoch": 1, "roles": list(DEFAULT_ROLES), "users": {}}


def load_store(path):
    if not os.path.exists(path):
        return _empty_store()
    with open(path, "r", encoding="utf-8") as f:
        s = json.load(f)
    s.setdefault("epoch", 1)
    s.setdefault("roles", list(DEFAULT_ROLES))
    s.setdefault("users", {})
    return s


def save_store(path, store):
    """Atomic write, then lock the file down to owner-only (F-31)."""
    d = os.path.dirname(path) or "."
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, sort_keys=True)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


# ------------------------------------------------------------------------------- password hashing
def _hash_pw(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERS)
    return base64.b16encode(salt).decode("ascii"), base64.b16encode(dk).decode("ascii")


def _check_pw(password, salt_hex, hash_hex):
    salt = base64.b16decode(salt_hex)
    _, cand = _hash_pw(password, salt)
    return hmac.compare_digest(cand, hash_hex)


# ------------------------------------------------------------------------------- operations
def _norm(user):
    return (user or "").strip().lower()


def add_role(path, role):
    store = load_store(path)
    role = role.strip()
    if not role:
        raise ValueError("role name is empty")
    if role in store["roles"]:
        raise ValueError("role already exists: " + role)
    store["roles"].append(role)
    save_store(path, store)
    return store["roles"]


def add_user(path, user, role, password):
    store = load_store(path)
    user = _norm(user)
    if not user:
        raise ValueError("username is empty")
    if user in store["users"]:
        raise ValueError("user already exists: " + user)
    if role not in store["roles"]:
        raise ValueError("unknown role: " + role + " (known: " + ", ".join(store["roles"]) + ")")
    if len(password) < MIN_PW_LEN:
        raise ValueError("password too short (min " + str(MIN_PW_LEN) + ")")
    salt_hex, hash_hex = _hash_pw(password)
    store["users"][user] = {"salt": salt_hex, "hash": hash_hex, "role": role,
                            "active": True, "created": _now_iso(), "note": ""}
    save_store(path, store)
    return True


def set_password(path, user, password):
    store = load_store(path)
    user = _norm(user)
    if user not in store["users"]:
        raise ValueError("no such user: " + user)
    if len(password) < MIN_PW_LEN:
        raise ValueError("password too short (min " + str(MIN_PW_LEN) + ")")
    salt_hex, hash_hex = _hash_pw(password)
    store["users"][user]["salt"] = salt_hex
    store["users"][user]["hash"] = hash_hex
    save_store(path, store)
    return True


def set_role(path, user, role):
    store = load_store(path)
    user = _norm(user)
    if user not in store["users"]:
        raise ValueError("no such user: " + user)
    if role not in store["roles"]:
        raise ValueError("unknown role: " + role + " (known: " + ", ".join(store["roles"]) + ")")
    store["users"][user]["role"] = role
    save_store(path, store)
    return True


def set_active(path, user, active):
    store = load_store(path)
    user = _norm(user)
    if user not in store["users"]:
        raise ValueError("no such user: " + user)
    store["users"][user]["active"] = bool(active)
    save_store(path, store)
    return True


def del_user(path, user):
    store = load_store(path)
    user = _norm(user)
    if user not in store["users"]:
        raise ValueError("no such user: " + user)
    del store["users"][user]
    save_store(path, store)
    return True


def verify_password(path, user, password):
    """Return the user's role if the password is correct AND the user is active, else None."""
    store = load_store(path)
    u = store["users"].get(_norm(user))
    if not u or not u.get("active", False):
        return None
    if _check_pw(password, u["salt"], u["hash"]):
        return u["role"]
    return None


def bump_epoch(path):
    """Sign out everywhere: invalidate every token issued before now."""
    store = load_store(path)
    store["epoch"] = int(store.get("epoch", 1)) + 1
    save_store(path, store)
    return store["epoch"]


def get_epoch(path):
    return int(load_store(path).get("epoch", 1))


def list_users(path):
    """Public listing -- NEVER includes salt or hash (D176)."""
    store = load_store(path)
    out = []
    for user, u in sorted(store["users"].items()):
        out.append({"user": user, "role": u.get("role"), "active": u.get("active", False),
                    "created": u.get("created", ""), "note": u.get("note", "")})
    return out


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


# ------------------------------------------------------------------------------- CLI
def _prompt_new_password():
    import getpass
    p1 = getpass.getpass("New password: ")
    p2 = getpass.getpass("Confirm password: ")
    if p1 != p2:
        print("passwords do not match")
        sys.exit(1)
    return p1


def _cli(argv):
    ap = argparse.ArgumentParser(description="Clinic SSO broker user/role admin")
    ap.add_argument("--file", default=DEFAULT_STORE, help="store path (default " + DEFAULT_STORE + ")")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("adduser"); p.add_argument("user"); p.add_argument("role")
    p = sub.add_parser("passwd"); p.add_argument("user")
    p = sub.add_parser("setrole"); p.add_argument("user"); p.add_argument("role")
    p = sub.add_parser("deactivate"); p.add_argument("user")
    p = sub.add_parser("activate"); p.add_argument("user")
    p = sub.add_parser("deluser"); p.add_argument("user")
    p = sub.add_parser("addrole"); p.add_argument("role")
    sub.add_parser("listusers")
    sub.add_parser("listroles")
    sub.add_parser("signout-all")
    sub.add_parser("get-epoch")
    sub.add_parser("selftest")

    args = ap.parse_args(argv)
    path = args.file

    if args.cmd == "adduser":
        add_user(path, args.user, args.role, _prompt_new_password())
        print("added user '" + args.user + "' as role '" + args.role + "'")
    elif args.cmd == "passwd":
        set_password(path, args.user, _prompt_new_password())
        print("password updated for '" + args.user + "'")
    elif args.cmd == "setrole":
        set_role(path, args.user, args.role)
        print("role of '" + args.user + "' set to '" + args.role + "'")
    elif args.cmd == "deactivate":
        set_active(path, args.user, False)
        print("deactivated '" + args.user + "'")
    elif args.cmd == "activate":
        set_active(path, args.user, True)
        print("activated '" + args.user + "'")
    elif args.cmd == "deluser":
        del_user(path, args.user)
        print("deleted '" + args.user + "'")
    elif args.cmd == "addrole":
        roles = add_role(path, args.role)
        print("roles: " + ", ".join(roles))
    elif args.cmd == "listusers":
        rows = list_users(path)
        if not rows:
            print("(no users)")
        for r in rows:
            flag = "active" if r["active"] else "OFF"
            print("  " + r["user"].ljust(16) + r["role"].ljust(12) + flag.ljust(8) + r["created"])
    elif args.cmd == "listroles":
        print("roles: " + ", ".join(load_store(path)["roles"]))
    elif args.cmd == "signout-all":
        print("epoch bumped to " + str(bump_epoch(path)) + " -- everyone must log in again")
    elif args.cmd == "get-epoch":
        print(get_epoch(path))
    elif args.cmd == "selftest":
        _selftest()
    else:
        ap.print_help()


# ------------------------------------------------------------------------------- selftest
def _selftest():
    import tempfile
    n = 0

    def ok(cond, label):
        nonlocal n
        assert cond, "FAIL: " + label
        n += 1

    d = tempfile.mkdtemp()
    path = os.path.join(d, "users.json")

    # add + verify
    add_user(path, "manoj", "doctor", "secret1")
    ok(verify_password(path, "manoj", "secret1") == "doctor", "add + verify returns role")
    ok(verify_password(path, "manoj", "wrongpw") is None, "wrong password rejected")

    # deactivate blocks login
    set_active(path, "manoj", False)
    ok(verify_password(path, "manoj", "secret1") is None, "deactivated user cannot log in")
    set_active(path, "manoj", True)
    ok(verify_password(path, "manoj", "secret1") == "doctor", "reactivated user can log in")

    # named managers with the two ledger maker mappings
    add_user(path, "shavez", "manager", "secret2")
    add_user(path, "alisha", "manager", "secret3")
    ok(verify_password(path, "shavez", "secret2") == "manager", "shavez manager")
    ok(verify_password(path, "alisha", "secret3") == "manager", "alisha manager")

    # role change
    set_role(path, "alisha", "doctor")
    ok(verify_password(path, "alisha", "secret3") == "doctor", "role change reflected")
    set_role(path, "alisha", "manager")

    # min length
    raised = False
    try:
        add_user(path, "tiny", "doctor", "abc")
    except ValueError:
        raised = True
    ok(raised, "short password refused")

    # duplicate user
    raised = False
    try:
        add_user(path, "manoj", "doctor", "secret1")
    except ValueError:
        raised = True
    ok(raised, "duplicate user refused")

    # unknown role
    raised = False
    try:
        add_user(path, "lab", "labrole", "secret4")
    except ValueError:
        raised = True
    ok(raised, "unknown role refused")

    # add role as data, then use it (the lab / future-user path)
    add_role(path, "lab")
    add_user(path, "lab", "lab", "secret4")
    ok(verify_password(path, "lab", "secret4") == "lab", "new role added as data + usable")

    # delete
    del_user(path, "lab")
    ok(verify_password(path, "lab", "secret4") is None, "deleted user gone")

    # epoch / sign-out-everywhere
    e0 = get_epoch(path)
    e1 = bump_epoch(path)
    ok(e1 == e0 + 1, "epoch bumps")
    ok(get_epoch(path) == e1, "epoch persists")

    # D176: listing exposes no secret material; hash != plaintext; salts differ
    rows = list_users(path)
    for r in rows:
        ok("hash" not in r and "salt" not in r, "listing hides secret material")
    raw = load_store(path)["users"]
    ok(raw["manoj"]["hash"] != "secret1", "stored hash is not plaintext")
    ok(raw["manoj"]["salt"] != raw["shavez"]["salt"], "salts are unique per user")

    # case-insensitive usernames (kills the capital-first-letter login trap)
    add_user(path, "MixedCase", "doctor", "secretX")
    ok(verify_password(path, "mixedcase", "secretX") == "doctor", "username stored lowercase")
    ok(verify_password(path, "MIXEDCASE", "secretX") == "doctor", "login is case-insensitive")
    ok(any(r["user"] == "mixedcase" for r in list_users(path)), "listing shows normalized name")
    del_user(path, "MIXEDCASE")
    ok(verify_password(path, "mixedcase", "secretX") is None, "case-insensitive delete works")

    # store reloads as valid json
    ok(isinstance(load_store(path)["users"], dict), "store reloads")

    # cleanup
    try:
        os.remove(path)
        os.rmdir(d)
    except OSError:
        pass

    print("clinic_users selftest: " + str(n) + "/" + str(n) + " PASSED")
    return n


if __name__ == "__main__":
    _cli(sys.argv[1:])
