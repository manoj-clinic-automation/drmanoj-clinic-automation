#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""add_jobs_s569.py -- kit S569_PROOF_REACH_AND_TWO_LINES, Part B (data only): two one-time 'tap' jobs on Amir's card.

    python3 -B add_jobs_s569.py walk [--work /tmp/s569walk]   scratch copies only (backup API): the staff-eye walk + its control
    python3 -B add_jobs_s569.py live [--work /tmp/s569live]   the build lock must name S569: backup, assert, insert, read back

Both modes first read Amir's voucher cards (/finance/stock/api/pad/amir/1, as amir) on a backup-API copy and STOP unless voucher 9 still
says KT ROS DT 6 patte + 11 goli and voucher 18 VINBACTUM DS 25 nag (STOCK ISSUE). The insert is keyed (amir_job.key is UNIQUE): a
second run adds nothing and says ALREADY. Each row added is audited job_added by system through amir_day's own _audit.
The walk signs in as amir through a walk-only portal (a random secret and its own user store in the scratch folder, never the live
ones), renders /finance/amir and the door /finance/amir/step/6 before and after, and diffs the card. Its control runs the same card
checks on the render without the two rows (= the old state): they must go RED. No person, phone or account number is printed."""
import base64
import difflib
import html as _html
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys

FIN, POR = "/root/finance", "/root/portal"
LIVE_DB, LIVE_SPINE = FIN + "/finance.db", FIN + "/spine/spine.db"
LOCK = "/root/deploy/.claude_code_build.lock"
KIT = "S569"
AUDIT = {"kit": "S569", "owner_word": "16-Oct 09:33"}
JOBS = [  # key, subject, text_hi, sub_hi, (voucher seq, the card's qty words)
    ("fix:S569:KT ROS DT", "KT ROS DT", "KT ROS DT \u2014 Marg mein STOCK ISSUE kijiye: 6 patte + 11 goli",
     "6 Sep ki stock ginti \u00b7 voucher 9 ki line", (9, "6 patte + 11 goli")),
    ("fix:S569:VINBACTUM DS", "VINBACTUM DS", "VINBACTUM DS \u2014 Marg mein STOCK ISSUE kijiye: 25 nag",
     "6 Sep ki stock ginti \u00b7 voucher 18 ki line", (18, "25 nag")),
]
DUE_SQL = ("SELECT COUNT(*) AS n, MIN(substr(show_from,1,10)) AS since FROM amir_job WHERE show_from IS NOT NULL AND done_at IS NULL "
           "AND NOT (said_at IS NOT NULL AND said_at > COALESCE(reopened_at, ''))")   # DUTY_MAP amir.marg_jobs, byte-equal
DOOR, MARK, TILE = "/finance/amir/step/6", "Ek baar ke kaam", "Amir ka kaam"
BAD_WORDS = ("check", "chhoot", "galat", "sahi", "verdict")      # D708: only "do this" words


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def copydb(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def segs(h):
    """The visible text of a page as a list of segments (one per text node), whitespace folded."""
    h = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", h or "")
    out = []
    for t in re.split(r"<[^>]+>", h):
        t = re.sub(r"\s+", " ", _html.unescape(t)).strip()
        if t:
            out.append(t)
    return out


# ============================================================================ the probe (a child process, its env says what it reads)
def probe():
    what = os.environ["S569_WHAT"]
    sys.path.insert(0, FIN)
    if what == "card":
        sys.path.insert(0, os.environ["S569_POR"])
    os.chdir(FIN)
    import finance_app as fa                                    # noqa: E402
    import stock_watch as SW                                    # noqa: E402
    SW.SPINE_DB = os.environ["SPINE_DB"]
    assert os.path.abspath(fa.DB_PATH) == os.path.abspath(os.environ["FINANCE_DB"]) and fa.DB_PATH.startswith("/tmp/"), "the probe reads a scratch copy only"
    fc = fa.app.test_client(use_cookies=False)
    out = dict(db=fa.DB_PATH)
    if what == "qty":
        r = fc.get("/finance/stock/api/pad/amir/1", headers={"X-Clinic-User": "amir", "X-Clinic-Role": "staff"})
        j = r.get_json(silent=True) or {}
        out["status"] = r.status_code
        found = {}
        for v in j.get("vouchers") or []:
            for ln in v.get("lines") or []:
                for key, subj, _t, _s, (seq, qty) in JOBS:
                    if ln.get("item") == subj:
                        found.setdefault(key, []).append(dict(seq=v.get("seq"), kind=v.get("kind"), title_hi=v.get("title_hi"), qty_hi=ln.get("qty_hi"),
                                                              sign=ln.get("change_sign")))
        out["found"] = found
    else:
        import portal as po                                     # noqa: E402
        BASE = "https://followup.dr-manoj.in"
        pc = po.app.test_client(use_cookies=False)
        W = json.loads(os.environ["S569_W"])
        r = pc.post("/portal/login", base_url=BASE, data={"user": "amir", "password": W["pw"]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        tok = m.group(1) if m else ""
        b = tok.split(".")[0] if tok else ""
        out["login"] = [r.status_code, (json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)).decode()).get("u") if b else None)]
        ck = {"Cookie": "clinic_sso=" + tok}
        rh = pc.get("/portal?all=1", base_url=BASE, headers=ck)
        out["tiles"] = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', rh.get_data(as_text=True))]

        def follow(path):
            hops = []
            for _ in range(5):
                rr = fc.get(path, base_url=BASE, headers=ck)
                hops.append([path, rr.status_code])
                loc = rr.headers.get("Location", "")
                if rr.status_code in (301, 302, 303) and loc.replace(BASE, "").startswith("/finance/"):
                    path = loc.replace(BASE, "")
                    continue
                return hops, rr.get_data(as_text=True)
            return hops, ""
        out["home_hops"], hh = follow("/finance/amir")
        out["home_segs"] = segs(hh)
        out["door_hops"], hd = follow(DOOR)
        out["door_segs"] = segs(hd)
        blk = hd.split("id=s494jobs", 1)
        out["forms"] = re.findall(r"name=job value='(tap:\d+)'><button class=btn>Kar diya</button>", hd)
        out["jobs_block"] = segs("<x " + blk[1])[:40] if len(blk) > 1 else []
        db = sqlite3.connect("file:%s?mode=ro" % fa.DB_PATH, uri=True)
        out["due"] = list(db.execute(DUE_SQL).fetchone())
    print("S569JSON " + json.dumps(out, default=str))
    return 0


def run_probe(what, dbp, spp, extra_env=None, cwd=FIN):
    nosso = os.path.join(os.path.dirname(dbp), "nosso")         # the qty read: header auth, no SSO secret at all
    os.makedirs(nosso, exist_ok=True)
    env = dict(os.environ, S569_WHAT=what, FINANCE_DB=dbp, SPINE_DB=spp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=nosso)
    if what == "card":                                          # the card: the walk-only portal's cookie, never a header
        env["FINANCE_ALLOW_HEADER_AUTH"] = "0"
    env.update(extra_env or {})
    env.pop("SARVAM_API_KEY", None)
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "probe"], env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, timeout=1500)
    js = [l for l in p.stdout.splitlines() if l.startswith("S569JSON ")]
    if not js:
        print("   the %s probe did not finish (exit %s); its last lines:" % (what, p.returncode))
        for l in p.stdout.splitlines()[-20:]:
            print("     " + mask(l[:300]))
        return None
    return json.loads(js[-1][9:])


def qty_ok(Q):
    """[(key, ok, seen)] -- each job's voucher card still says the brief's words."""
    res = []
    for key, _subj, _t, _s, (seq, qty) in JOBS:
        seen = (Q or {}).get("found", {}).get(key) or []
        ok = any(x["seq"] == seq and x["kind"] == "ISSUE" and x["qty_hi"] == qty and x["sign"] == -1 for x in seen)
        res.append((key, ok, seen))
    return res


# ============================================================================ the data step (one transaction, keyed)
def insert(dbp):
    sys.path.insert(0, FIN)
    import amir_day as AD                                       # noqa: E402 -- its own _audit and _stamp
    cx = sqlite3.connect(dbp, timeout=60)
    try:
        if not cx.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='amir_job'").fetchone():
            raise SystemExit("STOP: amir_job is not in %s -- nothing written" % dbp)
        now = AD._stamp()
        res = []
        cx.execute("BEGIN IMMEDIATE")
        for key, subj, t, s, _q in JOBS:
            r = cx.execute("SELECT id FROM amir_job WHERE key=?", (key,)).fetchone()
            if r:
                res.append((key, r[0], "ALREADY"))
                continue
            cur = cx.execute("INSERT INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                             (key, "tap", subj, t, s, now, KIT, now))
            AD._audit(cx, "system", "job_added", key, dict(AUDIT))
            res.append((key, cur.lastrowid, "ADDED"))
        cx.commit()
        return res
    finally:
        cx.close()


def rows_of(dbp):
    db = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    db.row_factory = sqlite3.Row
    keys = [j[0] for j in JOBS]
    rows = [dict(r) for r in db.execute("SELECT * FROM amir_job WHERE key IN (?,?) ORDER BY id", keys)]
    aud = [dict(r) for r in db.execute("SELECT id, at, who, action, ref, detail FROM purchase_audit WHERE action='job_added' AND ref IN (?,?) ORDER BY id", keys)]
    due = list(db.execute(DUE_SQL).fetchone())
    n = db.execute("SELECT COUNT(*) FROM amir_job").fetchone()[0]
    db.close()
    return rows, aud, due, n


def row_shape_ok(rows):
    want = {j[0]: j for j in JOBS}
    ok = len(rows) == 2
    for r in rows:
        key, subj, t, s, _q = want.get(r["key"], (None,) * 5)
        ok = ok and r["kind"] == "tap" and r["subject"] == subj and r["text_hi"] == t and r["sub_hi"] == s and r["created_by"] == KIT \
            and r["show_from"] == r["created_at"] and bool(re.match(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$", r["created_at"] or "")) \
            and all(r.get(c) is None for c in ("said_at", "said_by", "said_what", "done_at", "done_how", "reopened_at"))
    return ok


# ============================================================================ the walk-only portal (its own secret and user store)
def walk_portal(work):
    por = os.path.join(work, "por")
    assert por.startswith("/tmp/"), "the walk's portal lives in a scratch folder"
    os.makedirs(por, exist_ok=True)
    for f in os.listdir(POR):
        if f.endswith(".py") and f != "portal_config.py":      # never the live secret, never the live user store
            shutil.copy2(os.path.join(POR, f), por)
    shutil.copy2(os.path.join(POR, "tile_grants.json"), por)
    secret = secrets.token_hex(32)
    with open(os.path.join(por, "portal_config.py"), "w") as fh:
        fh.write("# S569 walk only -- a random secret made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\n"
                 "PORTAL_TOKEN_SEED = 's569-walk-seed'\n" % secret)
    sys.path.insert(0, por)
    import clinic_users                                         # noqa: E402
    store = os.path.join(por, "clinic_users.json")
    pw = secrets.token_urlsafe(12)
    for u, role, p in (("amir", "staff", pw), ("manoj", "doctor", secrets.token_urlsafe(12))):
        try:
            clinic_users.add_role(store, role)
        except ValueError:
            pass
        clinic_users.add_user(store, u, role, p)
    sys.path.remove(por)
    sys.modules.pop("clinic_users", None)
    env = dict(S569_POR=por, FINANCE_SSO_DIR=por, CLINIC_PORTAL_DIR=por, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"),
               CLINIC_SSO_SECRET=secret, S569_W=json.dumps({"pw": pw}))
    return env


# ============================================================================ walk
def walk(work):
    assert work.startswith("/tmp/"), "the walk works in /tmp only"
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    fails, ctrl = [], []

    def check(label, cond, got=None, into=fails):
        print(("  GREEN " if cond else "  RED   ") + label + (("   [" + mask(str(got))[:500] + "]") if got is not None else ""))
        if not cond:
            into.append(label)
    dbp, spp = os.path.join(work, "scratch.db"), os.path.join(work, "spine.db")
    copydb(LIVE_DB, dbp)
    copydb(LIVE_SPINE, spp)
    print("-- scratch copies by the backup API: %s, %s" % (dbp, spp))
    penv = walk_portal(work)
    Q = qty_ok(run_probe("qty", dbp, spp))
    for key, ok, seen in Q:
        check("W1 the voucher card still says the brief's words: %s" % key, ok, seen)
    rows0, _a0, due0, n0 = rows_of(dbp)
    print("-- before: amir_job rows %d; the two keys present %d; DUTY_MAP amir.marg_jobs due %s" % (n0, len(rows0), due0))
    B1 = run_probe("card", dbp, spp, penv)
    B2 = run_probe("card", dbp, spp, penv)
    if not (B1 and B2):
        print("WALK RED: the before card could not be rendered")
        return 1
    res = insert(dbp)
    print("-- the data step on the scratch copy: %s" % res)
    rows1, aud1, due1, n1 = rows_of(dbp)
    A = run_probe("card", dbp, spp, penv)
    res2 = insert(dbp)
    rows2, aud2, due2, n2 = rows_of(dbp)
    print("-- a second run: %s" % res2)
    if not A:
        print("WALK RED: the after card could not be rendered")
        return 1
    ids = {r["key"]: r["id"] for r in rows1}
    texts = [(j[2], j[3], ids.get(j[0])) for j in JOBS]

    def card_checks(C, due_before, into):
        door = C["door_segs"]
        check("W4 amir signs in (walk-only portal) as 'amir'; the tile '%s' is on his home" % TILE, C["login"][1] == "amir" and TILE in C["tiles"],
              [C["login"], TILE in C["tiles"]], into)
        check("W5 /finance/amir answers 200 for him (via %s)" % C["home_hops"], bool(C["home_hops"]) and C["home_hops"][-1][1] == 200, None, into)
        check("W6 the door %s: '%s' shown" % (DOOR, MARK), C["door_hops"][-1][1] == 200 and MARK in door, C["door_hops"], into)
        for t, s, jid in texts:
            i = door.index(t) if t in door else -1
            check("W7 '%s' under %s, its line '%s', a Kar diya button (tap:%s)" % (t, MARK, s, jid),
                  i >= 0 and MARK in door[:i] and door[i + 1:i + 2] == [s] and door[i + 2:i + 3] == ["Kar diya"] and ("tap:%s" % jid) in C["forms"],
                  door[i:i + 3] if i >= 0 else None, into)
        check("W8 DUTY_MAP amir.marg_jobs due_sql: n %s -> %s (+2)" % (due_before[0], C["due"][0]), C["due"][0] == due_before[0] + 2, C["due"], into)
    print("-- the staff-eye walk, after the two rows (scratch copy):")
    card_checks(A, due0, fails)
    vol = set(x for x in difflib.ndiff(B1["door_segs"], B2["door_segs"]) if x[:2] in ("- ", "+ "))
    d = [x for x in difflib.ndiff(B2["door_segs"], A["door_segs"]) if x[:2] in ("- ", "+ ")]
    allowed = {"+ " + x for t, s, _ in texts for x in (t, s, "Kar diya")} | {"+ " + MARK}
    added = [x for x in d if x.startswith("+ ")]
    removed = [x for x in d if x.startswith("- ") and x not in vol and ("+ " + x[2:]) not in vol]
    extra = [x for x in added if x not in allowed and x not in vol and ("- " + x[2:]) not in vol]
    check("W9 nothing else on his card changed: added only the two lines (%d segments), removed none" % len(added),
          not extra and not removed and all(("+ " + t) in added for t, _s, _ in texts), dict(extra=extra, removed=removed))
    hd = [x for x in difflib.ndiff(B2["home_segs"], A["home_segs"]) if x[:2] in ("- ", "+ ")]
    vh = set(x for x in difflib.ndiff(B1["home_segs"], B2["home_segs"]) if x[:2] in ("- ", "+ "))
    hx = [x for x in hd if x not in vh and ("+ " + x[2:]) not in vh and ("- " + x[2:]) not in vh
          and not (x.startswith("+ ") and x in allowed)]
    check("W9b /finance/amir: the same (no other change)", not hx, hx)
    check("W2 two rows, the brief's shape (tap, created_by S569, show_from = created_at, the rest NULL)", row_shape_ok(rows1) and n1 == n0 + 2,
          [(r["id"], r["key"], r["created_at"]) for r in rows1])
    check("W3 audited: two job_added by system, %s" % json.dumps(AUDIT), len(aud1) == 2 and all(a["who"] == "system" and json.loads(a["detail"]) == AUDIT for a in aud1),
          [(a["id"], a["ref"], a["detail"]) for a in aud1])
    check("W10 a second run adds nothing (ALREADY, rows %d = %d, audits %d = %d)" % (n2, n1, len(aud2), len(aud1)),
          all(x[2] == "ALREADY" for x in res2) and n2 == n1 and len(aud2) == len(aud1) and due2 == due1, res2)
    check("W11 only 'do this' words (D708): none of %s" % (BAD_WORDS,), not any(w in (j[2] + " " + j[3]).lower() for j in JOBS for w in BAD_WORDS))
    print("-- CONTROL: the same card checks on the card WITHOUT the two rows (the old state) -- must go RED:")
    card_checks(B2, due0, ctrl)
    must = [l for l in ctrl if l.startswith(("W7", "W8"))]
    cok = len(must) == len(texts) + 1
    print("CONTROL %s: %d of %d card checks RED on the old state (W7 x2, W8 must be RED)" % ("RED as it must" if cok else "DID NOT GO RED", len(must), len(texts) + 1))
    print("WALK %s: %d red; control %s" % ("GREEN" if not fails and cok else "RED", len(fails), "ok" if cok else "FAILED"))
    shutil.rmtree(work, ignore_errors=True)
    return 0 if (not fails and cok) else 1


# ============================================================================ live
def live(work):
    own = os.path.join(LOCK, "owner")
    if not (os.path.isfile(own) and KIT in open(own).read()):
        print("STOP: the build lock %s does not name %s -- nothing written" % (LOCK, KIT))
        return 2
    assert work.startswith("/tmp/")
    os.makedirs(work, exist_ok=True)
    rows0, _a, due0, n0 = rows_of(LIVE_DB)
    if len(rows0) == 2 and row_shape_ok(rows0):
        print("ALREADY INSTALLED: both rows are on the live database (ids %s) -- nothing written" % [r["id"] for r in rows0])
        return 0
    stamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = "%s.bak_S569_%s" % (LIVE_DB, stamp)
    copydb(LIVE_DB, bak)
    ib = sqlite3.connect("file:%s?mode=ro" % bak, uri=True).execute("PRAGMA integrity_check").fetchone()[0]
    print("backup: %s (%d bytes, integrity %s)" % (bak, os.path.getsize(bak), ib))
    if ib != "ok":
        print("STOP: the backup is not sound -- nothing written")
        return 2
    dbp, spp = os.path.join(work, "check.db"), os.path.join(work, "spine.db")
    copydb(LIVE_DB, dbp)
    copydb(LIVE_SPINE, spp)
    Q = qty_ok(run_probe("qty", dbp, spp))
    for key, ok, seen in Q:
        print("  %s the voucher card says the brief's words: %s %s" % ("ok  " if ok else "STOP", key, mask(seen)))
    if not all(ok for _k, ok, _s in Q):
        print("STOP: a voucher card no longer reads as the brief says -- nothing written")
        return 2
    print("before: amir_job rows %d; DUTY_MAP amir.marg_jobs due %s" % (n0, due0))
    res = insert(LIVE_DB)
    rows1, aud1, due1, n1 = rows_of(LIVE_DB)
    print("inserted: %s" % res)
    for r in rows1:
        print("  row id %s key %r kind %s subject %r created_at %s created_by %s show_from %s" % (r["id"], r["key"], r["kind"], r["subject"], r["created_at"], r["created_by"], r["show_from"]))
        print("      text_hi %r | sub_hi %r" % (r["text_hi"], r["sub_hi"]))
    for a in aud1:
        print("  audit id %s at %s who %s action %s ref %r detail %s" % (a["id"], a["at"], a["who"], a["action"], a["ref"], a["detail"]))
    print("after: amir_job rows %d; DUTY_MAP amir.marg_jobs due %s" % (n1, due1))
    ok = row_shape_ok(rows1) and len(aud1) == 2 and n1 == n0 + 2 and due1[0] == due0[0] + 2
    # read back as amir sees it: a fresh backup-API copy of the live database, the walk-only portal
    copydb(LIVE_DB, dbp)
    penv = walk_portal(work)
    C = run_probe("card", dbp, spp, penv)
    if C:
        blk = C.get("jobs_block") or []
        print("read-back (a copy of the live database taken after the insert), amir's door %s: %s" % (DOOR, C["door_hops"]))
        print("   his 'Ek baar ke kaam' block: %s" % mask(blk[:12]))
        ok = ok and all(j[2] in C["door_segs"] for j in JOBS)
    shutil.rmtree(work, ignore_errors=True)
    print("LIVE %s" % ("DONE" if ok else "RED -- the backup %s stays; see above" % bak))
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    mode = a[0] if a else ""
    work = a[a.index("--work") + 1] if "--work" in a else ("/tmp/s569walk" if mode == "walk" else "/tmp/s569live")
    if mode == "probe":
        return probe()
    if mode == "walk":
        return walk(work)
    if mode == "live":
        return live(work)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
