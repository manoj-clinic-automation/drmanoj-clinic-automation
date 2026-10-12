#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_s537.py -- kit S537_VOUCHER_GUARD: the install-day state (charter 7) before and after placing, and the read-back of the live board
and Needs-you through a walk-only portal session after the restart.

    python3 -B state_s537.py --mode state    --finance /root/finance --db <a backup-API COPY of finance.db>
    python3 -B state_s537.py --mode readback --finance /root/finance --por <scratch portal copy>

  state     on a scratch COPY only (amir_stage writes once-only stage events): count #1's stage by key, A, B, C (held), whether voucher 29
            (round 6) is a batch, Amir's board's vouchers as amir (their numbers), the owner's Needs-you lines naming the count, a held line,
            the closing not readable, YUVIKA; the spot-count list's head (stock_watch_ask, open). Run by the files in --finance as they stand.
  readback  the live board API as amir and as the owner and the owner's Needs-you, signed in through the kit's own portal secret and user
            store (never the live ones).  Like any owner read, it lets amir_stage write its once-only stage events.
No person, phone or account number is printed (numbers of ten digits or more are masked)."""
import argparse
import os
import re
import secrets
import sqlite3
import sys

WANT = r"Count #|not given to Amir|not readable|YUVIKA|Goods tapped|ordering"


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True)
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--db", default="")
    ap.add_argument("--por", default="")
    a = ap.parse_args()
    sys.path.insert(0, a.finance)
    os.chdir(a.finance)
    if a.mode == "state":
        assert a.db and os.path.abspath(a.db) != os.path.abspath(os.path.join(a.finance, "finance.db")), "state reads a COPY, never the live database"
        os.environ["FINANCE_DB"] = a.db
    else:                                                       # the read-back's own secret and user store, laid BEFORE any app is imported
        assert a.por.startswith("/tmp/"), "the read-back's portal copy must be a scratch folder"
        secret = secrets.token_hex(32)
        pw = {u: secrets.token_urlsafe(12) for u in ("amir", "manoj")}
        with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
            fh.write("# S537 read-back only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
        store = os.path.join(a.por, "clinic_users.json")
        os.environ.update(CLINIC_SSO_SECRET=secret, CLINIC_PORTAL_DIR=a.por, FINANCE_SSO_DIR=a.por, CLINIC_USERS_FILE=store,
                          TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"))
        sys.path.insert(0, a.por)
        import clinic_users                                     # noqa: E402
        if os.path.exists(store):
            os.remove(store)
        for role in ("staff", "doctor"):
            try:
                clinic_users.add_role(store, role)
            except ValueError:
                pass
        clinic_users.add_user(store, "amir", "staff", pw["amir"])
        clinic_users.add_user(store, "manoj", "doctor", pw["manoj"])
    import finance_app as fa                                    # noqa: E402,F401 -- the app, so the modules are this folder's
    import amir_day as AD                                       # noqa: E402
    import stock_app as SA                                      # noqa: E402
    if a.mode == "state":
        con = sqlite3.connect(a.db, timeout=60)
        con.row_factory = sqlite3.Row
        root = SA._s446_root(con)
        st = SA.amir_stage(con, root) or {}
        A, B, Cc = st.get("A") or {}, st.get("B") or {}, st.get("C") or {}
        b = SA._s446_batches(con, root)
        print("STATE: count #%s stage %s; A entered %s of %s, open %s, pending %s, held %s, proof %s; B renames %s of %s verified (B verified at %s); "
              "round 6 a batch: %s%s" % (root, st.get("stage"), A.get("entered"), A.get("total"), A.get("open"), A.get("pending"), len(A.get("held") or []) if "held" in A else "-",
                                          (A.get("proof") or {}).get("state"), B.get("verified"), B.get("total"), B.get("verified_at"), any(k[0] == 6 for k in b),
                                          ("; C released %s of %s, today %d, held %s" % (Cc.get("released"), Cc.get("total"), len(Cc.get("today") or []),
                                                                                       [(h.get("item"), h.get("seq")) for h in Cc.get("held") or []])) if Cc else ""))
        try:
            v = con.execute("SELECT COUNT(*) FROM stock_voucher_void").fetchone()[0]
            s = con.execute("SELECT COUNT(*) FROM stock_voucher_settle").fetchone()[0]
            print("   void rows %s, settle rows %s" % (v, s))
        except sqlite3.Error:
            print("   no void / settle table (the old files)")
        roles = [r[0] for r in con.execute("SELECT role FROM unit_role WHERE unit='medical' AND username='amir' AND active=1").fetchall()]
        board = SA._amir_board_light(con, root, dict(user="amir", role="staff", roles=sorted(roles)), st)
        print("   AMIR'S BOARD as amir: %d voucher(s): %s" % (len(board.get("vouchers") or []), ", ".join(v_["title_hi"] + (" (entered)" if v_.get("entered") else "")
                                                                                              for v_ in board.get("vouchers") or [])[:600]))
        print("   AMIR'S BOARD stage line: %s" % mask((board.get("proof") or {}).get("hi"))[:200])
        for l in AD.needs_you_lines(con):
            t = l.get("text") or ""
            if re.search(WANT, t):
                print("   NEEDS-YOU: %s" % mask(t)[:300])
        try:
            ask = [r[0] for r in con.execute("SELECT item FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id").fetchall()]
            print("   SPOT-COUNT asks open (the head of Darpan's next list): %s" % (ask[:6] or "none"))
        except sqlite3.Error:
            pass
        con.close()
        print("STATE OK")
        return 0
    # ---- readback: the live board API and Needs-you through the kit's own portal session
    import portal as po                                         # noqa: E402
    base = "https://followup.dr-manoj.in"
    pc, fc = po.app.test_client(use_cookies=False), fa.app.test_client(use_cookies=False)
    ck = {}
    for who in ("amir", "manoj"):
        r = pc.post("/portal/login", base_url=base, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        ck[who] = {"Cookie": "clinic_sso=" + (m.group(1) if m else "")}
    ok = True
    con = sqlite3.connect("file:%s?mode=ro" % os.environ.get("FINANCE_DB", os.path.join(a.finance, "finance.db")), uri=True)
    root = SA._s446_root(con)
    con.close()
    for who in ("amir", "manoj"):
        r = fc.get("/finance/stock/api/pad/amir/%d" % root, base_url=base, headers=ck[who])
        j = r.get_json(silent=True) or {}
        vs = j.get("vouchers") or []
        r6 = [v for v in vs if int(v.get("round_no") or 0) == 6]
        print("board as %s: %s, %d bytes; stage %s; %d voucher(s); round 6 shown: %s" % (who, r.status_code, len(r.get_data()), (j.get("stage") or {}).get("stage"),
                                                                                 len(vs), bool(r6)))
        ok = ok and r.status_code == 200 and not r6
    r = fc.get("/finance/sanjeevni/api/needs-you", base_url=base, headers=ck["manoj"])
    j = r.get_json(silent=True) or {}
    lines = [l for l in j.get("lines") or [] if isinstance(l, dict)]
    print("owner Needs-you: %s, %d lines" % (r.status_code, len(lines)))
    for l in lines:
        if re.search(WANT, str(l.get("text"))):
            print("   NEEDS-YOU: %s" % mask(l.get("text"))[:300])
    ok = ok and r.status_code == 200
    print("READ_BACK OK" if ok else "READ_BACK RED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
