#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""claude_vs_sarvam_s565.py -- kit S565_DARPAN_SMS_AND_CLAUDE_BILLS, part B (15-Oct-2026).  READ ONLY: run once on the box, nothing
installed, scheduled or left running.  Every read and write is on sqlite-backup copies under --work (default /tmp/s565b), which is
removed at the end.  No screen, no Marg, no stored bill changes; the live databases are opened read-only and only to copy them.
    python3 -B claude_vs_sarvam_s565.py --csv <path for the per-bill CSV> [--fresh 5] [--cap-usd 12]

What it does (the brief's section 2.3):
  a  copies finance.db and assets.db (the backup API) into --work;
  b  the sample = every purchase_scan_link row whose asset bill has its scan file on disk (bills.source_stored under
     purchase_app._s446_uploads()); sorts each bill: Claude-at-capture (a claude_reading ok=1 row taken at the bill's capture, so the
     stored reading may be Claude's) or a stored reading that is Sarvam's / a person's (the bill captured before S550, or the reading
     kept aside -- S550 never writes on a pharmacy paper); the gate before any call (the reader 'on' on the copy; the daily cap minus
     today's calls not under 94);
  c  Claude's reading: an existing claude_reading ok=1 row as it is (no call); else claude_reader.read(<scan>, bid, db_path=<copy>).
     --fresh N bills (lowest ids) are also read fresh, on their own copy, only to measure the cost per bill and whether today's reading
     agrees with the stored one.  claude_reader._post is wrapped to record each answer's usage; spend capped at --cap-usd;
  d  scoring by purchase_app._s446_compare_one, called as it is (no monkeypatch), on two (three) sets of copies: Sarvam (the assets copy
     as stored) and Claude (an assets copy whose four header fields and items are Claude's, via claude_reader.to_bill);
  e  prints the aggregates (the report's table) and writes the per-bill CSV: no vendor_phone / vendor_email column, any run of 10 digits
     masked to its last 4.
Prints 'PART B OK S565 ...' at the end, or 'PART B STOPPED: <why>' (exit 2)."""
import argparse
import collections
import csv
import datetime as dt
import inspect
import json
import os
import re
import shutil
import sqlite3
import sys
import threading

sys.dont_write_bytecode = True
PRICES = {"claude-sonnet-5-5": (2.00, 10.00), "claude-haiku-5-5": (0.10, 0.50)}     # USD per MTok, the brief / the published table
HAIKU_LONG = (0.50, 2.50)                                                          # haiku-5-5 prompts over 100k tokens
S550_FROM = "2026-10-14 00:00:00"                                                  # S550 installed 14-Oct-2026 (before it, no reading at capture)
FIELDS = ("supplier_ok", "billno_ok", "date_ok", "total_ok", "all_ok")
FAULTS = ("name", "qty", "rate", "batch", "expiry")
OUT = []


def say(s=""):
    s = re.sub(r"\d{10,}", lambda m: "#" * (len(m.group(0)) - 4) + m.group(0)[-4:], str(s))
    OUT.append(s)
    print(s, flush=True)


def mask(v):
    return re.sub(r"\d{10,}", lambda m: "#" * (len(m.group(0)) - 4) + m.group(0)[-4:], "" if v is None else str(v))


def stop(why):
    say("PART B STOPPED: %s" % why)
    sys.exit(2)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst, timeout=60)
    s.backup(d)
    d.close()
    s.close()


def conn(p):
    c = sqlite3.connect(p, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def price(model, tin, tout):
    if model == "claude-haiku-5-5" and tin > 100000:
        pi, po = HAIKU_LONG
    else:
        pi, po = PRICES.get(model, max(PRICES.values()))
    return tin / 1e6 * pi + tout / 1e6 * po


class Meter:
    """Wraps claude_reader._post: records usage per call and refuses a call that could pass the cap (the reader catches the refusal
    as an error and records a failed reading on the copy; the run then stops calling)."""

    def __init__(self, CR, cap):
        self.CR, self.cap, self.orig = CR, cap, CR._post
        self.calls, self.tin, self.tout, self.spent, self.max_call, self.refused = 0, 0, 0, 0.0, 0.0, 0
        self.lock = threading.Lock()
        self.models = collections.Counter()
        self.codes = collections.Counter()

    def est(self, model):
        floor = price(model, 100000, 8000)            # a prompt of 100k tokens and the reader's max_tokens 8000
        return max(floor, 1.5 * self.max_call)

    def __call__(self, body, key):
        model = body.get("model")
        with self.lock:
            e = self.est(model)
            if self.spent + e > self.cap:
                self.refused += 1
                raise RuntimeError("S565 spend cap")
        code, js, text = self.orig(body, key)
        u = (js or {}).get("usage") if isinstance(js, dict) else None
        tin = int((u or {}).get("input_tokens") or 0) + int((u or {}).get("cache_creation_input_tokens") or 0) + int((u or {}).get("cache_read_input_tokens") or 0)
        tout = int((u or {}).get("output_tokens") or 0)
        c = price(model, tin, tout)
        with self.lock:
            self.calls += 1
            self.tin += tin
            self.tout += tout
            self.spent += c
            self.max_call = max(self.max_call, c)
            self.models[model] += 1
            self.codes[code] += 1
        return code, js, text

    def install(self):
        self.CR._post = self

    def remove(self):
        self.CR._post = self.orig


def agg(rows):
    """rows: purchase_sarvam_check-shaped dicts -> the table's figures."""
    out = dict(n=len(rows), items_read=0, items_wrong=0, faults=collections.Counter())
    for f in FIELDS:
        out[f] = sum(int(r[f] or 0) for r in rows)
    for r in rows:
        out["items_read"] += int(r["items_read"] or 0)
        out["items_wrong"] += int(r["items_wrong"] or 0)
        for it in (json.loads(r["detail"] or "{}").get("items") or []):
            for b in it.get("bad") or []:
                out["faults"][b] += 1
    return out


def checks(dbp):
    c = conn(dbp)
    try:
        return {int(r["asset_bill_id"]): dict(r) for r in c.execute("SELECT * FROM purchase_sarvam_check")}
    finally:
        c.close()


def score(PA, fdb, adb, links):
    """purchase_app._s446_compare_one as it is, on a finance copy whose purchase_sarvam_check is emptied first."""
    con, acon = conn(fdb), conn(adb)
    try:
        con.execute(PA.S446_SARVAM_DDL)
        con.execute("DELETE FROM purchase_sarvam_check")       # a scratch copy only
        con.commit()
        none = 0
        for lk in links:
            if PA._s446_compare_one(con, acon, dict(bill_id=lk["bill_id"], asset_bill_id=lk["asset_bill_id"])) is None:
                none += 1
        con.commit()
    finally:
        con.close()
        acon.close()
    return none


def put_claude(CR, adb, readings):
    """The assets copy takes Claude's reading: the four header fields updated, the items replaced (to_bill's mapping)."""
    c = conn(adb)
    try:
        for bid, data in readings.items():
            hdr, items = CR.to_bill(data)
            c.execute("UPDATE bills SET vendor=?, bill_no=?, bill_date=?, total_amount=? WHERE id=?",
                      (hdr.get("vendor"), hdr.get("bill_no"), hdr.get("bill_date"), hdr.get("total_amount"), bid))
            c.execute("DELETE FROM bill_items WHERE bill_id=?", (bid,))      # a scratch copy only
            for it in items:
                c.execute("INSERT INTO bill_items (bill_id, item_name, quantity, rate, batch, expiry) VALUES (?,?,?,?,?,?)",
                          (bid, it.get("name") or "", it.get("qty"), it.get("rate"), it.get("batch"), it.get("expiry")))
        c.commit()
    finally:
        c.close()


def same_hdr(CR, stored, data):
    """Does the stored bill's header equal Claude's reading (the four fields, loosely)?"""
    hdr, _ = CR.to_bill(data)
    d = lambda s: re.sub(r"\D", "", str(s or "")).lstrip("0")
    n = lambda s: re.sub(r"[^A-Z0-9]", "", str(s or "").upper())
    try:
        t = stored["total_amount"] not in (None, "") and hdr.get("total_amount") is not None and abs(float(stored["total_amount"]) - float(hdr["total_amount"])) < 1
    except (TypeError, ValueError):
        t = False
    return (n(stored["vendor"]) == n(hdr.get("vendor")) and n(stored["vendor"]) != "", d(stored["bill_no"]) == d(hdr.get("bill_no")) and d(stored["bill_no"]) != "", t)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]      # never import from the kit folder
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", default="/root/finance")
    ap.add_argument("--fdb", default="/root/finance/finance.db")
    ap.add_argument("--adb", default="/root/assetapp/assets.db")
    ap.add_argument("--reader", default="/root/assetapp/claude_reader.py")
    ap.add_argument("--work", default="/tmp/s565b")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--fresh", type=int, default=5)
    ap.add_argument("--cap-usd", type=float, default=12.0)
    ap.add_argument("--min-left", type=int, default=94)
    a = ap.parse_args()
    if os.environ.get("ASSETS_DB") or os.environ.get("ASSETS_UPLOADS"):
        stop("ASSETS_DB / ASSETS_UPLOADS set in the environment -- the scan folder would not be the live one")
    t0 = dt.datetime.now().replace(microsecond=0)
    say("-- S565 part B: Claude vs Sarvam on the Sanjeevni medicine bills -- read only, copies under %s (%s IST)" % (a.work, t0))

    # a -- copies
    if os.path.exists(a.work):
        stop("%s exists already -- a previous run's copies; nothing done" % a.work)
    os.makedirs(a.work)
    os.chmod(a.work, 0o700)
    P = {k: os.path.join(a.work, k + ".db") for k in ("f_sarvam", "f_claude", "f_fresh", "a_stored", "a_claude", "a_fresh", "a_freshsc")}
    copydb(a.fdb, P["f_sarvam"])
    copydb(a.adb, P["a_stored"])
    for k in ("f_claude", "f_fresh"):
        copydb(P["f_sarvam"], P[k])
    for k in ("a_claude", "a_fresh", "a_freshsc"):
        copydb(P["a_stored"], P[k])
    say("   copies made by the sqlite backup API: finance.db x3, assets.db x4")

    # the code, as it is
    sys.path.insert(0, os.path.abspath(a.fin))
    import purchase_app as PA                                   # noqa: E402
    if not os.path.abspath(PA.__file__).startswith(os.path.abspath(a.fin)):
        stop("purchase_app came from %s" % PA.__file__)
    try:
        import item_check                                       # noqa: E402
        ok_ic = callable(getattr(item_check, "learnt_line", None)) and PA._s454_ic() is item_check
    except Exception as e:                                      # noqa: BLE001
        ok_ic, item_check = False, e
    if not ok_ic:
        stop("the learnt-name helper (item_check.learnt_line) does not import -- the compare would fall back to the older matching")
    say("   purchase_app %s and item_check %s import from %s; _s446_compare_one called as it is"
        % (md5f(PA.__file__)[:8], md5f(item_check.__file__)[:8], a.fin))
    sys.path.insert(0, os.path.dirname(os.path.abspath(a.reader)))
    import claude_reader as CR                                  # noqa: E402
    sig_r = str(inspect.signature(CR.read))
    sig_t = str(inspect.signature(CR.to_bill))
    if sig_r != "(path, bid=None, db_path=None)" or sig_t != "(data)":
        stop("claude_reader's shapes moved: read%s to_bill%s" % (sig_r, sig_t))
    say("   claude_reader %s (version %s): read%s, to_bill%s" % (md5f(CR.__file__)[:8], getattr(CR, "VERSION", "?"), sig_r, sig_t))

    # b -- the sample
    uploads = os.path.realpath(PA._s446_uploads())
    fc, ac = conn(P["f_sarvam"]), conn(P["a_stored"])
    links = [dict(r) for r in fc.execute("SELECT bill_id, asset_bill_id FROM purchase_scan_link ORDER BY asset_bill_id")]
    stored_chk = {int(r["asset_bill_id"]): dict(r) for r in fc.execute("SELECT * FROM purchase_sarvam_check")}
    pbill = {int(r["id"]): dict(r) for r in fc.execute("SELECT id, supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE id IN (%s)"
                                                       % ",".join(str(int(x["bill_id"])) for x in links))} if links else {}
    sample, missing, badext = [], [], []
    for lk in links:
        b = ac.execute("SELECT * FROM bills WHERE id=?", (lk["asset_bill_id"],)).fetchone()
        if b is None or not b["source_stored"]:
            missing.append(lk["asset_bill_id"])
            continue
        p = os.path.realpath(os.path.join(uploads, os.path.basename(str(b["source_stored"]))))
        if not p.startswith(uploads + os.sep) or not os.path.isfile(p):
            missing.append(lk["asset_bill_id"])
            continue
        ext = p.rsplit(".", 1)[-1].lower() if "." in p else ""
        lk.update(path=p, ext=ext, created_at=b["created_at"], status=b["status"], stored=dict(b))
        if ext not in ("pdf", "jpg", "jpeg", "png", "webp"):
            badext.append(lk["asset_bill_id"])
        sample.append(lk)
    say("   sample: %d purchase_scan_link rows; %d with the scan on disk (%s); missing: %s; not PDF/photo (a failure, counted): %d"
        % (len(links), len(sample), dict(collections.Counter(x["ext"] for x in sample)), missing or "none", len(badext)))
    say("   statuses: %s; captured %s .. %s" % (dict(collections.Counter(x["status"] for x in sample)),
                                                 min((x["created_at"] for x in sample), default="-"), max((x["created_at"] for x in sample), default="-")))
    cr = {int(r["bill_id"]): dict(r) for r in ac.execute("SELECT * FROM claude_reading")}
    at_capture, kept_aside = [], []
    for lk in sample:
        r = cr.get(lk["asset_bill_id"])
        lk["cr"] = r if (r and int(r["ok"] or 0) == 1) else None
        cap_moment = str(lk["created_at"] or "") >= S550_FROM
        near = False
        if lk["cr"] and cap_moment:
            try:
                near = abs((dt.datetime.fromisoformat(str(lk["cr"]["at"])[:19]) - dt.datetime.fromisoformat(str(lk["created_at"])[:19])).total_seconds()) <= 6 * 3600
            except ValueError:
                near = True
        (at_capture if (lk["cr"] and near) else kept_aside).append(lk)
    with_cr = [x for x in sample if x["cr"]]
    say("   sorted: %d with a Claude reading (ok=1) already; of them read AT CAPTURE (captured on/after S550, read within 6 h): %d; "
        "kept aside (captured before S550 -- the stored reading is Sarvam's or a person's): %d" % (len(with_cr), len(at_capture), len([x for x in kept_aside if x["cr"]])))
    # the data check of the sort: does the stored header equal Claude's reading?
    eq = collections.Counter()
    for lk in with_cr:
        v, b, t = same_hdr(CR, lk["stored"], json.loads(lk["cr"]["data"] or "{}"))
        eq["vendor"] += v
        eq["bill_no"] += b
        eq["total"] += t
        eq["all3"] += v and b and t
    say("   stored header = Claude's reading (exactly, after spacing/case): vendor %d, bill no %d, total %d, all three %d of %d"
        % (eq["vendor"], eq["bill_no"], eq["total"], eq["all3"], len(with_cr)))
    ids = [x["asset_bill_id"] for x in sample]
    acts = collections.Counter()
    edited = set()
    if ids:
        for r in ac.execute("SELECT bill_id, who, action FROM bill_audit WHERE bill_id IN (%s)" % ",".join(str(i) for i in ids)):
            acts[str(r["action"])] += 1
            if re.search(r"edit|correct|fix|chang|updat|save|set_", str(r["action"]), re.I) and str(r["who"] or "") not in ("", "system", "ocr", "sarvam", "claude"):
                edited.add(int(r["bill_id"]))
    say("   bill_audit on the sample (actions, counts): %s" % (dict(acts) or "none"))
    say("   bills with a person's edit-type action in bill_audit (a hand correction the data shows): %d" % len(edited))
    fc.close()
    ac.close()

    # the gate before any call
    gc = conn(P["a_fresh"])
    try:
        st, capn, today = CR.state(gc), CR.cap(gc), CR.calls_today(gc)
        model = CR.setting(gc, "read.claude_model") or CR.MODELS[0]
    finally:
        gc.close()
    say("   gate: reader state on the copy '%s'; daily cap %d, calls today %d (left %d); model %s"
        % (st if not st.startswith("stopped") else "stopped", capn, today, capn - today, model))
    if st != "on" or capn - today < a.min_left:
        stop("the reader is '%s' on the copy, or the day's cap minus today's calls (%d) is under %d -- not switched on, no call made"
             % (st, capn - today, a.min_left))

    # c -- Claude's readings: the existing rows as they are; fresh reads for the bills without one, and the --fresh cost sample
    readings = {x["asset_bill_id"]: json.loads(x["cr"]["data"] or "{}") for x in sample if x["cr"]}
    need = [x for x in sample if not x["cr"]]
    costs = sorted(sample, key=lambda x: x["asset_bill_id"])[:max(0, a.fresh)]
    meter = Meter(CR, a.cap_usd)
    meter.install()
    fresh_fail, fresh = [], {}
    try:
        for lk in need:
            d = CR.read(lk["path"], bid=lk["asset_bill_id"], db_path=P["a_claude"])
            if d:
                readings[lk["asset_bill_id"]] = d
            else:
                fresh_fail.append(lk["asset_bill_id"])
            if meter.refused:
                break
        for lk in costs:
            if meter.refused:
                break
            c0 = meter.calls
            d = CR.read(lk["path"], bid=lk["asset_bill_id"], db_path=P["a_fresh"])
            lk["fresh_calls"] = meter.calls - c0
            if d:
                fresh[lk["asset_bill_id"]] = d
            else:
                fresh_fail.append(lk["asset_bill_id"])
    finally:
        meter.remove()
    nbill = len([x for x in need if x["asset_bill_id"] in readings]) + len(fresh)
    say("   Claude's readings: %d from existing rows (no call); %d bills without one read fresh; %d read fresh again only for the cost"
        % (len(sample) - len(need), len([x for x in need if x["asset_bill_id"] in readings]), len(fresh)))
    say("   calls %d (%s; HTTP %s); tokens in %d, out %d; spend USD %.4f (cap %.2f; refused by the cap: %d); failed readings: %d"
        % (meter.calls, dict(meter.models), dict(meter.codes), meter.tin, meter.tout, meter.spent, a.cap_usd, meter.refused, len(fresh_fail)))
    if nbill:
        say("   cost per bill read fresh: USD %.4f (%.1f calls, %d tokens in, %d out per bill)"
            % (meter.spent / nbill, meter.calls / float(nbill), meter.tin // nbill, meter.tout // nbill))

    # d -- scoring, the same function on both sides
    side = [x for x in sample if x not in at_capture]
    put_claude(CR, P["a_claude"], {k: v for k, v in readings.items()})
    n1 = score(PA, P["f_sarvam"], P["a_stored"], side)
    n2 = score(PA, P["f_claude"], P["a_claude"], sample)
    cc = conn(P["f_claude"])
    cc.execute("DROP TABLE IF EXISTS claude_check_s565")
    cc.execute("CREATE TABLE claude_check_s565 AS SELECT * FROM purchase_sarvam_check")
    cc.commit()
    cc.close()
    S, C = checks(P["f_sarvam"]), checks(P["f_claude"])
    F = {}
    if fresh:
        put_claude(CR, P["a_freshsc"], fresh)
        score(PA, P["f_fresh"], P["a_freshsc"], [x for x in sample if x["asset_bill_id"] in fresh])
        F = checks(P["f_fresh"])
    both = [i for i in S if i in C]
    say("   scored: Sarvam %d bills (fresh, now), Claude %d bills; the compare found no Marg bill / no scan for %d / %d"
        % (len(S), len(C), n1, n2))

    # e -- the result
    def fig(rows):
        return agg(rows)
    sa, ca = fig([S[i] for i in both]), fig([C[i] for i in both])
    st_ = fig([stored_chk[i] for i in both if i in stored_chk])
    say("")
    say("RESULT (the same %d bills, the same compare, %s IST):" % (len(both), dt.datetime.now().strftime("%d-%b %H:%M")))
    say("   %-34s %10s %10s %16s" % ("", "Sarvam", "Claude", "Sarvam (stored)"))
    for f, lab in (("supplier_ok", "supplier right"), ("billno_ok", "bill number right"), ("date_ok", "date right"), ("total_ok", "total right"),
                   ("all_ok", "fully right (all + every line)")):
        say("   %-34s %10d %10d %16d" % (lab, sa[f], ca[f], st_[f]))
    say("   %-34s %10d %10d %16d" % ("item lines read", sa["items_read"], ca["items_read"], st_["items_read"]))
    say("   %-34s %10d %10d %16d" % ("item lines with any fault", sa["items_wrong"], ca["items_wrong"], st_["items_wrong"]))
    for k in FAULTS:
        say("   %-34s %10d %10d %16d" % ("  fault: " + k, sa["faults"][k], ca["faults"][k], st_["faults"][k]))
    for f, lab in (("supplier_ok", "supplier"), ("billno_ok", "bill number"), ("date_ok", "date"), ("total_ok", "total"), ("all_ok", "fully right")):
        only_s = sum(1 for i in both if S[i][f] and not C[i][f])
        only_c = sum(1 for i in both if C[i][f] and not S[i][f])
        say("   only one right -- %-14s Sarvam only %3d   Claude only %3d" % (lab, only_s, only_c))
    lines_ok_s = sum(1 for i in both if int(S[i]["items_read"] or 0) and not int(S[i]["items_wrong"] or 0))
    lines_ok_c = sum(1 for i in both if int(C[i]["items_read"] or 0) and not int(C[i]["items_wrong"] or 0))
    say("   bills whose every item line is right: Sarvam %d, Claude %d; bills with no item line read: Sarvam %d, Claude %d"
        % (lines_ok_s, lines_ok_c, sum(1 for i in both if not int(S[i]["items_read"] or 0)), sum(1 for i in both if not int(C[i]["items_read"] or 0))))
    if at_capture:
        xa = fig([C[i["asset_bill_id"]] for i in at_capture if i["asset_bill_id"] in C])
        say("   Claude-at-capture bills (kept out of the side-by-side; Claude's column only): %d -- supplier %d, bill no %d, date %d, total %d, fully %d"
            % (xa["n"], xa["supplier_ok"], xa["billno_ok"], xa["date_ok"], xa["total_ok"], xa["all_ok"]))
    if F:
        fa = fig(list(F.values()))
        ea = fig([C[i] for i in F])
        say("   the %d fresh cost-sample readings, scored: supplier %d, bill no %d, date %d, total %d, fully %d, lines %d / faulty %d  "
            "(the stored Claude readings of the same bills: %d, %d, %d, %d, %d, %d / %d)"
            % (fa["n"], fa["supplier_ok"], fa["billno_ok"], fa["date_ok"], fa["total_ok"], fa["all_ok"], fa["items_read"], fa["items_wrong"],
               ea["supplier_ok"], ea["billno_ok"], ea["date_ok"], ea["total_ok"], ea["all_ok"], ea["items_read"], ea["items_wrong"]))
    # the fairness notes: how the sample came to be, and what the compare learnt from Sarvam's own spellings
    fc, ac = conn(P["f_sarvam"]), conn(P["a_stored"])
    mo = collections.Counter()
    for r in fc.execute("SELECT matched_on FROM purchase_scan_link"):
        t = str(r[0] or "").lower()
        mo["bill number"] += ("bill" in t or "number" in t)
        mo["supplier"] += ("vendor" in t or "supplier" in t)
        mo["amount"] += ("amount" in t or "total" in t)
        mo["reception / auto"] += ("reception" in t or "auto_link" in t)
    try:
        n_alias = fc.execute("SELECT COUNT(*) FROM purchase_scan_alias").fetchone()[0]
    except sqlite3.Error:
        n_alias = 0
    try:
        n_learnt = fc.execute("SELECT COUNT(*) FROM s454_item_name").fetchone()[0]
    except sqlite3.Error:
        n_learnt = 0
    via_alias = 0
    for i in both:
        if not S[i]["supplier_ok"]:
            continue
        lk = next(x for x in sample if x["asset_bill_id"] == i)
        bill = fc.execute("SELECT * FROM purchase_bill WHERE id=?", (lk["bill_id"],)).fetchone()
        v = ac.execute("SELECT vendor FROM bills WHERE id=?", (i,)).fetchone()[0]
        via_alias += bool(v) and not PA._vendor_match(v, bill["supplier"])
    bn = collections.Counter()
    for i in both:
        if C[i]["billno_ok"]:
            continue
        dd = json.loads(C[i]["detail"] or "{}")
        cb = str((dd.get("scan") or {}).get("bill_no") or "")
        bn["wrong"] += 1
        bn["letter-prefixed"] += bool(re.match(r"^\s*[A-Za-z]", cb))
        bn["none read"] += not cb.strip()
        bn["total right"] += int(C[i]["total_ok"] or 0)
    fc.close()
    ac.close()
    say("   fairness: the %d links were made from the stored (Sarvam) readings -- on the bill number %d, the supplier %d, the amount %d, by reception / auto %d"
        % (len(links), mo["bill number"], mo["supplier"], mo["amount"], mo["reception / auto"]))
    say("   fairness: the supplier check knows %d spellings learnt from Sarvam's readings (purchase_scan_alias); %d of Sarvam's supplier passes need one "
        "or the chosen supplier; the item check knows %d learnt printed names (s454_item_name)" % (n_alias, via_alias, n_learnt))
    say("   Claude's bill number not Marg's: %d bills -- %d letter-prefixed numbers, %d with nothing read; on %d of them Claude's total is right"
        % (bn["wrong"], bn["letter-prefixed"], bn["none read"], bn["total right"]))
    say("AGG " + json.dumps(dict(n=len(both), sarvam={k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in sa.items()},
                                 claude={k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in ca.items()},
                                 stored={k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in st_.items()},
                                 calls=meter.calls, tin=meter.tin, tout=meter.tout, usd=round(meter.spent, 4), fresh=len(fresh)), sort_keys=True))

    # the per-bill CSV -- no vendor_phone / vendor_email column; 10-digit runs masked
    os.makedirs(os.path.dirname(os.path.abspath(a.csv)), exist_ok=True)
    cols = ["asset_bill_id", "purchase_bill_id", "month", "file", "group", "marg_supplier", "marg_bill_no"]
    for p in ("sarvam", "claude"):
        cols += ["%s_%s" % (p, f) for f in FIELDS] + ["%s_items_read" % p, "%s_items_wrong" % p] + ["%s_f_%s" % (p, k) for k in FAULTS]
    cols += ["fresh_all_ok", "fresh_items_wrong", "fresh_calls"]
    with open(a.csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for lk in sample:
            i = lk["asset_bill_id"]
            pb = pbill.get(int(lk["bill_id"]), {})
            row = [i, lk["bill_id"], str(pb.get("bill_date") or "")[:7], lk["ext"], "claude_at_capture" if lk in at_capture else "side_by_side",
                   mask(pb.get("supplier")), mask(pb.get("bill_no"))]
            for src in (S, C):
                r = src.get(i)
                if r is None:
                    row += [""] * (len(FIELDS) + 2 + len(FAULTS))
                    continue
                fl = collections.Counter(b for it in (json.loads(r["detail"] or "{}").get("items") or []) for b in (it.get("bad") or []))
                row += [r[f] for f in FIELDS] + [r["items_read"], r["items_wrong"]] + [fl[k] for k in FAULTS]
            r = F.get(i)
            row += [r["all_ok"] if r else "", r["items_wrong"] if r else "", lk.get("fresh_calls", "")]
            w.writerow([mask(x) for x in row])
    say("   per-bill CSV: %s (%d rows; no phone or email column; 10-digit runs masked)" % (a.csv, len(sample)))

    shutil.rmtree(a.work, ignore_errors=True)
    say("   %s removed: %s" % (a.work, "yes" if not os.path.exists(a.work) else "NO -- left, name it in the report"))
    leak = re.search(r"\d{10}", "\n".join(OUT))
    say("PART B OK S565: %d bills side by side; calls %d, USD %.4f; output 10-digit-free: %s" % (len(both), meter.calls, meter.spent, "yes" if not leak else "NO"))
    return 0


def md5f(p):
    import hashlib                                              # noqa: PLC0415
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


if __name__ == "__main__":
    sys.exit(main())
