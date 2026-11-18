"""synth_s867.py <finance dir under test> <finance.db COPY> [--real] -- kit S867_CONFIRM_WORDS proof. Works on COPIES only.
 October 2026 of the copy holds the one owner-confirmed dealer (Ravi Medical Agency, his Confirm given 08-Nov): the payment sheet, the dealer
 ledger and row 7 say 'settled by your confirmation'; with the Confirm taken away (on the copy) they say 'waiting for your confirmation';
 an unreadable tally says 'see the purchase check, row 3', never green; nothing but those words changes, in any month. --real: every counted
 month's payment sheet, purchase check and the owner-confirmed dealers' ledgers draw, and 'your Confirm' is gone from them -- no frozen
 expectations. Last line: 'SYNTH S867: n PASS, m FAIL'."""
import os, shutil, sqlite3, sys, tempfile
FIN, DBC = sys.argv[1], sys.argv[2]
REAL = "--real" in sys.argv
tmp = tempfile.mkdtemp(prefix="s867synth_")
code = os.path.join(tmp, "finance")
shutil.copytree(FIN, code, ignore=shutil.ignore_patterns("*.db", "__pycache__", "_off"))
_me = os.path.dirname(os.path.abspath(__file__))           # F-1415: never the kit's own copy beside this script
sys.path[:] = [x for x in sys.path if os.path.abspath(x or os.getcwd()) != _me]
sys.path.insert(0, code)
P = F = 0
M = "2026-10"
SETTLED, WAITING = "settled by your confirmation", "waiting for your confirmation (purchase check, row 3)"


def ok(c, what):
    global P, F
    if c:
        P += 1
        print("PASS", what)
    else:
        F += 1
        print("FAIL", what)


def fresh():
    db = os.path.join(tmp, "f%d.db" % (P + F))
    shutil.copy(DBC, db)
    con = sqlite3.connect(db, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


try:
    import purchase_app as pa                                 # noqa: E402
    import scan_register as SR                                # noqa: E402
    import month_asks as ma                                   # noqa: E402
    from flask import Flask                                   # noqa: E402
    have = True
except Exception as e:                                        # noqa: BLE001
    print("import:", e)
    have = False
ok(have, "T0 the finance code under test imports")


def get(con, path):
    app = Flask("s867_%d" % (P + F))
    pa.init(app, lambda: con, lambda *roles: (dict(user="manoj", roles=["checker"], role="checker"), None), assets_db="/nonexistent")
    r = app.test_client().get(path)
    return r.status_code, r.get_data(as_text=True)


def conf_keys(con, m):
    try:
        return [k for k in SR._s749_owner_sups(con) if k]
    except Exception:                                         # noqa: BLE001
        return []


def counted(con):
    return [m for m in ma.months(con) if SR.month_class(con, m) == "counted"]


if have and REAL:
    con = fresh()
    try:
        res = []
        for m in counted(con):
            c1, pay = get(con, "/finance/purchase/page/pay/%s" % m)
            c2, chk = get(con, "/finance/purchase/page/check?month=%s" % m)
            led = [get(con, "/finance/purchase/page/ledger/%s" % k) for k in conf_keys(con, m)]
            bad = [x for x in [pay, chk] + [b for _c, b in led] if "your Confirm" in x]
            res.append((m, c1, c2, [c for c, _b in led], len(bad)))
        ok(res and all(c1 == 200 and c2 == 200 and all(c == 200 for c in lc) and nb == 0 for _m, c1, c2, lc, nb in res),
           "R1 the live copy: every counted month's payment sheet, purchase check and the owner-confirmed dealers' ledgers draw; 'your Confirm' gone (%r)" % (res,))
    except Exception as e:                                    # noqa: BLE001
        ok(False, "R1 the live copy: %r" % (e,))
    con.close()

if have:
    con = fresh()
    K = "RAVI MEDICAL AGENCY"
    sh = SR.s750_sheet(con, M)
    ds = [d for d in SR.s750_dealers(con, M) if d["key"] == K]
    have_case = K in sh and sh[K].get("state") == "confirm" and ds
    if not have_case:
        ok(False, "T1 the copy's October has no owner-confirmed dealer to prove on (%r)" % (sh.get(K),))
    else:
        ok(sh[K]["words"] == SETTLED and pa._s750_chip(sh[K]) == ' <span class="chip ok">settled by your confirmation</span>'
           and ds[0]["words"].startswith("Settled by your confirmation — it stands as the summary · Marg ₹"),
           "T1 his Confirm given: the sheet's chip 'settled by your confirmation' (green); the ledger/row 7 words say so (%r / %r)" % (sh[K]["words"], ds[0]["words"]))
        c1, pay = get(con, "/finance/purchase/page/pay/%s" % M)
        c2, chk = get(con, "/finance/purchase/page/check?month=%s" % M)
        c3, led = get(con, "/finance/purchase/page/ledger/%s" % K)
        ok(c1 == 200 and '<span class="chip ok">settled by your confirmation</span>' in pay and "your Confirm" not in pay
           and c2 == 200 and "Settled by your confirmation — it stands as the summary" in chk and "your Confirm" not in chk
           and c3 == 200 and "your Confirm" not in led,
           "T2 the real pages: payment sheet, purchase check (row 7) and Ravi's ledger say settled; 'your Confirm' nowhere (%d/%d/%d)" % (c1, c2, c3))
        # nothing else changes: every counted month, every dealer, every field but the words of a confirm-state dealer
        diff = [] if hasattr(SR, "_s750_sheet_before_s867") else [("control", "no S867 seam")]
        for m in (counted(con) if not diff else []):
            a, b = SR._s750_sheet_before_s867(con, m), SR.s750_sheet(con, m)
            if set(a) != set(b):
                diff.append((m, "keys"))
            for k in a:
                x, y = dict(a[k]), dict(b.get(k) or {})
                if x.get("state") == "confirm":
                    x.pop("words", None), y.pop("words", None)
                if x != y:
                    diff.append((m, k))
            da, db_ = SR._s750_dealers_before_s867(con, m), SR.s750_dealers(con, m)
            if len(da) != len(db_) or any({kk: vv for kk, vv in p.items() if kk != "words"} != {kk: vv for kk, vv in q.items() if kk != "words"} for p, q in zip(da, db_)):
                diff.append((m, "dealers"))
            if any(p["words"] != q["words"] and p["state"] != "confirm" for p, q in zip(da, db_)):
                diff.append((m, "words of a non-confirm dealer"))
        ok(not diff and counted(con), "T3 nothing but those words changes: every counted month (%d), every dealer, state/figures/holds/payable the same (%r)" % (len(counted(con)), diff[:5]))
        con.execute("DELETE FROM s749_confirm")
        con.commit()
        sh2 = SR.s750_sheet(con, M)
        d2 = [d for d in SR.s750_dealers(con, M) if d["key"] == K]
        c1, pay2 = get(con, "/finance/purchase/page/pay/%s" % M)
        ok(sh2[K]["words"] == WAITING and "chip warn" in pa._s750_chip(sh2[K]) and d2 and d2[0]["words"].startswith("Waiting for your confirmation on row 3 of the purchase check")
           and c1 == 200 and '<span class="chip warn">waiting for your confirmation (purchase check, row 3)</span>' in pay2,
           "T4 his Confirm not given (taken away on the copy): 'waiting for your confirmation (purchase check, row 3)', amber, on the sheet; the ledger words too")
        real = SR._s749_groups

        def boom(*a, **k):
            raise RuntimeError("made up")
        SR._s749_groups = boom
        try:
            sh3 = SR.s750_sheet(con, M)
            d3 = [d for d in SR.s750_dealers(con, M) if d["key"] == K]
        finally:
            SR._s749_groups = real
        ok(sh3[K]["words"] == "your confirmation — see the purchase check, row 3" and "chip ok" not in pa._s750_chip(sh3[K])
           and d3 and d3[0]["words"].startswith("Your confirmation stands as the summary — see row 3"),
           "T5 the tally unreadable: 'see the purchase check, row 3', never green")
        ok(hasattr(SR, "_S867_IN") and not getattr(SR._S867_IN, "on", False), "T6 the re-entry guard is off after every call")
    con.close()
    src = open(os.path.join(code, "scan_register.py"), encoding="utf-8").read()
    ok("_s750_sheet_before_s867 = s750_sheet" in src and "_s750_dealers_before_s867 = s750_dealers" in src, "T7 the seam: s750_sheet and s750_dealers, one tally")
print("SYNTH S867: %d PASS, %d FAIL" % (P, F))
