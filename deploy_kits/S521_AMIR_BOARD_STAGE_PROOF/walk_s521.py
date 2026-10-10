#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s521.py -- kit S521_AMIR_BOARD_STAGE_PROOF: the walk (the brief's walk section), on the server, on scratch copies only.

    python3 -B walk_s521.py --kit DIR --work /tmp/... --fin-new DIR --fin-old DIR --por DIR --db finance.db --adb assets.db --spine spine.db
                            [--json-out FILE]   (the NEW board JSON as amir, for the render check on the PC)

  fin-new / fin-old   scratch copies of /root/finance: NEW carries the built stock_app.py, OLD is the box as it is (1f43f47e).
  por                 a scratch copy of /root/portal's *.py and tile_grants.json; the walk writes its OWN secret and user store there.
  db / adb / spine    backup-API copies; every probe works on its OWN further copy; the walk's rows carry W521 in their item names and
                      live under count ids beyond any real one.

Two probes, each a fresh process per side ("api": the live case through the board's own route, signed in through a walk-only portal as
amir and as the owner, and his step 6; "fn": the synthetic stage A / C cases on the NEW function), every one with ORDER_PUSH_STUB, a
scratch RING_PORTAL_DIR and REPORTS_NTFY_STUB: nothing reaches a phone.  _S446_PROOF_CACHE and _S444_RENAMES_CACHE never carry from
OLD to NEW (each side its own process) and are cleared before every direct call.  Every control is the same probe on the OLD file and
must go red there.  No person, phone or account number is in this file.
"""
import argparse
import hashlib
import html as _html
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys

TAG = "W521JSON "
EARLIER = ("ANKLE BINDER BAMBOO M", "TYNOR WRIST SPLINT RT M ELAST")
USERS = {"amir": "staff", "manoj": "doctor"}
WAIT_HI = "Naam badalna — orthotic voucher Marg mein sahi hone ke baad"
NO_FIGURE_HI = "Abhi baaki — closing stock aa gaya — server ka hisaab banna baaki (bikri report ke baad)"
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + mask(label) + (("   [" + mask(str(got))[:900] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def md5b(b):
    return hashlib.md5(b).hexdigest()


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def ins(con, table, row):
    row = dict(row)
    for _cid, name, typ, notnull, dflt, pk in con.execute("PRAGMA table_info(%s)" % table).fetchall():
        if notnull and dflt is None and not pk and name not in row:
            row[name] = 0 if "INT" in (typ or "").upper() else ""
    cols = list(row)
    return con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(cols), ", ".join("?" * len(cols))), [row[c] for c in cols]).lastrowid


def texts(h):
    return [_html.unescape(x).strip() for x in re.findall(r">([^<]{3,200})<", h or "")]


def board_view(j):
    """The part of the board JSON the walk judges (item names and counts only)."""
    j = j or {}
    rn = (j.get("renames") or {}).get("rows") or []
    return dict(ok=j.get("ok"), count_id=j.get("count_id"), proof_state=j.get("proof_state"), proof_hi=j.get("proof_hi"),
                renames_ready=j.get("renames_ready"), renames_wait_hi=j.get("renames_wait_hi"), renames_n=len(rn),
                renames_planned=sum(1 for r in rn if r.get("state") == "planned"),
                vouchers_flat_n=len(((j.get("made") or {}).get("vouchers_flat") or [])), stage=j.get("stage"), you=(j.get("you") or {}).get("user"))


# ============================================================================================================== the "api" probe
def probe_api():
    FIN, POR, DB, SIDE = (os.environ[k] for k in ("FINDIR", "PORDIR", "FINANCE_DB", "SIDE"))
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import stock_app as SA                                              # noqa: E402
    assert SA.__file__.startswith(FIN), SA.__file__
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W521J"])["pw"]
    c = sqlite3.connect(DB, timeout=60)
    root = SA._s446_root(c)                                             # the count whose vouchers Amir works -- by key, never by counting
    try:
        import item_alias                                               # noqa: E402,PLC0415
        alias_n = len(item_alias.rows(c))
        alias_planned = sum(1 for r in item_alias.rows(c) if r.get("state") == "planned")
    except Exception as e:                                              # noqa: BLE001
        alias_n, alias_planned = None, str(e)[:80]
    ev0 = [list(r) for r in c.execute("SELECT stage, event, ref, detail FROM stock_stage_event WHERE count_id=? ORDER BY id", (root,))]
    out = dict(side=SIDE, root=root, alias_n=alias_n, alias_planned=alias_planned, events_before=ev0, board={}, step6={})
    for who in USERS:
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        ck = {"Cookie": "clinic_sso=" + (m.group(1) if m else "")}
        rr = fc.get("/finance/stock/api/pad/amir/%d" % root, base_url=BASE, headers=ck)
        j = rr.get_json(silent=True) or {}
        out["board"][who] = dict(code=rr.status_code, **board_view(j))
        if who == "amir" and os.environ.get("W521_JSON_OUT"):
            with open(os.environ["W521_JSON_OUT"], "w", encoding="utf-8") as fh:
                json.dump(j, fh, ensure_ascii=False, indent=1)
        rr = fc.get("/finance/amir/step/6", base_url=BASE, headers=ck)
        h = rr.get_data(as_text=True)
        tx = texts(h)
        out["step6"][who] = dict(code=rr.status_code, naam=[x for x in tx if "aam badl" in x.lower()][:3], ortho=[x for x in tx if x.startswith("Orthotic")][:3],
                                 earlier=[b for b in EARLIER if b in h], block=("Marg mein yeh abhi sahi nahi hain" in h))
    # his step-6 rename duty, asked directly (the cache cleared): NEW asks the stage, OLD asks _proof_state
    SA._S444_RENAMES_CACHE.clear()
    SA._S446_PROOF_CACHE.clear()
    try:
        ready, n_open = SA._s444_renames(c, int(root))
        out["s444_renames"] = dict(ready=bool(ready), open=int(n_open))
    except Exception as e:                                              # noqa: BLE001
        out["s444_renames"] = dict(error=str(e)[:120])
    try:
        st = SA.amir_stage(c, root)
        out["stage"] = dict(stage=(st or {}).get("stage"), B_open=len(((st or {}).get("B") or {}).get("open") or []),
                            A_open=((st or {}).get("A") or {}).get("open"))
    except Exception as e:                                              # noqa: BLE001
        out["stage"] = dict(error=str(e)[:120])
    out["events_after"] = [list(r) for r in c.execute("SELECT stage, event, ref, detail FROM stock_stage_event WHERE count_id=? ORDER BY id", (root,))]
    c.close()
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the "fn" probe
def probe_fn():
    FIN, WORK, SIDE, DB0 = (os.environ[k] for k in ("FINDIR", "WORKDIR", "SIDE", "W521_DB0"))
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    out = dict(side=SIDE, has_fn=False)
    import finance_app as fa                                            # noqa: E402,F401 -- the app, so stock_app is the side's own file
    import stock_app as SA                                              # noqa: E402
    assert SA.__file__.startswith(FIN), SA.__file__
    out["has_fn"] = hasattr(SA, "_s521_stage_proof")
    if not out["has_fn"]:
        print(TAG + json.dumps(out, default=str))
        return

    def mk(name):
        p = os.path.join(WORK, "w521_%s.db" % name)
        copydb(DB0, p)
        c = sqlite3.connect(p, timeout=60)
        c.row_factory = sqlite3.Row
        SA._voucher_ensure(c)
        SA._feed_ensure(c)
        SA._s446_ensure(c)
        return c

    DAYS = dict(B="05-03-2031", A1="08-03-2031")
    RCV = dict(B="2031-03-05T22:30:00", A1="2031-03-08T22:30:00")
    ENTERED = "2031-03-06T10:00:00"

    def feed(c, day_key, item, marg, exp=None):
        d = DAYS[day_key]
        ins(c, "stock_feed", dict(as_on=d, source="push_snapshot W521", item=item, qty=marg, received_at=RCV[day_key]))
        if exp is not None:
            ins(c, "stock_feed", dict(as_on=d, source="push_expected W521 pur_to=%s-%s-%s base=W521" % (d[6:10], d[3:5], d[0:2]), item=item, qty=exp, received_at=RCV[day_key]))

    def voucher(c, root, section, lines, batch=1, entered=True):
        for i, (item, ch) in enumerate(lines, 1):
            ins(c, "stock_voucher_line", dict(count_id=root, round_no=1, kind="ISSUE", batch_no=batch, section=section, item=item, change=ch, marg_to=0,
                                              made_at="2031-03-04T12:00:00", line_no=i))
        if entered:
            ins(c, "stock_voucher_entered", dict(count_id=root, round_no=1, kind="ISSUE", batch_no=batch, marg_voucher_no="W521V%d" % batch, at=ENTERED, by_user="W521"))

    def event(c, root, stage, ev, ref="", detail=None):
        ins(c, "stock_stage_event", dict(count_id=root, stage=stage, event=ev, ref=ref, at="2031-03-04T12:00:00", detail=detail))

    def b0(root):
        return dict(count_id=root, proof_state="x-before", proof_hi="x-before", renames_ready=True, renames_wait_hi="x-before", made=dict(vouchers_flat=[]))

    def run(c, root):
        SA._S446_PROOF_CACHE.clear()
        b = SA._s521_stage_proof(c, b0(root))
        st = SA.amir_stage(c, root)
        A = (st or {}).get("A") or {}
        C = (st or {}).get("C") or {}
        return dict(b={k: b.get(k) for k in ("proof_state", "proof_hi", "renames_ready", "renames_wait_hi")}, same_as_before=(b == b0(root)),
                    stage=(st or {}).get("stage"), A_open=A.get("open"), A_proof=((A.get("proof") or {}).get("state")),
                    card_rows=[r["item"] for r in ((A.get("proof") or {}).get("rows") or [])] + [r["item"] for r in (C.get("wrong") or [])],
                    C_waiting=len(C.get("waiting_export") or []), tail=SA._s488_tail_hi(SA._s488_stage_proof(st)))

    res = {}
    # ---- group 1: one copy -- stage A open (a), stage A wrong (b), stage C wrong (d), stage C nothing wrong (f), stage done (g), no stage (h)
    c = mk("g1")
    for item, d1 in (("W521 A WRONG ONE", 0), ("W521 A WRONG TWO", 0), ("W521 A RIGHT", -10),
                     ("W521 C WRONG", 0), ("W521 C RIGHT", -10), ("W521 F RIGHT", -10), ("W521 G RIGHT", -10)):
        feed(c, "B", item, 100, 100)
        feed(c, "A1", item, 100 + d1, 100)
    c.commit()
    voucher(c, 9521001, "Orthotics", [("W521 A OPEN", -10)], entered=False)                       # (a) stage A, one voucher open
    voucher(c, 9521002, "Orthotics", [("W521 A WRONG ONE", -10), ("W521 A WRONG TWO", -10), ("W521 A RIGHT", -10)])   # (b) stage A, proof wrong
    for root in (9521004, 9521006, 9521007):                                                     # stage C / done: A and B verified by event
        event(c, root, "A", "verified", detail=DAYS["A1"])
        event(c, root, "B", "verified")
    voucher(c, 9521004, "Medicines", [("W521 C WRONG", -10), ("W521 C RIGHT", -10)])             # (d) a released lot, entered, one item wrong
    event(c, 9521004, "C", "release", "1|ISSUE|1")
    voucher(c, 9521006, "Medicines", [("W521 F RIGHT", -10)])                                    # (f) lot 1 right; batch 2 not yet released
    voucher(c, 9521006, "Medicines", [("W521 F NEXT", -10)], batch=2, entered=False)
    event(c, 9521006, "C", "release", "1|ISSUE|1")
    voucher(c, 9521007, "Medicines", [("W521 G RIGHT", -10)])                                    # (g) the only lot right -> stage done
    event(c, 9521007, "C", "release", "1|ISSUE|1")
    c.commit()
    for tag, root in (("a_open", 9521001), ("b_wrong", 9521002), ("d_c_wrong", 9521004), ("f_c_done", 9521006), ("g_done", 9521007), ("h_none", 9521999)):
        try:
            res[tag] = run(c, root)
        except Exception as e:                                          # noqa: BLE001
            res[tag] = dict(error="%s: %s" % (type(e).__name__, str(e)[:200]))
    c.close()
    # ---- group 2: its own copy -- the after-closing is Marg's only (no server figure): the proof waits, S488 says why (c, e)
    c = mk("g2")
    for item in ("W521 E ORTHO", "W521 E MED"):
        feed(c, "B", item, 100, 100)
        feed(c, "A1", item, 90)                                         # marg only -> why = no_figure
    c.commit()
    voucher(c, 9521003, "Orthotics", [("W521 E ORTHO", -10)])                                    # (c) stage A, proof export
    event(c, 9521005, "A", "verified", detail=DAYS["A1"])
    event(c, 9521005, "B", "verified")
    voucher(c, 9521005, "Medicines", [("W521 E MED", -10)])                                      # (e) stage C, the lot waiting for an export
    event(c, 9521005, "C", "release", "1|ISSUE|1")
    c.commit()
    for tag, root in (("c_export", 9521003), ("e_c_export", 9521005)):
        try:
            res[tag] = run(c, root)
        except Exception as e:                                          # noqa: BLE001
            res[tag] = dict(error="%s: %s" % (type(e).__name__, str(e)[:200]))
    c.close()
    out["cases"] = res
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the walk
def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("--probe-fn", "--probe-api"):
        return probe_fn() if sys.argv[1] == "--probe-fn" else probe_api()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--fin-new", "--fin-old", "--por", "--db", "--adb", "--spine"):
        ap.add_argument(k, required=True)
    ap.add_argument("--json-out", default="")
    a = ap.parse_args()
    Wd = os.path.abspath(a.work)
    assert Wd.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/"), "refusing a non-scratch path: %s" % Wd
    os.makedirs(Wd)
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W521 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                 # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    for role in ("staff", "doctor"):
        try:
            clinic_users.add_role(store, role)
        except ValueError:
            pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])

    def run(mode, side, fin):
        wd = os.path.join(Wd, "%s_%s" % (mode, side))
        for sub in ("nosso", "noring", "nomarg"):
            os.makedirs(os.path.join(wd, sub))
        dbp, adbp, spp = [os.path.join(wd, "w521_%s.db" % x) for x in ("app", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, SIDE=side, FINDIR=fin, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, W521_DB0=a.db,
                   FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=(a.por if mode == "api" else os.path.join(wd, "nosso")), CLINIC_PORTAL_DIR=a.por,
                   CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, W521J=json.dumps(dict(pw=pw)),
                   MARG_INGEST_DIR=os.path.join(wd, "nomarg"), RING_PORTAL_DIR=os.path.join(wd, "noring"), ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"),
                   REPORTS_NTFY_STUB=os.path.join(wd, "ntfy_stub.jsonl"), ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"), SR_DB_PATH=os.path.join(wd, "no_staff_register.db"),
                   CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
        if mode == "api" and side == "new" and a.json_out:
            env["W521_JSON_OUT"] = os.path.abspath(a.json_out)
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "ORDER_CLOCK", "ORDER_PUSH_NONE", "FINANCE_MARG_TOKEN", "FINANCE_DEV_USER", "FINANCE_DEV_ROLE", "FINANCE_CRON_TOKEN"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe-" + mode], env=env, cwd=fin, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=1800)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s %s probe did not finish (exit %s); its last lines:" % (side, mode, p.returncode))
            for l in p.stdout.splitlines()[-40:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])

    # ------------------------------------------------------------------------------------------------------------------------------- 1
    print("-- 1  the live case on the copy: Amir's board through its own route, signed in as amir and as the owner (a walk-only portal)")
    NW, OL = run("api", "new", a.fin_new), run("api", "old", a.fin_old)
    if not check("both board probes ran to the end (NEW = the box + S521, OLD = the box as it is), each on its own copies", NW is not None and OL is not None):
        return finish()
    na, nm, oa, om = NW["board"]["amir"], NW["board"]["manoj"], OL["board"]["amir"], OL["board"]["manoj"]
    print("   root count %s; item_alias rows on the copy %s (planned %s); stage on the NEW copy %s; events before %s / after %s"
          % (NW["root"], NW["alias_n"], NW["alias_planned"], NW["stage"], NW["events_before"], NW["events_after"]))
    print("   NEW as amir : %s" % mask(na))
    print("   NEW as owner: %s" % mask(nm))
    print("   OLD as amir : %s" % mask(oa))
    check("NEW as amir: the board answers 200 and proof_state is 'done' (%s)" % na.get("proof_state"), na.get("code") == 200 and na.get("proof_state") == "done")
    check("NEW as amir: proof_hi carries 'Orthotic: sab sahi' and names neither %s nor %s (%s)" % (EARLIER[0], EARLIER[1], na.get("proof_hi")),
          "Orthotic: sab sahi" in str(na.get("proof_hi")) and not any(e in str(na.get("proof_hi")) for e in EARLIER))
    check("control OLD as amir: the board names both items under '2 to correct' (%s)" % oa.get("proof_hi"),
          "2 to correct: %s, %s" % EARLIER in str(oa.get("proof_hi")))
    check("NEW as amir: renames_ready true, renames_wait_hi empty, and ALL of item_alias.rows listed (%s of %s; %s still to do)"
          % (na.get("renames_n"), NW["alias_n"], na.get("renames_planned")),
          na.get("renames_ready") is True and not na.get("renames_wait_hi") and na.get("renames_n") == NW["alias_n"] and na.get("renames_n") > 0)
    check("the board and his card say the same number of names to change (board planned %s, card B.open %s)" % (na.get("renames_planned"), NW["stage"].get("B_open")),
          na.get("renames_planned") == NW["stage"].get("B_open") and na.get("renames_planned") > 0)
    check("NEW as amir: made.vouchers_flat is empty -- stage B lists no voucher (%s)" % na.get("vouchers_flat_n"), na.get("vouchers_flat_n") == 0)
    check("NEW as the owner: the same proof_hi as amir's, and renames_ready true (%s / %s)" % (nm.get("proof_hi"), nm.get("renames_ready")),
          nm.get("code") == 200 and nm.get("proof_hi") == na.get("proof_hi") and nm.get("proof_state") == "done" and nm.get("renames_ready") is True and not nm.get("renames_wait_hi"))
    check("control OLD as the owner: renames held back (renames_ready %s) behind _proof_state (%s)" % (om.get("renames_ready"), om.get("proof_hi")),
          om.get("renames_ready") is False)
    print("   the owner sees every voucher (vouchers_flat %s on NEW, %s on OLD); amir sees %s" % (nm.get("vouchers_flat_n"), om.get("vouchers_flat_n"), na.get("vouchers_flat_n")))
    check("the read of the board wrote no stage event on the copy (before == after)", NW["events_before"] == NW["events_after"], NW["events_after"])
    # his step-6 rename duty
    s6n, s6o = NW["step6"]["amir"], OL["step6"]["amir"]
    print("   NEW step 6 as amir: %s; as the owner: %s" % (mask(s6n), mask(NW["step6"]["manoj"])))
    check("NEW step 6 as amir (stage B): the rename line 'Naam badlo: N naam' shows, 'Orthotic: sab sahi' shows, no item named wrong (%s)" % s6n.get("naam"),
          s6n.get("code") == 200 and any(x.startswith("Naam badlo:") for x in s6n.get("naam") or []) and any("sab sahi" in x for x in s6n.get("ortho") or [])
          and not s6n.get("earlier") and not s6n.get("block"))
    check("NEW _s444_renames (his step-6 duty, asked directly): ready True from the stage, open = the planned names (%s)" % NW.get("s444_renames"),
          (NW.get("s444_renames") or {}).get("ready") is True and (NW.get("s444_renames") or {}).get("open") == na.get("renames_planned"))
    check("control OLD _s444_renames: ready False (it asks _proof_state, which is not 'done') (%s)" % OL.get("s444_renames"),
          (OL.get("s444_renames") or {}).get("ready") is False)

    # ------------------------------------------------------------------------------------------------------------------------------- 2
    print("-- 2  synthetic W521 counts on their own copies: stage A open / wrong / export, stage C wrong / export / nothing wrong, done, no stage")
    FN = run("fn", "new", a.fin_new)
    if not check("the function probe ran to the end on NEW and the file carries _s521_stage_proof", FN is not None and FN.get("has_fn")):
        return finish()
    cs = FN["cases"]
    for k, v in cs.items():
        print("   %-10s %s" % (k, mask(v)))
    g = lambda k: (cs.get(k) or {}).get("b") or {}                     # noqa: E731
    check("(a) stage A with a voucher open -> wait, no exception (A's proof is None); renames_ready False with the filter's wording",
          cs["a_open"].get("stage") == "A" and cs["a_open"].get("A_open") == 1 and g("a_open") == dict(proof_state="wait", proof_hi="Abhi baaki — pehle orthotic voucher Marg mein daaliye", renames_ready=False, renames_wait_hi=WAIT_HI))
    check("(b) a wrong stage-A proof -> wrong, with the names its card would show, in the card's order",
          cs["b_wrong"].get("stage") == "A" and cs["b_wrong"].get("A_proof") == "wrong" and cs["b_wrong"].get("card_rows") == ["W521 A WRONG ONE", "W521 A WRONG TWO"]
          and g("b_wrong") == dict(proof_state="wrong", proof_hi="Marg = shelf: 2 theek karna hai — W521 A WRONG ONE, W521 A WRONG TWO", renames_ready=False, renames_wait_hi=WAIT_HI))
    check("(c) stage A waiting for an export -> export, the line carries the S488 reason tail (no_figure), the same tail the card reads",
          cs["c_export"].get("stage") == "A" and cs["c_export"].get("A_proof") == "export" and cs["c_export"].get("tail") and cs["c_export"]["tail"] in g("c_export").get("proof_hi", "")
          and g("c_export") == dict(proof_state="export", proof_hi=NO_FIGURE_HI, renames_ready=False, renames_wait_hi=WAIT_HI))
    check("(d) one wrong stage-C lot -> wrong with its names; renames_ready True, wait_hi empty",
          cs["d_c_wrong"].get("stage") == "C" and cs["d_c_wrong"].get("card_rows") == ["W521 C WRONG"]
          and g("d_c_wrong") == dict(proof_state="wrong", proof_hi="Marg = shelf: 1 theek karna hai — W521 C WRONG", renames_ready=True, renames_wait_hi=""))
    check("(e) a stage-C lot waiting for an export -> export with the S488 reason tail",
          cs["e_c_export"].get("stage") == "C" and cs["e_c_export"].get("C_waiting") == 1
          and g("e_c_export") == dict(proof_state="export", proof_hi=NO_FIGURE_HI, renames_ready=True, renames_wait_hi=""))
    check("(f) stage C, nothing wrong, the next lot opened -> the right done line",
          cs["f_c_done"].get("stage") == "C" and g("f_c_done") == dict(proof_state="done", proof_hi="Ab tak ke voucher Marg mein sahi ✓", renames_ready=True, renames_wait_hi=""))
    check("(g) stage done -> done, the card's own words",
          cs["g_done"].get("stage") == "done" and g("g_done") == dict(proof_state="done", proof_hi="Orthotic: sab sahi ✓", renames_ready=True, renames_wait_hi=""))
    check("(h) a count with no stage -> b exactly as it came", cs["h_none"].get("stage") is None and cs["h_none"].get("same_as_before") is True)
    return finish()


def finish():
    if FAILS:
        print("WALK_S521 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:220])
        return 1
    print("WALK_S521 GREEN (%d checks)" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
