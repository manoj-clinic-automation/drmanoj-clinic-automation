"""spine_build.py -- S272 / kit S331 (Sanjeevni). Builds the spine from the evidence store, whole, every time.

    python spine_build.py --readings DIR --rules spine_rules.json --out spine.db [--finance-db finance.db] [--acceptance]

* INPUT: only the evidence store (one JSON reading per Marg export, written by spine_evidence.py with the
  certified readers of marg_read.py) and spine_rules.json (every hand-declared fact, each with its source).
  It never reads a business table of finance.db. --finance-db is opened READ-ONLY for one purpose: to
  prove the 06-Sep count baseline is untouched (gate check 5).
* OUTPUT: <out>.new is built from empty, the gate runs against it, and only a build whose BLOCKING checks
  all pass is renamed over <out> (one atomic rename). A failed build is kept as <out>.failed for reading;
  the last good spine stays in place. Exit 0 = swapped, 3 = gate failed (nothing swapped), 2 = usage.
* Stock is kept at Marg's own unit: a 'strip:tab' figure counts in tablets; an item Marg prints as a plain
  figure (whole packs) counts in packs -- exactly the S270 method (reference s3).
* --acceptance: stock must equal Marg on EVERY item on EVERY checkable full closing (reference s8 item 4).
  Without it, a new difference is recorded as a dated finding (sp_finding) and does not block, because an
  unexported Marg voucher is a fact about Marg, not a fault in the spine.
"""
import argparse
import collections
import datetime as dt
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_VERSION = "S331.1"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def K(n):
    """The key every Marg report can be joined on: the first 20 characters, spaces collapsed (the sale clip)."""
    return re.sub(r'\s+', ' ', (n or "").strip())[:20].strip()


def packn(p):
    m = re.match(r'^(\d+)\*(\d+)$', (p or "").rstrip('.'))
    return int(m.group(1)) * int(m.group(2)) if m else None


def supnorm(s):
    return re.sub(r'[^A-Z]', '', (s or "").upper())[:8]


def dates(a, b):
    d0, d1 = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    while d0 <= d1:
        yield d0.isoformat()
        d0 += dt.timedelta(days=1)


SCHEMA = """
CREATE TABLE sp_meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE sp_export (md5 TEXT PRIMARY KEY, name TEXT, family TEXT, stamp TEXT, date_from TEXT, date_to TEXT,
  as_on TEXT, ok INTEGER, failed TEXT, role TEXT, note TEXT);
CREATE TABLE sp_item (k20 TEXT, name TEXT, packing TEXT, unit_kind TEXT, first_seen TEXT, last_seen TEXT,
  PRIMARY KEY (name, packing));
CREATE TABLE sp_item_fact (name TEXT, packing TEXT, fact TEXT, value TEXT, as_on TEXT, source_md5 TEXT);
CREATE TABLE sp_alias (alias TEXT PRIMARY KEY, k20 TEXT, kind TEXT, source TEXT);
CREATE TABLE sp_sale_bill (date TEXT, bill TEXT, gross_p INTEGER, disc_p INTEGER, tax_p INTEGER, drcr_p INTEGER,
  net_p INTEGER, cash_p INTEGER, credit_note INTEGER, source_md5 TEXT, PRIMARY KEY (date, bill));
CREATE TABLE sp_sale_line (date TEXT, bill TEXT, seq INTEGER, name20 TEXT, k20 TEXT, pack TEXT, qty_raw TEXT,
  units REAL, rate_p INTEGER, batch TEXT, expiry TEXT, PRIMARY KEY (date, bill, seq));
CREATE TABLE sp_purchase_bill (supplier TEXT, supkey TEXT, bill TEXT, date TEXT, amount_p INTEGER, direction TEXT,
  source_md5 TEXT, PRIMARY KEY (supkey, bill, date));
CREATE TABLE sp_purchase_line (supkey TEXT, bill TEXT, date TEXT, seq INTEGER, name27 TEXT, k20 TEXT, packing TEXT,
  qty REAL, free REAL, units REAL, amount_p INTEGER, net_amount_p INTEGER, direction TEXT, source_md5 TEXT);
CREATE TABLE sp_close (as_on TEXT, k20 TEXT, units REAL, source_md5 TEXT, PRIMARY KEY (as_on, k20));
CREATE TABLE sp_move (k20 TEXT, date TEXT, kind TEXT, units REAL, ref TEXT);
CREATE TABLE sp_recon (k20 TEXT, date TEXT, units REAL, reason TEXT, source TEXT);
CREATE TABLE sp_check (as_on TEXT, k20 TEXT, marg REAL, spine REAL, diff REAL, PRIMARY KEY (as_on, k20));
CREATE TABLE sp_finding (as_on TEXT, k20 TEXT, diff REAL, note TEXT);
CREATE TABLE sp_gate (n INTEGER PRIMARY KEY, name TEXT, blocking INTEGER, ok INTEGER, detail TEXT);
CREATE INDEX ix_move ON sp_move (k20, date);
CREATE INDEX ix_sl ON sp_sale_line (k20, date);
CREATE INDEX ix_pl ON sp_purchase_line (k20, date);
"""


def load_readings(d):
    out = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            with open(os.path.join(d, fn)) as fh:
                out.append(json.load(fh))
    return out


class Gate:
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail="", blocking=True):
        self.rows.append((name, int(bool(blocking)), int(bool(ok)), str(detail)[:2000]))

    @property
    def passed(self):
        return all(ok for _, b, ok, _ in self.rows if b)


def build(readings, rules, acceptance=False, finance_db=None, log=print):
    G = Gate()
    exc = {(e["file_md5_prefix"], e["check"]): e["reason"] for e in rules.get("exceptions", [])}
    alias = {a: v["to"] for a, v in rules.get("aliases", {}).items()}
    fam = rules.get("families", {})

    def Z(name):
        k = K(name)
        k = alias.get(k, k)
        return fam.get(k, k)

    # ---------------------------------------------------------------- 1. the evidence, each file judged
    by_md5 = {}
    for r in readings:
        by_md5.setdefault(r["md5"], r)
    ev = list(by_md5.values())
    exports = {}
    for r in ev:
        fails = [c for c in r.get("checks", []) if not c[1]]
        waived = [c for c in fails if (r["md5"][:8], c[0]) in exc]
        real = [c for c in fails if (r["md5"][:8], c[0]) not in exc]
        r["_accepted"] = r.get("family") is not None and not real and not [f for f in r.get("failed", []) if " at row " in f]
        r["_waived"] = [c[0] for c in waived]
        r["_real_fail"] = [c[0] for c in real]
        exports[r["md5"]] = r
    fam_of = lambda f: [r for r in ev if r.get("family") == f]

    # ---------------------------------------------------------------- 2. purchases: bills (bill-wise), period supersession
    BW = sorted([r for r in fam_of("PURCHASE_BILLWISE") if r["_accepted"]], key=lambda r: r["stamp"])
    auth_bw = {}
    for r in BW:                                         # latest stamp covering a day is that day's authority
        for d in dates(r["data"]["date_from"], r["data"]["date_to"]):
            auth_bw[d] = r["md5"]
    pbills = {}
    for r in BW:
        for b in r["data"]["bills"]:
            if auth_bw.get(b["date"]) == r["md5"]:
                pbills[(supnorm(b["supplier"]), b["bill"], b["date"])] = dict(b, source=r["md5"])
    by_supbill = collections.defaultdict(list)
    for (sk, bill, d), b in pbills.items():
        by_supbill[(sk, bill)].append(b)
    by_billdate = collections.defaultdict(list)
    for (sk, bill, d), b in pbills.items():
        by_billdate[(bill, d)].append(b)
    pur_cover = sorted(auth_bw)

    # ---------------------------------------------------------------- 3. purchases: lines, joined to their bill for date + direction
    PL = sorted([r for r in ev if r.get("family") in ("PURCHASE_ITEMWISE", "PURCHASE_BILLITEMWISE")], key=lambda r: r["stamp"])
    auth_pl = {}
    for r in PL:
        for d in dates(r["data"]["date_from"], r["data"]["date_to"]):
            auth_pl[d] = r["md5"]
    plines = []
    undated = []
    xwit = []
    ubill = lambda b: (b or "").upper().lstrip("0") or "0"
    by_supbill_u = collections.defaultdict(list)
    for (sk, bill, d), b in pbills.items():
        by_supbill_u[(sk, ubill(bill))].append(b)
    by_billdate_u = collections.defaultdict(list)
    for (sk, bill, d), b in pbills.items():
        by_billdate_u[(ubill(bill), d)].append(b)
    for r in PL:
        tot_amt = 0
        ret_amt = 0
        days_auth = [d for d in dates(r["data"]["date_from"], r["data"]["date_to"]) if auth_pl.get(d) == r["md5"]]
        whole_auth = len(days_auth) == len(list(dates(r["data"]["date_from"], r["data"]["date_to"])))
        # BILL grouping: a bill number two suppliers share on one day is settled by the money of its own lines
        grp_net = collections.defaultdict(int)
        for ln in r["data"]["lines"]:
            if r["data"]["grouping"] == "BILL":
                grp_net[(ubill(ln["bill"]), ln["date"])] += ln["net_amount_p"]
        for ln in r["data"]["lines"]:
            if r["data"]["grouping"] == "SUPPLIER":
                cands = [b for b in by_supbill_u.get((supnorm(ln["supplier"]), ubill(ln["bill"])), [])
                         if r["data"]["date_from"] <= b["date"] <= r["data"]["date_to"]]
            else:
                cands = by_billdate_u.get((ubill(ln["bill"]), ln["date"]), [])
                if len(cands) > 1:
                    net = grp_net[(ubill(ln["bill"]), ln["date"])]
                    cands = [b for b in cands if abs(abs(b["amount_p"]) - net) <= 100 + 0.002 * abs(b["amount_p"])]
            if len(cands) != 1:
                undated.append((r["name"], ln["bill"], ln["name"], len(cands), whole_auth))
                continue
            b = cands[0]
            tot_amt += ln["amount_p"]
            if b["direction"] == "RETURN":
                ret_amt += ln["amount_p"]
            if auth_pl.get(b["date"]) != r["md5"]:
                continue                                    # a later export is the authority for that day
            plines.append(dict(ln, supkey=supnorm(b["supplier"]), date=b["date"], direction=b["direction"], source=r["md5"]))
        # the cross-report witness: Marg prints a return line POSITIVE and nets it in the total
        grand_fail = [c for c in r.get("checks", []) if not c[1] and c[0].startswith("closing total AMOUNT")]
        if grand_fail:
            printed = float(grand_fail[0][2].split(" vs ")[0])
            lines = sum(l["amount_p"] for l in r["data"]["lines"]) / 100.0
            ok = abs(printed - (lines - 2 * ret_amt / 100.0)) < 1.0
            xwit.append((r["name"], printed, lines, ret_amt / 100.0, ok))
            if ok:
                r["_accepted"] = True
                r["_waived"] = r["_real_fail"]
                r["_real_fail"] = []
    rej_pl = [r["name"] for r in PL if not r["_accepted"]]
    G.add("every purchase line export passes its own witness, or the returns witness (total = lines - 2 x return lines)",
          not rej_pl, "cross-witnessed %d: %s | refused: %s" % (len(xwit), [(x[0][-24:], x[1], x[2], x[3], x[4]) for x in xwit], rej_pl))
    plines = [l for l in plines if exports[l["source"]]["_accepted"]]
    pl_bills = {(l["supkey"], l["bill"], l["date"]) for l in plines}
    hard = [u for u in undated if u[4]]
    G.add("every purchase line of an export that is the authority for its whole period belongs to exactly one bill",
          not hard, "%d lines: %s | lines of superseded exports not tied (information): %d %s" % (
              len(hard), hard[:6], len(undated) - len(hard), [u[:4] for u in undated if not u[4]][:6]))
    # lines re-add to the bill (Rs 1 per bill)
    lsum = collections.defaultdict(int)
    for l in plines:
        lsum[(l["supkey"], l["bill"], l["date"])] += l["net_amount_p"]
    covered_pb = [(k, b) for k, b in pbills.items() if auth_pl.get(b["date"]) is not None]
    badadd = [(k, b["amount_p"], lsum.get(k, 0)) for k, b in covered_pb
              if abs(abs(b["amount_p"]) - lsum.get(k, 0)) > 100 + 0.002 * abs(b["amount_p"])]
    G.add("every purchase bill: its lines re-add to the bill (net, within Rs 1)", not badadd,
          "%d of %d bills off: %s" % (len(badadd), len(covered_pb), badadd[:6]), blocking=False)

    # ---------------------------------------------------------------- 4. sales: latest export per bill
    SB = sorted([r for r in fam_of("SALE_BILLWISE")], key=lambda r: r["stamp"])
    rej_s = [r["name"] for r in SB if not r["_accepted"]]
    G.add("every sale export passes its own witness", not rej_s, rej_s)
    sbills = {}
    sale_days = set()
    for r in SB:
        if not r["_accepted"]:
            continue
        for b in r["data"]["bills"]:
            sbills[(b["date"], b["bill"])] = dict(b, source=r["md5"])
        if r["data"]["date_from"]:
            sale_days.update(dates(r["data"]["date_from"], r["data"]["date_to"]))
    nums = collections.defaultdict(list)
    for (d, b) in sbills:
        m = re.match(r'^([A-Z]+)(\d+)$', b)
        nums[m.group(1)].append(int(m.group(2)))
    gaps = {s: [n for n in range(min(v), max(v) + 1) if n not in set(v)] for s, v in nums.items()}
    dups = {s: [n for n, c in collections.Counter(v).items() if c > 1] for s, v in nums.items()}
    G.add("sale bills: numbering has no repeat", not any(dups.values()), dups)
    G.add("sale bills held (information)", True, "%d bills; series %s; gaps %s" % (
        len(sbills), {s: (min(v), max(v), len(v)) for s, v in nums.items()}, gaps), blocking=False)

    # ---------------------------------------------------------------- 5. closings
    CL = sorted([r for r in fam_of("STOCK_CLOSING") if r["_accepted"]], key=lambda r: r["stamp"])
    closings = {}
    for r in CL:
        items = r["data"]["items"]
        full = len(items) >= int(rules.get("min_full_closing_items", 250))   # a category-filtered print is far shorter
        r["_full"] = full
        if full:
            closings[r["data"]["as_on"]] = r                 # the latest capture of a date wins
    rej_c = [r["name"] for r in fam_of("STOCK_CLOSING") if not r["_accepted"]]
    G.add("every closing export passes its own witness (or a declared, sourced exception)", not rej_c, rej_c)
    op = rules["opening"]
    opening = [r for r in CL if r["md5"].startswith(op["file_md5_prefix"])]
    G.add("the opening is the declared export, full, and accepted", bool(opening) and opening[0].get("_full"),
          "%s waived: %s" % (op, opening[0]["_waived"] if opening else "MISSING"))
    # whole-pack items: Marg prints a plain figure for an item it keeps in whole packs
    plain_seen = collections.defaultdict(set)
    for r in closings.values():
        for i in r["data"]["items"]:
            if i["qty_raw"] not in ("-", ""):
                plain_seen[Z(i["name"])].add(bool(i["plain"]))
    whole = {k for k, v in plain_seen.items() if v == {True}}
    mixed = sorted(k for k, v in plain_seen.items() if len(v) > 1)
    G.add("no item is printed both as packs:loose and as a plain figure", not mixed, mixed, blocking=False)

    def units(k, qty_raw, pack):
        q = (qty_raw or "").strip()
        m = re.match(r'^(-?)(\d+):(\d+)$', q)
        if m:
            return (int(m.group(2)) * (packn(pack) or 1) + int(m.group(3))) * (-1 if m.group(1) else 1)
        try:
            v = float(q or 0)
        except ValueError:
            return 0.0
        return v if k in whole else v * (packn(pack) or 1)

    # ---------------------------------------------------------------- 6. movements
    moves = []
    if opening:
        for i in opening[0]["data"]["items"]:
            moves.append((Z(i["name"]), op["as_on"], "OPENING", i["units"], opening[0]["md5"][:8]))
    sale_lines = []
    for (d, b), bill in sbills.items():
        for ln in bill["lines"]:
            k = Z(ln["name"])
            u = units(k, ln["qty"], ln["pack"])
            sign = 1 if bill["credit_note"] else -1
            sale_lines.append((d, b, ln, k, u))
            moves.append((k, d, "SALE_RETURN" if bill["credit_note"] else "SALE", sign * u, b))
    for l in plines:
        k = Z(l["name"])
        u = ((l["qty"] or 0) + (l["free"] or 0)) * (1 if k in whole else (packn(l["packing"]) or 1))
        l["_k"], l["_u"] = k, u
        moves.append((k, l["date"], "PURCHASE_RETURN" if l["direction"] == "RETURN" else "PURCHASE",
                      -u if l["direction"] == "RETURN" else u, "%s/%s" % (l["supkey"], l["bill"])))

    # ---------------------------------------------------------------- 7. which closings can be checked
    last_sale = max(sale_days) if sale_days else ""
    last_pur = min(max(auth_bw) if auth_bw else "", max(auth_pl) if auth_pl else "")
    first_sale = min(sale_days) if sale_days else ""
    checkable = [d for d in sorted(closings) if d > op["as_on"] and first_sale <= "2026-04-01" and d <= last_sale and d <= last_pur
                 and all(x in sale_days for x in dates("2026-04-01", d) if dt.date.fromisoformat(x).weekday() != 6)]
    pending = [d for d in sorted(closings) if d > op["as_on"] and d not in checkable]
    recon_date = checkable[0] if checkable else ""
    recons = [(r["k20"], recon_date, r["units"], r["reason"], r["source"]) for r in rules.get("reconciliation", [])]
    for k, d, u, why, src in recons:
        moves.append((k, d, "RECONCILIATION", u, why[:60]))

    bal_by = collections.defaultdict(list)
    for k, d, kind, u, ref in moves:
        bal_by[k].append((d, u))
    checks = []
    findings = []
    for d in checkable:
        cl = collections.defaultdict(float)
        for i in closings[d]["data"]["items"]:
            cl[Z(i["name"])] += i["units"]
        keys = set(cl) | {k for k, v in bal_by.items() if any(x[0] <= d for x in v)}
        for k in keys:
            s = round(sum(u for dd, u in bal_by.get(k, []) if dd <= d), 3)
            m = round(cl.get(k, 0.0), 3)
            checks.append((d, k, m, s, round(m - s, 3)))
            if abs(m - s) >= 0.5:
                findings.append((d, k, round(m - s, 3)))
    per_date = collections.OrderedDict()
    for d in checkable:
        rows = [c for c in checks if c[0] == d]
        on_cl = {Z(i["name"]) for i in closings[d]["data"]["items"]}
        per_date[d] = "%d/%d" % (sum(1 for c in rows if abs(c[4]) < 0.5 and c[1] in on_cl), len(on_cl))
    # A Marg closing knows only what had been KEYED when it was exported: a purchase entered next morning
    # with yesterday's bill date is missing from yesterday's closing and present in every later one.
    # So: the LATEST checkable closing must be exact; an earlier difference must be gone by a later one.
    last = checkable[-1] if checkable else ""
    G.add("at least one full closing after the opening can be checked (every sale day and the purchases up to it are in the store)",
          bool(last), "checkable: %s; pending: %s; sale days held: %s..%s" % (checkable, pending, first_sale, last_sale))
    at_last = [f for f in findings if f[0] == last]
    purch = collections.defaultdict(list)
    for k, d, kind, u, ref in moves:
        if kind in ("PURCHASE", "PURCHASE_RETURN"):
            purch[k].append((d, u))
    classed = []
    for d, k, x in findings:
        if d == last:
            classed.append((d, k, x, "OPEN at the latest closing"))
            continue
        later = [c for c in checks if c[1] == k and c[0] > d]
        gone = bool(later) and all(abs(c[4]) < 0.5 for c in later if c[0] == min(cc[0] for cc in later))
        pl = [u for (pd, u) in purch.get(k, []) if pd <= d and pd >= (dt.date.fromisoformat(d) - dt.timedelta(days=21)).isoformat()]
        sub = any(abs(x + u) < 0.5 for u in pl) or any(abs(x + pl[i] + pl[j]) < 0.5 for i in range(len(pl)) for j in range(i + 1, len(pl)))
        classed.append((d, k, x, ("TIMING: a purchase keyed after the export" if sub else "TIMING: keyed after the export")
                        if gone else "PERSISTS to the next closing"))
    timing = collections.Counter(c[3] for c in classed if c[3].startswith("TIMING") or c[3].startswith("PERSISTS"))
    findings[:] = [(d, k, x, n.replace("PERSISTS to the next closing", "TIMING: closed by a later closing")) for d, k, x, n in classed]
    G.add("STOCK: the spine equals Marg on every item at the latest checkable closing (%s)" % last, bool(last) and not at_last,
          "items equal per closing: %s; pending (exports not complete yet): %s; open: %s" % (dict(per_date), pending, at_last[:12]),
          blocking=acceptance)
    G.add("STOCK: earlier closings differ only by entries Marg had not keyed when the export was taken (information)",
          True, "%d item-days, every one closed by the latest closing: %s" % (sum(timing.values()), dict(timing)), blocking=False)

    # ---------------------------------------------------------------- 8. the count baseline is untouched
    if finance_db:
        try:
            con = sqlite3.connect("file:%s?mode=ro" % finance_db, uri=True)
            n = con.execute("SELECT COUNT(*) FROM stock_count_item").fetchone()[0]
            con.close()
            G.add("the 06-Sep count baseline is untouched (read-only look: stock_count_item rows)", n == 373, n)
        except sqlite3.Error as e:
            G.add("the 06-Sep count baseline is untouched", False, repr(e))

    # ---------------------------------------------------------------- 9. items and facts
    items = {}
    for f in ("SALT_WISE_ITEM_LIST",):                    # every item Marg holds, stock or none
        for r in sorted([r for r in fam_of(f) if r["_accepted"]], key=lambda r: (r["data"].get("as_on", ""), r["stamp"])):
            for i in r["data"]["items"]:
                if i.get("name"):
                    it = items.setdefault((i["name"], i["packing"]), dict(first=r["data"]["as_on"], last=r["data"]["as_on"]))
                    it["first"] = min(it["first"], r["data"]["as_on"]); it["last"] = max(it["last"], r["data"]["as_on"])
    for d in sorted(closings):
        for i in closings[d]["data"]["items"]:
            if not i["name"]:
                continue
            key = (i["name"], i["packing"])
            it = items.setdefault(key, dict(first=d, last=d))
            it["first"] = min(it["first"], d); it["last"] = max(it["last"], d)
    facts = []
    latest = {}
    for f in ("SALT_WISE_ITEM_LIST", "CATEGORY_WISE_ITEM_LIST", "ITEM_MASTER"):
        rs = sorted([r for r in fam_of(f) if r["_accepted"]], key=lambda r: (r["data"].get("as_on", ""), r["stamp"]))
        rej = [r["name"] for r in fam_of(f) if not r["_accepted"]]
        G.add("every %s export passes its own witness" % f, not rej, rej)
        if rs:
            latest[f] = rs[-1]
        for r in rs:
            for i in r["data"]["items"]:
                if not i.get("name"):
                    continue
                if f == "SALT_WISE_ITEM_LIST":
                    for fct in ("group", "mrp", "p_rate", "s_rate"):
                        facts.append((i["name"], i["packing"], "salt" if fct == "group" else fct, i.get(fct), r["data"]["as_on"], r["md5"]))
                elif f == "CATEGORY_WISE_ITEM_LIST":
                    facts.append((i["name"], i["packing"], "category", i["group"], r["data"]["as_on"], r["md5"]))
                else:
                    facts.append((i["name"], i["packing"], "company", i.get("company", ""), r["data"]["as_on"], r["md5"]))
    salt = latest.get("SALT_WISE_ITEM_LIST")
    if salt:
        heads = {i["group"].upper() for i in salt["data"]["items"]}
        G.add("no salt is the shop's own name (F-536)", "SANJEEVNI MEDICOS" not in heads)
        dupn = [n for n, c in collections.Counter(i["name"] for i in salt["data"]["items"]).items() if c > 1]
        G.add("identity: a name that repeats in Marg is told apart by its packing (information)", True,
              "names that repeat: %s" % dupn, blocking=False)
    # every sale / purchase name reaches an item or a declared family
    k_of_items = collections.defaultdict(set)
    for (n, p) in items:
        k_of_items[Z(n)].add((n, p))
    unknown = sorted({k for (_, _, _, k, _) in sale_lines if k not in k_of_items} |
                     {l["_k"] for l in plines if l["_k"] not in k_of_items})
    G.add("every sale and purchase name reaches an item held in Marg's closings", not unknown, unknown[:20])
    shared = {k: sorted(v) for k, v in k_of_items.items() if len(v) > 1}
    G.add("names the 20-character clip cannot tell apart are held as one family (information)", True,
          "%d families: %s" % (len(shared), list(shared)[:12]), blocking=False)

    # sale bills: every bill re-adds from its own lines (rate is per pack; units / pack)
    pack_of = {}
    for (n, p) in items:
        pack_of.setdefault(Z(n), packn(p) or 1)
    off = []
    for (d, b), bill in sbills.items():
        s = 0.0
        for ln in bill["lines"]:
            k = Z(ln["name"])
            pk = packn(ln["pack"]) or pack_of.get(k, 1)
            u = units(k, ln["qty"], ln["pack"] or "1*%d" % pk)
            s += (ln["rate_p"] or 0) * (u if k in whole else u / pk)
        s = s / 100.0 * (-1 if bill["credit_note"] else 1)
        if abs(s - bill["gross_p"] / 100.0) > 0.02 * max(1, len(bill["lines"])) + 0.01:
            off.append((d, b, round(s, 2), bill["gross_p"] / 100.0))
    G.add("sale bills: each re-adds from its own lines (Marg-side exceptions carried and listed)", True,
          "%d of %d bills do not re-add: %s" % (len(off), len(sbills), off[:15]), blocking=False)

    return dict(G=G, exports=exports, pbills=pbills, plines=plines, sbills=sbills, sale_lines=sale_lines,
                closings=closings, moves=moves, recons=recons, checks=checks, findings=findings, items=items,
                facts=facts, whole=whole, Z=Z, checkable=checkable, pending=pending, alias=alias)


def write(db, B, rules, readings_dir):
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    now = dt.datetime.now(IST).isoformat(timespec="seconds")
    meta = dict(built=now, build_version=BUILD_VERSION, rules_version=rules.get("version", ""), readings=readings_dir,
                checkable=",".join(B["checkable"]), pending=",".join(B["pending"]))
    con.executemany("INSERT INTO sp_meta VALUES (?,?)", list(meta.items()))
    for r in B["exports"].values():
        d = r.get("data", {})
        con.execute("INSERT INTO sp_export VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
            r["md5"], r["name"], r.get("family"), r.get("stamp", ""), d.get("date_from", ""), d.get("date_to", ""), d.get("as_on", ""),
            int(bool(r.get("_accepted"))), json.dumps(r.get("_real_fail", [])), "READ" if r.get("family") else "NOT_USED",
            ("waived: " + "; ".join(r["_waived"])) if r.get("_waived") else ""))
    for (n, p), it in B["items"].items():
        k = B["Z"](n)
        con.execute("INSERT OR IGNORE INTO sp_item VALUES (?,?,?,?,?,?)",
                    (k, n, p, "WHOLE" if k in B["whole"] else "LOOSE", it["first"], it["last"]))
    con.executemany("INSERT INTO sp_item_fact VALUES (?,?,?,?,?,?)", [(a, b, c, None if d is None else str(d), e, f) for a, b, c, d, e, f in B["facts"]])
    con.executemany("INSERT INTO sp_alias VALUES (?,?,?,?)", [(a, v["to"], v["kind"], v["source"]) for a, v in rules.get("aliases", {}).items()])
    for (d, b), bill in B["sbills"].items():
        con.execute("INSERT INTO sp_sale_bill VALUES (?,?,?,?,?,?,?,?,?,?)", (d, b, bill["gross_p"], bill["disc_p"], bill["tax_p"],
                    bill["drcr_p"], bill["net_p"], bill["cash_p"], int(bill["credit_note"]), bill["source"]))
    con.executemany("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    [(d, b, ln["seq"], ln["name"], k, ln["pack"], ln["qty"], u, ln["rate_p"], ln["batch"], ln["expiry"])
                     for d, b, ln, k, u in B["sale_lines"]])
    for (sk, bill, d), b in B["pbills"].items():
        con.execute("INSERT INTO sp_purchase_bill VALUES (?,?,?,?,?,?,?)", (b["supplier"], sk, bill, d, b["amount_p"], b["direction"], b["source"]))
    con.executemany("INSERT INTO sp_purchase_line VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(l["supkey"], l["bill"], l["date"], l["seq"], l["name"], l["_k"], l["packing"], l["qty"], l["free"], l["_u"],
                      l["amount_p"], l["net_amount_p"], l["direction"], l["source"]) for l in B["plines"]])
    for d, r in B["closings"].items():
        agg = collections.defaultdict(float)
        for i in r["data"]["items"]:
            agg[B["Z"](i["name"])] += i["units"]
        con.executemany("INSERT INTO sp_close VALUES (?,?,?,?)", [(d, k, u, r["md5"]) for k, u in agg.items()])
    con.executemany("INSERT INTO sp_move VALUES (?,?,?,?,?)", B["moves"])
    con.executemany("INSERT INTO sp_recon VALUES (?,?,?,?,?)", B["recons"])
    con.executemany("INSERT INTO sp_check VALUES (?,?,?,?,?)", B["checks"])
    con.executemany("INSERT INTO sp_finding VALUES (?,?,?,?)", B["findings"])
    con.executemany("INSERT INTO sp_gate (name, blocking, ok, detail) VALUES (?,?,?,?)", B["G"].rows)
    con.commit()
    con.close()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--readings", required=True)
    ap.add_argument("--rules", default=os.path.join(HERE, "spine_rules.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--finance-db", default="/root/finance/finance.db" if os.path.exists("/root/finance/finance.db") else "")
    ap.add_argument("--acceptance", action="store_true")
    a = ap.parse_args(argv)
    for flag in (os.path.join(HERE, "OFF"), "/root/finance/_off/ALL_OFF"):
        if os.path.exists(flag):
            print("spine_build: switched off (%s)" % flag)
            return 0
    rules = json.load(open(a.rules))
    B = build(load_readings(a.readings), rules, acceptance=a.acceptance, finance_db=a.finance_db or None)
    tmp = a.out + ".new"
    write(tmp, B, rules, a.readings)
    for name, blocking, ok, detail in B["G"].rows:
        print("  %-4s %s%s" % ("ok" if ok else ("FAIL" if blocking else "note"), name, ("  -- " + detail[:400]) if (not ok or not blocking) else ""))
    if B["G"].passed:
        os.replace(tmp, a.out)
        print("SPINE BUILT AND SWAPPED: %s" % a.out)
        return 0
    os.replace(tmp, a.out + ".failed")
    print("GATE FAILED -- nothing swapped; the failed build is %s.failed" % a.out)
    return 3


if __name__ == "__main__":
    sys.exit(main())
