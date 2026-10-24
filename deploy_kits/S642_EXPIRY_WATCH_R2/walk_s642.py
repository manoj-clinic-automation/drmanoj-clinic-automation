#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s642.py -- kit S642_EXPIRY_WATCH_R2 (Sanjeevni, session 348, 24-Oct-2026): S638's walk, one check corrected (F-1020).  Runs on SCRATCH folders and SCRATCH databases only.

    python3 -B walk_s642.py --side <dir> --pc <dir with the medical PC's marg_txt.py (the kit's TO, copied out)> [--expect-red]

<dir> holds a scratch copy of the box: fin/ (/root/finance, spine/spine.db a backup-API copy of the live spine), marg/ (/root/marg_ingest
with its archive), por/ (/root/portal), finance.db and assets.db (backup-API copies).  The walk makes its OWN Batch Stock -- a made-up
text in Marg's exact layout, the shop's letterhead replaced by TEST lines, built from the spine's own newest closing so it is the whole
shop -- converts it with the medical PC's reader, sends it through the server's one door (marg_take.take, the scratch archive), runs the
nightly (spine/near_expiry.py), and reads every screen through the real finance app (its own header session; never the live secret or
user store) as the owner, Darpan, Amir, Shivani and reception.  Its own rows by key (W638 ...), never by counting.  No phone number is
printed.  --expect-red is the negative control: the same walk on the OLD files -- every 'C:' check must be red.

Prints 'WALK OK S642 <n> checks' (NEW) or 'WALK NEGATIVE CONTROL RED S642 <n> controls' (OLD); anything else is a failed walk."""
import argparse
import datetime as dt
import glob
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile

# never import from the kit folder (rulebook 11): the kit holds expiry_watch.py, and an import from it would pass the OLD side
_ME = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _ME]
KIT = "S642_EXPIRY_WATCH_R2"   # S638 again (F-1020): the same twelve files; this check corrected
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff", "shivani": "staff"}
RES = []


def say(*a):
    print(*a, flush=True)


def ck(name, ok, got=None, control=False):
    RES.append((name, bool(ok), control))
    say("%s %s%s%s" % ("  ok  " if ok else "  RED ", "C: " if control else "", name, "" if got is None else "   [%s]" % str(got)[:160]))


def mask(s):
    return re.sub(r"\d{10,}", "##########", s)


def copy_db(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------------------------------------ the made-up Batch Stock
def _t(*parts):
    s = ""
    for col, txt in parts:
        a = col if col >= 0 else (-col - len(txt) + 1)
        s = s.ljust(a) + txt
    return s


def made_up_batch_stock(spine_db, today):
    """A Batch Stock in Marg's own text layout from the spine's newest closing (every item in stock, one batch each, expiry far off),
    except three items the walk names: E expired (this month), N near (next month), W wrong batch (a batch at -1 beside its stock)."""
    sp = sqlite3.connect("file:%s?mode=ro" % spine_db, uri=True)
    on = sp.execute("SELECT MAX(as_on) FROM sp_close").fetchone()[0]
    rows = sp.execute("SELECT c.k20, c.units, i.name, i.packing FROM sp_close c JOIN sp_item i ON i.k20=c.k20 WHERE c.as_on=? AND c.units>0 "
                      "GROUP BY c.k20 ORDER BY i.name", (on,)).fetchall()
    sp.close()
    items = []
    for k20, units, name, packing in rows:
        if len(name) > 30 or not re.match(r"^1\*\d+$|^1$", packing or ""):
            continue
        pack = int(packing.split("*")[1]) if "*" in packing else 1
        items.append(dict(k20=k20, name=name, packing=packing, pack=pack, units=int(units)))
    strips = [x for x in items if x["pack"] >= 10 and x["units"] >= 30]
    E, N, W, Y = strips[0], strips[1], strips[2], strips[3]
    exp_e = "%d/%d" % (today.month, today.year)
    nm = today.month % 12 + 1
    ny = today.year + (1 if today.month == 12 else 0)
    exp_n = "%d/%d" % (nm, ny)
    lines = ["", _t((31, "TEST MEDICOS")), _t((24, "TEST STREET , TESTTOWN")), _t((16, "GSTIN : TESTGST  TIN No. : TESTTIN")), "",
             _t((19, "WHOLE STORES CLOSING STOCK AS ON %s" % dt.date.fromisoformat(on).strftime("%d-%m-%Y"))), "-" * 80,
             _t((0, "S.No. Description"), (44, "Batch"), (57, "Expiry"), (70, "Stock Unit")), "-" * 80]
    n, total = 0, 0

    def q(u, pack):
        if pack <= 1:
            return str(u)
        s = "-" if u < 0 else ""
        return "%s%d:%d" % (s, abs(u) // pack, abs(u) % pack)

    def row(x, batch, exp, u):
        nonlocal n, total
        n += 1
        total += u
        return _t((-4, str(n)), (6, x["name"]), (37, x["packing"]), (44, batch), (-62, exp), (-75, q(u, x["pack"])), (77, "STR" if x["pack"] > 1 else "ITE"))
    half = len(items) // 2
    for i_, x in enumerate(items):
        if i_ == half:                                       # a page break, as Marg prints one (Continued / letterhead / Page No / head)
            lines += ["-" * 80, _t((66, "Continued..2")), "", "", "", "TEST MEDICOS", _t((68, "Page No..2")),
                      "WHOLE STORES CLOSING STOCK AS ON %s" % dt.date.fromisoformat(on).strftime("%d-%m-%Y"), "-" * 80,
                      _t((0, "S.No. Description"), (44, "Batch"), (57, "Expiry"), (70, "Stock Unit")), "-" * 80]
        if x is Y:                                           # two batches with stock (the re-supply test sells one below zero)
            a_ = x["units"] // 2
            lines.append(row(x, "W638Y1", "3/2031", a_))
            lines.append(row(x, "W638Y2", "4/2031", x["units"] - a_))
            lines += [_t((47, "-" * 33)), _t((47, "Batch TOTAL"), (-75, str(x["units"])))]
        elif x is W:
            lines.append(row(x, "W638NEG", "1/2031", -x["pack"]))
            lines.append(row(x, "W638POS", "2/2031", x["units"] + x["pack"]))
            lines += [_t((47, "-" * 33)), _t((47, "Batch TOTAL"), (-75, str(x["units"])))]
        elif x is E:
            lines.append(row(x, "W638EXP", exp_e, x["units"]))
        elif x is N:
            lines.append(row(x, "W638NEAR", exp_n, x["units"]))
        else:
            lines.append(row(x, "W638B%d" % (n + 1), "12/2030", x["units"]))
        lines.append("")
    # a batch that fills its 12 places runs into its expiry (Marg's own print: 'LGP11/244/0710/2027'); a bottle item, plain stock
    lines.append(row(dict(name="W638 LONG BATCH TAB", packing="1*10", pack=10), "W638LONG1234", "10/2030", 25))
    lines.append("")
    lines.append(row(dict(name="W638 LOTION", packing="60ML", pack=1), "W638LOT", exp_n, 3))
    lines.append("")
    lines += ["-" * 80, _t((0, "TOTAL"), (-75, str(total))), "-" * 80, "*** End of Report ***"]
    raw = ("\r\n".join(lines) + "\r\n").encode("latin-1")
    return raw, dict(E=E, N=N, W=W, Y=Y, on=on, n_items=len(items))


# ------------------------------------------------------------------------------------------------ the walk
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", required=True)
    ap.add_argument("--pc", required=True)
    ap.add_argument("--expect-red", action="store_true")
    a = ap.parse_args()
    side = os.path.abspath(a.side)
    fin, marg, por = os.path.join(side, "fin"), os.path.join(side, "marg"), os.path.join(side, "por")
    dbp, adb = os.path.join(side, "finance.db"), os.path.join(side, "assets.db")
    spine_db = os.path.join(fin, "spine", "spine.db")
    today = dt.date.today()
    SIDE = "OLD" if a.expect_red else "NEW"
    say("walk_s638 on %s (%s)" % (side, SIDE))
    spine_md5_0 = hashlib.md5(open(spine_db, "rb").read()).hexdigest()
    # the scratch copy starts as the box was BEFORE any S638 run: a re-install after an undo leaves the two (inert) tables and the
    # expiry.* settings behind -- the walk clears them in its own copy, so the negative control judges the code, never the leftovers
    c0 = sqlite3.connect(dbp)
    c0.execute("DROP TABLE IF EXISTS stock_expiry_line")
    c0.execute("DROP TABLE IF EXISTS stock_expiry_run")
    c0.execute("DELETE FROM setting WHERE key LIKE 'expiry.%'")
    c0.commit()
    c0.close()

    # 1 · the medical PC's reader takes Marg's Batch Stock (the kit's TO; the same file on both sides)
    mt = load(os.path.join(a.pc, "marg_txt.py"), "marg_txt_w638")
    raw, who = made_up_batch_stock(spine_db, today)
    k = mt.kind(raw)
    ck("the medical PC's reader recognises a Batch Stock text (kind EXPIRY)", k == "EXPIRY", k)
    xls, info = mt.convert(raw)
    ck("it converts to the sheet (%d rows)" % info["rows"], len(xls) > 4096)
    r = subprocess.run([sys.executable, "-B", os.path.join(a.pc, "marg_txt.py"), "--selftest"], capture_output=True, text=True, timeout=600)
    ck("the reader's own selftest (S638 included)", "SELFTEST OK" in r.stdout and "S638:" in r.stdout, r.stdout.strip().splitlines()[-1:])

    # 2 · the stock figure BEFORE the file reaches the door (the witness, kept to compare after the door and the nightly)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=adb, SPINE_DB=spine_db)
    token = secrets.token_hex(16)
    os.environ.update(FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=marg, ORDER_PUSH_NONE="1", FINANCE_SSO_DIR=os.path.join(side, "nosso"),
                      RING_PORTAL_DIR=os.path.join(side, "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token,
                      TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"))
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for kk in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "DUTY_MAP_JSON"):
        os.environ.pop(kk, None)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_figure as SF                                # noqa: E402
    assert SF.__file__.startswith(fin)
    when = dt.datetime(2026, 10, 26, 23, 58, 2)
    work = tempfile.mkdtemp(prefix="w638_")

    def wit(tag):
        d = os.path.join(work, tag)
        os.makedirs(d, exist_ok=True)
        con = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True, timeout=60)
        p = SF.witness(con, SF._sw().Spine(), out_dir=d, when=when)
        con.close()
        return "\n".join(open(p, encoding="utf-8").read().splitlines()[1:])
    w0 = wit("before")
    # 3 · the door files it as BATCH_STOCK (F-1008), never a closing
    for p in (os.path.join(marg, "lib"), marg):
        sys.path.insert(0, p)
    os.environ["MARG_INGEST"] = marg
    import marg_take as T                                    # noqa: E402
    assert T.__file__.startswith(marg), T.__file__
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    name = "%s__%s__user_aa0000000000_TXT__w638.xls" % (stamp, stamp)
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        tk = T.take(xls, name=name, source="push", db=dbp, archive=os.path.join(marg, "archive"))
    ck("the door takes it (%s)" % tk["status"], tk["status"] == "TAKEN" and tk["verdict"] == "VERIFIED", (tk["type"], tk["variant"], tk.get("reason")))
    ck("filed under its own name, BATCH_STOCK (F-1008)", tk["type"] == "BATCH_STOCK", tk["type"], control=True)
    ck("never in the closing-stock folder", not glob.glob(os.path.join(marg, "archive", "STOCK_CLOSING", "*", "*%s*" % stamp)), control=True)
    sys.path.insert(0, os.path.join(fin, "spine"))
    import marg_read                                         # noqa: E402
    arch = glob.glob(os.path.join(marg, "archive", "*", "*", "*%s*" % stamp))
    ck("the spine's reader does not take it as a closing (identify None)", arch and marg_read.identify(marg_read.rows_of(arch[0])) is None, arch[:1])

    # the nightly, as cron runs it
    r = subprocess.run([sys.executable, "-B", os.path.join(fin, "spine", "near_expiry.py")], cwd=os.path.join(fin, "spine"),
                       capture_output=True, text=True, timeout=900, env=dict(os.environ, MARG_INGEST=marg))
    say("   nightly: " + mask((r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "(silent)"))
    w1 = wit("after")
    ck("every item's stock figure byte-identical with the report and its list (the witness, %d lines)" % len(w0.splitlines()),
       w0 == w1 and len(w0.splitlines()) > 50)
    ck("the spine is not written by anything here", hashlib.md5(open(spine_db, "rb").read()).hexdigest() == spine_md5_0)

    con = sqlite3.connect(dbp, timeout=60)
    con.row_factory = sqlite3.Row
    has = con.execute("SELECT 1 FROM sqlite_master WHERE name='stock_expiry_run'").fetchone() is not None
    ck("the nightly made a list (stock_expiry_run)", has, control=True)
    run = con.execute("SELECT * FROM stock_expiry_run ORDER BY id DESC LIMIT 1").fetchone() if has else None
    ck("from the walk's own Batch Stock, whole shop (%s items)" % (run["export_items"] if run else "-"),
       bool(run) and stamp in (run["export_name"] or "") and run["whole"] == 1, (dict(run) if run else None), control=True)
    L = {}
    if has and run:
        for x in con.execute("SELECT * FROM stock_expiry_line WHERE run_id=?", (run["id"],)):
            L.setdefault(x["section"], []).append(dict(x))
    E, N, W = who["E"], who["N"], who["W"]
    ck("expired: the walk's expired batch (%s W638EXP)" % E["name"], any(x["batch"] == "W638EXP" for x in L.get("expired", [])), control=True)
    ck("near expiry: the walk's batch that stops on the 1st of next month", any(x["batch"] == "W638NEAR" for x in L.get("near", [])), control=True)
    ck("wrong batch: the walk's -1 strip beside its stock", any("W638NEG" in (x["batch"] or "") for x in L.get("wrong", [])), control=True)
    ck("no other batch of the walk's file is expired or near", not [x for x in L.get("expired", []) + L.get("near", [])
                                                                  if x["batch"].startswith("W638B")])
    ck("a page break, a batch run into its expiry, a bottle item: read (W638LOT near, 3; W638LONG1234 not near)",
       any(x["batch"] == "W638LOT" and x["units"] == 3 for x in L.get("near", []))
       and not any(x["batch"].startswith("W638LONG") for x in L.get("near", []) + L.get("expired", [])), control=True)
    for name_, ok_ in _logic(fin, spine_db, dbp, marg, who, today):
        ck(name_, ok_, control=True)
    # 3b · a filtered batch print is kept, never used
    ck("a filtered batch list (40 batches) is never taken as the shop", True if a.expect_red else _filtered_not_used(con, fin, marg, dbp, spine_db, mt, today))

    # 4 · the screens, through the real finance app
    import finance_app as fa                                 # noqa: E402
    assert fa.__file__.startswith(fin)
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none"))
    cl = fa.app.test_client(use_cookies=False)

    def GET(u, path):
        r_ = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, follow_redirects=(u == "amir"))
        return r_.status_code, r_.get_data().decode("utf-8", "replace")

    def POST(u, path, data=None, js=None):
        r_ = cl.post(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, data=data, json=js)
        return r_.status_code, r_.get_data().decode("utf-8", "replace")
    s, h = GET("manoj", "/finance/sanjeevni/expiry")
    ck("the owner's page opens (%d)" % s, s == 200 and "Expired medicines" in h and "Near expiry" in h and "Dump" in h and "Wrong batch" in h
       and "New products" in h and "Out of stock" in h, s, control=True)
    ck("it names the walk's expired and near batches", "W638EXP" in h and "W638NEAR" in h, control=True)
    s2, _h2 = GET("darpan", "/finance/sanjeevni/expiry")
    ck("Darpan cannot open the owner's page", s2 != 200 or "Expired medicines" not in _h2, s2)
    s, h = POST("manoj", "/finance/sanjeevni/expiry/settings", data={"expiry.near_days": "120", "expiry.bold_strips": "abc"})
    v = con.execute("SELECT value FROM setting WHERE key='expiry.near_days'").fetchone()
    ck("a setting saved from the page (near_days 120; a non-number ignored)", s == 200 and v and v[0] == "120"
       and (con.execute("SELECT value FROM setting WHERE key='expiry.bold_strips'").fetchone() or ["5"])[0] == "5", (s, v and v[0]), control=True)
    con.execute("UPDATE setting SET value='90' WHERE key='expiry.near_days'")
    con.commit()
    s, h = GET("manoj", "/finance/sanjeevni/api/needs-you")
    j = json.loads(h) if s == 200 else {}
    ny = [x for x in j.get("lines", []) if "Expiry watch" in x.get("text", "")]
    ck("Needs you: the expiry line, opening the page", ny and ny[0].get("href") == "/finance/sanjeevni/expiry", [x.get("text") for x in ny], control=True)
    s, h = GET("manoj", "/finance/approvals")
    ck("the approvals page follows a line's href, and links the page", "l.href?" in h and "/finance/sanjeevni/expiry" in h, control=True)
    # Darpan's tab
    s, h = GET("darpan", "/finance/darpan/kal/api/order")
    jo = json.loads(h) if s == 200 and h.strip().startswith("{") else {}
    sf = jo.get("sell_first") or []
    ck("Darpan's order tab carries the batches to sell first (%d group%s)" % (len(sf), "" if len(sf) == 1 else "s"),
       any(r_["batch"] == "W638NEAR" for g in sf for r_ in g.get("rows", [])), [g.get("label") for g in sf], control=True)
    page = open(os.path.join(fin, "darpan_kal.html"), encoding="utf-8").read()
    ck("his tab draws them: 'In batches ko pehle bechein', batch and stock, nothing to tap",
       "In batches ko pehle bechein" in page and "function sellFirst(j)" in page and "let h=sellFirst(j);" in page, control=True)
    # Amir's card
    s, h = GET("amir", "/finance/amir")
    ck("Amir's page: the expired batch to write off or return", s == 200 and "Marg mein expiry write-off ya stockist ko return karein" in h
       and "W638EXP" in h, s, control=True)
    ck("Amir's page: the batches to correct (folded)", "dawaon ka batch theek karein" in h, control=True)
    ck("Amir's page: no Batch Stock card -- this month's has come", "Mahine ki report: Batch Stock" not in h)
    held = con.execute("SELECT md5, received_at FROM mi_file WHERE type='BATCH_STOCK'").fetchall()
    con.execute("UPDATE mi_file SET received_at='2000-01-01T00:00:00+05:30' WHERE type='BATCH_STOCK'")
    con.commit()
    s, h = GET("amir", "/finance/amir")
    ck("Amir's page: the Batch Stock card with its eight steps while the month's file has not come", "Mahine ki report: Batch Stock (poora store)" in h
       and "Stocks</b> &rarr; <b>Batch Stock" in h, control=True)
    s, hn = GET("manoj", "/finance/sanjeevni/api/needs-you")
    if today.day >= 7:
        ck("Needs you after the 7th: the month's Batch Stock not received", "Batch Stock not received" in hn, control=True)
    for m5, at in held:
        con.execute("UPDATE mi_file SET received_at=? WHERE md5=?", (at, m5))
    con.commit()
    ck("Amir's day is never held open by these lines (his_line False)", _his_lines_false(fin), control=True)
    # Shivani (D778)
    g = json.load(open(os.path.join(por, "tile_grants.json"), encoding="utf-8"))
    ck("Shivani's home shows 'Aaj ki reports' (D778)", "Aaj ki reports" in (g["users"].get("shivani") or {}).get("extra", []), control=True)
    s, h = GET("shivani", "/finance/reports/aaj")
    ck("her login opens /finance/reports/aaj -- the page itself, not its refusal (%d)" % s,      # F-1020: never a line that shows only while due
       s == 200 and "<h1>Aaj ki reports</h1>" in h and "Nahin khul saka" not in h, s)
    # reception's late card (F-1015)
    oid = _late_order(con)
    s, h = GET("reception", "/finance/porders/s454/late")
    ck("reception: a late order where nothing came names its medicines and quantities (F-1015)",
       "W638 MED ONE" in h and "W638 MED TWO" in h and "s638aw" in h, s, control=True)
    con.execute("DELETE FROM purchase_order_line WHERE order_id=?", (oid,))
    con.execute("DELETE FROM purchase_order WHERE id=?", (oid,))
    con.commit()
    # the SMS-seen NEFT (F-1014)
    ev, month = _sms_event(con)
    if ev:
        s, h = GET("manoj", "/finance/purchase/page/pay/%s" % month)
        ck("the pay page offers the confirm for an SMS-seen NEFT (F-1014)", "Seen in bank SMS" in h, s, control=True)
        s, h = POST("manoj", "/finance/sanjeevni/api/neft-event/ok", js={"id": ev})
        n1 = con.execute("SELECT COUNT(*) FROM supplier_msg WHERE kind='neft' AND ref=?", (ev,)).fetchone()[0]
        ck("the owner's OK queues the suppliers' messages (%d)" % n1, n1 > 0, h[:120], control=True)
        s, h = POST("manoj", "/finance/sanjeevni/api/neft-event/ok", js={"id": ev})
        n2 = con.execute("SELECT COUNT(*) FROM supplier_msg WHERE kind='neft' AND ref=?", (ev,)).fetchone()[0]
        ck("a second OK adds nothing (idempotent)", n2 == n1 and '"already"' in h.replace(" ", ""), (n1, n2))
    else:
        ck("a finalised month with a NEFT portion exists in the copy (for F-1014)", False, "none")
    # the duty map's new SQL runs (one row: n, since)
    for sql in DUE_SQL:
        try:
            row = con.execute(sql).fetchone()
            ok_ = row is not None and len(row) == 2
        except sqlite3.Error as ex:
            ok_, row = False, str(ex)
        ck("duty SQL runs: %s" % sql[:60], ok_, tuple(row) if ok_ else row)
    con.close()
    shutil.rmtree(work, ignore_errors=True)

    n_ok = sum(1 for r_ in RES if r_[1])
    ctrl = [r_ for r_ in RES if r_[2]]
    if a.expect_red:
        red = [r_ for r_ in ctrl if not r_[1]]
        if len(red) == len(ctrl):
            say("WALK NEGATIVE CONTROL RED S642 %d controls" % len(ctrl))
            return 0
        say("WALK NEGATIVE CONTROL NOT RED S642: %d of %d controls passed on the OLD files: %s"
            % (len(ctrl) - len(red), len(ctrl), [r_[0] for r_ in ctrl if r_[1]]))
        return 1
    if n_ok == len(RES):
        say("WALK OK S642 %d checks (%d controls)" % (len(RES), len(ctrl)))
        return 0
    say("WALK RED S642: %d of %d failed: %s" % (len(RES) - n_ok, len(RES), [r_[0] for r_ in RES if not r_[1]]))
    return 1


DUE_SQL = [
    "SELECT CASE WHEN EXISTS (SELECT 1 FROM stock_expiry_run r WHERE r.id = (SELECT MAX(id) FROM stock_expiry_run WHERE ok = 1) AND r.whole = 1 AND substr(r.export_as_on,1,7) = strftime('%Y-%m','now','localtime')) OR EXISTS (SELECT 1 FROM mi_file f WHERE f.type = 'BATCH_STOCK' AND f.verdict = 'VERIFIED' AND substr(f.received_at,1,7) = strftime('%Y-%m','now','localtime') AND replace(substr(f.received_at,1,19),'T',' ') > COALESCE((SELECT replace(substr(at,1,19),'T',' ') FROM stock_expiry_run WHERE ok = 1 ORDER BY id DESC LIMIT 1), '')) THEN 0 ELSE 1 END AS n, date('now','localtime','start of month') AS since",
    "SELECT COUNT(*) AS n, MIN(r.today) AS since FROM stock_expiry_line l JOIN stock_expiry_run r ON r.id = l.run_id WHERE l.section = 'expired' AND l.units > 0 AND r.id = (SELECT MAX(id) FROM stock_expiry_run WHERE ok = 1)",
    "SELECT COUNT(*) AS n, MIN(r.today) AS since FROM stock_expiry_line l JOIN stock_expiry_run r ON r.id = l.run_id WHERE l.section = 'wrong' AND l.part = 'batch' AND r.id = (SELECT MAX(id) FROM stock_expiry_run WHERE ok = 1)",
    "SELECT COUNT(*) AS n, MIN(l.expiry) AS since FROM stock_expiry_line l JOIN stock_expiry_run r ON r.id = l.run_id WHERE l.section = 'near' AND l.units > 0 AND l.expiry <= strftime('%Y-%m', 'now', 'localtime', 'start of month', '+' || COALESCE((SELECT value FROM setting WHERE key = 'expiry.darpan_months'), '2') || ' months') AND r.id = (SELECT MAX(id) FROM stock_expiry_run WHERE ok = 1)",
]


def _logic(fin, spine_db, dbp, marg, who, today):
    """The watch's own rules on SCRATCH copies of the spine (the walk's rows only): a credit note puts its units back on its batch;
    a batch written off in Marg (the closing fell by it beyond the sales) leaves Amir's list; a batch sold below zero beside one with stock
    is named; after a re-supply (no batch on the spine) only Marg's printed minus counts."""
    out = []
    try:
        import expiry_watch as EW                            # noqa: PLC0415
        assert EW.__file__.startswith(fin)
    except Exception:                                        # noqa: BLE001
        return [("the watch's rules (returns, written off, oversold, re-supply)", False)]
    on = who["on"]
    d1 = (dt.date.fromisoformat(on) + dt.timedelta(days=1)).isoformat()
    arch = os.path.join(marg, "archive")
    E, N, Y = who["E"], who["N"], who["Y"]

    def run_on(mut):
        p = os.path.join(tempfile.mkdtemp(prefix="w638s_"), "spine.db")
        copy_db(spine_db, p)
        c = sqlite3.connect(p)
        mut(c)
        c.commit()
        c.close()
        con = sqlite3.connect(":memory:")
        copy_db(dbp, os.path.join(os.path.dirname(p), "f.db"))
        con = sqlite3.connect(os.path.join(os.path.dirname(p), "f.db"))
        sp, alias = EW._spine(p)
        r, lines = EW.compute(con, sp, alias, arch, max(today, dt.date.fromisoformat(d1)))
        sp.close()
        con.close()
        shutil.rmtree(os.path.dirname(p), ignore_errors=True)
        return lines

    def sale(c, bill, k20, batch, units, cn):
        c.execute("INSERT INTO sp_sale_bill (date, bill, gross_p, disc_p, tax_p, drcr_p, net_p, cash_p, credit_note, source_md5) "
                  "VALUES (?,?,0,0,0,0,0,0,?,'w638')", (d1, bill, cn))
        c.execute("INSERT INTO sp_sale_line (date, bill, seq, name20, k20, pack, qty_raw, units, rate_p, batch, expiry) "
                  "VALUES (?,?,1,?,?,'1*10','',?,0,?,'')", (d1, bill, k20, k20, units, batch))
    ln = run_on(lambda c: sale(c, "CNW638", N["k20"], "W638NEAR", 5, 1))
    got = [x["units"] for x in ln if x["section"] == "near" and x["batch"] == "W638NEAR"]
    out.append(("a credit note puts its units back on its batch (%s -> %s)" % (N["units"], got), got == [N["units"] + 5]))

    def wo(c):
        c0 = c.execute("SELECT units FROM sp_close WHERE k20=? AND as_on=?", (E["k20"], on)).fetchone()[0]
        c.execute("INSERT INTO sp_close (as_on, k20, units, source_md5) VALUES (?,?,?,'w638')", (d1, E["k20"], c0 - E["units"]))
    ln = run_on(wo)
    out.append(("a batch Marg's closing shows written off leaves the expired list (Amir is not asked twice)",
                not any(x["batch"] == "W638EXP" for x in ln if x["section"] == "expired")))
    a_ = Y["units"] // 2
    ln = run_on(lambda c: sale(c, "AW638", Y["k20"], "W638Y1", a_ + 7, 0))
    out.append(("a batch sold below zero beside one with stock is named wrong", any(x["section"] == "wrong" and "W638Y1" in (x["batch"] or "")
                                                                                    for x in ln)))

    def resup(c):
        sale(c, "AW638", Y["k20"], "W638Y1", a_ + 7, 0)
        c.execute("INSERT INTO sp_move (k20, date, kind, units, ref) VALUES (?,?,'PURCHASE',?,'w638')", (Y["k20"], d1, a_ + 20))
    ln = run_on(resup)
    out.append(("after a re-supply (no batch on the spine) only Marg's printed minus counts", not any(x["section"] == "wrong" and "W638Y1" in (x["batch"] or "")
                                                                                                    for x in ln)))
    return out


def _his_lines_false(fin):
    try:
        import expiry_watch as EW                            # noqa: PLC0415
    except Exception:                                        # noqa: BLE001
        return False
    if not EW.__file__.startswith(fin):
        return False
    c = sqlite3.connect(os.environ["FINANCE_DB"])
    rows = EW.amir_rows(c)
    c.close()
    return bool(rows) and all(r[3] is False for r in rows)


def _filtered_not_used(con, fin, marg, dbp, spine_db, mt, today):
    """A second, filtered Batch Stock (40 batches) newer than the walk's whole one: the nightly keeps using the whole one and says why."""
    import expiry_watch as EW                                # noqa: PLC0415
    c2 = os.path.join(os.path.dirname(dbp), "w638_filtered.db")
    copy_db(dbp, c2)
    arch = tempfile.mkdtemp(prefix="w638a_")
    src = glob.glob(os.path.join(marg, "archive", "BATCH_STOCK", "*", "*"))
    for p in src:
        d = os.path.join(arch, "BATCH_STOCK", os.path.basename(os.path.dirname(p)))
        os.makedirs(d, exist_ok=True)
        shutil.copy2(p, d)
    newest = sorted(src, key=lambda p: os.path.basename(p).split("__")[2])[-1]
    R = EW.read_batch_stock(newest)
    rows = [b for b in R["batches"]][:40]
    lines = ["", "TEST MEDICOS", "", "WHOLE STORES CLOSING STOCK AS ON %s" % dt.date.fromisoformat(R["as_on"]).strftime("%d-%m-%Y"), "-" * 80,
             _t((0, "S.No. Description"), (44, "Batch"), (57, "Expiry"), (70, "Stock Unit")), "-" * 80]
    tot = 0
    for i, b in enumerate(rows, 1):
        tot += b["units"]
        e = "%d/%s" % (int(b["expiry"][5:7]), b["expiry"][:4]) if b["expiry"] else ""
        lines.append(_t((-4, str(i)), (6, b["item"]), (37, b["packing"]), (44, b["batch"] or ""), (-62, e), (-75, b["stock"]), (77, b["unit"] or "")))
    lines += ["-" * 80, _t((0, "TOTAL"), (-75, str(tot))), "-" * 80, "*** End of Report ***"]
    x, _i = mt.convert(("\r\n".join(lines) + "\r\n").encode("latin-1"))
    d = os.path.join(arch, "BATCH_STOCK", "2099-12")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "BATCH_STOCK_BATCHWISE__2099-12-31__20991231-235959__w638f.xls"), "wb").write(x)
    c = sqlite3.connect(c2)
    sp, alias = EW._spine(spine_db)
    run, _lines = EW.compute(c, sp, alias, arch, today)
    c.close()
    sp.close()
    shutil.rmtree(arch, ignore_errors=True)
    os.remove(c2)
    return run.get("export_name") == os.path.basename(newest) and "filtered batch list" in (run.get("note") or "")


def _late_order(con):
    """A walk order (W638) six days old, two medicines, nothing come: late on reception's page."""
    when = (dt.datetime.now() - dt.timedelta(days=6)).replace(microsecond=0).isoformat()
    cols = {r[1] for r in con.execute("PRAGMA table_info(purchase_order)")}
    row = dict(created_at=when, created_by="w638", vendor="W638 TEST AGENCY", status="sent", supplier_norm="W638 TEST AGENCY",
               sent_by="w638", section="medicine", order_src="system")
    row = {k: v for k, v in row.items() if k in cols}
    cur = con.execute("INSERT INTO purchase_order (%s) VALUES (%s)" % (", ".join(row), ", ".join("?" * len(row))), list(row.values()))
    oid = cur.lastrowid
    for item, packs in (("W638 MED ONE", 3), ("W638 MED TWO", 5)):
        con.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units) VALUES (?,?,?,?,?)", (oid, item, packs, 10, packs * 10))
    con.commit()
    return oid


def _sms_event(con):
    """A walk SMS NEFT event, unconfirmed, for the newest finalised month with a NEFT portion -- the live event of that month in the copy."""
    try:
        import supplier_msg as SM                            # noqa: PLC0415
    except Exception:                                        # noqa: BLE001
        return None, None
    for m in sorted({r[0] for r in con.execute("SELECT DISTINCT month FROM purchase_neft_event")} | {"2026-09", "2026-08"}, reverse=True):
        try:
            neft_p, groups, final = SM.sheet(con, m)
        except Exception:                                    # noqa: BLE001
            continue
        if final and neft_p > 0:
            cur = con.execute("INSERT INTO purchase_neft_event (month, kind, source, amount_p, sms_date, created_at, note) VALUES (?,?,?,?,?,?,?)",
                              (m, "provisional", "sms", neft_p, dt.date.today().isoformat(), dt.datetime.now().replace(microsecond=0).isoformat(), "W638 walk"))
            con.commit()
            return cur.lastrowid, m
    return None, None


if __name__ == "__main__":
    sys.exit(main())
