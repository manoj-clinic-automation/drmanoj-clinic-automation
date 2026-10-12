#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s539.py -- kit S539_NORTIMER_OUT: the walk (the brief's section 3), on the server, on scratch copies only.

    python3 -B walk_s539.py --kit DIR --work /tmp/... --finance <scratch copy of /root/finance> --db finance.db --spine spine.db --map DUTY_MAP.json

  finance   a scratch copy of the finance folder (no file of it is edited by this kit); the walk imports stock_app from it.
  db/spine  backup-API copies of the live finance.db and spine.db; every case works on its own further copy.
The data step runs as its own process on each copy. Controls: the same reads on the untouched copy, printed red.
No person, phone or account number is in this file."""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys

KEY = (2, "ISSUE", 10)
NORT = "NORTIMER TAB"
FIVE = {"NIMREX P": -11, "NUROKIND LC": -5, "NURVION LC TAB": -38, "OLMETIME H 20": -45, "ONDEM MD 4": -35}
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + mask(label) + (("   [" + mask(str(got))[:1200] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)


def red(label, cond, got=None):
    N[0] += 1
    print(("  RED  control: " if cond else "  FAIL control did not go red: ") + mask(label) + (("   [" + mask(str(got))[:900] + "]") if got is not None else ""))
    if not cond:
        FAILS.append("control: " + label)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def counts(db):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    out = {t: c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t in ("stock_voucher_void", "stock_voucher_settle", "stock_voucher_line",
                                                                              "stock_voucher_entered")}
    c.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--finance", "--db", "--spine", "--map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    W = os.path.abspath(a.work)
    assert W.startswith("/tmp/") and os.path.abspath(a.db).startswith("/tmp/") and os.path.abspath(a.finance).startswith("/tmp/"), "refusing a non-scratch path"
    os.makedirs(W)
    os.makedirs(os.path.join(W, "noring"))
    os.environ.update(SPINE_DB=a.spine, ORDER_PUSH_STUB=os.path.join(W, "push.jsonl"), RING_PORTAL_DIR=os.path.join(W, "noring"),
                      REPORTS_NTFY_STUB=os.path.join(W, "ntfy.jsonl"), FINANCE_DB=os.path.join(W, "none.db"))
    sys.path.insert(0, os.path.join(a.finance, "spine"))
    sys.path.insert(0, a.finance)
    os.chdir(a.finance)
    import stock_app as SA                                              # noqa: E402
    assert os.path.abspath(SA.__file__).startswith(os.path.abspath(a.finance)) and hasattr(SA, "_void_sql"), SA.__file__
    sql12 = [x for x in json.load(open(a.map, encoding="utf-8"))["duties"] if x["id"] == "amir.count_vouchers"][0]["due_sql"]

    def run(db, *extra):
        p = subprocess.run([sys.executable, "-B", os.path.join(a.kit, "data_s539.py"), "--db", db, "--finance", a.finance] + list(extra),
                           cwd=a.finance, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=1800, env=dict(os.environ))
        return p.returncode, p.stdout

    def show(out):
        for l in out.splitlines():
            if l.startswith("DATA_S539"):
                print("   " + mask(l)[:330])

    def read(db):
        for nm in ("_S446_PROOF_CACHE", "_S524_REPORT_CACHE"):
            getattr(SA, nm, {}).clear()
        c = sqlite3.connect(db, timeout=60)
        r = dict(seq=SA._voucher_seq(c, 1), batches=set(SA._s446_batches(c, 1)))
        st = SA.amir_stage(c, 1) or {}
        C = st.get("C") or {}
        r["stage"], r["held"] = st.get("stage"), [(tuple(h["key"]) if h.get("key") else None, h.get("item")) for h in C.get("held") or []]
        roles = {u: sorted(x[0] for x in c.execute("SELECT role FROM unit_role WHERE unit='medical' AND username=? AND active=1", (u,))) for u in ("amir", "manoj")}
        r["board"] = {u: [(v["round_no"], v["kind"], v["batch_no"]) for v in SA._amir_board_light(c, 1, dict(user=u, role=("staff" if u == "amir" else "doctor"),
                                                                                                         roles=roles[u]), st).get("vouchers") or []]
                      for u in ("amir", "manoj")}
        sw = SA._s521_stage_words(c, st)
        r["owner"] = [l["text"] for l in sw.get("owner_lines") or []] + ["Count #1: %s" % sw.get("owner_en")]
        r["due"] = c.execute(sql12).fetchone()[0]
        r["settled"] = [x[0] for x in c.execute("SELECT item FROM stock_voucher_settle WHERE count_id=1")]
        bs = {}
        for rno, kind, bno, item, ch in c.execute("SELECT round_no, kind, batch_no, item, change FROM stock_voucher_line WHERE count_id=1 AND round_no>2"):
            bs.setdefault((rno, kind, bno), {})[item] = int(ch)
        vd = {(x[0], x[1], x[2]) for x in c.execute("SELECT round_no, kind, batch_no FROM stock_voucher_void WHERE count_id=1")}
        r["new"] = [(k, v) for k, v in bs.items() if k not in vd and set(v) & set(FIVE)]
        c.close()
        return r

    # ---- the untouched copy: the controls
    U = os.path.join(W, "untouched.db")
    copydb(a.db, U)
    print("-- the untouched install-day copy (the controls)")
    u = read(U)
    print("   stage %s; C held %s; the owner's board %d vouchers; amir.count_vouchers due %s" % (u["stage"], u["held"], len(u["board"]["manoj"]), u["due"]))
    red("1 OLD: voucher 11 is held in C['held'] (%s)" % u["held"], (KEY, NORT) in u["held"])
    red("1 OLD: NORTIMER on the owner's Needs-you", any(NORT in t for t in u["owner"]), [t for t in u["owner"] if NORT in t])
    red("1 OLD: voucher 11 a batch, on the owner's board", KEY in u["batches"] and KEY in u["board"]["manoj"])

    # ---- 1. the data step on a copy
    A = os.path.join(W, "after.db")
    copydb(a.db, A)
    c0 = counts(A)
    print("-- 1 the data step on a copy of the live finance.db (+ the live spine.db)")
    rc, out = run(A)
    show(out)
    c1 = counts(A)
    check("1: exit 0, committed (rows %s -> %s)" % (c0, c1), rc == 0 and "DATA_S539: committed" in out and c1["stock_voucher_void"] == c0["stock_voucher_void"] + 1
          and c1["stock_voucher_settle"] == c0["stock_voucher_settle"] + 1 and c1["stock_voucher_line"] == c0["stock_voucher_line"] + 5)
    n = read(A)
    check("1: voucher 11 gone from _s446_batches and from the board as amir and as the owner", KEY not in n["batches"] and KEY not in n["board"]["amir"]
          and KEY not in n["board"]["manoj"])
    check("1: amir.count_vouchers (v12 SQL) %s -> %s -- voucher 11 was never released, so never due; it can no longer become due" % (u["due"], n["due"]),
          n["due"] == u["due"])
    check("1: NORTIMER TAB in stock_voucher_settle (%s)" % n["settled"], NORT in n["settled"])
    check("1: exactly one new ISSUE batch with exactly the five lines and their 6-Sep changes: %s" % n["new"],
          len(n["new"]) == 1 and n["new"][0][1] == FIVE and n["new"][0][0][1] == "ISSUE")
    nk = n["new"][0][0] if n["new"] else None
    check("1: _voucher_seq of every pre-existing batch unchanged; the new batch is STOCK ISSUE voucher %s (30 expected)" % ((n["seq"].get(nk) or (None,))[0] if nk else None),
          all(n["seq"].get(k) == v for k, v in u["seq"].items()) and nk and n["seq"].get(nk) == (30, "ISSUE"))
    check("1: C['held'] empty (%s); NORTIMER absent from Needs-you" % n["held"], n["held"] == [] and not any(NORT in t for t in n["owner"]),
          [t for t in n["owner"] if "Count #" in t])
    check("1: the new batch is on the owner's board, not yet on Amir's (it waits for a coming lot of 12)", nk in n["board"]["manoj"] and nk not in n["board"]["amir"])
    rc2, out2 = run(A)
    check("1: a second run -> ALREADY DONE, no row written", rc2 == 0 and "ALREADY DONE" in out2 and counts(A) == c1, [l for l in out2.splitlines() if "ALREADY" in l or "STOP" in l])

    # ---- 2. --dry
    D = os.path.join(W, "dry.db")
    copydb(a.db, D)
    d0 = counts(D)
    print("-- 2 --dry")
    rcd, outd = run(D, "--dry")
    show(outd)
    check("2: --dry exits 0 and writes nothing (void, settle, line, entered counts %s)" % d0, rcd == 0 and "DATA_S539: DRY -- rolled back" in outd and counts(D) == d0,
          counts(D))
    check("2: --dry's own scratch copy shows the outcome (voucher 11 no batch, the five re-made as STOCK ISSUE voucher 30)",
          "voucher 11 a batch: False" in outd and "STOCK ISSUE voucher 30" in outd)

    # ---- 3. an entry on voucher 11
    E = os.path.join(W, "entered.db")
    copydb(a.db, E)
    ce = sqlite3.connect(E)
    ce.execute("INSERT INTO stock_voucher_entered (count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at) VALUES (1,2,'ISSUE',10,'W539-11','2026-10-12','amir','2026-10-12T09:00:00')")
    ce.commit()
    ce.close()
    e0 = counts(E)
    print("-- 3 voucher 11 carrying an entry")
    rce, oute = run(E)
    check("3: STOP, exit 2, nothing written", rce == 2 and "DATA_S539: STOP" in oute and counts(E) == e0, [l for l in oute.splitlines() if "STOP" in l])
    if FAILS:
        print("WALK_S539 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:260])
        return 1
    print("WALK_S539 GREEN (%d checks)" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
