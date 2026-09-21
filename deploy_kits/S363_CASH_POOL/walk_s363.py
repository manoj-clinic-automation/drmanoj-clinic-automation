#!/usr/bin/env python3
"""walk_s363.py -- kit S363_CASH_POOL (the pool: an approved day's cash went to the doctors' pool). Runs the REAL app twice over the SAME scratch copy of
finance.db (never the live one) -- once with the live files (--before), once with the patched
files (--after) -- and prints every Sanjeevni cash figure each screen serves, side by side.
Passes only if the patched screens all agree with the one calculation (sanjeevni_cash) and with
one another, the clinic unit's screens are byte-identical, and the cash log asks nothing about
August. Prints dates, counts and rupees only.

  python3 walk_s363.py --before DIR --after DIR --db scratch.db
"""
import argparse, importlib, json, os, sqlite3, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("--before", required=True); ap.add_argument("--after", required=True)
ap.add_argument("--db", required=True); ap.add_argument("--probe", action="store_true")
ap.add_argument("--pdf", help="optional: the owner's real Yes Bank statement, to prove the two pool deposits match it")
ap.add_argument("--unseeded", help="a second scratch copy WITHOUT the S361 tables: every answer must be identical before and after")
a = ap.parse_args()

PROBE = r'''
import io, json, os, sys
sys.path.insert(0, os.environ["APPDIR"])
os.environ.update(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="manoj", FINANCE_DEV_ROLE="owner")
import finance_app as fa
c = fa.app.test_client()
H = {"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"}
out = {}
def get(u):
    r = c.get(u, headers=H)
    try:
        return r.status_code, r.get_json()
    except Exception:
        return r.status_code, None
s, j = get("/finance/api/cash-position"); out["cash_position"] = [s, {k: (j or {}).get(k) for k in ("drawer","reserve","with_manoj","unbanked","as_of","basis","last_bank_date","waiting_days")}]
s, j = get("/finance/api/days?ym=2026-09"); out["days_sep"] = [s, {d["date"]: d["closing"] for d in (j or {}).get("days", [])}]
s, j = get("/finance/api/days?ym=2026-08"); out["days_aug"] = [s, {d["date"]: d["closing"] for d in (j or {}).get("days", [])}]
s, j = get("/finance/api/workbench/2026-08"); out["workbench_aug"] = [s, {d["date"]: d["closing"] for d in (j or {}).get("days", [])}, (j or {}).get("custody", {}).get("held")]
s, j = get("/finance/api/month?ym=2026-09"); out["month_grid_sep"] = [s, {d["date"]: d["closing"] for d in (j or {}).get("days", []) if d.get("closing")}]
s, j = get("/finance/api/custody"); out["custody_held"] = [s, (j or {}).get("held")]
s, j = get("/finance/api/where-is-the-cash"); out["where_is_the_cash"] = [s, (j or {}).get("parked"), (j or {}).get("parked_total")]
s, j = get("/finance/api/tile"); out["tile"] = [s, (j or {}).get("cash_in_hand"), (j or {}).get("last_bank_deposit")]
for d in ("2026-08-17", "2026-08-31", "2026-09-14"):
    s, j = get("/finance/api/day/" + d); out["day_" + d] = [s, {k: ((j or {}).get("day") or j or {}).get(k) for k in ("opening", "closing")}]
s, j = get("/finance/darpan/api/card?date=2026-08-31"); out["darpan_card_31aug"] = [s, ((j or {}).get("drawer") or {}).get("expected_p")]
s, j = get("/finance/darpan/kal/api/pending"); out["kal_pending"] = [s, (j or {}).get("unlogged"), [d["date"] for d in (j or {}).get("days", [])][:40], (j or {}).get("log_from")]
s, j = get("/finance/darpan/kal/api/month?ym=2026-08"); out["kal_month"] = [s, [{k: m.get(k) for k in ("ym","sale_p","upi_p","cash_p","home_p","proc_p","other_p","received_elsewhere_p","net_cash_p","income_p","to_manoj_p","to_bhawna_p","to_pool_p","to_bank_p")} for m in (j or {}).get("months", [])], [(d["date"], d.get("handed_p"), d.get("handed_to")) for d in (j or {}).get("days", [])]]
with fa.app.app_context():
    con = fa.db()
    hs = fa._health_state(con) if hasattr(fa, "_health_state") else None
    out["health_raw"] = str(type(hs)) + " " + (",".join(sorted(hs.keys())) if isinstance(hs, dict) else "")
    rows = (hs.get("checks") or hs.get("items") or hs.get("rows") or []) if isinstance(hs, dict) else (hs or [])
    out["health_drawer"] = [x.get("detail") for x in rows if isinstance(x, dict) and x.get("key") == "drawer"]
s, j = get("/finance/clinic/api/days?ym=2026-09"); out["clinic_days"] = [s, j]
print("JSON:" + json.dumps(out, default=str))
'''

def run(appdir, db):
    env = dict(os.environ, APPDIR=appdir, FINANCE_DB=db)
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    for line in p.stdout.splitlines():
        if line.startswith("JSON:"):
            return json.loads(line[5:])
    sys.exit("!! the app did not answer (%s): %s" % (appdir, (p.stderr or "")[-1500:]))

if a.unseeded:
    U0, U1 = run(a.before, a.unseeded), run(a.after, a.unseeded)
    same = [k for k in U0 if U0[k] == U1.get(k)]
    diff = [k for k in U0 if U0[k] != U1.get(k)]
    print("  %s without the one calculation's tables, every screen answers exactly as before (%d/%d identical%s)"
          % ("ok  " if not diff else "FAIL", len(same), len(U0), (": differs " + ",".join(diff)) if diff else ""))
    if diff:
        print("WALK_S363 RED -- the fallback is not the old arithmetic"); sys.exit(1)
B = run(a.before, a.db)
A = run(a.after, a.db)
sys.path.insert(0, a.after)
import sanjeevni_cash as sc
con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
def R(p): return None if p is None else sc._rs(p)
p31 = sc.position(con, "2026-08-31"); pnow = sc.position(con, "9999-12-31")
rows = {r["date"]: r for r in sc.days(con, "2026-08-17", "9999-12-31")["rows"]}

n, fails = 0, []
def check(label, cond, before=None, after=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [before %s -> after %s]" % (before, after)) if (before is not None or after is not None) else ""))
    if not cond: fails.append(label)

def num(s):
    try: return int(round(float(str(s).replace(",", "")) * 100))
    except Exception: return None

cp = A["cash_position"][1]
check("approvals 'Where the money is': drawer = the one calculation", num(cp["drawer"]) == pnow["drawer"], B["cash_position"][1]["drawer"], cp["drawer"])
check("  ... with you & Dr Bhawna (the pool)", num(cp["reserve"]) == pnow["with_doctors"], (B["cash_position"][1]["reserve"], B["cash_position"][1]["with_manoj"]), cp["reserve"])
check("  ... the drawer names the days awaiting your approval", cp.get("waiting_days") == pnow["waiting_days"], None, len(cp.get("waiting_days") or []))
check("  ... last bank deposit is the pool's 15-Sep deposit", cp.get("last_bank_date") == "2026-09-15", B["cash_position"][1].get("last_bank_date"), cp.get("last_bank_date"))
check("  ... cash in the unit", num(cp["unbanked"]) == pnow["in_unit"], B["cash_position"][1]["unbanked"], cp["unbanked"])
bad = [d for d, v in A["days_sep"][1].items() if d in rows and num(v) != rows[d]["close"]["drawer"]]
check("approvals 'The drawer' / queue: every September day's closing = the one calculation", not bad,
      B["days_sep"][1].get(max(A["days_sep"][1] or [""])), A["days_sep"][1].get(max(A["days_sep"][1] or [""])))
check("  ... 31-Aug closes at Rs 7", num(A["days_aug"][1].get("2026-08-31")) == 700, B["days_aug"][1].get("2026-08-31"), A["days_aug"][1].get("2026-08-31"))
bad = [d for d, v in A["workbench_aug"][1].items() if d in rows and num(v) != rows[d]["close"]["drawer"]]
check("workbench month grid: every August closing = the one calculation", not bad)
held = {h["party"]: num(h["held"]) for h in (A["custody_held"][1] or [])}
check("workbench 'Held now': no negative, and = the one calculation", all(v >= 0 for v in held.values()) and held.get("drawer") == pnow["drawer"] and held.get("Dr Bhawna & Dr Manoj (pool)") == pnow["with_doctors"],
      B["custody_held"][1], A["custody_held"][1])
wc = {x["party"]: num(x["amount"]) for x in (A["where_is_the_cash"][1] or [])}
check("Darpan's 'where is the cash': the doctors' pool = the one calculation", wc.get("pool") == pnow["with_doctors"],
      B["where_is_the_cash"][2], A["where_is_the_cash"][2])
check("the portal tile's cash in hand = the drawer, and its last deposit is 15-Sep", num(A["tile"][1]) == pnow["drawer"] and A["tile"][2] == "2026-09-15", B["tile"][1:], A["tile"][1:])
check("the day panel 31-Aug: opening and closing from the one calculation",
      num(A["day_2026-08-31"][1]["closing"]) == 700 and num(A["day_2026-08-31"][1]["opening"]) == p31["drawer"] - rows["2026-08-31"]["into_drawer_p"] + sum(h["amount_p"] for h in rows["2026-08-31"]["handed"]),
      B["day_2026-08-31"][1], A["day_2026-08-31"][1])
check("the day panel 17-Aug opens at the count (drawer 0)", num(A["day_2026-08-17"][1]["opening"]) == 0, B["day_2026-08-17"][1], A["day_2026-08-17"][1])
check("Darpan's card, 31-Aug: the drawer he should hold is Rs 7", A["darpan_card_31aug"][1] == 700, B["darpan_card_31aug"][1], A["darpan_card_31aug"][1])
km = {m["ym"]: m for m in A["kal_month"][1]}.get("2026-08") or {}
check("month table, August: bill 2777 paid at the clinic, not without cash", km.get("received_elsewhere_p") == 300000 and km.get("other_p") == 0)
check("month table, August: handed to Dr Bhawna includes the 27-Aug 23,130 (both registers)", km.get("to_bhawna_p") == 4390000 + 2313000 + 2618000 + 871000 + 1600000 + 2400000,
      {m["ym"]: m for m in B["kal_month"][1]}.get("2026-08", {}).get("to_bhawna_p"), km.get("to_bhawna_p"))
check("month table, August days: every counter day from 17-Aug reads handed", all(h is not None for d, h, t in A["kal_month"][2] if d >= "2026-08-17"))
ks = {m["ym"]: m for m in A["kal_month"][1]}.get("2026-09") or {}
check("month table, September: to the bank = the pool's two deposits (4,00,000)", ks.get("to_bank_p") == 40000000, None, ks.get("to_bank_p"))
check("month table, September: to the pool = the approved days' cash", ks.get("to_pool_p") == sum(h["amount_p"] for r in rows.values() if r["date"] >= "2026-09-01" for h in r["handed"] if h.get("src") == "approval"), None, ks.get("to_pool_p"))
check("month table: income = net cash + UPI", all(m["income_p"] == m["cash_p"] - m["home_p"] - m["proc_p"] - m["other_p"] + m["upi_p"] for m in A["kal_month"][1] if m.get("income_p") is not None))
check("the health card's drawer leg reads the one calculation", bool(A["health_drawer"]) and sc._rs(pnow["drawer"]).replace(",", "") in (A["health_drawer"][0] or "").replace(",", ""),
      B["health_drawer"], A["health_drawer"])
check("the clinic unit's screen is unchanged (byte-identical answer)", A["clinic_days"] == B["clinic_days"])
first = (A["kal_pending"][2] or [None])[0]
if not first:
    print("  note: no day is waiting for approval, so the approval step has nothing to exercise")
else:
    import shutil
    logdb = a.db + ".approve"
    shutil.copy2(a.db, logdb)
    APPROBE = r'''
import json, os, sys
sys.path.insert(0, os.environ["APPDIR"])
os.environ.update(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="manoj", FINANCE_DEV_ROLE="owner")
import finance_app as fa
c = fa.app.test_client(); H = {"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"}
r = c.post("/finance/api/approve/" + os.environ["DAY"], json={}, headers=H)
p = c.get("/finance/darpan/kal/api/pending", headers=H).get_json() or {}
y = c.get("/finance/api/yesbank/reconcile?from=2026-09-01&to=2026-09-20", headers=H).get_json() or {}
print("JSON:" + json.dumps(dict(status=r.status_code, body=(r.get_json() or {}), unlogged=p.get("unlogged"), yb=y)))
'''
    env = dict(os.environ, APPDIR=a.after, FINANCE_DB=logdb, DAY=first)
    pp = subprocess.run([sys.executable, "-B", "-c", APPROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=a.after)
    L = next((json.loads(x[5:]) for x in pp.stdout.splitlines() if x.startswith("JSON:")), None)
    lc = sqlite3.connect(logdb)
    st = lc.execute("SELECT status FROM day_entry WHERE unit='medical' AND business_date=?", (first,)).fetchone()
    pl = sc.position(lc, "9999-12-31")
    into1 = rows[first]["into_drawer_p"]
    check("approving %s (as you will) moves exactly that day's cash from the drawer to the pool" % first,
          bool(L) and L["status"] == 200 and st and st[0] in ("approved", "locked")
          and pl["drawer"] == pnow["drawer"] - into1 and pl["with_doctors"] == pnow["with_doctors"] + into1 and pl["in_unit"] == pnow["in_unit"],
          sc._rs(pnow["drawer"]), L and sc._rs(pl["drawer"]))
    check("  ... and it leaves the cash log's list (approval is the record; nothing to log)",
          bool(L) and L["unlogged"] == A["kal_pending"][1] - 1, A["kal_pending"][1], L and L["unlogged"])
    yb = (L or {}).get("yb") or {}
    bits = [x.get("date") for x in (yb.get("deposit_unevidenced") or []) + (yb.get("deposit_not_in_bank") or [])] + ([None] * int(yb.get("matched") or 0))
    check("  ... the Yes Bank check sees the pool's two deposits as booked (unevidenced until the statement is loaded, or matched)",
          len(bits) >= 2 and not (yb.get("bank_deposit_not_booked") or []), None, yb and dict(matched=yb.get("matched"), unevidenced=[x.get("date") for x in yb.get("deposit_unevidenced") or []]))
    if a.pdf:
        PDFPROBE = r'''
import io, json, os, sys
sys.path.insert(0, os.environ["APPDIR"])
os.environ.update(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="manoj", FINANCE_DEV_ROLE="owner")
import finance_app as fa
c = fa.app.test_client(); H = {"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"}
r = c.post("/finance/api/yesbank-statement", data={"file": (io.BytesIO(open(os.environ["PDF"], "rb").read()), "statement.pdf")}, content_type="multipart/form-data", headers=H)
print("JSON:" + json.dumps(dict(status=r.status_code, rec=(r.get_json() or {}).get("reconciled"))))
'''
        env = dict(os.environ, APPDIR=a.after, FINANCE_DB=logdb, PDF=a.pdf, FINANCE_YESBANK_DIR=logdb + "_yb")
        pp = subprocess.run([sys.executable, "-B", "-c", PDFPROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=a.after)
        P = next((json.loads(x[5:]) for x in pp.stdout.splitlines() if x.startswith("JSON:")), None)
        rec = (P or {}).get("rec") or {}
        check("  ... with your real statement loaded: both deposits MATCHED, nothing unbooked, nothing missing",
              bool(P) and P["status"] == 200 and rec.get("matched") == 2 and not rec.get("bank_deposit_not_booked") and not rec.get("deposit_not_in_bank"),
              None, rec and dict(matched=rec.get("matched"), not_booked=rec.get("bank_deposit_not_booked")))
    os.remove(logdb)
if a.probe:
    print(json.dumps(dict(before=B["kal_pending"], after=A["kal_pending"]), indent=0)[:1500])
print("  pending in the cash log -- before: %s day(s) %s ; after: %s day(s) %s" % (B["kal_pending"][1], B["kal_pending"][2][:3], A["kal_pending"][1], A["kal_pending"][2][:3]))
print("WALK_S363 %s -- %d/%d" % ("GREEN" if not fails else "RED", n - len(fails), n))
sys.exit(1 if fails else 0)
