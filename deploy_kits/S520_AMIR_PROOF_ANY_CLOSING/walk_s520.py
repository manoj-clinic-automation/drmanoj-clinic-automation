#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s520.py -- kit S520_AMIR_PROOF_ANY_CLOSING: the walk (the brief's walk section), on the server, on scratch copies only.

    python3 -B walk_s520.py --kit DIR --work /tmp/... --fin-new DIR --fin-old DIR --por DIR --db finance.db --adb assets.db --spine spine.db

  fin-new / fin-old   scratch copies of /root/finance: NEW carries the built stock_app.py, OLD is the box as it is (bfc2a40b).
  por                 a scratch copy of /root/portal's *.py and tile_grants.json; the walk writes its OWN secret and user store there.
  db / adb / spine    backup-API copies; every probe works on its OWN further copy; the walk's rows carry W520 in their item names and
                      live under count ids beyond any real one.

Each side runs in its own process ("fn": the live case through the card's own path and the synthetic cases; "eye": Amir's card, signed in
through the portal), every one with ORDER_PUSH_STUB, a scratch RING_PORTAL_DIR and REPORTS_NTFY_STUB: nothing reaches a phone.  Each
side's probe is a fresh process, so _S446_PROOF_CACHE never carries from OLD to NEW; it is cleared before every call besides.  Every
control is the same probe on the OLD file and must go red there.  No person, phone or account number is in this file.
"""
import argparse
import datetime as dt
import hashlib
import html as _html
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys

TAG = "W520JSON "
BELTS = ("L S BELT CONT GRAY UNISON L", "L S BELT CONT GRAY UNISON XXL")
EARLIER = ("ANKLE BINDER BAMBOO M", "TYNOR WRIST SPLINT RT M ELAST")
USERS = {"amir": "staff", "manoj": "doctor"}
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


def spans(h):
    return [_html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<(?:span|p|b|li)[^>]*>(.*?)</(?:span|p|b|li)>", h or "", re.S)]


# ============================================================================================================== the "fn" probe
def probe_fn():
    FIN, WORK, SIDE, DB0 = (os.environ[k] for k in ("FINDIR", "WORKDIR", "SIDE", "W520_DB0"))
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    out = dict(side=SIDE)
    import finance_app as fa                                            # noqa: E402,F401 -- the app, so stock_app is the side's own file
    import stock_app as SA                                              # noqa: E402
    assert SA.__file__.startswith(FIN), SA.__file__

    def mk(name):
        p = os.path.join(WORK, "w520_%s.db" % name)
        copydb(DB0, p)
        c = sqlite3.connect(p, timeout=60)
        c.row_factory = sqlite3.Row
        return p, c

    def proof(c, root, keys, ent, batches):
        SA._S446_PROOF_CACHE.clear()
        r = SA._s446_proof(c, root, keys, ent, batches)
        return dict(state=r.get("state"), rows=[dict(item=x["item"], moved=x.get("moved"), marg=x.get("marg"), should=x.get("should")) for x in (r.get("rows") or [])],
                    as_before=r.get("as_before"), as_after=r.get("as_after"), items=r.get("items"), proven_on=r.get("proven_on"), text=r.get("text"))

    # ---------------------------------------------------------------- 1  the live case, through the card's own path (amir_stage)
    s1 = {}
    _p, c = mk("live")
    SA._S446_PROOF_CACHE.clear()
    st = SA.amir_stage(c)
    A = (st or {}).get("A") or {}
    pr = A.get("proof") or {}
    s1["stage"] = (st or {}).get("stage")
    s1["A"] = dict(total=A.get("total"), entered=A.get("entered"), open=A.get("open"), verified_at=A.get("verified_at"))
    s1["proof"] = dict(state=pr.get("state"), as_before=pr.get("as_before"), as_after=pr.get("as_after"), items=pr.get("items"),
                       rows=[dict(item=x["item"], moved=x.get("moved"), marg=x.get("marg"), should=x.get("should")) for x in (pr.get("rows") or [])],
                       proven_on={k: v for k, v in (pr.get("proven_on") or {}).items() if k in BELTS + EARLIER})
    s1["events"] = [list(r) for r in c.execute("SELECT stage, event, ref, detail FROM stock_stage_event WHERE count_id=1 ORDER BY id")]
    s1["renames_visible"] = (st or {}).get("renames_visible")
    s1["B"] = {k: v for k, v in ((st or {}).get("B") or {}).items() if k in ("total", "verified", "ticked")}
    c.close()
    out["s1"] = s1

    # ---------------------------------------------------------------- 2  synthetic, keyed W520
    s2 = {}
    _p, c = mk("synth")
    SA._voucher_ensure(c)
    SA._feed_ensure(c)
    DAYS = dict(B="05-03-2031", A1="08-03-2031", A2="09-03-2031", A3="10-03-2031")
    RCV = dict(B="2031-03-05T22:30:00", A1="2031-03-08T22:30:00", A2="2031-03-09T22:30:00", A3="2031-03-10T22:30:00")
    ENTERED = "2031-03-06T10:00:00"

    def feed(root_tag, day_key, item, marg, exp, basis="W520"):
        d = DAYS[day_key]
        ins(c, "stock_feed", dict(as_on=d, source="push_snapshot %s" % root_tag, item=item, qty=marg, received_at=RCV[day_key]))
        ins(c, "stock_feed", dict(as_on=d, source="push_expected %s pur_to=%s-%s-%s base=%s" % (root_tag, d[6:10], d[3:5], d[0:2], basis), item=item, qty=exp, received_at=RCV[day_key]))

    def voucher(root, section, lines, batch=1):
        for i, (item, ch) in enumerate(lines, 1):
            ins(c, "stock_voucher_line", dict(count_id=root, round_no=1, kind="ISSUE", batch_no=batch, section=section, item=item, change=ch, marg_to=0,
                                              made_at="2031-03-04T12:00:00", line_no=i))
        ins(c, "stock_voucher_entered", dict(count_id=root, round_no=1, kind="ISSUE", batch_no=batch, marg_voucher_no="W520V%d" % batch, at=ENTERED, by_user="W520"))
    # the feed rows are shared by every synthetic root (stock_feed is not per count): one set of W520 items with a known pattern
    ITEMS = {"W520 ALWAYS WRONG": (0, 0, 0), "W520 RIGHT NEWEST": (0, 0, -10), "W520 RIGHT FIRST": (-10, 0, 0), "W520 RIGHT MIDDLE": (0, -10, 0),
             "W520 MED RIGHT FIRST": (-10, 0, 0), "W520 MED RIGHT MIDDLE": (0, -10, 0)}
    for item, (d1, d2, d3) in ITEMS.items():                        # marg - expected: 100 - 100 before; then 100 + d - 100 after
        feed("W520", "B", item, 100, 100)
        feed("W520", "A1", item, 100 + d1, 100)
        feed("W520", "A2", item, 100 + d2, 100)
        feed("W520", "A3", item, 100 + d3, 100)
    c.commit()
    R1 = 9520001
    voucher(R1, "Orthotics", [(i, -10) for i in ("W520 ALWAYS WRONG", "W520 RIGHT NEWEST", "W520 RIGHT FIRST", "W520 RIGHT MIDDLE")])
    R2 = 9520002
    voucher(R2, "Medicines", [("W520 MED RIGHT FIRST", -10), ("W520 MED RIGHT MIDDLE", -10)])
    c.commit()
    for tag, root in (("ortho", R1), ("med", R2)):
        b = SA._s446_batches(c, root)
        e = SA._s446_entered(c, root)
        s2[tag] = proof(c, root, list(b), e, b)
    c.close()
    out["s2"] = s2
    # the re-based cases (a later closing on another basis): its own copy, the same items, the first closing re-based / every closing re-based
    s3 = {}
    _p, c = mk("rebase")
    SA._voucher_ensure(c)
    SA._feed_ensure(c)
    for item, (d1, d2, d3) in ITEMS.items():
        feed("W520R", "B", item, 100, 100)
        feed("W520R", "A1", item, 100 + d1, 100, basis="W520other")  # the FIRST closing after the vouchers is on another basis
        feed("W520R", "A2", item, 100 + d2, 100)
        feed("W520R", "A3", item, 100 + d3, 100)
    c.commit()
    R3 = 9520003
    voucher(R3, "Orthotics", [(i, -10) for i in ("W520 RIGHT FIRST", "W520 RIGHT NEWEST", "W520 RIGHT MIDDLE")])
    b = SA._s446_batches(c, R3)
    e = SA._s446_entered(c, R3)
    s3["first_rebased"] = proof(c, R3, list(b), e, b)
    c.execute("UPDATE stock_feed SET source = replace(source, 'base=W520', 'base=W520other') WHERE source LIKE 'push_expected W520R%' AND as_on IN (?,?,?)", (DAYS["A1"], DAYS["A2"], DAYS["A3"]))
    c.commit()
    s3["all_rebased"] = proof(c, R3, list(b), e, b)
    c.close()
    out["s3"] = s3
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the "eye" probe
def probe_eye():
    FIN, POR, DB, SIDE = (os.environ[k] for k in ("FINDIR", "PORDIR", "FINANCE_DB", "SIDE"))
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import stock_app as SA                                              # noqa: E402
    assert SA.__file__.startswith(FIN)
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W520J"])["pw"]
    out = dict(side=SIDE, eye={})
    for who in USERS:
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        ck = {"Cookie": "clinic_sso=" + (m.group(1) if m else "")}
        pages = {}
        for p in (["/finance/amir"] + ["/finance/amir/step/%d" % n for n in (1, 3, 6)]) if who == "amir" else ["/finance/amir/step/6", "/finance/amir/day"]:
            rr = fc.get(p, base_url=BASE, headers=ck)
            h = rr.get_data(as_text=True)
            sp = [x for x in spans(h) if x]
            txt = [_html.unescape(x).strip() for x in re.findall(r">([^<]{3,160})<", h)]
            pages[p] = dict(code=rr.status_code, belts=[b for b in BELTS if b in h], earlier=[b for b in EARLIER if b in h],
                            block=("Marg mein yeh abhi sahi nahi hain" in h), sab_sahi=("sab sahi" in h), naam=[x for x in txt if "aam badl" in x.lower()][:3],
                            ortho=[x for x in txt if x.startswith("Orthotic")][:4], big=[x for x in sp if "voucher" in x.lower()][:6])
        out["eye"][who] = pages
    c = sqlite3.connect(DB, timeout=60)
    out["events"] = [list(r) for r in c.execute("SELECT stage, event, ref, detail FROM stock_stage_event WHERE count_id=1 ORDER BY id")]
    c.close()
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the walk
def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("--probe-fn", "--probe-eye"):
        return probe_fn() if sys.argv[1] == "--probe-fn" else probe_eye()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--fin-new", "--fin-old", "--por", "--db", "--adb", "--spine"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    Wd = os.path.abspath(a.work)
    assert Wd.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/"), "refusing a non-scratch path: %s" % Wd
    os.makedirs(Wd)
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W520 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
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
        dbp, adbp, spp = [os.path.join(wd, "w520_%s.db" % x) for x in ("app", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, SIDE=side, FINDIR=fin, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, W520_DB0=a.db,
                   FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=(a.por if mode == "eye" else os.path.join(wd, "nosso")), CLINIC_PORTAL_DIR=a.por,
                   CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, W520J=json.dumps(dict(pw=pw)),
                   MARG_INGEST_DIR=os.path.join(wd, "nomarg"), RING_PORTAL_DIR=os.path.join(wd, "noring"), ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"),
                   REPORTS_NTFY_STUB=os.path.join(wd, "ntfy_stub.jsonl"), ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"), SR_DB_PATH=os.path.join(wd, "no_staff_register.db"),
                   CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
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
    NW, OL = run("fn", "new", a.fin_new), run("fn", "old", a.fin_old)
    if not check("both function probes ran to the end (NEW = the box + S520, OLD = the box as it is), each on its own copies", NW is not None and OL is not None):
        return finish()

    # ------------------------------------------------------------------------------------------------------------------------------- 1
    print("-- 1  the live case: Amir's orthotic stage-A proof through the card's own path (amir_stage on a copy)")
    n1, o1 = NW["s1"], OL["s1"]
    pn, po_ = n1["proof"], o1["proof"]
    rows_n = [r["item"] for r in pn["rows"]]
    check("NEW: the two belts are not in the rows (%s) and their proven_on is the 04-10 closing (%s)" % (rows_n, pn["proven_on"]),
          not any(b in rows_n for b in BELTS) and all(pn["proven_on"].get(b) == "04-10-2026" for b in BELTS), pn)
    check("control OLD lists them both (%s)" % [r["item"] for r in po_["rows"]], all(b in [r["item"] for r in po_["rows"]] for b in BELTS))
    print("   NEW state: %s (as_before %s, as_after %s, items %s); rows that remain: %s; the earlier two (%s) %s"
          % (pn["state"], pn["as_before"], pn["as_after"], pn["items"], pn["rows"] or "none", ", ".join(EARLIER),
             "REMAIN WRONG" if any(r["item"] in EARLIER for r in pn["rows"]) else "are right (proven on %s)" % {k: v for k, v in pn["proven_on"].items() if k in EARLIER}))
    print("   NEW card path: stage %s, A %s, stage events on the copy %s, renames_visible %s, B %s" % (n1["stage"], n1["A"], n1["events"], n1["renames_visible"], n1["B"]))
    check("the live stage-A proof on NEW is done or wrong, never export (%s)" % pn["state"], pn["state"] in ("done", "wrong"))
    if pn["state"] == "done":
        check("a passed proof on the copy wrote the stage-A verified event with detail = as_after, and the card moves to stage B (the renames) by the existing code (%s / stage %s)"
              % (n1["events"], n1["stage"]), any(e[0] == "A" and e[1] == "verified" and e[3] == pn["as_after"] for e in n1["events"]) and n1["stage"] in ("B", "C", "done"))

    # ------------------------------------------------------------------------------------------------------------------------------- 2
    print("-- 2  synthetic W520 items: one before-closing, three after (first, middle, newest)")
    n2, o2 = NW["s2"], OL["s2"]
    o = n2["ortho"]
    wrong = sorted(r["item"] for r in o["rows"])
    check("NEW orthotic lot: wrong, rows = ALWAYS WRONG and RIGHT MIDDLE from the newest closing (moved 0, marg 100, should 90) (%s); proven_on NEWEST=10-03, FIRST=08-03 (%s)"
          % (o["rows"], o["proven_on"]),
          o["state"] == "wrong" and wrong == ["W520 ALWAYS WRONG", "W520 RIGHT MIDDLE"] and all(r["moved"] == 0 and r["marg"] == 100 and r["should"] == 90 for r in o["rows"])
          and o["as_after"] == "10-03-2031" and o["as_before"] == "05-03-2031"
          and o["proven_on"] == {"W520 RIGHT NEWEST": "10-03-2031", "W520 RIGHT FIRST": "08-03-2031"})
    oo = o2["ortho"]
    check("control OLD: RIGHT FIRST is wrong too (only the newest counted) (%s)" % sorted(r["item"] for r in oo["rows"]),
          sorted(r["item"] for r in oo["rows"]) == ["W520 ALWAYS WRONG", "W520 RIGHT FIRST", "W520 RIGHT MIDDLE"])
    m = n2["med"]
    check("NEW medicine lot (stage C's path, the same function): RIGHT FIRST ok, RIGHT MIDDLE wrong (%s / %s)" % ([r["item"] for r in m["rows"]], m["proven_on"]),
          m["state"] == "wrong" and [r["item"] for r in m["rows"]] == ["W520 MED RIGHT MIDDLE"] and m["proven_on"] == {"W520 MED RIGHT FIRST": "08-03-2031"})
    check("control OLD medicine lot: both wrong (%s)" % [r["item"] for r in o2["med"]["rows"]], sorted(r["item"] for r in o2["med"]["rows"]) == ["W520 MED RIGHT FIRST", "W520 MED RIGHT MIDDLE"])
    n3 = NW["s3"]
    fr = n3["first_rebased"]
    check("the first closing after the vouchers on ANOTHER basis is skipped (never a later closing standing in for it): RIGHT FIRST is wrong, RIGHT NEWEST ok, as_after the newest on R's basis (%s / %s)"
          % ([r["item"] for r in fr["rows"]], fr["proven_on"]),
          fr["state"] == "wrong" and sorted(r["item"] for r in fr["rows"]) == ["W520 RIGHT FIRST", "W520 RIGHT MIDDLE"] and fr["proven_on"] == {"W520 RIGHT NEWEST": "10-03-2031"}
          and fr["as_after"] == "10-03-2031")
    ar = n3["all_rebased"]
    check("every closing after the vouchers on another basis: the 're-based' answer, naming R and the newest (%s)" % ar["text"],
          ar["state"] == "export" and ar["text"] == "re-based between 05-03-2031 and 10-03-2031")

    # ------------------------------------------------------------------------------------------------------------------------------- 3
    print("-- 3  staff-eye on the scratch copy: amir's card through the portal (a walk-only store and secret)")
    EN, EO = run("eye", "new", a.fin_new), run("eye", "old", a.fin_old)
    if not check("both staff-eye probes ran to the end", EN is not None and EO is not None):
        return finish()
    en, eo = EN["eye"]["amir"], EO["eye"]["amir"]
    check("NEW: on every page of Amir's card the block names neither belt (%s); step 6 is 200" % {p: (v["code"], v["belts"]) for p, v in en.items()},
          all(not v["belts"] for v in en.values()) and en["/finance/amir/step/6"]["code"] == 200)
    check("control OLD: step 6 shows the two belts under 'Marg mein yeh abhi sahi nahi hain' (%s)" % eo["/finance/amir/step/6"]["belts"],
          eo["/finance/amir/step/6"]["block"] and sorted(eo["/finance/amir/step/6"]["belts"]) == sorted(BELTS))
    s6 = en["/finance/amir/step/6"]
    print("   NEW step 6 as amir: block 'Marg mein yeh abhi sahi nahi hain' %s; 'sab sahi' %s; Orthotic lines %s; naam lines %s; stage events on the eye copy %s"
          % (s6["block"], s6["sab_sahi"], s6["ortho"], s6["naam"], EN["events"]))
    print("   NEW step 6 as the owner: Orthotic lines %s; naam lines %s" % (EN["eye"]["manoj"]["/finance/amir/step/6"]["ortho"], EN["eye"]["manoj"]["/finance/amir/step/6"]["naam"]))
    return finish()


def finish():
    if FAILS:
        print("WALK_S520 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:220])
        return 1
    print("WALK_S520 GREEN (%d checks)" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
