#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s574.py -- kit S574_PHONEBOOK_ONE_RECORD (18-Oct-2026). Runs on a SCRATCH folder and SCRATCH databases only.
    python3 -B walk_s574.py --fin <scratch copy of /root/finance with the files under test> --old <a folder with the five OLD files>
                            --db <a COPY of finance.db> --adb <a COPY of assets.db> --marg <scratch marg_ingest> --portal <scratch portal *.py
                            + tile_grants.json, no portal_config> --map <DUTY_MAP.json> --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s574.py --page [--after] --fin ... --db ... --adb ... --marg ... --map ...     (the owner's state before / after placing)
The real finance app in one process (the walk's own header session, a walk-only Marg token -- never the live secret or token); the OLD
purchase_app.py and order_sheet.py loaded beside it from --old for the "as before" answers. Its own rows by key (W574 ..., made-up numbers
built at run time, never written as ten digits); the live pairs by alias key. No number is printed (last 4 at most).
  0  the live state: the pending pairs by alias key (names, slot counts, last 4), RAVI MEDICAL AGENCY, the singles, the switch
  1  OFF = as before: every reader for every name (39 rows' names and norms, the alias names) equals the old file's; the pages 200; the
     doctor's book page byte for byte the old one plus the one line; the staff order pages byte for byte; a number 3 saved while ON is
     nowhere after OFF
  2  ON before the merge: the same, except RAVI MEDICAL AGENCY (its bank record's number)
  3  merge all: the page lists the dealers left, Gunina's name, Kedar by both names, every reader as in 2 (KEDAR PHARMA named), the bank
     readers identical, no row deleted, the premerge rows
  4  picks: Kedar's payment number, the order number unchanged, every _digits non-empty
  5  Marg's push: an existing number, a new number for a merged dealer, a full dealer (the owner's line), a new dealer; OFF as before
  6  the doors: darpan / shavez refused, shavez bank as before, the doctor allowed
  7  undo: back to 2's numbers; refused after a number edit; a save by the record's key lands on the record
  8  staff-eye (CLAUDE.md, S444): portal homes, the order page, no control in their book page
  9  staff words: the no-number sentence, Call / WhatsApp lines, no system words, under 100 KB
 10  dead code: no caller of order_sheet._phones or purchase_app._phones_for
 11  no run of ten digits in the walk's own output
--expect-red: the same walk on the OLD files; every 'C:' check must be red (the negative control).
Prints 'WALK OK S574 ...' on success; exit 1 on any failure."""
import argparse
import datetime as dt
import html as _html
import importlib.util
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time

KIT = "S574_PHONEBOOK_ONE_RECORD"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "darpan": "staff", "shavez": "manager", "reception": "staff"}
STAFF = ("darpan", "shavez", "reception")
BOOK, API, PUSH = "/finance/purchase/page/book", "/finance/purchase/api/book", "/finance/purchase/api/vendors"
ORDER = "/finance/porders/s454/order"
PAIRS = ("DRUG DEAL", "ESS KAY AGENCIES EXTN", "GUNINA PHARMACEUTICALS PVT LTD", "JUBILEE AGENCIES", "KEDAR PHARMACEUTICAL", "L.K. DRUG HOUSE",
         "RADHA MEDICAL & SCIENTIFIC", "SAISUN PHARMA PVT. LTD", "SCIENTIFIC&MEDICAL AID CENTRE", "SHRADDHA MEDICOSE", "VERMA BROS. AND CO",
         "YOGENDRA AGENCIES", "YUVIKA SURGICALS")       # the brief's 13 pending pairs, by alias key (bill_norm)
RAVI, KEDAR_M, KEDAR_R = "RAVI MEDICAL AGENCY", "KEDAR PHARMACEUTICAL", "KEDAR PHARMA"
NONUM = "Number nahi hai — Dr sahab ko dijiye"
OLDNO = "phone number yahan nahi hai"
REFUSE = "Numbers are changed only by Dr Manoj."
CLOSED = "Undo is closed: numbers were changed after the merge."
SYSWORDS = ("point", "trace", "round", "gap", "base", "row", "id", "sync")
CONTROLS = (r"bookForm\(\d+,'phones'\)", r'id="addform"', r"s574Picks\(", r"s574Merge\(", r"s574Switch\(", r"s574Edit\(", r"s574Undo\(", r'id="pk-call-')
RUN, FAILS, CTRL, OUT = [0], [], [], []


def mk(n):
    """A made-up mobile number, built at run time (F-185: never a ten-digit literal in a file)."""
    return "9" + "0" * 5 + "%04d" % n


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:400] + "]") if (got is not None and not cond) else ""))
    if label.startswith("C:"):
        CTRL.append((label, bool(cond)))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def l4(s):
    d = re.sub(r"\D", "", str(s or ""))
    return ("…" + d[-4:]) if d else "-"


def d10(s):
    d = re.sub(r"\D", "", str(s or ""))
    return d[-10:] if len(d) >= 10 else ""


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst, timeout=60)
    s.backup(d)
    d.close()
    s.close()


def text(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)))


def ins(con, table, row):
    cols = {r[1]: r for r in con.execute("PRAGMA table_info(%s)" % table)}
    full = dict((k, v) for k, v in row.items() if k in cols)
    for name, r in cols.items():
        if name not in full and r[3] and r[4] is None and not r[5]:
            full[name] = 0 if "INT" in (r[2] or "").upper() else ""
    cur = con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(full), ", ".join("?" * len(full))), list(full.values()))
    return cur.lastrowid


def app_env(a, dbp, token):
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(a.marg),
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(a.map), FINANCE_SSO_DIR=os.path.join(os.path.dirname(dbp), "nosso"),
                      RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="",
                      FINANCE_MARG_TOKEN=token)
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN"):
        os.environ.pop(k, None)


def load_old(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def page_look(a, fin, dbp):
    """The owner's state, read by the files in --fin (the live ones before placing, the placed ones after) on a copy of the live database,
    the walk's own header session: the switch, the pending pairs, the doctor's book page, the staff order page."""
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    cl = fa.app.test_client(use_cookies=False)

    def get(u, p):
        return cl.get(p, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
    c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    sw = c.execute("SELECT value FROM setting WHERE key='purchase.book_one_record.on'").fetchone()
    c.close()
    rb = get("manoj", BOOK)
    hb = rb.get_data().decode("utf-8", "replace")
    c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    sw2 = c.execute("SELECT value FROM setting WHERE key='purchase.book_one_record.on'").fetchone()
    pend = []
    for b, rg in c.execute("SELECT bill_norm, register_norm FROM purchase_vendor_alias ORDER BY bill_norm").fetchall():
        hb_ = c.execute("SELECT 1 FROM purchase_vendor_contact WHERE vendor_norm=?", (b,)).fetchone()
        hr_ = c.execute("SELECT 1 FROM purchase_vendor_contact WHERE vendor_norm=?", (rg,)).fetchone()
        if hb_ and hr_:
            pend.append(b)
    rows = c.execute("SELECT COUNT(*) FROM purchase_vendor_contact").fetchone()[0]
    c.close()
    ro = {u: get(u, ORDER) for u in ("shavez", "reception")}
    say("   the switch purchase.book_one_record.on: %s before the first read, %s after it" % (repr(sw[0]) if sw else "absent", repr(sw2[0]) if sw2 else "absent"))
    say("   the phone book: %d rows; %d alias pairs with both rows: %s" % (rows, len(pend), ", ".join(pend)))
    say("   /page/book as the doctor: %s, %d bytes, 'One record per dealer: OFF -- Turn on' %s, the merge panel %s"
        % (rb.status_code, len(hb), "shown" if "One record per dealer: OFF" in hb else "not there", "shown" if 'id="s574merge"' in hb else "not there"))
    for u, r in ro.items():
        t = r.get_data().decode("utf-8", "replace")
        say("   %s as %s: %s, %d bytes, the new no-number sentence %s" % (ORDER, u, r.status_code, len(t), "PRESENT" if NONUM in t else "absent"))
    if not a.after:
        say("PAGE STATE S574 (before)")
        return 0
    ok = (rb.status_code == 200 and "One record per dealer: OFF" in hb and 'id="s574merge"' not in hb and sw2 and sw2[0] == "0"
          and all(r.status_code == 200 and NONUM not in r.get_data().decode("utf-8", "replace") for r in ro.values()))
    leak = re.search(r"\d{10}", "\n".join(OUT))
    say(("PAGE OK S574" if ok and not leak else "PAGE RED S574") + ": switch OFF, the book page as before plus the doctor's line, the staff order page as before")
    return 0 if ok and not leak else 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--map"):
        ap.add_argument(k, required=True)
    for k in ("--old", "--portal", "--dump", "--old-dump"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--page", action="store_true")
    ap.add_argument("--after", action="store_true")
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S574_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.page:
        return page_look(a, fin, dbp)
    if not (a.old and a.portal and a.dump):
        ap.error("--old, --portal and --dump are needed for the walk")
    say("-- S574 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    token = secrets.token_hex(16)                             # a walk-only Marg token (never the live one)
    app_env(a, dbp, token)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import purchase_app as pa                                 # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import order_sheet_pdf as SP                              # noqa: E402
    import porders_s454 as PS                                 # noqa: E402
    import supplier_msg as SM                                 # noqa: E402
    import amir_day as AD                                     # noqa: E402
    for m in (pa, OS, SP, PS, SM, AD):
        assert m.__file__.startswith(fin), m.__file__
    old = os.path.abspath(a.old)
    PAO = load_old(os.path.join(old, "purchase_app.py"), "purchase_app_s574old")
    OSO = load_old(os.path.join(old, "order_sheet.py"), "order_sheet_s574old")
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != old]      # the old folder never serves an import
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none"))
    cl = fa.app.test_client(use_cookies=False)
    TIMES = []

    def GET(u, path):
        t0 = time.time()
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        TIMES.append((u, path, time.time() - t0, len(r.get_data())))
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def POST(u, body, path=API):
        r = cl.post(path, base_url=BASE, json=body, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        try:
            j = r.get_json(silent=True) or {}
        except Exception:                                      # noqa: BLE001
            j = {}
        return r.status_code, j

    def PUSHV(pairs):
        r = cl.post(PUSH, base_url=BASE, json=dict(pairs=pairs), headers={"X-Finance-Marg": token})
        return r.status_code

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    pristine = dbp + ".pristine"
    copydb(dbp, pristine)

    def reset():
        copydb(pristine, dbp)
        GET("manoj", BOOK)                                    # the first read of the book adds its columns (as on the box)

    def row(c, k):
        r = c.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (k,)).fetchone()
        return dict(r) if r else None

    def section(name, fn):
        say("-- " + name)
        try:
            fn()
        except Exception as e:                                # noqa: BLE001 -- a section that raises is red, the walk goes on
            import traceback                                  # noqa: PLC0415
            tb = traceback.format_exc().strip().splitlines()
            check("C: section '%s' ran to its end" % name.split()[0], False, "%s: %s | %s" % (type(e).__name__, str(e)[:160], " / ".join(x.strip() for x in tb[-4:])[:300]))

    W = {}
    # ============================================================================================ 0 the live state (rule 7)
    c = conn()
    names = set()
    for r in c.execute("SELECT vendor_norm, vendor FROM purchase_vendor_contact"):
        names.add(r[0])
        names.add(r[1])
    alias = [tuple(r) for r in c.execute("SELECT bill_norm, register_norm FROM purchase_vendor_alias ORDER BY bill_norm")]
    for b_, r_ in alias:
        names.add(b_)
        names.add(r_)
    W["names"] = sorted(n for n in names if n)
    W["rows"] = c.execute("SELECT COUNT(*) FROM purchase_vendor_contact").fetchone()[0]
    pend, differ = [], []
    for b_, r_ in alias:
        mb, rg = row(c, b_), row(c, r_)
        if mb and rg:
            pend.append(b_)
            if d10(mb["phone"]) and d10(mb["phone"]) != d10(rg["phone"]):
                differ.append(b_)
            say("   pair %-32s | %-32s | Marg's row %d number(s) %s | bank sheet's row %d number(s) %s%s"
                % (b_, r_, len([x for x in (mb["phone"], mb["phone2"]) if x]), " ".join(l4(x) for x in (mb["phone"], mb["phone2"]) if x),
                   len([x for x in (rg["phone"], rg["phone2"]) if x]), " ".join(l4(x) for x in (rg["phone"], rg["phone2"]) if x),
                   " (bank: %s)" % (rg.get("bank_status") or "none")))
        else:
            say("   alias %-31s | %-32s | Marg's row %s, bank sheet's row %s" % (b_, r_, "yes" if mb else "none", "yes" if rg else "none"))
    W["pend"] = pend
    al = {x for p in alias for x in p}
    singles = [r[0] for r in c.execute("SELECT vendor_norm FROM purchase_vendor_contact ORDER BY vendor_norm") if r[0] not in al]
    sw = c.execute("SELECT value FROM setting WHERE key='purchase.book_one_record.on'").fetchone()
    amap = {b_: r_ for b_, r_ in alias}
    ravi_ok = RAVI in amap and row(c, RAVI) is None and row(c, amap[RAVI]) is not None
    c.close()
    say("   %d rows; %d alias rows; %d pending pairs; singles (no alias): %d; the switch %s" % (W["rows"], len(alias), len(pend), len(singles),
                                                                                           repr(sw[0]) if sw else "absent"))
    check("the live state: the pending pairs are exactly the brief's 13, by alias key", sorted(pend) == sorted(PAIRS), sorted(set(pend) ^ set(PAIRS)))
    check("the live state: RAVI MEDICAL AGENCY has an alias row and no row of its own; its bank record exists", ravi_ok)
    check("the live state: Kedar is the only pair whose first numbers differ", differ == [KEDAR_M], differ)
    check("the live state: the switch is absent or '0'", (not sw) or sw[0] == "0", sw and sw[0])

    def readers_new(c, v):
        return dict(order=pa.book_number(c, v, "order"), call=pa.book_number(c, v, "call"), pay=SM._digits(c, v), wrap=pa._phone_for(c, v),
                    shown=list(pa.book_shown(c, v)), card=OS.book_card(c, v)[:3])

    def readers_old(c, v):
        o = PAO._phone_for(c, v)
        oo = OSO._phones(c, v)
        return dict(o=o, d=PAO._wa_digits(o), f=list(PAO._phones_for(c, v)), os=oo)

    def triple(c, v):
        return (pa.book_number(c, v, "order"), pa.book_number(c, v, "call"), SM._digits(c, v))

    # ============================================================================================ 1 OFF = as before
    def s1():
        s, h = GET("manoj", BOOK)
        os.makedirs(a.dump, exist_ok=True)
        dumps = {"book_manoj.html": h}
        s2, h2 = GET("shavez", ORDER)
        dumps["order_shavez.html"] = h2
        c = conn()
        ents = []
        try:
            ents = [e["sn"] for e in OS.entries(c)]
        except Exception:                                     # noqa: BLE001
            ents = []
        c.close()
        for sn in ents[:12]:
            from urllib.parse import quote                    # noqa: PLC0415
            dumps["sup_%s.html" % re.sub(r"\W", "_", sn)] = GET("shavez", ORDER + "/" + quote(sn, safe=""))[1]
        for k, v in dumps.items():
            with open(os.path.join(a.dump, k), "w", encoding="utf-8") as fh:
                fh.write(v)
        check("the pages answer 200: /page/book (manoj), %s (shavez)" % ORDER, s == 200 and s2 == 200, (s, s2))
        c = conn()
        bad = []
        for v in W["names"]:
            n, o = readers_new(c, v), readers_old(c, v)
            want_shown = [x for x in o["os"] if x]
            if not (n["order"] == n["call"] == n["wrap"] == o["o"] and n["pay"] == o["d"] and n["shown"] == o["f"] == want_shown
                    and list(n["card"]) == [o["os"][0], o["os"][0], want_shown]):
                bad.append(v)
        say("   compared %d names x 7 readers with the switch OFF" % len(W["names"]))
        check("C: OFF -- every reader (order, call, pay, _phone_for, book_shown, book_card) for all %d names equals the old file's _phone_for / "
              "_phones_for / order_sheet._phones / _wa_digits(_phone_for)" % len(W["names"]), not bad, bad[:5])
        lay = SP.layout(c)
        lb = [(b["name"], b["phones"], [x for x in OSO._phones(c, b["name"]) if x]) for b in lay["blocks"]]
        check("OFF -- the order sheet's bands print the old numbers (%d bands)" % len(lb), all(x[1] == x[2] for x in lb), [x[0] for x in lb if x[1] != x[2]][:4])
        c.close()
        check("C: OFF -- the doctor's book page carries 'One record per dealer: OFF' and a Turn on button", "One record per dealer: OFF" in h and "s574Switch(1)" in h)
        if a.old_dump:
            def norm_t(x):
                return re.sub(r"([?&](?:amp;)?t=)\d+", r"\g<1>T", x)
            od = {k: open(os.path.join(a.old_dump, k), encoding="utf-8").read() for k in os.listdir(a.old_dump)}
            line = pa._s574_switch_line(conn())
            same_book = h.replace(line, "", 1).replace(pa.S574_JS, "", 1) == od.get("book_manoj.html")
            check("C: OFF -- the doctor's book page is the old page byte for byte, plus the one line and its script", same_book,
                  (len(h), len(od.get("book_manoj.html") or "")))
            diffs = [k for k in dumps if k != "book_manoj.html" and norm_t(dumps[k]) != norm_t(od.get(k) or "")]
            check("OFF -- the staff order page and %d supplier pages (shavez) are the old ones byte for byte (the tap's moment t= aside)" % (len(dumps) - 2),
                  not diffs and set(dumps) == set(od), diffs[:4] or sorted(set(dumps) ^ set(od))[:4])
        # a number 3 saved while ON, then OFF: nowhere
        st, j = POST("manoj", dict(action="add", vendor="W574 THREE", phone=mk(301)))
        st2, j2 = POST("manoj", dict(action="switch", on=1))
        st3, j3 = POST("manoj", dict(action="phones", vendor_norm="W574 THREE", phone=mk(301), phone3=mk(303)))
        c = conn()
        on3 = [n for _s, n in pa.book_numbers(pa.book_record(c, "W574 THREE"))]
        c.close()
        check("C: while ON, number 3 of a made-up dealer (W574 THREE) is saved and read (slot 3)", st == 200 and st2 == 200 and st3 == 200 and mk(303) in on3,
              (st, st2, st3, j3.get("message")))
        POST("manoj", dict(action="switch", on=0))
        c = conn()
        n = readers_new(c, "W574 THREE")
        c.close()
        _s, hb = GET("manoj", BOOK)
        _s, hd = GET("darpan", BOOK)
        leak3 = [k for k, v in n.items() if mk(303) in json.dumps(v)] + (["book page"] if mk(303) in hb + hd else [])
        check("after OFF the number 3 appears nowhere: no reader, neither book page (the doctor's, Darpan's)", not leak3 and n["order"] == mk(301), leak3)
        reset()
    section("1  OFF = as before", s1)

    # ============================================================================================ 2 ON before the merge
    def s2():
        reset()
        st, j = POST("manoj", dict(action="switch", on=1))
        check("C: the doctor turns the switch ON", st == 200 and j.get("on") is True, (st, j))
        c = conn()
        B3, diff = {}, []
        for v in W["names"]:
            B3[v] = triple(c, v)
            o = readers_old(c, v)
            if B3[v] != (o["o"], o["o"], o["d"]):
                diff.append(v)
        rv = row(c, dict((x, y) for x, y in c.execute("SELECT bill_norm, register_norm FROM purchase_vendor_alias"))[RAVI])
        c.close()
        W["B3"] = B3
        check("C: ON, before the merge -- every reader for every name as before, except exactly RAVI MEDICAL AGENCY", diff == [RAVI], diff[:5])
        check("C: RAVI MEDICAL AGENCY now gives its bank record's number (%s; the old file: none)" % l4(rv and rv["phone"]),
              rv and B3.get(RAVI, ("",))[0] == rv["phone"] and B3[RAVI][2] == PAO._wa_digits(rv["phone"]), B3.get(RAVI) and [l4(x) for x in B3[RAVI]])
        s, h = GET("manoj", BOOK)
        check("C: the doctor's ON page shows the merge panel: '%d dealers are in the book twice' and 'Merge all %d'" % (len(W["pend"]), len(W["pend"])),
              s == 200 and ("%d dealers are in the book twice" % len(W["pend"])) in h and ("Merge all %d" % len(W["pend"])) in h, s)
        check("the panel's default names: JUBILEE AGENCIES, GUNINA PHARMACEUTICALS PVT LTD, SAISUN PHARMA PVT. LTD. selected",
              all(re.search(r'<option selected>%s</option>' % re.escape(_html.escape(x, quote=True)), h) for x in
                  ("JUBILEE AGENCIES", "GUNINA PHARMACEUTICALS PVT LTD", "SAISUN PHARMA PVT. LTD.")))
        check("the panel says the numbers differ for Kedar only", h.count("Numbers differ:") == 1 and "Numbers differ" in h.split(KEDAR_M, 1)[-1][:2000])
    section("2  ON before the merge", s2)

    def bank_state(c):
        norms = sorted({r[0] for r in c.execute("SELECT vendor_norm FROM purchase_vendor_contact")} | {x for p in
                       c.execute("SELECT bill_norm, register_norm FROM purchase_vendor_alias") for x in p})
        return json.dumps([pa._vendor_bank(c), pa._advice_accounts_s265(c), {n: AD._s494_bank(c, n) for n in norms}], sort_keys=True, default=str)

    def merged_now():
        reset()
        POST("manoj", dict(action="switch", on=1))
        return POST("manoj", dict(action="merge"))

    # ============================================================================================ 3 merge all
    def s3():
        reset()
        POST("manoj", dict(action="switch", on=1))
        c = conn()
        bank0 = bank_state(c)
        marg0 = {k: row(c, k) for k in W["pend"]}
        reg0 = {k: row(c, dict(c.execute("SELECT bill_norm, register_norm FROM purchase_vendor_alias").fetchall())[k]) for k in W["pend"]}
        n0 = c.execute("SELECT COUNT(*) FROM purchase_vendor_contact").fetchone()[0]
        c.close()
        st, j = POST("manoj", dict(action="merge"))
        check("C: the doctor taps Merge all: %d pairs merged" % len(W["pend"]), st == 200 and j.get("merged") == len(W["pend"]), (st, j))
        c = conn()
        live_keys = {r[0] for r in c.execute("SELECT vendor_norm FROM purchase_vendor_contact WHERE COALESCE(merged_into,'')=''")}
        s, h = GET("manoj", BOOK)
        m = re.search(r"const BOOKV=(\[.*?\]);", h)
        page_keys = set(json.loads(m.group(1))) if m else set()
        check("C: the book page lists %d dealers -- every record not merged away, by key (%d rows less the %d merged)"
              % (len(live_keys), n0, len(W["pend"])), page_keys == live_keys and len(page_keys) == n0 - len(W["pend"]), (len(page_keys), len(live_keys)))
        g = row(c, "GUNINA PHARMACEUTICALS")
        check("C: Gunina's record keeps the name GUNINA PHARMACEUTICALS PVT LTD", g and g.get("display_name") == "GUNINA PHARMACEUTICALS PVT LTD",
              g and g.get("display_name"))
        km = marg0[KEDAR_M]["phone"]
        kk = {v: triple(c, v) for v in (KEDAR_M, KEDAR_R)}
        check("C: Kedar's order, call and pay numbers equal the Marg row's phone (%s), by KEDAR PHARMACEUTICAL and by KEDAR PHARMA" % l4(km),
              all(x[0] == km and x[1] == km and x[2] == PAO._wa_digits(km) for x in kk.values()), {k: [l4(y) for y in v] for k, v in kk.items()})
        bad = [v for v in W["names"] if pa.supplier_key(v) != KEDAR_R and triple(c, v) != W["B3"][v]]
        check("C: every reader's number for every other name equals step 2's (%d names; KEDAR PHARMA itself now gives Marg's number, as the "
              "brief's step 4 orders)" % len([v for v in W["names"] if pa.supplier_key(v) != KEDAR_R]), not bad, bad[:5])
        check("the bank readers (_vendor_bank, _advice_accounts_s265, amir_day._s494_bank) give the same for every norm before and after",
              bank_state(c) == bank0)
        n1 = c.execute("SELECT COUNT(*) FROM purchase_vendor_contact").fetchone()[0]
        npm = c.execute("SELECT COUNT(*) FROM purchase_vendor_premerge WHERE undone_at IS NULL").fetchone()[0]
        check("C: no row deleted (%d before, %d after); purchase_vendor_premerge holds %d rows" % (n0, n1, npm), n1 == n0 and npm == len(W["pend"]), (n0, n1, npm))
        keep = [k for k in W["pend"] if {x: y for x, y in row(c, k).items() if x != "merged_into"} != {x: y for x, y in marg0[k].items() if x != "merged_into"}]
        rk = ("vendor", "acct_name", "acct_no", "ifsc", "bank_branch", "upi_id", "bank_status", "bank_verified_by", "bank_verified_at")
        regch = [k for k in W["pend"] if any(row(c, reg0[k]["vendor_norm"])[f] != reg0[k][f] for f in rk)]
        check("Marg's rows: only merged_into set; the bank sheet's rows: vendor, account name and bank fields untouched", not keep and not regch, (keep, regch))
        c.close()
        st2, j2 = POST("manoj", dict(action="merge"))
        check("a second Merge all merges nothing (keyed, idempotent)", st2 == 200 and j2.get("merged") == 0, (st2, j2))
    section("3  merge all", s3)

    # ============================================================================================ 4 picks
    def s4():
        merged_now()
        c = conn()
        rk = row(c, KEDAR_R)
        c.close()
        st, j = POST("manoj", dict(action="picks", vendor_norm=KEDAR_R, call_pick=2, order_pick=2, pay_pick=1))
        c = conn()
        dg = SM._digits(c, KEDAR_M)
        on = pa.book_number(c, KEDAR_M, "order")
        empty = [v for v in W["names"] if triple(c, v)[0] and not SM._digits(c, v)]
        c.close()
        check("C: Kedar's Payment msg set to number 1 -> supplier_msg._digits('KEDAR PHARMACEUTICAL') gives it (%s)" % l4(rk["phone"]),
              st == 200 and dg and dg == PAO._wa_digits(rk["phone"]), (st, j.get("message"), l4(dg)))
        check("Kedar's Order WhatsApp number unchanged (%s)" % l4(rk["phone2"]), on == rk["phone2"], l4(on))
        check("supplier_msg._digits is non-empty for every name that has a number (%d names)" % len(W["names"]), not empty, empty[:5])
        s, h = GET("manoj", BOOK)
        check("C: the doctor's page carries the three drop-downs on Kedar's line (2 numbers) and the pick in the changes", 'id="pk-pay-' in h
              and "Payment msg: number 1" in h, s)
    section("4  picks", s4)

    # ============================================================================================ 5 Marg's push
    def s5():
        merged_now()
        c = conn()
        n0 = c.execute("SELECT COUNT(*) FROM purchase_vendor_contact").fetchone()[0]
        dd0, ddr0 = row(c, "DRUG DEAL"), row(c, "DRUG DEALS")
        jm0, jr0 = row(c, "JUBILEE AGENCIES"), row(c, "JUBLI AGENCY")
        c.close()
        s1_ = PUSHV({dd0["vendor"]: dd0["phone"]})
        c = conn()
        dd1, ddr1 = row(c, "DRUG DEAL"), row(c, "DRUG DEALS")
        c.close()
        drop = lambda r: {k: v for k, v in r.items() if k != "updated_at"}        # noqa: E731
        check("push, an existing number (DRUG DEAL BAREILLY, %s): nothing changes but updated_at" % l4(dd0["phone"]),
              s1_ == 200 and drop(dd1) == drop(dd0) and drop(ddr1) == drop(ddr0), s1_)
        s2_ = PUSHV({jm0["vendor"]: mk(501)})
        c = conn()
        jm1, jr1 = row(c, "JUBILEE AGENCIES"), row(c, "JUBLI AGENCY")
        n1 = c.execute("SELECT COUNT(*) FROM purchase_vendor_contact").fetchone()[0]
        fm = c.execute("SELECT COUNT(*) FROM purchase_book_change WHERE vendor_norm='JUBLI AGENCY' AND what='from Marg' AND new4=?", (mk(501)[-4:],)).fetchone()[0]
        c.close()
        free = next((s for s in ("phone2", "phone3", "phone4") if not (jr0.get(s) or "")), None)
        check("C: push, a made-up new number for a merged dealer (JUBILEE AGENCIES BAREILLY): into the record's free slot (%s), Marg's row "
              "untouched, rows still %d, one 'from Marg' line" % (free, n0), s2_ == 200 and free and jr1[free] == mk(501) and jm1 == jm0 and n1 == n0 and fm == 1,
              (s2_, free, jm1 == jm0, n1, fm))
        POST("manoj", dict(action="add", vendor="W574 FULL", phone=mk(511), phone2=mk(512)))
        POST("manoj", dict(action="phones", vendor_norm="W574 FULL", phone=mk(511), phone2=mk(512), phone3=mk(513), phone4=mk(514)))
        c = conn()
        f0 = row(c, "W574 FULL")
        c.close()
        PUSHV({"W574 FULL": mk(515)})
        PUSHV({"W574 FULL": mk(515)})
        c = conn()
        f1 = row(c, "W574 FULL")
        mx = c.execute("SELECT COUNT(*) FROM purchase_book_change WHERE vendor_norm='W574 FULL' AND what='marg_extra' AND new4=?", (mk(515)[-4:],)).fetchone()[0]
        c.close()
        s, h = GET("manoj", BOOK)
        check("C: push, a made-up number for a full dealer (W574 FULL, 4 numbers), twice: nothing written to the record, one 'marg_extra' line, "
              "and the owner's line 'Marg has another number for W574 FULL (…%s)'" % mk(515)[-4:],
              f0 and f1 == f0 and mx == 1 and ("Marg has another number for W574 FULL (…%s)" % mk(515)[-4:]) in h, (f1 == f0, mx))
        POST("manoj", dict(action="phones", vendor_norm="W574 FULL", phone=mk(511), phone2=mk(512), phone3=mk(513), phone4=mk(515)))
        s, h = GET("manoj", BOOK)
        check("after the doctor edits W574 FULL's numbers the owner's line is gone", "Marg has another number for W574 FULL" not in h)
        PUSHV({"W574 NEW DEALER": mk(521)})
        c = conn()
        nd = row(c, "W574 NEW DEALER")
        c.close()
        check("push, a made-up new dealer (W574 NEW DEALER): a new row with its number", nd and nd["phone"] == mk(521), nd and l4(nd["phone"]))
        POST("manoj", dict(action="switch", on=0))
        c = conn()
        jmb = row(c, "JUBILEE AGENCIES")
        c.close()
        PUSHV({jm0["vendor"]: mk(531), "W574 OFF DEALER": mk(532)})
        c = conn()
        jma, od = row(c, "JUBILEE AGENCIES"), row(c, "W574 OFF DEALER")
        c.close()
        check("switch OFF: the push is the old statement -- Marg's own row takes the pushed number (it is not 'server'), a new name makes a row",
              jma["phone"] == (jmb["phone"] if (jmb.get("source") or "") == "server" else mk(531)) and od and od["phone"] == mk(532), (l4(jma["phone"]),))
    section("5  Marg's push", s5)

    # ============================================================================================ 6 the doors
    def s6():
        reset()
        POST("manoj", dict(action="add", vendor="W574 DOOR", phone=mk(601)))
        POST("manoj", dict(action="switch", on=1))
        refused = {}
        for u in ("darpan", "shavez"):
            got = []
            for body in (dict(action="picks", vendor_norm="W574 DOOR", call_pick=1), dict(action="phones", vendor_norm="W574 DOOR", phone=mk(602)),
                         dict(action="add", vendor="W574 DOOR %s" % u.upper(), phone=mk(603)), dict(action="merge"), dict(action="unmerge"),
                         dict(action="switch", on=0)):
                st, j = POST(u, body)
                got.append((body["action"], st, j.get("message") == REFUSE))
            refused[u] = got
        for u in ("darpan", "shavez"):
            check("C: %s posts picks / phones / add / merge / unmerge / switch: each refused 403 '%s'" % (u, REFUSE),
                  all(st == 403 and m for _a, st, m in refused[u]), [x for x in refused[u] if not (x[1] == 403 and x[2])])
        bank = dict(acct_name="W574 DOOR", acct_no="1" + "0" * 9 + "574", ifsc="SBIN0W57400", bank_branch="W574 BRANCH", upi_id="")
        st, j = POST("shavez", dict(action="bank", vendor_norm="W574 DOOR", **bank))
        check("shavez saves bank details as before (allowed, UNVERIFIED)", st == 200 and j.get("bank_status") == "UNVERIFIED", (st, j.get("message")))
        st, j = POST("darpan", dict(action="bank", vendor_norm="W574 DOOR", **bank))
        check("darpan's bank save refused as before ('Bank details are for Dr Manoj and Shavez.')", st == 403, (st, j.get("message")))
        a1 = POST("manoj", dict(action="picks", vendor_norm="W574 DOOR", call_pick=1, order_pick="", pay_pick=""))
        a2 = POST("manoj", dict(action="phones", vendor_norm="W574 DOOR", phone=mk(601), phone2=mk(604)))
        a3 = POST("manoj", dict(action="add", vendor="W574 DOOR TWO", phone=mk(605)))
        check("C: the doctor's picks, phones and add are allowed", a1[0] == 200 and a2[0] == 200 and a3[0] == 200, (a1[0], a2[0], a3[0], a1[1].get("message")))
        st, j = POST("manoj", dict(action="phones", vendor_norm="W574 DOOR", phone="5" + "0" * 9))
        check("a number not starting 6-9 is refused (the one-record page's check)", st == 400, (st, j.get("message")))
        st, j = POST("manoj", dict(action="phones", vendor_norm="W574 DOOR", phone=mk(601), email1="w574.example"))
        check("an email without one @ and a dot is refused", st == 400, (st, j.get("message")))
    section("6  the doors", s6)

    # ============================================================================================ 7 undo
    def s7():
        merged_now()
        st, j = POST("manoj", dict(action="unmerge"))
        c = conn()
        back = [v for v in W["names"] if triple(c, v) != W["B3"][v]]
        still = [k for k in W["pend"] if (row(c, k) or {}).get("merged_into")]
        und = c.execute("SELECT COUNT(*) FROM purchase_vendor_premerge WHERE undone_at IS NOT NULL").fetchone()[0]
        c.close()
        check("C: undo on a fresh merge: every reader for every name gives step 2's numbers again (Kedar PHARMA included); Marg's rows unmerged",
              st == 200 and j.get("undone") == len(W["pend"]) and not back and not still, (st, j.get("message"), back[:4], still[:4]))
        check("the premerge rows are kept and marked undone (%d)" % und, und == len(W["pend"]), und)
        POST("manoj", dict(action="merge"))
        c = conn()
        jm0, jr0 = row(c, "JUBILEE AGENCIES"), row(c, "JUBLI AGENCY")
        c.close()
        st1, _j1 = POST("manoj", dict(action="phones", vendor_norm="JUBLI AGENCY", phone=jr0["phone"], phone3=mk(701)))
        st2, _j2 = POST("manoj", dict(action="phones", vendor="JUBILEE AGENCIES", phone=jr0["phone"], phone3=mk(701), phone4=mk(702)))
        c = conn()
        jm1, jr1 = row(c, "JUBILEE AGENCIES"), row(c, "JUBLI AGENCY")
        c.close()
        check("C: a save posted by the record's key lands on the bank sheet's row (number 3), never the hidden Marg row; one by Marg's name too",
              st1 == 200 and st2 == 200 and jr1["phone3"] == mk(701) and jr1["phone4"] == mk(702) and jm1 == jm0, (st1, st2, jm1 == jm0))
        st, j = POST("manoj", dict(action="unmerge"))
        s, h = GET("manoj", BOOK)
        check("C: after a number edit the undo is refused: '%s' (the API and the page)" % CLOSED, st == 409 and j.get("message") == CLOSED and CLOSED in h,
              (st, j.get("message")))
    section("7  undo", s7)

    # ============================================================================================ 8 staff-eye
    def s8():
        merged_now()
        code = ("import json,sys; sys.path.insert(0, %r); import portal as po; out={}\n"
                "for u in %r: out[u]=[t['name'] for g, ts in po._visible_sections('staff', False, u) for t in ts]\n"
                "print('TILES ' + json.dumps(out))" % (a.portal, list(STAFF)))
        pp = subprocess.run([sys.executable, "-B", "-c", code], cwd=a.portal, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                            env=dict(os.environ, TILE_GRANTS_FILE=os.path.join(a.portal, "tile_grants.json"), CLINIC_SSO_SECRET="w574-walk-only",
                                     PYTHONDONTWRITEBYTECODE="1"))
        tl = [x for x in pp.stdout.splitlines() if x.startswith("TILES ")]
        tiles = json.loads(tl[-1][6:]) if tl else {}
        check("staff-eye: each portal home renders its tiles, 'Purchase orders' on it, for %s (the real portal.py + the grants file, a walk-only secret)"
              % ", ".join(STAFF), tiles and all("Purchase orders" in tiles.get(u, []) for u in STAFF), (tiles and {u: len(v) for u, v in tiles.items()}, pp.stdout[-200:]))
        for u in STAFF:
            s, h = GET(u, ORDER)
            check("staff-eye: %s reads %s (200, %d bytes)" % (u, ORDER, len(h)), s == 200 and len(h.encode("utf-8")) < 100000, s)
        for on in (1, 0):
            POST("manoj", dict(action="switch", on=on))
            for u in ("darpan", "shavez"):
                s, h = GET(u, BOOK)
                found = [p for p in CONTROLS if re.search(p, h)]
                check("C: switch %s -- %s's book page (200) has no number, pick, add, merge, undo or switch control" % ("ON" if on else "OFF", u),
                      s == 200 and not found, (s, found))
                if u == "shavez":
                    check("switch %s -- Shavez's book page keeps the bank Add/Edit as before" % ("ON" if on else "OFF"), re.search(r"bookForm\(\d+,'bank'\)", h))
        s, _h = GET("reception", BOOK)
        check("a reception login does not open the book page (as before)", s != 200, s)
        say("   no duty is added, moved or removed: DUTY_MAP is not changed by this kit")
    section("8  staff-eye", s8)

    # ============================================================================================ 9 staff words
    def s9():
        merged_now()
        c = conn()
        import order_rules                                    # noqa: PLC0415
        if order_rules._frozen(c):
            c.execute("UPDATE setting SET value='' WHERE key='order.freeze'")    # this scratch copy only: the cards show only while ordering is open
            say("   ordering is frozen on the copy: the freeze is lifted on this scratch copy only, for the cards to show")
        SM.ensure(c)
        now = dt.datetime.now().replace(microsecond=0).isoformat()
        month = dt.date.today().strftime("%Y-%m")
        ids = {}
        for sn in ("W574 NONUM", KEDAR_M):
            d = ins(c, "purchase_order", dict(created_at=now, created_by="w574walk", vendor=sn, status="draft", total_p=0, supplier_norm=sn,
                                              ext_ref="", order_src="s454", order_via="whatsapp"))     # no ext_ref: drawn on the sheet as its own band
            ins(c, "purchase_order_line", dict(order_id=d, item="W574 ITEM", packs=1, pack_size=1, units=1))
            ins(c, "supplier_msg", dict(month=month, vendor_norm=sn, vendor=sn, kind="order", ref=d, channel="whatsapp", body="W574 walk",
                                        status="queued", queued_at=now))
            ids[sn] = d
        c.commit()
        es = {e["sn"]: e for e in OS.entries(c)}
        c.close()
        from urllib.parse import quote                        # noqa: PLC0415
        s, h = GET("shavez", ORDER + "/" + quote("W574 NONUM", safe=""))
        t = text(h)
        check("C: switch ON, a made-up dealer with no number (W574 NONUM): its page reads '%s', not '%s'" % (NONUM, OLDNO), s == 200 and NONUM in t and OLDNO not in t, (s, t[:160]))
        e = es.get("W574 NONUM")
        card = PS._card(False, dict(e, state="pending", called="")) if e else ""
        check("C: ... and its card on the list (pending) reads '%s'" % NONUM, e and NONUM in card and OLDNO not in card, card[:160])
        s, h = GET("shavez", ORDER + "/" + quote(KEDAR_M, safe=""))
        c = conn()
        call, wa = pa.book_number(c, KEDAR_M, "call"), pa.book_number(c, KEDAR_M, "order")
        c.close()
        tel = re.search(r'id="callkaro" href="tel:([0-9+]*)"', h)
        check("C: Kedar's page (merged) carries 'Call: <the Calls number>' and 'WhatsApp: <the Order WhatsApp number>'; Call karo dials the Calls number",
              s == 200 and ('id="numcall">Call: %s<' % call) in h and ('id="numwa">WhatsApp: %s<' % wa) in h and tel and d10(tel.group(1)) == d10(call), s)
        c = conn()
        ek = {x["sn"]: x for x in OS.entries(c)}.get(KEDAR_M)
        OS._queue_message(c, ek, ids[KEDAR_M], "w574walk", requeue=True)
        to = c.execute("SELECT to_number FROM supplier_msg WHERE kind='order' AND ref=?", (ids[KEDAR_M],)).fetchone()[0]
        lay = SP.layout(c)
        kb = [b for b in lay["blocks"] if b["name"] == KEDAR_M]
        c.close()
        check("the WhatsApp queue sends Kedar's order to the Order WhatsApp number", to == pa._wa_digits(wa), l4(to))
        check("the order sheet's band for Kedar prints the Calls number (and the WhatsApp one when another)", kb and kb[0]["phones"] == [x for x in (call, "" if wa == call else wa) if x],
              kb and [l4(x) for x in kb[0]["phones"]])
        s2, h2 = GET("shavez", ORDER)
        sysw = [w for w in SYSWORDS if re.search(r"\b%s\b" % w, text(h) + " " + text(h2), re.I)]
        check("no system words (%s) on the staff order page or Kedar's page" % ", ".join(SYSWORDS), not sysw, sysw)
        check("the staff order page is under 100 KB (%d bytes)" % len(h2.encode("utf-8")), s2 == 200 and len(h2.encode("utf-8")) < 100000, s2)
        POST("manoj", dict(action="switch", on=0))
        s, h = GET("shavez", ORDER + "/" + quote("W574 NONUM", safe=""))
        check("switch OFF: the same page reads the old sentence ('Is supplier ka %s'), words as before" % OLDNO, s == 200 and ("Is supplier ka " + OLDNO) in text(h)
              and NONUM not in h, s)
    section("9  staff words", s9)

    # ============================================================================================ 10 dead code
    def s10():
        hits = []
        for f in sorted(os.listdir(fin)):
            if not f.endswith(".py"):
                continue
            for i, ln in enumerate(open(os.path.join(fin, f), encoding="utf-8", errors="replace"), 1):
                if re.search(r"\b_phones_for\(|(?<![\w.])_phones\(|OS\._phones\(|\bdef _phones\b", ln):
                    hits.append("%s:%d" % (f, i))
        check("C: dead code -- no definition or caller of order_sheet._phones or purchase_app._phones_for in the %s folder" % ("new" if not a.expect_red else "old"),
              not hits, hits[:6])
    section("10 dead code", s10)

    # ---------------------------------------------------------------- the end
    try:
        os.remove(pristine)
    except OSError:
        pass
    heavy = [(u, p, round(t_, 2), n) for u, p, t_, n in TIMES if u in STAFF and p.startswith("/finance/porders") and (t_ >= 2.0 or n >= 100000)]
    check("every staff order page the walk opened: under 100 KB and under 2 s (%d reads)" % len([x for x in TIMES if x[0] in STAFF and x[1].startswith("/finance/porders")]),
          not heavy, heavy[:4])
    leak = re.search(r"\d{10}", "\n".join(OUT))
    check("11 the walk's own output holds no run of 10 digits", not leak)
    red = len(FAILS)
    if a.expect_red:
        cr = [l for l, ok in CTRL if not ok]
        cg = [l for l, ok in CTRL if ok]
        for l in cr:
            say("  RED on the old files: " + l[:150])
        if CTRL and not cg:
            say("WALK OK negative control: every one of the %d 'C:' checks is red on the old files (%d of %d checks red)" % (len(CTRL), red, RUN[0]))
            return 0
        say("NEGATIVE CONTROL FAILED: %d 'C:' checks stayed green on the old files: %s" % (len(cg), "; ".join(x[:80] for x in cg)))
        return 1
    if FAILS:
        say("WALK RED: %d of %d checks failed" % (red, RUN[0]))
        return 1
    say("WALK OK S574: %d checks green (OFF as before, ON, the merge, picks, the push, the doors, undo, staff-eye, staff words, dead code)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
