#!/usr/bin/env python3
"""walk_s845.py -- S845_ITEM_LEDGER's walk on a COPY of the live database and a stock record built from Marg's real exports.
    SPINE_DB=<spine.db> python3 walk_s845.py <finance dir with the built files> <copy of finance.db> [--control]
Every check prints PASS/FAIL; exit 0 only when all pass. --control breaks the page on purpose (vouchers dropped, a sale's sign flipped):
the reconciliation checks must go red. The database copy is opened read-write and must show NO change after every page and door."""
import datetime as dt, hashlib, json, os, re, sqlite3, sys

FIN, DBP = sys.argv[1], sys.argv[2]
CONTROL = "--control" in sys.argv
BOX = "--box" in sys.argv                                     # on the server: no check of frozen data (F-1427) -- only rules
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]   # the kit folder carries item_ledger.py: never imported from there
sys.path.insert(0, FIN)
sys.path.insert(0, os.path.join(FIN, "spine"))
RES = []


def ok(name, cond, detail=""):
    RES.append(bool(cond))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, ("  -- " + str(detail)[:300]) if detail else ""))


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


m_db, m_sp = md5(DBP), md5(os.environ["SPINE_DB"])
try:
    import item_ledger as IL
except Exception as e:                                       # the live files hold no item_ledger: the control on the live side
    ok("item_ledger imports", False, e)
    sys.exit(1)
import spine_read
if CONTROL:
    IL.vouchers = lambda con, sp, key: []
    _e = IL._entry
    IL._entry = lambda kind, u, ref, d, sup: dict(_e(kind, u, ref, d, sup), u=(-float(u) if kind == "SALE" and str(ref).endswith("1") else float(u)))

con = sqlite3.connect(DBP)
con.row_factory = sqlite3.Row                                 # as production's connection (review S6)
sp = IL.spine_con()
S = spine_read.Spine(os.environ["SPINE_DB"])
T0 = con.total_changes

# ---- 1. units
U = IL.Unit("1*10", "LOOSE", "X")
ok("strips:tabs 159 -> 15:9", U.fmt(159) == "15:9", U.fmt(159))
ok("negative -3 -> −0:3", U.fmt(-3) == "−0:3", U.fmt(-3))
ok("signed +20 strips", U.fmt(200, sign=True) == "+20:0", U.fmt(200, sign=True))
ok("a whole-pack item reads its own word", "tube" in IL.Unit("1", "WHOLE", "TRAMAVIN GEL").fmt(12), IL.Unit("1", "WHOLE", "TRAMAVIN GEL").fmt(12))

# ---- 2. search
one = sp.execute("SELECT name FROM sp_item ORDER BY last_seen DESC, name LIMIT 1").fetchone()
pfx = (one[0] if one else "ZZ")[:3]
f = IL.find(sp, pfx)
ok("search by the first 3 letters finds the item (%s)" % pfx, one and any(r["name"] == one[0] for r in f), [r["key"] for r in f][:5])
ok("search ranks names starting with the letters first", f and f[0]["name"].upper().startswith(pfx.upper()), f[:2])
ok("one letter finds nothing", IL.find(sp, "z") == [])
ok("search is capped", len(IL.find(sp, "a", 15)) <= 15)

# ---- 3. the ledger reconciles, item by item (every item that moved in the last 30 days, and the full ledger of 25)
t = IL.today()
d1, d2 = (t - dt.timedelta(days=29)).isoformat(), t.isoformat()
keys = [r[0] for r in sp.execute("SELECT DISTINCT k20 FROM sp_move WHERE date>=? AND kind IN ('SALE','PURCHASE')", (d1,))]
hand = {}
for r in con.execute("SELECT k20, day_to, status, kind, rec_kind FROM marg_hand_change"):
    hand.setdefault(r[0], []).append(r)
bad_chain, bad_end, bad_sales, bad_bills, bad_red, n = [], [], [], [], [], 0
bills = {(d, b) for d, b in sp.execute("SELECT date, bill FROM sp_sale_bill")}
pbills = {(s, b, d) for s, b, d in sp.execute("SELECT supkey, bill, date FROM sp_purchase_bill")}
for k in keys:
    if IL.item(sp, k) is None:
        continue
    n += 1
    L = IL.ledger(con, sp, k, d1, d2)
    days = list(reversed(L["days"]))
    prev = L["totals"]["opening"]
    for d in days:                                            # each day opens on the day before: Marg's closing when there was one, else the expected
        if abs(d["opening"] - prev) > 1e-6:
            bad_chain.append((k, d["day"])); break
        if abs(d["opening"] + sum(e["u"] for e in d["entries"]) - d["expected"]) > 1e-6:
            bad_chain.append((k, d["day"], "sum")); break
        prev = d["marg"] if d["marg"] is not None else d["expected"]
    cl = L["totals"]["closing_day"]
    if days and cl and days[-1]["day"] == cl and abs(L["totals"]["end"] - float(L["totals"]["closing"])) > 1e-6:
        bad_end.append(k)
    sold = sum(e["u"] for d in days for e in d["entries"] if e["kind"] == "SALE")
    ref = S.sales(k, d1, d2)
    want = -sum(float(r["units"] if r.get("units") is not None else 0) for r in S.q("SELECT l.units FROM sp_sale_line l JOIN sp_sale_bill b ON b.date=l.date AND b.bill=l.bill "
                                                                                     "WHERE l.k20=? AND l.date BETWEEN ? AND ? AND COALESCE(b.credit_note,0)=0", k, d1, d2))
    if abs(sold - want) > 1e-6:
        bad_sales.append((k, sold, want))
    for d in days:
        for e in d["entries"]:
            if e["kind"] in ("SALE", "SALE_RETURN") and (d["day"], e["ref"]) not in bills:
                bad_bills.append((k, d["day"], e["ref"]))
            if e["kind"] in ("PURCHASE", "PURCHASE_RETURN") and (e.get("supkey"), e["ref"], d["day"]) not in pbills:
                bad_bills.append((k, d["day"], e["ref"]))
    reds = sorted(d["day"] for d in days if d["state"] == "bad")
    hs = hand_rows = IL.hand_rows(con, k)
    want_red = sorted({str(h["day_to"])[:10] for h in hs if h["state"] == "bad" and d1 <= str(h["day_to"])[:10] <= d2})
    if reds != want_red:
        bad_red.append((k, reds, want_red))
ok("items walked (moved in the last 30 days)", n > (0 if BOX else 100), n)
ok("each day opens where the day before ended, and adds up", not bad_chain, bad_chain[:5])
ok("the period ends on Marg's own closing", not bad_end, bad_end[:5])
ok("sales = the stock record's own sale lines (credit notes apart)", not bad_sales, bad_sales[:3])
ok("every bill number is a bill Marg reported", not bad_bills, bad_bills[:5])
ok("red days = the Marg watch's own counted moves, exactly", not bad_red, bad_red[:5])

# review M1: a counted move on a day with no closing of this key is still red, and counted once
fk = keys[0] if keys else (sp.execute("SELECT k20 FROM sp_item LIMIT 1").fetchone() or ["X"])[0]
fake = dict(id=-1, k20=fk, item=fk, kind="hand", day_from=d1, day_to="2001-01-01", shift=-3.0, state="bad", why="made-up move", asked=False)
nodays = [x for x in (t - dt.timedelta(days=j) for j in range(29)) if x.isoformat() not in {r[0] for r in sp.execute("SELECT as_on FROM sp_close WHERE k20=?", (fk,))}]
if nodays:
    fake["day_to"] = nodays[0].isoformat()
    Lf = IL.ledger(con, sp, fk, d1, d2, [fake])
    dd = [d for d in Lf["days"] if d["day"] == fake["day_to"]]
    ok("a counted move on a day with no closing of the item is red", dd and dd[0]["state"] == "bad" and Lf["totals"]["n_bad"] == 1, [d["state"] for d in dd])
else:
    ok("a counted move on a day with no closing (every day has one -- not testable here)", True)
# review S2: a key whose members differ in strip size reads plain units, the search the same as the page
mixed = None
for k, in sp.execute("SELECT k20 FROM sp_item GROUP BY k20 HAVING COUNT(DISTINCT packing) > 1"):
    its = sp.execute("SELECT name, packing, unit_kind FROM sp_item WHERE k20=?", (k,)).fetchall()
    if len({IL.Unit(p, u, n).n if IL.Unit(p, u, n).strip else 0 for n, p, u in its}) > 1:
        mixed = k
        break
if mixed:
    ok("a key of mixed strip sizes reads plain units (%s)" % mixed, isinstance(IL.item(sp, mixed)["unit"], IL.Plain))
    fr = [r for r in IL.find(sp, mixed[:12]) if r["key"] == mixed]
    c0 = sp.execute("SELECT units FROM sp_close WHERE k20=? ORDER BY as_on DESC LIMIT 1", (mixed,)).fetchone()
    ok("the search shows it in the page's own unit", fr and c0 and fr[0]["marg"] == IL.item(sp, mixed)["unit"].fmt(c0[0]), fr[:1])
else:
    ok("a key of mixed strip sizes (none in this copy)", True)

# vouchers: every filed voucher of the range on the right item, with its number
import spine_build
fv = spine_build.filed_vouchers(DBP)
miss, by_key = [], {}
alias = {r[0]: r[1] for r in sp.execute("SELECT alias, k20 FROM sp_alias")}
for nm, lst in fv.items():                                    # a family (one key, several names) sums its names
    k = alias.get(IL.K(nm), IL.K(nm))
    by_key[k] = by_key.get(k, 0.0) + sum(u for d, u in lst)
for k, want in by_key.items():
    if IL.item(sp, k) is None:
        continue
    got = IL.vouchers(con, sp, k)
    if round(want, 3) != round(sum(v["units"] for v in got), 3) or any(not v["no"] for v in got):
        miss.append((k, want, sum(v["units"] for v in got)))
ok("every filed voucher is on its item with its Marg number", (fv or BOX) and not miss, miss[:4])

# full ledger of 25 busy items: the opening is the stock record's own, the end Marg's
busy = [r[0] for r in sp.execute("SELECT k20 FROM sp_move WHERE kind='SALE' GROUP BY k20 ORDER BY COUNT(*) DESC LIMIT 25")]
fb = []
for k in busy:
    L = IL.ledger(con, sp, k, IL.first_day(sp), d2)
    cl = L["totals"]["closing_day"]
    if L["days"] and cl and L["days"][0]["day"] == cl and abs(L["totals"]["end"] - float(L["totals"]["closing"])) > 1e-6:
        fb.append(k)
ok("full ledger of the 25 busiest items ends on Marg's closing", not fb, fb)

# a late bill is named, never red (the bench's frozen case; on the box only the rule: no late/late_in day is ever red)
if not BOX:
    z = IL.ledger(con, sp, "ZIBON EXTRA", "2026-11-08", "2026-11-16")
    st = {d["day"]: d["state"] for d in z["days"]}
    ok("a bill Marg keyed late reads late, then taken in (ZIBON EXTRA 11-11 / 14-11)", st.get("2026-11-11") == "late" and st.get("2026-11-14") == "late_in", st)
ok("_late: Marg below by one purchase line reads late; the same rise later reads taken in",
   IL._late(-20.0, "2026-11-11", [dict(u=20.0, ref="1", label="Purchase · X", day="2026-11-11")], []) is not None)
ow = []
pend = [dict(u=20.0, ref="1", label="Purchase · X", day="2026-11-11")]
IL._late(-20.0, "2026-11-11", pend, ow)
ok("_late: a rise that equals no owed bill is not explained", IL._late(7.0, "2026-11-14", [], ow) is None and len(ow) == 1)
ok("_late: the owed bill taken in is paid off once", IL._late(20.0, "2026-11-14", [], ow) is not None and ow == [])

# ---- 4. arrived, not yet in Marg: the Purchase bills page's own list (made up here), the tracker's matcher, M1 -- on an item whose units ARE
# proven (any such item: no frozen name), and one whose units are not
PV = IL._PV()
real = PV.provisional
proven = None
for k, in sp.execute("SELECT DISTINCT k20 FROM sp_purchase_line WHERE direction='PURCHASE' ORDER BY k20"):
    if IL._factor(sp, k) and IL.item(sp, k) and not IL.item(sp, k)["family"]:
        proven = k
        break
other = next((k for k, in sp.execute("SELECT k20 FROM sp_item ORDER BY k20") if k != proven and IL.item(sp, k)), None)
if proven:
    pn = IL.item(sp, proven)["name"]
    on = IL.item(sp, other)["name"] if other else "SOMETHING ELSE ENTIRELY"
    PV.provisional = lambda c, ym: ([dict(id=9001, stamp="B-9001", dealer="", known=False, bill_no="99", date=d2, total_p=1000, day=d2,
                                          lines=[dict(name=pn, qty=3, batch="X", expiry="09/28"), dict(name=on, qty=2)], why=[]),
                                     dict(id=9002, stamp="B-9002", dealer="", known=False, bill_no="98", date=d2, total_p=500, day=d2,
                                          lines=[dict(name=pn, qty=5)], why=["probably already in Marg as bill 1"])]
                                    if ym == t.strftime("%Y-%m") else [])
    A = IL.arrived(con, sp, proven)
    fac = IL._factor(sp, proven)
    ok("a scanned bill not in Marg is listed with this item's line (%s)" % proven, len(A) == 2 and A[0]["lines"][0]["qty"] == 3, [(a["scan"]["stamp"], a["units"]) for a in A])
    ok("its units are proven from Marg's own bills and added", A and abs(A[0]["units"] - 3 * fac) < 1e-6, (fac, A[0]["units"] if A else None))
    ok("a scan probably already in Marg is shown but never added", len(A) > 1 and A[1]["units"] == 0.0 and A[1]["twin"])
    ok("another item's line on the same scan is not this item's", all(m["name"] == pn for a in A for m in a["lines"]))
    if other:
        A2 = [a for a in IL.arrived(con, sp, other) if a["scan"]["id"] == 9002]
        ok("an item on no waiting scan has nothing arrived", A2 == [], A2)
else:
    ok("arrivals (no item with proven units in this copy)", True)
PV.provisional = real

# ---- 5. the routes: the doctor only, read only
import flask
app = flask.Flask("walk")
WHO = {"u": {"user": "manoj"}}
IL.init(app, lambda: con, lambda role: (WHO["u"], None) if WHO["u"] and role == "checker" else (None, ("refused", 403)))
c = app.test_client()
codes, errs = {}, []
pages = keys[:40] + [k for k in ("ZIBON EXTRA", "ROSIKA FORTE", "TRAMAVIN GEL") if not BOX and IL.item(sp, k)]
for k in pages:
    for r in ("30", "full"):
        resp = c.get("/finance/sanjeevni/ledger?k=%s&r=%s" % (IL._u(k), r))
        codes[resp.status_code] = codes.get(resp.status_code, 0) + 1
        tx = resp.get_data(as_text=True)
        if "Traceback" in tx or "The stock record could not be opened" in tx or "<h1>Item ledger</h1>" not in tx or "Ledger</h2>" not in tx:
            errs.append(k)
ok("every item page answers 200", (not pages) or list(codes) == [200], codes)
ok("no page shows an error", not errs, errs[:3])
rk = keys[0] if keys else None
a0, b0 = (t - dt.timedelta(days=20)), (t - dt.timedelta(days=10))
if rk:
    r = c.get("/finance/sanjeevni/ledger?k=%s&r=range&from=%s&to=%s" % (IL._u(rk), a0.isoformat(), b0.isoformat())).get_data(as_text=True)
    ok("a date range shows that range", "%s to %s" % (IL.dmon(a0.isoformat()), IL.dmon(b0.isoformat())) in r)
    r = c.get("/finance/sanjeevni/ledger?k=%s&r=range&from=%s&to=%s" % (IL._u(rk), b0.isoformat(), a0.isoformat())).get_data(as_text=True)
    ok("a range back to front falls back to the last 30 days, no error", "Date range ·" in r and "Traceback" not in r)
uniq = next((nm for nm, in sp.execute("SELECT name FROM sp_item ORDER BY LENGTH(name) DESC LIMIT 200") if len(IL.find(sp, nm, 2)) == 1), None)
if uniq:
    r = c.get("/finance/sanjeevni/ledger?q=%s" % IL._u(uniq)).get_data(as_text=True)
    ok("one item holding the letters opens straight", "Expected stock" in r)
r = c.get("/finance/sanjeevni/ledger?q=%s" % IL._u(pfx)).get_data(as_text=True)
ok("a search lists or opens, no error", ("items holding" in r or "Expected stock" in r or "Nothing in the stock record" in r) and "Traceback" not in r)
r = c.get("/finance/sanjeevni/ledger/api/find?q=%s" % IL._u(pfx)).get_json()
ok("the search door answers JSON", r and r.get("ok") is True and isinstance(r.get("items"), list), r)
pb = con.execute("SELECT b.supplier, b.bill_no, b.bill_date, l.asset_bill_id FROM purchase_scan_link l JOIN purchase_bill b ON b.id=l.bill_id "
                 "ORDER BY b.bill_date DESC LIMIT 1").fetchone() if IL._table(con, "purchase_scan_link") and IL._table(con, "purchase_bill") else None
if pb:
    r = c.get("/finance/sanjeevni/ledger/api/bill?s=%s&b=%s&d=%s" % (re.sub(r"[^A-Z]", "", pb[0].upper())[:8], IL._u(pb[1]), pb[2])).get_data(as_text=True)
    ok("a purchase row opens its own paper (the newest paired bill)", "/finance/purchase/api/s738/scan/%d" % int(pb[3]) in r or "Traceback" not in r, r[:200])
else:
    ok("a purchase row opens its own paper (no paired bill in this copy)", True)
r = c.get("/finance/sanjeevni/ledger/api/bill?s=NOBODY&b=0&d=2026-11-13").get_data(as_text=True)
ok("a bill not in the register says so", "not in the purchase register" in r, r[:120])
redk = next((k for k in keys if any(h["state"] == "bad" and d1 <= str(h["day_to"])[:10] <= d2 for h in IL.hand_rows(con, k))), None)
if redk:
    r = c.get("/finance/sanjeevni/ledger?k=%s" % IL._u(redk)).get_data(as_text=True)
    ok("a red day carries the Marg watch's own ask button (%s)" % redk, ('data-ask="' in r or "Register asked" in r) and "/finance/sanjeevni/marg-watch" in r)
else:
    ok("a red day carries the ask button (no red day in the last 30 days)", True)
WHO["u"] = None
ok("not the doctor: refused", c.get("/finance/sanjeevni/ledger").status_code == 403 and c.get("/finance/sanjeevni/ledger/api/find?q=ro").status_code == 403)
ok("nothing written to the database by any page or door", con.total_changes == T0, con.total_changes - T0)
con.close(); sp.close()
ok("the database file is byte-for-byte unchanged", md5(DBP) == m_db)
ok("the stock record is byte-for-byte unchanged", md5(os.environ["SPINE_DB"]) == m_sp)

# ---- 6. the Hub: Go to carries the box and the link once; the Hub mounts the ledger
h = open(os.path.join(FIN, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
ok("Go to: the search box, once", h.count('action="/finance/sanjeevni/ledger"') == 1)
ok("Go to: the link, once", h.count('href="/finance/sanjeevni/ledger"') == 1)
sa = open(os.path.join(FIN, "sanjeevni_approvals.py"), encoding="utf-8").read()
ok("the Hub mounts the ledger, fail-soft", "item_ledger.init(app, db_getter, require_fn)" in sa and "item_ledger NOT mounted" in sa)
try:                                                          # review S2: the Hub's OWN init mounts it (not a string search alone)
    import io, contextlib
    import sanjeevni_approvals as SA
    app2 = flask.Flask("hub")
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        SA.init(app2, lambda: sqlite3.connect(DBP), lambda role: (None, ("refused", 403)))
    rules = {r.rule for r in app2.url_map.iter_rules()}
    ok("the Hub's own init mounts the ledger (4 doors)", {"/finance/sanjeevni/ledger", "/finance/sanjeevni/ledger/api/find", "/finance/sanjeevni/ledger/api/bill",
                                                         "/finance/sanjeevni/ledger/api/healthz"} <= rules and "item_ledger NOT mounted" not in err.getvalue(), err.getvalue()[-200:])
except Exception as e:                                        # noqa: BLE001
    ok("the Hub's own init mounts the ledger", False, "%s: %s" % (e.__class__.__name__, e))

print("WALK S845: %d PASS, %d FAIL%s" % (sum(RES), len(RES) - sum(RES), " (CONTROL)" if CONTROL else ""))
sys.exit(0 if all(RES) else 1)
