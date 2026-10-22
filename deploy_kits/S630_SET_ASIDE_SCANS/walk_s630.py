#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s630.py -- kit S630_SET_ASIDE_SCANS (22-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s630.py --fin <scratch /root/finance with the files under test> --db <COPY of finance.db> --adb <COPY of assets.db>
                            --shared <scratch /root/shared> --por <scratch /root/portal> --marg <scratch marg_ingest> [--expect-red]
The real finance app in one process (header sessions on a walk-only portal store). Its own row by key: a pharmacy scan stamped 'W630-1'
(a second, NOT set-aside copy of a paper whose other copy IS set aside). --expect-red: the same walk on the OLD files (S629's), every 'C:'
check red. Prints 'WALK OK S630 ...'. No phone number is printed."""
import argparse
import json
import os
import re
import secrets
import sqlite3
import sys

BASE = "https://followup.dr-manoj.in"
P = "/finance/porders"
ROLE = {"manoj": "doctor", "darpan": "staff", "reception": "staff", "alisha": "staff", "shivani": "staff", "bhati": "staff", "shavez": "manager", "amir": "staff"}
RUN, FAILS, CTRL = [0], [], []


def say(s):
    print(re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s)), flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:500] + "]") if (got is not None and not cond) else ""))
    if label.startswith("C:"):
        CTRL.append((label, bool(cond)))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def portal_setup(por):
    assert por.startswith("/tmp/")
    secret = secrets.token_hex(32)
    with open(os.path.join(por, "portal_config.py"), "w") as fh:
        fh.write("# W630 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w630-walk'\n" % secret)
    sys.path.insert(0, por)
    import clinic_users                                        # noqa: E402
    store = os.path.join(por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    for u, role in ROLE.items():
        try:
            clinic_users.add_role(store, role)
        except ValueError:
            pass
        clinic_users.add_user(store, u, role, secrets.token_urlsafe(12))
    sys.path.remove(por)
    sys.modules.pop("clinic_users", None)
    return secret, store


def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--shared", "--por", "--marg"):
        ap.add_argument(k, required=True)
    ap.add_argument("--expect-red", action="store_true")
    a = ap.parse_args()
    fin, dbp, adb, por, shared, marg = (os.path.abspath(getattr(a, k)) for k in ("fin", "db", "adb", "por", "shared", "marg"))
    for p in (fin, dbp, adb, por, shared, marg):
        assert p.startswith("/tmp/"), "scratch copies in /tmp only: %s" % p
    say("-- S630 walk on the %s: %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin))
    # the walk's own scan: a second copy (W630-1) of the paper whose fuller copy the scan app set aside
    ac = sqlite3.connect(adb)
    ac.row_factory = sqlite3.Row
    aside = ac.execute("SELECT b.id, b.vendor, b.bill_no, b.total_amount, b.created_at FROM bills b WHERE b.lane='pharmacy' AND b.status='rejected' AND b.dup_of IS NOT NULL "
                       "AND substr(b.created_at,1,10)>='2026-10-12' AND EXISTS (SELECT 1 FROM claude_reading r WHERE r.bill_id=b.id AND r.ok=1) ORDER BY b.id").fetchall()
    target = None
    for r in aside:
        rd = ac.execute("SELECT data FROM claude_reading WHERE bill_id=? AND ok=1 ORDER BY at DESC LIMIT 1", (r["id"],)).fetchone()
        d = json.loads(rd[0]) if rd and rd[0] else {}
        if d.get("bill_no") and d.get("total_amount") not in (None, ""):
            target = (r, d)
            break
    if target is None:
        say("   no set-aside scan with a reading on this copy -- the same-paper control cannot be laid")
    else:
        r, d = target
        cols = {x[1] for x in ac.execute("PRAGMA table_info(bills)")}
        row = dict(kind="Pharmacy", vendor=r["vendor"], bill_no=r["bill_no"], total_amount=r["total_amount"], status="captured", lane="pharmacy",
                   created_at=str(r["created_at"]), stamp_no="W630-1", created_by="W630 walk")
        row = {k: v for k, v in row.items() if k in cols}
        cur = ac.execute("INSERT INTO bills (%s) VALUES (%s)" % (", ".join(row), ",".join("?" * len(row))), list(row.values()))
        wid = cur.lastrowid
        rc = {x[1] for x in ac.execute("PRAGMA table_info(claude_reading)")}
        rr = {k: v for k, v in dict(bill_id=wid, at="2026-10-14 10:00:00", model="w630", ok=1, doc_kind="bill", data=json.dumps(d)).items() if k in rc}
        ac.execute("INSERT INTO claude_reading (%s) VALUES (%s)" % (", ".join(rr), ",".join("?" * len(rr))), list(rr.values()))
        ac.commit()
        say("   laid: scan #%d 'W630-1', a second copy of set-aside scan #%d (bill %s)" % (wid, r["id"], d.get("bill_no")))
    rejected = {int(x[0]) for x in ac.execute("SELECT id FROM bills WHERE status='rejected' OR dup_of IS NOT NULL")}
    ac.close()

    secret, store = portal_setup(por)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=adb, SHARED_LIB_DIR=shared, CLINIC_PORTAL_DIR=por, FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=marg,
                      ORDER_PUSH_NONE="1", FINANCE_SSO_DIR=por, RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="",
                      FINANCE_DEV_ROLE="", PYTHONDONTWRITEBYTECODE="1", CLINIC_SSO_SECRET=secret, CLINIC_USERS_FILE=store,
                      TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"), SPINE_DB=os.path.join(fin, "spine", "spine.db"))
    os.makedirs(os.environ["RING_PORTAL_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SARVAM_API_KEY", "PORDERS_SOURCE"):
        os.environ.pop(k, None)
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != here]
    sys.path.insert(0, fin)
    sys.path.insert(1, shared)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import order_track as OT                                  # noqa: E402
    assert fa.__file__.startswith(fin) and OT.__file__.startswith(fin)
    say("   the real finance app from the scratch folder; parts that did not load: %s; order_track %s %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none", OT.VERSION, OT.KIT))
    cl = fa.app.test_client(use_cookies=False)

    def GET(u, path):
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def POST(u, path, body):
        r = cl.post(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, json=body)
        try:
            return r.status_code, json.loads(r.get_data().decode("utf-8", "replace"))
        except ValueError:
            return r.status_code, {}

    st, h = GET("manoj", P + "/s454/track")
    check("the owner's track page 200", st == 200, st)
    offered = sorted({int(x) for x in re.findall(r'data-sbscan="(\d+)"', h)})
    bad = [x for x in offered if x in rejected]
    say("   Send back offered on %d scans; set aside among them: %s" % (len(offered), bad))
    check("C: no set-aside scan is offered Send back", not bad, bad)
    pairs = re.findall(r'data-same="(\d+)-(\d+)"', h)
    badp = [p for p in pairs if int(p[0]) in rejected or int(p[1]) in rejected]
    if target is not None:
        check("C: no set-aside scan is named in 'The same paper scanned twice'", not badp, badp)
    else:
        check("no set-aside scan is named in 'The same paper scanned twice'", not badp, badp)
    check("B-0150 and B-0154 (neither set aside) are still named as one paper", 'data-same="150-154"' in h or "data-same=" not in h, pairs)
    st2, h2 = GET("shavez", P + "/s454/track")
    off2 = {int(x) for x in re.findall(r'data-sbscan="(\d+)"', h2)}
    check("C: Shavez's page offers Send back on no set-aside scan either", st2 == 200 and not (off2 & rejected), sorted(off2 & rejected))
    refused = []
    for sid in offered:
        if 'data-sbscan="%d"' % sid in h and re.search(r'data-sbscan="%d"[^<]*>[^<]*<span class="am">sent back' % sid, h):
            continue                                          # already asked: Withdraw shown, not the chips
        c, j = POST("manoj", P + "/api/s454/rescan", {"asset_bill_id": sid, "reason": "blurred"})
        if c != 200:
            refused.append((sid, c, j.get("error")))
    check("C: every Send back the page offers is accepted by the server (%d tried)" % len(offered), offered and not refused, refused)
    for u, pth in (("alisha", P), ("alisha", P + "/s454/order"), ("darpan", "/finance/darpan/kal"), ("manoj", P + "/s454/scans")):
        c, _h = GET(u, pth)
        check("%s as %s renders (%s)" % (pth, u, c), c in (200, 302), c)

    c_red = [l for l, ok in CTRL if not ok]
    if a.expect_red:
        green = [l for l, ok in CTRL if ok]
        say("NEGATIVE CONTROL: %d 'C:' checks, %d red, %d green%s" % (len(CTRL), len(c_red), len(green), (": " + "; ".join(green)) if green else ""))
        if green:
            say("WALK NEGATIVE CONTROL NOT RED S630 -- a C: check passed on the OLD files")
            sys.exit(1)
        say("WALK NEGATIVE CONTROL RED S630 (every C: check red on the OLD files)")
        return
    if FAILS:
        say("WALK FAILED S630 -- %d of %d checks: %s" % (len(FAILS), RUN[0], "; ".join(FAILS)))
        sys.exit(1)
    say("WALK OK S630 -- %d checks green, %d of them controls" % (RUN[0], len(CTRL)))


if __name__ == "__main__":
    main()
