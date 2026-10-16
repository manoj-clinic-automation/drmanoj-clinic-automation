#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_s570.py -- kit S570_PROOF_MORNING_WINDOW: the owner's proof as the box serves it, read on backup-API copies (never the live files).

    python3 -B state_s570.py --finance /root/finance --work /tmp/...

Copies finance.db and spine/spine.db by the backup API into --work, then (a child process) imports the finance app from --finance with
FINANCE_DB / SPINE_DB on the copies and reads /finance/stock/api/pad/hub/1's `proof` by the app's test client as the owner (header auth on
the copy only): state, stage, text, each waiting lot's why / closing_day / closing_at, the verdict rows (item, need, Marg moved), the
owner's lines, Amir's card words. Also: the reach, and any PURCHASE_* file received on 16-10 after 11:00 IST (mi_file). Prints
'STATE_S570 OK' at the end. No person, phone or account number is printed (runs of ten digits are masked)."""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys

TAG = "S570STATE "


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


def child():
    fin = os.environ["S570_FIN"]
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                    # noqa: E402
    import stock_watch as SW                                    # noqa: E402
    SW.SPINE_DB = os.environ["SPINE_DB"]
    import stock_app as SA                                      # noqa: E402
    assert fa.DB_PATH.startswith("/tmp/"), "a scratch copy only"
    out = {}
    sp = SA._s524_spine()
    out["reach"] = SA._s524_reach(sp) if sp is not None else None
    con = sqlite3.connect(fa.DB_PATH, timeout=60)
    out["purchase_files_today"] = [dict(family=r[0], date_from=r[1], date_to=r[2], received_at=r[3], status=r[4]) for r in con.execute(   # mi_file.type = the family
        "SELECT type, date_from, date_to, received_at, verdict FROM mi_file WHERE type LIKE 'PURCHASE%' AND received_at >= '2026-10-16T11:00' ORDER BY received_at")]
    fc = fa.app.test_client(use_cookies=False)
    r = fc.get("/finance/stock/api/pad/hub/1", headers={"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"})
    pr = (r.get_json(silent=True) or {}).get("proof") or {}
    C = pr.get("C") or {}
    out["hub"] = dict(code=r.status_code, state=pr.get("state"), stage=pr.get("stage"), text=pr.get("text"), lines=pr.get("lines"),
                      waiting=[dict(at=w.get("at"), n=len(w.get("keys") or []), **{k: (w.get("proof") or {}).get(k) for k in
                               ("state", "why", "closing_day", "closing_at", "since")}) for w in C.get("waiting_export") or []],
                      wrong=[{k: x.get(k) for k in ("item", "need_key", "need_hi", "moved", "moved_hi", "marg_hi", "closing_day", "keys")} for x in (C.get("wrong") or [])],
                      counts={k: C.get(k) for k in ("total", "entered", "released", "lots", "verified")})
    st = SA.amir_stage(con)
    out["card_hi"] = (SA._s521_stage_words(con, st) or {}).get("card_hi") if st else None
    print(TAG + json.dumps(out, default=str))
    return 0


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        return child()
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--work", required=True)
    a = ap.parse_args()
    w = os.path.abspath(a.work)
    assert w.startswith("/tmp/"), "scratch only"
    os.makedirs(os.path.join(w, "nosso"), exist_ok=True)
    os.makedirs(os.path.join(w, "noring"), exist_ok=True)
    db, sp = os.path.join(w, "finance.db"), os.path.join(w, "spine.db")
    copydb(os.path.join(a.finance, "finance.db"), db)
    copydb(os.path.join(a.finance, "spine", "spine.db"), sp)
    env = dict(os.environ, S570_FIN=os.path.abspath(a.finance), FINANCE_DB=db, SPINE_DB=sp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=os.path.join(w, "nosso"),
               ORDER_PUSH_STUB=os.path.join(w, "pushes.jsonl"), RING_PORTAL_DIR=os.path.join(w, "noring"), REPORTS_NTFY_STUB=os.path.join(w, "ntfy.jsonl"))
    for k in ("SARVAM_API_KEY", "ORDER_PUSH_NONE", "ORDER_TODAY", "ORDER_TICK", "ORDER_CLOCK"):
        env.pop(k, None)
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child"], env=env, cwd=os.path.abspath(a.finance), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, universal_newlines=True, timeout=1500)
    js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
    for f in (db, sp):
        os.remove(f)
    if not js:
        print("the read did not finish (exit %s):" % p.returncode)
        for l in p.stdout.splitlines()[-12:]:
            print("  " + mask(l[:300]))
        return 1
    o = json.loads(js[-1][len(TAG):])
    h = o["hub"]
    L = []
    L.append("reach: sale to %s @ %s · purchase to %s @ %s" % (o["reach"]["last_sale"], o["reach"]["sale_stamp"], o["reach"]["last_pur"], o["reach"]["pur_stamp"]) if o["reach"] else "reach: the spine is not readable")
    L.append("purchase files received 16-10 after 11:00 IST: %s" % ("; ".join("%s %s..%s at %s (%s)" % (x["family"], x["date_from"], x["date_to"], x["received_at"], x["status"])
                                                                        for x in o["purchase_files_today"]) or "none"))
    L.append("proof: hub %s · state %s · stage %s · %s" % (h["code"], h["state"], h["stage"], h["counts"]))
    L.append("text: %s" % h["text"])
    for x in h["waiting"]:
        L.append("  lot released %s (%d vouchers): %s · why %s · closing_day %s · closing_at %s · since %s" % (str(x["at"])[:16], x["n"], x["state"], x["why"], x["closing_day"], x["closing_at"], x["since"]))
    for r in h["wrong"]:
        L.append("  WRONG: %s · voucher(s) %s · need %s (%s) · Marg moved %s (%s) · Marg at %s %s" % (r["item"], ",".join(r.get("keys") or []), r.get("need_key"), r.get("need_hi"),
                                                                                         r.get("moved"), r.get("moved_hi"), r.get("closing_day"), r.get("marg_hi")))
    for l in h["lines"] or []:
        L.append("  owner line: %s" % (l.get("text") if isinstance(l, dict) else l))
    L.append("Amir's card: %s" % o.get("card_hi"))
    print(mask("\n".join(L)))
    print("STATE_S570 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
