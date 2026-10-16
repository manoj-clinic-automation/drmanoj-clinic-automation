#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""add_jobs_s572.py -- kit S572_TWO_MORE_LINES (data only): two more one-time 'tap' jobs on Amir's card, the S569 Part B way.

    python3 -B add_jobs_s572.py walk [--work /tmp/s572walk]   scratch copies only (backup API): the staff-eye walk + its control
    python3 -B add_jobs_s572.py live [--work /tmp/s572live]   the build lock must name S572: backup, assert, insert, read back

Both modes first read the owner's proof (/finance/stock/api/pad/hub/1, proof.C.wrong) on a backup-API copy: a job is added only while
its line is still wrong with the brief's numbers (FOLITRAX 15 MG TAB need -6 moved 0, packing 1*5; OSTOVAXL DM need +21 moved +25,
packing 1*10). A line no longer wrong is NOT added and is said so. The quantity words are qty_words' own (6 of 1*5, 4 of 1*10); if
they differ from the brief's, qty_words' words are used and printed. The insert is keyed (amir_job.key is UNIQUE): a second run adds
nothing and says ALREADY. Each row added is audited job_added by system through amir_day's own _audit. S569's rows are never written.
The walk signs in as amir through a walk-only portal (a random secret and its own user store in the scratch folder, never the live
ones), renders /finance/amir and the door /finance/amir/step/6 before and after, and diffs the card. Its control runs the same card
checks on the render without the new rows (= the old state): they must go RED. No person, phone or account number is printed."""
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
KIT = "S572"
AUDIT = {"kit": "S572", "owner_word": "16-Oct 13:47"}
# key, subject, the brief's qty words, sub_hi, the proof line it answers: (need, moved, packing, units to issue)
JOBS = [
    ("fix:S572:FOLITRAX 15 MG TAB", "FOLITRAX 15 MG TAB", "1 patte + 1 goli", "6 Sep ki stock ginti \u00b7 voucher 8 ki line", (-6, 0, "1*5", 6)),
    ("fix:S572:OSTOVAXL DM", "OSTOVAXL DM", "4 goli", "6 Sep ki stock ginti \u00b7 receive voucher 6 ki line", (21, 25, "1*10", 4)),
]
S569_KEYS = ("fix:S569:KT ROS DT", "fix:S569:VINBACTUM DS")
S569_TEXTS = ("KT ROS DT \u2014 Marg mein STOCK ISSUE kijiye: 6 patte + 11 goli", "VINBACTUM DS \u2014 Marg mein STOCK ISSUE kijiye: 25 nag")
DUE_SQL = ("SELECT COUNT(*) AS n, MIN(substr(show_from,1,10)) AS since FROM amir_job WHERE show_from IS NOT NULL AND done_at IS NULL "
           "AND NOT (said_at IS NOT NULL AND said_at > COALESCE(reopened_at, ''))")   # DUTY_MAP amir.marg_jobs, byte-equal
DOOR, MARK, TILE = "/finance/amir/step/6", "Ek baar ke kaam", "Amir ka kaam"
BAD_WORDS = ("check", "chhoot", "galat", "sahi", "verdict")      # D708: only "do this" words


def text_of(subj, qty):
    return "%s \u2014 Marg mein STOCK ISSUE kijiye: %s" % (subj, qty)


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
    what = os.environ["S572_WHAT"]
    sys.path.insert(0, FIN)
    if what == "card":
        sys.path.insert(0, os.environ["S572_POR"])
    os.chdir(FIN)
    import finance_app as fa                                    # noqa: E402
    import stock_watch as SW                                    # noqa: E402
    SW.SPINE_DB = os.environ["SPINE_DB"]
    assert os.path.abspath(fa.DB_PATH) == os.path.abspath(os.environ["FINANCE_DB"]) and fa.DB_PATH.startswith("/tmp/"), "the probe reads a scratch copy only"
    fc = fa.app.test_client(use_cookies=False)
    out = dict(db=fa.DB_PATH)
    if what == "hub":
        import qty_words as QW                                  # noqa: E402 -- the estate's one quantity speller
        r = fc.get("/finance/stock/api/pad/hub/1", headers={"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"})
        j = r.get_json(silent=True) or {}
        pr = j.get("proof") or {}
        out["status"], out["state"], out["stage"], out["text"] = r.status_code, pr.get("state"), pr.get("stage"), pr.get("text")
        out["wrong"] = [{k: x.get(k) for k in ("item", "need", "need_hi", "moved", "moved_hi", "packing", "pack", "closing_day", "keys")}
                        for x in ((pr.get("C") or {}).get("wrong") or [])]
        out["qw"] = {key: QW.words(n, pk, lang="hi", name=subj) for key, subj, _q, _s, (_n, _m, pk, n) in JOBS}
    else:
        import portal as po                                     # noqa: E402
        BASE = "https://followup.dr-manoj.in"
        pc = po.app.test_client(use_cookies=False)
        W = json.loads(os.environ["S572_W"])
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
    print("S572JSON " + json.dumps(out, default=str))
    return 0


def run_probe(what, dbp, spp, extra_env=None, cwd=FIN):
    nosso = os.path.join(os.path.dirname(dbp), "nosso")         # the hub read: header auth, no SSO secret at all
    os.makedirs(nosso, exist_ok=True)
    env = dict(os.environ, S572_WHAT=what, FINANCE_DB=dbp, SPINE_DB=spp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=nosso)
    if what == "card":                                          # the card: the walk-only portal's cookie, never a header
        env["FINANCE_ALLOW_HEADER_AUTH"] = "0"
    env.update(extra_env or {})
    env.pop("SARVAM_API_KEY", None)
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "probe"], env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, timeout=1500)
    js = [l for l in p.stdout.splitlines() if l.startswith("S572JSON ")]
    if not js:
        print("   the %s probe did not finish (exit %s); its last lines:" % (what, p.returncode))
        for l in p.stdout.splitlines()[-20:]:
            print("     " + mask(l[:300]))
        return None
    return json.loads(js[-1][9:])


def plan(H):
    """From the hub read: [(key, subj, text_hi, sub_hi)] to add -- only lines still wrong with the brief's numbers; prints each decision."""
    if not H or H.get("status") != 200:
        print("STOP: the owner's proof could not be read (%s) -- nothing written" % (H or {}).get("status"))
        return None
    print("   proof: state %s stage %s; text %r" % (H["state"], H["stage"], H["text"]))
    for w in H["wrong"]:
        print("   wrong row: %s need %s (%s) moved %s (%s) packing %s closing %s keys %s" % (w["item"], w["need"], w["need_hi"], w["moved"], w["moved_hi"],
                                                                                         w["packing"], w["closing_day"], w["keys"]))
    out = []
    for key, subj, qty, sub, (need, moved, pk, n) in JOBS:
        rows = [w for w in H["wrong"] if w["item"] == subj]
        hit = [w for w in rows if float(w["need"]) == need and float(w["moved"]) == moved and w["packing"] == pk]
        qw = H["qw"][key]
        print("   qty_words(%d, %s) for %s = %r (the brief: %r)%s" % (n, pk, subj, qw, qty, "" if qw == qty else " -- DIFFERS: qty_words' words used"))
        if not hit:
            print("   NOT ADDED: %s is no longer wrong with need %s / moved %s (seen: %s)" % (subj, need, moved, rows))
            continue
        print("   ok: %s is wrong with need %s, moved %s, packing %s" % (subj, need, moved, pk))
        out.append((key, subj, text_of(subj, qw), sub))
    return out


# ============================================================================ the data step (one transaction, keyed)
def insert(dbp, jobs):
    sys.path.insert(0, FIN)
    import amir_day as AD                                       # noqa: E402 -- its own _audit and _stamp
    cx = sqlite3.connect(dbp, timeout=60)
    try:
        if not cx.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='amir_job'").fetchone():
            raise SystemExit("STOP: amir_job is not in %s -- nothing written" % dbp)
        now = AD._stamp()
        res = []
        cx.execute("BEGIN IMMEDIATE")
        for key, subj, t, s in jobs:
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
    old = [dict(r) for r in db.execute("SELECT * FROM amir_job WHERE key IN (?,?) ORDER BY id", S569_KEYS)]
    due = list(db.execute(DUE_SQL).fetchone())
    n = db.execute("SELECT COUNT(*) FROM amir_job").fetchone()[0]
    db.close()
    return rows, aud, due, n, old


def row_shape_ok(rows, jobs):
    want = {j[0]: j for j in jobs}
    ok = len(rows) == len(jobs)
    for r in rows:
        key, subj, t, s = want.get(r["key"], (None,) * 4)
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
        fh.write("# S572 walk only -- a random secret made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\n"
                 "PORTAL_TOKEN_SEED = 's572-walk-seed'\n" % secret)
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
    env = dict(S572_POR=por, FINANCE_SSO_DIR=por, CLINIC_PORTAL_DIR=por, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"),
               CLINIC_SSO_SECRET=secret, S572_W=json.dumps({"pw": pw}))
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
    print("-- the owner's proof on the copy (/api/pad/hub/1, proof.C.wrong):")
    jobs = plan(run_probe("hub", dbp, spp))
    check("W1 the proof still names both lines wrong with the brief's numbers; qty_words = the brief's words",
          jobs is not None and len(jobs) == 2 and all(j[2] == text_of(J[1], J[2]) for j, J in zip(jobs, JOBS)), [j[2] for j in jobs or []])
    if not jobs:
        print("WALK: nothing to add -- see above")
        shutil.rmtree(work, ignore_errors=True)
        return 1
    rows0, _a0, due0, n0, old0 = rows_of(dbp)
    print("-- before: amir_job rows %d; the new keys present %d; S569 rows %s; DUTY_MAP amir.marg_jobs due %s" % (n0, len(rows0), [r["id"] for r in old0], due0))
    B1 = run_probe("card", dbp, spp, penv)
    B2 = run_probe("card", dbp, spp, penv)
    if not (B1 and B2):
        print("WALK RED: the before card could not be rendered")
        return 1
    res = insert(dbp, jobs)
    print("-- the data step on the scratch copy: %s" % res)
    rows1, aud1, due1, n1, old1 = rows_of(dbp)
    A = run_probe("card", dbp, spp, penv)
    res2 = insert(dbp, jobs)
    rows2, aud2, due2, n2, _old2 = rows_of(dbp)
    print("-- a second run: %s" % res2)
    if not A:
        print("WALK RED: the after card could not be rendered")
        return 1
    ids = {r["key"]: r["id"] for r in rows1}
    texts = [(j[2], j[3], ids.get(j[0])) for j in jobs]
    k = len(jobs)

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
        check("W8 DUTY_MAP amir.marg_jobs due_sql: n %s -> %s (+%d)" % (due_before[0], C["due"][0], k), C["due"][0] == due_before[0] + k, C["due"], into)
    print("-- the staff-eye walk, after the rows (scratch copy):")
    card_checks(A, due0, fails)
    door = A["door_segs"]
    four = [t for t in S569_TEXTS + tuple(t for t, _s, _i in texts) if t in door and MARK in door[:door.index(t)]]
    check("W7b the four lines under %s: S569's two + these two (%d)" % (MARK, len(four)), len(four) == 2 + k, four)
    check("W12 S569's rows untouched (byte-equal before/after)", old0 == old1 and len(old0) == 2, [r["id"] for r in old1])
    vol = set(x for x in difflib.ndiff(B1["door_segs"], B2["door_segs"]) if x[:2] in ("- ", "+ "))
    d = [x for x in difflib.ndiff(B2["door_segs"], A["door_segs"]) if x[:2] in ("- ", "+ ")]
    allowed = {"+ " + x for t, s, _ in texts for x in (t, s, "Kar diya")} | {"+ " + MARK}
    added = [x for x in d if x.startswith("+ ")]
    removed = [x for x in d if x.startswith("- ") and x not in vol and ("+ " + x[2:]) not in vol]
    extra = [x for x in added if x not in allowed and x not in vol and ("- " + x[2:]) not in vol]
    check("W9 nothing else on his card changed: added only the new lines (%d segments), removed none" % len(added),
          not extra and not removed and all(("+ " + t) in added for t, _s, _ in texts), dict(extra=extra, removed=removed))
    hd = [x for x in difflib.ndiff(B2["home_segs"], A["home_segs"]) if x[:2] in ("- ", "+ ")]
    vh = set(x for x in difflib.ndiff(B1["home_segs"], B2["home_segs"]) if x[:2] in ("- ", "+ "))
    hx = [x for x in hd if x not in vh and ("+ " + x[2:]) not in vh and ("- " + x[2:]) not in vh
          and not (x.startswith("+ ") and x in allowed)]
    check("W9b /finance/amir: the same (no other change)", not hx, hx)
    check("W2 %d rows, the brief's shape (tap, created_by S572, show_from = created_at, the rest NULL)" % k, row_shape_ok(rows1, jobs) and n1 == n0 + k,
          [(r["id"], r["key"], r["created_at"]) for r in rows1])
    check("W3 audited: %d job_added by system, %s" % (k, json.dumps(AUDIT)), len(aud1) == k and all(a["who"] == "system" and json.loads(a["detail"]) == AUDIT for a in aud1),
          [(a["id"], a["ref"], a["detail"]) for a in aud1])
    check("W10 a second run adds nothing (ALREADY, rows %d = %d, audits %d = %d)" % (n2, n1, len(aud2), len(aud1)),
          all(x[2] == "ALREADY" for x in res2) and n2 == n1 and len(aud2) == len(aud1) and due2 == due1, res2)
    check("W11 only 'do this' words (D708): none of %s" % (BAD_WORDS,), not any(w in (j[2] + " " + j[3]).lower() for j in jobs for w in BAD_WORDS))
    print("-- CONTROL: the same card checks on the card WITHOUT the new rows (the old state) -- must go RED:")
    card_checks(B2, due0, ctrl)
    must = [l for l in ctrl if l.startswith(("W7", "W8"))]
    cok = len(must) == k + 1
    print("CONTROL %s: %d of %d card checks RED on the old state (W7 x%d, W8 must be RED)" % ("RED as it must" if cok else "DID NOT GO RED", len(must), k + 1, k))
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
    rows0, _a, due0, n0, old0 = rows_of(LIVE_DB)
    if len(rows0) == len(JOBS):
        print("ALREADY INSTALLED: both rows are on the live database (ids %s) -- nothing written" % [r["id"] for r in rows0])
        return 0
    dbp, spp = os.path.join(work, "check.db"), os.path.join(work, "spine.db")
    copydb(LIVE_DB, dbp)
    copydb(LIVE_SPINE, spp)
    print("the owner's proof, re-read on a copy taken now:")
    jobs = plan(run_probe("hub", dbp, spp))
    if not jobs:
        print("STOP: no line to add -- nothing written")
        return 2
    stamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = "%s.bak_S572_%s" % (LIVE_DB, stamp)
    copydb(LIVE_DB, bak)
    ib = sqlite3.connect("file:%s?mode=ro" % bak, uri=True).execute("PRAGMA integrity_check").fetchone()[0]
    print("backup: %s (%d bytes, integrity %s)" % (bak, os.path.getsize(bak), ib))
    if ib != "ok":
        print("STOP: the backup is not sound -- nothing written")
        return 2
    print("before: amir_job rows %d; DUTY_MAP amir.marg_jobs due %s" % (n0, due0))
    res = insert(LIVE_DB, jobs)
    rows1, aud1, due1, n1, old1 = rows_of(LIVE_DB)
    print("inserted: %s" % res)
    for r in rows1:
        print("  row id %s key %r kind %s subject %r created_at %s created_by %s show_from %s" % (r["id"], r["key"], r["kind"], r["subject"], r["created_at"], r["created_by"], r["show_from"]))
        print("      text_hi %r | sub_hi %r" % (r["text_hi"], r["sub_hi"]))
    for a in aud1:
        print("  audit id %s at %s who %s action %s ref %r detail %s" % (a["id"], a["at"], a["who"], a["action"], a["ref"], a["detail"]))
    print("after: amir_job rows %d; DUTY_MAP amir.marg_jobs due %s; S569 rows unchanged %s" % (n1, due1, old0 == old1))
    added = sum(1 for x in res if x[2] == "ADDED")
    ok = row_shape_ok(rows1, jobs) and len(aud1) == len(jobs) and n1 == n0 + added and due1[0] == due0[0] + added and old0 == old1
    # read back as amir sees it: a fresh backup-API copy of the live database, the walk-only portal
    copydb(LIVE_DB, dbp)
    penv = walk_portal(work)
    C = run_probe("card", dbp, spp, penv)
    if C:
        blk = C.get("jobs_block") or []
        print("read-back (a copy of the live database taken after the insert), amir's door %s: %s" % (DOOR, C["door_hops"]))
        print("   his 'Ek baar ke kaam' block: %s" % mask(blk[:20]))
        ok = ok and all(j[2] in C["door_segs"] for j in jobs) and all(t in C["door_segs"] for t in S569_TEXTS)
    else:
        ok = False
    shutil.rmtree(work, ignore_errors=True)
    print("LIVE %s" % ("DONE" if ok else "RED -- the backup %s stays; see above" % bak))
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    mode = a[0] if a else ""
    work = a[a.index("--work") + 1] if "--work" in a else ("/tmp/s572walk" if mode == "walk" else "/tmp/s572live")
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
