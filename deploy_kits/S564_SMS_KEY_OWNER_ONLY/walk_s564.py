#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s564.py -- kit S564_SMS_KEY_OWNER_ONLY (15-Oct-2026).  Runs on SCRATCH folders and SCRATCH databases only.
    python3 -B walk_s564.py --fin <scratch finance, the files under test> --oldfin <scratch finance, the OLD files>
                            --db <a COPY of finance.db> --adb <a COPY of assets.db> --marg <scratch marg_ingest> --map <DUTY_MAP.json> [--expect-red]
    python3 -B walk_s564.py --page --fin <a copy of the placed files> --db <a copy of the live database> ... --keyfile <the key file>   (after placing)
The real finance app (Flask's test client, the walk's own header session -- FINANCE_ALLOW_HEADER_AUTH in a scratch process, never a live
secret), each code folder in its own child process on its own copy of the database, the same fixed clock.  A made-up key file (the walk's
own text); made-up logins w564_clin (clinic checker), w564_med (medical checker), w564_none (no role) written into unit_role on the scratch
copy only (w564_clin also a medical viewer, as the real clinic checkers are; w564_view a medical viewer
alone); made-up merchant tails 000563 / 000564 for the door.  The walk prints counts, offsets and yes/no only -- never page text, never
an SMS text, never a key.
  a  as manoj: the fold and the key are there, step 4 is the new text; the page is byte for byte the old page with only step 4 changed.
  b  as a clinic checker and a medical checker (made-up): 200, no fold, no key, no key-file path; byte for byte the old page minus the fold.
     Staff-eye (CLAUDE.md): the real logins shavez, bhawna, manoj on the copy -- status as before; the fold for manoj alone; no duty of
     DUTY_MAP has this page as its door (so none can be hidden by the kit).
  c  a login the page refuses (w564_view, a medical viewer) is still refused (403); a login with no role (w564_none) is still sent to
     /portal by the finance gate (302), as today.
  d  the door: the right key -> 200 stored; a wrong key -> 401 -- as the old file.
  e  is_owner raising -> the page still renders (200) for manoj and a checker, with no fold for anyone.
--expect-red: the same walk on the OLD files; every 'C:' check must be red (the negative control).
Prints 'WALK OK ...' on success; exit 1 on any failure."""
import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys

KIT = "S564_SMS_KEY_OWNER_ONLY"
BASE = "https://followup.dr-manoj.in"
NOW = "2027-03-12T12:00:00"
DOOR_NOW = "2027-03-12T07:05:00"
WALK_KEY = "w564-walk-only-made-up-door-key"
FOLD_START = '<details class="card"><summary><b>Phone setup — MacroDroid</b>'
FOLD_END = "</ol></details>"
OLD_STEP4 = ('<li>Body: content type <b>form</b> · field <code>text</code> = <code>[sms_message]</code> · field <code>sender</code> = '
             '<code>[sms_number]</code></li>\n')
NEW_STEP4 = ('<li>What the phone sends: the SMS <code>[sms_message]</code> in a query parameter on the URL, plus a field named '
             '<code>from</code> = <code>[sms_number]</code> (the SMS number) — the macro as set on 15-Oct-2026.</li>\n')
MID = {"clinic": "000563", "medical": "000564"}
MADE_UP = (("w564_clin", "clinic"), ("w564_med", "medical"))
VIEWER = ("w564_clin", "w564_view")        # a medical viewer row: the finance gate admits only logins with a role on its own unit (as the real
                                           # clinic checkers shavez and bhawna have); w564_view has that row alone -> the page refuses it
ROLE = {"manoj": "doctor", "bhawna": "doctor", "shavez": "manager", "w564_clin": "staff", "w564_med": "staff", "w564_none": "staff", "w564_view": "staff"}
RUN, FAILS, CTRL, OUT = [0], [], [], []


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if (got is not None and not cond) else ""))
    if label.startswith("C:"):
        CTRL.append((label, bool(cond)))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst, timeout=60)
    s.backup(d)
    d.close()
    s.close()


def app_env(fin, dbp, adb, marg, dmap, keyfile, now):
    work = os.path.dirname(dbp)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(marg),
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(dmap), FINANCE_SSO_DIR=os.path.join(work, "nosso"),
                      RING_PORTAL_DIR=os.path.join(work, "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", BANK_SMS_KEY_FILE=keyfile,
                      PYTHONDONTWRITEBYTECODE="1")
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_MARG_TOKEN", "FINANCE_CRON_TOKEN"):
        os.environ.pop(k, None)
    clock(now)
    sys.path.insert(0, fin)
    os.chdir(fin)


def clock(iso):
    for k in ("CLINIC_MONEY_NOW", "BANK_STANDIN_NOW", "BANK_SMS_NOW"):
        if iso:
            os.environ[k] = iso
        else:
            os.environ.pop(k, None)


def sms_text(unit):
    """A made-up ICICI settlement SMS: account XX000, the walk's merchant tail, a made-up amount and balance."""
    return ("ICICI Bank Account XX000 credited:Rs. 1,234.00 on 12-Mar-27. Info EZY*ICICIPOS_SET_10XX%s_. Available Balance is Rs. 5,000.00."
            % MID[unit])


def cut_fold(h):
    i = h.find(FOLD_START)
    if i < 0:
        return h
    j = h.find(FOLD_END, i)
    return h if j < 0 else h[:i] + h[j + len(FOLD_END):]


def first_diff(x, y):
    """Only WHERE two pages part (an offset and the lengths) -- never their text."""
    if x == y:
        return "same"
    n = min(len(x), len(y))
    i = next((k for k in range(n) if x[k] != y[k]), n)
    return "they part at character %d (lengths %d / %d)" % (i, len(x), len(y))


# ============================================================================================ the child: one code folder, one copy
def child(a):
    spec = json.load(open(a.spec, encoding="utf-8"))
    fin = os.path.abspath(a.fin)
    app_env(fin, os.path.abspath(a.db), a.adb, a.marg, a.map, spec["keyfile"], spec["now"])
    import finance_app as fa                                  # noqa: E402
    import bank_sms as SMS                                    # noqa: E402
    import bank_standin as BS                                 # noqa: E402
    for m in (SMS, BS):
        assert m.__file__.startswith(fin), (m.__name__, m.__file__)
    if spec.get("raise_owner"):
        def _boom(con, u):
            raise RuntimeError("w564: the owner test cannot be read")
        BS.is_owner = _boom
    cl = fa.app.test_client(use_cookies=False)
    out = {"_mount_failed": [n for n, _w in getattr(fa, "_MOUNT_FAILED", [])]}
    for name, u, method, path, data, extra in spec["pages"]:
        h = {"X-Clinic-User": u, "X-Clinic-Role": ROLE.get(u, "staff")} if u else {}
        h.update(extra or {})
        if spec.get("door_now"):
            clock(spec["door_now"])
        try:
            if method == "POST":
                r = cl.post(path, base_url=BASE, headers=h, data=data)
            else:
                r = cl.get(path, base_url=BASE, headers=h)
            out[name] = [r.status_code, r.get_data().decode("utf-8", "replace")]
        except Exception as e:                                # noqa: BLE001 -- an exception through the test client = a 500
            out[name] = [599, "exception %s" % type(e).__name__]
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
    return 0


def run_child(a, fin, dbsrc, work, tag, spec):
    cdb = os.path.join(work, "w564_%s.db" % tag)
    copydb(dbsrc, cdb)
    sp, op = os.path.join(work, "w564_spec_%s.json" % tag), os.path.join(work, "w564_out_%s.json" % tag)
    json.dump(spec, open(sp, "w", encoding="utf-8"))
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child", "--fin", fin, "--db", cdb, "--adb", a.adb, "--marg", a.marg,
                        "--map", a.map, "--spec", sp, "--out", op], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                       timeout=900, cwd="/tmp")
    if p.returncode != 0 or not os.path.isfile(op):
        tail = [x for x in p.stdout.splitlines() if x.startswith(("Traceback", "  File", "AssertionError", "ImportError", "ModuleNotFound"))]
        check("the %s child renders (%s)" % (tag, os.path.basename(fin)), False, " / ".join(tail[-4:]))
        return {}
    return json.load(open(op, encoding="utf-8"))


# ============================================================================================ the look, after placing
def page_look(a):
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    work = os.path.dirname(dbp)
    try:
        key = open(a.keyfile, encoding="utf-8").read().strip()
    except OSError:
        key = ""
    spec = dict(now="", keyfile=os.path.abspath(a.keyfile), pages=[[u, u, "GET", "/finance/bank-sms", None, None] for u in ("manoj", "shavez", "bhawna")])
    o = run_child(a, fin, dbp, work, "look", spec)
    ok = bool(o) and bool(key)
    res = []
    for u in ("manoj", "shavez", "bhawna"):
        s, h = o.get(u, [0, ""])
        fold, has_key = FOLD_START in h, bool(key) and key in h
        res.append("%s %s, fold %s, the key on the page %s" % (u, s, "yes" if fold else "no", "yes" if has_key else "no"))
        if u == "manoj":
            ok = ok and s == 200 and fold and has_key and NEW_STEP4 in h
        else:
            ok = ok and s in (200, 403) and not fold and not has_key
    for f in os.listdir(work):
        if f.startswith("w564_"):
            os.remove(os.path.join(work, f))
    say("   /finance/bank-sms on the placed files (copied), a copy of the live database, the real clock, the key file there %s: %s"
        % ("present" if key else "MISSING", "; ".join(res)))
    leak = re.search(r"\d{10}", "\n".join(OUT))
    good = ok and not leak
    say(("PAGE OK S564" if good else "PAGE RED S564") + ": the fold and the key for manoj only")
    return 0 if good else 1


# ============================================================================================ the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--map"):
        ap.add_argument(k, required=True)
    for k in ("--oldfin", "--spec", "--out", "--keyfile"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--page", action="store_true")
    ap.add_argument("--child", action="store_true")
    a = ap.parse_args()
    anywhere = os.environ.get("S564_WALK_ANYWHERE") == "1"
    for p in (a.fin, a.db, a.adb, a.marg) + ((a.oldfin,) if a.oldfin else ()):
        assert os.path.abspath(p).startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.child:
        return child(a)
    if a.page:
        if not a.keyfile:
            ap.error("--keyfile is needed for the look")
        return page_look(a)
    if not a.oldfin:
        ap.error("--oldfin is needed for the walk")
    fin, old, dbp = os.path.abspath(a.fin), os.path.abspath(a.oldfin), os.path.abspath(a.db)
    work = os.path.dirname(dbp)
    say("-- S564 walk on the %s: %s . db %s" % ("OLD file (negative control)" if a.expect_red else "new file", fin, os.path.basename(dbp)))

    # the made-up world on the scratch copy: a made-up key file, made-up logins, made-up merchant tails
    keyfile = os.path.join(work, "w564_walk.key")
    with open(keyfile, "w") as fh:
        fh.write(WALK_KEY)
    c = sqlite3.connect(dbp, timeout=60)
    for u, unit in MADE_UP:
        c.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES (?,?,?,1,'W564 walk')", (unit, u, "checker"))
    for u in VIEWER:
        c.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES ('medical',?,'viewer',1,'W564 walk')", (u,))
    for unit in ("clinic", "medical"):
        c.execute("UPDATE business_unit SET merchant_id=? WHERE code=?", ("W564XX" + MID[unit], unit))
    c.commit()
    nrole = c.execute("SELECT COUNT(*) FROM unit_role WHERE note='W564 walk'").fetchone()[0]
    c.close()
    say("   made-up: the walk's key file, %d made-up unit_role rows (W564: two checkers, two medical viewers), merchant tails 000563 / 000564 -- on the scratch copy only" % nrole)

    logins = ("manoj", "w564_clin", "w564_med", "w564_view", "w564_none", "shavez", "bhawna")
    pages = [[u, u, "GET", "/finance/bank-sms", None, None] for u in logins]
    spec = dict(now=NOW, keyfile=keyfile, pages=pages)
    N = run_child(a, fin, dbp, work, "new", spec)
    O = run_child(a, old, dbp, work, "old", spec)
    if not (N and O):
        return finish(a)
    say("   parts of the finance app that did not load: new %s, old %s" % (N["_mount_failed"] or "none", O["_mount_failed"] or "none"))

    # ---------------------------------------------------------------- a
    say("-- a  as manoj (the owner)")
    s, h = N["manoj"]
    so, ho = O["manoj"]
    check("C: manoj: 200; the fold is there once, with the key, and step 4 is the new text (the old step 4 gone)",
          s == 200 and h.count(FOLD_START) == 1 and WALK_KEY in h and NEW_STEP4 in h and OLD_STEP4 not in h,
          (s, h.count(FOLD_START), WALK_KEY in h, NEW_STEP4 in h, OLD_STEP4 in h))
    check("C: manoj: byte for byte the old page with only step 4 changed (%s)" % first_diff(ho.replace(OLD_STEP4, NEW_STEP4, 1), h),
          so == 200 and OLD_STEP4 in ho and ho.replace(OLD_STEP4, NEW_STEP4, 1) == h)

    # ---------------------------------------------------------------- b
    say("-- b  as a clinic checker and a medical checker (made-up logins)")
    for u, unit in MADE_UP:
        s, h = N[u]
        so, ho = O[u]
        check("%s (%s checker) is let in, as by the old file (%s / old %s)" % (u, unit, s, so), s == 200 and so == 200)
        check("C: %s: no fold, no key, no key-file path, no key header name" % u,
              s == 200 and FOLD_START not in h and "Phone setup" not in h and WALK_KEY not in h and "bank_sms.key" not in h
              and "w564_walk.key" not in h and "X-Bank-Sms-Key" not in h and 'class="key"' not in h,
              (s, FOLD_START in h, WALK_KEY in h, "X-Bank-Sms-Key" in h))
        check("C: %s: byte for byte the old page with the fold removed (%s)" % (u, first_diff(cut_fold(ho), h)),
              so == 200 and FOLD_START in ho and cut_fold(ho) == h)
    say("-- b' staff-eye (CLAUDE.md): the real logins on the copy, the walk's own session")
    for u in ("shavez", "bhawna"):
        s, h = N[u]
        so, ho = O[u]
        check("%s: the page answers as before (%s / old %s)" % (u, s, so), s == so and s in (200, 403))
        if so == 200:
            check("C: %s: no fold, no key; otherwise the old page (%s)" % (u, first_diff(cut_fold(ho), h)),
                  s == 200 and FOLD_START not in h and WALK_KEY not in h and cut_fold(ho) == h and FOLD_START in ho)
        else:
            say("   %s is not let into this page at all (403, as before) -- nothing to hide from that login" % u)
    try:
        m = json.load(open(a.map, encoding="utf-8"))
        at = [d.get("id") for d in m.get("duties", []) if "/finance/bank-sms" in str(d.get("door", ""))]
        check("staff-eye: no duty in DUTY_MAP has /finance/bank-sms as its door (%d duties read) -- the kit hides no duty" % len(m.get("duties", [])),
              not at, at)
    except (OSError, ValueError) as e:
        check("staff-eye: DUTY_MAP.json read", False, type(e).__name__)

    # ---------------------------------------------------------------- c
    say("-- c  a login the page refuses")
    check("w564_view (a medical viewer, no checker role): refused 403, as by the old file (%s / old %s)" % (N["w564_view"][0], O["w564_view"][0]),
          N["w564_view"][0] == 403 and O["w564_view"][0] == 403 and "Not permitted" in N["w564_view"][1] and FOLD_START not in N["w564_view"][1])
    check("w564_none (no role at all): still sent away by the finance gate (302), as by the old file (%s / old %s)" % (N["w564_none"][0], O["w564_none"][0]),
          N["w564_none"][0] == 302 and O["w564_none"][0] == 302)

    # ---------------------------------------------------------------- d
    say("-- d  the door, unchanged")
    door = [["right_clin", "", "POST", "/finance/api/bank-sms", {"text": sms_text("clinic"), "sender": "W564-WALK"}, {"X-Bank-Sms-Key": WALK_KEY}],
            ["right_med", "", "POST", "/finance/api/bank-sms", {"text": sms_text("medical"), "sender": "W564-WALK"}, {"X-Bank-Sms-Key": WALK_KEY}],
            ["wrong", "", "POST", "/finance/api/bank-sms", {"text": sms_text("clinic"), "sender": "W564-WALK"}, {"X-Bank-Sms-Key": "w564-not-the-key"}],
            ["none", "", "POST", "/finance/api/bank-sms", {"text": sms_text("clinic"), "sender": "W564-WALK"}, None]]
    dspec = dict(now=DOOR_NOW, door_now=DOOR_NOW, keyfile=keyfile, pages=door)
    for which, f in (("new", fin), ("old", old)):
        D = run_child(a, f, dbp, work, "door_%s" % which, dspec)
        if not D:
            continue
        js = {}
        for k in ("right_clin", "right_med", "wrong", "none"):
            try:
                js[k] = json.loads(D[k][1])
            except (ValueError, KeyError):
                js[k] = {}
        check("the door (%s file): the right key -> 200 stored (clinic, Sanjeevni); a wrong key -> 401; no key -> 401 (%s %s %s %s)"
              % (which, D["right_clin"][0], D["right_med"][0], D["wrong"][0], D["none"][0]),
              D["right_clin"][0] == 200 and D["right_med"][0] == 200 and js["right_clin"].get("stored") is True and js["right_med"].get("stored") is True
              and D["wrong"][0] == 401 and D["none"][0] == 401 and js["wrong"].get("error") == "bad_key")

    # ---------------------------------------------------------------- e
    say("-- e  the owner test raising")
    espec = dict(now=NOW, keyfile=keyfile, raise_owner=True, pages=[["manoj", "manoj", "GET", "/finance/bank-sms", None, None],
                                                                   ["w564_clin", "w564_clin", "GET", "/finance/bank-sms", None, None]])
    E = run_child(a, fin, dbp, work, "raise", espec)
    for u in ("manoj", "w564_clin"):
        s, h = E.get(u, [0, ""])
        check("C: is_owner raising, as %s: the page still renders (%s), no fold, no key; the switch is not offered" % (u, s),
              s == 200 and FOLD_START not in h and WALK_KEY not in h and "Switch ON" not in h and "Switch OFF" not in h and "Bank settlement SMS" in h)
    return finish(a)


def finish(a):
    work = os.path.dirname(os.path.abspath(a.db))
    for f in os.listdir(work):
        if f.startswith("w564_"):
            p = os.path.join(work, f)
            shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
    leak = re.search(r"\d{10}", "\n".join(OUT))
    check("static: the walk's own output holds no run of 10 digits, no key", not leak and WALK_KEY not in "\n".join(OUT))
    red = len(FAILS)
    if a.expect_red:
        cr = [l for l, ok in CTRL if not ok]
        cg = [l for l, ok in CTRL if ok]
        for l in cr:
            say("  RED on the old file: " + l[:150])
        if CTRL and not cg:
            say("WALK OK negative control: every one of the %d 'C:' checks is red on the old file (%d of %d checks red)" % (len(CTRL), red, RUN[0]))
            return 0
        say("NEGATIVE CONTROL FAILED: %d 'C:' checks stayed green on the old file: %s" % (len(cg), "; ".join(x[:80] for x in cg)))
        return 1
    if FAILS:
        say("WALK RED: %d of %d checks failed" % (red, RUN[0]))
        return 1
    say("WALK OK S564: %d checks green (the fold and the key for the owner only; step 4 the new text; checkers see the old page minus the fold; "
        "a refused login still refused; the door unchanged; the owner test raising -> no fold, the page renders)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
