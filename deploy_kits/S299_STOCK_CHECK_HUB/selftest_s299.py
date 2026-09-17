#!/usr/bin/env python3
"""selftest_s299.py -- proves S299_STOCK_CHECK_HUB offline.
Bytes: the five files at their live pins; anchors once; refusal; idempotence; compile; the desk
and hub scripts parse. Behaviour over a fixture shaped like count #1: the orthotic pairs by
product then nearest size (LS belt sizes read right), the medicine pairs by salt; never a
consumable, a parked line or a Marg-negative line; a Yes takes its units off both lines (a
part swap leaves the rest short, a whole swap reads 'swap confirmed'); Darpan's list waits
for every answer and then carries shortages only; the list PDF prints Qty in Marg | Physical
<day> | Difference with the swap line; the portal tile opens the hub.
S299: a confirmed swap is STOCK ISSUE on the short item and STOCK RECEIVE on the extra item for
the swapped quantity, at once (a part swap without waiting, a whole swap never CHANGE 0); a
decided remainder runs from Marg-after-swap to the shelf; the hub and Amir's board say the
owner types answers too.
    python3 -B selftest_s299.py --base <dir with the five live files>"""
import argparse, hashlib, importlib.util, io, os, re, shutil, sqlite3, subprocess, sys, tempfile, types
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import patch_stock_check_hub_s299 as P  # noqa: E402
PINS = dict(stock_app="bb7df8d78b0f1ff8cfd86a5c260f301c", pad_receipt="239a81fb7f637663092424c20974ca01",
            stock_desk="aac7f96c73f879dba557310d207d064f", portal="c14c2c649e0405378abcd95d8749c666",
            stock_amir="32aa7d45fc93f19d4526a5bca3a3743a")
EXT = dict(stock_app=".py", pad_receipt=".py", stock_desk=".html", portal=".py", stock_amir=".html")
FAILS = []
def check(n, ok, d=""):
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else "  -- " + str(d)[:400]))
    if not ok: FAILS.append(n)
def md5(p): return hashlib.md5(io.open(p, "rb").read()).hexdigest()
def stub_flask():
    f = types.ModuleType("flask")
    class BP:
        def __init__(s, *a, **k): pass
        def route(s, *a, **k): return lambda fn: fn
    f.Blueprint = BP; f.jsonify = lambda *a, **k: (a, k); f.request = types.SimpleNamespace(args={}, form={}, get_json=lambda *a, **k: {})
    f.Response = object; f.redirect = lambda *a, **k: None
    sys.modules.setdefault("flask", f)
def load(path, name):
    stub_flask(); spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def fixture():
    def x(item, lane, marg, counted, mrp_unit=100, pack=1, word=None, consumable=False):
        return dict(item=item, lane=lane, marg=marg, counted=counted, diff=counted - marg, pack=pack, packing="1*%d" % pack,
                    mrp_p=(counted - marg) * mrp_unit, cost_p=(counted - marg) * mrp_unit // 2, consumable=consumable,
                    word=(dict(action=word, label=word) if word else None))
    diffs = [x("ANKLE BINDER BAMBOO L", "ortho", 3, 0, 27520), x("ANKLE BINDER L TYNOR", "ortho", 0, 2, 30960),
             x("L S BELT CONT GRAY UNISON M", "ortho", 2, 1, 97300), x("L S BELT CONT GRAY UNISON L", "ortho", 2, 3, 139000),
             x("KNEE SUPPORT HINGED XXL UNISO", "ortho", 2, 1, 80500), x("KNEE SUPPORT HINGED M", "ortho", 3, 4, 80500),
             x("RIB BELT S TYNOR", "ortho", 1, 0, 52000), x("DISPO SYRINGE NIPRO 3ML", "consume", 62, 0, 1000, consumable=True),
             x("CERVICAL COLLAR SOFT HOPE L", "ortho", -1, 0, 19600), x("CERVICAL COLLAR SOFT HOPE M", "ortho", 1, 0, 19600),
             x("ETOZOX 90", "loss", 100, 80, 20, 10, word="PARKED"), x("PARI CR 12.5", "recount", 84, 367, 15, 10),
             x("MOTIF FORTE", "loss", 60, 55, 468, 10), x("ASTOFEN P", "recount", 10, 30, 550, 10),
             x("ROSIKA FORTE", "loss", 723, 553, 30, 10)]
    pairs = [dict(salt="ETORICOXIB 90", short=[dict(item="ETOZOX 90")], over=[dict(item="PARI CR 12.5")]),
             dict(salt="ACECLOFENAC 100 + PCM", short=[dict(item="MOTIF FORTE")], over=[dict(item="ASTOFEN P")])]
    return diffs, pairs
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--base", required=True); a = ap.parse_args(argv)
    src = {k: os.path.join(a.base, k + EXT[k]) for k in PINS}
    for k, p in src.items(): check("%s is the live pin" % k, md5(p) == PINS[k], md5(p))
    tmp = tempfile.mkdtemp(prefix="s299_"); w = {k: os.path.join(tmp, os.path.basename(p)) for k, p in src.items()}
    for k in src: shutil.copy2(src[k], w[k])
    for k, edits in (("stock_app", P.APP_EDITS), ("pad_receipt", P.RECEIPT_EDITS), ("stock_desk", P.DESK_EDITS), ("portal", P.PORTAL_EDITS), ("stock_amir", P.AMIR_EDITS)):
        t = io.open(w[k], encoding="utf-8").read()
        for old, _ in edits: check("%s anchor once: %s" % (k, old.strip()[:34].replace("\n", " ")), t.count(old) == 1, t.count(old))
    cmd = [sys.executable, "-B", os.path.join(HERE, "patch_stock_check_hub_s299.py"), "--app", w["stock_app"], "--receipt", w["pad_receipt"], "--desk", w["stock_desk"], "--portal", w["portal"], "--amir", w["stock_amir"]]
    r = subprocess.run(cmd + ["--app-from", "0" * 32], capture_output=True, text=True); check("refuses a wrong --from", r.returncode != 0 and "REFUSING" in r.stdout + r.stderr)
    r = subprocess.run(cmd + ["--app-from", PINS["stock_app"], "--receipt-from", PINS["pad_receipt"], "--desk-from", PINS["stock_desk"], "--portal-from", PINS["portal"], "--amir-from", PINS["stock_amir"]], capture_output=True, text=True)
    check("patches all five from the live pins", r.returncode == 0, r.stdout + r.stderr)
    h = {k: md5(p) for k, p in w.items()}
    r = subprocess.run(cmd, capture_output=True, text=True); check("idempotent", {k: md5(p) for k, p in w.items()} == h and r.stdout.count("ALREADY") == 5, r.stdout)
    for k, p in w.items(): check("%s backup is the live bytes" % k, md5(p + ".bak_S299_" + PINS[k][:8]) == PINS[k])
    r = subprocess.run([sys.executable, "-m", "py_compile", w["stock_app"], w["pad_receipt"], w["portal"]], capture_output=True, text=True); check("the Python files compile", r.returncode == 0, r.stderr)
    for name, path in (("desk", w["stock_desk"]), ("hub", os.path.join(HERE, "stock_hub.html")), ("amir", w["stock_amir"])):
        sc = re.findall(r"<script[^>]*>(.*?)</script>", io.open(path, encoding="utf-8").read(), re.S); js = os.path.join(tmp, name + ".js"); io.open(js, "w", encoding="utf-8").write(sc[-1])
        r = subprocess.run(["node", "--check", js], capture_output=True, text=True); check("%s script parses" % name, r.returncode == 0, r.stderr[:300])
    hub = io.open(os.path.join(HERE, "stock_hub.html"), encoding="utf-8").read()
    for col in ("Family", "Item that is SHORT", "Item that is EXTRA", "Qty", "Rate of the item that left", "Rate of the item billed", "Difference per", "How close", "Confirmed? (yes / no)"):
        check("hub carries the workbook column: %s" % col, col in hub)
    check("hub BOOT placeholder once", hub.count("/*__BOOT__*/") == 1)
    portal = io.open(w["portal"], encoding="utf-8").read()
    check("portal: the Stock Check tile opens the hub", re.search(r'"name": "Stock Check",.*?"url": "/finance/stock/page/hub"', portal, re.S) is not None)
    check("portal: the counting screen is no longer a tile address", '"url": "/finance/stock/page/count"' not in portal)
    check("desk footer points at the hub", "every step, in order (the tile)" in io.open(w["stock_desk"], encoding="utf-8").read())
    print("predicted: stock_app.py %s · pad_receipt.py %s · stock_desk.html %s · portal.py %s · stock_amir.html %s" % (h["stock_app"], h["pad_receipt"], h["stock_desk"], h["portal"], h["stock_amir"]))
    app_t = io.open(w["stock_app"], encoding="utf-8").read(); amir_t = io.open(w["stock_amir"], encoding="utf-8").read()
    check("S299 (a): hub step 4 -- by Amir or by you, with the button", "Darpan's answers typed — by Amir or by you" in hub and "#answers\">Type Darpan" in hub)
    check("S299 (a): Amir's board opens at the typing card and says Amir or the doctor", 'id="answers"' in amir_t and "Amir or the doctor types" in amir_t and 'location.hash==="#answers"' in amir_t)
    check("S299 (b): Amir's board lists the swaps first", "Swaps confirmed — stock issue and stock receive" in amir_t and "V.swap.map(srow)" in amir_t)
    check("S299 (b): hub step 6 names the swap vouchers", "STOCK ISSUE on the short item" in hub and "STOCK RECEIVE on the extra item" in hub)
    check("S299 (b): Amir's board and the cleanup read the swap vouchers", "swap=_swap_vouchers(d)" in app_t and "rows = _cleanup_rows(d)" in app_t and "for x in _word_vouchers(d):" in app_t)
    check("S299: the orthotics sheet no longer says 'swap the figures in Marg'", "swap the figures in Marg. Tick" not in app_t and "Key NOTHING in Marg from this sheet" in app_t)
    S = load(w["stock_app"], "sa_new")
    check("LS belt sizes read right", S._match_type_size("L S BELT CONT GRAY UNISON XL") == ("LS BELT", "XL") and S._match_type_size("L S BELT CONT GRAY UNISON M")[1] == "M")
    check("wrist splint sides are one product", S._match_type_size("TYNOR WRIST SPLINT LF M ELAS") == S._match_type_size("TYNOR WRIST SPLINT RT M ELAST"))
    diffs, pairs = fixture()
    words = {x["item"]: x["word"] for x in diffs if x["word"]}
    props = S._match_proposals(diffs, pairs, words)
    got = sorted((p["short"], p["over"], p["qty"], p["close_text"]) for p in props)
    print("   proposals:", got)
    check("ankle binder: same size, 2 units", ("ANKLE BINDER BAMBOO L", "ANKLE BINDER L TYNOR", 2, "same size") in got)
    check("LS belt M against L: one size apart", ("L S BELT CONT GRAY UNISON M", "L S BELT CONT GRAY UNISON L", 1, "one size apart") in got)
    check("knee support XXL against M: sizes differ", ("KNEE SUPPORT HINGED XXL UNISO", "KNEE SUPPORT HINGED M", 1, "sizes differ") in got)
    check("medicine by salt", ("MOTIF FORTE", "ASTOFEN P", 5, "same salt") in got)
    check("never a parked line (ETOZOX 90)", not any(p["short"] == "ETOZOX 90" for p in props))
    check("never a consumable or a Marg-negative line", not any("NIPRO" in p["short"] or "HOPE" in p["short"] or "HOPE" in p["over"] for p in props))
    check("a lone shortage is not paired (RIB BELT)", not any(p["short"] == "RIB BELT S TYNOR" for p in props))
    con = sqlite3.connect(":memory:"); con.executescript(S.MATCH_SCHEMA)
    ins = lambda s, o, q, a_: con.execute("INSERT INTO stock_match (count_id, short_item, over_item, qty, answer, at) VALUES (1,?,?,?,?, 'x')", (s, o, q, a_))  # noqa: E731
    d = dict(differences=diffs, matches=S._match_apply(con, 1, diffs, pairs, words))
    check("no answers: Darpan's list waits, and says for what", S._tranche_pool(d, "med") == [] and "Try to match" in S._tranche_hold(d, "med") and "3 orthotic pairs" in S._tranche_hold(d, "med") and "1 medicine pair" in S._tranche_hold(d, "med"), S._tranche_hold(d, "med"))
    ins("ANKLE BINDER BAMBOO L", "ANKLE BINDER L TYNOR", 2, "YES"); ins("L S BELT CONT GRAY UNISON M", "L S BELT CONT GRAY UNISON L", 1, "YES")
    ins("KNEE SUPPORT HINGED XXL UNISO", "KNEE SUPPORT HINGED M", 1, "NO"); ins("MOTIF FORTE", "ASTOFEN P", 5, "NO")
    diffs, pairs = fixture(); words = {x["item"]: x["word"] for x in diffs if x["word"]}
    d = dict(differences=diffs, matches=S._match_apply(con, 1, diffs, pairs, words)); by = {x["item"]: x for x in diffs}
    ab = by["ANKLE BINDER BAMBOO L"]
    check("part swap: 3 short, 2 swapped -> 1 short, value a third", ab["diff"] == -1 and ab["diff_count_day"] == -3 and ab["mrp_p"] == int(round(-3 * 27520 / 3.0)) and not ab.get("word"), (ab["diff"], ab["mrp_p"], ab.get("word")))
    check("whole swap on the extra line reads 'swap confirmed'", by["ANKLE BINDER L TYNOR"]["diff"] == 0 and (by["ANKLE BINDER L TYNOR"]["word"] or {}).get("action") == "EXPLAINED")
    check("both LS belt lines settled", by["L S BELT CONT GRAY UNISON M"]["diff"] == 0 and by["L S BELT CONT GRAY UNISON L"]["diff"] == 0)
    check("a No changes nothing", by["KNEE SUPPORT HINGED XXL UNISO"]["diff"] == -1 and by["MOTIF FORTE"]["diff"] == -5)
    check("the count's own figures untouched", ab["marg"] == 3 and ab["counted"] == 0)
    d.update(count_id=1, day="06-09-2026")
    sv = S._swap_vouchers(d); svk = sorted((v["voucher"], v["item"], v["qty"], v["marg"], v["after"], v["change"]) for v in sv)
    print("   swap vouchers:", svk)
    check("S299 part swap: STOCK ISSUE 2 on the short item at once, Marg 3 -> 1 (no word on the rest yet)", ("ISSUE", "ANKLE BINDER BAMBOO L", 2, 3, 1, -2) in svk and not ab.get("word"), svk)
    check("S299 whole swap: STOCK RECEIVE 2 on the extra item, Marg 0 -> 2", ("RECEIVE", "ANKLE BINDER L TYNOR", 2, 0, 2, 2) in svk, svk)
    check("S299 LS belt: issue 1 on M (2 -> 1), receive 1 on L (2 -> 3)", ("ISSUE", "L S BELT CONT GRAY UNISON M", 1, 2, 1, -1) in svk and ("RECEIVE", "L S BELT CONT GRAY UNISON L", 1, 2, 3, 1) in svk, svk)
    check("S299: a No gives no voucher", not any(v["item"] in ("KNEE SUPPORT HINGED XXL UNISO", "KNEE SUPPORT HINGED M", "MOTIF FORTE", "ASTOFEN P") for v in sv))
    check("S299: every swap line says 'swap confirmed'", sv and all(v["reason"] == "swap confirmed" for v in sv))
    wv = S._word_vouchers(d)
    check("S299: a swap-settled line is not repeated as a word voucher", not any(x["item"] in ("ANKLE BINDER L TYNOR", "L S BELT CONT GRAY UNISON M", "L S BELT CONT GRAY UNISON L") for x in wv), [x["item"] for x in wv])
    rows = S._cleanup_rows(d)
    check("S299: no cleanup row reads CHANGE 0", rows and all(r[5] != 0 for r in rows), [(r[0], r[5]) for r in rows])
    check("S299: cleanup rows carry the voucher kind", all(r[2] in ("STOCK ISSUE", "STOCK RECEIVE") for r in rows) and rows[0][2] in ("STOCK ISSUE", "STOCK RECEIVE"))
    ab["word"] = dict(action="WRITE_OFF", label="written off", at_text="17-09-2026 19:00 IST")
    wv = {x["item"]: x for x in S._word_vouchers(d)}
    r1 = wv.get("ANKLE BINDER BAMBOO L") or {}
    check("S299: the remainder, once decided, runs from Marg-after-swap (1) to the shelf (0)", r1.get("marg_from") == 1 and r1.get("change") == -1 and r1.get("voucher") == "ISSUE", r1)
    chain = [r for r in S._cleanup_rows(d) if r[0] == "ANKLE BINDER BAMBOO L"]
    check("S299: keyed in order, the two rows end at the shelf", len(chain) == 2 and chain[0][3] == 3 and chain[0][4] == chain[1][3] == 1 and chain[1][4] == 0 and chain[0][5] + chain[1][5] == ab["counted"] - ab["marg"], chain)
    ab["word"] = None
    med = [x["item"] for x in S._tranche_pool(d, "med")]; ort = [x["item"] for x in S._tranche_pool(d, "ortho")]
    print("   after answers -- med list pool:", med, " ortho:", ort)
    check("all answered: the hold is gone", S._tranche_hold(d, "med") == "")
    check("medicine list: shortages only (no PARI CR, no ASTOFEN surplus), no parked ETOZOX", "ROSIKA FORTE" in med and "MOTIF FORTE" in med and "PARI CR 12.5" not in med and "ASTOFEN P" not in med and "ETOZOX 90" not in med, med)
    check("orthotic list: the part-swap remainder and the lone shortages, no settled or extra line", set(ort) >= {"ANKLE BINDER BAMBOO L", "RIB BELT S TYNOR", "KNEE SUPPORT HINGED XXL UNISO"} and "ANKLE BINDER L TYNOR" not in ort and "KNEE SUPPORT HINGED M" not in ort and "L S BELT CONT GRAY UNISON M" not in ort, ort)
    ins("ANKLE BINDER BAMBOO L", "ANKLE BINDER L TYNOR", 2, "OPEN")
    diffs, pairs = fixture(); words = {x["item"]: x["word"] for x in diffs if x["word"]}
    d = dict(differences=diffs, matches=S._match_apply(con, 1, diffs, pairs, words))
    check("an answer taken back restores the line and the hold", {x["item"]: x for x in diffs}["ANKLE BINDER BAMBOO L"]["diff"] == -3 and "1 orthotic pair" in S._tranche_hold(d, "med"), S._tranche_hold(d, "med"))
    spec = importlib.util.spec_from_file_location("pr_new", w["pad_receipt"]); PR = importlib.util.module_from_spec(spec); spec.loader.exec_module(PR)
    pdf = os.path.join(tmp, "l.pdf")
    io.open(pdf, "wb").write(PR.render_tranche(dict(count_id=1, day="06-09-2026", reasons=[(1, "count error", ""), (2, "not billed", "")],
        tranche=dict(no=1, kind="ortho", issued_text="17-09-2026 18:00"),
        rows=[dict(item="ANKLE BINDER BAMBOO L", packing="1*1", pack=1, marg=3, counted=0, diff=-3, swapped=2, swap_with=["ANKLE BINDER L TYNOR"]),
              dict(item="RIB BELT S TYNOR", packing="1*1", pack=1, marg=1, counted=0, diff=-1)])))
    tx = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    check("list heads Qty in Marg | Physical 06-Sep | Difference", re.search(r"Qty in Marg\s+Physical 06-Sep\s+Difference", tx) is not None, tx[:600])
    check("a swapped line prints its remainder", re.search(r"ANKLE BINDER BAMBOO L.*3 pc\s+0 pc\s+short 1 pc", tx) is not None, [l for l in tx.splitlines() if "ANKLE" in l])
    check("and says so under the item", "short 3 pc on the count; 2 pc swapped with ANKLE BINDER L TYNOR" in tx)
    check("an ordinary line unchanged", re.search(r"RIB BELT S TYNOR.*1 pc\s+0 pc\s+short 1 pc", tx) is not None)
    print("\n%d failed" % len(FAILS)); return 1 if FAILS else 0
if __name__ == "__main__": sys.exit(main())
