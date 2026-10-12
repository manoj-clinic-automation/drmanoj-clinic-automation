#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_s533.py -- kit S533_AMIR_DAY_PAGE: the install-day state (charter 7) before and after placing, the read-back of the live pages
through a walk-only portal session after the restart, and the retired-name grep.

    python3 -B state_s533.py --mode state    --finance /root/finance --db <a backup-API COPY of finance.db>
    python3 -B state_s533.py --mode readback --finance /root/finance --por <scratch portal copy>     (FINANCE_SSO_DIR=<por> set by the caller)
    python3 -B state_s533.py --mode grep     --dirs /root/finance /root/portal

  state     on a scratch COPY only (amir_stage writes once-only stage events; scans_for_amir re-matches on read): the stage, the two rename rows
            by old_name, the bills by state, the scans (the Yuvika scan's three places: the card's count, step 2's list, not step 5), the exact
            card Amir will see, the owner's state line and Needs-you lines.  The OLD file (before placing): its card and its owner's line.
  readback  the live pages after the restart, signed in through the kit's own portal secret and user store (never the live ones): the owner's
            day page, the visit summary, Needs-you; Amir's step 1, step 6 and step 7 (his GETs run the page's own settle -- the same writes his
            first open of the day makes).
  grep      the retired names and the two history tables over the given folders, word-bounded, .bak files and the kit's own three comment
            lines aside.  Exit 1 when any hit remains.
No person, phone or account number is printed (numbers of ten digits or more are masked)."""
import argparse
import html as _html
import io
import json
import os
import re
import secrets
import sqlite3
import sys

RETIRED = ("_salt_list_state", "_salt_prompt_amir", "_salt_owner_line", "_applied_line", "SALTS_STATE", "_STAMP_IN_NAME", "_s444_card", "_s444_left",
           "_s444_summary_rows", "_s444_open", "_s444_voucher_line", "_s444_duties", "_s444_state", "_s444_rs", "_s444_ddmm", "_s444_days_since",
           "_s444_login", "_s444_who_line", "_packs_card_s408", "_s446_bills_list", "_s446_summary_rows", "_s446_left", "_s446_voucher_line",
           "_s446_owner_lines", "_s452_extra_hi", "_s452_left_hi", "_s454_entry_mode", "_left", "_work", "_s446_state", "_s446_watch", "_s452_state",
           "_s494_spine", "S488_TAIL_HI", "_s488_tail_hi", "_s488_wait_html", "_s488_proof", "S494_JOBS", "s494_seed_jobs", "MARK_KIT",
           "S243_AMIR_VISIT", "S246_AMIR_LIST_REOPEN", "_s444_renames", "amir_duties", "_S444_RENAMES_CACHE", "scans_to_enter", "AMIR_BILLS_FROM",
           "amir_step", "amir_bill_disposition")
KIT_LINES = ("(S533: _s444_renames retired with amir_day's rebuild).", "(S533: its second reader _s444_renames is gone).",
             "(S533: scans_to_enter retired -- step 2 reads scans_for_amir)")
OLDS = ("L S BELT CONT GRAY UNISON XXX", "TYNOR WRIST SPLINT LF M ELAS")


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def vis(h):
    h = re.sub(r"(?is)<(style|script|title)[^>]*>.*?</\1>", " ", h or "")
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", _html.unescape(h)).strip()


def grep(dirs):
    hits = []
    for d in dirs:
        for root, _ds, files in os.walk(d):
            if "/pad_uploads" in root or "/__pycache__" in root:
                continue
            for fn in files:
                if not fn.endswith((".py", ".html")) or ".bak_" in fn:
                    continue
                p = os.path.join(root, fn)
                try:
                    t = io.open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                for n, line in enumerate(t.splitlines(), 1):
                    if any(k in line for k in KIT_LINES):
                        continue
                    for nm in RETIRED:
                        if re.search(r"(?<![A-Za-z0-9_])" + re.escape(nm) + r"(?![A-Za-z0-9_])", line):
                            hits.append("%s:%d %s" % (p, n, nm))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True)
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--db", default="")
    ap.add_argument("--por", default="")
    ap.add_argument("--dirs", nargs="*", default=[])
    a = ap.parse_args()
    if a.mode == "grep":
        h = grep(a.dirs)
        for x in h[:20]:
            print("GREP HIT %s" % x)
        print("GREP %s (%d hit%s over %s)" % ("CLEAN" if not h else "RED", len(h), "" if len(h) == 1 else "s", ", ".join(a.dirs)))
        return 0 if not h else 1
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
            fh.write("# S533 read-back only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
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
    NEW = hasattr(AD, "DUTY_SQL")
    if a.mode == "state":
        con = sqlite3.connect(a.db, timeout=60)
        con.row_factory = sqlite3.Row
        root = SA._s446_root(con)
        st = SA.amir_stage(con, root)
        A = (st or {}).get("A") or {}
        pr = A.get("proof") or {}
        print("STATE: count #%s stage %s; A entered %s of %s, open %s, pending %s; proof %s%s; B %s" % (
            root, (st or {}).get("stage"), A.get("entered"), A.get("total"), A.get("open"), A.get("pending"), pr.get("state"),
            (" why " + str(pr.get("why"))) if pr.get("why") else "", {k: v for k, v in ((st or {}).get("B") or {}).items() if k in ("total", "verified", "ticked", "questions")}))
        for r in con.execute("SELECT old_name, new_name, done_at, verified_at, verified_as_on FROM marg_item_rename WHERE old_name IN (?,?) ORDER BY id", OLDS).fetchall():
            print("   rename %-31s -> %-31s %s" % (r[0], r[1], ("verified (closing %s)" % r[4]) if r[3] else ("ticked %s, not yet seen" % (r[2] or "-")[:16])))
        today = AD._today()
        if NEW:
            AD.ensure(con)
            S = AD.state(con, today, "amir", step=5)
            b = S.bills
            print("   bills: today %d (Aaj aaye bill) · carried %d (Pichhle dinon ke baaki) · flagged %d · his corrections waiting %d"
                  % (len(b["today"]), len(b["carry"]), len(b["flagged"]), len(b["waiting"])))
            ys = [x for x in S.scans if "YUVIKA" in str(x.get("supplier") or "")]
            yb = [x for x in b["today"] + b["carry"] + b["flagged"] + b["waiting"] if "YUVIKA" in str(x.get("supplier_norm") or "")]
            print("   scans not yet in Marg's export: %d listed, %d held for reception -> the card's line 'Scan hua bill Marg mein baaki: %d'" % (len(S.scans), len(S.held), len(S.scans)))
            print("   the Yuvika scan: on the card's count %s; on step 2's list %s (%s); on step 5 %s" % (
                bool(ys), bool(ys), ", ".join("%s scan %s bill %s" % (x.get("supplier"), x.get("scan_ddmm"), x.get("bill_date") or "-") for x in ys) or "-", bool(yb)))
            print("   AMIR'S CARD: %s" % (" | ".join(vis(r[1]) for r in S.card) or "(empty)"))
            head, second = AD.owner_state_line(S)
            print("   OWNER'S DAY: %s%s" % (head, (" / " + second) if second else ""))
            print("   AMIR'S STEP 7 (holding): %s" % ("; ".join(g[1] for g in S.gate_open) or "nothing -- ready to close"))
            print("   AMIR'S STEP 7 (not holding): %s" % ("; ".join(x[0] for x in S.extra) or "-"))
            arr = AD._d712_owner_lines(con, S)
            print("   D712 owner line(s) now (an arrival older than the grace with no scan): %d" % len(arr))
            for l in AD.needs_you_lines(con):
                print("   NEEDS-YOU: %s" % mask(l.get("text"))[:300])
        else:
            w = AD._work(con, today)
            card = AD._s446_card(w, top=True)
            print("   OLD CARD (Amir): %s" % (vis(card) or "(empty)"))
            print("   OLD bills: today %d · carried %d · flagged %d" % (len(w["today_bills"]), len(w["carry_bills"]), len(w["flagged_bills"])))
            print("   OLD OWNER'S DAY: %s" % ("; ".join(AD._left(w)) or "ready to close"))
        con.close()
        print("STATE OK")
        return 0
    # ---- readback: the live pages through the kit's own portal session
    import portal as po                                         # noqa: E402
    base = "https://followup.dr-manoj.in"
    pc, fc = po.app.test_client(use_cookies=False), fa.app.test_client(use_cookies=False)
    ck = {}
    for who in ("amir", "manoj"):
        r = pc.post("/portal/login", base_url=base, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        ck[who] = {"Cookie": "clinic_sso=" + (m.group(1) if m else "")}
    ok = True
    r = fc.get("/finance/amir/day", base_url=base, headers=ck["manoj"])
    h = r.get_data(as_text=True)
    m = re.search(r"id=daystate>(.*?)</p>", h, flags=re.S)
    m2 = re.search(r"id=daynothold>(.*?)</p>", h, flags=re.S)
    print("owner /finance/amir/day: %s -- %s%s" % (r.status_code, _html.unescape(m.group(1)) if m else "?", (" / " + _html.unescape(m2.group(1))) if m2 else ""))
    ok = ok and r.status_code == 200 and m is not None
    r = fc.get("/finance/amir/day/api/visit-summary", base_url=base, headers=ck["manoj"])
    j = r.get_json(silent=True) or {}
    print("owner visit summary: %s kit %s state %s; steps %s" % (r.status_code, j.get("kit"), j.get("state"), [(s.get("n"), s.get("state")) for s in j.get("steps") or []]))
    ok = ok and r.status_code == 200 and j.get("kit") == "S533_AMIR_DAY_PAGE"
    r = fc.get("/finance/sanjeevni/api/needs-you", base_url=base, headers=ck["manoj"])
    j = r.get_json(silent=True) or {}
    lines = [l for l in j.get("lines") or [] if isinstance(l, dict)]
    print("owner Needs-you: %s, %d lines; Amir's: %s" % (r.status_code, len(lines), mask([l.get("text") for l in lines if re.search(r"Amir|Count #|Goods tapped|Salt list", str(l.get("text")))][:8])))
    ok = ok and r.status_code == 200
    for n in (1, 6, 7):
        r = fc.get("/finance/amir/step/%d" % n, base_url=base, headers=ck["amir"])
        t = vis(r.get_data(as_text=True))
        keep = re.findall(r"(Orthotic[^·|]{0,60}|Naam bad[^·|]{0,40}|Scan hua bill Marg mein baaki: \d+|Aaj aaye bill: \d+ · Pichhle dinon ke baaki: \d+ · Flag kiye hue: \d+|"
                          r"Abhi kuch baaki hai|Din band karein\?|DIN BAND|Ek export aur: SALT WISE ITEM LIST|Aaj Marg mein sudhaar ka kuch nahi hai)", t)
        print("amir step %d: %s, %d bytes; %s" % (n, r.status_code, len(r.get_data()), mask(keep[:8])))
        ok = ok and r.status_code == 200
    print("READ_BACK OK" if ok else "READ_BACK RED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
