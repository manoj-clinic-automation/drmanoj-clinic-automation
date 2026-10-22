#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s628.py -- kit S628_ONE_NAME_LIST (22-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s628.py --fin <scratch /root/finance with the files under test> --db <COPY of finance.db> --adb <COPY of assets.db>
                            --shared <scratch /root/shared> --por <scratch /root/portal: the walk writes its OWN secret and user store>
                            --marg <scratch marg_ingest> [--expect-red]
The real finance app in one process (header sessions on a walk-only portal store). The spine is the scratch folder's spine/spine.db, a COPY:
the walk adds its own lines to it ('W628 ...' items, dealer 'W628 PHARMA'). Its own rows by key, never found by counting. The four cases of
S338 (THIO Q AP, ZUPRINOR 5, POWERGESIC 100 PATCH, LINVIZ 600) are read on the copy by order and item. --expect-red is the negative control:
the same walk on the OLD files, every 'C:' check must be red. No phone number is printed (ten digits masked). Prints 'WALK OK S628 ...'."""
import argparse
import datetime as dt
import html as _html
import json
import os
import re
import secrets
import sqlite3
import sys

KIT = "S628_ONE_NAME_LIST"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "darpan": "staff", "reception": "staff", "alisha": "staff", "shivani": "staff", "bhati": "staff", "shavez": "manager", "amir": "staff"}
RUN, FAILS, CTRL, OUT = [0], [], [], []
P = "/finance/porders"


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:600] + "]") if (got is not None and not cond) else ""))
    if label.startswith("C:"):
        CTRL.append((label, bool(cond)))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def section(title, fn):
    say("-- %s" % title)
    try:
        fn()
    except Exception as e:                                     # noqa: BLE001
        import traceback
        check("C: section %s ran without an exception" % title[:40], False, "%s: %s | %s" % (type(e).__name__, str(e)[:300], traceback.format_exc()[-1200:]))


def text(h):
    h = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", "", h)
    h = re.sub(r"<(br|/div|/h1|/summary|/details|/button)[^>]*>", "\n", h)
    h = re.sub(r"<[^>]+>", " ", h)
    return "\n".join(x.strip() for x in _html.unescape(h).splitlines() if x.strip())


def portal_setup(por):
    assert por.startswith("/tmp/"), "the walk writes its own portal_config only into a scratch folder"
    secret = secrets.token_hex(32)
    with open(os.path.join(por, "portal_config.py"), "w") as fh:
        fh.write("# W628 walk only -- a random secret made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w628-walk'\n" % secret)
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
        assert p.startswith("/tmp/"), "the walk runs on scratch copies in /tmp only: %s" % p
    spine = os.path.join(fin, "spine", "spine.db")
    say("-- S628 walk on the %s: %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin))
    secret, store = portal_setup(por)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=adb, SHARED_LIB_DIR=shared, CLINIC_PORTAL_DIR=por, FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=marg,
                      ORDER_PUSH_NONE="1", FINANCE_SSO_DIR=por, RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="",
                      FINANCE_DEV_ROLE="", PYTHONDONTWRITEBYTECODE="1", CLINIC_SSO_SECRET=secret, CLINIC_USERS_FILE=store,
                      TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"), SPINE_DB=spine)
    os.makedirs(os.environ["RING_PORTAL_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SARVAM_API_KEY", "PORDERS_SOURCE"):
        os.environ.pop(k, None)
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != here]   # never import from the kit's own folder
    sys.path.insert(0, fin)
    sys.path.insert(1, shared)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import porders as PO                                      # noqa: E402
    import order_track as OT                                  # noqa: E402
    import purchase_app as pa                                 # noqa: E402
    for m in (fa, OS, PO, OT):
        assert m.__file__.startswith(fin), m.__file__
    try:
        import med_names as MN                                # noqa: E402
        if not MN.__file__.startswith(fin):
            MN = None
    except ImportError:
        MN = None
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; med_names %s" % (
        [n for n, _w in fa._MOUNT_FAILED] or "none", "NEW (S628)" if MN else "absent (OLD)"))
    cl = fa.app.test_client(use_cookies=False)
    NOW = dt.datetime(2026, 10, 22, 18, 0)

    def GET(u, path):
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def POST(u, path, body):
        r = cl.post(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, json=body)
        try:
            j = json.loads(r.get_data().decode("utf-8", "replace"))
        except ValueError:
            j = {}
        return r.status_code, j

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def line_state(c, oid, item):
        for s in OT.light_all(c, NOW, oids=[oid]):
            for x in s["lines"]:
                if x["item"] == item:
                    return s, x
        return None, None

    # ---- the walk's own spine lines and orders (dealer W628 PHARMA; items W628 ZEDOL ...)
    def lay():
        sp = sqlite3.connect(spine)
        for name, pk, kind in (("W628 ZEDOL 500", "1*10", "LOOSE"), ("W628 ZEDOL 500 TAB", "1*10", "LOOSE"), ("W628 ZEDOL 650", "1*10", "LOOSE"),
                               ("W628 KARVOL 40", "1*10", "LOOSE"), ("W628 KARVOLL 40", "1*10", "LOOSE"), ("W628 BANDAGE 6*4", "1*1", "WHOLE"),
                               ("W628 BANDAGE 8*4", "1*1", "WHOLE"), ("W628 MIXOL 5", "1*1", "WHOLE"), ("W628 NOVAX 20", "1*10", "LOOSE")):
            sp.execute("INSERT INTO sp_item (k20, name, packing, unit_kind, first_seen, last_seen) VALUES (?,?,?,?,?,?)",
                       (re.sub(r"\s+", " ", name)[:20].strip(), name, pk, kind, "2026-04-01", "2026-10-21"))
        cols = [r[1] for r in sp.execute("PRAGMA table_info(sp_purchase_line)")]

        def pl(sup, bill, date, seq, name, qty, free, amt, pk):
            row = dict(supkey=sup, bill=bill, date=date, seq=seq, name27=name[:27], k20=re.sub(r"\s+", " ", name)[:20].strip(), packing=pk, qty=qty, free=free,
                       units=qty * 10 if pk == "1*10" else qty, amount_p=amt, net_amount_p=amt, direction="PURCHASE", source_md5="w628walk")
            sp.execute("INSERT INTO sp_purchase_line (%s) VALUES (%s)" % (", ".join(c for c in cols if c in row), ",".join("?" * len([c for c in cols if c in row]))),
                       [row[c] for c in cols if c in row])
        # history: W628 ZEDOL 500 bought before at Rs 50.00 a strip; W628 KARVOL 40 at Rs 30.00
        pl("WPHARMA", "W628-H1", "2026-09-10", 1, "W628 ZEDOL 500", 10, 0, 50000, "1*10")
        pl("WPHARMA", "W628-H2", "2026-09-10", 2, "W628 KARVOL 40", 10, 0, 30000, "1*10")
        # after the order (14-10): the pack-word partner (sure), a sibling strength (never), a one-letter name (asked), a bandage size (never)
        pl("WPHARMA", "W628-1", "2026-10-14", 1, "W628 ZEDOL 500 TAB", 10, 0, 50000, "1*10")
        pl("WPHARMA", "W628-1", "2026-10-14", 2, "W628 ZEDOL 650", 10, 0, 70000, "1*10")
        pl("WPHARMA", "W628-1", "2026-10-14", 3, "W628 KARVOLL 40", 10, 0, 30000, "1*10")
        pl("WPHARMA", "W628-1", "2026-10-14", 4, "W628 BANDAGE 8*4", 5, 0, 5000, "1*1")
        # another dealer's bill (W628 OTHERCO) carrying W628 MIXOL 5 two days after the order; and W628 NOVAX 20 as two lines on one own bill
        pl("WOTHERCO", "W628-9", "2026-10-15", 1, "W628 MIXOL 5", 4, 0, 4000, "1*1")
        pl("WPHARMA", "W628-1", "2026-10-14", 5, "W628 NOVAX 20", 3, 0, 9000, "1*10")
        pl("WPHARMA", "W628-1", "2026-10-14", 6, "W628 NOVAX 20", 2, 0, 6000, "1*10")
        sp.commit()
        sp.close()
        c = conn()
        oid = c.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, note, total_p, sent_by, section, supplier_norm, order_src, order_via) "
                        "VALUES ('2026-10-13T17:00:00','W628 walk','W628 PHARMA','sent','W628 walk',0,'W628 walk','Medicines',?,'s454','whatsapp')",
                        (pa.supplier_key("W628 PHARMA"),)).lastrowid
        for item, packs, rate in (("W628 ZEDOL 500", 10, 5000), ("W628 KARVOL 40", 10, 3000), ("W628 BANDAGE 6*4", 5, 1000), ("W628 MIXOL 5", 4, 1000),
                                  ("W628 NOVAX 20", 5, 3000)):
            c.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units, rate_p, value_p, short, missing) VALUES (?,?,?,?,?,?,0,0,0)",
                      (oid, item, packs, 10 if "BANDAGE" not in item and "MIXOL" not in item else 1, packs * 10, rate))
        # an order whose every line was tapped Nahi mila (the planted 'nothing came')
        o2 = c.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, note, total_p, sent_by, section, supplier_norm, order_src, order_via, "
                       "received_at, received_by) VALUES ('2026-10-20T13:00:00','W628 walk','W628 EMPTYCO','received','W628 walk',0,'W628 walk','Medicines',?,'s454',"
                       "'whatsapp','2026-10-21T12:29:00','alisha')", (pa.supplier_key("W628 EMPTYCO"),)).lastrowid
        c.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units, rate_p, value_p, supplied, short, missing, arrived_by, arrived_at) "
                  "VALUES (?,?,?,?,?,0,0,0,1,1,'alisha','2026-10-21T12:29:00')", (o2, "W628 NILCO 10", 5, 10, 50))
        # F-990's shape: a line billed earlier at the first of two lines (3), as the code before S598 wrote it -- S628 raises it to the sum (5)
        c.execute("UPDATE purchase_order_line SET billed_qty=3, billed_bill_no='W628-1', billed_date='2026-10-14', detected_at='2026-10-15T09:30:00', "
                  "supplied=3, short=1, arrived_by='marg', arrived_at='2026-10-15T09:30:00' WHERE order_id=? AND item='W628 NOVAX 20'", (oid,))
        c.execute("INSERT INTO setting (key, value, note) VALUES ('names.last_learn','2000-01-01T00:00:00','W628 walk') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
        c.commit()
        c.close()
        return oid, o2

    O = {}

    def s_units():
        if MN is None:
            check("C: med_names is present", False)
            return
        check("pack_pair: THIO Q AP = THIO Q AP TAB", MN.pack_pair("THIO Q AP", "THIO Q AP TAB"))
        check("pack_pair: LINVIZ 600 = LINVIZ 600 6T", MN.pack_pair("LINVIZ 600", "LINVIZ 600 6T"))
        check("pack_pair: never two bandage sizes (6*4 / 8*4)", not MN.pack_pair("LEUKOCREPE 6*4", "LEUKOCREPE 8*4"))
        check("pack_pair: never a tablet and a capsule", not MN.pack_pair("ECOFOO TAB", "ECOFOO CAP"))
        check("pack_pair: never two strengths", not MN.pack_pair("DOLO 650", "DOLO 500"))
        check("near_pair: a substitute (FLACORT 6 / FLEMCORT 6) is never even asked", not MN.near_pair("FLACORT 6", "FLEMCORT 6"))
        check("loose: PATOPAN D is not PATOPAN DSR", MN.loose("PATOPAN D", "PATOPAN DSR") == 0)
        check("loose: DOLO 650 PLUS is not DOLO 650", MN.loose("DOLO 650 PLUS", "DOLO 650") == 0)
        check("loose: TAB ORICOX-P 10*10 = ORICOX P", MN.loose("TAB ORICOX-P 10*10", "ORICOX P") > 0)
        check("loose: NASO B12 NASAL SPRY = NASO B12", MN.loose("NASO B12 NASAL SPRY", "NASO B12") > 0)
        check("loose: ASTUFEN-SP = ASTOFEN SP (one letter)", MN.loose("ASTUFEN-SP", "ASTOFEN SP") > 0)

    def s_detect():
        oid, o2 = lay()
        O.update(oid=oid, o2=o2)
        c = conn()
        n = PO.detect_supplies(c)
        say("   detect_supplies -> %s" % n)
        cp = OT.carry_pass(c, NOW)
        say("   carry_pass -> %s" % cp)
        # S338's four cases on the copy of the live data
        _s, x = line_state(c, 22, "THIO Q AP")
        check("C: THIO Q AP (order 22) came -- 12 strips (10 + 2) on Deepam's A000678 as THIO Q AP TAB", x and x["state"] == "came" and x["came"] == 12, x)
        _s, x = line_state(c, 24, "ZUPRINOR 5")
        check("C: ZUPRINOR 5 (order 24) came -- the two lines of JP23217 summed (6)", x and x["state"] == "came" and x["came"] == 6, x)
        _s, x = line_state(c, 33, "POWERGESIC 100 PATCH")
        check("C: POWERGESIC 100 PATCH (order 33) came from Janta (23672), not short", x and x["state"] == "came" and x.get("how") == "other", x)
        _s, x = line_state(c, 38, "LINVIZ 600")
        check("C: LINVIZ 600 (order 38) short 7 strips -- 36 tablets of 100 came", x and x["state"] == "short" and x["short"] == 7, x)
        _s, x = line_state(c, 25, "C2CALZ")
        check("C2CALZ (order 25) still short 2", x and x["state"] == "short" and x["short"] == 2, x)
        _s, x = line_state(c, 34, "XGESIC LA")
        check("XGESIC LA (order 34) still short", x and x["state"] == "short", x)
        _s, x = line_state(c, 25, "FLACORT 6")
        check("FLACORT 6 (order 25) still short -- FLEMCORT never closes it (D760)", x and x["state"] == "short", x)
        carr = {r["item"]: dict(r) for r in c.execute("SELECT * FROM order_carry WHERE done_at IS NULL AND dropped_at IS NULL")}
        check("C: no open carry for THIO Q AP / ZUPRINOR 5 / POWERGESIC 100 PATCH", not ({"THIO Q AP", "ZUPRINOR 5", "POWERGESIC 100 PATCH"} & set(carr)), sorted(carr))
        lc = c.execute("SELECT qty, done_order_id FROM order_carry WHERE from_line_id=(SELECT l.id FROM purchase_order_line l WHERE l.order_id=38 AND l.item='LINVIZ 600')").fetchone()
        if lc is not None and lc["done_order_id"]:
            say("   LINVIZ 600's carry was already re-ordered on order %s before this copy -- its quantity stays as ordered" % lc["done_order_id"])
            check("C: LINVIZ 600's carry: re-ordered already (the line itself reads short 7 above)", MN is not None, None)
        else:
            check("C: LINVIZ 600's carry is 7", (carr.get("LINVIZ 600") or {}).get("qty") == 7, carr.get("LINVIZ 600"))
        # the walk's own order
        _s, x = line_state(c, oid, "W628 ZEDOL 500")
        check("C: W628 ZEDOL 500 came as W628 ZEDOL 500 TAB (a pack-word partner, price agrees: sure)", x and x["state"] == "came" and x["came"] == 10, x)
        _s, x = line_state(c, oid, "W628 BANDAGE 6*4")
        check("W628 BANDAGE 6*4 did NOT come -- the 8*4 is another size", x and x["state"] == "short", x)
        _s, x = line_state(c, oid, "W628 KARVOL 40")
        check("W628 KARVOL 40 short until the owner answers (KARVOLL is one letter apart: asked)", x and x["state"] == "short", x)
        _s, x = line_state(c, oid, "W628 MIXOL 5")
        check("C: W628 MIXOL 5 came from another dealer (W628-9), not short", x and x["state"] == "came" and x.get("how") == "other", x)
        _s, x = line_state(c, oid, "W628 NOVAX 20")
        check("C: W628 NOVAX 20 billed 3 earlier: read again, the two lines of one bill summed (3 + 2 = 5)", x and x["state"] == "came" and x["came"] == 5, x)
        if MN is not None:
            rows = {(r["form"], r["item"]): r["state"] for r in c.execute("SELECT form, item, state FROM med_name WHERE kind='marg' AND item LIKE 'W628%'")}
            check("the list: W628 ZEDOL 500 TAB = W628 ZEDOL 500 sure", rows.get(("W628 ZEDOL 500 TAB", "W628 ZEDOL 500")) == "sure", rows)
            check("the list: W628 KARVOLL 40 = W628 KARVOL 40 asked", rows.get(("W628 KARVOLL 40", "W628 KARVOL 40")) == "ask", rows)
            check("the list: no row for W628 ZEDOL 650 or a bandage size", not any("650" in f or "BANDAGE" in f for f, _i in rows), rows)
            n_scan = c.execute("SELECT COUNT(*) FROM med_name WHERE kind='scan' AND state='sure'").fetchone()[0]
            check("the September seed: the scan spellings learnt from the linked, Claude-read scans (%d)" % n_scan, n_scan >= 20, n_scan)
        c.close()

    def s_question():
        c = conn()
        q = c.execute("SELECT id FROM med_name WHERE state='ask' AND item='W628 KARVOL 40'").fetchone() if MN else None
        c.close()
        if not check("C: the owner's question exists", q is not None):
            return
        st, h = GET("manoj", P + "/s454/track")
        check("C: the owner's track page asks it (Yes / No)", st == 200 and 'data-nameq="%d"' % q[0] in h and "W628 KARVOLL 40" in h, st)
        st, h = GET("shavez", P + "/s454/track")
        check("Shavez's page does not carry the owner's question", st == 200 and 'data-nameq="%d"' % q[0] not in h, st)
        st, j = POST("shavez", P + "/api/s454/name_answer", {"id": q[0], "yes": 1})
        check("Shavez cannot answer it (403)", st == 403, (st, j))
        st, j = POST("manoj", P + "/api/s454/name_answer", {"id": q[0], "yes": 1})
        check("C: the owner's Yes", st == 200 and j.get("state") == "yes", (st, j))
        st, j = POST("manoj", P + "/api/s454/name_answer", {"id": q[0], "yes": 0})
        check("a second answer is refused (409)", st == 409, (st, j))
        c = conn()
        c.execute("UPDATE setting SET value='2000-01-01T00:00:00' WHERE key='names.last_learn'")
        c.commit()
        PO.detect_supplies(c)
        _s, x = line_state(c, O["oid"], "W628 KARVOL 40")
        check("C: after the Yes, W628 KARVOL 40 came (10)", x and x["state"] == "came" and x["came"] == 10, x)
        c.close()

    def s_pages():
        st, h = GET("manoj", P + "/s454/track")
        t = text(h)
        check("the owner's track page 200", st == 200, st)
        check("C: 'came X of Y' the right way (no '2 of 1 came' shape)", not re.search(r"\b(\d+) of (\d+) came", t) or all(int(m.group(1)) <= int(m.group(2)) for m in re.finditer(r"\b(\d+) of (\d+) came", t)),
              re.findall(r"\b\d+ of \d+ came", t)[:5])
        check("C: an arrival with none of its lines says so (W628 EMPTYCO)", "arrived — nothing on it came" in t, None)
        check("C: Send back chips on a scan the check passed (B-0181)", 'data-sbscan="181"' in h, None)
        check("C: the dealer door on B-0161", 'data-fix="161"' in h, None)
        check("C: the same paper twice: B-0150 and B-0154", 'data-same="150-154"' in h, None)
        check("C: POWERGESIC 'came from' words on the owner's page", "came from" in t and "23672" in t, None)
        hindi = [w for w in ("ne bheja", "Doctor sahab", "mein se", "aayi", "baaki maal", "nahi aaya") if w in t]
        check("no Roman Hindi on the owner's track page", not hindi, hindi)
        st, j = POST("manoj", P + "/api/s454/rescan", {"asset_bill_id": 176, "reason": "not_bill"})   # an ask by the owner: the scans page names its sender
        say("   the owner's ask on B-0176: %s %s" % (st, j.get("ok")))
        st, h = GET("manoj", P + "/s454/scans")
        t = text(h)
        check("the owner's scans page 200", st == 200, st)
        check("C: the scans page lists every pharmacy scan (folded) with Send back", 'id="sec_every"' in h, None)
        check("C: no Roman Hindi on the owner's scans page", "ne bheja" not in t and "Doctor sahab" not in t, None)
        st, h = GET("shavez", P + "/s454/track")
        check("Shavez's track page 200, in Roman Hindi", st == 200 and "Kam aaye" in text(h), st)
        for u, pth in (("alisha", P), ("alisha", P + "/s454/order"), ("alisha", P + "/s454/late"), ("alisha", P + "/s454/maal"),
                       ("darpan", "/finance/darpan/kal"), ("darpan", P), ("amir", P), ("reception", P)):
            st, h = GET(u, pth)
            leak = [w for w in ("Send back", "Change dealer", "came from", "same paper", "Names to confirm", "data-nameq", "data-fix") if w in h]
            check("staff page %s as %s renders (%s) and carries none of the owner's S628 doors" % (pth, u, st), st in (200, 302) and not leak, leak)

    def s_send_back():
        st, j = POST("darpan", P + "/api/s454/rescan", {"asset_bill_id": 181, "reason": "blurred"})
        check("Darpan cannot send a scan back (403)", st == 403, (st, j))
        st, j = POST("manoj", P + "/api/s454/rescan", {"asset_bill_id": 181, "reason": "blurred"})
        check("the owner sends B-0181 back (a scan the check passed)", st == 200 and j.get("ok"), (st, j))
        st, h = GET("manoj", P + "/s454/track")
        check("C: B-0181 now reads 'sent back for rescan ✓' with Withdraw on its order card", st == 200 and re.search(r'data-sbscan="181"[^<]*>[^<]*<span class="am">sent back', h) is not None, None)
        c = conn()
        aid = c.execute("SELECT id FROM scan_rescan_ask WHERE asset_bill_id=181 AND withdrawn_at IS NULL AND done_at IS NULL").fetchone()
        c.close()
        st, j = POST("manoj", P + "/api/s454/rescan/withdraw", {"id": aid[0] if aid else 0})
        check("the owner withdraws it", st == 200 and j.get("ok"), (st, j))

    def s_dealer():
        st, j = POST("alisha", P + "/api/s454/dealer_fix", {"scan": 161})
        check("reception cannot correct a dealer (403)", st == 403, (st, j))
        st, j = POST("darpan", P + "/api/s454/dealer_fix", {"scan": 161})
        check("Darpan cannot correct a dealer (403)", st == 403, (st, j))
        st, j = POST("manoj", P + "/api/s454/dealer_fix", {"scan": 158})
        check("a scan of the right dealer is refused (409 or 404 on OLD)", st in (409, 404), (st, j))
        st, j = POST("manoj", P + "/api/s454/dealer_fix", {"scan": 161})
        check("C: the owner corrects B-0161 to Kedar", st == 200 and "KEDAR" in str(j.get("dealer") or ""), (st, j))
        c = conn()
        tie = c.execute("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=161").fetchone()
        check("C: B-0161's tie to Shivaaz's order 28 is gone", tie is None or tie[0] != 28, tie and tuple(tie))
        ch = c.execute("SELECT value FROM s454_scan_answer WHERE asset_bill_id=161 AND kind='vendor'").fetchone()
        check("C: the corrected dealer is kept (s454_scan_answer)", ch is not None and "KEDAR" in ch[0], ch and tuple(ch))
        cs = c.execute("SELECT chosen_vendor FROM purchase_scan_state WHERE asset_bill_id=161").fetchone()
        check("C: the S440 matcher's door has it too (purchase_scan_state.chosen_vendor)", cs is not None and "KEDAR" in str(cs[0] or ""), cs and tuple(cs))
        c.close()
        st, h = GET("manoj", P + "/s454/track")
        check("C: B-0161 has left 'Saved under another dealer'", st == 200 and 'data-wrong="161"' not in h, None)
        st, j = POST("manoj", P + "/api/s454/dealer_fix", {"scan": 161})
        check("a second correction is refused (409)", st == 409, (st, j))

    section("1 the name rules (med_names)", s_units)
    section("2 detect_supplies and the carry on the copy: the four cases and the walk's own order", s_detect)
    section("3 the owner's name question", s_question)
    section("4 the pages", s_pages)
    section("5 Send back on every pharmacy scan", s_send_back)
    section("6 the dealer door", s_dealer)

    c_red = [l for l, ok in CTRL if not ok]
    if a.expect_red:
        green = [l for l, ok in CTRL if ok]
        say("NEGATIVE CONTROL: %d 'C:' checks, %d red, %d green%s" % (len(CTRL), len(c_red), len(green), (": " + "; ".join(green)) if green else ""))
        if green:
            say("WALK NEGATIVE CONTROL NOT RED S628 -- a C: check passed on the OLD files")
            sys.exit(1)
        say("WALK NEGATIVE CONTROL RED S628 (every C: check red on the OLD files)")
        return
    if FAILS:
        say("WALK FAILED S628 -- %d of %d checks: %s" % (len(FAILS), RUN[0], "; ".join(FAILS)))
        sys.exit(1)
    say("WALK OK S628 -- %d checks green, %d of them controls" % (RUN[0], len(CTRL)))


if __name__ == "__main__":
    main()
