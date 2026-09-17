#!/usr/bin/env python3
"""selftest_s308.py -- proves S308_PURSUE_EVIDENCE offline.
Bytes: stock_app.py at S304's pin, stock_hub.html at S304's; anchors once; refusal; idempotence; backup;
compile; the hub script parses and lists the cards. Behaviour over an in-memory database: an item that sells
every week reads its units, bills and last sale; an item that never sold says so in as many words; sales since
the count and the last purchase are named; a return is netted off; only lines the owner marked to pursue make a
card, worst first; a line with no sale lines at all still makes a card and never raises.
    python3 -B selftest_s308.py --base <dir with stock_app.py (S304), stock_hub.html (S304), padwriter.py>"""
import argparse, hashlib, importlib.util, io, os, re, shutil, sqlite3, subprocess, sys, tempfile, types, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import patch_pursue_evidence_s308 as P  # noqa: E402
APP_FROM, HUB_FROM = "b997aa355d4b56a0794534369e38385f", "3f54859201892ec59dfc4455f07b330b"
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
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--base", required=True); a = ap.parse_args(argv)
    app = os.path.join(a.base, "stock_app.py")
    check("stock_app.py is the S304 pin", md5(app) == APP_FROM, md5(app))
    check("stock_hub.html (live) is the S304 pin", md5(os.path.join(a.base, "stock_hub.html")) == HUB_FROM)
    tmp = tempfile.mkdtemp(prefix="s308_"); w = os.path.join(tmp, "stock_app.py"); shutil.copy2(app, w)
    shutil.copy2(os.path.join(a.base, "padwriter.py"), os.path.join(tmp, "padwriter.py"))
    t = io.open(w, encoding="utf-8").read()
    for old, _ in P.APP_EDITS: check("anchor once: %s" % old.strip()[:40], t.count(old) == 1, t.count(old))
    cmd = [sys.executable, "-B", os.path.join(HERE, "patch_pursue_evidence_s308.py"), "--app", w]
    r = subprocess.run(cmd + ["--app-from", "0" * 32], capture_output=True, text=True); check("refuses a wrong --from", r.returncode != 0 and "REFUSING" in r.stdout + r.stderr)
    r = subprocess.run(cmd + ["--app-from", APP_FROM], capture_output=True, text=True); check("patches from the S304 pin", r.returncode == 0, r.stdout + r.stderr)
    h = md5(w)
    r = subprocess.run(cmd, capture_output=True, text=True); check("idempotent", md5(w) == h and "ALREADY" in r.stdout)
    check("backup is the S304 bytes", md5(w + ".bak_S308_" + APP_FROM[:8]) == APP_FROM)
    r = subprocess.run([sys.executable, "-m", "py_compile", w], capture_output=True, text=True); check("compiles", r.returncode == 0, r.stderr)
    hub = io.open(os.path.join(HERE, "stock_hub.html"), encoding="utf-8").read()
    sc = re.findall(r"<script[^>]*>(.*?)</script>", hub, re.S); js = os.path.join(tmp, "hub.js"); io.open(js, "w", encoding="utf-8").write(sc[-1])
    r = subprocess.run(["node", "--check", js], capture_output=True, text=True); check("hub script parses", r.returncode == 0, r.stderr[:300])
    check("hub step 8 lists the cards", "d.pursue.cards" in hub and "with the evidence in hand" in hub)
    print("predicted: stock_app.py %s · stock_hub.html %s" % (h, md5(os.path.join(HERE, "stock_hub.html"))))
    stub_flask(); sys.path.insert(0, tmp)
    spec = importlib.util.spec_from_file_location("sa308", w); S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
    S._unit = "medical"
    con = sqlite3.connect(":memory:")
    con.executescript("""CREATE TABLE sale_line_item (unit TEXT, item_key TEXT, bill_no TEXT, is_return INT,
        qty_raw TEXT, business_date TEXT, pack TEXT, amount_p INT);
        CREATE TABLE purchase_line (id INTEGER PRIMARY KEY, item TEXT, bill_date TEXT, qty TEXT, free TEXT, packing TEXT);""")
    sale = lambda item, bill, q, day, ret=0: con.execute("INSERT INTO sale_line_item VALUES ('medical',?,?,?,?,?,'1*10',0)", (S._sale_key(item), bill, ret, q, day))  # noqa: E731
    for i, day in enumerate(("2026-08-20", "2026-08-27", "2026-09-02", "2026-09-04")):
        sale("ROSIKA FORTE", "b%d" % i, "0:5", day)
    sale("ROSIKA FORTE", "r1", "0:2", "2026-09-03", ret=1)          # a return, netted off
    sale("ROSIKA FORTE", "b9", "0:3", "2026-09-10")                  # after the count
    sale("OLD ITEM", "b8", "0:4", "2026-05-01")                      # long before the window
    con.execute("INSERT INTO purchase_line (item, bill_date, qty, free, packing) VALUES ('ROSIKA FORTE','2026-08-18','2','0','1*10')")
    con.commit()
    x = lambda item, diff, mrp, word: dict(item=item, diff=diff, pack=10, packing="1*10", mrp_p=mrp, lookups=[], word=(dict(action=word, label=word) if word else None))  # noqa: E731
    d = dict(count_id=1, day="06-09-2026", differences=[x("ROSIKA FORTE", -12, -3600, "RECOVER"), x("OLD ITEM", -5, -9000, "RECOVER"),
                                                        x("NO LINES AT ALL", -2, -100, "RECOVER"), x("NOT PURSUED", -9, -99999, "WRITE_OFF")])
    cards = S._pursue_cards(con, d)
    by = {c["item"]: c for c in cards}
    check("only the lines marked to pursue get a card", sorted(by) == ["NO LINES AT ALL", "OLD ITEM", "ROSIKA FORTE"], sorted(by))
    check("worst first", [c["item"] for c in cards][0] == "OLD ITEM", [c["item"] for c in cards])
    c = by["ROSIKA FORTE"]
    check("a selling item: units net of the return, bills, last sale", c["before_units"] == 18 and c["before_bills"] == 4 and c["last_sale"] == "2026-09-10", c)
    check("...and it says so in words", "sold 1 strip 8 tabs on 4 bills in the 30 days before the count" in c["lines"][0] and "04-09-2026" in c["lines"][0], c["lines"])
    check("sales since the count are named", "sold 3 tabs since the count" in c["lines"][1], c["lines"])
    check("the last purchase is named", any("last bought 18-08-2026" in l for l in c["lines"]), c["lines"])
    check("the short quantity rides along", c["short_text"] == "1 strip 2 tabs", c["short_text"])
    c2 = by["OLD ITEM"]
    check("an item that did not sell in the window says so plainly", "NOT SOLD ONCE" in c2["lines"][0] and c2["before_units"] == 0, c2["lines"])
    check("...and nothing since the count", c2["lines"][1] == "nothing sold since the count", c2["lines"])
    check("no purchase line: no last-bought line, no crash", all("last bought" not in l for l in c2["lines"]))
    c3 = by["NO LINES AT ALL"]
    check("an item with nothing at all still makes a card", c3["before_units"] == 0 and c3["lines"][0].startswith("NOT SOLD ONCE"))
    d2 = dict(d, day="")
    check("a count with no day: an empty card, never a crash", S._pursue_cards(con, d2)[0]["lines"] == [])
    con2 = sqlite3.connect(":memory:")
    check("no tables at all: empty cards, no crash", [c["lines"] for c in S._pursue_cards(con2, d)] == [[], [], []])
    x2 = dict(x("WITH QUESTION", -3, -500, "RECOVER"), lookups=["Marg > item ledger: which voucher took 3 strips?", "second", "third"])
    cs = S._pursue_cards(con, dict(d, differences=[x2]))[0]
    check("the item's own Marg question rides with it, at most two", cs["lines"][-1] == "second" and "third" not in cs["lines"], cs["lines"])
    print("\n%d failed" % len(FAILS)); return 1 if FAILS else 0
if __name__ == "__main__": sys.exit(main())
