"""walk_s760.py -- kit S760_HUB_RETURNS (Sanjeevni session 414, 09-Nov-2026, D873 / F-1200). Writes nothing outside --scratch.
Loads returns_kinds, darpan_app, finance_returns_audit and spine_read from the root under test and runs them on a COPY of finance.db
and a MADE-UP spine of the walk's own rows (every return it judges is its own, dated 2098-12 .. 2099-02).
  python walk_s760.py --root <root holding finance/ (as built, or live for the control)> --db <a COPY of finance.db> --scratch <dir>
       [--page <finance_approvals.html to draw with node>]
The control (the live files): every S760 check red, every older check green."""
import argparse, json, os, shutil, sqlite3, subprocess, sys, warnings
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--root"); ap.add_argument("--db"); ap.add_argument("--scratch"); ap.add_argument("--page")
a = ap.parse_args()
ROOT = os.path.abspath(a.root)
FIN = os.path.join(ROOT, "finance")
a.scratch = os.path.abspath(a.scratch); os.makedirs(a.scratch, exist_ok=True)
DB = os.path.join(a.scratch, "walk760.db")
shutil.copyfile(os.path.abspath(a.db), DB)
SPINE = os.path.join(a.scratch, "spine_walk760.db")
os.environ["SPINE_DB"] = SPINE
sys.path[:0] = [FIN, os.path.join(FIN, "spine")]
os.chdir(a.scratch)
res = []


def check(name, ok, s760=True, note=""):
    res.append((name, bool(ok), s760, str(note)[:400]))


def con_():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    return c


# ---- the made-up spine ----------------------------------------------------------------------------------------------------------------
sb = open(os.path.join(FIN, "spine", "spine_build.py"), encoding="utf-8").read()
SCHEMA = sb[sb.index('SCHEMA = """') + len('SCHEMA = """'):]
SCHEMA = SCHEMA[:SCHEMA.index('"""')]
if os.path.exists(SPINE):
    os.remove(SPINE)
s = sqlite3.connect(SPINE)
s.executescript(SCHEMA)
s.executemany("INSERT INTO sp_meta VALUES (?,?)", [("built", "2099-02-15T10:00:00"), ("checkable", "2099-02-14"), ("pending", "")])
for n in ("WALK ALPHA", "WALK BETA", "WALK GAMMA", "WALK DELTA", "WALK OMEGA"):
    s.execute("INSERT OR IGNORE INTO sp_item VALUES (?,?,?,?,?,?)", (n[:20], n, "1*10", "LOOSE", "2098-12-01", "2099-02-14"))
BILLS = [("2099-01-05", "A976001", 0), ("2099-01-06", "A976002", 0), ("2099-01-07", "A976003", 0), ("2099-01-08", "A976004", 0),
         ("2099-01-10", "CN97601", 1), ("2099-02-03", "CN97602", 1), ("2099-02-04", "CN97603", 1), ("2099-02-05", "CN97604", 1),
         ("2099-02-06", "CN97605", 1), ("2099-02-07", "CN97606", 1), ("2099-02-08", "CN97607", 1), ("2099-02-09", "CN97608", 1),
         ("2099-01-01", "CN97609", 1), ("2098-12-21", "CN97611", 1), ("2099-02-10", "CN97612", 1)]
for d, b, cn in BILLS:
    s.execute("INSERT INTO sp_sale_bill VALUES (?,?,?,?,?,?,?,?,?,?)", (d, b, 100000, 0, 0, 0, 100000, 100000, cn, "walk"))
LINES = [("2099-01-05", "A976001", 1, "WALK ALPHA", "1:0", 1.0, 100000, "AL1"), ("2099-01-05", "A976001", 2, "WALK BETA", "0:5", 0.5, 300000, "BE1"),
         ("2099-01-06", "A976002", 1, "WALK GAMMA", "1:0", 1.0, 30000, "GA1"), ("2099-01-07", "A976003", 1, "WALK GAMMA", "0:5", 0.5, 30000, "GA1"),
         ("2099-01-08", "A976004", 1, "WALK DELTA", "1:0", 1.0, 5000, "DE1"), ("2099-01-08", "A976004", 2, "WALK DELTA", "0:2", 0.2, 5000, "de  2 "),
         ("2099-01-10", "CN97601", 1, "WALK ALPHA", "0:5", 0.5, 100000, "AL1"), ("2099-01-10", "CN97601", 2, "WALK GAMMA", "0:3", 0.3, 30000, "GA1"),
         ("2099-02-03", "CN97602", 1, "WALK GAMMA", "0:2", 0.2, 30000, "GA1"),
         ("2099-02-04", "CN97603", 1, "WALK OMEGA", "0:1", 0.1, 20000, "ZZ9"),
         ("2099-02-05", "CN97604", 1, "WALK BETA", "0:5", 0.5, 300000, "BE1"),
         ("2099-02-06", "CN97605", 1, "WALK DELTA", "0:2", 0.2, 5000, "DE1"),
         ("2099-02-07", "CN97606", 1, "WALK ALPHA", "0:4", 0.4, 100000, "AL1"),
         ("2099-02-08", "CN97607", 1, "WALK ALPHA", "0:4", 0.4, 100000, "AL1"),
         ("2099-02-09", "CN97608", 1, "WALK GAMMA", "0:1", 0.1, 30000, "GA1"),
         ("2099-01-01", "CN97609", 1, "WALK OMEGA", "0:1", 0.1, 20000, "ZZ9"),
         ("2098-12-21", "CN97611", 1, "WALK DELTA", "0:1", 0.1, 5000, "DE1"),
         ("2099-02-10", "CN97612", 1, "WALK OMEGA", "0:1", 0.1, 20000, "ZZ9")]
for d, b, q, nm, qr, u, rate, bt in LINES:
    s.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", (d, b, q, nm, nm[:20], "1*10", qr, u, rate, bt, "1/30"))
s.commit(); s.close()

# ---- the finance side -----------------------------------------------------------------------------------------------------------------
c = con_()
c.execute("INSERT INTO patient_ref (clinic_id, name, phone_last4, first_seen) VALUES ('WALK760P1','WALK PATIENT SEVENSIXTY','0001','2098-12-01')")
c.execute("INSERT INTO patient_ref (clinic_id, name, phone_last4, first_seen) VALUES ('WALK760P2','WALK OTHERPERSON','0002','2098-12-01')")
P1 = c.execute("SELECT id FROM patient_ref WHERE clinic_id='WALK760P1'").fetchone()[0]
P2 = c.execute("SELECT id FROM patient_ref WHERE clinic_id='WALK760P2'").fetchone()[0]
DE = {}
for d in sorted({x[0] for x in BILLS} | {"2098-12-20"}):
    c.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) VALUES ('medical',?,'approved','app','walk','2099-02-15T10:00:00')", (d,))
    DE[d] = c.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (d,)).fetchone()[0]
SI = [("2099-01-05", "A976001", "pharmacy", 130000, P1), ("2099-01-06", "A976002", "pharmacy", 30000, P2),
      ("2099-01-07", "A976003", "pharmacy", 15000, P2),
      ("2099-01-10", "CN97601", "pharmacy_return", 59000, P1), ("2099-02-03", "CN97602", "pharmacy_return", 1000, P1),
      ("2099-02-04", "CN97603", "pharmacy_return", 2000, P1), ("2099-02-05", "CN97604", "pharmacy_return", 150000, P1),
      ("2099-02-07", "CN97606", "pharmacy_return", 39883, P1), ("2099-02-08", "CN97607", "pharmacy_return", 30000, P1),
      ("2099-02-09", "CN97608", "pharmacy_return", 3000, P1), ("2099-01-01", "CN97609", "pharmacy_return", 2000, P1),
      ("2098-12-20", "CN97610", "pharmacy_return", 5000, P1), ("2099-02-10", "CN97612", "pharmacy_return", 2000, P1)]
for d, b, sv, amt, pid in SI:
    c.execute("INSERT INTO sale_item (day_entry_id, unit, patient_ref_id, service, description, amount_p, mode, source, source_ref) "
              "VALUES (?,?,?,?,?,?,?,?,?)", (DE[d], "medical", pid, sv, "walk", amt, "cash", "manual", b))
c.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('returns.act_from', '2099-01-02', 'walk_s760')")
c.execute("INSERT OR IGNORE INTO darpan_return_approval (unit, cn_bill, business_date, status, decided_by, decided_at, note) "
          "VALUES ('medical','CN97612','2099-02-10','approved','manoj','2099-02-11T09:00:00','walk')")
c.commit()

import returns_kinds, finance_returns_audit as fra                    # noqa: E402
for m in (returns_kinds, fra):
    assert os.path.dirname(os.path.abspath(m.__file__)) == FIN, "%s not loaded from the root under test" % m.__name__
returns_kinds.flip(c, "medical", "CN97608", "noncash", "walk")

# ---- O: older behaviour (green on both) --------------------------------------------------------------------------------------------
try:
    notes = returns_kinds.month_notes(c, "medical", "2099-02")
    summ = returns_kinds.enrich(c, "medical", "2099-02", notes, with_prev=False)
    nb = {n["bill"]: n for n in notes}
    check("O1 month_notes + enrich (cn-detail's road) still answer: February's eight returns, the pending count from the S406 rule",
          len(notes) == 8 and summ["pending_ok"] == 3, s760=False, note=(len(notes), summ["pending_ok"], sorted(nb)))
    check("O2 enrich's old fields stand: CN97606's shortfall is carried (117) and its status is ok; CN97607 reads 'discounted'",
          nb["CN97606"]["refund_shortfall_p"] == 117 and nb["CN97606"]["status"] == "ok" and nb["CN97607"]["status"] == "discounted",
          s760=False, note=(nb["CN97606"].get("refund_shortfall_p"), nb["CN97606"].get("status"), nb["CN97607"].get("status")))
    check("O3 month_fields (the Month table's returns columns) still answer", isinstance(returns_kinds.month_fields(c, "medical", "2099-02"), dict), s760=False)
except Exception as e:                                                # noqa: BLE001
    check("O0 the S406 read layer answers", False, s760=False, note=repr(e))

# ---- F: F-1200 inside enrich (the cn-detail road the month view draws) ------------------------------------------------------------
try:
    check("F1 F-1200: CN97606's ₹1.17 shortfall is under the rounding line -- short_noise true", nb["CN97606"].get("short_noise") is True, note=nb["CN97606"].get("short_noise"))
    check("F2 F-1200: CN97607's ₹100 shortfall is over it -- short_noise false (the badge stays)", nb["CN97607"].get("short_noise") is False, note=nb["CN97607"].get("short_noise"))
except Exception as e:                                                # noqa: BLE001
    check("F0 short_noise", False, note=repr(e))

# ---- H: the hub read -------------------------------------------------------------------------------------------------------------------
H = None
try:
    H = returns_kinds.hub(c, "medical", today="2099-02-15")
except Exception as e:                                                # noqa: BLE001
    check("H0 returns_kinds.hub answers", False, note=repr(e))
if H:
    R = {r["bill"]: r for m in H["months"] for r in m["rows"]}
    check("H1 every month newest first: February (current, open) and January; December 2098 is history, counted 2 (a bill row and an orphan's lines)",
          [m["ym"] for m in H["months"]] == ["2099-02", "2099-01"] and H["months"][0]["current"] and not H["months"][1]["current"]
          and [(x["ym"], x["n"]) for x in H["history"] if x["ym"].startswith("2098")] == [("2098-12", 2)],
          note=([m["ym"] for m in H["months"]], [(x["ym"], x["n"]) for x in H["history"]][:4]))
    check("H2 Needs your OK: every month together, newest first -- CN97604, CN97603, CN97602 (February) then CN97601 (January); 4 in all",
          [k.split("|")[1] for k in H["needs"]] == ["CN97604", "CN97603", "CN97602", "CN97601"] and H["pending_ok"] == 4, note=H["needs"])
    r1 = R["CN97601"]
    check("H3 CN97601 names only the medicine in question: GAMMA, 1 of 2 items, ₹ in question = its line (0:3 of ₹300 a strip = ₹90); ALPHA folded as bought",
          [x["item"] for x in r1["in_question"]] == ["WALK GAMMA"] and r1["n_items"] == 2 and r1["q_p"] == 9000
          and [g["item"] for g in r1["bought"]] == ["WALK ALPHA"] and r1["whys"] == ["not bought by this patient"], note=r1)
    check("H4 the batch check: GAMMA batch GA1 was sold twice in 180 days (two bills of another patient) -- a count; OMEGA ZZ9 never sold -- 0",
          r1["in_question"][0]["batch_sold"] == 2 and R["CN97603"]["in_question"][0]["batch_sold"] == 0 and H["batch_check"] is True,
          note=(r1["in_question"][0], R["CN97603"]["in_question"][0]))
    blob = json.dumps(H, ensure_ascii=False)
    check("H5 no other patient leaves the door: the read carries neither the other patient's name nor his ID nor any sale bill number",
          "OTHERPERSON" not in blob and "WALK760P2" not in blob and not any(b in blob for b in ("A976001", "A976002", "A976003", "A976004")))
    check("H6 repeats: GAMMA batch GA1 is in 2 of the waiting returns (10-Jan, 03-Feb), named once; its lines carry the ↻ mark",
          [(x["item"], x["batch"], x["n"], x["days"]) for x in H["repeats"]] == [("WALK GAMMA", "GA1", 2, ["10-Jan", "03-Feb"])]
          and R["CN97602"]["in_question"][0]["repeat"] and r1["in_question"][0]["repeat"], note=H["repeats"])
    r4 = R["CN97604"]
    check("H7 CN97604 (₹1,500, everything bought): the whole return in question, ₹1,000+, recover = the refund",
          r4["whole"] and r4["big"] and r4["recover_p"] == 150000 and r4["q_p"] == 150000 and r4["pending_ok"], note=r4)
    check("H8 Reject never recovers more than was refunded: CN97602's line is worth ₹60, the refund ₹10 -- recover ₹10",
          R["CN97602"]["q_p"] == 6000 and R["CN97602"]["recover_p"] == 1000, note=(R["CN97602"]["q_p"], R["CN97602"]["recover_p"]))
    check("H9 can't be checked yet: CN97605 alone (no patient on the bill)",
          [k.split("|")[1] for k in H["cant"]] == ["CN97605"] and R["CN97605"]["cant"] == "no patient on the bill", note=(H["cant"], R["CN97605"]["cant"]))
    check("H10 F-1200 on the card: CN97606's ₹1.17 is not shown at all (no shortfall, ✓ bought by the patient)",
          R["CN97606"]["short_p"] is None and R["CN97606"]["word"] == "✓ bought by the patient" and R["CN97606"]["tone"] == "ok", note=R["CN97606"])
    check("H11 CN97607's ₹100 is shown: 'refund ₹100 short'", R["CN97607"]["short_p"] == 10000 and R["CN97607"]["word"] == "refund ₹100 short", note=R["CN97607"]["word"])
    check("H12 the owner's own non-cash return: not asked, named as his", R["CN97608"]["kind"] == "noncash" and not R["CN97608"]["pending_ok"]
          and "non-cash" in R["CN97608"]["word"] and H["months"][0]["noncash_n"] == 1, note=R["CN97608"]["word"])
    check("H13 before the rules (01-Jan, act_from 02-Jan): kept, never asked", R["CN97609"]["historical"] and not R["CN97609"]["pending_ok"], note=R["CN97609"])
    check("H14 an approved one reads '✓ approved by you' and counts as fine", R["CN97612"]["word"] == "✓ approved by you" and H["months"][0]["fine"] >= 2,
          note=(R["CN97612"]["word"], H["months"][0]["fine"]))
    feb = H["months"][0]
    check("H15 February's fold line: 8 returns, 3 need your OK, 1 can't be checked, 1 discounted, 1 non-cash not in purchases",
          (feb["n"], feb["need"], feb["cant"], feb["discounted"], feb["noncash_bad"]) == (8, 3, 1, 1, 1),
          note=(feb["n"], feb["need"], feb["cant"], feb["discounted"], feb["noncash_bad"]))
    check("H16 the GET reads only: no approval row written by the hub (the decisions stay cn-approve's)",
          c.execute("SELECT COUNT(*) FROM darpan_return_approval WHERE cn_bill LIKE 'CN976%'").fetchone()[0] == 1)

# ---- N: the Needs-you returns line reads the card's own count (one source) ----------------------------------------------------------
if True:
    HP = H or {}
    try:
        import sanjeevni_approvals as sa                              # noqa: E402
        assert os.path.dirname(os.path.abspath(sa.__file__)) == FIN, "sanjeevni_approvals not from the root under test"
        fn = getattr(sa, "_s760_returns_line", None)
        ln = fn(c, "2099-02-15") if fn else None
        check("N1 the Needs-you returns line counts exactly what the card counts: 4 on the fixture (the card's pending_ok)",
              bool(ln) and ln.get("n") == HP.get("pending_ok") == 4, note=ln)
        check("N2 its words match the card: 'Returns waiting for your OK — 4 · ₹2,120 · oldest 10-Jan' (the card's header: 4, ₹2,120)",
              bool(ln) and ln.get("text") == "Returns waiting for your OK — 4 · ₹2,120 · oldest 10-Jan" and HP.get("pending_ok_rupees") == 2120, note=(ln, HP.get("pending_ok_rupees")))
        keep_hub = getattr(returns_kinds, "hub", None)
        returns_kinds.hub = lambda *x, **k: (_ for _ in ()).throw(RuntimeError("walk: the card's read failed"))
        ln2 = fn(c, "2099-02-15") if fn else None
        if keep_hub is None:
            del returns_kinds.hub
        else:
            returns_kinds.hub = keep_hub
        old = sa._s446_returns_line(c, "2099-02-15")
        check("N3 if the card's read fails, the line falls back to the S446 line exactly as it was (fail-soft)",
              fn is not None and bool(old) and ln2 == old and "Counter returns waiting" in old.get("text", ""), note=(ln2, old))
        src_sa = open(os.path.join(FIN, "sanjeevni_approvals.py"), encoding="utf-8").read()
        check("N4 needs_you() takes its returns line from _s760_returns_line (the S446 line only behind it)",
              "    rl = _s760_returns_line(con, today)" in src_sa and "    rl = _s446_returns_line(con, today)" not in src_sa)
        os.environ["NEEDS_YOU_WITHOUT_S406"] = "1"
        ln3 = fn(c, "2099-02-15") if fn else "absent"
        del os.environ["NEEDS_YOU_WITHOUT_S406"]
        check("N5 an older kit's frozen walk (NEEDS_YOU_WITHOUT_S406=1) still gets the old path (None)", ln3 is None, note=ln3)
        try:
            hl = returns_kinds.hub(c, "medical", today="2099-02-15", light=True)
            ok6 = ((hl["needs"], hl["pending_ok_p"], hl["pending_oldest"]) == (HP.get("needs"), HP.get("pending_ok_p"), HP.get("pending_oldest"))
                   and hl["history"] == [] and hl["batch_check"] is False)
        except Exception as e6:                                       # noqa: BLE001
            hl, ok6 = repr(e6), False
        check("N6 the light read gives the same needs, amount and oldest as the full read (no batch look-up, no history count)", ok6, note=str(hl)[:200])
    except Exception as e:                                            # noqa: BLE001
        check("N0 the Needs-you line answers", False, note=repr(e))

# ---- B: the batch compared the same way on both sides (the spine's column normalised in SQL as batch_norm does) -----------------
try:
    import spine_read                                                 # noqa: E402
    spx = spine_read.Spine(SPINE)
    b1 = returns_kinds.batch_sold(spx, "WALK DELTA", "DE 2", "2099-02-06", 180)
    b2 = returns_kinds.batch_sold(spx, "WALK DELTA", "  de   2", "2099-02-06", 180)
    check("BN1 the batch match normalises both sides alike: the spine's 'de  2 ' is found as 'DE 2' and as '  de   2' (1 sale each)", b1 == 1 and b2 == 1, note=(b1, b2))
except Exception as e:                                                # noqa: BLE001
    check("BN1 the batch match normalises both sides alike", False, note=repr(e))

# ---- R: repeats found and shown by the same normalisation as the batch match ---------------------------------------------------------
try:
    src_rk = open(os.path.join(FIN, "returns_kinds.py"), encoding="utf-8").read()
    check("R1 repeats use batch_norm, the match's own normalisation ('  ga   1 ' -> 'GA 1'), for the key, the skip and the mark",
          returns_kinds.batch_norm("  ga   1 ") == "GA 1" and 'if not batch_norm(x["batch"]):' in src_rk
          and src_rk.count('batch_norm(x["batch"])') >= 3, note=src_rk.count('batch_norm(x["batch"])'))
except Exception as e:                                                # noqa: BLE001
    check("R1 repeats use batch_norm", False, note=repr(e))

# ---- W: no new GET writes -- the hub and the Needs-you line read on a READ-ONLY connection --------------------------------------------
try:
    cro = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=30)
    cro.row_factory = sqlite3.Row
    hro = returns_kinds.hub(cro, "medical", today="2099-02-15")
    hlo = returns_kinds.hub(cro, "medical", today="2099-02-15", light=True)
    import sanjeevni_approvals as sa_ro                               # noqa: E402
    lro = sa_ro._s760_returns_line(cro, "2099-02-15")
    cro.close()
    check("W1 the hub (full and light) and the Needs-you line answer on a READ-ONLY connection -- they write nothing (4 waiting each)",
          len(hro["needs"]) == 4 and len(hlo["needs"]) == 4 and isinstance(lro, dict) and lro.get("n") == 4, note=(len(hro["needs"]), lro))
except Exception as e:                                                # noqa: BLE001
    check("W1 the hub and the Needs-you line answer on a READ-ONLY connection", False, note=repr(e))

# ---- U: an amount the engine could not read is never 'recover ₹0' ----------------------------------------------------------------------
try:
    stx = returns_kinds.settings(c)
    nx = dict(date="2099-02-12", bill="CN97699", amount_p=5000, verdict="NEVER BOUGHT", status="your OK", pending_ok=True, kind="counter",
              historical=False, approval=None, refund_shortfall_p=None, audit_lines=[dict(item="WALK OMEGA", qty_raw="?", pack="1*10",
              amount_line_p=None, batch="", verdict="NEVER BOUGHT", detail="")])
    sx = returns_kinds._s760_shape(c, stx, nx, None, 180, False)
    check("U1 a line whose money could not be computed: no amount in question, nothing to recover, said so (amount_unread)",
          sx["q_p"] is None and sx["recover_p"] is None and sx["amount_unread"] is True, note=sx)
except Exception as e:                                                # noqa: BLE001
    check("U1 an unreadable amount is never 'recover ₹0'", False, note=repr(e))

# ---- E: the door, through Flask -------------------------------------------------------------------------------------------------------
try:
    from flask import Flask                                           # noqa: E402
    import darpan_app                                                  # noqa: E402
    assert os.path.dirname(os.path.abspath(darpan_app.__file__)) == FIN
    WHO = {"user": "manoj"}
    app = Flask("walk760")
    darpan_app.init(app, lambda: con_(), lambda role: (dict(WHO), None), unit="medical")
    import sanjeevni_approvals as sa_w                                # noqa: E402 -- registered before the first request
    sa_w.init(app, lambda: con_(), lambda role: (dict(WHO), None), unit="medical")
    cl = app.test_client()
    owner = sorted(darpan_app._owners(c))[0]
    WHO["user"] = owner
    r = cl.get("/finance/darpan/api/cn-hub")
    j = r.get_json(silent=True) or {}
    check("E1 GET /finance/darpan/api/cn-hub answers 200, ok, owner true, with months / needs / spot_checks",
          r.status_code == 200 and j.get("ok") and j.get("owner") is True and "months" in j and "spot_checks" in j, note=(r.status_code, str(j)[:200]))
    WHO["user"] = "walk_not_owner_760"
    j2 = cl.get("/finance/darpan/api/cn-hub").get_json(silent=True) or {}
    check("E2 a checker who is not the owner reads it with owner false (the page then shows no buttons)", j2.get("ok") and j2.get("owner") is False, note=str(j2)[:200])
    WHO["user"] = owner
    keep = getattr(returns_kinds, "hub", None)
    returns_kinds.hub = lambda *x, **k: (_ for _ in ()).throw(RuntimeError("walk: hub down"))
    r3 = cl.get("/finance/darpan/api/cn-hub")
    if keep is None:
        del returns_kinds.hub
    else:
        returns_kinds.hub = keep
    check("E3 the hub failing answers 503 with a reason (the page falls back to the month view)", r3.status_code == 503 and (r3.get_json() or {}).get("ok") is False)
    r4 = cl.get("/finance/darpan/api/cn-detail?month=2099-02")
    j4 = r4.get_json(silent=True) or {}
    # W2: cn_kind's row count is unchanged by the cn-hub GET and the needs-you GET (dates shimmed to the fixture's 15-Feb-2099)
    import datetime as _rdt
    class _D(_rdt.date):
        @classmethod
        def today(cls):
            return _rdt.date(2099, 2, 15)
    class _Shim:
        date, timedelta, datetime = _D, _rdt.timedelta, _rdt.datetime
    keep_dt, keep_today = returns_kinds.dt, sa_w._today
    try:
        returns_kinds.dt = _Shim
        sa_w._today = lambda: "2099-02-15"
        n0 = c.execute("SELECT COUNT(*) FROM cn_kind").fetchone()[0]
        g1 = cl.get("/finance/darpan/api/cn-hub")
        g2 = cl.get("/finance/sanjeevni/api/needs-you")
        n1 = c.execute("SELECT COUNT(*) FROM cn_kind").fetchone()[0]
        j1, j2 = (g1.get_json(silent=True) or {}), (g2.get_json(silent=True) or {})
        rl = [x for x in (j2.get("lines") or []) if x.get("target") == "returns"]
    finally:
        returns_kinds.dt, sa_w._today = keep_dt, keep_today
    check("W2 no new GET writes: cn_kind holds %d rows before and after GET cn-hub (4 waiting) and GET needs-you (its line: 4)" % n0,
          g1.status_code == 200 and len(j1.get("needs") or []) == 4 and g2.status_code == 200 and n0 == n1 and len(rl) == 1 and rl[0].get("n") == 4,
          note=(g1.status_code, g2.status_code, n0, n1, rl))
    # A: a return only the spine holds (CN97605, the orphan) can be decided -- Approve, then Reject
    a1 = cl.post("/finance/darpan/api/cn-approve", json=dict(bill="CN97605", decision="approved", note="walk"))
    ra = c.execute("SELECT business_date, status FROM darpan_return_approval WHERE unit='medical' AND cn_bill='CN97605'").fetchone()
    check("A1 Approve on the spine-only return CN97605 answers 200 and records it on its spine date (06-Feb)",
          a1.status_code == 200 and ra is not None and tuple(ra) == ("2099-02-06", "approved"), note=(a1.status_code, tuple(ra) if ra else None))
    c.execute("DELETE FROM darpan_return_approval WHERE unit='medical' AND cn_bill='CN97605'"); c.commit()
    a2 = cl.post("/finance/darpan/api/cn-approve", json=dict(bill="CN97605", decision="rejected", note="recover ₹10 (WALK DELTA) — walk"))
    rr = c.execute("SELECT business_date, status FROM darpan_return_approval WHERE unit='medical' AND cn_bill='CN97605'").fetchone()
    check("A2 Reject on the spine-only return CN97605 answers 200 and records it rejected",
          a2.status_code == 200 and rr is not None and tuple(rr) == ("2099-02-06", "rejected"), note=(a2.status_code, tuple(rr) if rr else None))
    src_da = open(os.path.join(FIN, "darpan_app.py"), encoding="utf-8").read()
    rb = c.execute("SELECT cn_bill FROM darpan_return_approval WHERE unit='medical' AND cn_bill LIKE 'CN97605%'").fetchall()
    check("A4 the spine fallback matches the bill exactly as cn-approve holds it (no extra upper-casing) and the row stores that same bill",
          "WHERE bill=? AND credit_note=1" in src_da and "UPPER(bill)=?" not in src_da and [tuple(x) for x in rb] == [("CN97605",)], note=[tuple(x) for x in rb])
    a3 = cl.post("/finance/darpan/api/cn-approve", json=dict(bill="CN99999", decision="approved", note="walk"))
    check("A3 a bill nobody holds still answers 404 (the old behaviour)", a3.status_code == 404, s760=False, note=a3.status_code)
    check("E4 cn-detail itself unchanged: 200, kinds present, its own day discovery (sale_line_item + sale_item, not the spine) -- 7 of the 8: the spine-only orphan CN97605 is the hub's alone", r4.status_code == 200 and j4.get("count") == 7 and "counter" in (j4.get("kinds") or {}),
          s760=False, note=(r4.status_code, j4.get("count")))
except Exception as e:                                                # noqa: BLE001
    check("E0 the door answers", False, note=repr(e))

# ---- J: the page draws it (node, the page's own script) -------------------------------------------------------------------------
if a.page and H:
    try:
        page = open(a.page, encoding="utf-8").read()
        js = page[page.rindex("<script>") + 8:page.rindex("</script>")]
        has = "function rhRender(" in js
        check("J0 the page carries the S760 renderer and cnMsg / hidden cnMonth; the month picker is gone", has and 'id="cnMsg"' in page
              and '<input type="hidden" id="cnMonth"' in page and 'type="month" id="cnMonth"' not in page)
        if has and not shutil.which("node"):
            print("  --  J1-J7 not run: node is not on this machine (the drawing was proved where it is)")
        if has and shutil.which("node"):
            H2 = json.loads(json.dumps(H)); H2["owner"] = True; H2["spot_checks"] = []
            start = js.index("/* ==== KIT_S760"); end = js.index("/* ==== end KIT_S760 ==== */")
            prelude = ("var document={getElementById:function(){return null}};function $(i){return null}\n"
                       "function esc(s){return (s==null?'':String(s)).replace(/[&<>\"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]})}\n")
            prog = prelude + js[start:end] + "\nRH=" + json.dumps(H2, ensure_ascii=False) + ";\nprocess.stdout.write(rhRender(RH));\n"
            open(os.path.join(a.scratch, "draw760.js"), "w", encoding="utf-8").write(prog)
            out = subprocess.run(["node", os.path.join(a.scratch, "draw760.js")], capture_output=True, text=True, timeout=60)
            o = out.stdout
            open(os.path.join(a.scratch, "draw760.html"), "w", encoding="utf-8").write(o)
            check("J1 drawn: 'Needs your OK — 4' with ₹2,120 (the Needs-you line's figure), the repeats line, CN97604 first in the table", "Needs your OK — 4" in o and "₹2,120 returned" in o and "Repeats:</b> WALK GAMMA batch GA1 is in 2 of these (10-Jan, 03-Feb)" in o
                  and o.index("CN97604") < o.index("CN97603") < o.index("CN97602") < o.index("CN97601"), note=out.stderr[:300] or o[:300])
            check("J2 drawn: the amber count (sold by us 2 times) and the red 'never sold' for ZZ9", "sold by us 2 times in the last 180 days" in o and "we never sold batch ZZ9" in o)
            check("J3 drawn: 'Can't be checked yet — 1', the months newest first (February open), history 'before your returns rules began on 02-Jan'",
                  "Can't be checked yet — 1" in o and o.index("February 2099") < o.index("January 2099") and "before your returns rules began on 02-Jan" in o)
            check("J4 drawn: no '₹1.17 withheld' anywhere; '₹100 withheld on the refund' / 'refund ₹100 short' present", "1.17" not in o and "refund ₹100 short" in o)
            check("J5 drawn: Approve / Reject on the waiting lines (owner), 'Reject — recover ₹10' inside CN97602", o.count('rhDecide(') >= 8 and "Reject — recover ₹10<" in o)
            H3 = json.loads(json.dumps(H2)); H3["owner"] = False
            prog2 = prelude + js[start:end] + "\nRH=" + json.dumps(H3, ensure_ascii=False) + ";\nprocess.stdout.write(rhRender(RH));\n"
            open(os.path.join(a.scratch, "draw760b.js"), "w", encoding="utf-8").write(prog2)
            o2 = subprocess.run(["node", os.path.join(a.scratch, "draw760b.js")], capture_output=True, text=True, timeout=60).stdout
            check("J6 not the owner: no decision buttons drawn", "rhDecide(" not in o2 and "the doctor" in o2)
            H4 = json.loads(json.dumps(H2))
            for m_ in H4["months"]:
                for r_ in m_["rows"]:
                    if r_["bill"] == "CN97603":
                        r_["in_question"][0]["amount_p"] = None; r_["q_p"] = None; r_["recover_p"] = None; r_["amount_unread"] = True
                    if r_["bill"] == "CN97601":
                        r_["in_question"][0]["item"] = "WALK O'QUOTE <b>"
            prog3 = prelude + js[start:end] + "\nRH=" + json.dumps(H4, ensure_ascii=False) + ";\nprocess.stdout.write(rhRender(RH));\n"
            open(os.path.join(a.scratch, "draw760c.js"), "w", encoding="utf-8").write(prog3)
            o3 = subprocess.run(["node", os.path.join(a.scratch, "draw760c.js")], capture_output=True, text=True, timeout=60).stdout
            check("J8 an unreadable amount: 'amount could not be read', a plain 'Reject', never 'recover ₹0' or 'recover —'",
                  "amount could not be read" in o3 and "recover ₹0" not in o3 and "recover —" not in o3 and ">Reject</button>" in o3, note=o3[:200])
            check("J9 the card escapes ' too, and no value sits inside a quoted onclick string",
                  "WALK O&#39;QUOTE &lt;b&gt;" in o3 and "O'QUOTE" not in o3 and "onclick=\"rhToggle('" not in o3 and "rhDecide('" not in o3 and "rhOlder('" not in o3, note=o3[:200])
            check("J7 the old view stays: loadCN406 and loadCNOld both present, loadCN once", js.count("function loadCN(){") == 1 and "function loadCN406(){" in js and "function loadCNOld(){" in js)
    except Exception as e:                                            # noqa: BLE001
        check("J0 the page draws", False, note=repr(e))
elif a.page:
    check("J0 the page carries the S760 renderer", "function rhRender(" in open(a.page, encoding="utf-8").read())
c.close()

for n, ok, s_, note in res:
    print(("  ok  " if ok else "  RED ") + n + ("" if ok else ("   | " + note if note else "")))
red = sum(1 for _, ok, s_, _ in res if not ok and s_); redold = sum(1 for _, ok, s_, _ in res if not ok and not s_)
print("walk_s760: %d check(s) failed (%d of them S760 checks)" % (red + redold, red))
