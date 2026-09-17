#!/usr/bin/env python3
"""selftest_s294.py -- proves S294_DARPAN_RECONCILED offline.
Bytes: the three files at their live pins; anchors once; refusal; idempotence; compile;
the desk script parses. Behaviour: the patched _tranche_pool/_tranche_hold driven as code
over a fixture shaped like count #1 (a consumable NIPRO line, a parked VINTAZ line, a
Marg-negative line, an undecided same-salt pair, an orthotic swap family, a bill-check
line, real losses) -- and the untouched pool over the same fixture as the control; then
render_tranche read back as text: Shelf counted | Marg stock | Difference, no paragraph.
    python3 -B selftest_s294.py --base base/     (base/ holds the three live files)
"""
import argparse, hashlib, importlib.util, io, os, re, shutil, subprocess, sys, tempfile, types
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import patch_darpan_reconciled_s294 as P  # noqa: E402
PINS = dict(stock_app="8615d64dbeda516e6efb6f025ec777b3", pad_receipt="a224e7b406dc2133048d9bff1523bc42", stock_desk="6b6636bfbcec022169532042ba6b7d53")
FAILS = []
def check(n, ok, d=""):
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else "  -- " + str(d)))
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
def fx():
    def x(item, lane, marg, counted, word=None):
        return dict(item=item, lane=lane, marg=marg, counted=counted, diff=counted - marg, mrp_p=(counted - marg) * 100, word=(dict(action=word) if word else None))
    diffs = [x("ROSIKA FORTE", "loss", 723, 553), x("FERONES HD", "loss", 394, 270), x("PARA CHECK", "recount", 10, 40),
             x("DISPO SYRINGE NIPRO 3ML", "consume", 62, 0), x("VINTAZ P 4500 INJ", "dead", 24, 0, "PARKED"),
             x("ALCOXIB 120", "recount", -13, 184), x("ETOBONE 60", "loss", 120, 112), x("INTACOXIA-60", "over", 10, 494),
             x("TYRO BR", "bill", 700, 470), x("ANKLE BINDER BAMBOO L", "ortho", 3, 0), x("ANKLE BINDER L TYNOR", "ortho", 0, 2, "EXPLAINED"),
             x("KNEE CAP M", "ortho", 5, 4), x("HYORTH XL", "loss", 1, 0, "PARKED"), x("SENT BACK", "loss", 9, 5, "RECOUNT")]
    pairs = [dict(salt="ETORICOXIB 60", over=[dict(item="INTACOXIA-60")], short=[dict(item="ETOBONE 60")])]
    fams = [dict(key="ANKLE BINDER L", short=3, over=2, members=[dict(item="ANKLE BINDER BAMBOO L", state="diff"), dict(item="ANKLE BINDER L TYNOR", state="diff")])]
    return dict(differences=diffs, pairs=pairs, ortho_families=fams)
FIXROWS = dict(count_id=1, day="06-09-2026", reasons=[(1, "count error", ""), (2, "not billed", "")], tranche=dict(no=1, kind="med", issued_text="17-09-2026 16:00"),
               rows=[dict(item="ROSIKA FORTE", packing="1*10", pack=10, marg=723, counted=553, diff=-170), dict(item="OVER ONE", packing="1*15", pack=15, marg=45, counted=60, diff=15)])
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--base", required=True); a = ap.parse_args(argv)
    src = {k: os.path.join(a.base, k + (".html" if k == "stock_desk" else ".py")) for k in PINS}
    for k, p in src.items(): check("%s is the live pin" % k, md5(p) == PINS[k], md5(p))
    tmp = tempfile.mkdtemp(prefix="s294_"); w = {k: os.path.join(tmp, os.path.basename(p)) for k, p in src.items()}
    for k in src: shutil.copy2(src[k], w[k])
    for (k, edits) in (("stock_app", P.APP_EDITS), ("pad_receipt", P.RECEIPT_EDITS), ("stock_desk", P.DESK_EDITS)):
        t = io.open(w[k], encoding="utf-8").read()
        for old, _ in edits: check("%s anchor once: %s" % (k, old.strip()[:30].replace("\n", " ")), t.count(old) == 1, t.count(old))
    cmd = [sys.executable, "-B", os.path.join(HERE, "patch_darpan_reconciled_s294.py"), "--app", w["stock_app"], "--receipt", w["pad_receipt"], "--desk", w["stock_desk"]]
    r = subprocess.run(cmd + ["--app-from", "0" * 32], capture_output=True, text=True); check("refuses a wrong --from", r.returncode != 0 and "REFUSING" in r.stdout + r.stderr)
    r = subprocess.run(cmd + ["--app-from", PINS["stock_app"], "--receipt-from", PINS["pad_receipt"], "--desk-from", PINS["stock_desk"]], capture_output=True, text=True)
    check("patches all three from the live pins", r.returncode == 0, r.stdout + r.stderr)
    h = {k: md5(p) for k, p in w.items()}
    r = subprocess.run(cmd, capture_output=True, text=True); check("idempotent", {k: md5(p) for k, p in w.items()} == h and r.stdout.count("ALREADY") == 3, r.stdout)
    for k, p in w.items(): check("%s backup is the live bytes" % k, md5(p + ".bak_S294_" + PINS[k][:8]) == PINS[k])
    r = subprocess.run([sys.executable, "-m", "py_compile", w["stock_app"], w["pad_receipt"]], capture_output=True, text=True); check("both Python files compile", r.returncode == 0, r.stderr)
    sc = re.findall(r"<script[^>]*>(.*?)</script>", io.open(w["stock_desk"], encoding="utf-8").read(), re.S); js = os.path.join(tmp, "s.js"); io.open(js, "w", encoding="utf-8").write(sc[0])
    r = subprocess.run(["node", "--check", js], capture_output=True, text=True); check("desk script parses", r.returncode == 0, r.stderr[:300])
    desk = io.open(w["stock_desk"], encoding="utf-8").read()
    check("desk link renamed: your copy (not for Darpan)", "your copy (not for Darpan)" in desk and "Hand sheet for Darpan" not in desk)
    check("desk links Darpan's list to the loss page (where the cut button is)", "cut and print it on the loss page" in desk and "esc(D.links.loss_page)" in desk)
    print("predicted: stock_app.py %s · pad_receipt.py %s · stock_desk.html %s" % (h["stock_app"], h["pad_receipt"], h["stock_desk"]))
    old = load(src["stock_app"], "sa_old"); new = load(w["stock_app"], "sa_new")
    d = fx()
    om = [x["item"] for x in old._tranche_pool(d, "med")]
    check("control: the old pool carried the Marg-negative, the paired, the bill-check lines", all(i in om for i in ("ALCOXIB 120", "ETOBONE 60", "TYRO BR", "INTACOXIA-60")), om)
    nm = [x["item"] for x in new._tranche_pool(d, "med")]; no = [x["item"] for x in new._tranche_pool(d, "ortho")]
    check("new: no medicine list while a same-salt pair waits for his word", nm == [], nm)
    check("new: no orthotic list while a swap family waits for his word", no == [], no)
    hm = new._tranche_hold(d, "med"); print("   hold:", hm)
    check("hold names both: the pair and the orthotic family", "1 same-salt pair" in hm and "ANKLE BINDER L" in hm and "after the swaps" in hm, hm)
    d["differences"][9]["word"] = dict(action="MARG_FIX")   # the ankle-binder swap decided on the desk
    check("still no list: the pair is still open", new._tranche_pool(d, "med") == [] and "1 same-salt pair" in new._tranche_hold(d, "med") and "ANKLE" not in new._tranche_hold(d, "med"))
    for x in d["differences"]:
        if x["item"] == "ETOBONE 60": x["word"] = dict(action="RECOUNT")
        if x["item"] == "INTACOXIA-60": x["word"] = dict(action="EXPLAINED")
    nm = [x["item"] for x in new._tranche_pool(d, "med")]; no = [x["item"] for x in new._tranche_pool(d, "ortho")]
    print("   new med pool:", nm, " ortho:", no)
    check("every swap has his word: the hold is gone", new._tranche_hold(d, "med") == "" and new._tranche_hold(d, "ortho") == "")
    check("new: real losses and a cannot-be-real line are on the list", all(i in nm for i in ("ROSIKA FORTE", "FERONES HD", "PARA CHECK")), nm)
    check("new: a RECOUNT word keeps a line on the list (the paired one he sent on too)", "SENT BACK" in nm and "ETOBONE 60" in nm, nm)
    check("new: no consumable (NIPRO)", "DISPO SYRINGE NIPRO 3ML" not in nm)
    check("new: no parked line (VINTAZ, HYORTH)", "VINTAZ P 4500 INJ" not in nm and "HYORTH XL" not in nm)
    check("new: no Marg-negative line (a voucher)", "ALCOXIB 120" not in nm)
    check("new: no explained surplus, no bill-check lane", "INTACOXIA-60" not in nm and "TYRO BR" not in nm)
    check("new: no orthotic on the medicine list", not any("ANKLE" in i or "KNEE" in i for i in nm))
    check("orthotics list: the swapped binder is settled, the open knee cap remains", no == ["KNEE CAP M"], no)
    pr = importlib.util.spec_from_file_location("pr_new", w["pad_receipt"]); prm = importlib.util.module_from_spec(pr); pr.loader.exec_module(prm)
    pdf = os.path.join(tmp, "l.pdf"); io.open(pdf, "wb").write(prm.render_tranche(dict(FIXROWS)))
    tx = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    check("list heads Shelf counted | Marg stock | Difference, in that order", re.search(r"Shelf counted\s+Marg stock\s+Difference", tx) is not None)
    check("the instruction paragraph is gone", "Do not count" not in tx and "These are the differences" not in tx)
    check("the date and what the figures are, in one line", "Stock count of 06-09-2026 - shelf counted that day, Marg stock export of that day" in tx)
    check("row reads shelf, Marg, difference", re.search(r"ROSIKA FORTE.*55s 3t\s+72s 3t\s+short 17s", tx) is not None, [l for l in tx.splitlines() if "ROSIKA" in l])
    check("surplus still reads over", "over 1s" in tx)
    check("reason legend and the two boxes' heads remain", "REASON:" in tx and "REASON no." in tx and "REMARKS" in tx)
    print("\n%d failed" % len(FAILS)); return 1 if FAILS else 0
if __name__ == "__main__": sys.exit(main())
