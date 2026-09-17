#!/usr/bin/env python3
"""selftest_s304.py -- proves S304_COUNT_PROOF offline.
Bytes: stock_app.py at S301's pin, stock_hub.html at S301's; anchors once; refusal; idempotence; backup;
compile; the hub script parses. Behaviour over an in-memory database: no voucher entered -> wait (and a
counting close never makes it done); entered but no later export -> now; the later export on the same
basis where every vouchered item moved by exactly its voucher -> PROVEN (done), an item moved without a
voucher counted but not blocking; an item that moved differently -> now, named; a voucher line not yet
entered keeps it from done; a re-based computed feed -> now, never a false proof.
    python3 -B selftest_s304.py --base <dir with stock_app.py (S301), stock_hub.html (S301), padwriter.py>"""
import argparse, hashlib, importlib.util, io, os, re, shutil, sqlite3, subprocess, sys, tempfile, types
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import patch_count_proof_s304 as P  # noqa: E402
APP_FROM, HUB_FROM = "5cc1328d9289ad8b1f662fe4d4e33ef4", "a3bfab191fb7ac2f0dd02bf6852ae9bf"
FAILS = []
def check(n, ok, d=""):
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else "  -- " + str(d)[:500]))
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
    check("stock_app.py is the S301 pin", md5(app) == APP_FROM, md5(app))
    check("stock_hub.html (live) is the S301 pin", md5(os.path.join(a.base, "stock_hub.html")) == HUB_FROM)
    tmp = tempfile.mkdtemp(prefix="s304_"); w = os.path.join(tmp, "stock_app.py"); shutil.copy2(app, w)
    shutil.copy2(os.path.join(a.base, "padwriter.py"), os.path.join(tmp, "padwriter.py"))
    t = io.open(w, encoding="utf-8").read()
    for old, _ in P.APP_EDITS: check("anchor once: %s" % old.strip()[:40], t.count(old) == 1, t.count(old))
    cmd = [sys.executable, "-B", os.path.join(HERE, "patch_count_proof_s304.py"), "--app", w]
    r = subprocess.run(cmd + ["--app-from", "0" * 32], capture_output=True, text=True); check("refuses a wrong --from", r.returncode != 0 and "REFUSING" in r.stdout + r.stderr)
    r = subprocess.run(cmd + ["--app-from", APP_FROM], capture_output=True, text=True); check("patches from the S301 pin", r.returncode == 0, r.stdout + r.stderr)
    h = md5(w)
    r = subprocess.run(cmd, capture_output=True, text=True); check("idempotent", md5(w) == h and "ALREADY" in r.stdout)
    check("backup is the S301 bytes", md5(w + ".bak_S304_" + APP_FROM[:8]) == APP_FROM)
    r = subprocess.run([sys.executable, "-m", "py_compile", w], capture_output=True, text=True); check("compiles", r.returncode == 0, r.stderr)
    hub = io.open(os.path.join(HERE, "stock_hub.html"), encoding="utf-8").read()
    sc = re.findall(r"<script[^>]*>(.*?)</script>", hub, re.S); js = os.path.join(tmp, "hub.js"); io.open(js, "w", encoding="utf-8").write(sc[-1])
    r = subprocess.run(["node", "--check", js], capture_output=True, text=True); check("hub script parses", r.returncode == 0, r.stderr[:300])
    check("hub step 7 reads the proof, not the counting close", "const P=d.proof" in hub and "d.proof.state" not in hub)
    check("the hub no longer computes step 7 from the counting close", 'proof=dict(state=("done" if d.get("closed")' not in io.open(w, encoding="utf-8").read())
    print("predicted: stock_app.py %s · stock_hub.html %s" % (h, md5(os.path.join(HERE, "stock_hub.html"))))
    stub_flask(); sys.path.insert(0, tmp)
    spec = importlib.util.spec_from_file_location("sa304", w); S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
    con = sqlite3.connect(":memory:"); S._feed_ensure(con); S._voucher_ensure(con); con.executescript(S.MATCH_SCHEMA)
    d = dict(count_id=1, day="06-09-2026", differences=[], matches=[], closed=dict(at="2026-09-06T14:43:14"))
    p = S._proof_state(con, d)
    check("no voucher entered -> wait, even though the counting was closed on 06-Sep", p["state"] == "wait", p)
    L = lambda it, kind, bno, ch: con.execute("INSERT INTO stock_voucher_line (count_id, round_no, kind, batch_no, batches_n, line_no, item, marg_from, change, marg_to, reason, made_at) VALUES (1,1,?,?,1,1,?,0,?,0,'x','2026-09-13T10:00:00')", (kind, bno, it, ch))  # noqa: E731
    L("A", "ISSUE", 1, -2); L("B", "RECEIVE", 1, 1)
    E = lambda kind, bno, no, at: con.execute("INSERT INTO stock_voucher_entered (count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at) VALUES (1,1,?,?,?,'13-09-2026','amir',?)", (kind, bno, no, at))  # noqa: E731
    E("ISSUE", 1, "SI-1", "2026-09-13T12:00:00"); E("RECEIVE", 1, "SR-1", "2026-09-13T12:05:00"); con.commit()
    def feed(as_on, source, rows, at):
        for it, q in rows.items():
            con.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES (?,?,?,?,?)", (as_on, source, it, q, at))
        con.commit()
    EXP = "push_expected base=03-09-2026 pur_to=%s"
    feed("12-09-2026", "push_snapshot", dict(A=5, B=3, C=10, D=4), "2026-09-12T23:00:00")
    feed("12-09-2026", EXP % "12-09-2026", dict(A=3, B=4, C=10, D=4), "2026-09-12T23:00:05")
    p = S._proof_state(con, d)
    check("entered, no export after them -> now, waiting for the next export", p["state"] == "now" and p["as_before"] == "12-09-2026" and "Waiting for the next Marg stock export" in p["text"], p)
    # 14-09: sales moved A by -1 in both figures; the vouchers moved Marg: A -2, B +1; C moved in Marg without a voucher
    feed("14-09-2026", "push_snapshot", dict(A=2, B=4, C=9, D=4), "2026-09-14T22:30:00")
    feed("14-09-2026", EXP % "14-09-2026", dict(A=2, B=4, C=10, D=4), "2026-09-14T22:30:05")
    p = S._proof_state(con, d)
    print("   proof:", p["state"], "|", p["text"])
    check("every vouchered item moved by exactly its voucher -> PROVEN (done)", p["state"] == "done" and p["agree"] == 2 and p["differ"] == 0 and p["as_after"] == "14-09-2026", p)
    check("an item that moved in Marg without a voucher is counted, not blocking", p["moved_without"] == 1)
    feed("13-09-2026", "push_snapshot", dict(A=9, B=9, C=9, D=9), "2026-09-13T23:00:00")
    feed("13-09-2026", EXP % "12-09-2026", dict(A=1, B=1, C=1, D=1), "2026-09-13T23:00:05")
    p = S._proof_state(con, d)
    check("an export whose computed figure lacks that day's purchases (pur_to behind) is never used", p["as_after"] == "14-09-2026" and p["state"] == "done", p)
    con.execute("DELETE FROM stock_feed WHERE as_on='13-09-2026'"); con.commit()
    feed("14-09-2026", "push_snapshot", dict(A=2, B=3, C=9, D=4), "2026-09-14T23:30:00")
    p = S._proof_state(con, d)
    check("B not moved in the newer export of the day -> now, B named", p["state"] == "now" and p["differ"] == 1 and any(r["item"] == "B" and not r["ok"] for r in p["rows"]), p)
    feed("14-09-2026", "push_snapshot", dict(A=2, B=4, C=9, D=4), "2026-09-15T00:10:00")
    L("D", "ISSUE", 2, -1); con.commit()
    p = S._proof_state(con, d)
    check("a voucher line made but not entered keeps it from done", p["state"] == "now" and p["pending_lines"] == 1 and p["differ"] == 0, p)
    E("ISSUE", 2, "", "2026-09-13T12:10:00"); con.commit()
    con.execute("DELETE FROM stock_voucher_line WHERE item='D'"); con.commit()
    feed("15-09-2026", "push_snapshot", dict(A=2, B=4, C=9, D=4), "2026-09-15T22:30:00")
    feed("15-09-2026", "push_expected base=15-09-2026 pur_to=15-09-2026", dict(A=2, B=4, C=9, D=4), "2026-09-15T22:30:05")
    con.execute("DELETE FROM stock_feed WHERE as_on='14-09-2026'"); con.commit()
    p = S._proof_state(con, d)
    check("a re-based computed feed -> now, never a false proof", p["state"] == "now" and "re-based" in p["text"], p)
    print("\n%d failed" % len(FAILS)); return 1 if FAILS else 0
if __name__ == "__main__": sys.exit(main())
